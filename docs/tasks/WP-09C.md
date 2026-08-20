# WP-09C — Run Result, Output, and History REST Queries

## Task status

- **TASK_ID**: `WP-09C`
- **ATTEMPT**: 4
- **IMPLEMENTATION_ATTEMPT**: 3
- **REVIEW_ATTEMPT**: 4
- **Status**: `ACCEPTED` — Attempt 4; Codex review PASS and Human acceptance recorded on 2026-08-20
- **Historical**: Implementation Attempt 3 product code/tests unchanged; Attempt 4 addresses governance sync only
- **Codex review**: `PASS`
- **Human acceptance**: Confirmed on 2026-08-20
- **Item progress**: `100%` — 1/1 point accepted
- **Item weight**: `1 point`
- **Accepted project progress**: `27/100 = 27%`
- **Accepted FVS progress**: `19/22 = 86.4%`
- **Branch**: `feature/first-vertical-slice`
- **Writer**: OpenCode
- **Reviewer**: Codex independent Core/API review
- **Antigravity**: `NOT_REQUIRED` — Core-only read API task; Browser E2E remains `UNVERIFIED/SKIPPED`
- **Dependency**: WP-09B Attempt 5 `ACCEPTED` on 2026-08-20
- **Roadmap target**: 2026-09-01

## Goal

Expose the persisted WP-09B Run result, findings, evidence, artifacts, and durable Run event history through authenticated, run-scoped, read-only REST queries for the later WP-09D UI.

The queries must return only existing persisted PolyNexus records. They must not execute or resume a Run, read artifact file content, fabricate missing output, or reinterpret AI opinion as verified evidence.

## Architecture gate result

`IMPLEMENTATION_DETAIL_WITH_STABLE_REST_CONTRACT`.

WP-09C extends the existing ADR-004 REST query boundary and uses the existing Domain/Repository records established by WP-09B. It does not require a new ADR, migration, dependency, storage subsystem, or Domain model change.

Required boundaries:

- ADR-004: UI consumes REST queries; it never reads SQLite, filesystem artifacts, runtime processes, or vendor state directly.
- ADR-008: artifact responses expose persisted metadata/reference only; no artifact file content is loaded or copied into SQLite/API responses.
- ADR-010: no secret/token value may enter schemas, logs, errors, evidence, artifacts, or responses.
- Existing WP-09B execution command and `POST /tasks/{task_id}/runs` behavior remain unchanged.

## REST contract

All routes use prefix `/api/v1`, require the existing authenticated loopback dependency, and are read-only.

| Method and path | Success wrapper | Empty state |
|---|---|---|
| `GET /runs/{run_id}/result` | `{ "result": RunResultResponse | null }` | `200` with `{ "result": null }` |
| `GET /runs/{run_id}/findings` | `{ "findings": FindingResponse[] }` | `200` with `{ "findings": [] }` |
| `GET /runs/{run_id}/evidence` | `{ "evidence": EvidenceResponse[] }` | `200` with `{ "evidence": [] }` |
| `GET /runs/{run_id}/artifacts` | `{ "artifacts": ArtifactResponse[] }` | `200` with `{ "artifacts": [] }` |
| `GET /runs/{run_id}/history` | `{ "events": RunEventResponse[] }` | `200` with `{ "events": [] }` |

HTTP behavior:

- `200`: persisted result/list/history returned, including valid empty wrappers.
- `403`: existing loopback authentication fails.
- `404`: `run_id` does not exist.
- `422`: stored ownership/contract integrity is invalid, including a missing parent Task or an output record/reference that belongs to another Run, Task, or Project.
- Do not use `204` for an empty result/list because WP-09D requires stable JSON wrappers.
- Do not expose raw exception text, SQL, filesystem content, vendor payload, token, or credential fragment.

## Response schemas

Reuse `RunResultResponse` and `RunEventResponse`. Add only the minimum response models needed for persisted fields already present in the Domain.

### `FindingResponse`

```text
id
task_id
run_id
title
description
severity
evidence_refs
status
created_at
```

### `EvidenceResponse`

```text
id
task_id
run_id
actor_id
source
type
status
artifact_refs
metadata
observed_at
```

### `ArtifactResponse`

```text
id
project_id
task_id
run_id
artifact_type
mime_type
source_type
storage_ref
sha256
size
```

Do not add `created_at`, `classification`, arbitrary metadata, artifact content, download behavior, or file existence claims to Artifact responses because those fields/capabilities are not present in the current accepted Domain. Record them as future work instead of fabricating values or adding a migration in WP-09C.

## Ownership and integrity rules

Every query first loads the Run and its parent Task through Repository APIs.

