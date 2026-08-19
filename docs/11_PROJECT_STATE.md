# Project State

Date: 2026-08-19
Version: Development Baseline v1.0 + Dev Preparation Profile v1.0.2
Milestone: First Vertical Slice — WP-07 ACCEPTED; FVS-MILESTONE-UI-E2E-01 ACCEPTED WITH HUMAN WAIVER

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
1. Continue approved development; defer Browser E2E re-test until development is complete.
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
2026-08-25: competition content v1 + Development Baseline operating on local machine.

## Current Development State

Phase: First Vertical Slice UI/Core Verification Accepted (Browser E2E Deferred)
Next Phase: Continued Development; Browser E2E Re-test Pending

Current Branch: feature/first-vertical-slice
Current Baseline Commit: 337bc47
Latest FVS Checkpoint: d7060c4 (`feat(core): add WP-07 execution integration`)
Current Planned Task: Continued development — next implementation task requires Human selection
Active Writer: NONE
Reviewer: Codex (FVS-MILESTONE-UI-E2E-01 accepted with Human waiver)
Antigravity: COMPLETED read-only verification; Browser E2E UNVERIFIED/SKIPPED

Architecture:
- ADR-001 through ADR-010 are CONFIRMED / FROZEN FOR V1 IMPLEMENTATION.

Development Environment:
- Windows development readiness: PASS
- Core pytest: 95 passed, 1 skipped (symlink containment UNVERIFIED; Human waiver accepted)
- Frontend build: PASS
- Frontend Vitest: 41 passed
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

FVS-MILESTONE-UI-E2E-01 (attempt 1) was accepted with an explicit Human waiver. Current acceptance evidence is 41 frontend Vitest tests, live Core/HTTP and Vite proxy checks reported by Antigravity, and static inspection. Browser DOM / Playwright E2E remains UNVERIFIED/SKIPPED and is deferred until development is complete.

- Frontend tests: 41 passed, exit code 0.
- Frontend build: PASS, exit code 0.
- Git diff check: PASS, exit code 0.
- Working tree: clean at review baseline `337bc47`.
- ADR impact: NONE.
- Scope deviation: NONE for product source; Browser E2E maturity remains deferred.

## Next Gate

Continue development. After development is complete, rerun Browser E2E and update this state with actual route, fixture, failure-path, and screenshot/artifact evidence.
