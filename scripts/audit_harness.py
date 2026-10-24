#!/usr/bin/env python3
"""Read-only, dependency-free inventory of the reusable Feature Map harness.

This detects structural maintenance signals, not semantic correctness or proof
that a proposed Skill change improves an agent's performance.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote

SKILL_REL = Path('skills/feature-map-workflow/SKILL.md')
REFS_REL = Path('skills/feature-map-workflow/references')
LINK_RE = re.compile(r'\[[^\]\n]*\]\(([^)\n]+)\)')
INLINE_CODE_RE = re.compile(r'`[^`\n]*`')
URL_SCHEME_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9+.-]*:')


def _prose_lines(text: str):
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        marker = re.match(r'^(`{3,}|~{3,})', stripped)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            yield number, INLINE_CODE_RE.sub('', line)


def audit(root: Path, *, max_skill_bytes: int = 16384,
          max_guide_bytes: int = 20480, max_total_bytes: int = 307200,
          max_guides: int = 32) -> dict:
    root = root.resolve()
    paths = [root / 'README.md', root / 'README.ja.md', root / SKILL_REL]
    guides = sorted((root / REFS_REL).glob('*.md'))
    paths += guides
    errors, warnings = [], []
    sizes = {}
    characters = lines_count = 0
    repeated = {}
    for path in paths:
        rel = path.relative_to(root).as_posix()
        if not path.is_file():
            errors.append({'kind': 'missing-document', 'path': rel})
            continue
        content = path.read_text(encoding='utf-8')
        sizes[rel] = len(content.encode('utf-8'))
        characters += len(content)
        lines_count += len(content.splitlines())
        # Only actual Markdown prose is scanned; examples in code fences are not links.
        lines = list(_prose_lines(content))
        for number, line in lines:
            for match in LINK_RE.finditer(line):
                href = match.group(1).strip().split()[0].strip('<>')
                if not href or href.startswith(('#', '/', '//')) or URL_SCHEME_RE.match(href):
                    continue
                target = unquote(href.split('#', 1)[0].split('?', 1)[0])
                resolved = (path.parent / target).resolve()
                if not resolved.is_relative_to(root) or not resolved.exists():
                    errors.append({'kind': 'invalid-relative-link', 'path': rel,
                                   'line': number, 'target': href})
        # Duplicated substantial prose is a candidate for review, not an automatic merge.
        paragraph = []
        for number, line in lines + [(0, '')]:
            if line.strip():
                paragraph.append(line.strip())
            else:
                normalized = ' '.join(' '.join(paragraph).split())
                if len(normalized) >= 240 and not normalized.startswith(('#', '|')):
                    repeated.setdefault(normalized, set()).add(rel)
                paragraph = []

    if sizes.get(SKILL_REL.as_posix(), 0) > max_skill_bytes:
        warnings.append({'kind': 'skill-size', 'path': SKILL_REL.as_posix(),
                         'bytes': sizes[SKILL_REL.as_posix()], 'threshold': max_skill_bytes})
    for guide in guides:
        rel = guide.relative_to(root).as_posix()
        if sizes.get(rel, 0) > max_guide_bytes:
            warnings.append({'kind': 'guide-size', 'path': rel,
                             'bytes': sizes[rel], 'threshold': max_guide_bytes})
    total = sum(sizes.values())
    if total > max_total_bytes:
        warnings.append({'kind': 'total-size', 'bytes': total, 'threshold': max_total_bytes})
    if len(guides) > max_guides:
        warnings.append({'kind': 'guide-count', 'count': len(guides), 'threshold': max_guides})
    for paragraph, locations in sorted(repeated.items()):
        if len(locations) > 1:
            warnings.append({'kind': 'repeated-prose', 'paths': sorted(locations),
                             'excerpt': paragraph[:100]})
    return {'documents': len(sizes), 'guide_count': len(guides),
            'total_bytes': total, 'total_characters': characters, 'total_lines': lines_count,
            'skill_bytes': sizes.get(SKILL_REL.as_posix(), 0),
            'errors': errors, 'warnings': warnings}


def markdown(report: dict) -> str:
    lines = ['## Harness maintenance audit', '',
             f"- Documents: {report['documents']} (guides: {report['guide_count']})",
             f"- Total bytes: {report['total_bytes']:,}",
             f"- Characters / lines: {report['total_characters']:,} / {report['total_lines']:,}",
             f"- SKILL.md bytes: {report['skill_bytes']:,}",
             f"- Broken/missing: {len(report['errors'])}; review candidates: {len(report['warnings'])}",
             '']
    for label, key in [('Errors (must fix)', 'errors'),
                       ('Advisory (review; do not auto-change)', 'warnings')]:
        lines.append(f'### {label}')
        items = report[key]
        lines.extend('- ' + json.dumps(item, ensure_ascii=False, sort_keys=True)
                     for item in items) if items else lines.append('- None')
        lines.append('')
    lines.append('This report is structural only. Periodically review semantic drift, '
                 'unnecessary rules, conflicting instructions, Japanese/English clarity '
                 'and total human-review cost using the cross-task maintenance guide.')
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--format', choices=['json', 'markdown'], default='markdown')
    parser.add_argument('--max-skill-bytes', type=int, default=16384)
    parser.add_argument('--max-guide-bytes', type=int, default=20480)
    parser.add_argument('--max-total-bytes', type=int, default=307200)
    parser.add_argument('--max-guides', type=int, default=32)
    args = parser.parse_args()
    report = audit(args.root, max_skill_bytes=args.max_skill_bytes,
                   max_guide_bytes=args.max_guide_bytes,
                   max_total_bytes=args.max_total_bytes,
                   max_guides=args.max_guides)
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.format == 'json'
          else markdown(report))
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
