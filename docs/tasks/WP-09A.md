# WP-09A — Execution Command API Contract / Architecture Gate

## Task status

- **TASK_ID**: `WP-09A`
- **Status**: `ACCEPTED_ARCHITECTURE_GATE` — Human approval and Codex confirmation recorded on 2026-08-19
- **Item progress**: `100%` gate complete; `0` product points assigned or earned from this contract-only task
- **Accepted project progress**: `24/100 = 24%`
- **Accepted FVS progress**: `16/22 = 72.7%`
- **Branch**: `feature/first-vertical-slice`
- **Writer**: Codex (proposal only); WP-09B implementation Writer is OpenCode
- **Reviewer / decision owner**: Codex independent architecture review; Human contract approval completed
- **Antigravity**: Not required for this contract gate; Browser E2E remains `UNVERIFIED/SKIPPED`
- **Estimated duration**: 1 calendar day for proposal, review, and Human decision
- **Roadmap target**: 2026-08-25

## Goal

Define and approve the execution command contract that will connect the accepted Run-creation API to `ExecutionService` and `RunSupervisor` in WP-09B.

The gate must resolve the existing Run-ownership mismatch before any endpoint or Core implementation is changed. It must preserve the accepted `CREATED` Run semantics, normalized lifecycle, durable events, ContextPackage reference semantics, and the UI/Core boundary.

## Current implementation facts

These are read-only findings from the current source, not proposed behavior:

1. `POST /api/v1/tasks/{task_id}/runs` in `services/core/src/polynexus_core/api/runs.py` validates the Task and ContextPackage, persists one `Run` in `CREATED`, returns `201`, and intentionally does not start a runtime.
2. `ExecutionService.execute_task(task_id)` in `services/core/src/polynexus_core/execution_service.py` loads `Task.context_package_id`, loads the workflow, and calls `RunSupervisor.start()`.
3. `RunSupervisor.start()` currently creates a new `Run` internally, transitions it through `STARTING` and `RUNNING`, and returns a `RunSession`; it does not accept the already-persisted Run created by the API.
4. Therefore a naive command endpoint can create a duplicate Run, execute a different ContextPackage than the one selected for the API-created Run, or leave the UI-created Run permanently `CREATED`.
5. `RunRepository` already exposes `get`, `add`, and `update`, and `SqlRunRepository.update()` persists changed Run fields and newly appended events. No API route currently invokes the execution service.
6. When `RunSupervisor.start()` raises, it transitions its in-memory Run to `FAILED`, but the current `ExecutionService.execute_task()` re-raises before `_persist_execution()`; WP-09B must define and test failure persistence rather than assuming the current path is API-ready.

## Source-of-truth constraints

- ADR-004: REST commands/queries cross the UI/Core boundary; durable Run history must not depend on a live WebSocket connection.
- ADR-007: Core-owned Run Supervisor owns normalized lifecycle, cancellation, timeout, and cleanup; V1 execution target is `LOCAL`.
- ADR-008: Run references a versioned ContextPackage manifest; artifacts remain metadata plus filesystem content with hash identity.
- ADR-010: authenticated loopback access and secret redaction remain mandatory; no secret value may enter Domain, Event, Evidence, Artifact, log, export, Git, or handoff.
- Existing WP-08A/WP-08B behavior is accepted and must remain compatible.
- Browser E2E remains `UNVERIFIED/SKIPPED` under the accepted Human waiver and is not part of this gate.

## Proposed contract options — decision required

### Option A — Execute an existing Run by `run_id` (recommended for review)

Approved command shape:

```text
POST /api/v1/runs/{run_id}/execute
```

The command would load the persisted Run, use its `task_id`, `workflow_id`, `workflow_version`, and `context_package_id`, validate all references, and execute that exact Run. WP-09B would adapt the service/supervisor boundary so the existing Run ID is retained rather than creating a second Run.

Benefits: stable UI-selected Run identity, no duplicate record, exact ContextPackage traceability, and a clear durable command target.

Risks to resolve in WP-09B: existing-Run lifecycle entry, concurrent/repeated commands, failure persistence, and safe session/transaction boundaries.

### Option B — Execute a Task and create a new Run

Candidate command shape, pending approval:

```text
POST /api/v1/tasks/{task_id}/execute
```

The command would preserve the current Run-creation endpoint as a preparation record but create a separate execution Run from the Task.

Benefits: closer to the current `ExecutionService.execute_task(task_id)` signature and smaller first implementation change.

Risks: a user-created Run can remain unused, duplicate Run records are likely, the selected Run ID is not the execution identity, and the relationship between `Task.context_package_id` and `Run.context_package_id` stays ambiguous.

