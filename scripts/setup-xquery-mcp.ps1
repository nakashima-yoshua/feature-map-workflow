$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Manifest = Join-Path $Root ".config/dotnet-tools.json"

if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    throw ".NET SDK is required. Install .NET 10 SDK, then run this script again."
}

$Version = (& dotnet --version).Trim()
$Major = [int]($Version.Split('.')[0])
if ($Major -lt 10) {
    throw "xquery-mcp requires .NET 10. Detected: $Version"
}

& dotnet tool restore --tool-manifest $Manifest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "xquery-mcp 1.4.0.3 restored for this plugin."
Write-Host "The MCP server is launched by mcp.json with: dotnet tool run xquery-mcp"
