# PowerShell (Windows): install Playwright/Chromium into a repository-local venv.
[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Check,
    [switch]$WithXQuery,
    [switch]$SkipWeb,
    [switch]$Smoke,
    [string]$WindowsUiProject
)
$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'setup-ai-testing.py'
$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    $executable = 'py'
    $args = @('-3')
} else {
    $executable = 'python'
    $args = @()
}
$args += $script
if ($DryRun) { $args += '--dry-run' }
if ($Check) { $args += '--check' }
if ($WithXQuery) { $args += '--with-xquery' }
if ($SkipWeb) { $args += '--skip-web' }
if ($Smoke) { $args += '--smoke' }
if ($WindowsUiProject) { $args += @('--windows-ui-project', $WindowsUiProject) }
& $executable @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
