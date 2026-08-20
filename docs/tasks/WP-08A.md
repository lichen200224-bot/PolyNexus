# WP-08A — ContextPackage REST Contract

## Task status

- **TASK_ID**: `WP-08A`
- **Status**: `ACCEPTED` — Codex independent review PASS; Human acceptance recorded on 2026-08-19
- **Human authorization**: Granted on 2026-08-19
- **Branch**: `feature/first-vertical-slice`
- **Writer**: OpenCode
- **Reviewer**: Codex
- **Antigravity**: `NOT_REQUIRED` for implementation; Browser E2E remains deferred

OpenCode Attempt 1 implementation was independently reviewed against the current working tree and deterministic evidence. Human acceptance is recorded; WP-08A earns 2/2 roadmap points.

## Goal

Expose the existing `ContextPackage` domain through a minimal authenticated REST command so the next UI slice can create a versioned reference manifest without directly accessing SQLite or runtime state.

## Context

The current domain model and SQL repository already persist `ContextPackage`. The existing Run API accepts a ContextPackage ID, while the UI has no Core command for creating one. This task fills that narrow product-path gap without starting execution or changing the existing Run creation semantics.

## Read first

- `AGENTS.md`
- `docs/00_SCOPE_BASELINE.md`
- `docs/10_DECISION_LOG.md`
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- `docs/18_ARCHITECTURE_DECISIONS.md`
- `docs/20_FIRST_VERTICAL_SLICE_PLAN.md`
- `services/core/src/polynexus_core/domain/models.py`
- `services/core/src/polynexus_core/persistence/repository.py`
- `services/core/src/polynexus_core/api/schemas.py`
- `services/core/src/polynexus_core/api/projects.py`
- `services/core/src/polynexus_core/api/runs.py`

## In scope

Add one authenticated endpoint:

```text
POST /api/v1/projects/{project_id}/context-packages
```

The endpoint must:

- use `AuthLoopback` and fail closed when authentication is unavailable;
- return `201 Created` with the persisted ContextPackage response;
- reuse the existing `ContextPackage` domain model and repository boundary;
- validate that the parent Project exists;
- validate `version >= 1` and preserve the existing manifest fields;
- keep ContextPackage as a versioned reference manifest, not a copied prompt blob;
- use repo-relative, portable data only;
- preserve existing `/api/v1` conventions and response schema style.

Recommended implementation files:

- `services/core/src/polynexus_core/api/context_packages.py` (new)
- `services/core/src/polynexus_core/api/schemas.py`
- `services/core/src/polynexus_core/app.py`
- `services/core/tests/test_wp08_context_packages.py` (new)

Observed OpenCode Attempt 1 files:

- `services/core/src/polynexus_core/api/context_packages.py` (new)
- `services/core/src/polynexus_core/api/schemas.py` (modified)
- `services/core/src/polynexus_core/app.py` (modified)
- `services/core/tests/test_wp08_context_packages.py` (new)

## Required tests

- `201` successful create and stable response fields;
- `403` without configured loopback authentication;
- `404` for an unknown Project;
- `422` for invalid version/body data;
- persistence reload through a new session;
- no secret/token field in request schema, response, database, or logs;
- no direct ORM operation from the route;
- existing Core and API regression tests remain green.

## Explicitly out of scope

- Do not change `POST /api/v1/tasks/{task_id}/runs` behavior.
- Do not call or modify `ExecutionService`.
- Do not add execution, WebSocket, vendor, plugin, or browser logic.
- Do not modify frontend source in WP-08A.
- Do not add a dependency or migration unless an existing schema gap is demonstrated.
- Do not change ADR-001–010 or decide the future execution command endpoint.
- Do not stage, commit, push, or modify unrelated files.

## Acceptance handoff

OpenCode must return:

```yaml
RESULT: READY_FOR_CODEX_REVIEW | NEED_ACTION
TASK_ID: WP-08A
ATTEMPT: 1
BRANCH: feature/first-vertical-slice
WRITER: OpenCode
REVIEWER: Codex
ANTIGRAVITY_STATUS: NOT_REQUIRED
CHANGED_FILES: tracked and untracked files, explicitly listed
PROTECTED_AREAS: Core boundaries, ADRs, existing API semantics
TESTS: exact command, result, and exit code
ADR_IMPACT: NONE or concrete impact
SCOPE_DEVIATION: NONE or concrete deviation
KNOWN_LIMITATIONS: explicit
UNVERIFIED: explicit
NEXT_ACTION: CODEX_REVIEW or NEED_ACTION
FIX_PROMPT: required when NEED_ACTION
```

Codex independently inspected the diff and reran the targeted test, API/persistence regression, full Core regression, baseline validation, and `git diff --check`.

## Codex review and Human acceptance

- **Codex result**: `PASS` — no BLOCKER or MAJOR findings.
- **Human decision**: Accepted on 2026-08-19.
- **Targeted test**: 14 passed, exit code 0.
- **API + persistence regression**: 70 passed, exit code 0.
- **Full Core regression**: 108 passed, 1 skipped, exit code 0.
- **Baseline validation**: PASS, exit code 0.
- **Diff check**: PASS, exit code 0.
- **Production route inspection**: `create_app()` registered `/api/v1/projects/{project_id}/context-packages`, exit code 0.
- **Skipped limitation**: existing WP-07 symlink containment test remains `UNVERIFIED/SKIPPED` because Windows policy denied symlink creation; Human waiver remains explicit and scoped to that test.
- **Environment note**: pytest emitted a Windows temp cleanup `PermissionError` at interpreter exit, but all test commands returned exit code 0.
- **Residual test recommendation**: `test_full_core_regression` is a no-op placeholder; the independent full Core command is the actual regression evidence. Remove or rename it in a later test-quality cleanup.

## Follow-up, not part of WP-08A

WP-08B may define an explicit execution command API that calls `ExecutionService`. That API contract must be separately reviewed before implementation; do not silently change the current Run creation endpoint.
