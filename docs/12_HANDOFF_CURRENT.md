# Current Handoff

## Task
First Vertical Slice

## Status
Previous: WP-09C — ACCEPTED (Attempt 4; IMPLEMENTATION_ATTEMPT: 3 / REVIEW_ATTEMPT: 4); Codex PASS and Human acceptance recorded on 2026-08-20.
Current: WP-09D — ACCEPTED (Attempt 3); Codex PASS and Human acceptance recorded on 2026-08-20.
Next: Prepare WP-10 FVS final deterministic acceptance.

Acceptance repair log: `docs/27_ACCEPTANCE_REPAIR_LOG.md`

Task document: `docs/tasks/WP-09D.md`; roadmap: `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`; accepted dependencies: `docs/tasks/WP-09A.md`, `docs/tasks/WP-09B.md`, and `docs/tasks/WP-09C.md`.
Historical task document: `docs/tasks/FVS-03.md`

## Active Writer
NONE — WP-09D accepted; WP-10 planning pending.

## Reviewer
Codex / Human — WP-09D PASS and acceptance recorded; prepare WP-10 final acceptance.

## Antigravity
`NOT_REQUIRED_FOR_IMPLEMENTATION` for WP-09D; this task does not include real-browser E2E. Browser DOM / Playwright E2E remains `UNVERIFIED/SKIPPED`.

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
- **Human**: Acceptance of WP-08A is recorded; approve future scope decisions as required.
- **OpenCode**: Do not start WP-08B until its task document and contract/architecture gate are complete.
- **Codex**: Prepare/review the WP-08B gate; WP-08A review and acceptance are complete.
- **Antigravity**: Not required for ROADMAP-01/WP-08A review; rerun Browser E2E only after the development sequence is complete.

## ROADMAP-01 Update

- **TASK_ID**: `ROADMAP-01`
- **STATUS**: `CONFIRMED — HUMAN_ACCEPTED 2026-08-19`
- **OWNER**: Codex
- **BRANCH**: `feature/first-vertical-slice`
- **TASK_DOC**: `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`
- **GOAL**: Record the complete V1 development order, scope, forecast dates, checkpoint weights, delivery sequence, and progress-reporting contract; gate WP-08A acceptance.

### Current progress

- Accepted project progress: **22/100 = 22%**.
- Accepted FVS progress: **14/22 = 63.6%**.
- WP-08A: `ACCEPTED`, **2/2 points earned** after current evidence, Codex review PASS, and Human approval.
- Browser E2E: `UNVERIFIED/SKIPPED`, Human waiver retained and no certification claim made.

### Changed files for ROADMAP-01

- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md` (new)
- `docs/04_DEVELOPMENT_PLAN.md` (roadmap reference and current baseline)
- `docs/11_PROJECT_STATE.md` (current checkpoint/progress state)
- `docs/12_HANDOFF_CURRENT.md` (this handoff)
- `docs/15_DOCUMENT_INDEX.md` (roadmap index entry)
- `docs/tasks/WP-08A.md` (Codex review and Human acceptance recorded)
- Product source changes from OpenCode WP-08A are preserved and accepted within WP-08A scope.

### Tests and validation

- Documentation/planning update: no additional product tests run by the status-sync portion of ROADMAP-01.
- `git diff --check`: exit code 0 after the roadmap document update.
- WP-08A current deterministic evidence and Codex review are recorded in the WP-08A section below.

### ADR and scope

- ADR impact: NONE. The roadmap records existing decisions and explicitly gates future execution API contract changes.
- Scope deviation: NONE for roadmap documentation.

### Next exact step

WP-08A acceptance is complete. Next exact step is the WP-08B task document and contract/architecture gate before implementation.

### Do Not Change

- Do not start WP-08B or WP-09A without a task document and contract/architecture gate.
- Do not modify product source as part of ROADMAP-01.
- Do not stage, commit, or push without explicit Git authorization.

## WP-08A Update

- **TASK_ID**: `WP-08A`
- **STATUS**: `ACCEPTED` — Codex review PASS; Human acceptance recorded on 2026-08-19
- **ATTEMPT**: 1
- **AUTHORIZATION**: Human authorized on 2026-08-19.
- **HUMAN_ACCEPTANCE**: Confirmed on 2026-08-19 after Codex independent review PASS.
- **BRANCH**: `feature/first-vertical-slice`
- **WRITER**: OpenCode
- **REVIEWER**: Codex
- **ANTIGRAVITY_STATUS**: `NOT_REQUIRED` for implementation; Browser E2E remains `UNVERIFIED/SKIPPED`.
- **TASK_DOC**: `docs/tasks/WP-08A.md`

### Goal

Add the minimal authenticated `POST /api/v1/projects/{project_id}/context-packages` command using the existing ContextPackage Domain model and Repository boundary, so a later UI slice can create a versioned reference manifest.

### Changed files

- `services/core/src/polynexus_core/api/context_packages.py` (new)
- `services/core/src/polynexus_core/api/schemas.py` (modified — added ContextPackageCreate/ContextPackageResponse)
- `services/core/src/polynexus_core/app.py` (modified — included context_packages router)
- `services/core/tests/test_wp08_context_packages.py` (new)

### Implemented

- `POST /api/v1/projects/{project_id}/context-packages` endpoint with `AuthLoopback` and fail-closed auth.
- Returns `201 Created` with persisted ContextPackage response.
- Validates parent Project exists (404 if not found).
- Validates `version >= 1` via Pydantic `Field(ge=1)` and Domain `__post_init__` (422 for invalid body/version).
- Uses existing `ContextPackage` domain model and `SqlContextPackageRepository` boundary — no direct ORM operations in route.
- Pydantic `ContextPackageCreate` request DTO with all optional manifest fields (instructions, constraints, project_facts, artifact_refs, prior_decision_refs, memory_refs, source_refs).
- Pydantic `ContextPackageResponse` response DTO returning all persisted fields.
- No changes to existing `POST /tasks/{task_id}/runs` behaviour.
- No calls to `ExecutionService`.

### Tests and validation (WP-08A ATTEMPT 1 — 2026-08-19)
- `services/core/tests/test_wp08_context_packages.py`: 14 passed — exit code 0.
  - 201 create with full fields, 201 create with minimal body, 403 auth, 404 project, 422 version zero, 422 version negative, 422 missing version, 422 empty body, persistence reload, no secret in response, no direct ORM operation, repository boundary, run API unchanged, placeholder regression.
- `services/core/tests/test_api.py`: 32 tests — PASS, exit code 0 (regression).
- `services/core/tests/test_persistence.py`: 38 tests — PASS, exit code 0 (regression).
- `services/core/tests/test_wp07_integration.py`: 12 passed, 1 skipped — exit code 0 (regression).
- API + persistence regression: 70 passed — exit code 0.
- Full `services/core` pytest: 108 passed, 1 skipped — exit code 0.
- `scripts/validate_baseline.py`: PASS, exit code 0.
- `git diff --check`: PASS, exit code 0.
- `create_app()` route inspection: ContextPackage endpoint registered — exit code 0.
- Execution environment: temp venv `C:\temp_pn_venv2\Scripts\python.exe` (Python 3.13.14).

### Test count
- New WP-08A tests: 14
- Total project tests: 108 (core, 1 skipped) + 41 (frontend) = 149

### Protected areas
- ADR-001–010: untouched.
- Existing `POST /tasks/{task_id}/runs` behaviour: untouched.
- `ExecutionService`: untouched.
- Frontend source: untouched.
- Workflow YAML: untouched.
- Dependencies: untouched.
- Database schema: untouched (existing ContextPackage table already supports all fields).

### ADR impact

NONE. ADR-002 (FastAPI/asyncio), ADR-004 (UI/Core boundary), ADR-008 (SQLite metadata / ContextPackage as reference manifest), ADR-010 (no secret in response) all respected.

### Scope deviation

NONE. All work within WP-08A scope.

### Known limitations

- Browser DOM / Playwright E2E remains `UNVERIFIED/SKIPPED` by Human waiver and is deferred until development is complete.
- The existing Run API still creates `CREATED` only; WP-08A does not change that behaviour.
- pytest emitted a Windows temp cleanup `PermissionError` at interpreter exit; all test commands returned exit code 0.
- `test_full_core_regression` is a no-op placeholder; the independent full Core command is the actual regression evidence. Remove or rename it in a later test-quality cleanup.

### Do Not Change

- Do not modify `POST /api/v1/tasks/{task_id}/runs` execution semantics.
- Do not call or modify `ExecutionService`.
- Do not add frontend, WebSocket, vendor, plugin, or browser logic.
- Do not change ADR-001–010 or add dependencies.
- Do not stage, commit, or push during implementation.

### Acceptance result and next

- **Codex**: Independent review `PASS`; no BLOCKER or MAJOR findings.
- **Human**: WP-08A acceptance confirmed on 2026-08-19.
- **OpenCode**: Prepare the next FVS task only after the WP-08B task document and gate are ready.

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

## WP-08B Attempt 2 Update

- **TASK_ID**: `WP-08B`
- **ATTEMPT**: `2`
- **BRANCH**: `feature/first-vertical-slice`
- **WRITER**: Antigravity
- **REVIEWER**: Codex
- **ANTIGRAVITY_STATUS**: `IMPLEMENTATION_COMPLETE`
- **RESULT**: `READY_FOR_CODEX_REVIEW`

### Goal
Implement ContextPackage authoring and selection in the React frontend, strictly validating version integer input, encoding path params, parsing all manifest fields (with whitespace trimming and blank omission), and populating the returned real ContextPackage ID into Run creation.

### Changed files (THIS_ATTEMPT: WP-08B Frontend)
- `apps/web/src/api.ts` (ContextPackage types and `createContextPackage`)
- `apps/web/src/components/RunPreparation.tsx` (authoring form, strict integer validation, ID auto-population)
- `apps/web/src/styles.css` (authoring UI and hints)
- `apps/web/src/App.test.tsx` (61 tests, including strict version, URL encoding, full manifest shape, Run regression)
- `docs/tasks/WP-08B.md` (task status sync)
- `docs/11_PROJECT_STATE.md` (project state sync)
- `docs/12_HANDOFF_CURRENT.md` (handoff sync)
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md` (roadmap sync)

