#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import os
import socket
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import task_runner as tr


MAP = '''<featureMap version="1.3" mode="change" state="ready">
<meta><system>fixture</system><feature>bounded repair</feature></meta>
<goal><purpose>Return the approved value.</purpose></goal>
<sourceMap><ref kind="entry" target="app.py:value"/></sourceMap>
</featureMap>'''
BAD = {"status": "change", "changes": [{"path": "app.py", "content": "def value():\n    return 3\n"}]}
GOOD = {"status": "change", "changes": [{"path": "app.py", "content": "def value():\n    return 2\n"}]}


class Proposals:
    def __init__(self, *values):
        self.values = iter(values)
        self.calls = 0

    def propose(self, runner):
        self.calls += 1
        return copy.deepcopy(next(self.values))


class FixtureEvaluator:
    """Test-only executor for fixed fixture code; never available from the CLI."""
    def __init__(self):
        self.calls = 0

    def check(self, *args):
        pass

    def run(self, worktree, argv, timeout, empty_git):
        self.calls += 1
        return tr.process([sys.executable, *argv[1:]], worktree, timeout,
                          {"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"})


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        tr.git(self.repo, "init", "-q")
        (self.repo / "app.py").write_text("def value():\n    return 1\n")
        (self.repo / "tests").mkdir()
        (self.repo / "tests/test_behavior.py").write_text(
            "import os, sys\nsys.path.insert(0, os.getcwd())\nfrom app import value\nassert value() == 2\nprint('invariant: passed')\n")
        (self.repo / "feature-map.xml").write_text(MAP)
        tr.git(self.repo, "add", ".")
        tr.git(self.repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@localhost", "commit", "-qm", "baseline")
        self.config = {"version": 1, "task_id": "fixture-fix", "purpose": "Return the approved value",
                       "exclude": ["Changing tests or API"], "contract_ref": "issue:fixture",
                       "invariants": ["value() returns 2"], "acceptance": ["Existing test passes"], "risk": "LOW",
                       "allowed_paths": ["app.py"], "read_paths": ["app.py", "tests/test_behavior.py"],
                       "protected_paths": ["tests/test_behavior.py"], "feature_map": "feature-map.xml",
                       "checks": [["python3", "tests/test_behavior.py"]], "max_attempts": 3,
                       "max_seconds": 60, "command_seconds": 10, "unverified": ["Actual business acceptance"]}
        self.evaluator = FixtureEvaluator()

    def tearDown(self):
        self.temp.cleanup()

    def create(self, approval=None, sandbox=None):
        return tr.Runner.create(self.repo, self.root / "runs", copy.deepcopy(self.config), approval,
                                sandbox or self.evaluator)

    def test_passed_candidate_preserves_source_and_requires_human_review(self):
        runner = self.create()
        state = runner.execute(Proposals(GOOD))
        self.assertEqual(state["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(state["review_state"], "UNREVIEWED")
        self.assertEqual(state["baseline"]["status"], "failed")
        self.assertEqual(state["last_result"]["status"], "passed")
        self.assertIn("return 1", (self.repo / "app.py").read_text())
        self.assertEqual(tr.git(self.repo, "rev-parse", "HEAD"), state["base_revision"])
        report = tr.read_json(runner.directory / "human-review-request.json")
        self.assertIn("UNVERIFIED", report["test_evidence_and_limits"])
        self.assertTrue((runner.directory / "candidate.patch").is_file())

    def test_valid_improvement_after_failed_attempt(self):
        runner = self.create()
        state = runner.execute(Proposals(BAD, GOOD))
        self.assertEqual([a["status"] for a in state["attempts"]], ["failed", "passed"])
        self.assertTrue((runner.directory / "attempt-1.patch").exists())
        self.assertEqual(state["status"], "HUMAN_REVIEW_REQUIRED")

    def test_failed_new_file_content_survives_recovery(self):
        self.config["allowed_paths"].append("extra.py")
        runner = self.create()
        candidate = {"status": "change", "changes": [*BAD["changes"], {"path": "extra.py", "content": "unused = 1\n"}]}
        state = runner.execute(Proposals(candidate, GOOD))
        self.assertEqual(state["status"], "HUMAN_REVIEW_REQUIRED")
        evidence = tr.read_json(runner.directory / "attempt-1-proposal.json")
        self.assertEqual(evidence["changes"][1]["content"], "unused = 1\n")
        self.assertFalse((runner.worktree / "extra.py").exists())
        self.assertIn("attempt-1-proposal.json", state["evidence_hashes"])

    def test_budget_and_repeated_failure_stop(self):
        self.config["max_attempts"] = 1
        runner = self.create()
        state = runner.execute(Proposals(BAD))
        self.assertEqual(state["status"], "HALT")
        self.assertEqual(state["failure_category"], "budget")
        self.config["max_attempts"] = 3
        runner = self.create()
        proposer = Proposals(BAD, BAD, GOOD)
        state = runner.execute(proposer)
        self.assertEqual(proposer.calls, 2)
        self.assertEqual(state["failure_category"], "implementation")

    def test_expired_budget_never_invokes_agent_or_evaluator(self):
        runner = self.create()
        runner.state["started_at"] = time.time() - 61
        proposer = Proposals(GOOD)
        self.assertEqual(runner.execute(proposer)["failure_category"], "budget")
        self.assertEqual(proposer.calls, 0)
        self.assertEqual(self.evaluator.calls, 0)

    def test_scope_escape_and_self_approval_are_rejected_before_write(self):
        proposals = [
            {"status": "change", "changes": [{"path": "tests/test_behavior.py", "content": "pass"}]},
            {"status": "change", "changes": [{"path": "../outside", "content": "bad"}]},
            {"status": "change", "changes": [{"path": "/tmp/outside", "content": "bad"}]},
            {**GOOD, "review_state": "APPROVED"},
            {"status": "change", "changes": [*GOOD["changes"], {"path": ".git/config", "content": "bad"}]},
        ]
        for proposal in proposals:
            with self.subTest(proposal=proposal):
                runner = self.create()
                state = runner.execute(Proposals(proposal))
                self.assertEqual(state["status"], "HALT")
                self.assertEqual(state["review_state"], "UNREVIEWED")
                self.assertIn("return 1", (runner.worktree / "app.py").read_text())

    def test_unapproved_medium_and_high_halt_before_execution(self):
        for risk in ("MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"):
            self.config["risk"] = risk
            runner = self.create()
            proposer = Proposals(GOOD)
            self.assertEqual(runner.execute(proposer)["failure_category"], "permission")
            self.assertEqual(proposer.calls, 0)
        self.assertEqual(self.evaluator.calls, 0)

    def test_medium_approval_is_bound_to_contract_and_revision(self):
        self.config["risk"] = "MEDIUM"
        approval = {"decision": "approved", "reviewer": "human", "evidence_ref": "review:fixture",
                    "config_hash": tr.digest(self.config), "revision": tr.git(self.repo, "rev-parse", "HEAD")}
        runner = self.create(approval)
        self.assertEqual(runner.execute(Proposals(GOOD))["status"], "HUMAN_REVIEW_REQUIRED")
        approval["revision"] = "stale"
        runner = self.create(approval)
        self.assertEqual(runner.execute(Proposals(GOOD))["failure_category"], "permission")

    def test_os_isolation_failure_is_fail_closed(self):
        class Unavailable(FixtureEvaluator):
            def check(self, *args):
                raise tr.Halt("OS isolation unavailable", "environment")
        sandbox = Unavailable()
        runner = self.create(sandbox=sandbox)
        proposer = Proposals(GOOD)
        self.assertEqual(runner.execute(proposer)["failure_category"], "environment")
        self.assertEqual(sandbox.calls, 0)
        self.assertEqual(proposer.calls, 0)

    def test_restart_uses_checkpoint_and_does_not_replay_baseline(self):
        runner = self.create()
        state = runner.execute(Proposals(BAD), pause_after=1)
        self.assertEqual(state["status"], "READY")
        self.assertEqual(self.evaluator.calls, 2)
        resumed = tr.Runner.load(runner.directory, self.evaluator)
        self.assertEqual(resumed.execute(Proposals(GOOD))["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(self.evaluator.calls, 3)
        proposer = Proposals(GOOD)
        resumed = tr.Runner.load(runner.directory, self.evaluator)
        resumed.execute(proposer)
        self.assertEqual(proposer.calls, 0)
        self.assertEqual(self.evaluator.calls, 3)

    def test_interrupt_does_not_replay_unknown_side_effect(self):
        runner = self.create()
        runner.state["next_action"] = "in_flight"
        runner.save()
        resumed = tr.Runner.load(runner.directory, self.evaluator)
        proposer = Proposals(GOOD)
        state = resumed.execute(proposer)
        self.assertEqual(state["status"], "HALT")
        self.assertEqual(proposer.calls, 0)

    def test_changed_config_evidence_and_revision_invalidate_resume(self):
        runner = self.create()
        runner.execute(Proposals(BAD), pause_after=1)
        config = tr.read_json(runner.directory / "config.json")
        config["max_attempts"] = 4
        tr.atomic_json(runner.directory / "config.json", config)
        with self.assertRaises(tr.Halt):
            tr.Runner.load(runner.directory)
        runner = self.create()
        runner.execute(Proposals(BAD), pause_after=1)
        (runner.directory / "baseline-check-0.log").write_text("tampered")
        resumed = tr.Runner.load(runner.directory, self.evaluator)
        proposer = Proposals(GOOD)
        self.assertEqual(resumed.execute(proposer)["status"], "HALT")
        self.assertEqual(proposer.calls, 0)

    def test_source_conflict_and_dirty_worktree_halt(self):
        runner = self.create()
        (runner.worktree / "app.py").write_text("modified")
        self.assertEqual(runner.execute(Proposals(GOOD))["failure_category"], "repository_conflict")
        runner = self.create()
        (self.repo / "app.py").write_text("modified")
        self.assertEqual(runner.execute(Proposals(GOOD))["failure_category"], "repository_conflict")

    def test_candidate_modified_during_evaluation_is_not_adopted(self):
        class ConcurrentWriter(FixtureEvaluator):
            def run(self, worktree, argv, timeout, empty_git):
                result = super().run(worktree, argv, timeout, empty_git)
                if self.calls > 1:
                    (worktree / "app.py").write_text("def value():\n    return 999\n")
                return result
        runner = self.create(sandbox=ConcurrentWriter())
        state = runner.execute(Proposals(GOOD))
        self.assertEqual(state["status"], "HALT")
        self.assertEqual(state["failure_category"], "repository_conflict")
        self.assertIsNone(state["candidate_revision"])

    def test_halt_resume_is_idempotent_and_preserves_original_failure(self):
        runner = self.create()
        runner.execute(Proposals({**GOOD, "review_state": "APPROVED"}))
        reason = runner.state["halt_reason"]
        resumed = tr.Runner.load(runner.directory, self.evaluator)
        proposer = Proposals(GOOD)
        resumed.execute(proposer)
        self.assertEqual(resumed.state["halt_reason"], reason)
        self.assertEqual(proposer.calls, 0)

    def test_approval_is_separate_and_invalidated_by_later_change(self):
        runner = self.create()
        runner.execute(Proposals(GOOD))
        revision = runner.state["candidate_revision"]
        runner.human_review("human", revision, "APPROVED", "review:fixture")
        self.assertEqual(runner.state["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(runner.state["review_state"], "APPROVED")
        (runner.worktree / "app.py").write_text("changed after review")
        self.assertFalse(runner.verify_evidence())
        self.assertEqual(runner.state["review_state"], "INVALIDATED")
        self.assertEqual(runner.state["status"], "HALT")

    def test_review_requires_exact_revision(self):
        runner = self.create()
        runner.execute(Proposals(GOOD))
        with self.assertRaises(tr.Halt):
            runner.human_review("human", runner.state["base_revision"], "APPROVED", "review:fixture")
        self.assertEqual(runner.state["review_state"], "UNREVIEWED")

    def test_no_change_is_valid_only_with_passing_fixed_checks(self):
        (self.repo / "app.py").write_text(GOOD["changes"][0]["content"])
        tr.git(self.repo, "add", "app.py")
        tr.git(self.repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@localhost", "commit", "-qm", "already correct")
        runner = self.create()
        self.assertEqual(runner.execute(Proposals({"status": "no_change", "changes": []}))["status"], "NO_CHANGE")

    def test_xsd_invalid_high_open_and_failed_acceptance_halt(self):
        cases = [("<wrong/>", "XSD"),
                 (MAP.replace("</featureMap>", '<open><item id="O1" impact="high" next="Ask human">unknown</item></open></featureMap>'), "High-impact"),
                 (MAP.replace("</featureMap>", '<verify><case id="V1" type="normal" status="failed"><condition>fixture</condition><expect>pass</expect></case></verify></featureMap>'), "acceptance")]
        for content, reason in cases:
            with self.subTest(content=content):
                runner = self.create()
                (runner.worktree / "feature-map.xml").write_text(content)
                with self.assertRaisesRegex(tr.Halt, reason):
                    runner.map_gate()

    def test_symlink_paths_are_rejected(self):
        runner = self.create()
        path = runner.worktree / "app.py"
        path.unlink()
        path.symlink_to(self.repo / "app.py")
        with self.assertRaises(tr.Halt):
            runner.apply(GOOD)
        self.assertIn("return 1", (self.repo / "app.py").read_text())

    def test_metrics_never_trade_correctness_for_performance(self):
        class Metrics(FixtureEvaluator):
            def run(self, *args):
                code, output = super().run(*args)
                return code, output + "\nMETRIC=1.0\n"
        self.config["metric"] = "minimize"
        runner = self.create(sandbox=Metrics())
        state = runner.execute(Proposals(BAD, GOOD))
        self.assertEqual(state["attempts"][0]["status"], "failed")
        self.assertEqual(state["status"], "HUMAN_REVIEW_REQUIRED")

    def test_model_input_requires_explicit_opt_in(self):
        runner = self.create()
        with patch("task_runner.process") as execution:
            with self.assertRaises(tr.Halt):
                tr.CodexProposer().propose(runner)
            execution.assert_not_called()

    def test_codex_broker_is_read_only_input_scoped_and_tool_restricted(self):
        self.config.update(external_input_allowed=True, codex_version=tr.CodexProposer.VERSION)
        runner = self.create()
        calls = []

        def fake_process(argv, cwd, timeout, env=None, stdin=None):
            calls.append((argv, cwd, env, stdin))
            if "--version" in argv:
                return 0, tr.CodexProposer.VERSION + "\n"
            path = Path(argv[argv.index("--output-last-message") + 1])
            tr.atomic_json(path, GOOD)
            return 0, '{"type":"turn.completed","usage":{"input_tokens":42,"output_tokens":7}}\n'

        with patch.dict(os.environ, {"OPENAI_API_KEY": "synthetic-key-not-sent-as-input"}), \
                patch("task_runner.shutil.which", return_value="/reviewed/codex"), \
                patch("task_runner.process", side_effect=fake_process):
            proposal = tr.CodexProposer().propose(runner)
        self.assertEqual(proposal, GOOD)
        argv, cwd, env, text = calls[-1]
        self.assertEqual(argv[argv.index("--sandbox") + 1], "read-only")
        self.assertIn("--ignore-user-config", argv)
        self.assertIn("--strict-config", argv)
        self.assertNotEqual(cwd, runner.worktree)
        self.assertEqual(set(json.loads(text)["files"]), set(self.config["read_paths"]))
        self.assertNotIn("synthetic-key-not-sent-as-input", text)
        self.assertNotIn("TYPESAFE_API_KEY", env)
        self.assertIn("shell_tool", argv)
        self.assertIn("plugins", argv)
        self.assertEqual(runner.state["usage"]["input_tokens"], 42)

    def test_changed_execution_environment_halts_before_retry(self):
        runner = self.create()
        runner.state["execution_environment"]["kernel"] = "changed"
        proposer = Proposals(GOOD)
        self.assertEqual(runner.execute(proposer)["failure_category"], "environment")
        self.assertEqual(proposer.calls, 0)

    def test_passing_but_slower_candidate_is_not_adopted(self):
        (self.repo / "app.py").write_text(GOOD["changes"][0]["content"])
        tr.git(self.repo, "add", "app.py")
        tr.git(self.repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@localhost", "commit", "-qm", "passing baseline")
        class Metrics(FixtureEvaluator):
            def run(self, worktree, *args):
                code, output = super().run(worktree, *args)
                metric = 11 if "slower" in (worktree / "app.py").read_text() else 10
                return code, output + f"\nMETRIC={metric}\n"
        self.config.update(metric="minimize", max_attempts=1)
        runner = self.create(sandbox=Metrics())
        candidate = {"status": "change", "changes": [{"path": "app.py", "content": "def value():\n    return 2 # slower\n"}]}
        state = runner.execute(Proposals(candidate))
        self.assertEqual(state["status"], "HALT")
        self.assertIsNone(state["candidate_revision"])
        self.assertEqual(state["attempts"][0]["comparison"], "not_improved")

    def test_data_file_proposals_never_execute_commands(self):
        runner = self.create()
        path = self.root / "proposal.json"
        tr.atomic_json(path, GOOD)
        state = runner.execute(tr.FileProposer([path]))
        self.assertEqual(state["status"], "HUMAN_REVIEW_REQUIRED")

    def test_human_change_request_requires_a_new_review_after_rework(self):
        runner = self.create()
        runner.execute(Proposals(GOOD))
        runner.human_review("human", runner.state["candidate_revision"], "CHANGES_REQUESTED", "review:rework")
        proposal = self.root / "rework.json"
        tr.atomic_json(proposal, GOOD)
        argv = ["task_runner", "retry", str(runner.directory), "--store", str(self.root / "runs"),
                "--proposal", str(proposal), "--feedback-ref", "review:rework"]
        with patch.object(sys, "argv", argv), patch.object(tr, "Sandbox", return_value=self.evaluator), patch("builtins.print"):
            self.assertEqual(tr.main(), 0)
        runs = list((self.root / "runs").iterdir())
        new = tr.Runner.load(next(p for p in runs if p != runner.directory), self.evaluator)
        self.assertEqual(new.state["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(new.state["review_state"], "UNREVIEWED")
        self.assertEqual(new.state["previous_run"], str(runner.directory))
        self.assertEqual(new.state["human_feedback_ref"], "review:rework")


class ProcessAndContractTests(unittest.TestCase):
    def test_timeout_and_output_limit_are_enforced(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(tr.Halt):
                tr.process([sys.executable, "-c", "import time; time.sleep(3)"], Path(d), .05)
            with self.assertRaises(tr.Halt):
                tr.process([sys.executable, "-c", "print('x'*2000000)"], Path(d), 5)

    def test_process_kills_detached_output_descendants(self):
        # A child retaining stdout must not hold a finished parent alive indefinitely.
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(tr.Halt):
                tr.process([sys.executable, "-c", "import os,time; p=os.fork(); time.sleep(3) if p==0 else None"], Path(d), .05)

    def test_invalid_paths_are_rejected(self):
        for p in ("../x", "/x", "./x", "a//b", "a/../b", "a\\b", ".git/config", "a/.codex/config"):
            with self.assertRaises(tr.Halt):
                tr.relative(p)

    def test_redaction_removes_environment_keys_and_personal_identifiers(self):
        with patch.dict(os.environ, {"TEST_API_KEY": "very-secret-value"}):
            text = tr.redact("very-secret-value person@example.org sk-test123456 password=abcdefgh")
        for value in ("very-secret-value", "person@example.org", "sk-test123456", "abcdefgh"):
            self.assertNotIn(value, text)

    def test_bubblewrap_is_networkless_read_only_and_has_no_host_home(self):
        with tempfile.TemporaryDirectory() as d:
            sandbox = tr.Sandbox()
            sandbox.binary = "/usr/bin/bwrap"
            command = sandbox.command(Path(d), ["python3", "test.py"], Path(d) / "empty")
            self.assertIn("--unshare-all", command)
            self.assertIn("--clearenv", command)
            self.assertNotIn("--bind", command)
            self.assertNotIn("--share-net", command)
            self.assertNotIn(str(Path.home()), command)
            self.assertNotIn("OPENAI_API_KEY", command)

    def test_single_writer_lock_is_exclusive(self):
        with tempfile.TemporaryDirectory() as d:
            with tr.locked(Path(d)):
                with self.assertRaises(tr.Halt):
                    with tr.locked(Path(d)):
                        pass


class RealSandboxTests(unittest.TestCase):
    """Real OS isolation, mandatory in CI; skip explicitly on unsupported hosts."""

    def setUp(self):
        RunnerTests.setUp(self)
        self.real = tr.Sandbox()
        runner = self.create(sandbox=self.real)
        try:
            self.real.check(runner.worktree, 10, runner.empty_git)
        except tr.Halt as exc:
            if os.environ.get("REQUIRE_RUNNER_SANDBOX") == "1":
                self.fail(str(exc))
            self.skipTest(str(exc))
        self.evaluator = self.real

    create = RunnerTests.create
    tearDown = RunnerTests.tearDown

    def test_actual_repair_preserves_source_and_requires_review(self):
        RunnerTests.test_passed_candidate_preserves_source_and_requires_human_review(self)

    def test_actual_failed_attempt_then_improvement(self):
        RunnerTests.test_valid_improvement_after_failed_attempt(self)

    def test_actual_sandbox_rejects_host_side_effects_and_network(self):
        runner = self.create()
        with socket.socket() as server:
            server.bind(("127.0.0.1", 0))
            server.listen()
            port = server.getsockname()[1]
            code, text = self.real.run(runner.worktree, ["python3", "-c", f'''
import os, socket
assert 'OPENAI_API_KEY' not in os.environ
assert open('/work/.git').read() == ''
try:
    open('/work/app.py', 'w')
except OSError:
    pass
else:
    raise AssertionError('source writable')
s = socket.socket()
s.settimeout(.2)
try:
    s.connect(('127.0.0.1', {port}))
except OSError:
    pass
else:
    raise AssertionError('host network reachable')
print('isolation: passed')
'''], 5, runner.empty_git)
        self.assertEqual(code, 0, text)
        self.assertIn("return 1", (runner.worktree / "app.py").read_text())


if __name__ == "__main__":
    unittest.main()
