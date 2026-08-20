# Project State

Date: 2026-08-20
Version: Development Baseline v1.0 + Dev Preparation Profile v1.0.2
Milestone: First Vertical Slice — WP-08A/WP-08B/WP-09B/WP-09C/WP-09D/WP-10 ACCEPTED; CP-02 complete; UI/Core waiver accepted; ROADMAP-01 CONFIRMED

## Confirmed
- Product Scope Decisions D01–D10 confirmed.
- ADR-001～ADR-010 confirmed.
- Stack: React/TypeScript/Vite + Python/FastAPI/asyncio + SQLAlchemy/Alembic/SQLite + REST/WebSocket + pytest/Vitest/Playwright + Chrome MV3 companion.
- Runtime process model: Core-owned Run Supervisor; Adapter-owned vendor logic.
- Artifact: SQLite metadata + filesystem content + SHA-256 identity.
- Context: versioned reference manifest, not prompt-only storage.
- Workflow: YAML authoring + JSON Schema + canonical model; fixed node set.
- Secret boundary: SecretRef + OS-backed SecretStore; secret values excluded from Git/Evidence/Export.
- Development target: Feature Freeze 2026-10-18; V1 acceptance 2026-10-31.
- Competition latest notice: initial-review deadline 2026-09-07.
- Development tools: Codex + OpenCode Go + Antigravity, same Git project directory, Single Active Writer.

## Local Workspace
- Primary Windows path: `D:\AI學習教材\PolyNexus`
- Absolute path is a local profile only; product code remains repo-relative.

## Current Priority
1. Prepare WP-11 Discuss / Review / Validate work-mode semantics and contract tests; defer Browser E2E re-test until development is complete.
2. Prepare competition proposal/deck content confidence gate by 2026-08-25.

## Current Product Slice
First Vertical Slice target by 2026-09-06:
`Project → Review → Runtime → Finding/Evidence → Result → History`.

## Remaining Non-blocking Decisions
- Final UI visual design system/components.
- Exact Windows SecretStore provider implementation detail.
- Final Python/Node dependency lock strategy after first local install.
- CI provider/remote Git service only after approved environment is known.
- Actual competition upload-form fields/demo requirement still require recheck before submission.

## Next Gate
Prepare WP-12 task scope and acceptance tests for the CP-03 Core product baseline; WP-11 is accepted.

## Current Development State

Phase: First Vertical Slice — WP-10 final deterministic acceptance PASS; Human acceptance recorded on 2026-08-20; CP-02 complete
Next Phase: CP-03 Core product baseline — WP-11 accepted; WP-12 next; Browser E2E Re-test deferred

Current Branch: feature/first-vertical-slice
Current Baseline Commit: 3a0237d (`feat(core): add WP-09C run output queries`)
Latest FVS Checkpoint: 3a0237d (`feat(core): add WP-09C run output queries`)
Current Planned Task: WP-12 — Council, parallel analysis, cross review, synthesis, and partial failures (WP-11 accepted)
Active Writer: None — WP-11 accepted; WP-12 task scope/planning pending
Reviewer: Codex — WP-11 independent review PASS; Human acceptance recorded on 2026-08-20
Antigravity: NOT_REQUIRED for WP-11; Browser E2E UNVERIFIED/SKIPPED

Architecture:
- ADR-001 through ADR-010 are CONFIRMED / FROZEN FOR V1 IMPLEMENTATION.

Development Environment:
- Windows development readiness: PASS
- Core pytest: 192 passed, 1 skipped (193 collected; Windows symlink creation policy denied → 1 skipped; pytest temp cleanup PermissionError is a non-fatal environment warning; Human waiver accepted). WP-10 accepted baseline was 169 passed / 170 collected.
- Frontend Vitest: 78 passed (61 baseline + 17 WP-09D)
- Frontend build: PASS
- Local Git backup: PASS

Tool Onboarding:
- OpenCode Desktop: PASS
- ChatGPT / Codex Desktop: PASS
- Antigravity Desktop: PASS

Primary Workspace:
D:\AI學習教材\PolyNexus

Tool Roles:
- Codex: Architecture / Core / Contract / Hard Bug / Critical Review
- OpenCode: Primary Builder / Tests / Templates / Routine Implementation
- Antigravity: Browser / UI / E2E / Integration / Milestone Red Team

Development Rule:
- Single Active Writer.
- AI opinion does not override deterministic evidence.
- Existing deterministic evidence is not rerun solely because the active AI tool changes.

OpenCode Model Routing:
1. Default: DeepSeek V4 Flash
2. If unavailable / policy-blocked: MiMo V2.5
3. If MiMo V2.5 repeatedly fails deterministic validation: MiMo V2.5 Pro
4. Architecture / security / lifecycle / hard root cause: escalate to Codex

## Latest Verification

