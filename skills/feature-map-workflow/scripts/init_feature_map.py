#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from xml.sax.saxutils import escape


def main() -> int:
    p = argparse.ArgumentParser(description="Create a minimal Source-first Feature Map XML and copy its XSD/XSLT support files.")
    p.add_argument("--system", required=True)
    p.add_argument("--feature", required=True)
    p.add_argument("--mode", choices=("catchup", "change"), default="change")
    p.add_argument("--purpose", default="TBD")
    p.add_argument("--output", default="feature-map.xml")
    p.add_argument("--force", action="store_true")
    p.add_argument("--no-support-files", action="store_true")
    args = p.parse_args()

    output = Path(args.output).resolve()
    if output.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing file: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="feature-map.xsl"?>
<featureMap xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:noNamespaceSchemaLocation="feature-map.xsd"
            version="1.3"
            mode="{args.mode}"
            state="draft">
  <meta>
    <system>{escape(args.system)}</system>
    <feature>{escape(args.feature)}</feature>
  </meta>
  <goal>
    <purpose>{escape(args.purpose)}</purpose>
  </goal>
  <sourceMap>
    <ref kind="entry" target="TBD"/>
  </sourceMap>
</featureMap>
'''
    output.write_text(xml, encoding="utf-8")

    if not args.no_support_files:
        assets = Path(__file__).resolve().parent.parent / "assets"
        for name in ("feature-map.xsd", "feature-map.xsl"):
            # Mermaid runtime is optional. The XSLT falls back to the pinned CDN if the local file is absent.
            dest = output.parent / name
            if not dest.exists() or args.force:
                shutil.copy2(assets / name, dest)

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
