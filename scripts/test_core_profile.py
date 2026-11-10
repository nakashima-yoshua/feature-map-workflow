#!/usr/bin/env python3
"""Smoke-test the standalone Core path: init, XSD, HTML and index; no Docker/AI."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "feature-map-workflow" / "scripts"


class StandaloneCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.maps = self.root / "maps"
        self.map = self.maps / "sample" / "feature-map.xml"
        self.run_tool(
            "init_feature_map.py",
            "--system", "Demo",
            "--feature", "Sample",
            "--mode", "catchup",
            "--purpose", "Understand a business feature",
            "--output", str(self.map),
        )

    def run_tool(self, name: str, *args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / name), *args],
            cwd=ROOT, capture_output=True, text=True, timeout=20,
        )
        return result

    def test_standalone_entry_links_resolve(self) -> None:
        # The supported project-local Skill snapshot must not depend on a
        # neighboring checkout for its core entrypoint references.
        installed = self.root / "project" / ".agents" / "skills" / "feature-map-workflow"
        shutil.copytree(ROOT / "skills" / "feature-map-workflow", installed,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.assertEqual((ROOT / "docs/scope-and-boundaries.md").read_bytes(),
                         (installed / "references/scope-and-boundaries.md").read_bytes())
        markdown = list(installed.rglob("*.md"))
        self.assertTrue(markdown)
        for document in markdown:
            links = re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", document.read_text(encoding="utf-8"))
            for link in links:
                if "://" in link or link.startswith("mailto:"):
                    continue
                with self.subTest(document=document.relative_to(installed), link=link):
                    self.assertTrue((document.parent / link).is_file(), link)

    def test_review_is_conditioned_on_actual_risk(self) -> None:
        references = ROOT / "skills/feature-map-workflow/references"
        lifecycle = (references / "development-lifecycle.md").read_text(encoding="utf-8")
        review = (references / "code-review.md").read_text(encoding="utf-8")
        self.assertNotIn("use the existing independent revision-bound diff review", lifecycle)
        self.assertIn("independent review when material risk", lifecycle)
        self.assertIn("human decision where required by existing rules", review)

    def test_configured_standards_remain_connected(self) -> None:
        references = ROOT / "skills/feature-map-workflow/references"
        contract = (references / "workspace-profile-contract.md").read_text(encoding="utf-8")
        workflow = (references / "unified-development.md").read_text(encoding="utf-8")
        self.assertIn("standards.common_skill", contract)
        self.assertIn("authoritative-source-model.md", workflow)
        self.assertIn("database-change-lifecycle.md", workflow)

    def test_init_validate_render_and_index(self) -> None:
        self.assertTrue(self.map.is_file())
        self.assertTrue(self.map.with_name("feature-map.xsd").is_file())
        self.assertTrue(self.map.with_name("feature-map.xsl").is_file())

        result = self.run_tool("validate_feature_map.py", str(self.map))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("VALID:", result.stdout)

        source = etree.parse(str(self.map))
        render = etree.XSLT(etree.parse(str(self.map.with_name("feature-map.xsl"))))
        html = str(render(source))
        self.assertIn("Demo", html)
        self.assertIn("Sample", html)
        self.assertIn("Understand a business feature", html)

        result = self.run_tool("build_feature_index.py", "--root", str(self.maps))
        self.assertEqual(0, result.returncode, result.stderr)
        index = (self.maps / "feature-map-index.html").read_text(encoding="utf-8")
        self.assertIn("1 features", index)
        self.assertIn("Sample", index)
        self.assertIn("sample/feature-map.xml", index)

    def test_invalid_schema_is_rejected(self) -> None:
        source = etree.parse(str(self.map))
        meta = source.getroot().find("meta")
        self.assertIsNotNone(meta)
        source.getroot().remove(meta)
        source.write(str(self.map), encoding="utf-8", xml_declaration=True)
        result = self.run_tool("validate_feature_map.py", str(self.map))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("INVALID:", result.stderr)

    def test_doctype_is_rejected(self) -> None:
        source = self.map.read_text(encoding="utf-8")
        source = source.replace(
            "?>", "?>\n<!DOCTYPE featureMap [<!ENTITY unsafe \"test\">]>", 1,
        )
        self.map.write_text(source, encoding="utf-8")
        result = self.run_tool("validate_feature_map.py", str(self.map))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("DOCTYPE is not permitted", result.stderr)


if __name__ == "__main__":
    unittest.main()
