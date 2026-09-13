$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($env:LOOPBACK_TOKEN)) {
  throw "PolyNexus START pairing is not configured. Use scripts/start.ps1."
}
Remove-Item Env:VITE_POLYNEXUS_LOOPBACK_TOKEN -ErrorAction SilentlyContinue

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
  $python = "python"
  if (Test-Path ".venv\Scripts\python.exe") {
    $python = ".venv\Scripts\python.exe"
  }

  $env:PYTHONPATH = (Resolve-Path ".\services\core\src")
  & $python -m uvicorn polynexus_core.app:app --host 127.0.0.1 --port 8765
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
} finally {
  Pop-Location
}
