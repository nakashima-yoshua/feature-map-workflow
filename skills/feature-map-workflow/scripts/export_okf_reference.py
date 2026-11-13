#!/usr/bin/env python3
"""Create an OKF draft reference from a validated canonical Feature Map.

This is opt-in and never changes Feature Map XML or approves derived knowledge.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from lxml import etree

from validate_feature_map import validate

COMMIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")


def source_url(value: str, revision: str) -> str:
    """Require a HTTPS source URL whose path includes a pinned Git revision."""
    parts = urlsplit(value)
    if (parts.scheme != "https" or not parts.hostname or parts.username
            or parts.password or parts.query or parts.fragment
            or any(char.isspace() or char in "()<>\\" for char in value)):
        raise ValueError("source URL must be a plain HTTPS URL without credentials or query")
    if not COMMIT_SHA.fullmatch(revision) or revision.lower() not in [x.lower() for x in parts.path.split("/")]:
        raise ValueError("source URL must include the explicit 40-hex commit revision as a path segment")
    return value


def timestamp(value: str | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("generated-at must be an ISO 8601 datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("generated-at needs an explicit UTC offset")
    return parsed.isoformat(timespec="seconds")


def inline(value: str) -> str:
    """Keep untrusted XML text to a single escaped Markdown line."""
    normalized = " ".join(value.split())
    return re.sub(r"([\\`*_{}\[\]<>])", r"\\\1", normalized)


def render(xml: Path, source: str, generated: str, xsd: Path) -> str:
    validate(xml, xsd)
    raw = xml.read_bytes()
    if len(raw) > 1_048_576:
        raise ValueError("Feature Map exceeds maximum input size")
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
    node = etree.fromstring(raw, parser=parser)
    system, feature, purpose = (
        (node.findtext(name) or "").strip()
        for name in ("meta/system", "meta/feature", "goal/purpose")
    )
    if not system or not feature or not purpose:
        raise ValueError("Feature Map needs nonempty system, feature and purpose")
    title = f"{system} / {feature}"
    # JSON strings are valid YAML quoted strings. Avoid unsafe hand-built YAML.
    quoted = lambda v: json.dumps(v, ensure_ascii=False)
    return (
        "---\n"
        "type: Feature Map\n"
        f"title: {quoted(title)}\n"
        f"description: {quoted(purpose)}\n"
        "status: draft\n"
        "tags: [feature-map]\n"
        f"generated: {{ by: process:fmw-okf-export, at: {quoted(generated)} }}\n"
        "sources:\n"
        "  - id: canonical-feature-map\n"
        f"    resource: {quoted(source)}\n"
        "    title: Revision-pinned Feature Map XML\n"
        "---\n\n"
        "# Feature reference\n\n"
        f"- System: {inline(system)}\n"
        f"- Feature: {inline(feature)}\n"
        f"- Purpose: {inline(purpose)}[^canonical-feature-map]\n\n"
        "# Authority\n\n"
        "This is an **unverified, derived index only**. Read the pinned XML, "
        "source code, accepted requirements, and test evidence before relying on any claim. "
        "It does not replace the Feature Map or imply test success or approval.\n\n"
        "[^canonical-feature-map]: Source revision recorded in frontmatter.\n"
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--xml", required=True, type=Path)
    p.add_argument("--source-url", required=True)
    p.add_argument("--revision", required=True, help="40-hex commit SHA embedded in --source-url")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--xsd", type=Path, default=Path(__file__).resolve().parent.parent / "assets/feature-map.xsd")
    p.add_argument("--generated-at", help="Explicit ISO 8601 timestamp for reproducible exports")
    args = p.parse_args(argv)
    try:
        source = source_url(args.source_url, args.revision)
        generated = timestamp(args.generated_at)
        content = render(args.xml, source, generated, args.xsd)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as output:
            output.write(content)
    except (OSError, ValueError, etree.LxmlError) as exc:
        print(f"OKF export rejected: {exc}", file=sys.stderr)
        return 2
    print(f"OKF draft created: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
