# Current Handoff

## Task
First Vertical Slice

## Status
Previous: WP-07 Integration Acceptance — ACCEPTED and checkpointed at `d7060c4`.
Current: FVS-MILESTONE-UI-E2E-01 attempt 1 — ACCEPTED WITH HUMAN WAIVER.
Next: Continue development; Browser E2E remains UNVERIFIED/SKIPPED and must be rerun after development is complete.

Acceptance repair log: `docs/27_ACCEPTANCE_REPAIR_LOG.md`

Task document: `docs/20_FIRST_VERTICAL_SLICE_PLAN.md` (WP-07 accepted; UI/Core milestone acceptance recorded below; Browser E2E deferred).
Historical task document: `docs/tasks/FVS-03.md`

## Active Writer
NONE — WP-07 and FVS-MILESTONE-UI-E2E-01 acceptance completed; no active writer.

## Reviewer
Codex — independently reviewed FVS-MILESTONE-UI-E2E-01; Human waiver accepted the documented Browser E2E limitation.

## Antigravity
COMPLETED read-only verification for FVS-MILESTONE-UI-E2E-01; Browser DOM / Playwright E2E is UNVERIFIED/SKIPPED.

## Starting Branch
feature/first-vertical-slice

## Goal
Deliver the first real PolyNexus end-to-end product path:

Project
→ Review Task
→ ContextPackage
→ WorkflowDefinition
→ Reference/Mock Runtime
→ Run Supervisor
→ Finding + Evidence
→ Persist
→ Result
→ Reload History

## Confirmed Baseline
- ADR-001 through ADR-010 frozen.
- Windows development environment accepted.
- OpenCode onboarding PASS.
- Codex onboarding PASS.
- Antigravity onboarding PASS.
- Git backup available at D:\GitBackup\PolyNexus_Backup.git.

## Tool Assignment

### Codex
First writer:
- domain boundaries
- run supervisor
- workflow execution contracts
- evidence/context/artifact integration boundaries

### OpenCode
Second writer:
- persistence implementation
- API wiring
- tests
- routine integration work

### Antigravity
Milestone verifier:
- UI/E2E only after vertical slice becomes runnable

## FVS-01 Update

### Goal
Implement the minimum Domain / Execution Skeleton for Project, Task, Run, Artifact, ContextPackage, Evidence, Finding, normalized Run lifecycle, Runtime Adapter boundary, and Workflow execution boundary.

### Changed files
- `services/core/src/polynexus_core/domain/enums.py`
- `services/core/src/polynexus_core/domain/models.py`
- `services/core/src/polynexus_core/runtime/contracts.py`
- `services/core/src/polynexus_core/runtime/reference.py`
- `services/core/src/polynexus_core/runtime/supervisor.py`
- `services/core/src/polynexus_core/workflows/models.py`
- `services/core/src/polynexus_core/workflows/execution.py`
- `services/core/src/polynexus_core/workflows/loader.py`
- `services/core/tests/test_domain_models.py`
- `services/core/tests/test_runtime_skeleton.py`
- `services/core/tests/test_workflow_loader.py`

### Implemented
- Stdlib-only Domain dataclasses with stable IDs and structured ContextPackage references.
- Reference in-memory RuntimeAdapter only; no Codex/OpenCode runtime integration.
- Core-owned RunSupervisor with normalized start/collect/cancel lifecycle and cleanup verification.
- Canonical WorkflowDefinition normalization while preserving existing raw loader behavior.
- Explicit RUNTIME_EVIDENCE separation from AI_OPINION and tests for evidence/status values.

### Tests and validation
- `git diff --check`: PASS, exit code 0.
- `services/core/tests/test_domain_models.py`, `test_runtime_skeleton.py`, `test_workflow_loader.py` via `.venv` pytest: blocked by Unicode workspace process launch, exit code 1.
- `scripts/test_core.ps1`: blocked when launching `.venv\Scripts\python.exe`, exit code 101.
- `scripts/preflight.ps1`: baseline validator launch blocked by the same issue; wrapper exit code 1, inner Python launch exit code 101.

### Known blocker
The existing `.venv\Scripts\python.exe` cannot be launched from the current Codex Desktop sandbox because the workspace path contains Chinese characters and the process launcher converts it to `????`. No dependency or environment setting was changed. Current pytest and baseline validation results remain UNVERIFIED.

