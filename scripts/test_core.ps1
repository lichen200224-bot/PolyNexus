$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$python = "python"
if (Test-Path $venvPython) {
  $python = $venvPython
}

Push-Location (Join-Path $repoRoot "services\core")
try {
  & $python -m pytest
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
  Pop-Location
}
