#!/usr/bin/env sh
set -eu

DEST="${1:-.}"
VERSION="12.0.0"
BASE="https://cdn.jsdelivr.net/npm/mermaid@${VERSION}"
mkdir -p "$DEST"

if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$BASE/dist/mermaid.min.js" -o "$DEST/feature-map.mermaid.min.js"
  curl -fsSL "$BASE/LICENSE" -o "$DEST/MERMAID-LICENSE.txt"
elif command -v wget >/dev/null 2>&1; then
  wget -q "$BASE/dist/mermaid.min.js" -O "$DEST/feature-map.mermaid.min.js"
  wget -q "$BASE/LICENSE" -O "$DEST/MERMAID-LICENSE.txt"
else
  echo "curl or wget is required" >&2
  exit 1
fi

echo "Installed Mermaid ${VERSION} to $DEST/feature-map.mermaid.min.js"
