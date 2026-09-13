# D2a W2 raw evidence transcription — 2026-09-13

This is the in-lane, immutable transcription of the necessary raw evidence
from the approved real-executor runs. It contains no credential values. The
executor prompt was synthetic and case-specific; the exact fixed CLI argv,
full cwd, actual inner command, source facts, process rows, exit, and cleanup
PID set are recorded for each case.

## Common transport facts

- Executor:
  `C:\Users\shawn\AppData\Local\OpenAI\Codex\bin\bffc5354119c8421\codex.exe`.
- `codex --version`: `codex-cli 0.154.0-alpha.6.2`, exit `0`.
- Executable SHA-256:
  `081E4DE4BE8E38FAC6ED4D95E3B1A0B9F6D31C090DDC36E1696B349FE406F575`.
- All standalone runs used these fixed argv tokens; the `--cd` value is the
  full case cwd shown in each case below, followed by its synthetic prompt
  token:

  ```text
  C:\Users\shawn\AppData\Local\OpenAI\Codex\bin\bffc5354119c8421\codex.exe exec --ephemeral --ignore-user-config --ignore-rules -c windows.sandbox="elevated" --cd
  ```

- All candidate-adapter runs used these fixed argv tokens; `--cd` was followed
  by the full staging cwd shown in each adapter case below and its synthetic
  prompt token:

  ```text
  C:\Users\shawn\AppData\Local\OpenAI\Codex\bin\bffc5354119c8421\codex.exe exec --ephemeral --ignore-user-config -c windows.sandbox="elevated" --sandbox workspace-write --json --cd
  ```

- No danger/bypass flag was used. The prompt scope was limited to the listed
  synthetic fixture; no parent path, credential, network service, or user
  repository was accessed.
- Fixture baseline for all positive runs: Git
  `99e204e79d27b879b41a8e0d37e51052499d3196`, tree
  `ae3cb6f9ce3fee3eec09b7d1fcaad21608141f6d`.

## Standalone real executor cases

### W2-SUCCESS

- Full cwd:
  `C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\artifacts\verification\d2a-20260913\fixtures\codex-managed-success-evidence-20260913`.
