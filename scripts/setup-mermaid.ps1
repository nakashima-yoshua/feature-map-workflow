param(
    [string]$Destination = "."
)

$ErrorActionPreference = "Stop"
$Version = "12.0.0"
$Base = "https://cdn.jsdelivr.net/npm/mermaid@$Version"
New-Item -ItemType Directory -Force -Path $Destination | Out-Null

Invoke-WebRequest -UseBasicParsing -Uri "$Base/dist/mermaid.min.js" -OutFile (Join-Path $Destination "feature-map.mermaid.min.js")
Invoke-WebRequest -UseBasicParsing -Uri "$Base/LICENSE" -OutFile (Join-Path $Destination "MERMAID-LICENSE.txt")

Write-Output "Installed Mermaid $Version to $(Join-Path $Destination 'feature-map.mermaid.min.js')"