### Next
Rerun `scripts/test_core.ps1` and `scripts/preflight.ps1` from an environment that can launch the existing project Python runtime. After deterministic validation passes, continue with WP-02 persistence/repository work.

## FVS-02 Update

### Goal
Persistence / Repository / Migration — make FVS-01 Domain / Execution Skeleton durable and reloadable.

### Changed files
- `services/core/src/polynexus_core/persistence/__init__.py` (new)
- `services/core/src/polynexus_core/persistence/database.py` (new)
- `services/core/src/polynexus_core/persistence/models.py` (new)
- `services/core/src/polynexus_core/persistence/repository.py` (new, modified in repair)
- `services/core/alembic.ini` (new)
- `services/core/alembic/env.py` (new)
- `services/core/alembic/script.py.mako` (new)
- `services/core/alembic/versions/0001_initial_schema.py` (new)
- `services/core/tests/test_persistence.py` (new, modified in repair)

### Implemented
- SQLAlchemy ORM models mapping Domain dataclasses to SQLite tables (metadata/state/index only per ADR-008).
- Repository interfaces (ABC) for Project, Task, ContextPackage, Run, RunEvent, Artifact, Finding, Evidence.
- SQLite repository implementations with Domain↔ORM conversion boundary.
- `SqlRunEventRepository` concrete implementation with `add()` and `list_by_run()`.
- `SqlRunRepository.list_by_task()` now hydrates RunEvent history for each returned Run.
- Timestamp contract: `_ensure_utc_naive()` normalizes timezone-aware UTC datetimes to naive UTC at the write boundary; read returns naive UTC as-is.
- Alembic initial migration (0001_initial_schema) with 8 tables: projects, tasks, context_packages, runs, run_events, artifacts, findings, evidence.
- JSON serialization for tuple/list fields (instructions, constraints, artifact_refs, evidence_refs, etc.).
- ContextPackage reference-based persistence (no artifact content in SQLite).
- Artifact SHA-256 identity field preserved.
- Run lifecycle state + events + result persistence.
- Full history reload from reopened database.
- Real Alembic lifecycle test: upgrade head → verify → downgrade base → verify → upgrade head → reopen/reload.

### DB schema summary
8 tables: `projects`, `tasks`, `context_packages`, `runs`, `run_events`, `artifacts`, `findings`, `evidence`. All string IDs, datetime fields, JSON-serialized tuple/list fields. No artifact content stored in SQLite.

### Repository boundaries
- Domain dataclasses remain stdlib-only; no SQLAlchemy/FastAPI dependency.
- All persistence goes through Repository ABC interfaces.
- ORM models are internal to `persistence` package only.
- No raw SQL in application code.

### Tests and validation (FVS-02 FINAL — 2026-08-18T22:45:00+08:00)
- `services/core/tests/test_persistence.py`: 38 tests — PASS, exit code 0.
- Full `services/core` pytest: 51 tests — PASS, exit code 0.
- `git diff --check`: PASS, exit code 0.
- Execution environment: temp venv `C:\temp_pn_venv2\Scripts\python.exe` (Python 3.13.14).
- FVS02-AC-001 BLOCKER (Unicode workspace path) remains — environment issue, not product issue.

### Codex acceptance findings (all resolved in `FVS02-AC-002` repair)
- ~~MAJOR: `RunEventRepository` has an ABC but no concrete `SqlRunEventRepository`; list-based Run history does not hydrate events.~~ FIXED.
- ~~MAJOR: timezone-aware Domain timestamps use timezone-unspecified persistence columns; round-trip preservation needs an explicit contract and tests.~~ FIXED.
- ~~MINOR: persistence migration tests use `Base.metadata.create_all()` rather than the Alembic upgrade/downgrade lifecycle.~~ FIXED.

### Test count
- New persistence tests: 38
- Total project tests: 51

### ADR impact
None. ADR-008 fully respected: SQLite stores metadata/state/index only; artifact content boundary preserved; ContextPackage uses reference-based persistence.

### Scope deviation
None. All work within FVS-02 scope (WP-02).