- Thread: `01a09ad7-11da-7e41-9a75-8ffcb5e39d30`.
- Outer exit: `0`; observed command executions exit `0`.
- Actual inner command:

  ```text
  "C:\Users\shawn\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe" -Command "Get-Location`nGet-FileHash -LiteralPath .\\bug.py -Algorithm SHA256"
  ```

- First cwd output matched the full cwd above.
- `bug.py` filesystem SHA-256 before/after:
  `FFC63EA42518CA28CBB11871A9480F74AD278991E31E421C6AC653747D62F80F` →
  `F3FF6AC5227D15099C9777C17C35E7C35FE1461F0057C57AF2665D35754611CB`.
- Git blob before/after:
  `4564ab261c7570752a00bfe7f281a945e5fcf951` →
  `4860f406c7a4c121fe0cd7d1b1c1314b4d30d889`.
- Codex emitted a completed file change for only `bug.py`; diff was exactly
  `return 41` → `return 42`.
- Focused verification command:

  ```text
  D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\artifacts\verification\d2a-20260913\fixtures\codex-managed-success-evidence-20260913\test_bug.py
  ```

  Exit `0`; `1 passed in 0.06s`.

### W2-CANCEL

- Full cwd:
  `C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\artifacts\verification\d2a-20260913\fixtures\codex-managed-cancel-20260913`.
- Thread: `01a09ad3-0d8f-7db3-9ef4-f37694bfd7df`.
- Actual inner command:

  ```text
  "C:\Users\shawn\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe" -Command "pwsh -NoLogo -NoProfile -NonInteractive -File .\\long_task.ps1"
  ```

- JSON command execution reached `status=in_progress`; external cancel was
  then sent to the real Codex session. Outer exit `1`; no terminal success.
- Pre-cancel process rows:

  ```text
  root Codex PID 25416
  executor script PID 10252 parent=25416
  child PID 17844 parent=10252
  grandchild PID 17592 parent=17844
  conhost PID 17556 parent=17844
  conhost PID 22372 parent=17592
  ```

- Post-cancel cleanup query target set:
  `25416,10252,17844,17592,17556,22372`; result: no rows.
- Source remained baseline blob
  `4564ab261c7570752a00bfe7f281a945e5fcf951` and filesystem SHA-256
  `FFC63EA42518CA28CBB11871A9480F74AD278991E31E421C6AC653747D62F80F`.

### W2-TIMEOUT

- Full cwd:
  `C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\artifacts\verification\d2a-20260913\fixtures\codex-managed-timeout-repo-20260913`.
- Thread: `01a09ad5-5bf6-7d41-964d-7a9fb8ad8d5b`.
- Actual inner command was the full `long_task.ps1` command shown in
  W2-CANCEL and reached `command_execution status=in_progress`.
- Bounded external supervisor observed the `15.0s` deadline and sent timeout
  cancellation. Outer exit `1`; no terminal success result.
- Pre-timeout process rows:

  ```text
  root Codex PID 34284
  executor script PID 13284 parent=34284
  child PID 5676 parent=13284
  grandchild PID 13520 parent=5676
  conhost PID 21524 parent=5676
  conhost PID 36292 parent=13520
  ```

- Post-timeout cleanup query target set:
  `34284,13284,5676,13520,21524,36292`; result: no rows.
- Source remained baseline with no diff.
- The installed CLI has no native `--timeout` flag; this is explicitly an
  external-supervisor timeout observation, not a native CLI timeout claim.

### W2-FAILURE

- Full cwd:
  `C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\artifacts\verification\d2a-20260913\fixtures\codex-managed-failure-20260913`.
- Thread: `01a09ad8-f511-7c51-afdb-bb4e94d0ee03`; outer exit `0`.
- Requested command:

  ```text
  pwsh -NoLogo -NoProfile -NonInteractive -Command "Write-Error 'D2A synthetic expected failure'; exit 17"
  ```

- Actual JSON command execution was wrapped by runtime PowerShell and
  reported `status=failed`, `exit_code=1`, stderr
  `Write-Error: D2A synthetic expected failure`. Codex final result exit was
  `1`, not the requested inner `17`.
- Post-state stayed at baseline HEAD/tree/source blob/SHA-256; Git diff empty.

## Candidate-adapter cases

### Adapter success

- Managed source cwd:
  `C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\artifacts\verification\d2a-20260913\fixtures\codex-managed-adapter-fixed-20260913`.
- Staging cwd:
  `C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\artifacts\verification\d2a-20260913\fixtures\staging_87f7ae23ea4a7a334038e997`.
- Runtime reference: `codex-exec:e6fd379e2c55489aa89c42e147299544`.
- Binding before `create_run`: `run_adapter_fixed` / `task_1`.
- Actual argv fixed tokens included the full staging cwd above; final state:
  `RUNNING` → `COMPLETED`, `cleanup=True`.
- Root PID `39544`, exit `0`, signal `none`, stopped `true`, stdout `3095`
  bytes, stderr `0` bytes.
- Normalized result:
  `{"format":"codex.exec.jsonl.v1","event_count":11,"terminal_type":"turn.completed"}`.
- Envelope SHA-256:
  `ee2b75885c1f4cc786d581d94bf8105c4a8402da55ba09535a8dac4da84ed70e`.
- Effective config fingerprint:
  `9f9bcae6f8ca21f0fd44df3ede2a121f0dcb8591e242d2b0038ccd942e41ab6d`.
- Permission policy fingerprint:
  `087be0f77d8f2cbc74097171536ceb971bad60f7f4dfe7fc4a50298c9936a853`.
- Route-policy evidence SHA-256:
  `59ac875107670d94ac0e2667e565c2334e19b991ec52a799dcc10cc600705166`.
- Auth ownership `RUNTIME_MANAGED`; provider-model egress `RUNTIME_MANAGED`;
  agent-extension egress `DENY`.
- Source manifest before/after:
  `c76a68598804445a0e9f36978b1ea4c5ebe715b28978ab28bd684b16f6c90db9` →
  `d17eadb9ba8940662ec65c3dbe067eed209affa83343e362f680272747ba54c3`.
- Allowlisted diff was `bug.py: return 41 → return 42`; imported Core content
  blob SHA-256/name `e68e6376c03551c78ce56204c4ed6c15727ce4a4e06a02677dd371b0bf976484`,
  size `155` bytes. Managed source remained baseline.

### Adapter cancel

- Staging cwd:
  `C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\artifacts\verification\d2a-20260913\fixtures\staging_de2681ad98717ab7f6c5034f`.
- Runtime reference: `codex-exec:ea8af6256dbf48ebb794ff1043b98b8b`.
- State `RUNNING` → `CANCELLED`; `cleanup=True`.
- Root Codex PID `36220`; executor `40504`, child `40700`, grandchild
  `40948`; root exit `1`, signal `job_terminate`, stopped `true`.
- Post-stop cleanup query target set `36220,40504,40700,40948`; result: no
  rows for root or any manifest PID.

### Adapter true deadline timeout

- Staging cwd:
  `C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\artifacts\verification\d2a-20260913\fixtures\staging_7780b8b14709c6e6b12395f4`.
- Runtime reference: `codex-exec:43bfee75fa93448f851a3b2e8595cbb8`.
- State `RUNNING` → `TIMED_OUT`; `cleanup=True`.
- Deadline budget `15.0s`; manifests ready at `9.344s`; stop trigger at
  `15.047s`.
- Root Codex PID `41708`; executor `41084`, child `39984`, grandchild
  `29944`; root exit `1`, signal `job_terminate`, stopped `true`.
- Post-stop cleanup query target set `41708,41084,39984,29944`; result: no
  row for any exact root/manifest PID. An unrelated `git-daemon` flow process
  had a numerically reused parent PID and was not touched.

## Negative/history boundary

- The former adapter argv without the Windows inline configuration exited
  `0` but produced no allowlisted source change; the adapter failed closed
  with `allowlisted_source_change_missing` and no source was mutated.
- The pre-approval host-policy rejection is historical `BLOCKED / NOT PASS`
  evidence and is not used as the positive real-executor gate.
- Windows symlink/reparse capability remains environment-unverified because
  the corresponding Core test was skipped; no pass claim is made for that OS
  privilege boundary.
