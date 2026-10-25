#!/usr/bin/env python3
"""Consume only fixed requests in a role-specific, isolated Compose service."""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
import tempfile
import time
from pathlib import Path

from task_runner import CodexProposer, Halt, digest, process, redact, safe_file
from workflow_contract import ROOT, ROLES, atomic_json, file_hash, inputs, read, tree, validate
from workflow_orchestrator import fingerprint


class Worker:
    def __init__(self, run: Path, role: str):
        if role not in ROLES:
            raise Halt("Unsupported worker capability", "capability")
        self.run, self.role = run, role
        self.config = validate(read(run / "state/config.json"))
        self.identity = read(run / "state/identity.json")
        if digest(self.config) != self.identity["config_hash"] or fingerprint() != self.identity["implementation"]:
            raise Halt("Worker configuration/implementation differs from the fixed run", "integrity")

    def stopped(self):
        return (self.run / "requests/STOP").exists()

    def assert_isolated(self):
        if platform.system() != "Linux":
            raise Halt("Worker services require Linux container isolation", "environment")
        for path in (Path("/"), self.run / "candidate", self.run / "requests", self.run / "state/config.json"):
            if not os.statvfs(path).f_flag & os.ST_RDONLY:
                raise Halt("Worker root, source, requests and configuration must be read-only mounts", "permission")
        if Path("/var/run/docker.sock").exists():
            raise Halt("Docker daemon access is forbidden inside workers", "permission")

    def execute(self, step: dict, result_dir: Path) -> tuple[str, str]:
        output = result_dir / "files"
        output.mkdir()
        if self.role == "ai":
            if step["mode"] == "recorded-proposal":
                proposal = read(safe_file(self.run / "candidate", step["proposal"]))
            else:
                proposal = self.codex_proposal(step)
            atomic_json(output / "proposal.json", proposal)
            return "passed", "Proposal produced; application and verification remain separate."
        with tempfile.TemporaryDirectory(prefix="fmw-build-") as temp:
            temp_path = Path(temp)
            artifacts = temp_path / "output"
            artifacts.mkdir()
            env = {"PATH": os.defpath + os.pathsep + os.environ.get("PATH", ""), "HOME": temp,
                   "TMPDIR": temp, "TMP": temp, "TEMP": temp, "PYTHONDONTWRITEBYTECODE": "1",
                   "FMW_OUTPUT_DIR": str(artifacts), "DOTNET_CLI_HOME": temp,
                   "DOTNET_CLI_TELEMETRY_OPTOUT": "1", "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1"}
            # Candidate is a read-only mount; all build outputs must go to FMW_OUTPUT_DIR/tmp.
            command = [sys.executable, str(ROOT / "scripts/workflow_sandbox.py"),
                       "--source", str(self.run / "candidate"), "--temporary", temp, "--", *step["argv"]]
            code, log = process(command, self.run / "candidate", step["seconds"], env=env,
                                stop_requested=self.stopped)
            (result_dir / "log.txt").write_text(redact(log), encoding="utf-8")
            selected = {}
            for name in step["outputs"]:
                source = safe_file(artifacts, name)
                if source.exists():
                    selected[name] = file_hash(source)
                elif code == 0:
                    raise Halt("Required build output is missing", "verification")
            if sum(x["bytes"] for x in selected.values()) > self.config["max_artifact_bytes"]:
                raise Halt("Build artifacts exceed configured budget", "budget")
            for name, expected in selected.items():
                target = safe_file(output, name)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(safe_file(artifacts, name), target)
                if file_hash(target) != expected:
                    raise Halt("Build output changed during copy", "integrity")
            return ("passed", "Approved command exited zero; see native results for individual checks.") if code == 0 else (
                "failed", "Approved command exited " + str(code))

    def codex_proposal(self, step: dict) -> dict:
        if not self.config.get("external_input_allowed"):
            raise Halt("Source transmission has not been authorized", "permission")
        key_path = Path(os.environ.get("FMW_CODEX_KEY_FILE", "/run/secrets/codex_api_key"))
        if key_path.is_symlink() or not key_path.is_file() or key_path.stat().st_size > 16384:
            raise Halt("AI-only credential file is unavailable", "permission")
        key = key_path.read_text(encoding="utf-8").strip()
        if not key or "\n" in key:
            raise Halt("AI-only credential file is invalid", "permission")
        # Reuse the existing version-gated, tool-disabled, read-only proposal broker.
        # The secret is available only to this worker/broker, never to the build command.
        previous = os.environ.get("OPENAI_API_KEY")
        try:
            os.environ["OPENAI_API_KEY"] = key
            with tempfile.TemporaryDirectory(prefix="fmw-broker-") as temp:
                class Context:
                    pass
                context = Context()
                context.worktree = self.run / "candidate"
                context.directory = Path(temp)
                context.config = {**self.config, "read_paths": step["inputs"]}
                context.state = {}
                started = time.monotonic()
                context.stop_requested = self.stopped
                context.timeout = lambda: max(.001, step["seconds"] - (time.monotonic() - started))
                return CodexProposer().propose(context)
        finally:
            if previous is None:
                os.environ.pop("OPENAI_API_KEY", None)
            else:
                os.environ["OPENAI_API_KEY"] = previous

    def once(self) -> bool:
        if self.stopped():
            return False
        for step in self.config["steps"]:
            if step["runner"] != self.role:
                continue
            sid = step["id"]
            request_path = self.run / "requests" / self.role / (sid + ".json")
            if not request_path.exists():
                continue
            result_dir = self.run / "results" / self.role / sid
            try:
                result_dir.mkdir()  # Exclusive claim. An interrupted job is never replayed.
            except FileExistsError:
                continue
            atomic_json(result_dir / "started.json", {"started_at": time.time()})
            request_hash = "unverified"
            try:
                request = read(request_path)
                request_hash = digest(request)
                expected = {"version": 1, "run_id": self.identity["run_id"], "step": sid,
                            "config_hash": digest(self.config), "implementation": self.identity["implementation"],
                            "candidate_hash": digest(tree(self.run / "candidate")),
                            "inputs": inputs(self.run / "candidate", step["inputs"])}
                if request != expected:
                    raise Halt("Worker request does not match fixed inputs or candidate", "integrity")
                status, reason = self.execute(step, result_dir)
                if digest(tree(self.run / "candidate")) != request["candidate_hash"]:
                    raise Halt("Candidate changed during worker execution", "integrity")
            except (Halt, OSError, ValueError, KeyError, TypeError) as exc:
                status, reason = "blocked", redact(str(exc))[:1000]
            files = tree(result_dir)
            files.pop("started.json", None)
            record = {"version": 1, "run_id": self.identity["run_id"], "step": sid,
                      "request_hash": request_hash, "status": status, "files": files, "reason": reason}
            atomic_json(result_dir / "record.json", record)
            return True
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=sorted(ROLES))
    parser.add_argument("--run", type=Path, default=Path("/run"))
    args = parser.parse_args()
    try:
        worker = Worker(args.run, args.role)
        worker.assert_isolated()
        while not worker.stopped():
            if not worker.once():
                time.sleep(.1)
        return 0
    except (Halt, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "HALT", "reason": redact(str(exc))[:1000]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
