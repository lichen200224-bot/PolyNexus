$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$hostExecutable = (Get-Process -Id $PID).Path
$tokenBytes = New-Object byte[] 32
$random = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
  $random.GetBytes($tokenBytes)
} finally {
  $random.Dispose()
}
$token = [Convert]::ToBase64String($tokenBytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')

$previousLoopbackToken = [Environment]::GetEnvironmentVariable("LOOPBACK_TOKEN", "Process")
$previousViteToken = [Environment]::GetEnvironmentVariable(
  "VITE_POLYNEXUS_LOOPBACK_TOKEN",
  "Process"
)
$coreProcess = $null
$webProcess = $null
$launchStartedAt = Get-Date

function Get-StartListenerProcessIds {
  $ids = @()
  foreach ($line in (& netstat.exe -ano -p TCP)) {
    $fields = @($line -split '\s+' | Where-Object { $_ })
    if ($fields.Count -lt 5 -or $fields[3] -ne "LISTENING") { continue }
    if ($fields[1] -notmatch '^127\.0\.0\.1:(5173|8765)$') { continue }
    $ids += [int]$fields[4]
  }
  return @($ids | Sort-Object -Unique)
}

$preexistingListenerProcessIds = @(Get-StartListenerProcessIds)

function Restore-ProcessEnvironment {
  param([string]$Name, $PreviousValue)
  if ($null -eq $PreviousValue) {
    Remove-Item "Env:$Name" -ErrorAction SilentlyContinue
  } else {
    [Environment]::SetEnvironmentVariable($Name, $PreviousValue, "Process")
  }
}

function Stop-OwnedProcessTree {
  param([System.Diagnostics.Process]$Process)
  if ($null -eq $Process) { return }
  $Process.Refresh()
  if (-not $Process.HasExited) {
    & taskkill.exe /PID $($Process.Id) /T /F 1>$null 2>$null
  }
}

function Stop-NewStartListeners {
  foreach ($processId in @(Get-StartListenerProcessIds)) {
    if ($processId -in $preexistingListenerProcessIds) { continue }
    $listenerProcess = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if ($null -eq $listenerProcess) { continue }
    if ($listenerProcess.StartTime -lt $launchStartedAt.AddSeconds(-2)) { continue }
    if ($listenerProcess.ProcessName -notin @("node", "python", "python3")) { continue }
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
  }
}

try {
  $env:LOOPBACK_TOKEN = $token
  Remove-Item Env:VITE_POLYNEXUS_LOOPBACK_TOKEN -ErrorAction SilentlyContinue
  $coreScript = Join-Path $PSScriptRoot "start_core.ps1"
  $webScript = Join-Path $PSScriptRoot "start_web.ps1"
  $commonArguments = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File")

  $coreProcess = Start-Process `
    -FilePath $hostExecutable `
    -ArgumentList ($commonArguments + "`"$coreScript`"") `
    -WorkingDirectory $repoRoot `
    -WindowStyle Hidden `
    -PassThru

  Remove-Item Env:LOOPBACK_TOKEN -ErrorAction SilentlyContinue
  $env:VITE_POLYNEXUS_LOOPBACK_TOKEN = $token
  $webProcess = Start-Process `
    -FilePath $hostExecutable `
    -ArgumentList ($commonArguments + "`"$webScript`"") `
    -WorkingDirectory $repoRoot `
    -WindowStyle Hidden `
    -PassThru

  Restore-ProcessEnvironment "LOOPBACK_TOKEN" $previousLoopbackToken
  Restore-ProcessEnvironment "VITE_POLYNEXUS_LOOPBACK_TOKEN" $previousViteToken
  [Array]::Clear($tokenBytes, 0, $tokenBytes.Length)
  $token = $null

  Write-Output "PolyNexus START launched Core at http://127.0.0.1:8765"
  Write-Output "PolyNexus START launched Web at http://127.0.0.1:5173"
  Write-Output "Press Ctrl+C to stop the owned Core and Web process trees."

  while ($true) {
    Start-Sleep -Milliseconds 250
    $coreProcess.Refresh()
    $webProcess.Refresh()
    if ($coreProcess.HasExited -or $webProcess.HasExited) {
      $component = if ($coreProcess.HasExited) { "Core" } else { "Web" }
      $componentProcess = if ($coreProcess.HasExited) { $coreProcess } else { $webProcess }
      throw "PolyNexus START stopped because $component exited with code $($componentProcess.ExitCode)."
    }
  }
} finally {
  Restore-ProcessEnvironment "LOOPBACK_TOKEN" $previousLoopbackToken
  Restore-ProcessEnvironment "VITE_POLYNEXUS_LOOPBACK_TOKEN" $previousViteToken
  Stop-OwnedProcessTree $webProcess
  Stop-OwnedProcessTree $coreProcess
  Start-Sleep -Milliseconds 250
  Stop-NewStartListeners
  [Array]::Clear($tokenBytes, 0, $tokenBytes.Length)
  $token = $null
}
