# Project State

Date: 2026-08-19
Version: Development Baseline v1.0 + Dev Preparation Profile v1.0.2
Milestone: First Vertical Slice — WP-06 accepted / WP-07 pending

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
1. Execute WP-07 Integration Acceptance from the accepted FVS-03 and WP-06 checkpoints.
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

Phase: First Vertical Slice In Progress
Next Phase: WP-07 Integration Acceptance

Current Branch: feature/first-vertical-slice
Current Baseline Commit: 2c8fcc0
Latest FVS Checkpoint: ed856a5 (`feat(web): add WP-06 project task run UI`)
Current Planned Task: WP-07 — Integration Acceptance
Active Writer: None (WP-06 accepted; WP-07 Codex acceptance pending)
Reviewer: Codex
Antigravity: NOT_REQUIRED

Architecture:
- ADR-001 through ADR-010 are CONFIRMED / FROZEN FOR V1 IMPLEMENTATION.

Development Environment:
- Windows development readiness: PASS
- Core pytest: 83 passed
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

Next Gate:
WP-07 Integration Acceptance, followed by the next Human approval gate.
