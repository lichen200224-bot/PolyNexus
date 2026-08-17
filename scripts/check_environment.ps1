$ErrorActionPreference = "Stop"

Write-Host "== PolyNexus Environment Check =="

function Require-Command($name) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if (-not $cmd) { throw "$name not found in PATH" }
  return $cmd
}

Require-Command "git" | Out-Null
Require-Command "python" | Out-Null
Require-Command "node" | Out-Null
Require-Command "npm" | Out-Null

$pythonVersion = (& python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))").Trim()
$nodeVersionRaw = (& node --version).Trim()
$nodeVersion = $nodeVersionRaw.TrimStart('v')

if ([version]$pythonVersion -lt [version]"3.12.0") {
  throw "Python $pythonVersion found; PolyNexus requires Python 3.12+"
}
if ([version]$nodeVersion -lt [version]"22.12.0") {
  throw "Node $nodeVersion found; PolyNexus baseline requires Node 22.12+"
}

Write-Host "Git    : $(& git --version)"
Write-Host "Python : $pythonVersion"
Write-Host "Node   : $nodeVersionRaw"
Write-Host "npm    : $(& npm --version)"

if (Get-Command codex -ErrorAction SilentlyContinue) {
  Write-Host "Codex  : found in PATH"
} else {
  Write-Warning "Codex CLI not found in PATH. This is not a Core build blocker if you use another Codex surface, but verify access before Runtime integration work."
}

if (Get-Command opencode -ErrorAction SilentlyContinue) {
  Write-Host "OpenCode: found in PATH"
} else {
  Write-Warning "OpenCode CLI not found in PATH. Install/configure before OpenCode implementation work."
}

Write-Host "Antigravity: verify manually by opening this same repository folder and confirming .agents/rules + .agents/skills are visible."
Write-Host "Environment check complete."
