[CmdletBinding()]
param(
    [string]$ArtifactRoot,
    [string]$ExecutorPath,
    [string]$PythonPath
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $ArtifactRoot) {
    $ArtifactRoot = Join-Path $repoRoot "artifacts\verification\b01-tech-$(Get-Date -Format yyyyMMdd-HHmmss)"
}
$ArtifactRoot = [System.IO.Path]::GetFullPath($ArtifactRoot)
New-Item -ItemType Directory -Force -Path $ArtifactRoot | Out-Null

if (-not $ExecutorPath) {
    $ExecutorPath = $env:POLYNEXUS_CODEX_EXECUTABLE
}
if (-not $ExecutorPath) {
    $ExecutorPath = "C:\Users\shawn\AppData\Local\OpenAI\Codex\bin\bffc5354119c8421\codex.exe"
}
if (-not (Test-Path -LiteralPath $ExecutorPath -PathType Leaf)) {
    throw "B01 real executor is unavailable: $ExecutorPath"
}
$ExecutorPath = (Resolve-Path -LiteralPath $ExecutorPath).Path

if (-not $PythonPath) {
    $localPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $localPython -PathType Leaf) {
        $PythonPath = $localPython
    } elseif (Test-Path -LiteralPath "D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe" -PathType Leaf) {
        $PythonPath = "D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe"
    } else {
        $PythonPath = "python"
    }
}

function Invoke-CapturedProcess {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [string]$StdOutPath,
        [string]$StdErrPath,
        [int]$TimeoutSeconds = 0
    )

    $start = [System.Diagnostics.ProcessStartInfo]::new()
    $start.FileName = $FilePath
    $start.WorkingDirectory = $WorkingDirectory
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    foreach ($argument in $Arguments) {
        [void]$start.ArgumentList.Add([string]$argument)
    }
    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $start
    $startedAt = [DateTimeOffset]::UtcNow
    if (-not $process.Start()) {
        throw "Could not start process: $FilePath"
    }
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $timedOut = $false
    if ($TimeoutSeconds -gt 0) {
        $completed = $process.WaitForExit($TimeoutSeconds * 1000)
        if (-not $completed) {
            $timedOut = $true
            # This helper owns the just-started process.  /T is required so a
            # bounded executor timeout does not leave its child tree alive.
            & taskkill.exe /PID $process.Id /T /F 2>$null | Out-Null
            $process.WaitForExit()
        }
    } else {
        $process.WaitForExit()
    }
    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
    if ($StdOutPath) {
        Set-Content -LiteralPath $StdOutPath -Value $stdout -Encoding utf8NoBOM
    }
    if ($StdErrPath) {
        Set-Content -LiteralPath $StdErrPath -Value $stderr -Encoding utf8NoBOM
    }
    [pscustomobject]@{
        file = $FilePath
        argv = @($Arguments)
        cwd = $WorkingDirectory
        pid = $process.Id
        started_at = $startedAt.ToString("o")
        ended_at = [DateTimeOffset]::UtcNow.ToString("o")
        exit_code = if ($timedOut) { 124 } else { $process.ExitCode }
        timed_out = $timedOut
        stdout = $stdout
        stderr = $stderr
    }
}

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    Invoke-CapturedProcess -FilePath "git" -Arguments $Arguments -WorkingDirectory $WorkingDirectory
}

function Assert-ExitZero {
    param([Parameter(Mandatory = $true)]$Result, [Parameter(Mandatory = $true)][string]$Label)
    if ($Result.exit_code -ne 0) {
        throw "$Label failed with exit $($Result.exit_code): $($Result.stderr)"
    }
}

function Get-JsonExitCodes {
    param([Parameter(Mandatory = $true)][string]$Path)
    $codes = [System.Collections.Generic.List[int]]::new()
    function Visit-JsonNode([object]$Node) {
        if ($null -eq $Node) { return }
        if ($Node -is [System.Collections.IEnumerable] -and $Node -isnot [string]) {
            foreach ($item in $Node) { Visit-JsonNode $item }
            return
        }
        $properties = $Node.PSObject.Properties
        foreach ($property in $properties) {
            if ($property.Name -eq "exit_code" -and $property.Value -is [ValueType]) {
                try { $codes.Add([int]$property.Value) } catch { }
            } else {
                Visit-JsonNode $property.Value
            }
        }
    }
    foreach ($line in (Get-Content -LiteralPath $Path)) {
        if (-not $line.Trim()) { continue }
        try {
            Visit-JsonNode ($line | ConvertFrom-Json)
        } catch {
            # The raw JSONL is retained; non-JSON diagnostic lines are not
            # promoted to evidence.
        }
    }
    return @($codes | Select-Object -Unique)
}

