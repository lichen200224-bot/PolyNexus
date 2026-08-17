$ErrorActionPreference = "Stop"

$python = "python"
if (Test-Path ".venv\Scripts\python.exe") {
  $python = ".venv\Scripts\python.exe"
}

$env:PYTHONPATH = (Resolve-Path ".\services\core\src")
& $python -m uvicorn polynexus_core.app:app --host 127.0.0.1 --port 8765 --reload
