# PolyNexus Product Requirements Document (PRD) v1.0 Baseline

Status: DEVELOPMENT BASELINE
Date: 2026-08-17

## 1. Product Positioning

PolyNexus 是 `Local-first Multi-AI Collaboration & Validation Workspace`。Phase 1 首先服務單一個人長期工作需求，同時保留未來 Personal Hub、部門／Team、Enterprise 的演進邊界。

產品優先順序：
1. 做得出來。
2. 真正可用。
3. 可重複、可驗證、可接續。
4. 再以相同 Domain / Contract 擴展。

## 2. Problem Statement

目前使用者在 ChatGPT、Claude、Gemini、Codex、OpenCode、Agent Runtime 與 Local AI 間切換時，主要痛點是：
- Context 重複搬運與遺失。
- 多 AI 結果難比較，分歧容易被摘要掉。
- AI Opinion 與真實 Tool/Test Evidence 混在一起。
- Web AI、CLI Agent、Local Model 各自孤立。
- 交接依賴聊天歷史，無法穩定接續。
- 上游 Runtime / Web UI 更新造成版本漂移與相容性風險。
- 個人工作缺乏統一 Workflow、Evidence、Decision、Artifact、History。
- 多 AI 使用若無 Budget/Context 控制，Token、Quota、延遲容易失控。

## 3. V1 Goal — 2026-10-31

交付可日常使用的 `LOCAL_PERSONAL` V1 Release Candidate：
- Project / Workspace 可持續累積 Task、Run、Context、Artifact、Finding、Evidence、Decision。
- Discuss / Review / Validate 三個入口有真實端到端能力。
- Council 支援獨立分析、Cross Review、Synthesis。
- Codex + OpenCode 為深度 Runtime target。
- ChatGPT / Claude / Gemini Web 提供 Level 3A Assisted Automation + mandatory fallback。
- LM Studio / Ollama / Generic OpenAI-compatible 可作 Local AI Resource。
- Workflow / Evidence 可重複、可驗證、可追溯。
- Doctor / Compatibility / Migration / Backup / Restore 可支援長期個人維護。
- Shared Git / Memory / Skills 可讓 Codex、OpenCode、Antigravity安全接續開發。

## 4. V1 Scope Maturity

### CORE
Workspace、Task/Run、Discuss/Review/Validate、Council、Workflow Engine、Evidence、Artifact、Context、Event Ledger、Codex/OpenCode Runtime、Doctor/Conformance、Schema Migration/Backup。

### BASELINE
Web AI Level 3A、Local AI、Data Routing/Local-only、Assurance/Governance、Cost/Timeout/Concurrency Guard、Evaluation/Usage Metrics。

### COMPATIBILITY
其他 Runtime/Harness/Protocol 必須存在真實接入與驗證路徑，但成熟度可為 PREVIEW / EXPERIMENTAL。

### FUTURE
Dynamic Plugin Marketplace、Visual Workflow Designer、Personal Hub implementation、Cloud Sync、Multi-user、Enterprise IAM、完整 RAG/Knowledge Platform、Fully Autonomous Dev Team。

## 5. Personas

### P1 Personal Power User / Developer
跨 Codex、OpenCode、Local AI、Web AI 工作，需低 Token 成本、可靠接續與可驗證輸出。

### P2 IT / QA
需要 Code Review、Release Validation、Incident Analysis、Evidence、Compatibility Matrix。

### P3 PM / Project User
需要 Requirement / Change Impact Review，保留共識、分歧、風險與決策。

### P4 General / Executive User
透過 Web AI 做文件與方案比較，不必理解 Runtime Contract 細節。

## 6. Core User Journeys

### UJ-01 Discuss
Project → New Task → Discuss → 選 AI/Role → Parallel Analysis → Cross Review → Synthesis → Human Decision → History。

### UJ-02 Review
Artifact → Review Workflow → Independent Findings → Severity / Recommendation → Cross Review → Report。