function Get-GitText {
    param(
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    $result = Invoke-Git -WorkingDirectory $WorkingDirectory -Arguments $Arguments
    Assert-ExitZero $result ("git " + ($Arguments -join " "))
    return $result.stdout.Trim()
}

$fixtureTemplate = Join-Path $repoRoot "services\core\tests\fixtures\b01_synthetic_repo"
if (-not (Test-Path -LiteralPath $fixtureTemplate -PathType Container)) {
    throw "B01 fixture template is missing: $fixtureTemplate"
}

$successRoot = Join-Path $ArtifactRoot "real-bug-fix"
$syntheticRepo = Join-Path $successRoot "synthetic-repo"
New-Item -ItemType Directory -Force -Path $syntheticRepo | Out-Null
Copy-Item -LiteralPath (Join-Path $fixtureTemplate "bug.py") -Destination $syntheticRepo -Force
Copy-Item -LiteralPath (Join-Path $fixtureTemplate "check_bug.py") -Destination (Join-Path $syntheticRepo "test_bug.py") -Force

$init = Invoke-Git -WorkingDirectory $syntheticRepo -Arguments @("init", "-b", "main")
Assert-ExitZero $init "synthetic git init"
Assert-ExitZero (Invoke-Git -WorkingDirectory $syntheticRepo -Arguments @("config", "user.name", "b01-runner")) "synthetic git user.name"
Assert-ExitZero (Invoke-Git -WorkingDirectory $syntheticRepo -Arguments @("config", "user.email", "b01@example.invalid")) "synthetic git user.email"
Assert-ExitZero (Invoke-Git -WorkingDirectory $syntheticRepo -Arguments @("add", "bug.py", "test_bug.py")) "synthetic git add"
Assert-ExitZero (Invoke-Git -WorkingDirectory $syntheticRepo -Arguments @("commit", "-m", "B01 baseline")) "synthetic git baseline commit"

$baselineHead = Get-GitText $syntheticRepo @("rev-parse", "HEAD")
$baselineTree = Get-GitText $syntheticRepo @("show", "-s", "--format=%T", "HEAD")
$baselineBlob = Get-GitText $syntheticRepo @("hash-object", "bug.py")
$baselineHash = (Get-FileHash -LiteralPath (Join-Path $syntheticRepo "bug.py") -Algorithm SHA256).Hash.ToLowerInvariant()
$baselineTest = Invoke-CapturedProcess -FilePath $PythonPath -Arguments @("-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_bug.py") -WorkingDirectory $syntheticRepo -StdOutPath (Join-Path $successRoot "baseline-test.stdout.log") -StdErrPath (Join-Path $successRoot "baseline-test.stderr.log")
if ($baselineTest.exit_code -eq 0) {
    throw "Synthetic baseline unexpectedly passed; B01 bug is not bounded"
}

$prompt = @"
Work only in the bounded synthetic repository at the current cwd.
This is a real bounded bug-fix task. Inspect bug.py and test_bug.py, then make
the smallest source-only fix so the existing test passes. Change only bug.py;
do not edit test_bug.py, Git metadata, parent directories, credentials, or any
file outside the current cwd. Do not use a provider private session. After the
source edit, run exactly:
$PythonPath -B -m pytest -q -p no:cacheprovider test_bug.py
Report the cwd, the changed path, the test command and its exit code in your
final response.
"@
$codexStdout = Join-Path $successRoot "codex.stdout.jsonl"
$codexStderr = Join-Path $successRoot "codex.stderr.log"
$codex = Invoke-CapturedProcess -FilePath $ExecutorPath -Arguments @(
    "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
    "-c", 'windows.sandbox="elevated"', "--sandbox", "workspace-write", "--json",
    "--cd", $syntheticRepo, $prompt
) -WorkingDirectory $syntheticRepo -StdOutPath $codexStdout -StdErrPath $codexStderr -TimeoutSeconds 180
$innerExitCodes = @(Get-JsonExitCodes $codexStdout)

$afterHash = (Get-FileHash -LiteralPath (Join-Path $syntheticRepo "bug.py") -Algorithm SHA256).Hash.ToLowerInvariant()
$afterBlob = Get-GitText $syntheticRepo @("hash-object", "bug.py")
$status = Get-GitText $syntheticRepo @("status", "--short", "--untracked-files=all")
$changedPaths = @( ((Get-GitText $syntheticRepo @("diff", "--name-only")) -split "`r?`n") | Where-Object { $_ })
$diff = Get-GitText $syntheticRepo @("diff", "--no-ext-diff", "--", "bug.py")
$postTest = Invoke-CapturedProcess -FilePath $PythonPath -Arguments @("-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_bug.py") -WorkingDirectory $syntheticRepo -StdOutPath (Join-Path $successRoot "post-test.stdout.log") -StdErrPath (Join-Path $successRoot "post-test.stderr.log")

if ($codex.exit_code -ne 0) { throw "Real Codex executor failed with exit $($codex.exit_code): $($codex.stderr)" }
if ($postTest.exit_code -ne 0) { throw "Independent synthetic test failed with exit $($postTest.exit_code): $($postTest.stderr)" }
if ($changedPaths.Count -ne 1 -or $changedPaths[0] -ne "bug.py") { throw "B01 source closure failed: $status" }
if ($diff -notmatch "-\s*return 41" -or $diff -notmatch "\+\s*return 42") { throw "B01 source diff is not the bounded 41-to-42 fix: $diff" }
if ($baselineHash -eq $afterHash) { throw "B01 source hash did not change" }

$realBugFix = [ordered]@{
    case = "B01-REAL-BOUNDED-BUG-FIX"
    actual_cwd = $syntheticRepo
    executor = $ExecutorPath
    executor_version = (Invoke-CapturedProcess -FilePath $ExecutorPath -Arguments @("--version") -WorkingDirectory $syntheticRepo).stdout.Trim()
    baseline = [ordered]@{
        head = $baselineHead
        tree = $baselineTree
        bug_blob = $baselineBlob
        bug_sha256 = $baselineHash
        test_exit = $baselineTest.exit_code
    }
    after = [ordered]@{
        bug_blob = $afterBlob
        bug_sha256 = $afterHash
        test_exit = $postTest.exit_code
        status = $status
        changed_paths = $changedPaths
        diff = $diff
    }
    runner = [ordered]@{
        wrapper = "tools/run_b01_tech.ps1"
        wrapper_cwd = $repoRoot
        wrapper_child_pid = $codex.pid
        child_exit = $codex.exit_code
        inner_command_exit_codes = $innerExitCodes
        stdout_path = $codexStdout
        stderr_path = $codexStderr
    }
    source_hash_changed = ($baselineHash -ne $afterHash)
    source_closure = ($changedPaths.Count -eq 1 -and $changedPaths[0] -eq "bug.py")
    no_parent_repo_used = ($codex.stdout -notmatch [regex]::Escape($repoRoot))
    provider_private_session_required = $false
}
$realBugFix | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $ArtifactRoot "real-bug-fix.json") -Encoding utf8NoBOM

