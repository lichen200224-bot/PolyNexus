# PolyNexus Current Product State

Date: 2026-09-15 (Asia/Taipei)
Task: `ENHANCED-DELIVERY-REPLAN-01`
Status: `REMOTE_RECONCILED / HUMAN_DIRECTION_APPROVED / DOCUMENTATION_CANDIDATE`
Product version: `UNCHANGED`

本文件是後續 routing 的 current-state read model，不覆寫既有 frozen source、歷史 acceptance 或 exact evidence。歷史文件中的 `NEXT_GOAL`、`NOT_STARTED`、`HOLD` 只有在與本文件及 canonical remote 一致時才可作為目前進度。產品完成狀態必須由 exact remote SHA、實際 source、實際 evidence 與適用的 Human/independent decision 判定。

## 1. Canonical remote facts

Canonical repository: `lichen200224-bot/PolyNexus`。

| Ref / checkpoint | Exact SHA | Current disposition |
|---|---|---|
| `feature/g24-g30-development-completion-routing` | `e9538f328f409e2cb7d6868a8b79cc33ba4bdd87` | GitHub default route currently resolves here; same SHA as D1B |
| `codex/product-d1b` | `e9538f328f409e2cb7d6868a8b79cc33ba4bdd87` | D1B implementation line; implementation evidence records technical validation and isolated Human product acceptance |
| `codex/product-d2a` | `8d219c999516ce651ac952c38bd31e67d19c54cb` | Real Codex external-runtime technical checkpoint in D1B ancestry; do not inflate its historical review status |
| `codex/product-b01-tech` | `ca85d22c44062d2856ab037a1ee1556ea26c70cc` | `B01_TECHNICAL_READY`; fresh engineering review receipt PASS; final Human UAT still pending |
| `feature/mcf-02-opencode-acp-runtime` | `030890b30160f1063ac2cef1d36705a9ea70bddb` | `REJECTED / NOT_ADOPTED` for D2a integration; wrong ancestry/destructive delta and fixture-only target evidence; never merge as a whole |
| `governance/current` | `1ea8ce3df9bf6b1fc0899fcafaedeba2f4052af4` | Governance reference; separate lineage, not product completion proof |
| `planning/full-delivery-design-consolidation` | `36d0fe453bbed7bea03f7dbcca67942f1b2591cf` | Historical docs repair candidate pending fresh independent review; retained as planning/source provenance, not current product-state authority |

## 2. Accepted / evidenced progress

### D1B product state

`e9538f328f409e2cb7d6868a8b79cc33ba4bdd87` contains the current D1B line. Durable evidence records:

- Candidate exact-view, verification, Assurance and eligibility surfaces;
- Local-personal Human enrollment/session/challenge/decision protocol;
- Windows Hello / WebAuthn Human UAT against an isolated runtime database;
- append-only Human decision and accepted-result semantics;
- D1a generation/workspace/policy/secret capabilities preserved in lineage;
- D2a external-runtime source present in lineage.

The D1B evidence record states `TECHNICAL_VALIDATION_PASS / HUMAN_PRODUCT_ACCEPTANCE_PASS` for its bounded isolated D1B Local-Personal scope. This does not imply full enhanced-product completion, release, deployment or future runtime-fleet acceptance.

### B01 technical checkpoint

`ca85d22c44062d2856ab037a1ee1556ea26c70cc` is two commits ahead of D1B. Its evidence records:

- real bounded Codex executor bug fix in a synthetic Git repository;
- failure → cleanup → retry and late-abort isolation;
- real Windows Job Object process-tree timeout evidence;
- accepted P0 verify/reconstruction technical proof;
- Core full suite `914 passed, 1 skipped` at the recorded checkpoint;
- Web `94` tests and production build PASS;
- browser companion `10` tests PASS;
- a fresh read-only engineering review receipt with exit `0`.

