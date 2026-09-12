# D0 commands and exit codes

- Baseline targeted Core tests before edits: `143 passed, 56 warnings`; exit `0`.
- First new D0/reconciliation targeted run: `20 passed, 2 failed`; exit `1`. Both failures were the same test-only tuple-versus-list expectation and were corrected within the first bounded repair.
- D0 plus affected regression: `152 passed, 56 warnings`; exit `0`.
- Writer-review targeted rerun after adding the impossible CREATED-with-claimed-binding case: `23 passed, 1 warning`; exit `0`.
- Final full Core suite (`python -B -m pytest -p no:cacheprovider services/core/tests`): `828 passed, 1 skipped, 192 warnings in 52.41s`; exit `0`.
- `git diff --check`: no output; exit `0`.
- Disposable SQLite database Alembic upgrade to head: `ALEMBIC_HEAD_READY`; exit `0`.
- First live Uvicorn attempt: exit `1`; the shared venv's editable install resolved to the untouched human checkout. No environment change was made.
- Live Uvicorn retry with process-local `PYTHONPATH` to the isolated checkout: application startup complete; health `200`; authenticated projects query `200`; wrong token `403`.
- A second Uvicorn on the occupied port: WinError 10048; exit `1` as expected, followed by clean application shutdown.
- Uvicorn against an empty/non-head database: `Database schema is not at the Alembic head`; exit `1` as expected.
- Health request after bounded service shutdown: `HttpRequestException` as expected.

All pytest temporary files and live-probe databases were outside the repository. No existing migration was modified and no new migration was necessary.
