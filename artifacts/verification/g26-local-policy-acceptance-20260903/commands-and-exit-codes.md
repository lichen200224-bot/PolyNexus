# G26 Commands and Actual Exit Codes — 2026-09-03

All commands ran in `D:/AI學習教材/PolyNexus/artifacts/worktrees/g26-local-policy-acceptance` unless noted.

| Command | Result | Exit |
|---|---|---:|
| `git ls-remote D:/GitBackup/PolyNexus_Backup.git refs/heads/feature/g24-g30-development-completion-routing` | resolved exact `04d37291d45ebbda8453f1b39e30fca523ee1548` | 0 |
| `git --git-dir=D:/GitBackup/PolyNexus_Backup.git merge-base --is-ancestor f4168c31592ac5c886b49d8878f60b99016fdcaf 04d37291d45ebbda8453f1b39e30fca523ee1548` | predecessor ancestry verified | 0 |
| `git status --short --branch` | isolated branch clean before edits | 0 |
| `py -3 -m pytest services/core/tests/test_cp04_wp17_wp18_local_routing.py -q` | no installed Python found (initial environment probe) | 112 |
| `.python312\python.exe -m pytest services/core/tests/test_cp04_wp17_wp18_local_routing.py -q` | 14 tests passed | 0 |
| `set PYTHONPATH=D:\AI學習教材\PolyNexus\artifacts\worktrees\g26-local-policy-acceptance\services\core\src&& .python312\python.exe -m pytest services/core/tests/test_cp04_wp17_wp18_local_routing.py services/core/tests/test_api.py -q --basetemp=artifacts/verification/g26-local-policy-acceptance-20260903/pytest-tmp-targeted` | 29 tests passed | 0 |
| `set PYTHONPATH=D:\AI學習教材\PolyNexus\artifacts\worktrees\g26-local-policy-acceptance\services\core\src&& .python312\python.exe -m pytest services/core/tests/test_run_lifecycle.py services/core/tests/test_runtime_skeleton.py services/core/tests/test_wp09_execution_api.py -q --basetemp=artifacts/verification/g26-local-policy-acceptance-20260903/pytest-tmp-regression` | 1 pre-existing WP-09 lifecycle ordering failure | 1 |
| `set PYTHONPATH=D:\AI學習教材\PolyNexus\artifacts\worktrees\g26-local-policy-acceptance\services/core\src&& .python312\python.exe -m pytest services/core/tests -q --basetemp=artifacts/verification/g26-local-policy-acceptance-20260903/pytest-tmp` | full Core: existing persistence/lifecycle/council/resource-guard failures | 1 |
| `.python312\python.exe scripts/validate_baseline.py` | baseline validation PASS | 0 |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/validate-polynexus-governance.ps1` | governance validation PASS | 0 |
| `node --test extensions/browser-companion/tests/test_websurface_drivers.mjs` | 10 tests passed, 0 failed | 0 |
| `node --check` on all extension JS sources | syntax valid | 0 |
| `node -e JSON.parse(manifest)` | manifest valid | 0 |
| `npm.cmd test --prefix apps/web -- --runInBand` | `vitest` unavailable | 1 |
| `npm.cmd ci --prefix apps/web` with isolated task cache | 90 packages added, 0 vulnerabilities | 0 |
| `npm.cmd test --prefix apps/web` | 80 tests passed, 1 file passed | 0 |
| `npm.cmd run build --prefix apps/web` | TypeScript and Vite production build passed | 0 |
| `node` candidate-file trailing-whitespace scan | no whitespace errors | 0 |
| `rg` no-secret scan over candidate source/docs/evidence | no matches; `rg` no-match result | 1 |
| `rg` Core vendor-selector scan | no matches; `rg` no-match result | 1 |
| `git diff --check` | no whitespace errors | 0 |

The portable Python runtime was used only inside the isolated worktree and is
not part of the staged allowlist. The initial `py -3` exit `112` remains an
environment probe; the later targeted Core evidence is current and passed.

Required but currently unverified: clean-clone checkpoint, full Core regression
cleanliness, HTTP cleanup/cancel, and any live/native browser journey.
Independent review is PASS. No skipped result is treated as PASS. Human
decision is recorded as `G26_DECISION=ACCEPT_AND_COMMIT_PUSH`; the score remains
72/100 with delta 0/12 because full Core regression exited 1.
