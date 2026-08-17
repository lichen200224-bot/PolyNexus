$ErrorActionPreference = "Stop"

Write-Host "== PolyNexus Development Setup =="

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw "Python not found. Install Python 3.12+ first."
}
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  throw "Node.js not found. Install Node 22.12+ (or another Vite 8-supported version)."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  throw "npm not found."
}

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

$python = Join-Path (Resolve-Path ".venv") "Scripts\python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install -e ".\services\core[dev]"

Push-Location ".\apps\web"
try {
  npm install
} finally {
  Pop-Location
}

Write-Host "Setup complete. Dependency lock files should be reviewed and committed after first successful local install."
