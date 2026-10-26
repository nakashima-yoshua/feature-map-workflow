#!/usr/bin/env python3
"""Specification-led serial workflow, preservation and worker-boundary tests."""
from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from task_runner import Halt, digest
from workflow_contract import atomic_json
import workflow_contract as contract
from workflow_orchestrator import Workflow, freeze_runtime, orchestrate, prepare, verify_runtime_snapshot
from workflow_worker import Worker
from workflow_compose import compose, reviewed_overrides, validate_effective

EXAMPLE = contract.ROOT / "examples/module-workflow"


class ContractTests(unittest.TestCase):
    def config(self):
        return contract.read(EXAMPLE / "workflow.json")

    def test_catalog_preserves_all_numbered_candidates_and_ten_phases(self):
        modules = list(contract.catalog().values())
        self.assertEqual(list(range(1, 50)), [m["number"] for m in modules])
        self.assertEqual(10, len({m["phase"] for m in modules}))
        self.assertEqual("要求受付", modules[0]["name"])
        self.assertEqual("納品パッケージ生成", modules[-1]["name"])
        contract.validate(self.config())

    def test_invalid_or_authority_expanding_config_is_rejected_before_any_dispatch(self):
        changes = [
            lambda c: c.update(approved=True),
            lambda c: c.update(risk="HIGH"),
            lambda c: c.update(allowed_paths=["spec.md"]),
            lambda c: c.update(allowed_paths=["tests/new.py"]),
            lambda c: c.update(allowed_paths=["../app.py"]),
            lambda c: c.update(allowed_paths=["C:/app.py"]),
            lambda c: c.update(allowed_paths=[".env.local"]),
            lambda c: c.update(protected_paths=["check_behavior.py"]),
            lambda c: c.update(verification_steps=["requirements"]),
            lambda c: c.update(max_seconds=True),
            lambda c: c["steps"][0].update(needs=["implementation"]),
            lambda c: c["steps"][0].update(module="unknown"),
            lambda c: c["steps"][0].update(id="../outside"),
            lambda c: c["steps"][0].update(runner="windows"),
            lambda c: c["steps"][0].update(runner="database"),
            lambda c: c["steps"][0].update(outputs=["approved.json"]),
            lambda c: c["steps"][0].update(mode="codex", proposal=None),
            lambda c: c["steps"][2].update(argv="python check_behavior.py"),
            lambda c: c["steps"].__setitem__(0, "not an object"),
            lambda c: c["steps"][3].update(outputs=[], argv=["/bin/true"]),
            lambda c: c["steps"][3].pop("verification_result"),
        ]
        for change in changes:
            config = self.config()
            change(config)
            with self.subTest(config=config), self.assertRaises(Halt):
                contract.validate(config)

    def test_duplicate_json_key_cannot_silently_replace_a_policy(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text('{"risk":"LOW","risk":"HIGH"}', encoding="utf-8")
            with self.assertRaisesRegex(Halt, "Duplicate"):
                contract.read(path)


class RunFixture(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        shutil.copytree(EXAMPLE / "fixture", self.repo / "fixture")
        self.git("init", "-q")
        self.git("config", "user.name", "Synthetic")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "core.autocrlf", "false")
        self.git("add", "fixture")
        self.git("commit", "-qm", "Synthetic baseline")
        self.config = contract.read(EXAMPLE / "workflow.json")
        self.config["source_subdir"] = "fixture"
        self.config_path = self.root / "workflow.json"
        self.run = self.prepare()
        self.workflow = Workflow(self.run)

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.repo), *args], capture_output=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr.decode(errors="replace"))
        return result.stdout.decode().strip()

    def prepare(self):
        atomic_json(self.config_path, self.config)
        return prepare(self.repo, self.config_path, self.root / "store")

    def result(self, status="passed", *, corrupt=False):
        """An external worker result, not a claim that a process actually ran."""
        step = self.workflow.config["steps"][self.workflow.state["index"]]
        sid, role = step["id"], step["runner"]
        request = contract.read(self.run / "requests" / role / (sid + ".json"))
        out = self.run / "results" / role / sid
        (out / "files").mkdir(parents=True)
        for name in step["outputs"]:
            path = out / "files" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if name == step.get("verification_result"):
                atomic_json(path, {"status": "passed", "checks": [
                    {"name": "synthetic external assertion", "expected": 2, "observed": 2, "passed": True}]})
            else:
                path.write_bytes(b"synthetic observation\n")
        files = contract.tree(out)
        record = {"version": 1, "run_id": self.run.name, "step": sid,
                  "request_hash": "wrong" if corrupt else digest(request),
                  "status": status, "files": files, "reason": "synthetic external result"}
        atomic_json(out / "record.json", record)

    def drive(self):
        for _ in range(30):
            self.workflow.tick()
            if self.workflow.state["status"] == "HUMAN_REVIEW_REQUIRED":
                return
            if self.workflow.state["index"] == len(self.config["steps"]):
                continue
            step = self.config["steps"][self.workflow.state["index"]]
            if step["runner"] == "ai":
                Worker(self.run, "ai").once()
            elif self.workflow.state["steps"][step["id"]]["status"] == "dispatched":
                self.result()
        self.fail("Workflow did not terminate within the selected steps")


