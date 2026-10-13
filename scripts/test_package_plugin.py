#!/usr/bin/env python3
"""Inspect real plugin ZIPs built from disposable, synthetic trees."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


class PackagePluginTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "scripts").mkdir()
        self.packager = self.root / "scripts" / "package_plugin.py"
        shutil.copy2(Path(__file__).with_name("package_plugin.py"), self.packager)
        self.expected_files = {
            "plugin.json": '{"name": "synthetic-plugin"}\n',
            "README.md": "Synthetic package fixture\n",
            "skills/example/SKILL.md": "Synthetic skill\n",
            "docs/local-test-evidence-guide.md": "Keep similar file names\n",
            "test-results-guide/example.txt": "Keep similar directory names\n",
        }
        for rel, content in self.expected_files.items():
            self.write_file(rel, content)

    def write_file(self, rel: str, content: str = "synthetic evidence\n") -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf-8"))

    def package(self) -> list[str]:
        result = subprocess.run(
            [sys.executable, str(self.packager)],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertFalse((self.root / ".package-staging").exists())
        with ZipFile(self.root / "dist" / "feature-map-plugin.zip") as archive:
            names = archive.namelist()
            for rel, content in self.expected_files.items():
                self.assertEqual(content.encode("utf-8"), archive.read(rel))
            self.assertIn("scripts/package_plugin.py", names)
        return names

    def test_excludes_evidence_at_root_and_nested_paths(self) -> None:
        for parent in ("", "examples/demo/"):
            for directory in ("local-test-evidence", "test-results"):
                rel = f"{parent}{directory}"
                self.write_file(f"{rel}/run/trace.txt")
                (self.root / rel / "empty").mkdir()

        names = self.package()
        for parent in ("", "examples/demo/"):
            for directory in ("local-test-evidence", "test-results"):
                with self.subTest(parent=parent, directory=directory):
                    prefix = f"{parent}{directory}/"
                    self.assertFalse(
                        any(name.startswith(prefix) for name in names), names
                    )

    def test_preserves_existing_exclusions_and_distribution_files(self) -> None:
        directories = (".git", ".plugin-data", "dist", "__pycache__", ".venv-ai-testing")
        excluded_names = ("feature-map.mermaid.min.js", "MERMAID-LICENSE.txt")
        for parent in ("", "examples/demo/"):
            for directory in directories:
                self.write_file(f"{parent}{directory}/artifact.txt")
            for name in excluded_names:
                self.write_file(f"{parent}{name}")

        names = self.package()
        for name in names:
            with self.subTest(name=name):
                parts = PurePosixPath(name).parts
                self.assertTrue(set(parts).isdisjoint(directories))
                self.assertNotIn(parts[-1], excluded_names)
                self.assertNotIn(".package-staging", parts)


if __name__ == "__main__":
    unittest.main()
