# D2a W2 real executor evidence — 2026-09-13

This is an immutable in-lane evidence summary for the D2a candidate. It is not
Human product acceptance and does not adopt MCF-02. The full raw transport log
is outside the lane at
`C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\D2A_W2_TRANSPORT_ATTEMPT_20260913.md`.

## Boundary and provenance

- Fixture baseline: Git `99e204e79d27b879b41a8e0d37e51052499d3196`, tree
  `ae3cb6f9ce3fee3eec09b7d1fcaad21608141f6d`.
- Installed executor:
  `C:\Users\shawn\AppData\Local\OpenAI\Codex\bin\bffc5354119c8421\codex.exe`.
- Version: `codex-cli 0.154.0-alpha.6.2`, probe exit `0`.
- Executable SHA-256:
  `081E4DE4BE8E38FAC6ED4D95E3B1A0B9F6D31C090DDC36E1696B349FE406F575`.
- Real argv boundary after the fix:
  `exec --ephemeral --ignore-user-config -c windows.sandbox="elevated" --sandbox workspace-write --json --cd <Core-created staging> <prompt>`.
- No danger/bypass flag was used. No credential value was read, printed, or
  exported. `thread.started`/`turn.started` handles from the standalone runs
  are recorded in the raw log as non-secret transport provenance.

## Case map

| Case | Real evidence | Result |
| --- | --- | --- |
| Candidate-adapter success | Core-created projected staging; actual Codex process; allowlisted diff; JSONL terminal; Core blob import | PASS |
| Candidate-adapter cancel | Real long-running Codex command with executor/child/grandchild PID manifests; `ControlledJob` stop | PASS |
| Candidate-adapter timeout | Same real tree; exact 15 s supervisor deadline; `TIMED_OUT`; Job Object cleanup | PASS |
| Standalone success | Real source edit in fresh managed worktree; exact cwd/hash/diff; independent pytest | PASS |
| Standalone failure | Real expected non-zero command; no source mutation | PASS |

## Candidate-adapter success

Fresh managed source worktree:
`...\fixtures\codex-managed-adapter-fixed-20260913`.

Projected staging:
`...\fixtures\staging_87f7ae23ea4a7a334038e997`.

- runtime reference: `codex-exec:e6fd379e2c55489aa89c42e147299544`
- binding was set before `create_run`: `run_adapter_fixed` / `task_1`.
- Run state: `RUNNING` → `COMPLETED`; `cleanup=True`.
- process facts: PID `39544`, exit `0`, signal `none`, stopped `true`,
  stdout `3095` bytes, stderr `0` bytes.
- normalized result:
  `{"format":"codex.exec.jsonl.v1","event_count":11,"terminal_type":"turn.completed"}`
- artifact diff SHA-256 and Core blob name:
  `e68e6376c03551c78ce56204c4ed6c15727ce4a4e06a02677dd371b0bf976484`;
  imported artifact size `155` bytes.
- envelope SHA-256:
  `ee2b75885c1f4cc786d581d94bf8105c4a8402da55ba09535a8dac4da84ed70e`.
- effective runtime configuration fingerprint:
  `9f9bcae6f8ca21f0fd44df3ede2a121f0dcb8591e242d2b0038ccd942e41ab6d`.
- permission policy fingerprint:
  `087be0f77d8f2cbc74097171536ceb971bad60f7f4dfe7fc4a50298c9936a853`.
- route-policy evidence SHA-256:
  `59ac875107670d94ac0e2667e565c2334e19b991ec52a799dcc10cc600705166`.
- auth ownership: `RUNTIME_MANAGED`; provider-model egress:
  `RUNTIME_MANAGED`; agent-extension egress: `DENY`.
- source manifest before/after:
  `c76a68598804445a0e9f36978b1ea4c5ebe715b28978ab28bd684b16f6c90db9` →
  `d17eadb9ba8940662ec65c3dbe067eed209affa83343e362f680272747ba54c3`.
- staging diff was exactly `bug.py: return 41 → return 42`.
- managed source worktree remained baseline blob
  `4564ab261c7570752a00bfe7f281a945e5fcf951` and SHA-256
  `FFC63EA42518CA28CBB11871A9480F74AD278991E31E421C6AC653747D62F80F`;
  only its synthetic content-store directory was created by the probe.

## Candidate-adapter cancel and timeout

Both cases used allowlisted scripts `long_task.ps1`, `child.ps1`, and
`grandchild.ps1` in a Core-created projected staging. The scripts wrote only
synthetic PID manifests and held a root → child → grandchild process tree.

### Cancel

- runtime reference:
  `codex-exec:ea8af6256dbf48ebb794ff1043b98b8b`.
- staging:
  `...\fixtures\staging_de2681ad98717ab7f6c5034f`.
- state: `RUNNING` → `CANCELLED`; `cleanup=True`.
- manifests: executor `40504`, child `40700`, grandchild `40948`.
- root process fact: PID `36220`, exit `1`, signal `job_terminate`, stopped
  `true`; post-stop query had no rows for root or manifest PIDs.

### True deadline timeout

- runtime reference:
  `codex-exec:43bfee75fa93448f851a3b2e8595cbb8`.
- staging:
  `...\fixtures\staging_7780b8b14709c6e6b12395f4`.
- state: `RUNNING` → `TIMED_OUT`; `cleanup=True`.
- timeout budget: `15.0` seconds; manifests became ready at `9.344` seconds;
  timeout trigger elapsed `15.047` seconds.
- manifests: executor `41084`, child `39984`, grandchild `29944`.
- root process fact: PID `41708`, exit `1`, signal `job_terminate`, stopped
  `true`; post-stop query had no row for any exact root/manifest PID.
- A post-query showed an unrelated `git-daemon` flow process whose parent PID
  numerically reused `29944`; it was excluded because the exact known
  grandchild PID was absent and the process identity/command/start time did not
  match the synthetic `pwsh` child. It was not touched.

## Standalone real success and failure

The independent standalone gate also ran the installed executor in fresh
managed worktrees using the approved explicit Windows sandbox flag.

- Success thread:
  `01a09ad7-11da-7e41-9a75-8ffcb5e39d30`; outer exit `0`; cwd and inner
  executor command were recorded in the raw log. Codex changed only `bug.py`:
  blob `4564ab261c7570752a00bfe7f281a945e5fcf951` →
  `4860f406c7a4c121fe0cd7d1b1c1314b4d30d889`; filesystem SHA-256
  `FFC63EA42518CA28CBB11871A9480F74AD278991E31E421C6AC653747D62F80F` →
  `F3FF6AC5227D15099C9777C17C35E7C35FE1461F0057C57AF2665D35754611CB`.
- Independent test:
  `D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider <managed-success>\test_bug.py`, exit `0`,
  `1 passed in 0.06s`.
- Failure thread:
  `01a09ad8-f511-7c51-afdb-bb4e94d0ee03`; requested one synthetic failing
  command, observed JSON command execution `status=failed`, exit `1`, and
  stderr `Write-Error: D2A synthetic expected failure`; post-state source blob,
  tree, and diff were unchanged.
- Standalone cancel/timeout runs independently observed real child/grandchild
  trees and no exact known PIDs after external stop; their complete PID rows
  and argv are in the raw log.

## Acceptance boundary

W2 real evidence is complete for the first approved local Codex target. This
file does not itself declare `D2A_TECHNICAL_PASS`: a fresh independent
read-only reviewer must still inspect the exact candidate and report no P0/P1,
after the targeted, affected, and relevant full Core/Web/build/START reruns are
recorded.