### Next
- **OpenCode**: Read `docs/tasks/FVS-03.md` and implement only the planned API foundation on `feature/first-vertical-slice`.
- **OpenCode**: Run required deterministic tests and record actual counts/exit codes.
- **OpenCode**: Stop and escalate if authenticated loopback behavior needs a new token/pairing/SecretStore decision.
- **Codex**: Independently accept FVS-03 only after the Writer reports `READY_FOR_CODEX_ACCEPTANCE`.

## FVS-03 Update

### Goal
Core API Foundation — persistence-backed Project / Task / Run endpoints with authenticated loopback boundary.

### Changed files
- `services/core/src/polynexus_core/api/dependencies.py` (new, modified in repair)
- `services/core/src/polynexus_core/api/schemas.py` (new, modified in repair)
- `services/core/src/polynexus_core/api/projects.py` (new)
- `services/core/src/polynexus_core/api/tasks.py` (new)
- `services/core/src/polynexus_core/api/runs.py` (new)
- `services/core/src/polynexus_core/app.py` (modified, modified in repair)
- `services/core/tests/test_api.py` (new, modified in repair)

### Implemented
- Authenticated loopback dependency (`require_loopback`) with test-only override; production default fail closed.
- **B-01 repair**: When `LOOPBACK_TOKEN` env var is not set, ALL non-health requests return 403 (fail closed). Arbitrary non-empty token does NOT bypass auth.
- Pydantic request/response DTOs isolating Domain dataclasses from HTTP layer.
- **M-02 repair**: Custom `field_validator` rejects whitespace-only `ProjectCreate.name` and `TaskCreate.title` at the API layer (422), preventing unhandled 500 from Domain `__post_init__`.
- `POST /api/v1/projects`, `GET /api/v1/projects`, `GET /api/v1/projects/{project_id}` — full Project CRUD.
- `POST /api/v1/projects/{project_id}/tasks`, `GET /api/v1/projects/{project_id}/tasks`, `GET /api/v1/tasks/{task_id}` — Task CRUD with parent/child validation.
- `POST /api/v1/tasks/{task_id}/runs`, `GET /api/v1/tasks/{task_id}/runs`, `GET /api/v1/runs/{run_id}` — Run persistence/query; creates CREATED record only, no runtime execution.
- Cross-project ContextPackage reference rejection.
- Invalid payload → 422, unknown ID → 404, unauthorized caller → 403.
- API routes do not import ORM models or raw SQL; no hard-coded secrets.
- `create_app()` backward compatible (no-argument call preserved).
- **M-01 repair**: Lif lifespan handler initialises database engine + creates tables on startup, disposes on shutdown. Default app data routes do not 500 from missing session factory.

### Architecture / boundary summary
- API layer uses Pydantic DTOs; routes call Repository ABCs only.
- DB session injected via FastAPI `Depends`; tests override with temporary SQLite.
- Auth boundary: `X-Loopback-Token` header validated against `LOOPBACK_TOKEN` env var; when not configured, all non-health requests denied (fail closed).
- Run creation is persistence-only — no `RunSupervisor.start()`, no `RuntimeAdapter`, no forged evidence.
- Lifespan lifecycle: `POLYNEXUS_DATABASE_URL` env var → `init_engine()` → `create_all()` on startup.

### Tests and validation (FVS-03 REPAIR — 2026-08-19)
- `services/core/tests/test_api.py`: 32 tests — PASS, exit code 0.
- `services/core/tests/test_health.py`: 1 test — PASS, exit code 0.
- `services/core/tests/test_persistence.py`: 38 tests — PASS, exit code 0.
- Full `services/core` pytest: 83 tests — PASS, exit code 0.
- `git diff --check`: PASS, exit code 0.
- `scripts/validate_baseline.py`: PASS, exit code 0.
- Execution environment: temp venv `C:\temp_pn_venv2\Scripts\python.exe` (Python 3.13.14).

### Test count
- New API tests: 32
- Total project tests: 83

### ADR impact
None. ADR-002 (FastAPI/asyncio), ADR-004 (UI/Core boundary), ADR-007 (RunSupervisor), ADR-008 (SQLite metadata), ADR-010 (loopback auth) all respected.

### Scope deviation
None. All work within FVS-03 scope.

### Known limitations
- FVS02-AC-001 BLOCKER (Unicode workspace path) remains — environment issue, not product issue.
- `scripts/test_core.ps1` and `scripts/preflight.ps1` cannot run from Codex Desktop sandbox due to Unicode path.

