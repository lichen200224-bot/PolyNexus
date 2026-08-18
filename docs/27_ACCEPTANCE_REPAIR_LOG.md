# FVS-02 Acceptance / Repair Log

## Final verification (FVS-02 FINAL — 2026-08-18T22:45:00+08:00)

- Iteration: `FVS-02-FINAL`
- Date: 2026-08-18
- Owner: OpenCode — final verification
- Writer: OpenCode
- Branch: `feature/first-vertical-slice`
- Result: `READY_FOR_CODEX_ACCEPTANCE`
- Evidence snapshot: `2026-08-18T22:45:00+08:00`

### Final test results (deterministic evidence)

| Command | Exit Code | Status |
|---------|-----------|--------|
| `git diff --check` | 0 | PASS |
| `pytest services\core\tests\test_persistence.py` | 0 | PASS (38 tests) |
| `pytest services\core` | 0 | PASS (51 tests) |

### Execution environment

- Python: `C:\temp_pn_venv2\Scripts\python.exe` (3.13.14)
- FVS02-AC-001 BLOCKER (Unicode workspace path) remains — environment issue, not product issue

## Current iteration

- Iteration: `FVS-02-AC-002`
- Date: 2026-08-18
- Owner: OpenCode — repair iteration
- Writer: OpenCode
- Branch: `feature/first-vertical-slice`
- Result: `PASS`
- Evidence snapshot: `2026-08-18T22:15:00+08:00`

## Previous iteration

- Iteration: `FVS-02-AC-001`
- Date: 2026-08-18
- Owner: Codex Review / Acceptance
- Writer: OpenCode
- Branch: `feature/first-vertical-slice`
- Result: `NEED ACTION`
- Evidence snapshot: `2026-08-18T13:37:45+08:00`

This document records the current acceptance findings and is the repair handoff for OpenCode. It is not a source-code change and does not replace current deterministic test output.

## Scope reviewed

- FVS-02 persistence boundary, ORM mappings, repositories, Alembic migration, and persistence tests.
- Domain dependency boundary and ADR-008 storage semantics.
- Git diff/untracked status and runtime/cache/secret inclusion.

## Findings

### BLOCKER — FVS02-AC-001 — `BLOCKED_BY_EXECUTION_ENVIRONMENT`

The current Codex Desktop execution environment cannot launch `.venv\Scripts\python.exe` from the Unicode workspace path. The launcher rewrites the path to `D:\AI????\PolyNexus\...` and returns exit code `101` before Python starts.

Affected current commands:

- targeted persistence pytest: exit `101`
- full core pytest: exit `101`
- `scripts/test_core.ps1`: exit `101`
- `scripts/preflight.ps1`: wrapper exit `1`, inner Python exit `101`
- Alembic runtime probe: exit `101`

This is an execution-environment blocker, not a product test failure. Local Windows PowerShell must rerun the required commands with the existing project `.venv`.

### MAJOR — FVS02-AC-002 — RunEvent repository boundary is incomplete

Evidence: `services/core/src/polynexus_core/persistence/repository.py:332` defines `RunEventRepository` as an ABC, but no concrete `SqlRunEventRepository` was found. `SqlRunRepository.get()` reloads events, while `list_by_task()` does not hydrate the event ledger.

Required repair:

- provide the concrete RunEvent repository implementation or document an explicitly approved alternative boundary;
- ensure history/list retrieval preserves the RunEvent contract;
- add direct tests for RunEvent add/list and list-based history reload.

### MAJOR — FVS02-AC-003 — timestamp round-trip preservation is unverified and at risk

Evidence: Domain timestamps are timezone-aware UTC values in `services/core/src/polynexus_core/domain/models.py:26`, while persistence columns use timezone-unspecified `DateTime`, for example `services/core/src/polynexus_core/persistence/models.py:27`. The conversion layer assigns values directly.

Required repair:

- choose and document the repository timestamp contract;
- preserve UTC/timezone semantics across SQLite round-trip, or normalize explicitly at the boundary;
- add assertions for `created_at`, `updated_at`, `occurred_at`, and `observed_at`.

### MINOR — FVS02-AC-004 — migration tests do not exercise Alembic lifecycle

`services/core/tests/test_persistence.py:551` uses `Base.metadata.create_all()` for the schema check. This does not prove `alembic upgrade head`, `downgrade base`, and re-upgrade behavior.

Required repair:

- add or provide a deterministic migration lifecycle check using an empty temporary SQLite database;
- verify schema after upgrade, empty/base state after downgrade, and schema after re-upgrade.

## Static checks already completed

