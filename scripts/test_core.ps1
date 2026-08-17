$ErrorActionPreference = "Stop"

$python = "python"
if (Test-Path ".venv\Scripts\python.exe") {
  $python = ".venv\Scripts\python.exe"
}

Push-Location ".\services\core"
try {
  & $python -m pytest
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
  Pop-Location
}
