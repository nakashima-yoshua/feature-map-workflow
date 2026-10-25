#!/usr/bin/env python3
"""Real Linux-service integration. No API, customer source, DB or UI calls."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from zipfile import ZipFile

from workflow_contract import ROOT, atomic_json, read, tree
from workflow_compose import COMPOSE, compose
from workflow_orchestrator import Workflow, prepare


def execute(config_path: Path, store: Path) -> Workflow:
    run = prepare(ROOT, config_path, store)
    print("Compose run: " + str(run), flush=True)
    env = {**os.environ, "FMW_RUN_DIR": str(run), "FMW_UID": str(os.getuid() if hasattr(os, "getuid") else 1000),
           "FMW_GID": str(os.getgid() if hasattr(os, "getgid") else 1000)}
    rendered = subprocess.run(["docker", "compose", "-f", str(COMPOSE), "config", "--format", "json"],
                              env=env, check=True, capture_output=True, text=True, timeout=30)
    services = json.loads(rendered.stdout)["services"]
    for name, service in services.items():
        assert service["read_only"] and service["network_mode"] == "none", name
        assert "ALL" in service["cap_drop"] and not service.get("privileged"), name
        assert not service.get("ports") and not service.get("secrets"), name
        assert all("docker.sock" not in mount["source"] for mount in service["volumes"]), name
    for role in ("ai", "build"):
        mounts = {m["target"]: m for m in services[role]["volumes"]}
        assert mounts["/run/candidate"]["read_only"]
        assert mounts["/run/requests"]["read_only"]
        assert "/run/state" not in mounts
        assert "/run/results/" + ("build" if role == "ai" else "ai") not in mounts
    try:
        code = compose(run, "up", "--build", "--abort-on-container-exit", "--exit-code-from", "orchestrator")
    finally:
        cleanup = compose(run, "down", "--remove-orphans")
    assert cleanup == 0, "Compose cleanup failed; run is preserved"
    workflow = Workflow(run)
    workflow.verify()
    assert code == (0 if workflow.state["status"] == "HUMAN_REVIEW_REQUIRED" else 2), workflow.state
    return workflow


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True, help="Private directory outside this repository; evidence is retained")
    args = parser.parse_args()
    store = args.store.resolve()
    store.mkdir(parents=True, exist_ok=True)
    example = ROOT / "examples/module-workflow/workflow.json"
    original = tree(ROOT / "examples/module-workflow/fixture")
    success = execute(example, store)
    assert success.state["status"] == "HUMAN_REVIEW_REQUIRED", success.state
    assert original == tree(ROOT / "examples/module-workflow/fixture")
    behavior = read(success.run / "state/evidence/verify/files/result.json")
    assert behavior["status"] == "passed" and behavior["checks"][0]["observed"] == 2
    isolation = read(success.run / "state/evidence/isolation/files/isolation.json")
    assert isolation["status"] == "passed" and all(check["passed"] for check in isolation["checks"]), isolation
    with ZipFile(success.run / "state/evidence/package/files/candidate.zip") as archive:
        assert set(archive.namelist()) == {"app.py", "requirements.md"}
        assert b"return 2" in archive.read("app.py")
    print("PASS: real proposal/build/test/isolation/package/preservation chain", flush=True)
    # Omit the repair so the independent check actually fails. No test oracle changes.
    config = read(example)
    config["steps"] = [step for step in config["steps"] if step["id"] != "implementation"]
    config["steps"][1]["needs"] = ["requirements"]
    failure_config = store / "failure-config.json"
    atomic_json(failure_config, config)
    failure = execute(failure_config, store)
    assert failure.state["status"] == "HALT", failure.state
    assert failure.state["steps"]["verify"]["status"] == "failed"
    assert failure.state["steps"]["package"]["status"] == "not-run"
    assert not (failure.run / "requests/build/package.json").exists()
    observation = read(failure.run / "state/evidence/verify/files/result.json")
    assert observation["status"] == "failed" and observation["checks"][0]["observed"] == 1
    print("PASS: real failed assertion retains evidence and blocks dependent work", flush=True)
    print(json.dumps({"success_run": str(success.run), "failure_run": str(failure.run)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
