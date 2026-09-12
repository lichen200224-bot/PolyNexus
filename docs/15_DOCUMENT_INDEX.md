# PolyNexus Document Index

| 文件 | 用途 | Agent 預設載入 |
|---|---|---|
| `00_SCOPE_BASELINE.md` | V1 功能範圍與成熟度 | 架構／範圍任務才讀 |
| `01_PRD.md` | Product Requirements Document v1.0 | 產品／UX／需求任務 |
| `02_SA.md` | System Analysis v1.0 | 架構、Domain、整合任務 |
| `03_SD.md` | System Design v1.0 | 核心模組、Contract、流程設計 |
| `04_DEVELOPMENT_PLAN.md` | 8/17–10/31 開發計畫 | 規劃／進度任務 |
| `05_GIT_WORKFLOW.md` | 同目錄多 AI Git 操作規範 | 開發／交接任務 |
| `06_AI_TOOL_COLLABORATION.md` | Codex / OpenCode / Antigravity 分工 | 指派任務前 |
| `07_SHARED_MEMORY.md` | 共用記憶與 Token 控制 | 新 session / 交接設計 |
| `08_ACCEPTANCE_STRATEGY.md` | V1 驗收與 Evidence 規則 | 測試／RC 任務 |
| `09_RISK_REGISTER.md` | 技術、時程、供應鏈風險 | 里程碑 Review |
| `10_DECISION_LOG.md` | 已確認 Product + ADR 摘要 | 架構變更前 |
| `11_PROJECT_STATE.md` | 目前版本、里程碑、阻塞 | **每個 session 先讀** |
| `12_HANDOFF_CURRENT.md` | 當前 Task Delta Handoff | **每個 session 先讀** |
| `13_COMPETITION_SUBMISSION_PLAN.md` | 9/7 初審交件計畫 | 競賽文件任務 |
| `14_COMPETITION_SLIDE_OUTLINE.md` | AI Use Case 簡報骨架 | 簡報任務 |
| `16_TOOLING_BOOTSTRAP.md` | Skills / Rules / Plugin/MCP 準備 | 首次環境建置 |
| `17_DEFINITION_OF_DONE.md` | 各成熟度 DoD | 開發／驗收 |
| `18_ARCHITECTURE_DECISIONS.md` | ADR-001～010 frozen baseline | **架構／核心開發必讀** |
| `19_DEVELOPMENT_BASELINE.md` | 第一條 Vertical Slice 執行契約 | **下一個開發任務必讀** |
| `20_FIRST_VERTICAL_SLICE_PLAN.md` | 第一條產品垂直切片詳細工作包 | Slice 開發必讀 |
| `28_MASTER_DEVELOPMENT_ROADMAP.md` | 全專案開發順序、範圍、時程、權重與 Checkpoint | **專案進度監控／每次交接必讀** |
| `29_ADR_011_RUNTIME_BINDING_AND_TRANSPORT.md` | Runtime/Profile/Adapter/Transport identity 與 immutable binding 架構 | **Runtime／Extension 架構必讀** |
| `30_RUNTIME_CONTRACT_FOUNDATION_GATE.md` | Runtime contract foundation、registry/binding/cleanup 驗收基線 | **Runtime／Extension 實作前必讀** |
| `31_ADR_012_RUNTIME_DOCTOR_REPORTING.md` | Runtime Doctor、capability/version/maturity truthfulness | Runtime inventory / conformance 任務 |
| `33_DEVELOPMENT_PROGRESS_AND_GOAL_EXECUTION_STANDARD.md` | Development-only 100 分制、WP ledger、G24–G30 授權與驗收規範 | **G24–G30 每個新 task 必讀** |
| `34_ADR_013_MODULAR_CORE_EXTENSION_ARCHITECTURE.md` | Modular Core、Module/Adapter 邊界、static extension contract 與未來外接 Runtime 方向 | **Extension／Plugin／Runtime 架構必讀** |
| `35_ADR_014_DURABLE_EVENT_ORDERING_AND_CANCELLATION_CLEANUP.md` | Human-approved durable event ordering、0003 migration 與 cancellation cleanup | **BASELINE-DEBT-01 實作／Review 必讀** |
| `tasks/ARCH-MODULAR-CORE-01.md` | MCF-01 static module contract 的 Codex 實作與獨立驗收工作包 | **MCF-01 Codex 啟動必讀** |
| `tasks/G24-G30-DEVELOPMENT-COMPLETION-ROUTING.md` | Luna High 的 G24–G30 系統提示詞、外部驗證 prompt 與 stop condition | **執行對應 Goal 必讀** |
| `../artifacts/verification/g24-development-ledger-20260902/ledger.json` | G24 current machine-readable WP-11–WP-32 ledger and score reconciliation | **G24 acceptance evidence** |
| `../artifacts/verification/g24-development-ledger-20260902/summary.md` | G24 current ledger scope, boundaries, and limitations | **G24 acceptance evidence** |
| `../artifacts/verification/g24-development-ledger-20260902/commands-and-exit-codes.md` | G24 current deterministic command evidence and exit codes | **G24 acceptance evidence** |
| `tasks/WP-08A.md` | ContextPackage REST Contract implementation task | WP-08A Writer / Review handoff |
| `tasks/WP-08B.md` | ContextPackage UI authoring / selection implementation task | Antigravity Writer / Codex Review handoff |
| `tasks/WP-09A.md` | Execution command API contract and architecture gate proposal | Human decision / Codex architecture review |
| `tasks/WP-09B.md` | Approved existing-Run execution command implementation task | OpenCode Writer / Codex Review handoff |
| `21_DEPENDENCY_BASELINE.md` | 初始依賴版本與 lock 規則 | 環境/依賴更新任務 |
| `22_BASELINE_VALIDATION_REPORT.md` | Baseline scaffold 實際驗證與 SKIP | Baseline/交接/驗收 |

## Token 原則

新 session 只先讀 `AGENTS.md + PROJECT_STATE + HANDOFF_CURRENT`。再依任務載入 1–3 份必要文件。聊天歷史不是 Source of Truth。

## Development preparation profile additions
- `25_LOCAL_WORKSPACE_PROFILE.md` — current Windows canonical workspace `D:\AI學習教材\PolyNexus` and portability rule.
- `26_DEV_PREPARATION_PATCH_v1.0.2.md` — Drive-D development-preparation patch summary.
