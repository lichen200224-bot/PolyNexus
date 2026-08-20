# WP-09B — Wire Approved Run Execution Command

## Task status

- **TASK_ID**: `WP-09B`
- **Status**: `ACCEPTED` — Attempt 5 Codex review PASS and Human acceptance recorded on 2026-08-20
- **Item progress**: `100%` — `2/2` points accepted
- **Accepted project progress**: `26/100 = 26%`
- **Accepted FVS progress**: `18/22 = 81.8%`
- **Branch**: `feature/first-vertical-slice`
- **Writer**: OpenCode (implementation complete)
- **Reviewer**: Codex independent Core/API review PASS
- **Antigravity**: Not required for this Core task; Browser E2E remains `UNVERIFIED/SKIPPED`
- **Dependency**: WP-09A `ACCEPTED_ARCHITECTURE_GATE` on 2026-08-19
- **Roadmap target**: 2026-08-29

## Acceptance record

- Codex result: `PASS` for Attempt 5; no BLOCKER, MAJOR, or MINOR findings.
- Human acceptance: confirmed on 2026-08-20.
- Targeted command: `C:\temp_pn_venv2\Scripts\python.exe -m pytest -q services\core\tests\test_wp09_execution_api.py` — 36 passed, exit code 0.
- Full Core command: `C:\temp_pn_venv2\Scripts\python.exe -m pytest -q services\core` — 134 passed, 1 skipped, exit code 0.
- Baseline command: `C:\temp_pn_venv2\Scripts\python.exe .\scripts\validate_baseline.py` — PASS, exit code 0.
- Whitespace command: `git diff --check` — clean, exit code 0.
- Unverified: symlink containment test `SKIPPED/UNVERIFIED` under the accepted Windows policy waiver; Browser E2E `UNVERIFIED/SKIPPED`; true concurrent HTTP duplicate-command execution `UNVERIFIED` with repository-level CAS one-winner coverage only.
- Next: prepare WP-09C task scope and Writer handoff.

## Approved contract

Implement exactly the approved WP-09A command:

```text
POST /api/v1/runs/{run_id}/execute
```

The command executes the already-persisted Run identified by `run_id`. It must not create a second Run. The existing endpoint remains unchanged:

```text
POST /api/v1/tasks/{task_id}/runs
```

That endpoint continues to persist a `CREATED` Run and return `201`; it does not execute.

### Response and idempotency contract

- First command on `CREATED`: accept execution and return direct `RunResponse` with HTTP `202`.
- The durable `GET /api/v1/runs/{run_id}` response is the source of truth for state/result. The Reference runtime may finish before the command response is returned; `202` remains the command contract and is not a fabricated success claim.
- `STARTING` or `RUNNING`: return the current Run with `202`; never submit a duplicate runtime.
- `COMPLETED`, `FAILED`, `TIMED_OUT`, `CANCELLED`, or `ORPHANED`: return the current Run with `200`; do not restart a terminal/diagnostic Run.
- `CANCEL_REQUESTED`: return `409`; do not submit runtime work.
- Only `CREATED` may claim a new execution. Resume is out of scope.

### Validation and errors

- `403`: existing authenticated loopback dependency rejects missing/invalid auth.
- `404`: Run does not exist.
- `409`: invalid lifecycle/concurrency state, including `CANCEL_REQUESTED` or an already claimed Run where the contract does not permit idempotent return.
- `422`: stored Task/Run/ContextPackage project mismatch, Task/Run workflow mismatch, workflow definition/version mismatch, or malformed command input.
- Sanitized `5xx/503` is allowed only for unexpected pre-acceptance infrastructure failure. Do not expose secret values, vendor payloads, tracebacks, or raw credentials.
- Runtime failure after acceptance must persist normalized `FAILED` state/events and must not become a fabricated `PASS`. Evidence, Finding, Artifact, and Result records are written only when actually produced by the runtime boundary.

### Reference authority and lifecycle

- Use the persisted Run's `task_id`, `workflow_id`, `workflow_version`, and `context_package_id` as the execution request.
- Validate Task, Run, and ContextPackage belong to the same project.
- Validate the Run workflow reference matches the Task and builtin canonical WorkflowDefinition.
- Do not silently mutate `Task.context_package_id` to make execution pass.
- Preserve durable lifecycle order: `CREATED → STARTING → RUNNING → terminal` with complete `(from_state, to_state)` event tuples and reloadable timestamps.
- Persist the execution claim/state before runtime submission so duplicate commands cannot submit the same Run twice.
- Core/RunSupervisor owns lifecycle, runtime cleanup, normalized result/error, and `LOCAL` execution target. No vendor-specific logic in the API route.

## In scope

- Add the execution command route under `services/core/src/polynexus_core/api/runs.py`.
- Extend `ExecutionService` and/or `RunSupervisor` minimally so an existing Run can execute without generating a new Run.
- Persist Run updates, lifecycle events, failure state, and actual runtime result/evidence/artifact references through Repository boundaries.
- Add focused Core API/integration tests and preserve all existing tests.
- Reuse `RunResponse`; do not invent a second response wrapper unless a contract issue is demonstrated and escalated.

## Explicitly out of scope

- No change to `POST /tasks/{task_id}/runs` semantics.
- No new ContextPackage list/get endpoint, UI change, WebSocket requirement, distributed queue, worker farm, vendor adapter, browser companion, or plugin.
- No cancellation/resume endpoint; preserve the existing lifecycle vocabulary for future tasks.
- No database migration unless an unavoidable schema gap is demonstrated and separately approved.
- No secret/token/storage changes, `localStorage`, `sessionStorage`, hard-coded credentials, or production config changes.
- No fabricated AI Opinion, Tool Evidence, Finding, Artifact, Result, or successful state.
- No stage, commit, push, reset, or unrelated refactor.

