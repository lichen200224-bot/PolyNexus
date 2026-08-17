# Project State

Date: 2026-08-17
Version: Development Baseline v1.0 + Dev Preparation Profile v1.0.2
Milestone: Architecture Freeze / Repository Scaffold

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
1. Establish Development Baseline v1.0 repository and initial Git checkpoint.
2. Verify scaffold/preflight/tests on target Windows environment.
3. Prepare competition proposal/deck content confidence gate by 2026-08-25.
4. Begin First Vertical Slice immediately after baseline verification.

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
