$ErrorActionPreference = "Stop"
$Expected = "D:\AI學習教材\PolyNexus"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path.TrimEnd('\')
$ExpectedNormalized = $Expected.TrimEnd('\')

Write-Host "== PolyNexus Workspace Path Check =="
Write-Host "Expected: $ExpectedNormalized"
Write-Host "Actual  : $RepoRoot"

if (-not [string]::Equals($RepoRoot, $ExpectedNormalized, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "Workspace path mismatch. Move/clone the repository to: $ExpectedNormalized"
}

Write-Host "Workspace path PASS: $RepoRoot"
