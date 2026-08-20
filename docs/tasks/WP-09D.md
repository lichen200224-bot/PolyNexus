# WP-09D — Result/History UI with Durable Reload and Error States

## Task metadata

- `TASK_ID`: `WP-09D`
- `STATUS`: `ACCEPTED`
- `ATTEMPT`: `3`
- `BRANCH`: `feature/first-vertical-slice`
- `WRITER`: `OpenCode`
- `REVIEWER`: `Codex`
- `ANTIGRAVITY_STATUS`: `NOT_REQUIRED_FOR_IMPLEMENTATION` — this task does not include real-browser E2E; the accepted Browser E2E waiver remains `UNVERIFIED/SKIPPED` and is deferred to the planned browser verification work.
- `NEXT_OWNER`: `Codex/Human` (WP-10 final deterministic acceptance)
- `HANDOFF_DOC`: `docs/12_HANDOFF_CURRENT.md`
- `ROADMAP`: `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`
- `BASELINE_COMMIT`: `3a0237d` (`feat(core): add WP-09C run output queries`)
- `ITEM_PROGRESS`: `100%` — 1/1 point accepted
- `PROJECT_PROGRESS`: `28/100` after WP-09D acceptance
- `FVS_PROGRESS`: `20/22` after WP-09D acceptance
- `ESTIMATE`: 2 calendar days (implementation, focused tests, handoff, one review cycle)
- `TARGET`: `2026-09-04`

## 1. Goal

Add a minimal Result/History detail view for a selected Run. The view must reload its data from the existing authenticated WP-09C REST query endpoints so that a fresh view does not depend on in-memory Run list state. It must render truthful empty states, stable loading/error states, and metadata-only Artifact information without reading the database, filesystem content, runtime process, or vendor session.

The accepted user path becomes:

`Project → Task → Run Preparation → selected Run → Result / Findings / Evidence / Artifacts / History`

This is a UI consumption task. It does not change the Core execution lifecycle or the accepted Run-create/execute semantics.

## 2. Preconditions and source of truth

- WP-08A, WP-08B, WP-09B, and WP-09C are accepted.
- WP-09C is the API contract source of truth for the five run-scoped query endpoints below.
- ADR-001–010 remain frozen.
- Existing frontend baseline is React/TypeScript/Vite with props-based view state and Vitest/JSDOM tests.
- Current frontend baseline evidence is 61 Vitest tests and a successful `npm run build`; the Writer must rerun these commands for the implementation handoff.

## 3. Existing REST contract to consume

The frontend must add typed client functions for these existing endpoints. Do not add or modify REST routes.

| Endpoint | Response wrapper | UI use |
|---|---|---|
| `GET /runs/{run_id}` | Run response | Fresh Run metadata: state, workflow, target, resume mode, timestamps |
| `GET /runs/{run_id}/result` | `{ result: RunResult \| null }` | Authoritative result or truthful no-result state |
| `GET /runs/{run_id}/findings` | `{ findings: Finding[] }` | Finding list or empty state |
| `GET /runs/{run_id}/evidence` | `{ evidence: Evidence[] }` | Evidence list or empty state |
| `GET /runs/{run_id}/artifacts` | `{ artifacts: Artifact[] }` | Metadata/reference-only Artifact list or empty state |
| `GET /runs/{run_id}/history` | `{ events: RunEvent[] }` | Authoritative durable lifecycle history in server order |

Requirements for the API client:

- Preserve the existing `baseUrl` convention and auth-header injection.
- Encode `run_id` with `encodeURIComponent` exactly as existing Run functions do.
- Preserve the stable wrapper shapes; do not unwrap or fabricate missing arrays.
- Reuse `ApiError`, `AuthError`, and `NotFoundError` behavior.
- No token value, secret, `localStorage`, `sessionStorage`, or hard-coded production credential.

## 4. In-scope implementation

Recommended changed files (the Writer may use one equivalent component filename, but must keep the same boundary):

- `apps/web/src/api.ts`
  - Add Finding/Evidence/Artifact query types and the five WP-09C query functions/wrappers.
- `apps/web/src/App.tsx`
  - Add one props-based `run-detail` view state carrying `project`, `task`, and `runId`.
  - Keep the existing no-router navigation model.
- `apps/web/src/components/RunPreparation.tsx`
  - Add a clear action for each listed Run to open its Result/History detail.
  - Preserve Run `CREATED / LOCAL / NONE`, ContextPackage authoring, manual ID, and create-run behavior.
- `apps/web/src/components/RunDetail.tsx`
  - New read-only detail view that fetches fresh Run metadata plus all five query wrappers on entry/retry.
  - Render Result, Findings, Evidence, Artifact metadata/reference, and History sections.
  - Provide a back action to Run Preparation.