class RunTests(RunFixture):
    def test_snapshot_and_proposals_preserve_originals_and_stop_before_human_acceptance(self):
        original = contract.tree(self.repo / "fixture")
        self.drive()
        state = self.workflow.state
        self.assertEqual("HUMAN_REVIEW_REQUIRED", state["status"])
        self.assertEqual(original, contract.tree(self.repo / "fixture"))
        self.assertIn("return 2", (self.run / "candidate/app.py").read_text())
        self.assertEqual(self.git("rev-parse", "HEAD"), self.workflow.identity["source_revision"])
        self.assertEqual("", self.git("status", "--porcelain"))
        self.assertEqual({"passed"}, {s["status"] for s in state["steps"].values()})
        manifest = contract.read(self.run / "state/final-manifest.json")
        self.assertIn("human review", manifest["authority"])
        self.workflow.verify()
        self.assertFalse(Worker(self.run, "ai").once())

    def test_clean_committed_source_and_external_store_are_required(self):
        with self.assertRaisesRegex(Halt, "outside"):
            prepare(self.repo, self.config_path, self.repo / "store")
        (self.repo / "fixture/app.py").write_text("uncommitted", encoding="utf-8")
        with self.assertRaisesRegex(Halt, "uncommitted"):
            self.prepare()

    def test_all_proposed_paths_are_validated_before_first_write(self):
        # Protected edit follows an otherwise allowed edit: neither may be applied.
        proposal = {"status": "change", "changes": [
            {"path": "requirements.md", "content": "must not be written"},
            {"path": "spec.md", "content": "changed expectation"}]}
        from task_runner import apply_proposal
        with self.assertRaises(Halt):
            apply_proposal(self.run / "candidate", self.config["allowed_paths"], proposal)
        self.assertFalse((self.run / "candidate/requirements.md").exists())
        for extra in ({"review_state": "APPROVED"}, {"status": "approved"}):
            bad = {"status": "change", "changes": [{"path": "app.py", "content": "x"}], **extra}
            with self.assertRaises(Halt):
                apply_proposal(self.run / "candidate", self.config["allowed_paths"], bad)

    def test_restart_adopts_one_completed_request_without_rerunning_it(self):
        self.workflow.tick()
        worker = Worker(self.run, "ai")
        self.assertTrue(worker.once())
        self.workflow = Workflow(self.run)
        self.workflow.tick()
        self.assertEqual(1, self.workflow.state["index"])
        self.assertFalse(worker.once())
        self.workflow.tick()
        self.assertTrue(worker.once())
        self.workflow.tick()
        self.assertEqual(2, self.workflow.state["index"])

    def test_interrupted_claim_is_never_executed_again(self):
        self.workflow.tick()
        (self.run / "results/ai/requirements").mkdir()
        self.assertFalse(Worker(self.run, "ai").once())
        self.assertFalse(self.workflow.tick())
        self.assertEqual(0, self.workflow.state["index"])

    def test_missing_request_after_dispatch_is_not_recreated(self):
        self.workflow.tick()
        request = self.run / "requests/ai/requirements.json"
        request.unlink()
        with self.assertRaises(Halt):
            Workflow(self.run).tick()
        self.assertFalse(request.exists())

    def test_failure_retains_evidence_and_never_dispatches_dependents(self):
        self.workflow.tick()
        self.result("failed")
        with self.assertRaisesRegex(Halt, "failed"):
            self.workflow.tick()
        self.assertEqual("failed", self.workflow.state["steps"]["requirements"]["status"])
        self.assertTrue((self.run / "state/evidence/requirements/record.json").is_file())
        self.assertFalse((self.run / "requests/ai/implementation.json").exists())

    def test_result_identity_and_output_integrity_are_checked(self):
        self.workflow.tick()
        self.result(corrupt=True)
        with self.assertRaisesRegex(Halt, "identity"):
            self.workflow.tick()
        self.assertEqual(0, self.workflow.state["index"])

    def test_worker_output_hash_and_missing_artifacts_cannot_be_accepted(self):
        self.workflow.tick()
        Worker(self.run, "ai").once()
        (self.run / "results/ai/requirements/files/proposal.json").write_bytes(b"changed")
        with self.assertRaisesRegex(Halt, "hash"):
            self.workflow.tick()
        self.assertFalse((self.run / "candidate/requirements.md").exists())

    def test_empty_native_checks_do_not_turn_zero_exit_into_verification(self):
        self.workflow.tick()
        Worker(self.run, "ai").once()
        self.workflow.tick()
        self.workflow.tick()
        Worker(self.run, "ai").once()
        self.workflow.tick()
        self.workflow.tick()
        self.result()  # Build, not functional verification.
        self.workflow.tick()
        self.workflow.tick()
        self.result()
        path = self.run / "results/build/verify/files/result.json"
        atomic_json(path, {"status": "passed", "checks": []})
        record_path = path.parents[1] / "record.json"
        record = contract.read(record_path)
        record["files"]["files/result.json"] = contract.file_hash(path)
        atomic_json(record_path, record)
        with self.assertRaisesRegex(Halt, "native checks"):
            self.workflow.tick()
        self.assertEqual("failed", self.workflow.state["steps"]["verify"]["status"])
        self.assertFalse((self.run / "requests/build/package.json").exists())

    def test_change_after_verification_invalidates_the_old_pass(self):
        self.drive()
        # Simulate a later adopted edit. Earlier verification keeps its old identity.
        (self.run / "candidate/app.py").write_text("def value():\n    return 3\n", encoding="utf-8")
        self.workflow.state["candidate"] = contract.tree(self.run / "candidate")
        self.workflow.state["status"] = "RUNNING"
        with self.assertRaisesRegex(Halt, "old PASS"):
            self.workflow.tick()

    def test_artifact_budget_rejects_result_before_candidate_application(self):
        self.workflow.tick()
        Worker(self.run, "ai").once()
        self.workflow.config["max_artifact_bytes"] = 1
        self.workflow.identity["config_hash"] = digest(self.workflow.config)
        self.workflow.state["identity_hash"] = digest(self.workflow.identity)
        with self.assertRaisesRegex(Halt, "hash/size"):
            self.workflow.tick()
        self.assertFalse((self.run / "candidate/requirements.md").exists())

    def test_worker_rejects_candidate_changed_since_dispatch(self):
        self.workflow.tick()
        (self.run / "candidate/app.py").write_text("unexpected", encoding="utf-8")
        Worker(self.run, "ai").once()
        result = contract.read(self.run / "results/ai/requirements/record.json")
        self.assertEqual("blocked", result["status"])
        self.assertFalse((self.run / "candidate/requirements.md").exists())

    def test_sealed_evidence_and_final_candidate_cannot_silently_change(self):
        self.drive()
        path = self.run / "state/evidence/verify/files/result.json"
        path.write_bytes(b"changed")
        with self.assertRaisesRegex(Halt, "evidence"):
            Workflow(self.run).verify()

    def test_configuration_change_is_not_a_resume(self):
        config = copy.deepcopy(self.config)
        config["purpose"] = "a different scope"
        atomic_json(self.run / "state/config.json", config)
        with self.assertRaisesRegex(Halt, "configuration"):
            Workflow(self.run).verify()

    def test_terminal_candidate_and_manifest_are_verified_when_reading_status(self):
        self.drive()
        candidate = self.run / "candidate/app.py"
        original = candidate.read_bytes()
        candidate.write_bytes(b"changed")
        with self.assertRaisesRegex(Halt, "Candidate"):
            Workflow(self.run).verify()
        candidate.write_bytes(original)
        (self.run / "state/final-manifest.json").write_bytes(b"changed")
        with self.assertRaisesRegex(Halt, "manifest"):
            Workflow(self.run).verify()

    def test_live_broker_is_opt_in_and_credential_is_scoped_without_an_api_call(self):
        self.config["steps"][0].pop("proposal")
        self.config["steps"][0].update(mode="codex", inputs=["spec.md"])
        self.config.update(external_input_allowed=True, codex_version="codex-cli 0.159.0-alpha.3")
        self.run = self.prepare()
        self.workflow = Workflow(self.run)
        self.workflow.tick()
        key_path = self.root / "private-key.txt"
        key_path.write_text("synthetic-not-a-live-key", encoding="utf-8")
        def propose(context):
            self.assertEqual("synthetic-not-a-live-key", os.environ["OPENAI_API_KEY"])
            self.assertEqual(["spec.md"], context.config["read_paths"])
            self.assertGreater(context.timeout(), 0)
            return {"status": "no_change", "changes": []}
        with patch.dict(os.environ, {"FMW_CODEX_KEY_FILE": str(key_path), "OPENAI_API_KEY": "previous-synthetic-key"}), \
                patch("workflow_worker.CodexProposer.propose", side_effect=propose) as broker:
            Worker(self.run, "ai").once()
            self.assertEqual(1, broker.call_count)
            self.assertEqual("previous-synthetic-key", os.environ["OPENAI_API_KEY"])
        record = contract.read(self.run / "results/ai/requirements/record.json")
        self.assertEqual("passed", record["status"])
        self.assertNotIn("synthetic-not-a-live-key", json.dumps(record))

    def test_stop_and_ownership_are_fail_closed(self):
        atomic_json(self.run / "requests/STOP", {"requested": True})
        state = orchestrate(self.run)
        self.assertEqual("HALT", state["status"])
        self.assertIn("stop", state["reason"])
        self.assertFalse((self.run / "requests/ai/requirements.json").exists())
        (self.run / "state/orchestrator.lock").touch()
        with self.assertRaisesRegex(Halt, "owned"):
            orchestrate(self.run)

    def test_missing_worker_and_elapsed_budget_never_count_as_success(self):
        self.workflow.tick()
        self.workflow.state["steps"]["requirements"]["dispatched_at"] -= 100
        with self.assertRaisesRegex(Halt, "ambiguous"):
            self.workflow.tick()
        self.workflow.state["started_at"] -= 1000
        with self.assertRaisesRegex(Halt, "budget"):
            self.workflow.tick()


