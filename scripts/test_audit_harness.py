#!/usr/bin/env python3
"""Offline tests for the read-only harness maintenance audit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from audit_harness import audit, markdown


class HarnessAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.write('README.md', '# Project\n[Skill](skills/feature-map-workflow/SKILL.md)\n')
        self.write('README.ja.md', '# プロジェクト\n')
        self.write('skills/feature-map-workflow/SKILL.md',
                   '# Skill\n[Guide](references/a.md)\n')
        self.write('skills/feature-map-workflow/references/a.md', '# Guide A\n')

    def write(self, rel: str, content: str) -> None:
        dest = self.root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding='utf-8')

    def test_valid_links_and_read_only(self) -> None:
        self.write('skills/feature-map-workflow/references/a.md',
                   '# A\n[local](../SKILL.md#heading)\n[external](https://example.org)\n'
                   '[anchor](#section)\n[encoded](../SKILL.md?raw=1)\n![asset](../SKILL.md)\n'
                   '```md\n[missing](not-a-real-file.md)\n```\n'
                   '`[ignored](also-missing.md)`\n')
        before = {p.relative_to(self.root): p.read_bytes()
                  for p in self.root.rglob('*.md')}
        result = audit(self.root)
        after = {p.relative_to(self.root): p.read_bytes()
                 for p in self.root.rglob('*.md')}
        self.assertEqual(before, after)
        self.assertEqual([], result['errors'])
        contents = [value.decode('utf-8').replace('\r\n', '\n') for value in before.values()]
        self.assertEqual(sum(map(len, contents)), result['total_characters'])
        self.assertEqual(sum(len(value.splitlines()) for value in contents), result['total_lines'])
        self.assertIn('This report is structural only.', markdown(result))

    def test_missing_link_and_missing_document_are_errors(self) -> None:
        (self.root / 'README.ja.md').unlink()
        self.write('skills/feature-map-workflow/references/a.md',
                   '[bad](../../../nonexistent.md)\n')
        report = audit(self.root)
        self.assertEqual({'invalid-relative-link', 'missing-document'},
                         {issue['kind'] for issue in report['errors']})

    def test_growth_and_repetition_are_advisory(self) -> None:
        prose = 'Reusable instructions should describe observable facts. ' * 7
        self.write('skills/feature-map-workflow/references/a.md', '# A\n\n' + prose + '\n')
        self.write('skills/feature-map-workflow/references/b.md', '# B\n\n' + prose + '\n')
        report = audit(self.root, max_skill_bytes=1, max_guide_bytes=1,
                       max_total_bytes=1, max_guides=1)
        self.assertFalse(report['errors'])
        kinds = {issue['kind'] for issue in report['warnings']}
        self.assertTrue({'skill-size', 'guide-size', 'total-size',
                         'guide-count', 'repeated-prose'} <= kinds)

    def test_cli_reports_errors_without_changes(self) -> None:
        self.write('README.md', '[bad](missing.md)\n')
        script = Path(__file__).with_name('audit_harness.py')
        result = subprocess.run([sys.executable, str(script), '--root', str(self.root),
                                 '--format', 'json'], capture_output=True, text=True)
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertEqual('invalid-relative-link', json.loads(result.stdout)['errors'][0]['kind'])


if __name__ == '__main__':
    unittest.main()
