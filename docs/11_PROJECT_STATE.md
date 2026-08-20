# Project State

Date: 2026-08-20
Version: Development Baseline v1.0 + Dev Preparation Profile v1.0.2
Milestone: First Vertical Slice — WP-08A/WP-08B/WP-09B/WP-09C ACCEPTED; UI/Core waiver accepted; ROADMAP-01 CONFIRMED

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
1. Prepare WP-09D Result/History UI task scope and Writer handoff; defer Browser E2E re-test until development is complete.
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
Prepare WP-09D task scope and handoff; then OpenCode implementation and Codex review.

## Current Development State

Phase: First Vertical Slice — WP-09C REST queries (Attempt 4) ACCEPTED; Codex PASS and Human acceptance recorded on 2026-08-20
Next Phase: WP-09D Result/History UI task preparation; Browser E2E Re-test deferred

Current Branch: feature/first-vertical-slice
Current Baseline Commit: 337bc47
Latest FVS Checkpoint: d7060c4 (`feat(core): add WP-07 execution integration`)
Current Planned Task: WP-09D — Result/History UI with durable reload and error states (task scope preparation pending)
Active Writer: NONE — WP-09C accepted; WP-09D task handoff pending
Reviewer: Codex — WP-09C PASS recorded; next prepares WP-09D scope
Antigravity: NOT_REQUIRED for WP-09C (Core-only); Browser E2E UNVERIFIED/SKIPPED

Architecture:
- ADR-001 through ADR-010 are CONFIRMED / FROZEN FOR V1 IMPLEMENTATION.

Development Environment:
- Windows development readiness: PASS
- Core pytest: 169 passed, 1 skipped (170 collected, symlink containment UNVERIFIED; Human waiver accepted) — historical WP-09B evidence was 134 passed, 1 skipped
- Frontend Vitest: 61 passed
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

WP-09C Attempt 4 was accepted after current Core evidence, Codex independent review PASS, and Human acceptance on 2026-08-20. Browser DOM / Playwright E2E remains UNVERIFIED/SKIPPED and is deferred until development is complete; true concurrent HTTP duplicate-command execution remains UNVERIFIED.

- WP-09C targeted query tests: 24 passed, exit code 0.
- WP-09B regression tests: 36 passed, exit code 0.
- Full Core tests: 169 passed, 1 skipped, exit code 0 (170 collected).
- Baseline validation: PASS, exit code 0.
- Git diff check: PASS, exit code 0.
- WP-09C: ACCEPTED, 1/1 point earned.
- Accepted project progress: **27/100 = 27%**.
- Accepted FVS progress: **19/22 = 86.4%**.
- ADR impact: NONE.
- Scope deviation: `docs/15_DOCUMENT_INDEX.md` remains a pre-existing cross-attempt task-preparation change; no product scope change.

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

WP-09B Attempt 5 and WP-09C Attempt 4 are accepted. Next gate is WP-09D task scope and Writer handoff preparation.

## WP-09B Development Gate

- Task document: `docs/tasks/WP-09B.md`.
- Status: `ACCEPTED` (Attempt 5); Codex independent review PASS and Human acceptance recorded on 2026-08-20.
- Scope: wire `POST /api/v1/runs/{run_id}/execute` to the existing persisted Run using the accepted Option A contract.
- Protected behavior: existing Run-create remains `201 CREATED` and inert; Run identity, ContextPackage reference, lifecycle events, failure persistence, sanitized reason, and no-fabricated-output rules are mandatory.
- Accepted project progress: **26/100 = 26%**; accepted FVS progress: **18/22 = 81.8%**; WP-09B earns **2/2 points**.
- Completed transition: WP-09C was implemented, independently reviewed, and Human-accepted; WP-09D preparation is next.
- Symlink containment remains `UNVERIFIED/SKIPPED`; Browser E2E remains `UNVERIFIED/SKIPPED`; true concurrent HTTP duplicate execution remains `UNVERIFIED`.

## WP-09C Development Gate

- Task document: `docs/tasks/WP-09C.md`.
- Status: `ACCEPTED` (Attempt 4; IMPLEMENTATION_ATTEMPT: 3 / REVIEW_ATTEMPT: 4); Codex review PASS and Human acceptance recorded on 2026-08-20.
- Architecture result: implementation detail under ADR-004/008/010; no new ADR, migration, dependency, Domain model, or frontend change.
- Scope: five authenticated, run-scoped, read-only REST queries for Result, Finding, Evidence, Artifact metadata/reference, and durable RunEvent history.
- Required behavior: stable wrappers, deterministic ordering, `403/404/422`, durable reload, fail-closed ownership validation, and no fabricated output.
- Protected behavior: WP-09B execution command, Run-create semantics, lifecycle/CAS/failure persistence, WP-08A/B, ADR-001–010, and all migration/frontend files.
- Accepted project progress is **27/100 = 27%**; accepted FVS progress is **19/22 = 86.4%**; WP-09C earns **1/1 point**.
- Next owner: Codex prepares WP-09D task scope and handoff.
- Antigravity: `NOT_REQUIRED` for this Core-only task; Browser E2E remains `UNVERIFIED/SKIPPED`.