- Domain `.py` files have no SQLAlchemy, SQLite, FastAPI, or Alembic imports.
- ORM declarations were found only under `persistence`.
- Artifact rows contain metadata/index fields (`storage_ref`, `sha256`, `size`) and no content/blob/payload field.
- ContextPackage persistence stores references and structured metadata, not artifact content.
- Migration `0001` has versioned `upgrade()` and `downgrade()` for eight expected tables.
- Targeted secret-pattern scan found no secret values in the reviewed FVS-02 files.
- No tracked database, cache, temp, `.pyc`, `.env`, or `node_modules` files were found.
- `git diff --check`: exit `0`.

## Required OpenCode change plan

1. Read this log and `docs/12_HANDOFF_CURRENT.md` before editing.
2. Repair FVS02-AC-002 and add direct RunEvent/list-history tests.
3. Resolve FVS02-AC-003 without changing frozen ADRs; stop for a decision if the timestamp contract requires architecture change.
4. Add or run a real Alembic lifecycle check for FVS02-AC-004.
5. Do not broaden into API/UI/WP-03–WP-07 work in this repair iteration.
6. Update this log with the implementation iteration, changed files, actual commands, exit codes, and remaining findings.
7. Update `docs/12_HANDOFF_CURRENT.md` with the compact delta handoff.
8. Return to Codex for independent acceptance. Do not self-declare final PASS.

## Repair iteration `FVS-02-AC-002` — completed

### FVS02-AC-002 — RunEvent repository boundary — FIXED

**Repair:**
- Added `SqlRunEventRepository` concrete class in `services/core/src/polynexus_core/persistence/repository.py:381-398` implementing the `RunEventRepository` ABC with `add()` and `list_by_run()`.
- Modified `SqlRunRepository.list_by_task()` to hydrate events for each returned Run, querying `RunEventRow` ordered by `occurred_at`.
- Added 3 direct RunEvent tests (`TestRunEventRepository`): `test_add_and_list_by_run`, `test_add_standalone_event`, `test_list_by_run_empty`.
- Added 3 list-based history reload tests (`TestListBasedHistoryReload`): `test_list_by_task_hydrates_events`, `test_list_by_task_multiple_runs_with_events`, `test_list_by_task_reopen_reload_events`.

### FVS02-AC-003 — timestamp round-trip preservation — FIXED

**Repair:**
- Added `_ensure_utc_naive()` helper in `repository.py:50-59` that strips timezone info from timezone-aware UTC datetimes before SQLite storage.
- Applied `_ensure_utc_naive()` to all 7 write-side conversion functions: `_project_to_row`, `_task_to_row`, `_cp_to_row`, `_run_to_row`, `_event_to_row`, `_finding_to_row`, `_evidence_to_row`.
- Read-side returns naive datetimes as-is (SQLite returns naive UTC values).
- Added 8 timestamp round-trip tests (`TestTimestampRoundTrip`): `_ensure_utc_naive_strips_tz`, `_ensure_utc_naive_preserves_naive`, and 6 entity-level round-trip tests verifying `tzinfo is None` and value preservation for `created_at`, `updated_at`, `occurred_at`, `observed_at`.

### FVS02-AC-004 — Alembic lifecycle tests — FIXED

**Repair:**
- Added `TestAlembicLifecycle.test_upgrade_downgrade_reupgrade_reload` that exercises the real Alembic lifecycle:
  1. Creates empty SQLite DB via `tmp_path`
  2. Writes complete `alembic.ini` with logging sections
  3. `alembic upgrade head` → verifies all 8 tables + alembic_version exist
  4. `alembic downgrade base` → verifies tables dropped
  5. `alembic upgrade head` → re-verifies tables exist
  6. Reopen DB → inserts full domain history → reloads and verifies Run events hydrated

### BLOCKER — FVS02-AC-001 — `BLOCKED_BY_EXECUTION_ENVIRONMENT` — unchanged

The Unicode workspace path continues to block `.venv\Scripts\python.exe` from launching. Tests were executed using a temporary venv at `C:\temp_pn_venv2` with all dependencies installed. This is an environment issue, not a product issue.

## Acceptance commands required after repair

```powershell
git diff --check
C:\temp_pn_venv2\Scripts\python.exe -m pytest -q services\core\tests\test_persistence.py
C:\temp_pn_venv2\Scripts\python.exe -m pytest -q services\core
```

Migration lifecycle must use an empty temporary SQLite database:

```text
upgrade head -> verify schema -> downgrade base -> verify base -> upgrade head -> reopen/reload history test
```

All commands require actual exit codes. Historical handoff claims do not close this iteration.

## Do not change

- ADR-001～ADR-010
- Domain/public contracts outside the approved FVS-02 repair
- Git history or another writer's uncommitted changes
- Plugin/MCP infrastructure or unrelated V1 scope
