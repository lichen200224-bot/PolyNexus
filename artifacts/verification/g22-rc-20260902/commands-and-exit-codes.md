# G22 RC hardening and delivery closeout evidence

Generated 2026-09-01T23:35:55.8975168Z (UTC). Branch:
`feature/g22-rc-hardening-cross-machine-delivery-closeout`. Predecessor:
`ada5e9c8b4873aad4c53c74198171740d376d926`.

| Exact command / check | Actual result | Exit code |
|---|---|---:|
| `C:\temp_pn_venv2\Scripts\python.exe -m pytest -q services/core` (sandbox attempt) | controlled launcher could not create process | 101 |
| `C:\temp_pn_venv2\Scripts\python.exe -m pytest -q services/core` (approved elevation) | full Core suite passed; one existing symlink-policy skip remained visible | 0 |
| `C:\temp_pn_venv2\Scripts\python.exe -m pytest --disable-warnings -rA services/core/tests/test_cp06_wp28_failure_injection.py services/core/tests/test_cp06_wp29_security_policy.py services/core/tests/test_cp06_wp30_clean_install.py services/core/tests/test_cp06_wp31_packaging_compatibility.py services/core/tests/test_g17_migration_restore_authority.py services/core/tests/test_wp23_backup_restore_migration.py` | 21 passed | 0 |
| `node --test extensions/browser-companion/tests/test_websurface_drivers.mjs` | 9/9 passed, including encoded traversal cases | 0 |
| `node --input-type=module -e '<encoded traversal supplementary matrix>'` | 15 unsafe rejected cases and 2 valid loopback cases passed | 0 |
| `npm ci` from `apps/web` (sandbox attempt) | npm cache/node_modules EPERM | -4048 |
| `npm ci` from `apps/web` (approved elevation) | 90 packages added, 91 audited, 0 vulnerabilities | 0 |
| `npm test` from `apps/web` | Vitest 80/80 passed | 0 |
| `npm run build` from `apps/web` | TypeScript/Vite production build passed | 0 |
| `C:\temp_pn_venv2\Scripts\python.exe -B scripts/validate_baseline.py` (sandbox attempt) | controlled launcher could not create process | 101 |
| `C:\temp_pn_venv2\Scripts\python.exe -B scripts/validate_baseline.py` (approved elevation) | 11 required files; workflows valid; MV3 valid | 0 |
| `powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate-polynexus-governance.ps1 .` | governance package and protected exclusions valid | 0 |
| `node artifacts/verification/g21-browser-20260902/run-g21-browser-evidence.mjs --artifact=artifacts/verification/g22-rc-20260902-browser --extension=extensions/browser-companion --pfx=C:\Users\hikar\AppData\Local\Temp\pn-g21-browser-20260902\fixture.pfx --port=9262` | fresh G22 browser attempt could not connect to CDP | 1 |
| G21 predecessor harness artifact `artifacts/verification/g21-browser-20260902` | 3/3 golden, 28/28 failure assertions, observed external requests 0, cleanup PASS | 0 |

The G21 predecessor harness uses `exit_code: "N/A"` for in-process matrix
assertions and preserves aggregate process exit `0`. The fresh G22 browser
attempt is explicitly `NEED_ACTION`; it does not upgrade the predecessor
evidence or claim native MV3 worker/live-vendor support.

The validated product checkpoint is `532ce8f1c479a3c593c990ede89b5b75e810762f`,
with clean clone `g22-clean-20260902` reproducing the required gates. The later
independently reviewed evidence-state tip is `9a17716f87e4df14def5086bafee6d86d3484596`,
with final clean clone `g22-clean-final-20260902` matching the approved remote
tip and passing required-path, manifest, and baseline checks. The current final
branch tip is resolved from the approved remote and its exact SHA is published
in the completion result rather than embedded in this self-referential artifact.
