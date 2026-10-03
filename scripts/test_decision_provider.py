#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "hooks"
if str(HOOKS) not in sys.path:
    sys.path.insert(0, str(HOOKS))

from decision_provider import (  # noqa: E402
    JevDecisionProvider,
    OffDecisionProvider,
    UnavailableDecisionProvider,
    completion_mode,
    context_mode,
    get_decision_provider,
)


class DecisionProviderSelectionTests(unittest.TestCase):
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

    def test_openai_provider_is_reserved_without_guessing_contract(self) -> None:
        env = {
            "FEATURE_MAP_DECISION_PROVIDER": "openai",
            "FEATURE_MAP_DECISION_CONTEXT_MODE": "metadata",
        }
        provider = get_decision_provider(env)
        self.assertIsInstance(provider, UnavailableDecisionProvider)
        result, warning = provider.context_decide("metadata", {}, "prompt", [])
        self.assertIsNone(result)
        self.assertIn("reserved", warning or "")

    def test_unknown_provider_fails_open(self) -> None:
        env = {
            "FEATURE_MAP_DECISION_PROVIDER": "other",
            "FEATURE_MAP_DECISION_COMPLETION_MODE": "metadata",
        }
        provider = get_decision_provider(env)
        result, warning = provider.completion_decide("metadata", {}, [], "", "", "")
        self.assertIsNone(result)
        self.assertIn("unknown provider", warning or "")


if __name__ == "__main__":
    unittest.main()