### Next
- **Codex**: Independently accept FVS-03 after the Writer reports `READY_FOR_CODEX_ACCEPTANCE`.
- **OpenCode**: After acceptance, proceed with FVS-04 or WP-06 (UI scaffold).

## WP-06 Update

### Goal
Minimal React UI for Project and Task flows on top of the existing FVS-03 API, without changing backend contracts or adding authentication architecture.

### Changed files
- `apps/web/src/api.ts` (new)
- `apps/web/src/App.tsx` (rewritten)
- `apps/web/src/App.test.tsx` (rewritten)
- `apps/web/src/styles.css` (extended)
- `apps/web/src/components/ProjectList.tsx` (new)
- `apps/web/src/components/CreateProjectForm.tsx` (new)
- `apps/web/src/components/TaskList.tsx` (new)
- `apps/web/src/components/CreateTaskForm.tsx` (new)
- `apps/web/src/components/RunPreparation.tsx` (new)
- `apps/web/vite.config.ts` (modified — added `/api` proxy to `127.0.0.1:8765`)
- `apps/web/vitest.config.ts` (new)
- `apps/web/tsconfig.json` (modified — exclude test files from tsc)

### Implemented
- `api.ts`: typed API client with correct response wrappers (`{ projects }`, `{ tasks }`, `{ runs }`), injectable `getAuthHeaders`, configurable `baseUrl` (includes `/api/v1`), no hard-coded token/port/secret.
- `ProjectList`: loading, empty, 403 auth error states; project selection navigation.
- `CreateProjectForm`: name + description form, 422 error display, loading/disabled states.
- `TaskList`: Discuss/Review/Validate mode labels, task selection, empty state.
- `CreateTaskForm`: title, workflow, version, mode form; 404/422/403 error handling.
- `RunPreparation`: ContextPackage ID input (non-empty validation only, real validity from API 422), run creation, Run CREATED/LOCAL/NONE state display, run history list.
- `App.tsx`: `useState`-based view state navigation (`projects` → `tasks` → `run-prep`), no router, props-based.
- Accessibility: `role="status"` for loading, `role="alert"` for errors, `aria-label` on all forms, `aria-required`, `disabled`/`loading` button states.
- Default API base URL: `/api/v1` (same-origin). Vite dev proxy forwards `/api` → `127.0.0.1:8765`. Overridable via `VITE_POLYNEXUS_API_BASE_URL` env var (not a secret). No CORS issue in dev mode.
- `LOOPBACK_TOKEN` is NOT stored, transmitted, or referenced as a value in frontend code. The 403 error hint mentions the environment variable name only — this is an operational hint, not a secret leak.

### Tests and validation
- `apps/web/src/App.test.tsx`: 41 tests — PASS, exit code 0.
- `npm run build` (tsc -b && vite build) — PASS, exit code 0.
- `git diff --check` — PASS, exit code 0.
- Test coverage: api error classes, loading state, empty state, 403 auth error, project list, create form 422 validation, create success (POST 201 + refresh GET), navigation flow (project→task→run-prep, back navigation), task list with Validate/Review/Discuss labels, task list 403/404/422 error branches, CreateTaskForm 403/404/422 error branches, Run CREATED/LOCAL/NONE state display, run list 403/404 error branches, run create 403/404/422 error branches, accessibility (role=status, role=alert, aria-label on forms).

### Test count
- Frontend tests: 41
- Total project tests: 83 (core) + 41 (frontend) = 124

### ADR impact
None. ADR-003 (React/TS/Vite), ADR-004 (UI/Core boundary via REST), ADR-010 (no secret in UI) all respected.

### Scope deviation
- WP-06 scope strictly followed. No backend changes, no new endpoints, no new runtime dependencies.
- Pre-existing untracked files in working tree (`docs/governance/`, `docs/tasks/`, `tools/`) are from prior治理/任務文件 work, unrelated to WP-06. They do not affect WP-06 verification.

### Known limitations
- No `@testing-library/react` installed; tests use direct DOM manipulation with jsdom.
- `jsdom` added as devDependency (not a runtime dependency).
- `vitest.config.ts` added to set `environment: 'jsdom'`.
- Vite proxy (`/api` → `127.0.0.1:8765`) only applies in dev mode (`npm run dev`). Production build (`npm run build`) outputs static files; production deployment needs its own reverse proxy or CORSMiddleware.
- Frontend has no real auth source; when `LOOPBACK_TOKEN` is not set on the backend, all API calls return 403. The UI surfaces "Authentication required" with a hint about `LOOPBACK_TOKEN`.

