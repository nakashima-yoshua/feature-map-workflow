#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from lxml import etree
except ImportError as exc:
    raise SystemExit("lxml is required: python -m pip install lxml") from exc

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "feature-map-workflow"
ASSETS = SKILL / "assets"


def check_json(path: Path) -> None:
    json.loads(path.read_text(encoding="utf-8"))
    print(f"json ok: {path.relative_to(ROOT)}")


def main() -> int:
    for rel in (
        "plugin.json",
        "mcp.json",
        "hooks/hooks.json",
        ".config/dotnet-tools.json",
    ):
        check_json(ROOT / rel)

    for path in list((ROOT / "hooks").glob("*.py")) + list((SKILL / "scripts").glob("*.py")):
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
        print(f"python ok: {path.relative_to(ROOT)}")

    xsd_doc = etree.parse(str(ASSETS / "feature-map.xsd"))
    schema = etree.XMLSchema(xsd_doc)
    example = etree.parse(str(ASSETS / "feature-map.example.xml"))
    if not schema.validate(example):
        raise SystemExit(str(schema.error_log))
    print("xsd ok: feature-map.example.xml")

    xslt = etree.XSLT(etree.parse(str(ASSETS / "feature-map.xsl")))
    html = str(xslt(example))
    required = (
        'class="mermaid"',
        "sequenceDiagram",
        "classDiagram",
        "feature-map.mermaid.min.js",
        "mermaid@12.0.0",
        "securityLevel: 'strict'",
        "layout: 'dagre'",
        "look: 'classic'",
    )
    missing = [item for item in required if item not in html]
    if missing:
        raise SystemExit(f"HTML renderer missing expected markers: {missing}")
    print("xslt ok: Mermaid blocks and pinned loader emitted")

    plugin = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    if plugin.get("version") != "0.4.0":
        raise SystemExit("plugin.json version must be 0.4.0")

    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    if not skill_text.startswith("---\nname: feature-map-workflow\n"):
        raise SystemExit("SKILL.md frontmatter is malformed")

    print("repository validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
