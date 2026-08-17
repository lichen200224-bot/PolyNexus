$ErrorActionPreference = "Stop"

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
  if (-not (Test-Path $path)) { throw "Required baseline path missing: $path" }
}

python .\scripts\validate_baseline.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (Get-Command git -ErrorAction SilentlyContinue) {
  git status --short --branch
  Write-Host "Latest commits:"
  git log -5 --oneline 2>$null
} else {
  Write-Warning "Git not found"
}

Write-Host "Preflight complete. Read PROJECT_STATE + HANDOFF before writing."