### Protected areas check (PRE_EXISTING_ACCEPTED: WP-08A Core)
- `services/core/src/polynexus_core/api/context_packages.py` (Unchanged by WP-08B)
- `services/core/src/polynexus_core/api/schemas.py` (Unchanged by WP-08B)
- `services/core/src/polynexus_core/app.py` (Unchanged by WP-08B)
- `services/core/tests/test_wp08_context_packages.py` (Unchanged by WP-08B)
- `docs/tasks/WP-08A.md` (Unchanged by WP-08B)
- ADR-001–010 respected. No backend modifications.

### Tests and deterministic evidence
- `cd apps/web && npm test` (`vitest run`): 61 passed across 1 file, exit code 0.
- `cd apps/web && npm run build` (`tsc -b && vite build`): PASS, exit code 0.
- `git diff --check`: PASS, exit code 0.

### Known limitations
- Selection uses manual ID input or the newly created ID from the authoring form (no GET/list endpoint in Core per WP-08A contract).

### Unverified
- Real Headless Browser E2E (Playwright) remains `UNVERIFIED/SKIPPED` under existing Human waiver.

### Next
- Codex independent review of WP-08B Attempt 2.

## WP-08B Acceptance Update

- **TASK_ID**: `WP-08B`
- **STATUS**: `ACCEPTED`
- **CODEX_REVIEW**: PASS; no BLOCKER, MAJOR, or MINOR findings.
- **HUMAN_ACCEPTANCE**: Confirmed on 2026-08-19.
- **ITEM_PROGRESS**: 100% — 2/2 points accepted.
- **PROJECT_PROGRESS**: 24/100 = 24%.
- **FVS_PROGRESS**: 16/22 = 72.7%.
- **TESTS**: 61 frontend tests passed, build passed, and `git diff --check` exited 0.
- **UNVERIFIED**: Browser DOM / Playwright E2E remains `UNVERIFIED/SKIPPED` under the accepted Human waiver.
- **NEXT**: Prepare WP-09A contract/architecture gate; do not implement execution API semantics before approval.

