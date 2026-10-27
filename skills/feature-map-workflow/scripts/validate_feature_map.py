#!/usr/bin/env python3
"""Validate one standalone Feature Map against its adjacent XSD, without MCP or .NET."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from lxml import etree
except ImportError as exc:
    raise SystemExit("lxml is required: python -m pip install lxml") from exc


def validate(xml_path: Path, xsd_path: Path) -> None:
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
    data = xml_path.read_bytes()
    if b"<!DOCTYPE" in data.upper():
        raise ValueError("DOCTYPE is not permitted in Feature Maps")
    document = etree.ElementTree(etree.fromstring(data, parser=parser))
    schema = etree.XMLSchema(etree.parse(str(xsd_path), parser=parser))
    if not schema.validate(document):
        raise ValueError(str(schema.error_log))


def main() -> int:
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("xml", type=Path, help="Path to feature-map.xml")
    command.add_argument(
        "--xsd", type=Path,
        help="XSD path (default: feature-map.xsd beside the XML)",
    )
    args = command.parse_args()
    xsd_path = args.xsd or args.xml.parent / "feature-map.xsd"
    try:
        validate(args.xml, xsd_path)
    except (OSError, ValueError, etree.LxmlError) as exc:
        print(f"INVALID: {args.xml}: {exc}", file=sys.stderr)
        return 1
    print(f"VALID: {args.xml}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
