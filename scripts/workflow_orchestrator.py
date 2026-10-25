#!/usr/bin/env python3
"""One feature, one serial run. No Docker API, publication or approval authority."""
from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import tarfile
import time
import uuid
from pathlib import Path

from task_runner import Halt, apply_proposal, digest, redact, safe_file
from workflow_contract import (CATALOG, MAX_FILE, ROOT, TERMINAL, catalog, file_hash, inputs,
                               atomic_json, layout, lock, path_name, read, tree, validate)


DEFINITIONS = ("Dockerfile", "Dockerfile.ai", "Dockerfile.dotnet", "compose.yaml", "compose.codex.yaml", "compose.dotnet.yaml")


def fingerprint(root: Path = ROOT) -> dict:
    names = ["task_runner.py", "workflow_contract.py", "workflow_orchestrator.py", "workflow_worker.py",
             "workflow_compose.py", "workflow_sandbox.py"]
    return {"runtime": {name: file_hash(root / "scripts" / name) for name in names},
            "catalog": file_hash(root / "skills/feature-map-workflow/assets/task-modules.json"),
            "deployment": {name: file_hash(root / "runtime" / name) for name in DEFINITIONS}}


def freeze_runtime(run: Path, root: Path = ROOT) -> tuple[dict, dict]:
    """Copy only known control inputs, then bind the actual copied bytes to identity."""
    captured = fingerprint(root)
    selected = {"scripts/" + name: item for name, item in captured["runtime"].items()}
    selected.update({"runtime/" + name: item for name, item in captured["deployment"].items()})
    selected["skills/feature-map-workflow/assets/task-modules.json"] = captured["catalog"]
    selected[".dockerignore"] = file_hash(root / ".dockerignore")
    context = run / "deployment/context"
    context.mkdir(parents=True)
    for name, expected in selected.items():
        source = safe_file(root, name)
        target = safe_file(context, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if file_hash(target) != expected:
            raise Halt("Runtime changed during snapshot; no deployment was started", "integrity")
        target.chmod(0o444)
    if tree(context) != selected or fingerprint(context) != captured:
        raise Halt("Runtime snapshot does not match captured inputs", "integrity")
    for directory in sorted((p for p in context.rglob("*") if p.is_dir()), reverse=True):
        directory.chmod(0o555)
    context.chmod(0o555)
    return captured, selected


def verify_runtime_snapshot(run: Path) -> Path:
    context = run / "deployment/context"
    identity = read(run / "state/identity.json")
    if "deployment_snapshot" not in identity or tree(context) != identity["deployment_snapshot"] or \
            fingerprint(context) != identity["implementation"]:
        raise Halt("Frozen runtime is missing/changed; preserve this run and create a new one", "integrity")
    if "execution_hash" in identity and digest(read(run / "deployment/execution-compose.json")) != identity["execution_hash"]:
        raise Halt("Frozen execution contract changed", "integrity")
    return context


def prepare(repo: Path, config_path: Path, store: Path) -> Path:
    repo, store = repo.resolve(), store.resolve()
    if store.is_relative_to(repo):
        raise Halt("Run store must survive source/worktree cleanup outside this repository", "permission")
    config = validate(read(config_path))
    def git(*args, raw=False):
        result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=30)
        if result.returncode:
            raise Halt("Git snapshot operation failed", "repository")
        return result.stdout if raw else result.stdout.decode().strip()
    revision = git("rev-parse", "HEAD")
    if git("status", "--porcelain", "--", config["source_subdir"]):
        raise Halt("Selected source contains uncommitted changes", "repository")
    archive = git("archive", "--format=tar", revision + ":" + config["source_subdir"], raw=True)
    if len(archive) > 70 * 1024 * 1024:
        raise Halt("Source archive exceeds first-stage budget", "budget")
    run = store / ("run-" + uuid.uuid4().hex)
    run.mkdir(parents=True, mode=0o700)
    layout(run)
    baseline = run / "state/baseline"
    baseline.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as src:
        for entry in src:
            name = path_name(entry.name.rstrip("/"))
            path = safe_file(baseline, name)
            if entry.isdir():
                path.mkdir(parents=True, exist_ok=True)
            elif entry.isfile() and entry.size <= 64 * 1024 * 1024:
                path.parent.mkdir(parents=True, exist_ok=True)
                with src.extractfile(entry) as stream, path.open("xb") as target:
                    shutil.copyfileobj(stream, target)
                path.chmod(0o755 if entry.mode & 0o111 else 0o644)
            else:
                raise Halt("Source contains unsupported linked/special files", "permission")
    baseline_tree = tree(baseline)
    inputs(baseline, config["protected_paths"])
    shutil.copytree(baseline, run / "candidate", dirs_exist_ok=True)
    atomic_json(run / "state/config.json", config)
    implementation, deployment = freeze_runtime(run)
    identity = {"run_id": run.name, "source_revision": revision, "source_subdir": config["source_subdir"],
                "config_hash": digest(config), "baseline": baseline_tree, "implementation": implementation,
                "deployment_snapshot": deployment}
    atomic_json(run / "state/identity.json", identity)
    state = {"version": 1, "run_id": run.name, "identity_hash": digest(identity), "status": "PREPARED",
             "started_at": None, "index": 0, "candidate": baseline_tree,
             "steps": {s["id"]: {"status": "not-run"} for s in config["steps"]}}
    atomic_json(run / "state/state.json", state)
    return run