Earlier WP-08B preparation and review text in this handoff is historical; this acceptance update and the top Status section are current.

## WP-09B Acceptance Update

- **TASK_ID**: `WP-09B`
- **ATTEMPT**: 5
- **STATUS**: `ACCEPTED`
- **BRANCH**: `feature/first-vertical-slice`
- **WRITER**: OpenCode
- **REVIEWER**: Codex — PASS
- **ANTIGRAVITY_STATUS**: `NOT_REQUIRED` (Core-only task; no browser/E2E involvement)
- **NEXT_OWNER**: transition completed; current owner is OpenCode for WP-09C
- **HANDOFF_DOC**: `docs/12_HANDOFF_CURRENT.md`
- **TASK_DOC**: `docs/tasks/WP-09B.md`

### Changed files

Modified (WP-09B core):
- `services/core/src/polynexus_core/api/runs.py`
- `services/core/src/polynexus_core/execution_service.py`
- `services/core/src/polynexus_core/runtime/supervisor.py` — now guards `version_info()` before COMPLETED, types `RunExecution.result` as `RunResult | None`
- `services/core/src/polynexus_core/persistence/repository.py`
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- `docs/tasks/WP-09B.md`
- `services/core/tests/test_wp09_execution_api.py` — version_info added to failure matrix, Finding/Evidence/Artifact output test

New (WP-09B):
- `services/core/src/polynexus_core/errors.py`
- `services/core/src/polynexus_core/api/errors.py`

### Implementation summary (Attempt 5 — guards version_info, typed result, production output test)

Durable claim (preserved):

**Durable claim** (preserved from Attempt 3):
- `RunRepository` ABC declares `claim_for_execution()` and `append_event()`.
- ExecutionService uses `RunRepository` ABC — no SqlRunRepository cast.
- Flow: validate all references → CAS claim → append claim event → commit → reload → execute.
- CAS claim + event committed BEFORE adapter invocation.

**Runtime failure isolation** (new in Attempt 4):
- `execute_claimed_run()` wraps each adapter boundary call individually: `workflow_executor.execute()` (which calls `create_run`+`submit`), `adapter.status()`, `adapter.result()`, `adapter.artifacts()`.
- Any runtime exception → `RunState.FAILED` transition with sanitized reason `"Runtime boundary error"`.
- Returns `RunExecution(run=run, result=None, findings=(), evidence=(), artifacts=())` — no fabricated Result/Evidence/Finding/Artifact.
- Programmer/domain validation errors (ValueError) are NOT caught — they propagate to caller.

**Sanitized failure** (new in Attempt 4):
- Fixed public-safe reason: `"Runtime boundary error"`.
- Never contains raw str(exc), vendor payload, path, token, or credential fragment.
- Test uses `_SECRET_MARKER` and asserts it does not appear in response, events, result, evidence, or DB reload.

**No fabricated output** (new in Attempt 4):
- ExecutionService only persists Finding/Evidence/Artifact when `execution.result is not None`.
- On failure: only Run state + events persisted. result=None, no Finding/Evidence/Artifact in DB.
- API returns 202 RunResponse with result=null per contract.

**Layer boundary** (preserved from Attempt 3):
- Exceptions in `polynexus_core.errors` (core layer).
- `api/errors.py` re-exports for backward compatibility.
- `ResourceNotFoundError` docstring says "API maps to HTTP 422".

### Tests and validation (Attempt 5 — accepted evidence)