$evidenceDir = Join-Path $ArtifactRoot "core-b01-tests"
$previousEvidenceDir = $env:B01_EVIDENCE_DIR
$env:B01_EVIDENCE_DIR = $evidenceDir
try {
    $coreTest = Invoke-CapturedProcess -FilePath $PythonPath -Arguments @(
        "-B", "-m", "pytest", "--override-ini", "addopts=", "-q", "--disable-warnings", "--tb=short",
        "--basetemp", (Join-Path $ArtifactRoot "pytest-basetemp"), "tests/test_b01_tech.py"
    ) -WorkingDirectory (Join-Path $repoRoot "services\core") -StdOutPath (Join-Path $ArtifactRoot "b01-tests.stdout.log") -StdErrPath (Join-Path $ArtifactRoot "b01-tests.stderr.log")
} finally {
    $env:B01_EVIDENCE_DIR = $previousEvidenceDir
}
if ($coreTest.exit_code -ne 0) { throw "B01 Core evidence tests failed with exit $($coreTest.exit_code): $($coreTest.stderr)" }

foreach ($evidencePath in (Get-ChildItem -LiteralPath $evidenceDir -Filter "*.json" -File)) {
    $evidence = Get-Content -LiteralPath $evidencePath.FullName -Raw | ConvertFrom-Json
    $evidence | Add-Member -NotePropertyName "pytest_runner_exit" -NotePropertyValue $coreTest.exit_code -Force
    $evidence | Add-Member -NotePropertyName "pytest_runner_cwd" -NotePropertyValue (Join-Path $repoRoot "services\core") -Force
    $evidence | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $evidencePath.FullName -Encoding utf8NoBOM
}

$run = [ordered]@{
    status = "B01_TECHNICAL_READY"
    human_uat = "PENDING_FINAL_HUMAN_UAT"
    human_acceptance = "NOT_CLAIMED"
    source_repo = $repoRoot
    source_head = Get-GitText $repoRoot @("rev-parse", "HEAD")
    source_tree = (Get-GitText $repoRoot @("show", "-s", "--format=%T", "HEAD"))
    real_executor_exit = $codex.exit_code
    baseline_synthetic_test_exit = $baselineTest.exit_code
    post_synthetic_test_exit = $postTest.exit_code
    b01_core_tests_exit = $coreTest.exit_code
    artifact_root = $ArtifactRoot
    generated_evidence = @(
        (Join-Path $ArtifactRoot "real-bug-fix.json"),
        (Join-Path $evidenceDir "failure-retry-recovery.json"),
        (Join-Path $evidenceDir "process-tree-timeout.json"),
        (Join-Path $evidenceDir "p0-reconstruct.json")
    )
}
$run | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $ArtifactRoot "run.json") -Encoding utf8NoBOM
Write-Output ("B01_TECHNICAL_READY artifact_root=" + $ArtifactRoot)
exit 0
