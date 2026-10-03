#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
MANIFEST="$ROOT/.config/dotnet-tools.json"

if ! command -v dotnet >/dev/null 2>&1; then
  echo ".NET SDK is required. Install .NET 10 SDK, then run this script again." >&2
  exit 1
fi

VERSION=$(dotnet --version)
MAJOR=${VERSION%%.*}
if [ "$MAJOR" -lt 10 ]; then
  echo "xquery-mcp requires .NET 10. Detected: $VERSION" >&2
  exit 1
fi

dotnet tool restore --tool-manifest "$MANIFEST"
printf '%s\n' "xquery-mcp 1.4.0.3 restored for this plugin."
printf '%s\n' "The MCP server is launched by mcp.json with: dotnet tool run xquery-mcp"
