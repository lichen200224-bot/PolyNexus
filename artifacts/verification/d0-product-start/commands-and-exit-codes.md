# D0 commands and exit codes

- Baseline targeted Core tests before edits: `143 passed, 56 warnings`; exit `0`.
- First new D0/reconciliation targeted run: `20 passed, 2 failed`; exit `1`. Both failures were the same test-only tuple-versus-list expectation and were corrected within the first bounded repair.
- D0 plus affected regression: `152 passed, 56 warnings`; exit `0`.
- Writer-review targeted rerun after adding the impossible CREATED-with-claimed-binding case: `23 passed, 1 warning`; exit `0`.
- First immutable-candidate review verification: full Core `828 passed, 1 skipped`; reviewer verdict `NEED_FIX` for two Core gaps and one apps/start governance exception.
- Repair targeted run: `25 passed, 1 warning in 2.61s`; exit `0`.
- Final repaired full Core suite (`python -B -m pytest -p no:cacheprovider services/core/tests`): `830 passed, 1 skipped, 192 warnings in 51.51s`; exit `0`.
- `git diff --check`: no output; exit `0`.
- Disposable SQLite database Alembic upgrade to head: `ALEMBIC_HEAD_READY`; exit `0`.
- First live Uvicorn attempt: exit `1`; the shared venv's editable install resolved to the untouched human checkout. No environment change was made.
- Live Uvicorn retry with process-local `PYTHONPATH` to the isolated checkout: application startup complete; health `200`; authenticated projects query `200`; wrong token `403`.
- A second Uvicorn on the occupied port: WinError 10048; exit `1` as expected, followed by clean application shutdown.
- Uvicorn against an empty/non-head database: `Database schema is not at the Alembic head`; exit `1` as expected.
- Health request after bounded service shutdown: `HttpRequestException` as expected.
- First sandboxed `npm ci --ignore-scripts`: registry/cache `EACCES`; exit `1`. Authorized retry using the same lockfile and default registry: 90 packages restored; exit `0`.
- Existing Web tests (`npm test`): 2 files and 85 tests passed; exit `0`.
- Existing Web typecheck/build (`npm run build`): `tsc -b` and Vite build passed; exit `0`.
- npm reported 2 existing moderate vulnerabilities. No `npm audit fix`, dependency update, or lockfile change was performed.
- Approved process-only pairing Web tests (`npm test`): 3 files and 89 tests passed; exit `0`.
- Production-token sentinel build (`npm run build` with a synthetic Vite token): typecheck/build passed and `rg` found no sentinel in `dist`; exit `0`.
- Core affected regression (`test_d0_product_start.py`, `test_g14_runtime_reconciliation.py`, `test_health.py`, `test_api.py`): 58 passed, 35 warnings; exit `0`.
- PowerShell parser checked `start.ps1`, `start_core.ps1`, and `start_web.ps1`: exit `0`.
- Direct Core/Web starts with no pairing credential: each child exited `1` with the bounded pairing-not-configured error.
- Fresh START browser journey: process/schema/Core/API-auth/Web-client displayed `ready`; runtime displayed `unknown`; client displayed `authenticated_api_verified`.
- First port-collision cleanup probe found an owned Vite listener left behind; that exact owned PID was stopped and the launcher received one bounded repair.
- Final port-collision probe: launcher exit `1`, pre-existing 8765 owner preserved, owned 5173 listener removed; verification exit `0`.
- Final positive START shutdown: Ctrl+C followed by no listener on 8765 or 5173; exit `0`.

All pytest temporary files and live-probe databases were outside the repository. `node_modules` and `dist` remained ignored test/build outputs. No existing migration was modified and no new migration was necessary.
