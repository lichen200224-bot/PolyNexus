$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($env:VITE_POLYNEXUS_LOOPBACK_TOKEN)) {
  throw "PolyNexus START pairing is not configured. Use scripts/start.ps1."
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Remove-Item Env:LOOPBACK_TOKEN -ErrorAction SilentlyContinue
Push-Location (Join-Path $repoRoot "apps\web")
try {
  npm run dev
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
} finally {
  Remove-Item Env:VITE_POLYNEXUS_LOOPBACK_TOKEN -ErrorAction SilentlyContinue
  Pop-Location
}
