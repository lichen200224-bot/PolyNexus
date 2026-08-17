# PolyNexus Development Baseline v1.0

Date: 2026-08-17
Baseline State: READY FOR FIRST VERTICAL SLICE

## 1. Frozen Inputs

- Scope Baseline D01–D10
- PRD v1.0
- SA v1.0
- SD v1.0
- ADR-001～010
- Git / Single Active Writer policy
- Shared Memory / Token Budget policy
- V1 Feature Freeze: 2026-10-18
- V1 Acceptance: 2026-10-31

## 2. Repository Architecture

```text
apps/web                  React/TS/Vite UI
services/core             FastAPI Core
extensions/browser-companion  Chrome MV3 companion
workflows/builtin         Built-in workflow YAML
schemas                   Versioned schemas
tests/e2e                 Cross-component E2E
.agents/skills            Shared Codex/OpenCode/Antigravity skills
.agents/rules             Antigravity workspace rules
docs                      Source of truth
scripts                   Local bootstrap/test/preflight
```

## 3. Development Tool Routing

- Codex: architecture/core/high-risk implementation and targeted review.
- OpenCode: implementation/tests/templates/repetitive engineering.
- Antigravity: Browser/E2E/milestone independent verification.
- Human: scope/final decision/acceptance judgment.

Default = one Writer. Do not make every task pass through all three AIs.

## 4. First Vertical Slice Definition

Target 2026-09-06.

```text
Create/Open Project
  -> Create Review Task
  -> create ContextPackage
  -> invoke reference/mock Runtime through RuntimeAdapter
  -> produce Finding + AI_OPINION
  -> attach deterministic/system Evidence where applicable
  -> complete Run
  -> reload History from persistence
```

This slice proves Domain/Repository/Workflow/Evidence boundaries before Web AI/Local AI scale-out.

## 5. First Slice Work Breakdown

1. Project/Task/Run domain entities and repository interfaces.
2. SQLite implementation + initial Alembic migration.
3. Event Ledger lifecycle persistence.
4. Artifact metadata + local file store boundary.
5. ContextPackage versioning.
6. Evidence/Finding model.
7. Minimal Workflow loader + schema validation.
8. Reference/Mock RuntimeAdapter under Run Supervisor.
9. REST API for project/task/run basic operations.
10. Minimal React UI: project list + Review action + result view.
11. pytest integration path; later add Vitest/Playwright as UI emerges.

## 6. Acceptance Gate

PASS only if actual commands exit 0 and persisted data can be loaded again.

Minimum evidence:
- Core tests output + exit code.
- Workflow schema validation output.
- DB migration output.
- End-to-end slice run ID + persisted Finding/Evidence references.

## 7. Stop Conditions

Escalate before coding if a change requires:
- changing ADR-001～010;
- adding a new infrastructure subsystem;
- weakening evidence/provenance truth;
- storing secrets in ordinary domain data;
- making vendor-specific Core changes;
- moving a FUTURE feature into V1 without replacing scheduled work.
