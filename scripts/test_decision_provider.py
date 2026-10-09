#!/usr/bin/env python3
from __future__ import annotations

import sys
import io
import json
import os
import tempfile
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
                   "FEATURE_MAP_DECISION_CONTEXT_MODE": "metadata", "FEATURE_MAP_DECISION_COMPLETION_MODE": "metadata"}
            with patch.dict(os.environ, env, clear=True), \
                    patch.object(feature_map_hook, "_find_feature_map", return_value=(feature_map, [feature_map])), \
                    patch.object(feature_map_hook, "_git_root", return_value=root), \
                    patch.object(feature_map_hook, "_load_state", return_value=state), \
                    patch.object(feature_map_hook, "_save_state"), \
                    patch.object(feature_map_hook, "_git_changed_files", return_value=["app.py"]), \
                    patch.object(feature_map_hook, "_git_diff_stat", return_value="private"), \
                    patch.object(feature_map_hook, "_emit") as emitted, \
                    patch("urllib.request.OpenerDirector.open", side_effect=[response1, response2]) as opening:
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


if __name__ == "__main__":
    unittest.main()
