#!/usr/bin/env python3
"""Host-only Compose lifecycle. Containers never receive the Docker socket."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from task_runner import Halt, redact
from workflow_contract import ROOT, atomic_json, lock, read
from task_runner import digest
from workflow_orchestrator import Workflow, prepare, verify_runtime_snapshot

COMPOSE = ROOT / "runtime/compose.yaml"
OVERRIDES = {"compose.codex.yaml", "compose.dotnet.yaml"}


def reviewed_overrides(paths: list[Path]) -> set[str]:
    names = set()
    for path in paths:
        resolved = path.resolve()
        if path.is_symlink() or resolved.parent != ROOT / "runtime" or resolved.name not in OVERRIDES or resolved.name in names:
            raise Halt("Only distinct reviewed repository Compose overrides are supported", "permission")
        names.add(resolved.name)
    return names


def validate_effective(data: dict, run: Path, overrides: set[str], config: dict) -> None:
    """Validate the rendered execution boundary, not just filenames or YAML text."""
    services = data.get("services", {})
    if set(services) != {"orchestrator", "ai", "build"}:
        raise Halt("Compose must contain exactly the three approved services", "permission")
    codex = "compose.codex.yaml" in overrides
    if codex != any(step["mode"] == "codex" for step in config["steps"]):
        raise Halt("Live AI configuration and credential/network override must match", "permission")
    expected_user = str(os.getuid() if hasattr(os, "getuid") else 1000) + ":" + str(os.getgid() if hasattr(os, "getgid") else 1000)
    allowed_fields = {"build", "cap_drop", "command", "cpus", "init", "mem_limit", "network_mode", "pids_limit",
                      "read_only", "restart", "security_opt", "tmpfs", "user", "volumes", "environment", "secrets", "entrypoint"}
    for role, service in services.items():
        if set(service) - allowed_fields or not service.get("read_only") or service.get("cap_drop") != ["ALL"] or \
                service.get("security_opt") != ["no-new-privileges:true"] or service.get("user") != expected_user or service.get("entrypoint") is not None:
            raise Halt("Compose privilege/root/identity boundary differs from policy", "permission")
        if service.get("network_mode") != ("bridge" if role == "ai" and codex else "none"):
            raise Halt("Worker networking differs from the approved role", "permission")
        memory = service.get("mem_limit", 0)
        if isinstance(memory, str) and memory.isdecimal():
            memory = int(memory)  # Compose JSON represents byte limits as decimal strings.
        if not service.get("init") or service.get("restart") != "no" or type(service.get("pids_limit")) is not int or \
                not 1 <= service["pids_limit"] <= 128 or type(memory) is not int or not 1 <= memory <= 2 * 1024**3 or \
                type(service.get("cpus")) not in {int, float} or not 0 < service["cpus"] <= 1:
            raise Halt("Compose lifecycle/resource bounds are invalid", "budget")
        if service.get("tmpfs") != ["/tmp:size=512m,mode=1777"]:
            raise Halt("Only the bounded private temporary filesystem is supported", "permission")
        dockerfile = "runtime/Dockerfile.ai" if role == "ai" and codex else "runtime/Dockerfile.dotnet" if (
            role == "build" and "compose.dotnet.yaml" in overrides) else "runtime/Dockerfile"
        build = service.get("build", {})
        if set(build) != {"context", "dockerfile"} or Path(build["context"]).resolve() != (run / "deployment/context").resolve() or build["dockerfile"] != dockerfile:
            raise Halt("Compose build input differs from the reviewed image", "permission")
        if role == "orchestrator":
            mounts = {"/run/state": ("state", False), "/run/candidate": ("candidate", False),
                      "/run/requests": ("requests", False), "/run/results": ("results", True)}
            command = ["scripts/workflow_orchestrator.py", "serve", "--run", "/run"]
        else:
            mounts = {"/run/state/config.json": ("state/config.json", True),
                      "/run/state/identity.json": ("state/identity.json", True), "/run/candidate": ("candidate", True),
                      "/run/requests": ("requests", True), "/run/results/" + role: ("results/" + role, False)}
            command = ["scripts/workflow_worker.py", role, "--run", "/run"]
        actual = service.get("volumes", [])
        if service.get("command") != command or len(actual) != len(mounts):
            raise Halt("Compose command or mount set differs from policy", "permission")
        seen = set()
        for volume in actual:
            target = volume.get("target")
            if target not in mounts or target in seen or volume.get("type") != "bind":
                raise Halt("Unexpected Compose mount", "permission")
            seen.add(target)
            source, readonly = mounts[target]
            if Path(volume.get("source", "")).resolve() != (run / source).resolve() or bool(volume.get("read_only")) != readonly:
                raise Halt("Compose mount source/access differs from policy", "permission")
        if role == "ai" and codex:
            if service.get("environment") != {"FMW_CODEX_KEY_FILE": "/run/secrets/codex_api_key"}:
                raise Halt("Only the fixed AI credential reference may be configured", "permission")
            secrets = service.get("secrets", [])
            if len(secrets) != 1 or secrets[0].get("source") != "codex_api_key" or secrets[0].get("target") not in {"codex_api_key", "/run/secrets/codex_api_key"}:
                raise Halt("AI must receive exactly its own credential secret", "permission")
        elif service.get("environment") or service.get("secrets"):
            raise Halt("Credentials/environment must not be shared with this role", "permission")
    if codex:
        secrets = data.get("secrets", {})
        if set(secrets) != {"codex_api_key"} or set(secrets["codex_api_key"]) != {"name", "file"}:
            raise Halt("Unexpected secret definition", "permission")
        path = Path(secrets["codex_api_key"]["file"])
        if path.is_symlink() or path.resolve().is_relative_to(ROOT) or path.resolve().is_relative_to(run.resolve()) or \
                not path.is_file() or not 1 <= path.stat().st_size <= 16384:
            raise Halt("Use an existing private AI credential file outside source/run stores", "permission")
    elif data.get("secrets"):
        raise Halt("Offline execution must have no credential secret", "permission")


def _compose(run: Path, *args: str, overrides: list[Path] | None = None) -> int:
    approved = reviewed_overrides(overrides or [])
    context = verify_runtime_snapshot(run)
    name = "fmw-" + run.name.removeprefix("run-")
    argv = ["docker", "compose", "--project-name", name, "-f", str(context / "runtime/compose.yaml")]
    for path in overrides or []:
        argv += ["-f", str(context / "runtime" / path.name)]
    env = {**os.environ, "FMW_RUN_DIR": str(run.resolve()), "FMW_UID": str(os.getuid() if hasattr(os, "getuid") else 1000),
           "FMW_GID": str(os.getgid() if hasattr(os, "getgid") else 1000)}
    if args and args[0] == "up":
        rendered = subprocess.run([*argv, "config", "--format", "json"], env=env, capture_output=True, text=True, timeout=30)
        if rendered.returncode:
            raise Halt("Compose rendering failed before execution", "environment")
        validate_effective(json.loads(rendered.stdout), run, approved, read(run / "state/config.json"))
        data = json.loads(rendered.stdout)
        execution = {"name": name, "services": data["services"]}
        if data.get("secrets"):
            execution["secrets"] = data["secrets"]
        frozen = run / "deployment/execution-compose.json"
        if frozen.exists():
            if read(frozen) != execution:
                raise Halt("Rendered execution contract changed; create a new run", "integrity")
        else:
            atomic_json(frozen, execution)
            frozen.chmod(0o444)
        identity = read(run / "state/identity.json")
        if "execution_hash" not in identity:
            state = read(run / "state/state.json")
            if state["status"] != "PREPARED" or state["started_at"] is not None:
                raise Halt("Execution identity can only be sealed before the first launch", "integrity")
            identity["execution_hash"] = digest(execution)
            state["identity_hash"] = digest(identity)
            atomic_json(run / "state/identity.json", identity)
            atomic_json(run / "state/state.json", state)
        verify_runtime_snapshot(run)
        argv = ["docker", "compose", "--project-name", name, "-f", str(frozen)]
    return subprocess.call([*argv, *args], env=env)


def compose(run: Path, *args: str, overrides: list[Path] | None = None) -> int:
    if not args or args[0] != "up":
        return _compose(run, *args, overrides=overrides)
    fd = lock(run / "deployment/launcher.lock")
    os.close(fd)
    try:
        try:
            return _compose(run, *args, overrides=overrides)
        finally:
            if _compose(run, "down", "--remove-orphans") != 0:
                raise Halt("Compose cleanup failed; inspect this run's containers", "environment")
    finally:
        (run / "deployment/launcher.lock").unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--override", type=Path, action="append", default=[])
    sub = parser.add_subparsers(dest="action", required=True)
    start = sub.add_parser("start")
    start.add_argument("--repo", type=Path, required=True)
    start.add_argument("--config", type=Path, required=True)
    start.add_argument("--store", type=Path, required=True)
    for action in ("resume", "down", "config"):
        command = sub.add_parser(action)
        command.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    try:
        run = prepare(args.repo, args.config, args.store) if args.action == "start" else args.run.resolve()
        print(json.dumps({"run": str(run)}), flush=True)
        if args.action == "config":
            return compose(run, "config", "--quiet", overrides=args.override)
        if args.action == "down":
            return compose(run, "down", "--remove-orphans", overrides=args.override)
        workflow = Workflow(run)
        workflow.verify()
        if workflow.state["status"] in {"HALT", "HUMAN_REVIEW_REQUIRED"}:
            print(json.dumps({"status": workflow.state["status"], "reason": "Terminal runs are not replayed."}))
            return 0 if workflow.state["status"] == "HUMAN_REVIEW_REQUIRED" else 2
        code = compose(run, "up", "--build", "--abort-on-container-exit", "--exit-code-from", "orchestrator",
                       overrides=args.override)
        final = Workflow(run)
        final.verify()
        print(json.dumps({"run": str(run), "status": final.state["status"],
                          "manifest_sha256": final.state.get("manifest_sha256")}, ensure_ascii=False))
        return 0 if code == 0 and final.state["status"] == "HUMAN_REVIEW_REQUIRED" else 2
    except (Halt, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "HALT", "reason": redact(str(exc))[:1000]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
