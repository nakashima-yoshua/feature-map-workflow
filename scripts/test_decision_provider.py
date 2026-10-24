#!/usr/bin/env python3
from __future__ import annotations

import sys
import io
import json
import os
import tempfile
import copy
import urllib.error
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "hooks"
if str(HOOKS) not in sys.path:
    sys.path.insert(0, str(HOOKS))

import feature_map_hook  # noqa: E402
from decision_provider import (  # noqa: E402
    JevDecisionProvider,
    OffDecisionProvider,
    OpenAIDecisionsProvider,
    UnavailableDecisionProvider,
    completion_mode,
    context_mode,
    get_decision_provider,
)


class HookContextReuseTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.map = self.root / "feature-map.xml"
        self.map.write_text('<featureMap><meta><feature>F</feature></meta>'
                            '<goal><scope>S</scope><exclude>X</exclude></goal></featureMap>', encoding="utf-8")
        self.state = {}
        self.emissions = []
        patches = [
            patch.object(feature_map_hook, "_find_feature_map", return_value=(self.map, [self.map])),
            patch.object(feature_map_hook, "_git_root", return_value=self.root),
            patch.object(feature_map_hook, "_run", return_value="fixture-revision"),
            patch.object(feature_map_hook, "_git_changed_files", return_value=[]),
            patch.object(feature_map_hook, "get_decision_provider", return_value=OffDecisionProvider()),
            patch.object(feature_map_hook, "_load_state", side_effect=lambda _: copy.deepcopy(self.state)),
            patch.object(feature_map_hook, "_save_state", side_effect=self.save),
            patch.object(feature_map_hook, "_emit", side_effect=self.emissions.append),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def save(self, _, state):
        self.state = copy.deepcopy(state)

    def prompt(self, **extra):
        event = dict(cwd=str(self.root), session_id="fixture", prompt="Inspect selected feature")
        event.update(extra)
        feature_map_hook._handle_user_prompt(event)
        return self.emissions[-1]["hookSpecificOutput"]["additionalContext"]

    def test_first_and_repeat_preserve_a_safety_kernel(self):
        first = self.prompt()
        repeat = self.prompt()
        self.assertIn("1) Reuse conversation", first)
        self.assertNotIn("1) Reuse conversation", repeat)
        for guarantee in ("scope", "authority", "acceptance", "local evidence", "one question", "no authority"):
            self.assertIn(guarantee, repeat)
        self.assertLess(len(repeat.encode()), len(first.encode()))

    def test_lifecycle_events_invalidate_repeat_cache(self):
        for source in ("startup", "resume", "compact", "clear"):
            with self.subTest(source=source):
                self.prompt()
                feature_map_hook._handle_session_start(dict(cwd=str(self.root), session_id="fixture", source=source))
                self.assertIn("1) Reuse conversation", self.prompt())

    def test_unknown_or_lost_state_never_suppresses_full_policy(self):
        for sid in ("", "unknown"):
            self.assertIn("1) Reuse conversation", self.prompt(session_id=sid))
            self.assertIn("1) Reuse conversation", self.prompt(session_id=sid))
        self.prompt()
        self.state = {}
        self.assertIn("1) Reuse conversation", self.prompt())

    def test_target_content_and_policy_changes_reinsert(self):
        self.prompt()
        self.map.write_text(self.map.read_text(encoding="utf-8").replace("<scope>S", "<scope>NEW"), encoding="utf-8")
        self.assertIn("Feature Map scope: NEW", self.prompt())
        self.prompt()
        with patch.object(feature_map_hook, "CONTEXT_POLICY", feature_map_hook.CONTEXT_POLICY + "\nPolicy revision."):
            self.assertIn("Policy revision.", self.prompt())
        self.prompt()
        with patch.object(feature_map_hook, "_run", return_value="different-revision"):
            self.assertIn("1) Reuse conversation", self.prompt())
        self.assertIn("1) Reuse conversation", self.prompt(cwd=str(self.root / "different-target")))

    def test_repeat_keeps_new_warning_and_ambiguity_signals(self):
        self.prompt()
        repeat = self.prompt(prompt="本番の権限を変更")
        self.assertIn("authority", repeat)
        self.assertIn("Local ambiguity signals", repeat)
        rendered = feature_map_hook._context_gate_context("", {}, [], None, "Provider unavailable", include_policy=False)
        self.assertIn("Provider unavailable", rendered)
        self.assertIn("no authority", rendered)

    def test_parse_failure_or_ambiguous_target_is_not_cached(self):
        self.prompt()
        self.map.write_text("<broken", encoding="utf-8")
        self.assertIn("1) Reuse conversation", self.prompt())
        self.assertIn("1) Reuse conversation", self.prompt())
        with patch.object(feature_map_hook, "_find_feature_map", return_value=(None, [self.map, self.root / "other.xml"])):
            self.assertIn("1) Reuse conversation", self.prompt())
            self.assertIn("1) Reuse conversation", self.prompt())

    def test_lost_persistence_and_failed_emission_do_not_mark_policy_delivered(self):
        with patch.object(feature_map_hook, "_save_state"):
            self.assertIn("1) Reuse conversation", self.prompt())
            self.assertIn("1) Reuse conversation", self.prompt())
        with patch.object(feature_map_hook, "_emit", side_effect=OSError("closed pipe")):
            with self.assertRaises(OSError):
                self.prompt()
        self.assertIn("1) Reuse conversation", self.prompt())


class DecisionProviderSelectionTests(unittest.TestCase):
    def test_hook_context_helpers_are_available(self) -> None:
        signals = feature_map_hook._context_gate_signals("関連箇所を適宜変更")
        self.assertTrue(signals)
        rendered = feature_map_hook._context_gate_context(
            "",
            {},
            signals,
            {
                "provider": "test",
                "question_required": 0.90,
                "missing_context_type": "scope",
            },
            None,
        )
        self.assertIn("test advisory: clarification likely required", rendered)

    def test_default_is_off(self) -> None:
        provider = get_decision_provider({})
        self.assertIsInstance(provider, OffDecisionProvider)
        self.assertEqual("off", context_mode(provider.name, {}))
        self.assertEqual("off", completion_mode(provider.name, {}))

    def test_legacy_jev_configuration_selects_jev(self) -> None:
        env = {"FEATURE_MAP_JEV_MODE": "metadata"}
        provider = get_decision_provider(env)
        self.assertIsInstance(provider, JevDecisionProvider)
        self.assertEqual("metadata", completion_mode(provider.name, env))

    def test_generic_modes_override_legacy_modes(self) -> None:
        env = {
            "FEATURE_MAP_DECISION_PROVIDER": "jev",
            "FEATURE_MAP_DECISION_CONTEXT_MODE": "prompt",
            "FEATURE_MAP_DECISION_COMPLETION_MODE": "summary",
            "FEATURE_MAP_CONTEXT_JEV_MODE": "off",
            "FEATURE_MAP_JEV_MODE": "off",
        }
        provider = get_decision_provider(env)
        self.assertIsInstance(provider, JevDecisionProvider)
        self.assertEqual("prompt", context_mode(provider.name, env))
        self.assertEqual("summary", completion_mode(provider.name, env))

    def test_legacy_context_mode_selects_jev(self) -> None:
        env = {"FEATURE_MAP_CONTEXT_JEV_MODE": "metadata"}
        provider = get_decision_provider(env)
        self.assertIsInstance(provider, JevDecisionProvider)
        self.assertEqual("metadata", context_mode(provider.name, env))

    def test_openai_provider_does_not_require_jev_credentials(self) -> None:
        env = {
            "FEATURE_MAP_DECISION_PROVIDER": "openai",
            "FEATURE_MAP_DECISION_CONTEXT_MODE": "metadata",
        }
        provider = get_decision_provider(env)
        self.assertIsInstance(provider, OpenAIDecisionsProvider)
        result, warning = provider.context_decide("metadata", {}, "prompt", [])
        self.assertIsNone(result)
        self.assertIn("OPENAI_API_KEY", warning or "")

    def test_unknown_provider_fails_open(self) -> None:
        env = {
            "FEATURE_MAP_DECISION_PROVIDER": "other",
            "FEATURE_MAP_DECISION_COMPLETION_MODE": "metadata",
        }
        provider = get_decision_provider(env)
        result, warning = provider.completion_decide("metadata", {}, [], "", "", "")
        self.assertIsNone(result)
        self.assertIn("unknown provider", warning or "")


class OpenAIDecisionsTests(unittest.TestCase):
    def setUp(self):
        self.provider = OpenAIDecisionsProvider({"OPENAI_API_KEY": "sk-test-secret123"})
        self.context_answers = [
            {"name": "context_sufficient", "type": "predicate", "probability": 0.9},
            {"name": "question_required", "type": "predicate", "probability": 0.1},
            {"name": "missing_context_type", "type": "choice", "choice": "none", "confidence": 0.8},
        ]

    def call(self, answers, completion=False):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"answers": answers, "model": "gpt-6-luna"}).encode()
        with patch("urllib.request.OpenerDirector.open", return_value=response) as opening:
            if completion:
                result = self.provider.completion_decide("metadata", {}, ["private/path"], "secret", "secret", "secret")
            else:
                result = self.provider.context_decide("metadata", {"purpose": "secret", "feature": "secret"}, "secret", [])
            request = opening.call_args.args[0]
        return result, json.loads(request.data), request

    def test_context_normalizes_named_answers_and_official_contract(self):
        (result, warning), payload, req = self.call(list(reversed(self.context_answers)))
        self.assertIsNone(warning)
        self.assertEqual(result["question_required"], 0.1)
        self.assertEqual(result["missing_context_confidence"], 0.8)
        self.assertEqual(req.full_url, "https://api.openai.com/v1/decisions")
        self.assertEqual(payload["model"], "gpt-6-luna")
        self.assertNotIn("state", payload)
        self.assertIsInstance(payload["input"], str)
        self.assertNotIn("secret", payload["input"])
        self.assertEqual(payload["questions"][0]["type"], "predicate")
        self.assertIn("choices", payload["questions"][2])
        self.assertNotIn("criteria", payload["questions"][2])

    def test_completion_uses_hook_compatible_names_without_source_metadata(self):
        answers = [
            {"name": "update_required", "type": "predicate", "probability": .7},
            {"name": "update_section", "type": "choice", "choice": "rule", "confidence": .8},
            {"name": "human_review_required", "type": "predicate", "probability": .9},
        ]
        (result, warning), payload, _ = self.call(answers, completion=True)
        self.assertIsNone(warning)
        self.assertEqual(result["human_review_required"], .9)
        self.assertEqual(result["update_section"], "rule")
        self.assertNotIn("private", payload["input"])
        self.assertNotIn("secret", payload["input"])

    def test_off_and_invalid_modes_never_open_network(self):
        with patch("urllib.request.OpenerDirector.open") as opening:
            for mode in ("off", "typo", "diff"):
                self.assertEqual((None, None), self.provider.context_decide(mode, {}, "text", []))
            for mode in ("off", "typo", "prompt"):
                self.assertEqual((None, None), self.provider.completion_decide(mode, {}, [], "", "", ""))
            opening.assert_not_called()

    def test_refusal_missing_duplicate_and_unexpected_answers_are_undetermined(self):
        bad = [self.context_answers[:-1], self.context_answers + [self.context_answers[0]],
               [{"name": "context_sufficient", "type": "refusal"}] + self.context_answers[1:],
               self.context_answers + [{"name": "extra", "type": "predicate", "probability": .2}]]
        for answers in bad:
            with self.subTest(answers=answers):
                (result, warning), _, _ = self.call(answers)
                self.assertIsNone(result)
                self.assertIn("undetermined", warning)

    def test_invalid_numeric_values_and_unknown_choices_are_not_false_evidence(self):
        for value in (None, "0.9", True, -1, 1.1, float("nan"), float("inf")):
            answers = [dict(a) for a in self.context_answers]
            answers[0]["probability"] = value
            (result, _), _, _ = self.call(answers)
            self.assertIsNone(result)
        answers = [dict(a) for a in self.context_answers]
        answers[2]["choice"] = "APPROVED"
        (result, _), _, _ = self.call(answers)
        self.assertIsNone(result)

    def test_transport_failures_hide_key_body_and_exception_text(self):
        errors = [TimeoutError("sk-test-secret123"), urllib.error.URLError("private prompt")]
        errors += [urllib.error.HTTPError("url", code, "secret reason", {}, io.BytesIO(b"secret body"))
                   for code in (301, 401, 403, 429, 500, 503)]
        for error in errors:
            with patch("urllib.request.OpenerDirector.open", side_effect=error):
                result, warning = self.provider.context_decide("metadata", {}, "", [])
            self.assertIsNone(result)
            self.assertNotIn("secret", warning)
            self.assertNotIn("private", warning)

    def test_malformed_json_and_response_shape(self):
        for raw in (b"not json", b"[]", b'{"answers":{}}', b"x" * 65537):
            response = MagicMock()
            response.__enter__.return_value.read.return_value = raw
            with patch("urllib.request.OpenerDirector.open", return_value=response):
                result, warning = self.provider.context_decide("metadata", {}, "", [])
            self.assertIsNone(result)
            self.assertIn("undetermined", warning)

    def test_opt_in_content_is_capped_and_redacted(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({"answers": self.context_answers}).encode()
        with patch("urllib.request.OpenerDirector.open", return_value=response) as opening:
            self.provider.context_decide("prompt", {}, "sk-test-secret123 person@example.org " + "a" * 4000, [])
        state = json.loads(json.loads(opening.call_args.args[0].data)["input"])
        self.assertNotIn("sk-test", state["prompt"])
        self.assertNotIn("person@example.org", state["prompt"])
        self.assertLessEqual(len(state["prompt"]), 3000)

    def test_legacy_modes_are_not_inherited_by_openai(self):
        env = {"FEATURE_MAP_DECISION_PROVIDER": "openai", "FEATURE_MAP_JEV_MODE": "diff",
               "FEATURE_MAP_CONTEXT_JEV_MODE": "prompt"}
        provider = get_decision_provider(env)
        self.assertEqual(context_mode(provider.name, env), "off")
        self.assertEqual(completion_mode(provider.name, env), "off")

    def test_both_real_hook_call_sites_use_normalized_openai_advice(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            feature_map = root / "feature-map.xml"
            feature_map.write_text('<featureMap version="1.3" mode="change" state="ready">'
                '<meta><system>fixture</system><feature>fixture</feature></meta>'
                '<goal><purpose>fixture</purpose></goal><sourceMap><ref kind="entry" target="app.py"/></sourceMap></featureMap>')
            state = {"feature_map_hash_start": feature_map_hook._xml_canonical_hash(feature_map)}
            completion = [
                {"name": "update_required", "type": "predicate", "probability": .2},
                {"name": "update_section", "type": "choice", "choice": "none", "confidence": .8},
                {"name": "human_review_required", "type": "predicate", "probability": .9}]
            response1, response2 = MagicMock(), MagicMock()
            response1.__enter__.return_value.read.return_value = json.dumps({"answers": self.context_answers}).encode()
            response2.__enter__.return_value.read.return_value = json.dumps({"answers": completion}).encode()
            env = {"FEATURE_MAP_DECISION_PROVIDER": "openai", "OPENAI_API_KEY": "synthetic-test-key",
                   "FEATURE_MAP_DECISION_CONTEXT_MODE": "metadata", "FEATURE_MAP_DECISION_COMPLETION_MODE": "metadata",
                   "FEATURE_MAP_DECISION_POLICY": "advisory"}
            with patch.dict(os.environ, env, clear=True), \
                    patch.object(feature_map_hook, "_find_feature_map", return_value=(feature_map, [feature_map])), \
                    patch.object(feature_map_hook, "_git_root", return_value=root), \
                    patch.object(feature_map_hook, "_load_state", return_value=state), \
                    patch.object(feature_map_hook, "_save_state"), \
                    patch.object(feature_map_hook, "_git_changed_files", return_value=["app.py"]), \
                    patch.object(feature_map_hook, "_git_diff_stat", return_value="private"), \
                    patch.object(feature_map_hook, "_emit") as emitted, \
                    patch("urllib.request.build_opener", return_value=MagicMock(
                        open=MagicMock(side_effect=[response1, response2]))) as opener_factory:
                opening = opener_factory.return_value.open
                (root / ".git").mkdir()
                event = {"cwd": str(root), "session_id": "fixture", "prompt": "関連箇所を適宜変更"}
                feature_map_hook._handle_user_prompt(event)
                self.assertEqual(state["last_context_decision"]["provider"], "openai")
                feature_map_hook._handle_stop(event)
                self.assertEqual(state["last_decision"]["provider"], "openai")
                self.assertTrue(emitted.call_args.args[0]["continue"])
                self.assertIn("human review", emitted.call_args.args[0]["systemMessage"])
                self.assertEqual(opening.call_count, 2)
                # A required local gate precedes (and cannot be overridden by) advisory API calls.
                feature_map.write_text(feature_map.read_text().replace('state="ready"', 'state="verified"').replace(
                    '</featureMap>', '<open><item impact="high" next="Ask human">unknown</item></open></featureMap>'))
                feature_map_hook._handle_stop(event)
                self.assertEqual(emitted.call_args.args[0]["decision"], "block")
                self.assertEqual(opening.call_count, 2)

    def test_jev_response_compatibility_is_preserved(self):
        provider = JevDecisionProvider({"TYPESAFE_API_KEY": "synthetic"})
        with patch.object(provider, "_request", return_value=({"model": "jev-latest", "answers": {
            "context_sufficient": {"noul": .9}, "question_required": {"noul": .1},
            "missing_context_type": {"choice": "none", "confidence": .8}}}, None)):
            result, warning = provider.context_decide("metadata", {}, "text", [])
        self.assertEqual(result["question_required"], .1)
        self.assertEqual(result["provider"], "jev")
        self.assertIsNone(warning)


class PhaseAdviceTests(unittest.TestCase):
    def setUp(self):
        self.env = {"OPENAI_API_KEY": "synthetic-key", "FEATURE_MAP_DECISION_PROVIDER": "openai",
                    "FEATURE_MAP_DECISION_PHASE_MODE": "prompt"}
        self.phase = {"name": "current_phase", "type": "choice", "choice": "implementation_ci", "confidence": .9}

    def request(self, env=None, mode="off", answers=None, summary=None):
        provider = OpenAIDecisionsProvider(self.env if env is None else env)
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"answers": [self.phase] if answers is None else answers}).encode()
        with patch("urllib.request.OpenerDirector.open", return_value=response) as opening:
            result = provider.context_decide(mode, summary or {}, "Implement person@example.org", [])
        payload = json.loads(opening.call_args.args[0].data) if opening.called else None
        return result, payload, opening

    def test_phase_is_separate_opt_in_and_defaults_to_no_network(self):
        for mode in (None, "off", "metadata", "typo"):
            env = dict(self.env)
            if mode is None:
                env.pop("FEATURE_MAP_DECISION_PHASE_MODE")
            else:
                env["FEATURE_MAP_DECISION_PHASE_MODE"] = mode
            (result, warning), _, opening = self.request(env)
            self.assertIsNone(result)
            self.assertIsNone(warning)
            opening.assert_not_called()

    def test_phase_only_request_is_redacted_and_not_an_approval(self):
        (result, warning), payload, _ = self.request(summary={"purpose": "synthetic goal", "scope": "a" * 2000})
        self.assertIsNone(warning)
        self.assertEqual("implementation_ci", result["current_phase"])
        self.assertEqual(.9, result["current_phase_confidence"])
        self.assertEqual(["current_phase"], [q["name"] for q in payload["questions"]])
        state = json.loads(payload["input"])
        self.assertNotIn("person@example.org", state["prompt"])
        self.assertLessEqual(len(state["feature_context"]["scope"]), 1000)
        choices = {c["value"] for c in payload["questions"][0]["choices"]}
        self.assertEqual(13, len(choices))  # 12 existing phases plus unknown.
        self.assertNotIn("APPROVED", choices)

    def test_context_and_phase_are_batched_with_distinct_confidence(self):
        context = OpenAIDecisionsTests()
        context.setUp()
        (result, warning), payload, opening = self.request(mode="prompt", answers=context.context_answers + [self.phase])
        self.assertIsNone(warning)
        self.assertEqual(.8, result["missing_context_confidence"])
        self.assertEqual(.9, result["current_phase_confidence"])
        self.assertEqual(4, len(payload["questions"]))
        self.assertEqual(1, opening.call_count)

    def test_unknown_low_confidence_and_stale_phase_are_not_routing_facts(self):
        for choice, confidence in (("unknown", .99), ("implementation_ci", .2)):
            decision = {"provider": "openai", "current_phase": choice, "current_phase_confidence": confidence}
            rendered = feature_map_hook._context_gate_context("", {}, [], decision, None)
            self.assertNotIn("phase candidate:", rendered)
        with tempfile.TemporaryDirectory() as directory:
            state = {"last_context_decision": {"current_phase": "requirements"}}
            with patch.dict(os.environ, {}, clear=True), \
                    patch.object(feature_map_hook, "_find_feature_map", return_value=(None, [])), \
                    patch.object(feature_map_hook, "_load_state", return_value=state), \
                    patch.object(feature_map_hook, "_save_state"), patch.object(feature_map_hook, "_emit"):
                feature_map_hook._handle_user_prompt({"cwd": directory, "prompt": "plain request"})
            self.assertNotIn("last_context_decision", state)

    def test_phase_opt_in_runs_for_unambiguous_prompt_and_observe_does_not_route(self):
        with tempfile.TemporaryDirectory() as directory:
            state = {}
            response = MagicMock()
            response.__enter__.return_value.read.return_value = json.dumps({"answers": [self.phase]}).encode()
            with patch.dict(os.environ, self.env, clear=True), \
                    patch.object(feature_map_hook, "_find_feature_map", return_value=(None, [])), \
                    patch.object(feature_map_hook, "_load_state", return_value=state), \
                    patch.object(feature_map_hook, "_save_state"), patch.object(feature_map_hook, "_emit") as emit, \
                    patch("urllib.request.build_opener", return_value=MagicMock(
                        open=MagicMock(return_value=response))) as opener_factory:
                opening = opener_factory.return_value.open
                feature_map_hook._handle_user_prompt({"cwd": directory, "prompt": "Implement fixture"})
            self.assertEqual(1, opening.call_count)
            self.assertEqual("implementation_ci", state["last_context_decision"]["current_phase"])
            self.assertNotIn("phase candidate:", emit.call_args.args[0]["hookSpecificOutput"]["additionalContext"])

    def test_advisory_phase_is_only_a_candidate(self):
        with patch.dict(os.environ, {"FEATURE_MAP_DECISION_POLICY": "advisory"}, clear=True):
            rendered = feature_map_hook._context_gate_context("", {}, [],
                {"provider": "openai", "current_phase": "implementation_ci", "current_phase_confidence": .9}, None)
        self.assertIn("phase candidate: implementation_ci", rendered)
        self.assertIn("not phase completion", rendered)

    def test_timeout_is_bounded_and_invalid_value_falls_back(self):
        for value, expected in (("1.5", 1.5), ("nan", 2.0), ("99", 2.0), ("0", 2.0), ("bad", 2.0)):
            env = dict(self.env, FEATURE_MAP_DECISION_TIMEOUT_SECONDS=value)
            _, _, opening = self.request(env)
            self.assertEqual(expected, opening.call_args.kwargs["timeout"])

    def test_observe_policy_never_weakens_local_gate(self):
        self.assertEqual("observe", feature_map_hook.decision_policy("openai", {}))
        self.assertEqual("observe", feature_map_hook.decision_policy("openai", {"FEATURE_MAP_DECISION_POLICY": "typo"}))
        self.assertEqual("advisory", feature_map_hook.decision_policy("jev", {}))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            fmap = root / "feature-map.xml"
            fmap.write_text('<featureMap state="ready"><sourceMap><ref kind="entry" target="app.py"/></sourceMap></featureMap>', encoding="utf-8")
            state = {"feature_map_hash_start": feature_map_hook._xml_canonical_hash(fmap)}
            provider = OpenAIDecisionsProvider(self.env)
            advice = {"provider": "openai", "update_required": 1.0, "update_section": "rule", "human_review_required": 1.0}
            with patch.dict(os.environ, {"FEATURE_MAP_DECISION_COMPLETION_MODE": "metadata"}, clear=True), \
                    patch.object(feature_map_hook, "get_decision_provider", return_value=provider), \
                    patch.object(provider, "completion_decide", return_value=(advice, None)) as decide, \
                    patch.object(feature_map_hook, "_find_feature_map", return_value=(fmap, [fmap])), \
                    patch.object(feature_map_hook, "_git_root", return_value=root), \
                    patch.object(feature_map_hook, "_load_state", return_value=state), \
                    patch.object(feature_map_hook, "_save_state"), \
                    patch.object(feature_map_hook, "_git_changed_files", return_value=["app.py"]), \
                    patch.object(feature_map_hook, "_git_diff_stat", return_value=""), \
                    patch.object(feature_map_hook, "_emit") as emit:
                feature_map_hook._handle_stop({"cwd": directory})
                self.assertEqual({"continue": True}, emit.call_args.args[0])
                self.assertEqual(advice, state["last_decision"])
                # Conflicting independent answers cannot invent a target section.
                advice["update_section"] = "none"
                with patch.dict(os.environ, {"FEATURE_MAP_DECISION_POLICY": "advisory"}):
                    feature_map_hook._handle_stop({"cwd": directory})
                    self.assertTrue(emit.call_args.args[0]["continue"])
                advice["update_section"] = "rule"
                fmap.write_text('<featureMap state="verified"><open><item impact="high">unknown</item></open></featureMap>', encoding="utf-8")
                feature_map_hook._handle_stop({"cwd": directory})
                self.assertEqual("block", emit.call_args.args[0]["decision"])
                self.assertEqual(2, decide.call_count)

    def test_phase_refusal_unknown_choice_and_invalid_confidence_are_undetermined(self):
        for changes in ({"type": "refusal"}, {"choice": "APPROVED"}, {"confidence": float("nan")}, {"confidence": True}):
            (result, warning), _, _ = self.request(answers=[dict(self.phase, **changes)])
            self.assertIsNone(result)
            self.assertIn("undetermined", warning)


if __name__ == "__main__":
    unittest.main()
