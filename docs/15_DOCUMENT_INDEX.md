# PolyNexus Document Index

## Mandatory session entry

New session reads in this order:

1. `../AGENTS.md`
2. `37_CURRENT_ROUTING_INDEX.md`
3. current `tasks/<TASK>.md`
4. relevant Project State / ADR / code/tests as needed

Conversation history and local path are not Source of Truth.

| 文件 | 用途 | Agent 預設載入 |
|---|---|---|
| `00_SCOPE_BASELINE.md` | V1 scope / maturity | Scope task |
| `01_PRD.md` | Product requirements | Product/UX |
| `02_SA.md` | System analysis | Architecture |
| `03_SD.md` | System design | Core design |
| `04_DEVELOPMENT_PLAN.md` | Development plan | Planning |
| `05_GIT_WORKFLOW.md` | Remote-first / SHA-first Git workflow | **Git / cross-machine必讀** |
| `06_AI_TOOL_COLLABORATION.md` | Role-first multi-AI collaboration | **Routing必讀** |
| `07_SHARED_MEMORY.md` | Shared memory/token rules | Context design |
| `08_ACCEPTANCE_STRATEGY.md` | Immutable Candidate / Evidence acceptance | **Review/acceptance必讀** |
| `09_RISK_REGISTER.md` | Risk register | Milestone |
| `10_DECISION_LOG.md` | Product/ADR decisions | Architecture change |
| `11_PROJECT_STATE.md` | Project historical/current state ledger | Project status |
| `12_HANDOFF_CURRENT.md` | Legacy/detailed handoff ledger | Deep handoff history |
| `15_DOCUMENT_INDEX.md` | Document map | Navigation |
| `17_DEFINITION_OF_DONE.md` | DoD | Development/acceptance |
| `18_ARCHITECTURE_DECISIONS.md` | Frozen/accepted ADR baseline | Core architecture |
| `25_LOCAL_WORKSPACE_PROFILE.md` | Portable machine-local workspace rules | **Environment setup** |
| `28_MASTER_DEVELOPMENT_ROADMAP.md` | Roadmap/checkpoints | Progress monitoring |
| `29_ADR_011_RUNTIME_BINDING_AND_TRANSPORT.md` | Runtime binding architecture | Runtime work |
| `30_RUNTIME_CONTRACT_FOUNDATION_GATE.md` | Runtime contract gate | Runtime work |
| `31_ADR_012_RUNTIME_DOCTOR_REPORTING.md` | Doctor reporting | Runtime Doctor |
| `33_DEVELOPMENT_PROGRESS_AND_GOAL_EXECUTION_STANDARD.md` | G24–G30 bounded score/routing | Legacy/current G24–G30 |
| `34_ADR_013_MODULAR_CORE_EXTENSION_ARCHITECTURE.md` | Modular Core architecture | Extension work |
| `35_ADR_014_DURABLE_EVENT_ORDERING_AND_CANCELLATION_CLEANUP.md` | BASELINE-DEBT-01 architecture (when present on implementation branch) | Debt implementation/review |
| `36_POLYNEXUS_CROSS_MACHINE_GOVERNANCE.md` | PolyNexus FlowGov-compatible governance profile | **所有跨機/跨工具工作** |
| `37_CURRENT_ROUTING_INDEX.md` | Active task/routing/checkpoint truth | **每個 session 必讀** |
| `../governance/POLYNEXUS_PROFILE.yaml` | Machine-readable project governance profile | Tooling / Repo Doctor |

## Task documents

`docs/tasks/` contains task-specific scope, stop conditions, evidence, and routing. Current task doc outranks stale historical handoff text for that task.

## Evidence

Large/raw evidence remains under ignored artifact storage or CI artifacts. Tracked docs should contain deterministic summaries, hashes/references, and actual exit codes rather than raw secrets or massive logs.

## Path rule

No tracked document should require a fixed repository directory. Use repo-relative paths or symbolic `<REPO_ROOT>` / `<TASK_WORKTREE>` / `<LOCAL_EVIDENCE_ROOT>`.