- `C:\temp_pn_venv2\Scripts\python.exe -m pytest -q services\core\tests\test_wp09_execution_api.py`: 36 tests passed — exit code 0.
- `C:\temp_pn_venv2\Scripts\python.exe -m pytest -q services\core`: 134 tests passed, 1 skipped — exit code 0.
- `scripts/validate_baseline.py`: PASS, exit code 0.
- `git diff --check`: PASS, exit code 0.

### Acceptance and progress

- Codex independent review: `PASS`; no BLOCKER, MAJOR, or MINOR findings.
- Human acceptance: confirmed on 2026-08-20.
- Item progress: `100%`, **2/2 points accepted**.
- Accepted project progress: **26/100 = 26%**.
- Accepted FVS progress: **18/22 = 81.8%**.
- Progress allocation decision: WP-09B 2 points; remaining CP-02 work is WP-09C 1 point, WP-09D 1 point, and WP-10 2 points, preserving the 22-point checkpoint total.

### Protected areas

- WP-08A ContextPackage REST contract and Core tests.
- WP-08B frontend authoring/selection and Run `CREATED / LOCAL / NONE` display.
- ADR-001–010 remain frozen.
- ReferenceRuntimeAdapter no-network behavior and workflow path containment.
- Repository/ORM boundary: routes use dependencies and repositories; no direct ORM/raw SQL in API route logic.

### ADR impact

NONE. ADR-004, ADR-007, ADR-008, ADR-010 respected with no ADR file changes.

### Scope deviation

NONE.

### Known limitations

- True concurrent HTTP execution: UNVERIFIED (sequential regression tested; repository-level CAS one-winner test included).
- Browser E2E: UNVERIFIED/SKIPPED.

### UNVERIFIED

- Browser DOM / Playwright E2E: `UNVERIFIED/SKIPPED`.
- True concurrent HTTP duplicate-command execution: `UNVERIFIED`.

### Do Not Change

- WP-08A/WP-08B contract, ADR-001–010, migration, dependency, existing POST task/runs 201 CREATED semantics.

### Next

- WP-09C task preparation is complete; OpenCode implements `docs/tasks/WP-09C.md` without changing the accepted WP-09B execution command contract.

## WP-09A Architecture Gate Acceptance

- **TASK_ID**: `WP-09A`
- **STATUS**: `ACCEPTED_ARCHITECTURE_GATE`
- **BRANCH**: `feature/first-vertical-slice`
- **WRITER**: Codex (proposal only)
- **REVIEWER / DECISION OWNER**: Codex independent architecture review PASS / Human contract approval confirmed 2026-08-19
- **ITEM_PROGRESS**: `100%` gate complete; no product points assigned or earned from this contract-only task
- **PROJECT_PROGRESS**: `24/100 = 24%`
- **FVS_PROGRESS**: `16/22 = 72.7%`

### Changed files in this gate preparation

