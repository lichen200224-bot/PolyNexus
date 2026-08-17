$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

Write-Host "== PolyNexus Development Readiness Gate =="

& (Join-Path $PSScriptRoot "check_environment.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Push-Location $repoRoot
try {
  & (Join-Path $PSScriptRoot "preflight.ps1")
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

  & (Join-Path $PSScriptRoot "test_core.ps1")
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

  Push-Location (Join-Path $repoRoot "apps\web")
  try {
    npm run build
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    npm run test
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  } finally {
    Pop-Location
  }

  git diff --check
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

  Write-Host ""
  Write-Host "Git state:"
  git status --short --branch
  Write-Host ""
  Write-Host "Development readiness checks passed. Review git status before creating feature/first-vertical-slice."
} finally {
  Pop-Location
}
