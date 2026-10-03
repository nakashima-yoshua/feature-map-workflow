#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "feature-map-workflow" / "scripts" / "xquery_result.py"
SPEC = importlib.util.spec_from_file_location("feature_map_xquery_result", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

QueryResultContractError = MODULE.QueryResultContractError
parse_query_result = MODULE.parse_query_result


class QueryResultTests(unittest.TestCase):
    def test_success_value_from_mcp_text_content(self) -> None:
        payload = {
            "content": [
                {
                    "type": "text",
                    "text": '{"ok":true,"value":"R1","elapsedMs":4}',
                }
            ]
        }
        result = parse_query_result(payload)
        self.assertTrue(result.ok)
        self.assertEqual(result.value, "R1")
        self.assertEqual(result.elapsed_ms, 4)
        self.assertFalse(result.is_empty_sequence)

    def test_empty_sequence_is_success(self) -> None:
        result = parse_query_result('{"ok":true,"count":0,"elapsedMs":1}')
        self.assertTrue(result.ok)
        self.assertIsNone(result.value)
        self.assertEqual(result.count, 0)
        self.assertTrue(result.is_empty_sequence)

    def test_structured_error(self) -> None:
        result = parse_query_result(
            {
                "ok": False,
                "errors": [
                    {
                        "code": "XPST0003",
                        "message": "syntax error",
                        "line": 1,
                        "column": 8,
                        "sourceSnippet": "for $x in",
                        "specUrl": None,
                    }
                ],
            }
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.errors[0].code, "XPST0003")
        self.assertEqual(result.errors[0].line, 1)
        self.assertEqual(result.errors[0].source_snippet, "for $x in")

    def test_failure_without_errors_is_contract_failure(self) -> None:
        with self.assertRaises(QueryResultContractError):
            parse_query_result({"ok": False})

    def test_plain_non_json_text_is_contract_failure(self) -> None:
        with self.assertRaises(QueryResultContractError):
            parse_query_result({"content": [{"type": "text", "text": "not json"}]})


if __name__ == "__main__":
    unittest.main()