- `docs/tasks/WP-09A.md` (new execution command contract proposal and decision gate)
- `docs/11_PROJECT_STATE.md` (current gate/status synchronization)
- `docs/12_HANDOFF_CURRENT.md` (current handoff synchronization)
- `docs/15_DOCUMENT_INDEX.md` (task index entry)
- `docs/04_DEVELOPMENT_PLAN.md` (progress/status note)
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md` (WP-09A gate status; accepted progress unchanged)
- `docs/tasks/WP-09B.md` (approved implementation Writer handoff)

### Critical finding

The accepted Run-create endpoint persists a `CREATED` Run and intentionally does not execute. The current `ExecutionService.execute_task()` and `RunSupervisor.start()` path creates another Run and reads the ContextPackage from `Task.context_package_id`. A direct API wiring would therefore risk duplicate Run records, wrong ContextPackage authority, and non-durable failure state. Human approved Option A and Codex confirmed the contract: execute the existing `run_id`, use the Run ContextPackage reference, return command `202`/durable GET semantics, and prevent duplicate runtime submission.

### Protected areas

- No product source changed under `services/core/` or `apps/web/`.
- ADR-001–010 remain frozen; ADR-004/007/008/010 are marked potentially affected pending decision, not modified.
- WP-08A Core contract, WP-08B UI behavior, and `CREATED / LOCAL / NONE` Run display remain protected.
- Browser DOM / Playwright E2E remains `UNVERIFIED/SKIPPED` under the accepted waiver.

### Required next action

WP-09A gate is complete. OpenCode may implement WP-09B under `docs/tasks/WP-09B.md`; Codex must independently review the resulting source and deterministic evidence before Human acceptance.

### Do not change

- Do not implement an execution endpoint yet.
- Do not change Core/frontend source, API schemas, migrations, runtime adapters, workflow YAML, or ADR-001–010.
- Do not stage, commit, push, or rewrite unrelated working-tree changes without explicit authorization.

## Restrictions
- Do not change ADR-001–010 without a new ADR and explicit human approval.
- Do not add Plugin/MCP infrastructure.
- Do not add unrelated V1 features.
- Do not allow multiple active writers.
- Do not claim PASS without current deterministic evidence.

## WP-09C Acceptance Update (Attempt 4)

- **TASK_ID**: `WP-09C`
- **ATTEMPT**: 4
- **IMPLEMENTATION_ATTEMPT**: 3
- **REVIEW_ATTEMPT**: 4
- **STATUS**: `ACCEPTED`
- **TASK_DOC**: `docs/tasks/WP-09C.md`
- **HANDOFF_DOC**: `docs/12_HANDOFF_CURRENT.md`
- **BRANCH**: `feature/first-vertical-slice`
- **WRITER**: OpenCode
- **REVIEWER**: Codex
- **ANTIGRAVITY_STATUS**: `NOT_REQUIRED` — Core-only task; Browser E2E remains `UNVERIFIED/SKIPPED`
- **NEXT_OWNER**: Codex
- **CODEX_REVIEW**: `PASS`
- **HUMAN_ACCEPTANCE**: Confirmed on 2026-08-20
- **ITEM_PROGRESS**: `100%` — 1/1 point accepted
- **PROJECT_PROGRESS**: `27/100 = 27%`
- **FVS_PROGRESS**: `19/22 = 86.4%`

### Changed files (actual git status)

Modified:
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- `docs/15_DOCUMENT_INDEX.md` — PRE_EXISTING task-preparation change (not WP-09C scope; see SCOPE_DEVIATION)
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`
- `services/core/src/polynexus_core/api/schemas.py` — Modified (wrappers added)
- `services/core/src/polynexus_core/app.py` — Modified (router mount)
- `services/core/src/polynexus_core/persistence/repository.py` — Modified (RunEvent tie-breaker order_by(occurred_at, id); list_by_run ordering)

Untracked:
- `docs/tasks/WP-09C.md` — Untracked (task document, part of WP-09C handoff)
- `services/core/src/polynexus_core/api/run_outputs.py` — Untracked (new, 5 endpoints)
- `services/core/tests/test_wp09_query_api.py` — Untracked (new, now 24 tests)

### Tests (Attempt 4 — current acceptance evidence; implementation baseline Attempt 3 historical)

- `test_wp09_query_api.py`: 24 passed, exit code 0
- `test_wp09_execution_api.py`: 36 passed, exit code 0 (unchanged)
- `services/core` full: 169 passed, 1 skipped, exit code 0 (170 collected)
- `services/core` collect: 170 tests, exit code 0
- `validate_baseline.py`: PASS, exit code 0
- `git diff --check`: PASS, exit code 0

### Protected areas

- WP-09B execution/lifecycle/CAS, WP-08A/B, ADR-001–010, Domain/ORM/Alembic, frontend — all unchanged

### ADR impact

NONE — extends ADR-004 query boundary, preserves ADR-008/010

### SCOPE_DEVIATION

- `docs/15_DOCUMENT_INDEX.md` modification is PRE_EXISTING task-preparation change (cross-attempt historical; not introduced in any WP-09C attempt); no product scope change

### UNVERIFIED

Symlink containment `UNVERIFIED/SKIPPED`, Browser E2E `UNVERIFIED/SKIPPED`, concurrent HTTP `UNVERIFIED`

### Next