class Workflow:
    def __init__(self, run: Path):
        self.run = run
        self.config = validate(read(run / "state/config.json"))
        self.identity = read(run / "state/identity.json")
        self.state = read(run / "state/state.json")

    def save(self):
        atomic_json(self.run / "state/state.json", self.state)

    def verify(self):
        if digest(self.config) != self.identity["config_hash"] or digest(self.identity) != self.state["identity_hash"]:
            raise Halt("Run configuration or identity changed", "integrity")
        if fingerprint() != self.identity["implementation"]:
            raise Halt("Runtime/catalog changed; create a new run", "integrity")
        if tree(self.run / "state/baseline") != self.identity["baseline"]:
            raise Halt("Baseline changed", "integrity")
        if tree(self.run / "candidate") != self.state["candidate"]:
            raise Halt("Candidate changed outside an adopted proposal", "integrity")
        if (self.run / "deployment").exists():  # Host/audit view; bootstrap inputs are not mounted into services.
            verify_runtime_snapshot(self.run)
        for sid, record in self.state["steps"].items():
            if "sealed" in record and tree(self.run / "state/evidence" / sid) != record["sealed"]:
                raise Halt("Adopted evidence changed", "integrity")
        if self.state["status"] == "HUMAN_REVIEW_REQUIRED":
            if file_hash(self.run / "state/final-manifest.json")["sha256"] != self.state["manifest_sha256"]:
                raise Halt("Final manifest changed", "integrity")

    def halt(self, exc: Exception):
        self.state["status"] = "HALT"
        self.state["reason"] = redact(str(exc))[:1000]
        if self.state["index"] < len(self.config["steps"]):
            sid = self.config["steps"][self.state["index"]]["id"]
            if self.state["steps"][sid]["status"] in {"dispatched", "passed"}:
                self.state["steps"][sid]["status"] = "blocked"
        self.save()

    def tick(self) -> bool:
        """Return True only when a transition was made, never resubmit dispatched work."""
        self.verify()
        if self.state["status"] in TERMINAL:
            return False
        if (self.run / "requests/STOP").exists():
            raise Halt("Operator requested stop", "operator_stop")
        if self.state["started_at"] is None:
            self.state["started_at"] = time.time()
        if time.time() - self.state["started_at"] > self.config["max_seconds"]:
            raise Halt("Workflow elapsed-time budget exhausted", "budget")
        index = self.state["index"]
        if index == len(self.config["steps"]):
            if any(self.state["steps"][sid]["status"] != "passed" for sid in self.config["verification_steps"]):
                raise Halt("Required verification is incomplete", "verification")
            if any(self.state["steps"][sid]["candidate_hash"] != digest(self.state["candidate"])
                   for sid in self.config["verification_steps"]):
                raise Halt("Candidate changed after required verification; old PASS cannot be reused", "verification")
            manifest = {"version": 1, "category": "candidate-and-execution-evidence", "identity": self.identity,
                        "candidate": self.state["candidate"], "steps": self.state["steps"],
                        "authority": "Self-check only; human review, release and delivery remain separate."}
            path = self.run / "state/final-manifest.json"
            atomic_json(path, manifest)
            self.state["manifest_sha256"] = file_hash(path)["sha256"]
            self.state["status"] = "HUMAN_REVIEW_REQUIRED"
            self.save()
            return True
        step = self.config["steps"][index]
        sid, role = step["id"], step["runner"]
        record = self.state["steps"][sid]
        request_path = self.run / "requests" / role / (sid + ".json")
        if record["status"] == "not-run":
            if any(self.state["steps"][dep]["status"] != "passed" for dep in step["needs"]):
                raise Halt("Dependency has not passed", "dependency")
            request = {"version": 1, "run_id": self.identity["run_id"], "step": sid,
                       "config_hash": digest(self.config), "implementation": self.identity["implementation"],
                       "candidate_hash": digest(self.state["candidate"]),
                       "inputs": inputs(self.run / "candidate", step["inputs"])}
            if request_path.exists():
                raise Halt("Unexpected existing request; no automatic replay", "integrity")
            record.update(status="dispatched", request_hash=digest(request), dispatched_at=time.time(),
                          candidate_hash=request["candidate_hash"])
            self.state["status"] = "RUNNING"
            self.save()  # A crash here HALTs on missing request; it never duplicates work.
            atomic_json(request_path, request)
            return True
        if record["status"] != "dispatched" or digest(read(request_path)) != record["request_hash"]:
            raise Halt("Missing or altered dispatched request", "integrity")
        result_dir = self.run / "results" / role / sid
        result_path = result_dir / "record.json"
        if not result_path.exists():
            if time.time() - record["dispatched_at"] > step["seconds"] + 15:
                raise Halt("Worker result unavailable/ambiguous; inspect before a new run", "environment")
            return False
        result = read(result_path)
        fields = {"version", "run_id", "step", "request_hash", "status", "files", "reason"}
        if set(result) != fields or result["version"] != 1 or result["run_id"] != self.identity["run_id"] or \
                result["step"] != sid or result["request_hash"] != record["request_hash"] or \
                result["status"] not in {"passed", "failed", "blocked"} or not isinstance(result["files"], dict):
            raise Halt("Invalid worker result identity or status", "integrity")
        actual = tree(result_dir)
        actual.pop("record.json", None)
        actual.pop("started.json", None)
        previous_bytes = sum(item["bytes"] for saved in self.state["steps"].values()
                             for item in saved.get("sealed", {}).values())
        if actual != result["files"] or previous_bytes + sum(x["bytes"] for x in actual.values()) + file_hash(result_path)["bytes"] > self.config["max_artifact_bytes"]:
            raise Halt("Worker artifact hash/size mismatch", "integrity")
        sealed = self.run / "state/evidence" / sid
        sealed.mkdir(parents=True)  # Never overwrite a possibly partial previous import.
        for name in ["record.json", *actual]:
            target = safe_file(sealed, path_name(name))
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(safe_file(result_dir, name), target)
        if {name: file_hash(safe_file(sealed, name)) for name in actual} != actual or \
                read(sealed / "record.json") != result:
            raise Halt("Evidence changed during import", "integrity")
        record.update(status=result["status"], sealed=tree(sealed))
        if result["status"] != "passed":
            self.save()
            raise Halt("Worker " + result["status"] + ": " + str(result["reason"]), "execution")
        if any("files/" + name not in actual for name in step["outputs"]):
            raise Halt("Required output artifact is missing", "verification")
        if sid in self.config["verification_steps"]:
            native = read(safe_file(sealed / "files", step["verification_result"]))
            checks = native.get("checks") if isinstance(native, dict) else None
            if not isinstance(native, dict) or native.get("status") != "passed" or not isinstance(checks, list) or not checks or any(
                    not isinstance(check, dict) or not isinstance(check.get("name"), str) or not check["name"].strip()
                    or check.get("passed") is not True or "expected" not in check or "observed" not in check
                    for check in checks):
                record["status"] = "failed"
                self.save()
                raise Halt("Required native checks do not support PASS", "verification")
        if role == "ai":
            proposal = read(sealed / "files/proposal.json")
            apply_proposal(self.run / "candidate", self.config["allowed_paths"], proposal)
        if inputs(self.run / "candidate", self.config["protected_paths"]) != {
                name: self.identity["baseline"][name] for name in self.config["protected_paths"]}:
            raise Halt("Protected specification or expectation changed", "integrity")
        self.state["candidate"] = tree(self.run / "candidate")
        self.state["index"] += 1
        self.save()
        return True


