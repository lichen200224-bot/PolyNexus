$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

Write-Host "== PolyNexus Preflight =="

$required = @(
  "AGENTS.md",
  "docs/11_PROJECT_STATE.md",
  "docs/12_HANDOFF_CURRENT.md",
  "docs/18_ARCHITECTURE_DECISIONS.md",
  "docs/19_DEVELOPMENT_BASELINE.md",
  ".agents/skills/polynexus-implement/SKILL.md",
  "services/core/pyproject.toml",
  "apps/web/package.json",
  "extensions/browser-companion/manifest.json"
)

foreach ($path in $required) {
  if (-not (Test-Path (Join-Path $repoRoot $path))) {
    throw "Required baseline path missing: $path"
  }
}

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
  throw "Project .venv Python not found. Run .\scripts\setup_dev.ps1 first."
}

Write-Host "Preflight Python: $venvPython"

Push-Location $repoRoot
try {
  & $venvPython ".\scripts\validate_baseline.py"
  if ($LASTEXITCODE -ne 0) {
    throw "Baseline validation failed with exit code $LASTEXITCODE"
  }

  if (Get-Command git -ErrorAction SilentlyContinue) {
    git status --short --branch
    Write-Host "Latest commits:"
    git log -5 --oneline
  } else {
    Write-Warning "Git not found"
  }

  Write-Host "Preflight complete. Read PROJECT_STATE + HANDOFF before writing."
} finally {
  Pop-Location
}