### Next
- **Codex**: Independently review WP-06 after `READY_FOR_CODEX_REVIEW`.
- **OpenCode**: After Codex review passes, proceed with WP-07 Integration Acceptance or next FVS task.

## WP-07 Update

### Goal
Integration Acceptance — execution persistence and reload. Establish the minimal Core-owned integration that executes a Task through RunSupervisor + ReferenceRuntimeAdapter, persists all results through repositories, and verifies full session-close-reopen reload.

### Changed files
- `services/core/src/polynexus_core/execution_service.py` (new)
- `services/core/tests/test_wp07_integration.py` (new)

### Implemented
- `ExecutionService`: thin orchestration layer connecting Repository layer, Workflow loader, and RunSupervisor.
  - Loads Task and ContextPackage from repositories; validates same-project ownership.
  - Loads WorkflowDefinition from builtin YAML; validates task workflow reference.
  - **Workflow path security**: workflow_id validated against allowlist pattern (`^[a-zA-Z0-9_-]+$`); resolved path containment verified via `Path.is_relative_to()` (not string prefix); rejects sibling-prefix paths and symlink/junction escapes. Containment logic factored into `_check_workflow_path_containment` static helper (called by `_load_workflow`).
  - Executes via `RunSupervisor` + `ReferenceRuntimeAdapter`.
  - Persists Run, RunEvents, RunResult, Finding, Evidence, Artifact through repository ABCs. No direct ORM operations in service layer.
  - Single explicit transaction boundary with commit.
- `test_wp07_integration.py`: 13 integration acceptance tests covering:
  - Full lifecycle: execute → persist → close session → reopen → reload → verify.
  - Cross-project validation (Task/ContextPackage must share project).
  - Workflow reference validation (task workflow must match loaded YAML).
  - Strict run event lifecycle ordering: CREATED→STARTING→RUNNING→COMPLETED with chain integrity and monotonic timestamps.
  - Cancel cleanup persistence verification.
  - Reference runtime network egress guarantee (purely in-memory).
  - **Workflow path traversal prevention**: rejects `../`, `..\\`, URL-encoded, and non-alphanumeric workflow IDs via regex; validates sibling-prefix false positive rejection (regex layer only — not production symlink containment); symlink escape detection test requires symlink-capable environment (currently UNVERIFIED/SKIPPED).

### Architecture / boundary summary
- `ExecutionService` does NOT own Domain logic, persistence schema, or runtime adapter internals.
- All persistence goes through Repository ABC interfaces (no direct ORM operations, no raw SQL).
- Workflow loaded from `workflows/builtin/review-minimal.yaml` via existing `load_workflow_definition`.
- `ReferenceRuntimeAdapter` is purely in-memory; no network/vendor egress.
- Alembic `upgrade head` used for migration lifecycle (not `Base.metadata.create_all()`).

### Tests and validation (WP-07 ATTEMPT 5 — 2026-08-19)
- `services/core/tests/test_wp07_integration.py`: 12 passed, 1 skipped — exit code 0.
  - SKIPPED / UNVERIFIED: `test_symlink_escape_rejected` — Windows symlink permission denied; uses `pytest.skip(reason=...)`. Symlink-based containment verification could not be executed on current environment. Sibling-prefix fallback test verifies regex rejection only; it does NOT exercise production symlink containment.
- `services/core/tests/test_runtime_skeleton.py`: 2 tests — PASS, exit code 0 (regression).
- `services/core/tests/test_persistence.py`: 38 tests — PASS, exit code 0 (regression).
- Full `services/core` pytest: 95 passed, 1 skipped — exit code 0.
- `scripts/validate_baseline.py`: PASS, exit code 0.
- `git diff --check`: PASS, exit code 0.
- Execution environment: temp venv `C:\temp_pn_venv2\Scripts\python.exe` (Python 3.13.14).

### Acceptance result
- Codex independent review: **PASS** on 2026-08-19.
- Human explicitly accepted the Windows symlink containment `UNVERIFIED/SKIPPED` limitation.
- WP-07 implementation checkpoint: `d7060c4` (`feat(core): add WP-07 execution integration`).