### Option C — Change the existing Run-creation endpoint to execute

This would make `POST /api/v1/tasks/{task_id}/runs` both create and execute a Run.

This option is **not recommended** and requires explicit compatibility approval because WP-08A/WP-08B accepted the endpoint as a `201 CREATED` persistence command with no runtime start. It would change public behavior, response timing, lifecycle guarantees, and failure semantics.

## Required Human/Codex decisions

The following decisions must be recorded before WP-09B implementation:

| Decision | Options to approve | Recommended review position |
|---|---|---|
| Command target | Existing `run_id` (A); Task creates a new Run (B); change existing create endpoint (C) | A |
| Context authority | Persisted Run reference; Task reference; explicit request body reference | Persisted Run for A; validate Task/Run equality without silently mutating Task |
| First-call response | `202 Accepted` with current `RunResponse`; `200` after completion; other explicit command response | `202` command semantics with GET as durable source of completion |
| Repeat command | Return current active/terminal Run idempotently; or reject invalid state with `409` | Define an explicit matrix; do not allow duplicate runtime submission |
| Initial state allowed | `CREATED` only; selected resumable states; other | `CREATED` only for WP-09B unless a separate resume decision is approved |
| Error mapping | `403` auth, `404` missing resource, `409` lifecycle/concurrency, `422` contract mismatch, sanitized `5xx/503` runtime failure | Preserve existing API conventions and never expose secret/vendor payloads |
| Failure persistence | Persist `FAILED` Run/events/result before returning error; or return error without a durable Run | Persist the normalized failure after execution has created lifecycle state |
| Async boundary | In-process completion; durable command acceptance plus polling; WebSocket notification | REST command plus durable GET polling; WebSocket is not required for this task |
| Cancel/resume | Include in this contract; defer to a separate gate | Defer endpoint additions; preserve ADR-007 state vocabulary |

## Approved decision record

- **HUMAN_APPROVAL**: Human approved Option A and the recommended contract positions on 2026-08-19.
- **CODEX_CONFIRMATION**: `PASS` — the approved shape preserves the accepted Run-create behavior and resolves the Run ownership mismatch before implementation.
- **Command target**: Option A, `POST /api/v1/runs/{run_id}/execute`.
- **Run identity**: execute and return the exact persisted `run_id`; no second Run may be created by the command.
- **Context authority**: the persisted Run's `context_package_id`; validate that Run, Task, and ContextPackage belong to the same project and that Run workflow reference matches Task/workflow definition. Do not silently mutate `Task.context_package_id`.
- **First-call response**: `202 Accepted` with the current direct `RunResponse`. The durable `GET /api/v1/runs/{run_id}` response is the source of truth for eventual state/result. The Reference runtime may complete before the command response is returned; clients must still treat the command as accepted, not as a fabricated success claim.
- **Initial state**: only `CREATED` may claim a new execution. WP-09B does not add resume semantics.
- **Repeat/idempotency matrix**:
  - `CREATED`: accept once, persist the execution claim/lifecycle, and do not submit more than one runtime for the Run.
  - `STARTING` or `RUNNING`: return `202` with the current Run; do not submit a duplicate runtime.
  - `COMPLETED`, `FAILED`, `TIMED_OUT`, `CANCELLED`, or `ORPHANED`: return `200` with the current immutable/diagnostic Run; do not restart it.
  - `CANCEL_REQUESTED`: return `409` and do not submit runtime work.
- **Error mapping**: authenticated loopback failure `403`; missing Run `404`; lifecycle/concurrency conflict `409`; stored Task/Run/ContextPackage/workflow contract mismatch or malformed command `422`; unexpected pre-acceptance infrastructure failure may use sanitized `5xx/503`. Runtime failure after acceptance must be durably represented as `FAILED` and must not be converted into a fabricated PASS.
- **Failure persistence**: once execution enters lifecycle, persist the state transition/events and normalized failure/result references before the request or later GET exposes the current Run.
- **Async boundary**: REST command plus durable GET polling; no WebSocket requirement and no distributed queue/worker farm in WP-09B. Core remains the Run Supervisor owner.
- **Cancel/resume**: separate future contract; preserve existing ADR-007 states and cleanup rules.
- **Compatibility**: existing `POST /api/v1/tasks/{task_id}/runs` remains a `201 CREATED` persistence command and does not execute.

## Contract invariants

Regardless of the selected option, WP-09B must preserve these invariants:

