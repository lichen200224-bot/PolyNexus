# PolyNexus V1 Development Plan v1.0

Date: 2026-08-17
Target: V1 Feature Freeze 2026-10-18 / Acceptance Complete 2026-10-31
Competition Initial Review: 2026-09-07

## Phase 0 — Baseline / Competition (8/17–8/25)

### Completed / Frozen
- D01–D10 scope/product decisions.
- ADR-001～010 architecture decisions.
- PRD/SA/SD Development Baseline v1.0.
- Shared Git/Skills/Memory/Token policy.
- Initial repository scaffold.

### Remaining by 8/25
- Verify baseline locally on Windows.
- Competition proposal and deck content confidence gate.
- Confirm major UI flow/mockups and competition claims are marked Implemented / Planned V1 / Future truthfully.

## Phase 1 — First Vertical Slice (8/26–9/06)

Goal: prove the system can persist and execute one real product path before integration breadth.

Deliverable:
`Project → Review Task → ContextPackage → RuntimeAdapter → Finding/Evidence → Result → History`.

Work:
1. Domain entities and Repository interfaces.
2. SQLite implementation + Alembic initial migration.
3. Event Ledger.
4. Artifact metadata/file store.
5. ContextPackage versioning.
6. Finding/Evidence model.
7. Workflow YAML/schema loader.
8. Reference/Mock Runtime under Run Supervisor.
9. REST APIs.
10. Minimal React Project/Review/Result UI.
11. Core integration tests.

Gate 2026-09-06: end-to-end path repeats from fresh DB and actual tests exit 0.

## Competition Submission Gate — 9/07

Final proposal/deck/required upload materials are checked against the actual form. Competition work must not stop product coding after content freeze except necessary corrections.

## Phase 2 — Core Product (9/07–9/20)

- Discuss / Review / Validate.
- Council / Parallel AI / Cross Review / Synthesis.
- Workflow hard-gate semantics.
- Codex deep Runtime adapter.
- OpenCode deep Runtime adapter.
- Doctor / Conformance / Compatibility matrix.

Gate 9/20: Core flows work without Web Companion dependency.

## Phase 3 — Web / Local / Policy (9/21–10/04)

- LocalModelEndpoint.
- LM Studio / Generic OpenAI-compatible / Ollama profiles.
- WebSurface Contract.
- ChatGPT / Claude / Gemini Level 3A drivers + fallback.
- Browser real E2E via Antigravity.
- Data Classification / Routing / LOCAL_ONLY.

Gate 10/04: integration baseline usable; driver failure does not break Core.

## Phase 4 — Product Completion (10/05–10/18)

- 9 built-in workflow templates.
- Backup / Restore.
- Migration acceptance.
- Budget/timeout/concurrency guard.
- Basic evaluation/quality metrics.
- UX progressive disclosure pass.
- Four Golden Workflow deep regression.

10/18 FEATURE FREEZE.

## Phase 5 — Hardening / Acceptance (10/19–10/31)

No new feature scope.

- Full regression / failure injection.
- Cancel / timeout / child cleanup.
- Secret / egress / policy review.
- Backup/restore/migration fresh test.
- Clean install/packaging test.
- Compatibility matrix / Known Limitations.
- V1 RC Acceptance.

## AI Tool Allocation

Default task-share target (not hard quota):
- OpenCode ~50–60% task count: implementation/tests/templates/repetitive work.
- Codex ~30–40%: architecture/core/hard bug/critical review.
- Antigravity ~10–15%: browser/E2E/milestone verification.

Rules:
- One Active Writer.
- One task does not automatically pass through all three tools.
- Delta handoff only.
- Machine filter logs first.
- High reasoning/max reserved for high-coupling decisions/root cause.

## Scope Escalation Rule

Any new V1 feature request must identify either:
1. which scheduled work it replaces, or
2. why it is a low-cost foundation whose omission causes clear major refactor.

Otherwise move to V1.x/Future.
