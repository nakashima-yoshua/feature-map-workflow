#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

EXCLUDE_DIRS = {".git", ".plugin-data", "dist", "__pycache__"}
EXCLUDE_NAMES = {"feature-map.mermaid.min.js", "MERMAID-LICENSE.txt"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="dist/feature-map-plugin.zip")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    out = (root / args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()

    staging = root / ".package-staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()

    try:
        for path in root.rglob("*"):
            rel = path.relative_to(root)
            if any(part in EXCLUDE_DIRS for part in rel.parts):
                continue
            if path.name in EXCLUDE_NAMES:
                continue
            if path == staging or staging in path.parents:
                continue
            dest = staging / rel
            if path.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, dest)
        archive_base = out.with_suffix("")
        created = Path(shutil.make_archive(str(archive_base), "zip", staging))
        if created != out:
            created.replace(out)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