## Protected areas

- WP-08A ContextPackage REST contract and Core tests.
- WP-08B frontend authoring/selection and Run `CREATED / LOCAL / NONE` display.
- ADR-001–010. The implementation must follow the accepted WP-09A decision; do not edit ADRs as part of this task.
- ReferenceRuntimeAdapter no-network behavior and workflow path containment.
- Repository/ORM boundary: routes use dependencies and repositories; no direct ORM/raw SQL in API route logic.

## Required tests

At minimum add or update tests for:

1. Create a real Project/Task/ContextPackage/Run, execute the exact `run_id`, assert `202`, exact response ID, and no duplicate Run.
2. Reload from a new session and verify the durable lifecycle events and final state.
3. Run-owned ContextPackage authority when the Task has no ContextPackage reference; do not silently mutate the Task.
4. Missing Run `404`, missing/invalid authentication `403`, invalid stored project/workflow relationship `422`.
5. Repeat command matrix: active idempotent response without duplicate runtime, terminal `200` current response, and `CANCEL_REQUESTED` `409`.
6. Runtime failure persists `FAILED` state/events after reload, with no fabricated evidence/result.
7. Reference runtime network-egress guard remains green.
8. Existing Run create/list/get and WP-07 integration regression remain green.
9. Fresh SQLite/Alembic lifecycle and request-session boundary remain valid.

If true concurrent execution cannot be deterministically exercised on the current Windows environment, report it as `UNVERIFIED` with the exact reason; do not skip the sequential duplicate-command regression.

## Deterministic verification

Use the validated project Python runtime where the Unicode workspace launcher is unavailable:

```powershell
$pnPython = "C:\temp_pn_venv2\Scripts\python.exe"
& $pnPython -m pytest -q services\core\tests\test_wp09_execution_api.py
& $pnPython -m pytest -q services\core
& $pnPython .\scripts\validate_baseline.py
git diff --check
```

Because this task is Core-only, do not modify the frontend. If the Writer runs frontend regression, report its exact command and result separately; it is not a substitute for Core evidence.

## OpenCode handoff output

```yaml
RESULT: READY_FOR_CODEX_REVIEW | NEED_ACTION
TASK_ID: WP-09B
ATTEMPT: 1 (or current attempt number)
BRANCH: feature/first-vertical-slice
WRITER: OpenCode
REVIEWER: Codex
CHANGED_FILES: tracked and untracked files, explicitly listed
PROTECTED_AREAS: WP-08A/WP-08B, ADR-001–010, existing Run-create semantics, ReferenceRuntime no-egress
TESTS: exact command, result, and exit code
ADR_IMPACT: NONE or concrete impact; do not silently alter ADRs
SCOPE_DEVIATION: NONE or concrete deviation
KNOWN_LIMITATIONS: explicit
UNVERIFIED: explicit, including concurrency/browser limitations
NEXT_ACTION: CODEX_REVIEW or NEED_ACTION
FIX_PROMPT: required when NEED_ACTION
```

## Copy-paste prompt for OpenCode

```text
你是 WP-09B 的唯一 Writer，請先讀取：
1. AGENTS.md
2. docs/11_PROJECT_STATE.md
3. docs/12_HANDOFF_CURRENT.md
4. docs/tasks/WP-09A.md（已 ACCEPTED_ARCHITECTURE_GATE）
5. docs/tasks/WP-09B.md
6. docs/18_ARCHITECTURE_DECISIONS.md（ADR-004、007、008、010）
7. services/core/src/polynexus_core/api/runs.py
8. services/core/src/polynexus_core/execution_service.py
9. services/core/src/polynexus_core/runtime/supervisor.py

實作已批准的 Option A：
POST /api/v1/runs/{run_id}/execute

契約不可自行更改：
- 執行既有 persisted Run，不得建立第二個 Run。
- Run 的 context_package_id 是 authority；驗證 Task/Run/ContextPackage 同 project，不能偷偷修改 Task。
- CREATED 首次執行回 202；STARTING/RUNNING 回目前 Run 的 202；COMPLETED/FAILED/TIMED_OUT/CANCELLED/ORPHANED 回目前 Run 的 200；CANCEL_REQUESTED 回 409。
- GET /api/v1/runs/{run_id} 是 durable source of truth。
- 保留 POST /api/v1/tasks/{task_id}/runs 的 201 CREATED-only semantics。
- persist execution claim、完整 lifecycle events、failure state；不可偽造 AI_OPINION、TOOL_EVIDENCE、Finding、Artifact、Result 或 PASS。
- API route 不直接操作 ORM/raw SQL/process/vendor；Reference runtime 不得 network egress。

允許最小修改範圍：runs API route、ExecutionService/RunSupervisor 的 existing-Run wiring、必要 schema/repository update、Core tests。不要修改 frontend、migration、dependency、ADR、secret/token config 或無關重構。

先寫/補測試再實作，至少涵蓋 task document 的 9 類測試與既有 services/core regression。使用 C:\temp_pn_venv2\Scripts\python.exe，回報每個 command 的實際 output 摘要與 exit code。

完成後停止並輸出完整 handoff：RESULT、ATTEMPT、CHANGED_FILES、PROTECTED_AREAS、TESTS+exit codes、ADR_IMPACT、SCOPE_DEVIATION、KNOWN_LIMITATIONS、UNVERIFIED、NEXT_ACTION；不要 stage/commit/push。
```

## Do not change

- Do not start WP-09C/D or Browser E2E work in this task.
- Do not stage, commit, push, reset, or rewrite unrelated working-tree changes.
