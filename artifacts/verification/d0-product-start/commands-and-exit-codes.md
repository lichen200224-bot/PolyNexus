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

All pytest temporary files and live-probe databases were outside the repository. No existing migration was modified and no new migration was necessary.