WP-10 final deterministic acceptance passed current Core, fresh-DB, frontend, baseline, and diff checks. Human acceptance was confirmed on 2026-08-20. Browser DOM / Playwright E2E remains `UNVERIFIED/SKIPPED` and is deferred until development is complete; true concurrent HTTP duplicate-command execution remains `UNVERIFIED`.

- Full Core tests: 192 passed, 1 skipped, exit code 0 (193 collected; Windows symlink creation policy denied → 1 skipped; pytest temp cleanup PermissionError is a non-fatal environment warning). WP-10 accepted baseline was 169 passed / 170 collected.
- Fresh DB / Alembic / reopen-reload checks: 4 passed, exit code 0.
- Frontend Vitest: 78 passed, exit code 0.
- Frontend build: PASS, exit code 0.
- Baseline validation: PASS, exit code 0.
- `git diff --check`: PASS, exit code 0.
- WP-10: ACCEPTED, 2/2 CP-02 points earned.
- Accepted project progress: **30/100 = 30%**.
- Accepted FVS progress: **22/22 = 100%**.
- ADR impact: NONE.
- Scope deviation: NONE; `docs/15_DOCUMENT_INDEX.md` remains pre-existing, unstaged, and excluded.

## ROADMAP-01 / WP-08A + WP-08B Acceptance (Historical checkpoint before WP-09B)

- Master roadmap: `docs/28_MASTER_DEVELOPMENT_ROADMAP.md` — CONFIRMED by Human on 2026-08-19.
- Accepted project progress: **24/100 = 24%**.
- Accepted FVS progress: **16/22 = 72.7%**.
- WP-08A: `ACCEPTED`, **2/2 points earned** after Codex review PASS and Human approval.
- WP-08B: `ACCEPTED`, **2/2 points earned** after Codex review PASS and Human approval on 2026-08-19.
- Current source changes are accepted within WP-08A/WP-08B scope; no Git checkpoint was created in this sync.
- Superseded next step: WP-09B review and Human acceptance completed on 2026-08-20.

## WP-09A Architecture Gate Preparation (Historical — gate completed 2026-08-19)

- Task document: `docs/tasks/WP-09A.md`.
- Status: `ACCEPTED_ARCHITECTURE_GATE`; Human approval and Codex confirmation recorded on 2026-08-19; no `services/core/` or `apps/web/` source changes in the gate.
- Key finding: the accepted Run-create API persists a `CREATED` Run, while the current `ExecutionService` / `RunSupervisor` path creates another Run. The execution target, ContextPackage authority, repeat semantics, response status, and failure persistence must be approved before WP-09B.
- Approved decision: Option A — `POST /api/v1/runs/{run_id}/execute`, using the persisted Run identity and Run ContextPackage reference; no duplicate Run.
- ADR impact: Codex/Human contract gate confirmed; ADR-004, ADR-007, ADR-008, and ADR-010 are respected with no ADR file changes. ADR-001–010 remain frozen.
- Item progress: `100%` for the architecture gate; no product points assigned or earned from this contract-only task.
- Accepted project progress remains **24/100 = 24%**; accepted FVS progress remains **16/22 = 72.7%**.
- Historical next owner completed: Codex review PASS and Human acceptance recorded on 2026-08-20.
- Browser E2E: remains `UNVERIFIED/SKIPPED` and is unrelated to this gate.

## WP-08B Development Gate

- Task document: `docs/tasks/WP-08B.md`.
- Scope: React UI authoring/selection using the accepted WP-08A ContextPackage POST endpoint; no Core changes.
- Architecture gate: implementation detail only; no new contract, ADR impact, migration, dependency, or endpoint.
- Product source changes: frontend implementation complete and accepted (Attempt 2, 61 tests PASS).
- Accepted project progress: **24/100 = 24%**; WP-08B earns **2/2 points**.
- Required next owner: WP-09A contract/architecture gate.
- Browser E2E: remains `UNVERIFIED/SKIPPED` and is deferred until the current development sequence is complete.

## WP-08A Development Gate

- Task document: `docs/tasks/WP-08A.md`.
- Scope: authenticated `POST /api/v1/projects/{project_id}/context-packages` using the existing Domain and Repository boundaries.
- Product source changes: WP-08A and WP-08B accepted; WP-09A implementation not started.
- ADR impact: NONE; WP-08B execution API remains a separate contract decision.
- Required next owner: WP-09A Codex/Human architecture gate.
- Browser E2E: remains `UNVERIFIED/SKIPPED` and is deferred until the current development sequence is complete.

## Current Next Gate

WP-09B, WP-09C, WP-09D, WP-10, and WP-11 are accepted. CP-02 is complete; WP-12 is the next gate for the CP-03 Core product baseline.

## WP-09B Development Gate