### UJ-03 Validate
Candidate → Review → Validation Runner → Tool Evidence → Hard Gates → Verified Verdict → Evidence Bundle。

### UJ-04 Web Decision Review
Task → Context Package → Launch ChatGPT/Claude/Gemini → Auto Fill → User Confirm Send → Capture / Clipboard Fallback → Normalize → Consensus / Disagreement / Risks。

### UJ-05 Local-only
Confidential/Restricted Task → Local Only → Local Endpoint/Runtime → External Tool denied → Evidence records actual route。

## 7. Functional Requirements

### Workspace / Task / History
- Create/Open/Archive Project。
- Project default data classification。
- Stable Task ID / Run ID。
- Task/Run/Artifact/Finding/Evidence/Decision History。

### Council
- 2–4 roles baseline。
- Independent analysis、Cross Review、Synthesis。
- Max rounds、timeout、partial failure representation。

### Evidence
Types：`AI_OPINION` / `RUNTIME_EVIDENCE` / `TOOL_EVIDENCE` / `DOCUMENT_EVIDENCE` / `HUMAN_EVIDENCE`。

Tool FAIL 若被 Workflow 指定為 Hard Gate，不得被 AI 投票轉成 PASS。

### Runtime
Health / Readiness / Capability Discovery / Create Run / Submit / Stable ID / Status / Result / Error Normalization / Timeout / Cancel / Resume semantics / Evidence / Artifact / Cleanup / Compatibility。

Resume maturity：`NATIVE` / `MANAGED` / `NONE`。

### Web AI
Launch / Fill / User-confirmed Send / Capture / Association / Normalize。
Mandatory fallback：manual paste / clipboard import / launch-only handoff。

### Local AI
Health、model discovery、selection、streaming、structured output where supported、timeout、model identity、evidence metadata。

### Workflow
V1 nodes：`CONTEXT` / `AI_TASK` / `PARALLEL_AI` / `CROSS_REVIEW` / `TOOL` / `EVIDENCE_CHECK` / `HUMAN_GATE` / `SYNTHESIS` / limited `CONDITION`。

### Policy / Assurance
Classification：PUBLIC / INTERNAL / CONFIDENTIAL / RESTRICTED。
Decision：ALLOW / APPROVAL_REQUIRED / DENY。
Execution Mode：STANDARD / LOCAL_PREFERRED / LOCAL_ONLY。
Assurance：FLEXIBLE / STANDARD / VERIFIED。

### Doctor / Compatibility
Runtime version、Adapter version、Contract version、health、capabilities、certified matrix、maturity state。

### Backup / Migration
Schema version、backup-before-migration、workspace metadata/artifact export/restore。Secret value 不進 export。

## 8. Cross-cutting Requirements

- Compatibility & Migration
- Evaluation & Quality
- Cost / Resource Control
- Context Lifecycle
- Artifact Lifecycle
- UX Progressive Disclosure
- Token-aware Development/Runtime Context
- Secret / Egress / Permission separation

## 9. UX Principle

主要入口永遠保持：

```text
Project
  -> Discuss | Review | Validate
```

Runtime、Model、Policy、Doctor、Contract、Capability 僅在必要時逐層展開。

## 10. Metrics

不預先宣稱效益百分比，實際記錄：
- Task completion time
- manual operations / copy-paste count
- workflow completion rate
- runtime failure / fallback rate
- unique findings
- evidence coverage
- accepted/rejected finding
- human override
- report preparation time
- AI/runtime/model usage metadata where available

## 11. V1 Release Criteria

V1 不是 Demo：
- 核心垂直流程可重複使用。
- 主要資料可 Migration / Backup / Restore。
- Codex/OpenCode 有真實 Runtime Conformance evidence。
- Browser Companion failure 不得拖垮 Core。
- Sensitive Local-only failure 不得 silent cloud fallback。
- Verified PASS 必須滿足 Workflow 所需 deterministic hard gates。
- Feature Freeze 2026-10-18；V1 Acceptance Complete 2026-10-31。
