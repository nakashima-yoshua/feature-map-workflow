#!/usr/bin/env python3
"""Build a lightweight HTML directory of existing per-feature XML maps."""

from __future__ import annotations

import argparse
import html
import os
import tempfile
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

SKIP_DIRS = {
    ".git", ".plugin-data", ".package-staging", ".venv-ai-testing",
    "__pycache__", "dist", "test-results", "local-test-evidence",
}
DEFAULT_FILENAME = "feature-map-index.html"


def collect(root: Path) -> list[tuple[Path, str, str, str, str]]:
    records = []
    for path in root.rglob("feature-map.xml"):
        relative = path.relative_to(root)
        if (any(part in SKIP_DIRS for part in relative.parts[:-1])
                or path.is_symlink() or not path.is_file()
                or not path.resolve().is_relative_to(root)):
            continue
        try:
            source = path.read_bytes()
            if b"<!DOCTYPE" in source.upper():
                raise ValueError("DOCTYPE is not permitted")
            doc = ET.fromstring(source)
        except (OSError, ET.ParseError, ValueError) as exc:
            raise ValueError(f"{relative}: cannot read Feature Map: {exc}") from exc
        if doc.tag != "featureMap":
            raise ValueError(f"{relative}: root must be featureMap")
        system = (doc.findtext("./meta/system") or "").strip()
        feature = (doc.findtext("./meta/feature") or "").strip()
        purpose = " ".join((doc.findtext("./goal/purpose") or "").split())
        state = doc.get("state", "").strip()
        if not system or not feature or not purpose or not state:
            raise ValueError(f"{relative}: system, feature, purpose and state are required")
        if len(purpose) > 160:
            purpose = purpose[:159] + "…"
        records.append((path, system, feature, purpose, state))
    records.sort(key=lambda r: (r[1].casefold(), r[2].casefold(), r[0].as_posix()))
    return records


def render(records: list[tuple[Path, str, str, str, str]], output: Path) -> str:
    rows = []
    for path, system, feature, purpose, state in records:
        relative = os.path.relpath(path, output.parent).replace(os.sep, "/")
        url = html.escape(quote(relative, safe="/"), quote=True)
        rows.append(
            "<tr><td>" + html.escape(system)
            + "</td><td><a href=\"" + url + "\">" + html.escape(feature)
            + "</a></td><td>" + html.escape(state)
            + "</td><td>" + html.escape(purpose) + "</td></tr>"
        )

    return """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Feature Map Index</title>
<style>
body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;max-width:1050px;margin:2rem auto;padding:0 1rem;color:#202124;line-height:1.5}
table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #ddd;padding:.65rem;text-align:left;vertical-align:top}th{background:#f5f5f5}
a{color:#125aa0}td{overflow-wrap:anywhere}@media(max-width:650px){table{font-size:.88rem}th,td{padding:.4rem}}
</style>
</head>
<body>
<h1>Feature Map Index</h1>
<p>""" + str(len(records)) + """ features. Each link opens its own XML/XSLT view; this page contains metadata only.</p>
<table><thead><tr><th>System</th><th>Feature</th><th>State</th><th>Purpose (excerpt)</th></tr></thead>
<tbody>
""" + "\n".join(rows) + """
</tbody></table>
</body></html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Directory containing per-feature feature-map.xml files")
    parser.add_argument("--output", type=Path, default=Path(DEFAULT_FILENAME), help="Output HTML path relative to --root")
    parser.add_argument("--force", action="store_true", help="Replace an existing generated index")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        parser.error(f"root directory not found: {root}")
    raw_output = root / args.output if not args.output.is_absolute() else args.output
    # Refuse to follow a final-component symlink even when its target stays inside --root.
    if raw_output.is_symlink():
        parser.error("output must not be a symbolic link")
    output = raw_output.resolve()
    if not output.is_relative_to(root) or output.suffix.lower() != ".html":
        parser.error("output must be an HTML file inside --root")
    if output.exists() and (not output.is_file() or not args.force):
        parser.error("output exists; specify --force to regenerate a regular HTML file")

    try:
        records = collect(root)
    except ValueError as exc:
        parser.error(str(exc))
    if not records:
        parser.error("no feature-map.xml files found under --root")
    output.parent.mkdir(parents=True, exist_ok=True)
    content = render(records, output)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=output.parent,
                                         prefix=".feature-map-index-", suffix=".tmp", delete=False) as writer:
            temporary = Path(writer.name)
            writer.write(content)
        os.replace(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f"{output} ({len(records)} features)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
