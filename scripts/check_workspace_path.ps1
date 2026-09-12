$ErrorActionPreference = "Stop"

Write-Host "== PolyNexus Portable Workspace Check =="

$CandidateRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$RepoRoot = (& git -C $CandidateRoot rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($RepoRoot)) {
    throw "Repository root could not be discovered with git rev-parse --show-toplevel"
}

$RepoRoot = (Resolve-Path $RepoRoot).Path.TrimEnd('\')
Write-Host "Repository root: $RepoRoot"

$required = @(
    "AGENTS.md",
    "docs/11_PROJECT_STATE.md",
    "docs/36_POLYNEXUS_CROSS_MACHINE_GOVERNANCE.md",
    "governance/POLYNEXUS_PROFILE.yaml"
)

foreach ($relative in $required) {
    $path = Join-Path $RepoRoot $relative
    if (-not (Test-Path $path)) {
        throw "Required repository file missing: $relative"
    }
}

$localProfile = Join-Path $RepoRoot ".flowgov.local.toml"
if (Test-Path $localProfile) {
    Write-Host "Machine-local profile: present (NON_AUTHORITATIVE / gitignored)"
} else {
    Write-Host "Machine-local profile: not present (defaults/discovery apply)"
}

Write-Host "Workspace portability PASS: repository location is machine-local and non-authoritative"