### Test count
- New integration tests: 12 passed + 1 skipped (UNVERIFIED) = 13 total
- Total project tests: 95 (core, 1 skipped) + 41 (frontend) = 136

### Acceptance governance files
This acceptance sync includes the following governance/state files; WP-07 source/test are checkpointed at `d7060c4`:
- `AGENTS.md`
- `docs/05_GIT_WORKFLOW.md`
- `docs/06_AI_TOOL_COLLABORATION.md`
- `docs/08_ACCEPTANCE_STRATEGY.md`
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`

### ADR impact
None. ADR-007 (RunSupervisor lifecycle), ADR-008 (SQLite metadata), ADR-010 (no secret in execution) all respected.

### Scope deviation
None. All work within WP-07 scope.

### Known limitations
- `ExecutionService` uses `ReferenceRuntimeAdapter` only; production adapters will need their own integration tests.
- The service does not handle concurrent execution or retry semantics (future work).
- FVS02-AC-001 BLOCKER (Unicode workspace path) remains — environment issue, not product issue.
- `test_symlink_escape_rejected` SKIPPED / UNVERIFIED on current Windows environment (symlink permission denied). Human accepted this limitation for WP-07; full symlink containment verification remains future environment-specific evidence.

### Next
- **Human**: Continue development; Browser E2E is deferred until development is complete.
- **Antigravity**: Re-run Browser DOM / Playwright E2E after development completion and record route, fixture, failure-path, and screenshot/artifact evidence.
- **OpenCode/Codex**: Do not start a new writer concurrently; preserve the waiver and deferred-test label.

## FVS-MILESTONE-UI-E2E-01 Update

- **TASK_ID**: `FVS-MILESTONE-UI-E2E-01`
- **ATTEMPT**: 1
- **BRANCH**: `feature/first-vertical-slice`
- **WRITER**: OpenCode (WP-06 frontend already implemented)
- **REVIEWER**: Codex
- **ANTIGRAVITY_STATUS**: Completed read-only verification; Browser E2E `UNVERIFIED/SKIPPED`
- **RESULT**: Accepted with explicit Human waiver; this is not full Browser E2E certification.

### Goal and evidence

Verify the existing UI/Core integration through Project → Task → Run Preparation, including `/api/v1`, Vite proxy, fail-closed auth, mode labels, ContextPackage validation, run-state display, navigation, errors, and accessibility.

- Codex rerun: `cd apps/web && npm test` — 41 passed, exit code 0.
- Codex rerun: `cd apps/web && npm run build` — success, exit code 0.
- Codex rerun: `git diff --check` — clean, exit code 0.
- Codex check: `git status --short --branch` — clean, no untracked files, exit code 0.
- Antigravity reported live Core health and Vite `/api` proxy checks — PASS, exit code 0.
- Browser DOM / Playwright screenshot or video artifact — `UNVERIFIED/SKIPPED`; browser binary unavailable in the verification environment.

### Changed files and protected areas

- Product source changed for this verification: **NONE**.
- Governance sync files: `docs/11_PROJECT_STATE.md`, `docs/12_HANDOFF_CURRENT.md`.
- Untracked files: **NONE** at review baseline.
- Protected: `services/core/`, existing `apps/web/src/` implementation, API contracts, workflow YAML, and ADR-001–010 were not changed.

### ADR impact

None. ADR-003, ADR-004, and ADR-010 remain respected.

### Scope deviation

None for product source. Browser E2E maturity is explicitly deferred, not certified.

### Human waiver and limitation

Human explicitly accepted 41 Vitest tests, live HTTP/proxy checks, and static inspection as the temporary acceptance basis, with Browser E2E marked `UNVERIFIED/SKIPPED`. Browser E2E must be rerun after development is complete.

### Do Not Change

- Do not relabel Browser E2E as PASS before a browser-capable rerun.
- Do not modify ADR-001–010, Core source, API contracts, or frontend source as part of this governance sync.
- Do not start multiple writers on `feature/first-vertical-slice`.

## Restrictions
- Do not change ADR-001–010 without a new ADR and explicit human approval.
- Do not add Plugin/MCP infrastructure.
- Do not add unrelated V1 features.
- Do not allow multiple active writers.
- Do not claim PASS without current deterministic evidence.