- `apps/web/src/styles.css`
  - Only the minimal styles required for the new sections, states, and accessible layout.
- `apps/web/src/App.test.tsx`
  - Add focused integration tests for the acceptance matrix below while retaining all existing tests.
- Governance files (`docs/11_PROJECT_STATE.md`, `docs/12_HANDOFF_CURRENT.md`, `docs/tasks/WP-09D.md`, and the roadmap/index when needed) must be updated in the Writer handoff with actual evidence.

## 5. Required UI behavior and acceptance matrix

| ID | Acceptance requirement | Required evidence |
|---|---|---|
| UI-01 | Run list exposes a Result/History action and opens the selected Run by ID. | Vitest interaction test; no route or direct Core import |
| UI-02 | Detail view loads fresh data using `getRun` plus the five WP-09C query functions. | Mock fetch asserts encoded URL/method and all wrappers |
| UI-03 | Result is rendered from `{ result }`; `result: null` shows an explicit no-result state and never invents summary/status/IDs. | Present-result and null-result tests |
| UI-04 | Findings, Evidence, Artifacts, and History render their returned fields; empty arrays show explicit empty states. | Non-empty and empty wrapper tests |
| UI-05 | Artifact display is metadata/reference-only. No content read, download, filesystem access, or fabricated artifact evidence. | Static inspection plus artifact metadata test |
| UI-06 | History preserves the API/server order and displays lifecycle transition, timestamp, and optional reason. | Ordered event fixture test |
| UI-07 | 403 displays authentication-required state and operational `LOOPBACK_TOKEN` hint; 404 displays Run-not-found; 422 displays validation/integrity error; generic/network failure displays a safe error and retry action. | One test per error branch; `role="alert"` |
| UI-08 | Loading state is visible while any detail request is pending and uses `role="status"`. | Deferred-fetch test |
| UI-09 | Retry reloads fresh data and does not append stale/fabricated records. | Retry test with changed second response |
| UI-10 | Back navigation returns to Run Preparation without changing existing project/task state. | Navigation regression test |
| UI-11 | Accessibility is complete for the new view: labelled section, heading hierarchy, form/button names, `role="status"`, `role="alert"`, and no color-only status meaning. | DOM assertions for roles/labels/accessible names |
| UI-12 | Existing WP-06/WP-08B behavior remains green, including Run `CREATED / LOCAL / NONE`, ContextPackage authoring, manual ID, and current 61-test baseline. | Full frontend test command and build |

The Writer must report the actual final Vitest count. Do not replace the existing 61 tests with a fabricated fixed total; add coverage for the matrix and preserve the baseline suite.

## 6. Error and data-truth rules

- The view is read-only. It must not trigger execution, cancel a Run, mutate a Project/Task/ContextPackage, or call a new endpoint.
- `result: null`, an empty list, and a missing optional reason are valid data states, not failures.
- Do not infer Finding, Evidence, Artifact, verdict, or summary records from Run state or IDs. Render only records returned by the corresponding query wrapper.
- Do not treat AI opinion as verified evidence and do not create UI-side evidence or Artifact records.
- Do not expose secret values. Preserve the Core response boundary; do not add token fields or client-side secret storage.
- Use the existing typed error classes and safe user-facing messages. Preserve enough status information for 403/404/422 tests without printing credentials or raw sensitive payloads.

## 7. Explicitly out of scope

- Any change under `services/core/` or `services/core/tests/`.
- New REST endpoints, schema changes, migrations, Domain/ORM changes, repository changes, or runtime behavior.
- Changes to WP-09B Run-create/execute/lifecycle/CAS/failure semantics.
- Changes to WP-08A/WP-08B ContextPackage contract or Run `CREATED / LOCAL / NONE` semantics.
- React Router, state-management dependencies, browser automation dependencies, or any new production dependency.
- `localStorage`, `sessionStorage`, secret/token persistence, direct SQLite/ORM access, filesystem reads, process/runtime calls, or vendor integration.
- Real Browser/Playwright E2E in this task. The accepted Browser E2E limitation remains `UNVERIFIED/SKIPPED`.
- Visual redesign, responsive-system rewrite, or unrelated CSS cleanup.

## 8. Protected areas and ADR impact

Protected:

- ADR-001–010, especially ADR-004 UI/Core REST boundary, ADR-005 test strategy, ADR-007 Run lifecycle, ADR-008 metadata/reference-only Artifact handling, and ADR-010 secret boundary.
- WP-08A ContextPackage REST contract.
- WP-08B authoring/selection flow and frontend no-storage/no-secret behavior.
- WP-09B execution command, durable lifecycle/failure isolation, and existing Run-create `201 CREATED` behavior.
- WP-09C five query endpoints, response wrappers, ownership/ordering guarantees, and no Artifact content read.