- Missing Run: `404`.
- Missing parent Task for an existing Run: `422` stored contract violation.
- Finding/Evidence: every returned record must match both `run.id` and `run.task_id`.
- Artifact: every returned record must match `run.id`, `run.task_id`, and the parent Task's `project_id`.
- Result: every referenced Finding/Evidence/Artifact ID must resolve and satisfy the same Run/Task/Project ownership rules. Missing or cross-owned references return `422`; they are not silently dropped.
- History: every event must match `run.id`.
- A cross-owned or dangling record/reference must never be returned, even if it exists in SQLite.

Repository queries must be deterministic:

- Findings: `created_at`, then `id`.
- Evidence: `observed_at`, then `id`.
- Artifacts: `id` because the current Artifact Domain has no creation timestamp.
- History events: `occurred_at`, then `id`.

## Allowed implementation surface

Product source:

- `services/core/src/polynexus_core/api/run_outputs.py` — new router for the five read-only queries.
- `services/core/src/polynexus_core/api/schemas.py` — response schemas/wrappers only.
- `services/core/src/polynexus_core/app.py` — mount the new router under the existing `/api/v1` prefix.
- `services/core/src/polynexus_core/persistence/repository.py` — add deterministic `list_by_run()` Repository ABC/SQL methods and ordering tie-breakers required by the queries.
- `services/core/tests/test_wp09_query_api.py` — new deterministic WP-09C integration tests.

Governance updates after implementation:

- `docs/tasks/WP-09C.md`
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`

If another file is genuinely required, stop and report `SCOPE_DEVIATION` before changing it.

## Protected and forbidden areas

- Do not modify `services/core/src/polynexus_core/domain/`.
- Do not modify SQLAlchemy models or Alembic migrations.
- Do not change WP-09A/WP-09B execute semantics, lifecycle, durable claim, failure isolation, or idempotency matrix.
- Do not change WP-08A ContextPackage or WP-08B frontend behavior.
- Do not modify `apps/web/`; WP-09D owns Result/History UI.
- Do not add dependencies, WebSocket behavior, pagination, filtering DSL, artifact download/content endpoints, vendor adapters, or network egress.
- Do not use direct ORM/raw SQL in API route logic; API routes use Repository boundaries.
- Do not fabricate Finding, Evidence, Artifact, Result, history, provenance, status, timestamps, hashes, or filesystem availability.
- Do not write tokens/secrets to source, tests, DB, handoff, or responses.

## Deterministic test matrix

Use a temporary SQLite database initialized with `alembic upgrade head`. Close and reopen sessions where stated so API assertions prove durable reload rather than in-memory reuse.

Required tests:

1. Each endpoint returns `403` without the auth override/configured token.
2. Each endpoint returns `404` for a missing Run.
3. A persisted `CREATED` Run with no outputs returns all five stable empty wrappers with `200`.
4. Execute a Run through the accepted production WP-09B API path with an injected `RuntimeResult` containing one Finding, one Evidence, and one Artifact; retain the supervisor-generated runtime Evidence, then query all five endpoints and assert exact persisted field fidelity.
5. Close/reopen the database session before query assertions.
6. Result IDs exactly match the queried Finding/Evidence/Artifact IDs; JSON tuple fields serialize as arrays.
7. History returns the strict persisted lifecycle order and deterministic timestamp/id ordering.
8. Multiple Runs under one Task do not leak Finding/Evidence/Artifact records across Run IDs.
9. Runs under different Tasks in the same Project do not leak outputs.
10. Runs under different Projects do not leak artifacts or references.
11. Stored missing parent Task returns `422` without exposing SQL/internal errors.
12. Dangling Result output ID returns `422`.
13. Cross-Run or cross-Task Finding/Evidence ownership mismatch returns `422`.
14. Cross-Project Artifact ownership mismatch returns `422`.
15. Artifact response returns metadata/reference only and never reads or inlines filesystem content.
16. Evidence `type` and `status` are returned exactly as persisted; no AI opinion is upgraded to verified evidence.
17. Existing WP-09B execute API tests remain unchanged and pass.
18. Full Core regression, baseline validation, and `git diff --check` pass with actual exit code 0.

Do not weaken, skip, or delete existing tests to make WP-09C pass. Any environment-limited test must be reported as `UNVERIFIED/SKIPPED`, not PASS.

## Verification commands

```powershell
$pnPython = "C:\temp_pn_venv2\Scripts\python.exe"
& $pnPython -m pytest -q services\core\tests\test_wp09_query_api.py
& $pnPython -m pytest -q services\core\tests\test_wp09_execution_api.py
& $pnPython -m pytest -q services\core
& $pnPython .\scripts\validate_baseline.py
git diff --check
git status --short --branch
```

## Required Writer handoff

```yaml
RESULT: READY_FOR_CODEX_REVIEW | NEED_ACTION
TASK_ID: WP-09C
ATTEMPT: <current attempt number>
TASK_DOC: docs/tasks/WP-09C.md
HANDOFF_DOC: docs/12_HANDOFF_CURRENT.md
BRANCH: feature/first-vertical-slice
WRITER: OpenCode
REVIEWER: Codex
ANTIGRAVITY_STATUS: NOT_REQUIRED (Core-only task; Browser E2E remains UNVERIFIED/SKIPPED)
NEXT_OWNER: Codex | OpenCode
CHANGED_FILES: complete tracked and untracked list
PROTECTED_AREAS: WP-08A/WP-08B/WP-09A/WP-09B, ADR-001–010, migrations, frontend
TESTS: exact current command, result, and exit code
ADR_IMPACT: NONE or concrete impact
SCOPE_DEVIATION: NONE or concrete deviation
KNOWN_LIMITATIONS: explicit
UNVERIFIED: explicit
NEXT_ACTION: CODEX_REVIEW | NEED_ACTION
FIX_PROMPT: required when NEED_ACTION
APPROVED_FOR_COMMIT: NO (until Codex PASS and Human authorization)
```

## Historical copy-paste prompt for OpenCode (implementation Attempt 3)

```text
你是 WP-09C 的唯一 Writer。請以最小、可審查變更實作 Run Result/Finding/Evidence/Artifact/History REST queries。

