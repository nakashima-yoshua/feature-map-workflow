#!/usr/bin/env python3
"""Host-only Compose lifecycle. Containers never receive the Docker socket."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from task_runner import Halt, redact
from workflow_contract import ROOT
from workflow_orchestrator import Workflow, prepare

COMPOSE = ROOT / "runtime/compose.yaml"


def compose(run: Path, *args: str, overrides: list[Path] | None = None) -> int:
    name = "fmw-" + run.name.removeprefix("run-")
    argv = ["docker", "compose", "--project-name", name, "-f", str(COMPOSE)]
    for path in overrides or []:
        argv += ["-f", str(path.resolve())]
    env = {**os.environ, "FMW_RUN_DIR": str(run.resolve()), "FMW_UID": str(os.getuid() if hasattr(os, "getuid") else 1000),
           "FMW_GID": str(os.getgid() if hasattr(os, "getgid") else 1000)}
    return subprocess.call([*argv, *args], env=env)


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
        try:
            code = compose(run, "up", "--build", "--abort-on-container-exit", "--exit-code-from", "orchestrator",
                           overrides=args.override)
        finally:
            cleanup = compose(run, "down", "--remove-orphans", overrides=args.override)
        final = Workflow(run)
        final.verify()
        print(json.dumps({"run": str(run), "status": final.state["status"],
                          "manifest_sha256": final.state.get("manifest_sha256")}, ensure_ascii=False))
        return 0 if code == cleanup == 0 and final.state["status"] == "HUMAN_REVIEW_REQUIRED" else 2
    except (Halt, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "HALT", "reason": redact(str(exc))[:1000]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