def orchestrate(run: Path) -> dict:
    fd = lock(run / "state/orchestrator.lock")
    os.close(fd)
    workflow = None
    try:
        workflow = Workflow(run)
        while workflow.state["status"] not in TERMINAL:
            if not workflow.tick():
                time.sleep(.1)
        workflow.verify()
        return workflow.state
    except (Halt, OSError, ValueError, KeyError, TypeError) as exc:
        if workflow is not None:
            workflow.halt(exc)
            return workflow.state
        raise
    finally:
        (run / "state/orchestrator.lock").unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    init = sub.add_parser("init")
    init.add_argument("--repo", type=Path, required=True)
    init.add_argument("--config", type=Path, required=True)
    init.add_argument("--store", type=Path, required=True)
    sub.add_parser("catalog")
    for action in ("serve", "status", "stop"):
        command = sub.add_parser(action)
        command.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == "catalog":
            print(json.dumps(list(catalog().values()), ensure_ascii=False))
            return 0
        if args.action == "init":
            print(prepare(args.repo, args.config, args.store))
            return 0
        if args.action == "stop":
            atomic_json(args.run / "requests/STOP", {"requested": True})
            return 0
        if args.action == "serve":
            state = orchestrate(args.run)
        else:
            workflow = Workflow(args.run)
            workflow.verify()
            state = workflow.state
        print(json.dumps(state, ensure_ascii=False))
        return 0 if state["status"] == "HUMAN_REVIEW_REQUIRED" else 2
    except (Halt, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "HALT", "reason": redact(str(exc))[:1000]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