ADR impact: `NONE` expected. If implementation requires changing an endpoint, response wrapper, lifecycle, evidence rule, or dependency, stop and return `NEED_ACTION` with an architecture-gate request; do not modify the protected contract in this task.

## 9. Verification commands for Writer handoff

Run from the repository root unless noted:

```powershell
cd apps/web
npm test
npm run build
cd ../..
git diff --check
git status --short --branch
```

Expected acceptance evidence:

- `npm test`: all existing and new WP-09D Vitest tests passed; exit code `0`.
- `npm run build`: TypeScript and Vite build succeed; exit code `0`.
- `git diff --check`: no whitespace errors; exit code `0`.
- `git status --short --branch`: exact changed/untracked file list reported.

Browser E2E is not a required command for this task and must remain explicitly `UNVERIFIED/SKIPPED`.

## 10. Required Writer handoff output

OpenCode must update `docs/12_HANDOFF_CURRENT.md` and return:

```yaml
RESULT: READY_FOR_CODEX_REVIEW
TASK_ID: WP-09D
ATTEMPT: <number>
BRANCH: feature/first-vertical-slice
WRITER: OpenCode
REVIEWER: Codex
ANTIGRAVITY_STATUS: NOT_REQUIRED_FOR_IMPLEMENTATION
NEXT_OWNER: Codex
HANDOFF_DOC: docs/12_HANDOFF_CURRENT.md
TASK_DOC: docs/tasks/WP-09D.md
CHANGED_FILES:        # complete modified + untracked list, including governance files
PROTECTED_AREAS:
ADR_IMPACT: NONE
SCOPE_DEVIATION: NONE
KNOWN_LIMITATIONS:
UNVERIFIED:
TESTS:                # exact command, result, and exit code for every command
NEXT_ACTION: CODEX_REVIEW
APPROVED_FOR_COMMIT: NO
```

Historical output, skipped Browser E2E, environment blockers, and unverified claims must remain explicitly labelled and must not be converted to PASS.

## 11. OpenCode implementation prompt

```text
TASK_ID: WP-09D
TASK_DOC: docs/tasks/WP-09D.md
HANDOFF_DOC: docs/12_HANDOFF_CURRENT.md
BRANCH: feature/first-vertical-slice
WRITER: OpenCode
REVIEWER: Codex

請先讀取本任務文件、docs/11_PROJECT_STATE.md、docs/12_HANDOFF_CURRENT.md、
docs/28_MASTER_DEVELOPMENT_ROADMAP.md，以及 WP-09C 的 run_outputs contract。

請只在 apps/web 範圍實作 Result/History detail UI：
1. api.ts 新增 WP-09C 五個 query wrappers/types/functions，保留 /api/v1、auth injection、error classes、URL encoding。
2. App.tsx 維持 props-based/no-router，新增 run-detail view；RunPreparation 提供 selected Run 的 detail action。
3. 新增單一 read-only RunDetail component，進入/Retry 時以 run_id 重新取得 Run metadata、result、findings、evidence、artifacts、history。
4. 完整處理 loading、empty/null、403、404、422、generic error/retry 與 accessibility；不得 fabricated output。
5. Artifact 只顯示 metadata/reference，不讀檔、不下載、不操作 Core/process/DB。
6. 保留 WP-06/WP-08B 所有行為與測試，不新增 dependency、不使用 storage、不修改 services/core 或 REST contract。

完成後執行並回報實際 exit code：
cd apps/web; npm test; npm run build; cd ../..; git diff --check; git status --short --branch

更新 docs/12_HANDOFF_CURRENT.md，使用完整 READY_FOR_CODEX_REVIEW 欄位（含 modified/untracked、protected areas、ADR impact、scope deviation、known limitations、unverified、每個 command/result/exit code），再停止等待 Codex review。不要 stage、commit、push。
```

## 12. Progress checkpoint

- Acceptance status: `ACCEPTED` — Codex review PASS and Human acceptance recorded on 2026-08-20 (Attempt 3).
- WP-09D item progress: `100%` — 1/1 point accepted.
- Accepted project progress is `28/100`.
- Accepted FVS progress is `20/22`.
- Browser E2E remains `UNVERIFIED/SKIPPED`; symlink containment and concurrent HTTP limitations remain explicitly recorded.

## 13. Human acceptance update

- `CODEX_REVIEW`: `PASS` — no BLOCKER, MAJOR, or MINOR findings.
- `HUMAN_ACCEPTANCE`: Confirmed on `2026-08-20`.
- `NEXT_OWNER`: Codex/Human prepare WP-10 final deterministic acceptance.
- `APPROVED_FOR_COMMIT`: `YES` by explicit Human authorization.
