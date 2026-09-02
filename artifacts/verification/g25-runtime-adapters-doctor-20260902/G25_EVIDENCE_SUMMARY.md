# G25 Runtime Adapters and Doctor — Evidence Summary

Date: 2026-09-02
Goal: `G25-RUNTIME-ADAPTERS-AND-DOCTOR-ACCEPTANCE`
Predecessor: `61cc7420e290cd93eda787c30b54a93edf4ca9a`
Approved ref: `feature/g24-g30-development-completion-routing`
Base score: `59/100`; candidate maximum: `+13`; candidate target: `72/100`

## Current candidate

The candidate is in the isolated lane
`artifacts/worktrees/g25-runtime-adapters-doctor`. Human authorization
`G25_DECISION=ACCEPT_AND_COMMIT_PUSH` has been received; commit, push, and
checkpoint verification remain pending. The protected primary checkout was not
modified.

WP-14 Codex Runtime Adapter is a deterministic local `EXPERIMENTAL` adapter.
WP-15 OpenCode Runtime Adapter is a deterministic local `EXPERIMENTAL` adapter.
WP-16 Doctor is a bounded `PREVIEW` diagnostic that separates declarations,
probes, failures, and evidence; it does not certify production support.
The companion `ledger.json` records each WP's weight, status, accepted points,
goal ID, checkpoint state, evidence/artifact reference, review result, Human
decision state, limitations, and last-updated date.

## Actual verification and exit codes

All pytest commands used `C:\temp_pn_venv2\Scripts\python.exe -B` in the
isolated lane. The sandbox launcher failure (exit `101`) and the earlier bundled
PowerShell module failure (exit `1`) remain historical environment results;
the current system Windows PowerShell governance run passed with exit `0`.
Governance command: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
-NoProfile -ExecutionPolicy Bypass -File tools\validate-polynexus-governance.ps1`.

| Check | Actual result | Exit |
|---|---|---:|
| WP-14 targeted conformance | 31 passed | 0 |
| WP-15 targeted conformance | 36 passed | 0 |
| WP-16 Doctor/conformance | 58 passed | 0 |
| G18 Doctor compatibility regression | 7 passed | 0 |
| WP-14 + WP-15 + WP-16 combined targeted run | 125 passed | 0 |
| Runtime skeleton + G16 policy + G18 regression | 33 passed | 0 |
| RuntimeBindingSnapshot + persistence/migration | 135 passed; isolated SQLite/Alembic lifecycle covered | 0 |
| Full Core regression | completed at 100%; 1 Windows symlink-policy test skipped; no failure | 0 |
| Earlier Full Core remediation run | failed only on stale uppercase maturity text in the compatibility matrix; fixed and rerun successfully | 1 |
| CP06 packaging/maturity tests | 3 passed | 0 |
| Baseline validator | 11 required files/workflows/MV3 valid | 0 |
| Governance validator | system Windows PowerShell: SOP v1.1 governance files, manifest, JSON and protected-path exclusions valid | 0 |
| `git diff --check` | clean | 0 |
| no-secret scan (`\bsk-[a-z0-9]{10,}\b`) | no matches | 1 (no matches) |
| no-secret scan (`\bapi-key-[a-z0-9]{10,}\b`) | no matches | 1 (no matches) |

The Full Core run retains the non-fatal Windows pytest temporary-directory
cleanup `PermissionError` emitted at interpreter exit. The symlink case remains
explicitly skipped under the host policy.

## Integration and boundaries

The normal Registry `create_adapter()` path still enforces execution-time
capability/auth compatibility. Doctor uses only the private observation factory
to observe declaration/probe failures without changing execution selection.
`doctor_legacy.py` preserves the accepted G18 public surface while the new
`RuntimeDoctorReport` is used for WP-16. No Attempt entity, second Run identity,
vendor-specific Core branch, cloud fallback, credential, cookie, token, real
database migration, external login, or vendor send was introduced.

## Acceptance state

Independent read-only review was routed to the distinct reviewer Carver. The
final remediation review returned `PASS` with `BLOCKER=0`, `MAJOR=0`, and
`MINOR=0`. Until the authorized checkpoint is verified, all three WP scores
remain unearned and project progress remains `59/100`.