- Task document: `docs/tasks/WP-09B.md`.
- Status: `ACCEPTED` (Attempt 5); Codex independent review PASS and Human acceptance recorded on 2026-08-20.
- Scope: wire `POST /api/v1/runs/{run_id}/execute` to the existing persisted Run using the accepted Option A contract.
- Protected behavior: existing Run-create remains `201 CREATED` and inert; Run identity, ContextPackage reference, lifecycle events, failure persistence, sanitized reason, and no-fabricated-output rules are mandatory.
- Accepted project progress: **26/100 = 26%**; accepted FVS progress: **18/22 = 81.8%**; WP-09B earns **2/2 points**.
- Completed transition: WP-09C and WP-09D were implemented, independently reviewed, and Human-accepted; WP-10 is next.
- Symlink containment remains `UNVERIFIED/SKIPPED`; Browser E2E remains `UNVERIFIED/SKIPPED`; true concurrent HTTP duplicate execution remains `UNVERIFIED`.

## WP-09C Development Gate

- Task document: `docs/tasks/WP-09C.md`.
- Status: `ACCEPTED` (Attempt 4; IMPLEMENTATION_ATTEMPT: 3 / REVIEW_ATTEMPT: 4); Codex review PASS and Human acceptance recorded on 2026-08-20.
- Architecture result: implementation detail under ADR-004/008/010; no new ADR, migration, dependency, Domain model, or frontend change.
- Scope: five authenticated, run-scoped, read-only REST queries for Result, Finding, Evidence, Artifact metadata/reference, and durable RunEvent history.
- Required behavior: stable wrappers, deterministic ordering, `403/404/422`, durable reload, fail-closed ownership validation, and no fabricated output.
- Protected behavior: WP-09B execution command, Run-create semantics, lifecycle/CAS/failure persistence, WP-08A/B, ADR-001–010, and all migration/frontend files.
- Accepted project progress is **27/100 = 27%**; accepted FVS progress is **19/22 = 86.4%**; WP-09C earns **1/1 point**.
- Next owner: Codex/Human prepare and execute WP-10 final deterministic acceptance.
- Antigravity: `NOT_REQUIRED` for this Core-only task; Browser E2E remains `UNVERIFIED/SKIPPED`.

## WP-09D Development Gate

- Task document: `docs/tasks/WP-09D.md`.
- Status: `ACCEPTED` (Attempt 3); Codex review PASS and Human acceptance recorded on 2026-08-20; 78 frontend tests PASS, build PASS.
- Goal: add a read-only Result/History detail view that reloads Run metadata and all five accepted WP-09C query wrappers from REST.
- Scope: `apps/web` API client, props-based view/navigation, Run detail component, minimal styles, and Vitest integration coverage.
- Protected behavior: WP-08A/WP-08B, WP-09B execution/lifecycle/CAS/failure, WP-09C endpoint wrappers/ordering/ownership, ADR-001–010, no storage/secret/direct Core access.
- ADR impact: `NONE`. No endpoint, response, lifecycle, evidence, or dependency change.
- Accepted project progress is **28/100 = 28%**; accepted FVS progress is **20/22 = 90.9%**; WP-09D earns **1/1 point**.
- Browser E2E remains `UNVERIFIED/SKIPPED`; it is not a WP-09D implementation acceptance requirement.
- Next owner: Codex/Human prepare WP-10 final deterministic acceptance.

## WP-10 Final Deterministic Acceptance

- Task document: `docs/tasks/WP-10.md`.
- Status: `ACCEPTED` (Attempt 1); Codex deterministic acceptance PASS and Human acceptance recorded on 2026-08-20.
- Scope: final acceptance-only verification of the First Vertical Slice; no product source, REST contract, schema, migration, dependency, or ADR changes.
- Evidence: Core `169 passed, 1 skipped` from `170 collected` (WP-10 accepted baseline; current WP-11 full-Core run is `193 collected / 192 passed / 1 skipped`), fresh DB/Alembic/reopen-reload `4 passed`, frontend `78 passed`, frontend build PASS, baseline PASS, and `git diff --check` PASS; all exit code 0.
- Skipped/unverified: Browser DOM / Playwright E2E, Windows symlink escape, and true concurrent HTTP duplicate execution remain explicitly `UNVERIFIED/SKIPPED`.
- ADR impact: `NONE`.
- Scope deviation: `NONE`; pre-existing `docs/15_DOCUMENT_INDEX.md` remains unstaged and excluded.
- Accepted project progress is **30/100 = 30%**; accepted FVS progress is **22/22 = 100%**; WP-10 earns **2/2 CP-02 points**.
- CP-02 First Vertical Slice is complete. WP-11 is `ACCEPTED` (Attempt 4): Codex review PASS and Human acceptance recorded on 2026-08-20; `services/core/tests/test_wp11_work_mode.py` has 23 passed, full Core is `193 collected / 192 passed / 1 skipped`, and `validate_baseline.py` is PASS. WP-11 item progress is 100%. The roadmap does not define a standalone WP-11 point allocation inside CP-03, so accepted project progress remains **30/100** until that allocation is explicitly recorded; CP-03 is now in progress. Next owner: WP-12 planning.