WP-09D task scope and Writer handoff are recorded in `docs/tasks/WP-09D.md`. OpenCode may now implement the scoped frontend task; do not modify protected Core contracts.

### Do not change

- ADR-001–010, Domain/ORM/Alembic, WP-08A/B, WP-09A/B, frontend, dependencies, artifact file content, or secret handling.

## WP-09D Implementation Handoff (Attempt 3)

- `TASK_ID`: `WP-09D`
- `STATUS`: `READY_FOR_CODEX_REVIEW`
- `ATTEMPT`: `3`
- `BRANCH`: `feature/first-vertical-slice`
- `WRITER`: `OpenCode`
- `REVIEWER`: `Codex`
- `ANTIGRAVITY_STATUS`: `NOT_REQUIRED_FOR_IMPLEMENTATION` — no real-browser E2E; waiver remains `UNVERIFIED/SKIPPED`
- `NEXT_OWNER`: `Codex`
- `HANDOFF_DOC`: `docs/12_HANDOFF_CURRENT.md`
- `TASK_DOC`: `docs/tasks/WP-09D.md`

### Changed files

Modified:
- `apps/web/src/App.test.tsx` — add WP-09D assertions for full metadata/reference fields including Finding task_id/run_id and Evidence task_id/run_id (78 tests = 61 baseline + 17 WP-09D, preserve existing; Attempt 3 adds task_id/run_id asserts inside existing full-metadata test)
- `apps/web/src/App.tsx` — add run-detail view state, props-based no-router navigation
- `apps/web/src/api.ts` — add WP-09C 5 query wrappers/types/functions, preserve /api/v1, auth injection, error classes, URL encoding
- `apps/web/src/components/RunPreparation.tsx` — add Result/History detail action per Run, preserve CREATED/LOCAL/NONE and ContextPackage authoring
- `apps/web/src/styles.css` — minimal detail-section styles (detail-section) + RunDetail metadata display
- `docs/11_PROJECT_STATE.md` — WP-09D Attempt 3 READY_FOR_CODEX_REVIEW — implementation complete / awaiting Codex review; 78 frontend tests; Current Next Gate = Codex review / Human acceptance
- `docs/12_HANDOFF_CURRENT.md` — this handoff (Attempt 3) with correct modified/untracked ledger
- `docs/15_DOCUMENT_INDEX.md` — PRE_EXISTING dirty state (not WP-09D scope; see SCOPE_DEVIATION)
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md` — WP-09D Attempt 3 READY_FOR_CODEX_REVIEW; 78 Vitest tests PASS + build PASS

Untracked:
- `apps/web/src/components/RunDetail.tsx` — read-only detail fetching 6 endpoints with full metadata fields (Finding: id/task_id/run_id/title/description/severity/status/evidence_refs/created_at; Evidence: id/task_id/run_id/actor_id/source/type/status/artifact_refs/metadata/observed_at; Artifact: id/project/task/run IDs/artifact_type/mime_type/source_type/storage_ref/sha256/size; History: id/run_id/from_state/to_state/occurred_at/reason), no artifact content read, no download, no fabricated evidence, no secret exposure
- `docs/tasks/WP-09D.md` — status READY_FOR_CODEX_REVIEW Attempt 3 (still untracked until commit) — Progress checkpoint synced to READY_FOR_CODEX_REVIEW, implementation complete / awaiting Codex review, ITEM_PROGRESS 0%, PROJECT_PROGRESS 27/100, FVS_PROGRESS 19/22

### Protected areas

- ADR-001–010 (frozen, no change)
- WP-08A/WP-08B contracts and frontend baseline (preserved, 61 tests retained + 17 new = 78)
- WP-09B execution/lifecycle/CAS/failure isolation (no Core change)
- WP-09C REST query contract (no endpoint/schema/migration change)
- No Core source, REST endpoint, schema, migration, runtime, dependency changes

### Tests

- `cd apps/web && npm test` — 78 passed, exit code 0 (61 baseline preserved + 17 WP-09D, including Attempt 3 finding/evid task_id/run_id asserts: `f_1 — task:t_1 — run:run_1 — FindTitle` and `ev_1 — task:t_1 — run:run_1 — actor_1`)
- `cd apps/web && npm run build` — PASS, exit code 0 (tsc -b && vite build)
- `git diff --check` — PASS, exit code 0 (no whitespace errors)
- `git status --short --branch` — Modified: 9 (apps/web 5 + docs 4) + Untracked: 2 (RunDetail.tsx + WP-09D.md), branch feature/first-vertical-slice, exit code 0
  - `## feature/first-vertical-slice...backup/feature/first-vertical-slice [ahead 1]`
  - ` M apps/web/src/App.test.tsx`
  - ` M apps/web/src/App.tsx`
  - ` M apps/web/src/api.ts`
  - ` M apps/web/src/components/RunPreparation.tsx`
  - ` M apps/web/src/styles.css`
  - ` M docs/11_PROJECT_STATE.md`
  - ` M docs/12_HANDOFF_CURRENT.md`
  - ` M docs/15_DOCUMENT_INDEX.md`
  - ` M docs/28_MASTER_DEVELOPMENT_ROADMAP.md`
  - `?? apps/web/src/components/RunDetail.tsx`
  - `?? docs/tasks/WP-09D.md`

