$ErrorActionPreference = "Stop"

$assets = Join-Path $PSScriptRoot "../../skills/feature-map-workflow/assets"
$xmlPath = Join-Path $PSScriptRoot "feature-map.xml"
$htmlPath = Join-Path $PSScriptRoot "feature-map.html"

# Validate before transforming. No Python or additional packages are required.
$settings = [System.Xml.XmlReaderSettings]::new()
$settings.DtdProcessing = [System.Xml.DtdProcessing]::Prohibit
$settings.XmlResolver = $null
$settings.ValidationType = [System.Xml.ValidationType]::Schema
$null = $settings.Schemas.Add("", (Join-Path $assets "feature-map.xsd"))
$reader = [System.Xml.XmlReader]::Create($xmlPath, $settings)
try {
    while ($reader.Read()) { }
} finally {
    $reader.Dispose()
}

$transform = [System.Xml.Xsl.XslCompiledTransform]::new()
$transform.Load((Join-Path $assets "feature-map.xsl"))
$transform.Transform($xmlPath, $htmlPath)
Write-Output "XSD validation passed. HTML generated: $htmlPath"
