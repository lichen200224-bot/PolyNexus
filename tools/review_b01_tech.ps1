[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$EvidenceRoot
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Assert-Review {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) {
        throw "B01 independent review failed: $Message"
    }
}

$run = Get-Content -LiteralPath (Join-Path $EvidenceRoot "run.json") -Raw | ConvertFrom-Json
$bug = Get-Content -LiteralPath (Join-Path $EvidenceRoot "real-bug-fix.json") -Raw | ConvertFrom-Json
$retry = Get-Content -LiteralPath (Join-Path $EvidenceRoot "core-b01-tests\failure-retry-recovery.json") -Raw | ConvertFrom-Json
$timeout = Get-Content -LiteralPath (Join-Path $EvidenceRoot "core-b01-tests\process-tree-timeout.json") -Raw | ConvertFrom-Json
$p0 = Get-Content -LiteralPath (Join-Path $EvidenceRoot "core-b01-tests\p0-reconstruct.json") -Raw | ConvertFrom-Json

Assert-Review ($run.status -eq "B01_TECHNICAL_READY") "status"
Assert-Review ($run.human_uat -eq "PENDING_FINAL_HUMAN_UAT") "Human UAT boundary"
Assert-Review ($run.human_acceptance -eq "NOT_CLAIMED") "Human acceptance boundary"
Assert-Review ($run.real_executor_exit -eq 0 -and $run.baseline_synthetic_test_exit -ne 0 -and $run.post_synthetic_test_exit -eq 0) "real bug-fix exits"
Assert-Review ($bug.source_closure -eq $true -and $bug.source_hash_changed -eq $true) "source closure/hash delta"
Assert-Review ($bug.after.changed_paths.Count -eq 1 -and $bug.after.changed_paths[0] -eq "bug.py") "bounded source path"
Assert-Review ($bug.runner.inner_command_exit_codes -contains 0) "inner child command exit"
Assert-Review ($bug.no_parent_repo_used -eq $true) "synthetic cwd boundary"
Assert-Review ($retry.old.generation -ne $retry.new.generation -and $retry.old.run_id -ne $retry.new.run_id) "generation/Run separation"
Assert-Review ($retry.ownership.fence_increased -eq $true) "fence ownership"
Assert-Review ($retry.late_abort.new_generation_unchanged -eq $true -and $retry.late_abort.new_run_process_facts_unchanged -eq $true) "late abort isolation"
Assert-Review ($retry.old.after_cleanup.Count -eq 3 -and $retry.new.after_cleanup.Count -eq 3) "retry process-tree handles"
Assert-Review ($timeout.runtime_state -eq "TIMED_OUT" -and $timeout.all_owned_handles_stopped -eq $true -and $timeout.all_owned_handles_have_end_observation -eq $true) "timeout cleanup"
Assert-Review ($timeout.owned_process_facts.Count -eq 3 -and $timeout.pid_scan_used_as_oracle -eq $false -and $timeout.flag_used_as_oracle -eq $false) "process-tree oracle"
Assert-Review ($p0.offline_verification.verified -eq $true -and $p0.original_accepted_bytes_unchanged -eq $true -and $p0.provider_private_session_required -eq $false) "P0 offline reconstruction"
Assert-Review ($p0.principal -like "TEST_ONLY:*") "test-only Human boundary"

$diffCheckOutput = @(git -C $repoRoot diff --check 2>&1)
Assert-Review ($LASTEXITCODE -eq 0) "git diff --check"
$productSourceChanges = @(git -C $repoRoot diff --name-only -- services/core/src)
Assert-Review ($productSourceChanges.Count -eq 0) "no unapproved Core source mutation"

$allowedPrefixes = @(
    "docs/delivery/checks/B01_TECHNICAL_READY_20260914.md",
    "docs/delivery/checks/B01_INDEPENDENT_REVIEW_20260914.md",
    "apps/web/package.json",
    "apps/web/package-lock.json",
    "services/core/tests/fixtures/b01_synthetic_repo/",
    "services/core/tests/test_b01_tech.py",
    "tools/run_b01_tech.ps1",
    "tools/review_b01_tech.ps1"
)
$unexpected = [System.Collections.Generic.List[string]]::new()
foreach ($line in @(git -C $repoRoot status --short --untracked-files=all)) {
    if (-not $line) { continue }
    $path = $line.Substring(3).Replace("\\", "/")
    if (-not ($allowedPrefixes | Where-Object { $path.StartsWith($_) })) {
        $unexpected.Add($path)
    }
}
Assert-Review ($unexpected.Count -eq 0) ("unexpected worktree paths: " + ($unexpected -join ", "))

Write-Output "B01_INDEPENDENT_REVIEW PASS"
Write-Output ("candidate=" + $run.source_head)
Write-Output ("real_executor_exit=" + $run.real_executor_exit)
Write-Output ("core_b01_tests_exit=" + $run.b01_core_tests_exit)
Write-Output ("product_source_changes=" + $productSourceChanges.Count)
Write-Output ("unexpected_worktree_paths=" + $unexpected.Count)
exit 0
