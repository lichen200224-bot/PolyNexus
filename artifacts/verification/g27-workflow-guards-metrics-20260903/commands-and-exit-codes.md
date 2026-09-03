# G27 deterministic evidence — 2026-09-03

All commands ran in the isolated lane
`artifacts/worktrees/g27-workflow-guards-metrics`.

The start-gate check compared isolated `HEAD` with the approved remote
`refs/heads/feature/g24-g30-development-completion-routing` and found both at
`7a7dee67395c8a07f2e5b055a306e63190bbd1f8` (exit `0`). The approved G26
product checkpoint and state-sync are recorded in `summary.md`.

| Command | Result | Exit |
|---|---:|---:|
| `C:/temp_pn_venv2/Scripts/python.exe -m pytest -q services/core/tests/test_workflow_loader.py services/core/tests/test_cp05_wp27_golden_workflows.py services/core/tests/test_wp24_resource_guards.py services/core/tests/test_cp06_wp28_failure_injection.py services/core/tests/test_wp25_evaluation_metrics.py` | 40 passed | 0 |
| `C:/temp_pn_venv2/Scripts/python.exe -m pytest -q services/core --maxfail=10` | 720 passed, 1 skipped | 0 |
| `C:/temp_pn_venv2/Scripts/python.exe -m pytest --collect-only -q services/core` | 721 collected | 0 |
| `C:/temp_pn_venv2/Scripts/python.exe scripts/validate_baseline.py` | baseline PASS | 0 |
| `cmd.exe /c C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-polynexus-governance.ps1 .` | governance PASS | 0 |
| `git diff --check` | clean | 0 |
| `git push origin HEAD:refs/heads/feature/g24-g30-development-completion-routing` | remote updated to `27ff09c224344821868dd8fd36ec2c0eb11504df` | 0 |
| `git clone --branch feature/g24-g30-development-completion-routing --single-branch D:/GitBackup/PolyNexus_Backup.git artifacts/verification/g27-clean-clone-20260903` | clean clone created | 0 |
| remote SHA + clean-clone SHA/status comparison | matching SHA; clean | 0 |

The one skipped Core test is the existing Windows symlink-policy case. Pytest
also emits a non-fatal Windows temp-directory cleanup warning at process exit;
the recorded process exit remains `0`.
