#!/usr/bin/env python3
"""Check the public three-view example against the existing Feature Map contract."""

from __future__ import annotations

import unittest
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "fictional-stock-request" / "feature-map.xml"
XSD = ROOT / "skills" / "feature-map-workflow" / "assets" / "feature-map.xsd"
XSL = ROOT / "skills" / "feature-map-workflow" / "assets" / "feature-map.xsl"


class ThreeViewUnderstandingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = etree.parse(str(EXAMPLE), etree.XMLParser(resolve_entities=False, no_network=True))
        cls.schema = etree.XMLSchema(etree.parse(str(XSD)))
        cls.diagrams = cls.doc.findall("./diagrams/diagram")

    def test_example_uses_original_xsd_and_is_not_claimed_verified(self) -> None:
        self.assertTrue(self.schema.validate(self.doc), str(self.schema.error_log))
        root = self.doc.getroot()
        self.assertEqual("1.3", root.get("version"))
        self.assertEqual("draft", root.get("state"))
        self.assertEqual("catchup", root.get("mode"))
        self.assertTrue(root.findtext("./knowledge/constraint[@id='CON-FICTION']"))
        self.assertTrue(root.findtext("./open/item[@id='O-METADATA']"))
        self.assertTrue(all(c.get("status") == "not-run" for c in root.findall("./verify/case")))

    def test_three_views_share_use_case_and_db_names(self) -> None:
        root = self.doc.getroot()
        uc = root.find("./useCase")
        self.assertIsNotNone(uc)
        uc_id = uc.get("id")
        self.assertEqual("UC-SUBMIT", uc_id)
        self.assertEqual(
            [("DG-FLOW", "flowchart", "flowchart TD"),
             ("DG-DFD", "flowchart", "flowchart LR"),
             ("DG-ER", "er", "erDiagram")],
            [(d.get("id"), d.get("kind"), (d.text or "").strip().splitlines()[0])
             for d in self.diagrams],
        )
        for d in self.diagrams:
            self.assertIn(uc_id, d.get("title", ""))
        dfd, er = self.diagrams[1], self.diagrams[2]
        source_tables = {
            ref.get("target", "").replace("fictional:", "")
            for ref in root.findall("./sourceMap/ref[@kind='table']")
        }
        self.assertEqual({"ITEM", "REQUEST", "REQUEST_LINE"}, source_tables)
        for table in source_tables:
            self.assertIn(table, dfd.text)
            self.assertIn(table, er.text)
        self.assertIn("書込なし", dfd.text)
        self.assertIn("同一トランザクション", dfd.text)
        self.assertIn("FK", er.text)
        self.assertIn("PK", er.text)

    def test_existing_xslt_displays_all_three_in_collapsed_panel(self) -> None:
        xslt = etree.XSLT(etree.parse(str(XSL)))
        result = xslt(self.doc)
        markup = str(result)
        html = etree.HTML(markup)
        panel = html.xpath("//details[@id='diagrams-details']")
        self.assertEqual(1, len(panel))
        self.assertNotIn("open", panel[0].attrib)
        blocks = panel[0].xpath(".//pre[contains(concat(' ', normalize-space(@class), ' '), ' mermaid ')]")
        self.assertEqual(3, len(blocks))
        for expected, block in zip(("flowchart TD", "flowchart LR", "erDiagram"), blocks):
            self.assertTrue("".join(block.itertext()).strip().startswith(expected))
        for title in ("業務フロー", "データフロー", "ER図"):
            self.assertIn(title, markup)
        self.assertIn("addEventListener('toggle', startWhenOpened)", markup)
        self.assertIn("feature-map.mermaid.min.js", markup)
        self.assertIn("mermaid@12.0.0", markup)


if __name__ == "__main__":
    unittest.main()
