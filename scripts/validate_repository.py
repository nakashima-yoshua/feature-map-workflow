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

    for path in (
        list((ROOT / "hooks").glob("*.py"))
        + list((ROOT / "scripts").glob("*.py"))
        + list((SKILL / "scripts").glob("*.py"))
        + list((ROOT / "examples").glob("**/*.py"))
    ):
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
        print(f"python ok: {path.relative_to(ROOT)}")

    xsd_doc = etree.parse(str(ASSETS / "feature-map.xsd"))
    schema = etree.XMLSchema(xsd_doc)
    fixture = etree.fromstring(b"""<featureMap version="1.3" mode="change" state="draft">
  <meta>
    <system>validation-fixture</system>
    <feature>rendering</feature>
  </meta>
  <goal>
    <purpose>Validate the public schema and renderer without a repository-specific example.</purpose>
  </goal>
  <sourceMap>
    <ref kind="entry" target="src:entry"/>
  </sourceMap>
  <diagrams>
    <diagram id="DG1" kind="sequence">sequenceDiagram
A-&gt;&gt;B: validate</diagram>
    <diagram id="DG2" kind="class">classDiagram
class Fixture</diagram>
  </diagrams>
</featureMap>""")
    fixture_doc = etree.ElementTree(fixture)
    if not schema.validate(fixture_doc):
        raise SystemExit(str(schema.error_log))
    print("xsd ok: inline public validation fixture")

    xslt = etree.XSLT(etree.parse(str(ASSETS / "feature-map.xsl")))
    html = str(xslt(fixture_doc))
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

    manifest = json.loads((ROOT / ".config/dotnet-tools.json").read_text(encoding="utf-8"))
    xquery_version = manifest["tools"]["xquery-mcp"]["version"]
    for rel in (
        "README.md",
        "README.ja.md",
        "THIRD_PARTY_NOTICES.md",
        "skills/feature-map-workflow/references/xquery-mcp.md",
    ):
        if xquery_version not in (ROOT / rel).read_text(encoding="utf-8"):
            raise SystemExit(f"{rel} does not mention pinned xquery-mcp {xquery_version}")
    print(f"xquery-mcp version references ok: {xquery_version}")

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