- Existing `POST /api/v1/tasks/{task_id}/runs` remains compatible unless Option C is separately approved.
- A command cannot execute a Run and then report a different persisted Run ID.
- A Task, Run, and ContextPackage must belong to the same project; mismatches fail closed.
- Workflow ID and version are validated against the builtin canonical WorkflowDefinition before runtime submission.
- Lifecycle events are durable and ordered. For a new execution, the expected path is `CREATED → STARTING → RUNNING → terminal`; no fabricated transition may be returned.
- `AI_OPINION`, `TOOL_EVIDENCE`, Finding, Artifact, or Result records are not fabricated. Reference runtime evidence must be limited to what the runtime actually observes and produces.
- Reference runtime execution has no network/vendor egress.
- Runtime/adaptor exceptions are normalized without leaking secret values; if a Run has entered execution, its failure state and events remain reloadable.
- UI continues to use REST and response wrappers; it never opens a DB session or controls a process directly.
- No new dependency, storage mechanism, token, secret, migration, WebSocket, vendor adapter, or unrelated endpoint is introduced by the gate document.

## WP-09B implementation boundary after approval

Only after the decision record is approved should the implementation Writer update the smallest required Core surface. The implementation handoff must identify whether it changes:

- `ExecutionService` signature and ContextPackage source;
- `RunSupervisor` ability to start an existing Run or an equivalent domain service;
- API route and schemas/status codes;
- repository update/event persistence and request-session transaction handling;
- failure and duplicate-command handling;
- Core API/integration tests.

No implementation Writer should infer a contract from the current `execute_task()` signature alone.

## Acceptance test matrix for WP-09B

The approved contract must have tests for at least:

1. authenticated first execution command and exact Run ID preservation;
2. missing Run/Task/ContextPackage/workflow mapping;
3. cross-project or inconsistent Task/Run/ContextPackage rejection;
4. invalid lifecycle state and duplicate/concurrent command behavior;
5. complete normalized lifecycle and strict event ordering after reload;
6. successful result/evidence/artifact references without fabricated Finding or AI/Tool evidence;
7. runtime failure with durable `FAILED` state and sanitized error mapping;
8. Reference runtime network-egress guard;
9. existing Run-create/list/get regression and 403/404/422 branches;
10. fresh database migration/session boundary and `git diff --check`.

## Gate evidence and review output

WP-09A is accepted as an architecture gate after the explicit contract decision. It earns no product points because it changes no product source and has no separate weight in the current progress register.

```yaml
RESULT: APPROVED
TASK_ID: WP-09A
STATUS: ACCEPTED_ARCHITECTURE_GATE
BRANCH: feature/first-vertical-slice
WRITER: Codex (proposal only)
REVIEWER: Codex independent architecture review
DECISION_OWNER: Human
CHANGED_FILES: docs/tasks/WP-09A.md and governance handoff files only
PRODUCT_SOURCE_CHANGED: false
ADR_IMPACT: pending decision; ADR-004/007/008/010 are potentially affected
SCOPE_DEVIATION: NONE for proposal
ITEM_PROGRESS: 0%
PROJECT_PROGRESS: 24/100
FVS_PROGRESS: 16/22
UNVERIFIED: Browser E2E remains UNVERIFIED/SKIPPED; not part of this gate
NEXT_ACTION: WP-09B_WRITER_HANDOFF
```

## Historical copy-paste prompt for Human/Codex gate decision

The following prompt records the gate that was completed on 2026-08-19. The approved implementation handoff is now `docs/tasks/WP-09B.md`.

```text
請審查 docs/tasks/WP-09A.md 的 Execution Command API Contract 提案。

請先確認現況落差：目前 Run create 只持久化 CREATED；ExecutionService/RunSupervisor 會另建 Run；Task.context_package_id 與 Run.context_package_id 的 authority 尚未定義；start failure 的 durable persistence 也尚未由 API contract 保證。

請對下列項目逐項作出決策並記錄：
1. 採 Option A（existing run_id）/B（task creates run）/C（改變既有 create endpoint）。
2. ContextPackage authority、首次回應 status、repeat/idempotency、allowed initial state。
3. 403/404/409/422/5xx error mapping 與 failure persistence。
4. REST polling 與 WebSocket 的邊界，以及 cancel/resume 是否另立 task。
5. 是否允許 WP-09B 依批准決策修改 ExecutionService、RunSupervisor、API schema/route、repository persistence/tests。

（歷史閘門限制；上述決策已完成。WP-09B 仍只能依批准契約修改最小 Core surface。）
```

## Do not change

- Do not implement the execution command in WP-09A.
- Do not change `services/core/`, `apps/web/`, API schemas, migrations, runtime adapters, or workflow YAML.
- Do not modify ADR-001–010 without a separately approved ADR impact decision.
- Do not relabel Browser E2E `UNVERIFIED/SKIPPED` as PASS.
- Do not stage, commit, push, reset, or rewrite unrelated working-tree changes.