開始前只讀：
1. AGENTS.md
2. docs/11_PROJECT_STATE.md
3. docs/12_HANDOFF_CURRENT.md
4. docs/tasks/WP-09C.md
5. docs/tasks/WP-09B.md（已 ACCEPTED）
6. docs/18_ARCHITECTURE_DECISIONS.md（ADR-004、ADR-008、ADR-010）
7. services/core/src/polynexus_core/domain/models.py
8. services/core/src/polynexus_core/persistence/repository.py
9. services/core/src/polynexus_core/api/runs.py
10. services/core/src/polynexus_core/api/schemas.py

先執行 git status --short --branch，確認 branch 為 feature/first-vertical-slice，保留所有既有變更。

依 docs/tasks/WP-09C.md 的固定契約實作五個 authenticated read-only endpoints：
- GET /api/v1/runs/{run_id}/result
- GET /api/v1/runs/{run_id}/findings
- GET /api/v1/runs/{run_id}/evidence
- GET /api/v1/runs/{run_id}/artifacts
- GET /api/v1/runs/{run_id}/history

要求：
- 穩定 wrappers；空資料回 200 + null/[]。
- 403 auth、404 missing Run、422 stored ownership/contract mismatch。
- Repository ABC/SQL list_by_run，確定性排序，不可在 route 直接 ORM/raw SQL。
- Result references 必須驗證存在且屬於同一 Run/Task/Project；不可靜默過濾。
- Artifact 只回既有 metadata/reference，不讀檔、不回 content、不宣稱檔案存在。
- 不修改 Domain、ORM models、Alembic、WP-09B execution、frontend、dependency、ADR。
- 不偽造 Result/Finding/Evidence/Artifact/history，不把 AI_OPINION 升級成 verified evidence。

新增 services/core/tests/test_wp09_query_api.py，完整覆蓋 task doc 的 deterministic test matrix。測試必須使用 Alembic upgrade head、production router/repository，並至少一次 close/reopen session 驗證 durable reload。

執行：
$pnPython = "C:\temp_pn_venv2\Scripts\python.exe"
& $pnPython -m pytest -q services\core\tests\test_wp09_query_api.py
& $pnPython -m pytest -q services\core\tests\test_wp09_execution_api.py
& $pnPython -m pytest -q services\core
& $pnPython .\scripts\validate_baseline.py
git diff --check
git status --short --branch

完成後同步 docs/tasks/WP-09C.md、docs/11_PROJECT_STATE.md、docs/12_HANDOFF_CURRENT.md、docs/28_MASTER_DEVELOPMENT_ROADMAP.md，並輸出規定 handoff。不得 stage、commit、push。
```

## Do not change

- ADR-001–010.
- WP-08A/WP-08B contracts and frontend.
- WP-09A approved Option A contract.
- WP-09B Run-create/execute status codes, lifecycle, CAS claim, failure persistence, sanitization, and no-fabricated-output behavior.
- Before Codex PASS and Human acceptance, progress remained `26/100` project and `18/22` FVS; after the acceptance recorded above, current accepted progress is `27/100` project and `19/22` FVS.
