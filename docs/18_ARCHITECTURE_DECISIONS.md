# PolyNexus Architecture Decision Baseline — ADR-001～010

Status: CONFIRMED / FROZEN FOR V1 IMPLEMENTATION
Date: 2026-08-17

Changes to these decisions require a new ADR entry, impact assessment, and explicit human approval.

## ADR-001 — Application Shell
Decision: Browser-first Local Web Application; desktop-wrapper-ready.

V1 runs Core locally and opens the UI in the user browser. Do not introduce mandatory Electron/Tauri packaging in V1. React UI must remain wrapper-compatible for a later desktop shell.

## ADR-002 — Core Stack
Decision: Python + FastAPI + asyncio; SQLAlchemy + Alembic + SQLite for metadata persistence.

Domain code is separated from infrastructure. Large artifacts do not live in SQLite. No Redis/Celery/Kafka/microservice requirement in V1.

## ADR-003 — Frontend
Decision: React + TypeScript + Vite.

No SSR/SEO framework requirement. UI uses progressive disclosure and must not become a raw Runtime control panel.

## ADR-004 — UI/Core Boundary
Decision: REST commands/queries + WebSocket live events + Durable Event Ledger.

UI never directly owns DB/process/vendor state. Live connection loss must not erase durable task/run/evidence history.

## ADR-005 — Verification Stack
Decision: pytest + Vitest + Playwright. Antigravity is used for real Browser/E2E/compatibility validation, not as the only deterministic release gate.

External Web AI UI availability is not a deterministic Core hard gate.

## ADR-006 — Browser Companion
Decision: Chrome MV3 thin companion, vendor-specific site drivers, authenticated loopback API.

Core contains no vendor DOM selectors. Mandatory manual/clipboard fallback. Native Messaging is future/optional, not V1 requirement.

## ADR-007 — Runtime Process Model
Decision: Core-owned Run Supervisor + Adapter-owned Runtime Logic.

Normalized lifecycle: CREATED → STARTING → RUNNING → terminal state. Cancel/timeout must verify real process-tree/resource cleanup. Resume maturity: NATIVE / MANAGED / NONE. V1 ExecutionTarget=LOCAL; future targets are architectural only.

## ADR-008 — Artifact / Context Storage
Decision: SQLite metadata + filesystem artifacts + content hash + versioned ContextPackage.

Context is a reference manifest, not a copied prompt blob. Runtime data is separate from user source repo by default. Artifact content can later move to NAS/object storage without changing Domain semantics.

## ADR-009 — Workflow Definition
Decision: YAML authoring + JSON Schema validation + Canonical WorkflowDefinition.

Fixed V1 nodes: CONTEXT / AI_TASK / PARALLEL_AI / CROSS_REVIEW / TOOL / EVIDENCE_CHECK / HUMAN_GATE / SYNTHESIS / limited CONDITION. No arbitrary script node or general programming language. Workflow version is immutable for historical runs.

## ADR-010 — Secret / Security Boundary
Decision: SecretRef + OS-backed SecretStore + least privilege + redaction + authenticated loopback API.

Secret value is prohibited from ordinary Domain tables, Event Ledger, Evidence, Artifacts, logs, export/backup, Git, handoff, telemetry. Credential, permission, and data-routing policy remain separate concerns.

## V1 Architecture Guardrails

- No vendor-specific Core branching for normal adapter differences.
- No microservices/distributed scheduler/mandatory Docker.
- No Web Companion single-point dependency.
- No AI opinion masquerading as deterministic evidence.
- No silent sensitive-data cloud fallback.
- No architecture change merely to support one vendor if an adapter boundary is sufficient.

## ADR-011 — Runtime Binding and Transport Contract

- Decision status: `HUMAN_ACCEPTED` on 2026-08-25 after independent documentation review.
- Implementation status: `NOT_IMPLEMENTED / NOT_AUTHORIZED`.
- Decision: Preserve independent Provider / TransportKind / Runtime / Adapter / ExecutionTarget semantics and plan a Run-owned immutable RuntimeBindingSnapshot through existing Supervisor/Adapter boundaries; see `docs/29_ADR_011_RUNTIME_BINDING_AND_TRANSPORT.md`.
- A future Alembic migration, deterministic legacy backfill, rollback/restore, product source changes and each `PRE-WP14-A/B` implementation task require separate Human authorization; architecture acceptance is not Git, migration or implementation permission.
- ADR-001 through ADR-010 remain unchanged, confirmed and frozen; `docs/30_RUNTIME_CONTRACT_FOUNDATION_GATE.md` separately defines `PRE-WP14-A` and `PRE-WP14-B`.
