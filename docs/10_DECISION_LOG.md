# PolyNexus Decision Log

Status: Development Baseline v1.0

## Product / Scope Decisions

### D01 — Work Modes — CONFIRMED
Phase 1 top-level：Discuss / Review / Validate。Develop 是 workflow action，不是第四入口。

### D02 — Web AI — CONFIRMED
ChatGPT / Claude / Gemini Web 採 Level 3A Assisted Automation：Launch / Fill / User-confirmed Send / Capture / Normalize + mandatory manual fallback。Web output = AI_OPINION。

### D03 — Compatibility — CONFIRMED
Broad Compatibility + different depths。只有通過完整 Core Contract 才可 SUPPORTED/CERTIFIED。Integration type 與 maturity 分離。

### D04 — Local AI — CONFIRMED
Local AI 是 first-class AI resource。LM Studio / Ollama / Generic OpenAI-compatible baseline。可 Discuss/Review/Council/Document/Validation Analyst，但不取代 deterministic validator。

### D05 — Data Routing — CONFIRMED
PUBLIC / INTERNAL / CONFIDENTIAL / RESTRICTED + trust profiles + ALLOW/APPROVAL_REQUIRED/DENY。No automatic downgrade / no silent sensitive cloud fallback。

### D06 — Governance — CONFIRMED
Flexible Governance + Assurance：FLEXIBLE / STANDARD / VERIFIED；UNREVIEWED / SELF_REVIEWED / CROSS_REVIEWED / VERIFIED。平台底線不可偽造 Evidence/Provenance。

### D07 — Plugin Architecture — CONFIRMED
Plugin-ready now, Plugin Platform later。V1 built-in/static extensions 使用 versioned contract、manifest、registry、lifecycle、capability、failure isolation、conformance。

### D08 — Workflow — CONFIRMED
Minimal Declarative Workflow Foundation + 9 built-in templates；不做 visual designer / arbitrary script nodes / generic BPM。

### D09 — Competition Golden Path — CONFIRMED
Engineering Review & Validation 為主（70–80%），Executive/Web AI Decision Review 為延伸（20–30%）。

### D10 — Long-term Product — CONFIRMED
Phase 1 必須是可用的 LOCAL_PERSONAL Product，且以同一 Domain/Contract 向 Personal Hub、部門／Team、Enterprise 演進；原始功能範圍保留，以成熟度分級控制深度。

### Cross-cutting — CONFIRMED
V1 補足最小必要：Compatibility/Migration、Evaluation/Quality、Cost/Resource Control、Context Lifecycle、Artifact Lifecycle、UX Complexity Control。

## Architecture Decisions

ADR-001～010 全部 CONFIRMED；詳見 `18_ARCHITECTURE_DECISIONS.md`。

- ADR-001 Browser-first local web; desktop-wrapper-ready.
- ADR-002 Python/FastAPI/asyncio + SQLAlchemy/Alembic/SQLite.
- ADR-003 React/TypeScript/Vite.
- ADR-004 REST + WebSocket + Durable Event Ledger.
- ADR-005 pytest + Vitest + Playwright + Antigravity real-browser validation.
- ADR-006 Chrome MV3 Thin Companion + authenticated localhost API.
- ADR-007 Core-owned Run Supervisor + normalized lifecycle/cancel/cleanup.
- ADR-008 SQLite metadata + filesystem artifacts + hash + versioned ContextPackage.
- ADR-009 YAML workflow + schema validation + canonical model + fixed nodes.
- ADR-010 SecretRef + OS-backed SecretStore + least privilege/redaction.
