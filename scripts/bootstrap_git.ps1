$ErrorActionPreference = "Stop"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  throw "Git not found. Install Git for Windows first."
}

if (-not (Test-Path ".git")) {
  git init
  git branch -M main
  git add .
  git commit -m "chore: establish PolyNexus development baseline v1.0"
  git switch -c develop
  Write-Host "Initialized Git baseline. Current branch: develop"
} else {
  Write-Host "Git repository already exists. No init performed."
  git status --short --branch
}

Write-Host "Remote is intentionally not configured. Add only an approved remote after review."
