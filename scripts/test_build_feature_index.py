#!/usr/bin/env python3
"""Regression tests for the metadata-only Feature Map HTML directory."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

SCRIPT = (
    Path(__file__).resolve().parents[1] / "skills" / "feature-map-workflow"
    / "scripts" / "build_feature_index.py"
)


class FeatureIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "maps"
        self.root.mkdir()

    def map(self, rel: str, *, system: str = "Demo", feature: str = "Import",
            purpose: str = "Read records", state: str = "ready") -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        doc = ET.Element("featureMap", version="1.3", mode="change", state=state)
        meta = ET.SubElement(doc, "meta")
        ET.SubElement(meta, "system").text = system
        ET.SubElement(meta, "feature").text = feature
        goal = ET.SubElement(doc, "goal")
        ET.SubElement(goal, "purpose").text = purpose
        refs = ET.SubElement(doc, "sourceMap")
        ET.SubElement(refs, "ref", kind="entry", target="example:entry")
        knowledge = ET.SubElement(doc, "knowledge")
        ET.SubElement(knowledge, "rule").text = "Do not copy full rule content to index"
        path.write_bytes(ET.tostring(doc, encoding="utf-8", xml_declaration=True))
        return path

    def build(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), *args],
            capture_output=True, text=True, timeout=15,
        )

    def test_metadata_only_sorted_and_relative_encoded_links(self) -> None:
        special = self.map("在庫 & テスト/feature-map.xml", system="Beta",
                           feature="<img src=x onerror=alert(1)>", purpose="A & B")
        self.map("alpha/feature-map.xml", system="Alpha", feature="Overview")
        self.map(".git/hidden/feature-map.xml", feature="Excluded")
        self.map("dist/hidden/feature-map.xml", feature="Excluded")
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        output = (self.root / "feature-map-index.html").read_text(encoding="utf-8")
        self.assertIn("2 features", output)
        self.assertLess(output.index("Alpha"), output.index("Beta"))
        self.assertIn(quote(special.relative_to(self.root).as_posix(), safe="/"), output)
        self.assertIn("&lt;img", output)
        self.assertNotIn("<img", output)
        self.assertIn("A &amp; B", output)
        self.assertNotIn("Do not copy full rule content to index", output)
        self.assertNotIn("Excluded", output)

    def test_requires_force_for_regeneration(self) -> None:
        path = self.map("one/feature-map.xml")
        self.assertEqual(self.build().returncode, 0)
        first = (self.root / "feature-map-index.html").read_text(encoding="utf-8")
        self.assertNotEqual(self.build().returncode, 0)
        self.assertEqual(first, (self.root / "feature-map-index.html").read_text(encoding="utf-8"))
        self.map("one/feature-map.xml", feature="Updated")
        self.assertEqual(self.build("--force").returncode, 0)
        self.assertIn("Updated", (self.root / "feature-map-index.html").read_text(encoding="utf-8"))
        self.assertTrue(path.exists())

    def test_failure_does_not_overwrite_previous_index(self) -> None:
        self.map("one/feature-map.xml")
        self.assertEqual(self.build().returncode, 0)
        output = self.root / "feature-map-index.html"
        before = output.read_bytes()
        invalid = self.root / "two" / "feature-map.xml"
        invalid.parent.mkdir()
        invalid.write_text("<featureMap>", encoding="utf-8")
        result = self.build("--force")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("two/feature-map.xml", result.stderr.replace("\\", "/"))
        self.assertEqual(before, output.read_bytes())

    def test_rejects_empty_root_and_output_outside_root(self) -> None:
        self.assertNotEqual(self.build().returncode, 0)
        self.map("one/feature-map.xml")
        result = self.build("--output", "../elsewhere.html")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root.parent / "elsewhere.html").exists())

    def test_rejects_doctype(self) -> None:
        self.map("one/feature-map.xml")
        external = self.root / "two" / "feature-map.xml"
        external.parent.mkdir()
        external.write_text(
            '<!DOCTYPE featureMap [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
            '<featureMap>&x;</featureMap>', encoding="utf-8",
        )
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DOCTYPE", result.stderr)


if __name__ == "__main__":
    unittest.main()
