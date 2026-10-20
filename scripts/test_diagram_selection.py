#!/usr/bin/env python3
"""Regression tests for purpose-driven, evidence-backed diagram selection."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPT = Path(__file__).resolve().parents[1] / "skills/feature-map-workflow/scripts/build_verification_brief.py"
spec = importlib.util.spec_from_file_location("build_verification_brief", SCRIPT)
brief = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = brief
spec.loader.exec_module(brief)


def diagram(kind: str, title: str, source: str) -> ET.Element:
    node = ET.Element("diagram", {"kind": kind, "title": title, "id": title})
    node.text = source
    return node


class DiagramSelectionTest(unittest.TestCase):
    def test_specific_roles_before_generic_flowchart(self):
        samples = {
            "データリネージ": "lineage",
            "CRUD matrix": "crud",
            "決定表": "decision",
            "トレーサビリティ": "traceability",
            "システムコンテキスト": "context",
            "コンポーネント": "component",
            "依存関係": "dependency",
            "配置図": "deployment",
            "タイミング図": "timing",
            "ジョブ依存": "batch",
            "データフロー": "data",
        }
        for name, role in samples.items():
            with self.subTest(name=name):
                self.assertEqual(brief.classify_diagram(diagram("flowchart", name, "flowchart LR\nA-->B")), role)
        self.assertEqual(brief.classify_diagram(diagram("flowchart", "通常の業務フロー", "flowchart TD\nA-->B")), "activity")
        self.assertEqual(brief.classify_diagram(diagram("er", "ER", "erDiagram\nA ||--o{ B : refs")), "er")

    def test_selects_only_existing_diagrams(self):
        root = ET.fromstring("""<featureMap>
          <sourceMap><ref kind="table" target="STOCK" access="read-write"/>
                     <ref kind="table" target="HISTORY" access="write"/></sourceMap>
          <diagrams>
            <diagram id="D1" kind="flowchart" title="UC-1 データリネージ">flowchart LR
A--&gt;B</diagram>
            <diagram id="D2" kind="flowchart" title="UC-2 データリネージ">flowchart LR
B--&gt;C</diagram>
            <diagram id="D3" kind="flowchart" title="UC-1 CRUD matrix">flowchart LR
A--&gt;C</diagram>
          </diagrams>
        </featureMap>""")
        focus = ET.Element("useCase", {"id": "UC-1"})
        case = ET.fromstring("<case type='normal'><condition>OK</condition><expect>出庫登録</expect></case>")
        chosen = brief.choose_diagrams(root, focus, [], [case])
        self.assertEqual([d.id for d in chosen], ["D1", "D3"])
        with self.assertRaisesRegex(ValueError, "Unknown or out-of-focus"):
            brief.choose_diagrams(root, focus, ["D2"], [case])

    def test_no_fabricated_diagrams(self):
        root = ET.fromstring("""<featureMap><sourceMap>
        <ref kind="table" target="STOCK" access="write"/>
        </sourceMap></featureMap>""")
        case = ET.fromstring("<case type='normal'><condition>通常</condition><expect>成功</expect></case>")
        self.assertEqual(brief.choose_diagrams(root, None, [], [case]), [])


if __name__ == "__main__":
    unittest.main()
