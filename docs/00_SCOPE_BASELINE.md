# PolyNexus Scope Baseline v1.0 Draft

日期：2026-08-17
目標完成：2026-10-31
Feature Freeze：2026-10-18

## 1. Product Positioning

PolyNexus 是 Local-first Multi-AI Collaboration & Validation Workspace。第一階段以「個人真正可長期使用」為首要目標，同時保留未來 Personal Hub、部門／團隊與企業演進邊界。

核心原則：
- Reuse Agent Runtime, Build Collaboration Intelligence.
- AI Opinion ≠ Evidence.
- Role ≠ Runtime ≠ Model ≠ Surface.
- Product-first, Personal-first, Local-first, Evolution-ready.
- 每個 V1 核心能力都必須有至少一條可實際操作的 End-to-End Vertical Slice。

## 2. V1 Maturity Classes

### CORE
必須深度完成、可長期個人使用、納入主要 Regression。

- Workspace / Project / Task / History
- Discuss / Review / Validate
- Council / Cross Review / Synthesis
- Evidence / Finding / Decision
- Artifact Model
- Context Package
- Declarative Workflow Foundation
- Event / Run Ledger
- Codex + OpenCode 深度 Runtime
- Doctor / Version Matrix
- Conformance Suite
- Backup / Restore / Migration Foundation
- Plugin-ready Extension Architecture

### BASELINE
必須有真實產品能力，但 V1 深度有限。

- ChatGPT / Claude / Gemini Web：Level 3A Assisted Automation + Manual Fallback
- Local AI：LM Studio / Ollama / Generic OpenAI-compatible
- Data Classification & Routing Policy
- Flexible Governance / Assurance
- Budget / Timeout / Parallelism Guard
- Minimal Evaluation / Usage Metrics
- Context Lifecycle baseline
- Artifact Lifecycle baseline
- UX Progressive Disclosure

### COMPATIBILITY
必須有真實接入／偵測／驗證路徑，可依成熟度標 SUPPORTED / PREVIEW / EXPERIMENTAL。

- Claude Code
- Gemini CLI
- Google Antigravity Runtime
- DeepSeek Harness / Framework Runtime
- ACP-compatible agents
- 其他常見 Agent Runtime / Harness

### FUTURE
V1 僅保留 Domain / Contract 邊界，不實作完整產品。

- Dynamic Plugin Marketplace / remote install / signing
- Visual Workflow Designer
- Personal Hub / Remote Nodes
- Multi-device Sync
- Multi-user / Team Server / Enterprise IAM
- Full RAG / Knowledge Graph / Advanced Auto Memory
- Distributed Scheduler
- Fully Autonomous Agent Team

## 3. Primary Work Modes

1. Discuss：獨立分析 → Cross Review → Consensus / Disagreement / Risks / Missing Info → Human Decision。
2. Review：Artifact / Code / Document → Findings / Severity / Blockers / Recommendations。
3. Validate：實際 Tool / Command / Rule / Document Check → Evidence → PASS / FAIL / NEED ACTION / HUMAN DECISION。

Discuss / Review / Validate 是工作意圖，可以組合；Develop 是 Workflow action / Agent role，不是 V1 第四個頂層入口。

## 4. V1 Workflow Templates

工程：
1. Code Review
2. Release Validation
3. Bug / Incident Analysis
4. Technical Design Review

專案：
5. Requirement Review
6. Change Impact Review

一般工作：
7. Document Review
8. SOP Review
9. Decision / Proposal Comparison

最高深度 Acceptance：Discuss/Council、Code/Artifact Review、Release Validation、Web AI Decision Review。

## 5. Governance Baseline

### Assurance Mode
- FLEXIBLE
- STANDARD
- VERIFIED

### Assurance Status
- UNREVIEWED
- SELF_REVIEWED
- CROSS_REVIEWED
- VERIFIED

平台不可關閉底線：
- 來源／Evidence 類型必須真實。
- 不得 Silent Policy / Permission Bypass。
- 不得把 AI Opinion 標為 Verified Evidence。
- 只有 Workflow 宣告的 Hard Gate Evidence 才具有 Verified PASS 否決權。

## 6. Data Policy

Classification：PUBLIC / INTERNAL / CONFIDENTIAL / RESTRICTED
Decision：ALLOW / APPROVAL_REQUIRED / DENY
Execution Mode：STANDARD / LOCAL_PREFERRED / LOCAL_ONLY

硬規則：Highest Classification Wins、不得自動降級、敏感資料 Local failure 不得 silent cloud fallback、外傳前必須 Egress Policy Check、例外核准需 Audit Evidence。

## 7. Extension Strategy

V1 = Plugin-ready, statically registered built-in extensions。

MUST：Versioned Contract、Manifest、Capabilities、Lifecycle、Registry、Config/Event Boundary、Failure Isolation、Conformance Tests。

不做：Marketplace、Remote Install、Auto Update、Signing、Hot Reload、Dependency Resolver、Third-party UI SDK。

## 8. Deployment Direction

V1 正式支援 `LOCAL_PERSONAL`。

Domain 預留：Actor、Execution Target、Repository Boundary、Artifact、Context、Event Ledger、Secret Reference、Schema Version。

未來演進：LOCAL_PERSONAL → PERSONAL_HUB → TEAM / DEPARTMENT → ENTERPRISE（只有取得實際價值與資源後才進行）。