### ADR impact

NONE — extends UI consumption of accepted WP-09C contract; preserves ADR-004/008/010; no services/core, REST contract, ADR, or dependency change

### Scope deviation

NONE

### Known limitations

- None new beyond inherited symlink UNVERIFIED/SKIPPED
- Frontend has no real auth source; 403 hint is operational LOOPBACK_TOKEN name only, not secret value

### Unverified

- Browser DOM / Playwright E2E: `UNVERIFIED/SKIPPED` (accepted waiver, deferred to browser verification work)
- True concurrent HTTP duplicate-command: `UNVERIFIED` (repository-level CAS test covers claim)
- Symlink containment: `UNVERIFIED/SKIPPED` (Windows permission, Human waiver accepted)

### Next

WP-09D Codex PASS and Human acceptance are recorded below. Prepare WP-10 final deterministic acceptance.

### Do not change

- Do not modify `services/core/` WP-09B/C execution, WP-09C REST routes/schemas, WP-08A/B frontend, ADR-001–010, migrations, dependencies, storage, or secret handling.
- Do not count WP-09D toward accepted progress (27/100, 19/22) before Codex PASS and Human acceptance.

## WP-09D Acceptance Update (Attempt 3)

- `TASK_ID`: `WP-09D`
- `STATUS`: `ACCEPTED`
- `ATTEMPT`: `3`
- `CODEX_REVIEW`: `PASS`
- `HUMAN_ACCEPTANCE`: Confirmed on `2026-08-20`
- `ITEM_PROGRESS`: `100%` — 1/1 point accepted
- `PROJECT_PROGRESS`: `28/100 = 28%`
- `FVS_PROGRESS`: `20/22 = 90.9%`
- `APPROVED_FOR_COMMIT`: `YES` — explicit Human authorization recorded in the current session

### Acceptance evidence

- `cd apps/web && npm test` — 78 passed, exit code 0
- `cd apps/web && npm run build` — PASS, exit code 0
- `git diff --check` — PASS, exit code 0
- Browser DOM / Playwright E2E remains `UNVERIFIED/SKIPPED` under the accepted waiver.

### Accepted stage allowlist

- `apps/web/src/App.test.tsx`
- `apps/web/src/App.tsx`
- `apps/web/src/api.ts`
- `apps/web/src/components/RunPreparation.tsx`
- `apps/web/src/components/RunDetail.tsx`
- `apps/web/src/styles.css`
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`
- `docs/tasks/WP-09D.md`

Excluded and preserved: `docs/15_DOCUMENT_INDEX.md` remains pre-existing dirty state and is not part of the WP-09D commit.

### Next

Prepare WP-10 FVS final deterministic acceptance. Do not relabel Browser E2E, symlink containment, or concurrent HTTP limitations as verified.
