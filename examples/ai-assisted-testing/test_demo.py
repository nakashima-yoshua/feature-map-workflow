"""Offline regression checks; no browser, external systems, or model API required."""

import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from run_demo import PUZZLE_NAME, run_scenario


class EvidenceDemoTests(unittest.TestCase):
    def test_http_to_db_and_evidence(self):
        with tempfile.TemporaryDirectory() as base:
            status, run_dir = run_scenario(output=Path(base))
            self.assertEqual("passed", status)
            result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
            self.assertEqual("passed", result["status"])
            self.assertEqual("UC-REGISTER", result["useCaseId"])
            self.assertEqual("TEST-REGISTER", result["verifyCaseId"])
            self.assertTrue(all(result["checks"].values()))
            self.assertEqual(PUZZLE_NAME, result["observed"][0]["name"])
            for path in ("before.json", "after.json", "diff.json", "application.log",
                         "operation.log"):
                self.assertTrue((run_dir / path).is_file(), path)
                self.assertIn(path, result["evidence"])

    def test_wrong_expectation_fails_without_changing_expected_value(self):
        with tempfile.TemporaryDirectory() as base:
            status, run_dir = run_scenario(output=Path(base), expected_name="NOT THE REAL NAME")
            self.assertEqual("failed", status)
            result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
            self.assertTrue(result["checks"]["registration_response"])
            self.assertFalse(result["checks"]["db_expected_state"])
            self.assertEqual("NOT THE REAL NAME", result["expected"][0]["name"])
            self.assertEqual(PUZZLE_NAME, result["observed"][0]["name"])

    def test_missing_feature_map_halts_before_creating_fixture(self):
        with tempfile.TemporaryDirectory() as base:
            with patch("run_demo.FEATURE_MAP", "missing-feature-map.xml"):
                with self.assertRaises(FileNotFoundError):
                    run_scenario(output=Path(base))
            self.assertEqual([], list(Path(base).iterdir()))

    def test_run_is_isolated_and_repeatable(self):
        with tempfile.TemporaryDirectory() as base:
            first, first_dir = run_scenario(output=Path(base))
            second, second_dir = run_scenario(output=Path(base))
            self.assertEqual(("passed", "passed"), (first, second))
            self.assertNotEqual(first_dir, second_dir)
            self.assertEqual(json.loads((first_dir / "after.json").read_text(encoding="utf-8")),
                             json.loads((second_dir / "after.json").read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