@unittest.skipUnless(os.name == "posix", "Approved command process groups require Linux")
class ProcessTests(RunFixture):
    def setUp(self):
        super().setUp()
        # Hosted CI's control interpreter may live in /opt/hostedtoolcache.
        # Execute the fixture with the same /usr runtime boundary as our images;
        # do not widen production Landlock grants for a test harness installation.
        choices = (Path(sys.executable), Path("/usr/local/bin/python3"), Path("/usr/bin/python3"))
        self.command_python = next((str(p) for p in choices if p.is_file() and p.resolve().is_relative_to(Path("/usr"))), None)
        self.assertIsNotNone(self.command_python, "Process tests require Python in the image's /usr runtime boundary")

    def test_real_build_process_reports_failure_and_bounded_timeout(self):
        self.config["steps"] = [{"id": "check", "module": "unit-test", "runner": "build", "needs": [],
                                 "inputs": ["app.py"], "outputs": ["result.json"], "verification_result": "result.json", "seconds": 2,
                                 "mode": "command", "argv": [self.command_python, "-c", "raise SystemExit(7)"]}]
        self.config["verification_steps"] = ["check"]
        self.run = self.prepare()
        self.workflow = Workflow(self.run)
        self.workflow.tick()
        Worker(self.run, "build").once()
        result = contract.read(self.run / "results/build/check/record.json")
        self.assertEqual("failed", result["status"])
        self.assertIn("7", result["reason"])
        self.config["steps"][0]["argv"] = [self.command_python, "-c", "import time; time.sleep(5)"]
        self.config["steps"][0]["seconds"] = 1
        self.run = self.prepare()
        self.workflow = Workflow(self.run)
        self.workflow.tick()
        Worker(self.run, "build").once()
        result = contract.read(self.run / "results/build/check/record.json")
        self.assertEqual("blocked", result["status"])
        self.assertIn("timed out", result["reason"])

    def test_build_child_cannot_forge_worker_results_or_read_requests(self):
        self.config["steps"] = [{"id": "check", "module": "security-verification", "runner": "build", "needs": [],
                                 "inputs": ["app.py"], "outputs": ["result.json"], "verification_result": "result.json", "seconds": 5,
                                 "mode": "command", "argv": [self.command_python, "-c", "pass"]}]
        self.config["verification_steps"] = ["check"]
        attack = "from pathlib import Path; import os,json; checks={}; root=Path.cwd().parent; " \
                 "targets=[root/'results/build/future',root/'requests/build/check.json']; " \
                 "\nfor p in targets:\n try:\n  p.mkdir() if p.suffix=='' else p.read_bytes()\n  checks[str(p)]=False\n except OSError:\n  checks[str(p)]=True\n" \
                 "\nPath(os.environ['FMW_OUTPUT_DIR'],'result.json').write_text(json.dumps(checks))\nraise SystemExit(0 if all(checks.values()) else 1)"
        self.config["steps"][0]["argv"] = [self.command_python, "-c", attack]
        self.run = self.prepare()
        self.workflow = Workflow(self.run)
        self.workflow.tick()
        Worker(self.run, "build").once()
        result = contract.read(self.run / "results/build/check/record.json")
        self.assertEqual("passed", result["status"], result)
        native = contract.read(self.run / "results/build/check/files/result.json")
        self.assertTrue(all(native.values()))

    def test_zero_exit_without_declared_result_is_blocked(self):
        self.config["steps"] = [{"id": "check", "module": "unit-test", "runner": "build", "needs": [],
                                 "inputs": ["app.py"], "outputs": ["result.json"], "verification_result": "result.json", "seconds": 5,
                                 "mode": "command", "argv": [self.command_python, "-c", "pass"]}]
        self.config["verification_steps"] = ["check"]
        self.run = self.prepare()
        self.workflow = Workflow(self.run)
        self.workflow.tick()
        Worker(self.run, "build").once()
        result = contract.read(self.run / "results/build/check/record.json")
        self.assertEqual("blocked", result["status"])
        self.assertIn("output is missing", result["reason"])