It remains `PENDING_FINAL_HUMAN_UAT`. B01 does not independently promote the whole product and does not grant release/merge authority.

## 3. Architecture already present and therefore not to be rebuilt

The enhanced-delivery plan MUST reuse, not duplicate:

- Project / Task / WorkGeneration / Run / Candidate identity separation;
- immutable RuntimeBinding and Core-owned Run lifecycle;
- Generation ownership/fence/retry/abort/recovery semantics;
- ContextPackage / Artifact / Evidence / Finding / Candidate boundaries;
- Core-owned `PROJECTED_STAGING`, input/output allowlists and external execution envelope;
- policy / egress / classification / SecretRef boundaries;
- verification / Assurance / Human exact-view decision protocol;
- Council analysis / cross-review / synthesis model;
- existing static ModuleRegistry / RuntimeRegistry / RuntimeSupervisor foundation.

Do not introduce parallel `AgentSession`, `AgentMessage`, `AgentHandoff`, `AgentWorkspace` or other duplicate authority models unless a future independently reviewed gap proves the existing contracts insufficient.

## 4. Current gaps that remain material for the enhanced version

The remaining product-level gaps are intentionally narrowed to:

1. `G0` — reconcile B01 technical candidate and current state before new product writes;
2. `D2b` — Strategic Runtime Fleet: real OpenCode, Gemini CLI, Claude Code and Antigravity execution behind the existing Core contract, without requiring equal vendor capability; separate FD-09 / PN-022/PN-023 Local AI work remains required for real LM Studio, Ollama and Generic compatible endpoints in D2B-06, with per-target evidence;
3. `D3` — expose existing Council/workflow semantics as bounded multi-agent role routing and structured handoff;
4. `D4` — Unified Work Control Plane / Runtime Fleet Doctor using a non-persistent aggregated read model, not a second execution engine;
5. `T1/T2` — cross-runtime functional and failure/security SIT;
6. `DELIVERY` — exact completion/evidence reconciliation and operator material;
7. one concentrated `FINAL_HUMAN_UAT` for the required Human-only scenarios, including the pending B01 Human-only closure.

## 5. Explicitly deferred unless frozen source proves required now

The enhanced version does not require the following as completion blockers unless an authoritative existing requirement says otherwise:

- autonomous quality/cost model optimizer or dynamic Agent router;
- capability equality across every runtime;
- vendor-native resume/roaming for every runtime;
- arbitrary MCP/plugin/remote-skill enablement;
- dynamic plugin marketplace / remote install / hot reload;
- direct agent-to-agent chat or a second shared-conversation domain;
- generic BPM / arbitrary graph scripting;
- WebSocket as a prerequisite when bounded polling/reconnect satisfies the required UX;
- cloud sync, distributed execution, multi-user RBAC or mobile control plane.

## 6. Current routing

The next documentation action is fresh independent review of the documentation candidate produced by `ENHANCED-DELIVERY-REPLAN-01`.

After that review passes, product execution proceeds without per-goal Human micro-approval:

```text
G0 Current/B01 reconciliation
  -> D2b Strategic Runtime Fleet
  -> D2B-06 FD-09 Local AI endpoints (LM Studio/Ollama/Generic compatible)
  -> D3 Multi-Agent Council / Workflow
  -> D4 Unified Work Control Plane
  -> D4-NEXT only source-required remainder
  -> T1 Functional Golden SIT
  -> T2 Failure / Security SIT
  -> DELIVERY
  -> FINAL_HUMAN_UAT
```

Codex is the sole product Writer/Test Executor. ChatGPT is the Project PM / Architecture & Governance Authority / independent Product Acceptance Center for exact Codex candidates and does not modify those candidates during review. Within the approved scope, a ChatGPT PASS may authorize Codex to continue to the next dependency-ready unit without another Human approval. Human intervention is reserved for the final Human UAT and genuine exception gates defined in `EXECUTION_CONTRACT.md`.
