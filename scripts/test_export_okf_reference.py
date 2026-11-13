"""Regression tests for the optional Feature Map to OKF reference exporter."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/feature-map-workflow/scripts/export_okf_reference.py"
SAMPLE = ROOT / "examples/fictional-puzzle-log/feature-map.xml"
REVISION = "a" * 40
URL = f"https://github.com/example/feature/blob/{REVISION}/feature-map.xml"


class ExportOKFTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.output = self.dir / "bundle/concepts/feature.md"

    def invoke(self, *extras, xml=SAMPLE, source_url=URL, revision=REVISION):
        return subprocess.run([
            sys.executable, str(SCRIPT), "--xml", str(xml),
            "--source-url", source_url, "--revision", revision,
            "--output", str(self.output), "--generated-at", "2026-11-14T07:00:00+09:00",
            *extras,
        ], capture_output=True, text=True)

    def test_writes_draft_with_source_provenance(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        content = self.output.read_text(encoding="utf-8")
        self.assertIn("type: Feature Map", content)
        self.assertIn("status: draft", content)
        self.assertIn(REVISION, content)
        self.assertIn("process:fmw-okf-export", content)
        self.assertIn("unverified, derived index", content)
        self.assertNotIn("status: stable", content)

    def test_existing_output_never_overwritten(self):
        self.output.parent.mkdir(parents=True)
        self.output.write_text("original", encoding="utf-8")
        self.assertEqual(self.invoke().returncode, 2)
        self.assertEqual(self.output.read_text(), "original")

    def test_unpinned_source_rejected(self):
        result = self.invoke(source_url="https://example.com/feature-map.xml")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.output.exists())

    def test_wrong_revision_rejected(self):
        self.assertEqual(self.invoke(revision="b" * 40).returncode, 2)

    def test_dtd_rejected_before_output(self):
        xml = self.dir / "evil.xml"
        original = SAMPLE.read_text(encoding="utf-8")
        xml.write_text(original.replace("<featureMap", '<!DOCTYPE featureMap [<!ENTITY leak SYSTEM "file:///etc/passwd">]>\n<featureMap', 1), encoding="utf-8")
        result = self.invoke(xml=xml)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.output.exists())

    def test_xsd_invalid_rejected(self):
        xml = self.dir / "invalid.xml"
        xml.write_text(SAMPLE.read_text(encoding="utf-8").replace('version="1.3"', 'version="9.9"', 1), encoding="utf-8")
        self.assertEqual(self.invoke(xml=xml).returncode, 2)

    def test_missing_timezone_rejected(self):
        # Check the pure function without running the CLI with duplicate flag.
        sys.path.insert(0, str(SCRIPT.parent))
        try:
            from export_okf_reference import timestamp
            with self.assertRaisesRegex(ValueError, "UTC offset"):
                timestamp("2026-11-14T07:00:00")
        finally:
            sys.path.remove(str(SCRIPT.parent))


if __name__ == "__main__":
    unittest.main()