class ComposePolicyTests(unittest.TestCase):
    def test_explicit_down_requires_and_releases_launcher_ownership(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp) / "run-down"
            (run / "deployment").mkdir(parents=True)
            owner = run / "deployment/launcher.lock"
            owner.touch()
            with patch("workflow_compose._compose", side_effect=AssertionError("Must not stop the other owner")):
                with self.assertRaisesRegex(Halt, "owned"):
                    compose(run, "down", "--remove-orphans")
            self.assertTrue(owner.exists())
            owner.unlink()
            operations = []
            def stop(run_path, *args, **kwargs):
                self.assertEqual(run, run_path)
                self.assertTrue(owner.exists())
                operations.append(args)
                return 0
            with patch("workflow_compose._compose", side_effect=stop):
                self.assertEqual(0, compose(run, "down", "--remove-orphans"))
            self.assertEqual([("down", "--remove-orphans")], operations)
            self.assertFalse(owner.exists())
            with patch("workflow_compose._compose", side_effect=Halt("Synthetic stop failure")):
                with self.assertRaisesRegex(Halt, "Synthetic"):
                    compose(run, "down")
            self.assertFalse(owner.exists())

    def test_external_or_duplicate_overrides_are_not_execution_authority(self):
        with self.assertRaisesRegex(Halt, "reviewed"):
            reviewed_overrides([Path("/tmp/hostile-compose.yaml")])
        approved = contract.ROOT / "runtime/compose.codex.yaml"
        with self.assertRaises(Halt):
            reviewed_overrides([approved, approved])

    def effective(self, run):
        user = str(os.getuid() if hasattr(os, "getuid") else 1000) + ":" + str(os.getgid() if hasattr(os, "getgid") else 1000)
        def service(role):
            mounts = {"state": ("/run/state", False), "candidate": ("/run/candidate", False),
                      "requests": ("/run/requests", False), "results": ("/run/results", True)} if role == "orchestrator" else {
                      "state/config.json": ("/run/state/config.json", True), "state/identity.json": ("/run/state/identity.json", True),
                      "candidate": ("/run/candidate", True), "requests": ("/run/requests", True),
                      "results/" + role: ("/run/results/" + role, False)}
            return {"build": {"context": str(run / "deployment/context"), "dockerfile": "runtime/Dockerfile"},
                    "read_only": True, "cap_drop": ["ALL"], "user": user, "security_opt": ["no-new-privileges:true"],
                    "network_mode": "none", "init": True, "restart": "no", "cpus": 1, "pids_limit": 128,
                    "mem_limit": str(1024**3), "tmpfs": ["/tmp:size=512m,mode=1777"],
                    "command": ["scripts/workflow_orchestrator.py", "serve", "--run", "/run"] if role == "orchestrator" else ["scripts/workflow_worker.py", role, "--run", "/run"],
                    "volumes": [{"type": "bind", "source": str(run / source), "target": target, "read_only": ro}
                                for source, (target, ro) in mounts.items()]}
        return {"services": {role: service(role) for role in ("orchestrator", "ai", "build")}}

    def test_effective_network_privilege_and_extra_host_mount_are_rejected(self):
        run = Path("/synthetic/run").resolve()
        data = self.effective(run)
        config = contract.read(EXAMPLE / "workflow.json")
        validate_effective(data, run, set(), config)
        for change in (lambda d: d["services"]["build"].update(network_mode="bridge"),
                       lambda d: d["services"]["build"].update(privileged=True),
                       lambda d: d["services"]["build"]["volumes"].append({"type": "bind", "source": "/private", "target": "/credentials"})):
            altered = copy.deepcopy(data)
            change(altered)
            with self.assertRaises(Halt):
                validate_effective(altered, run, set(), config)

    def test_mutating_original_yaml_and_build_context_after_validation_cannot_change_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            run = base / "run-snapshot"
            contract.layout(run)
            # A temporary source tree, never the working repository or its originals.
            original = base / "original"
            first = base / "first-capture"
            freeze_runtime(first)
            shutil.copytree(first / "deployment/context", original)
            for p in original.rglob("*"):
                p.chmod(0o755 if p.is_dir() else 0o644)
            original.chmod(0o755)
            implementation, snapshot = freeze_runtime(run, original)
            identity = {"implementation": implementation, "deployment_snapshot": snapshot}
            atomic_json(run / "state/identity.json", identity)
            atomic_json(run / "state/state.json", {"status": "PREPARED", "started_at": None,
                                                   "identity_hash": digest(identity)})
            atomic_json(run / "state/config.json", contract.read(EXAMPLE / "workflow.json"))
            data = self.effective(run)
            launched = []
            def render(argv, **kwargs):
                self.assertEqual(run / "deployment/context/runtime/compose.yaml", Path(argv[argv.index("-f") + 1]))
                # Simulate another source writer during the validation/start boundary.
                (original / "runtime/compose.yaml").write_text("services: {build: {privileged: true}}", encoding="utf-8")
                (original / "runtime/Dockerfile").write_text("FROM unreviewed-image\n", encoding="utf-8")
                (original / "scripts/workflow_worker.py").write_text("unreviewed runtime\n", encoding="utf-8")
                return subprocess.CompletedProcess(argv, 0, json.dumps(data), "")
            def execute(argv, **kwargs):
                action = "up" if "up" in argv else "down"
                launched.append(action)
                if action == "up":
                    path = Path(argv[argv.index("-f") + 1])
                    self.assertEqual(run / "deployment/execution-compose.json", path)
                    execution = contract.read(path)
                    self.assertEqual(data["services"], execution["services"])
                    context = Path(execution["services"]["build"]["build"]["context"])
                    self.assertEqual(run / "deployment/context", context)
                    self.assertNotIn("unreviewed", (context / "runtime/Dockerfile").read_text())
                    self.assertEqual(digest(execution), contract.read(run / "state/identity.json")["execution_hash"])
                    verify_runtime_snapshot(run)
                return 0
            with patch("workflow_compose.ROOT", original), patch("workflow_compose.COMPOSE", original / "runtime/compose.yaml"), \
                    patch("workflow_compose.subprocess.run", side_effect=render), patch("workflow_compose.subprocess.call", side_effect=execute):
                self.assertEqual(0, compose(run, "up", "--build"))
            self.assertEqual(["up", "down"], launched)
            verify_runtime_snapshot(run)
            (run / "deployment/launcher.lock").touch()
            with patch("workflow_compose.subprocess.call", side_effect=AssertionError("Must not stop the other owner")):
                with self.assertRaisesRegex(Halt, "owned"):
                    compose(run, "up", "--build")


if __name__ == "__main__":
    unittest.main(verbosity=2)
