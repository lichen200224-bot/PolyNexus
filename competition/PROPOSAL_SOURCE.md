# PolyNexus 初審提案計畫書內容來源 v0.2

> 正式 Word 版由本內容轉製；最新通知截止日 2026-09-07。

## 提案名稱
PolyNexus：多 AI 協作、交叉審查與可信驗證工作平台

## 提案摘要
企業與個人在日常工作中已同時使用 ChatGPT、Claude、Gemini、Codex、OpenCode 與 Local AI，但各工具彼此孤立，使用者必須重複搬運脈絡、人工比較答案與整理結果；更大的問題是 AI 的判斷常與真實測試、文件規則或人工核准混在一起，造成結果難以追溯、驗證與接續。PolyNexus 提出 Local-first 的多 AI 協作與驗證 Workspace，透過 Project / Task / Workflow 統一 Context、Artifact、Council、Evidence 與 Decision，讓不同 AI 先獨立分析、再交叉審查，重要結果再由真實工具或規則產生 Evidence。第一階段提供 Discuss、Review、Validate 三種工作入口，整合 Codex、OpenCode、Web AI 與 Local AI，並以可替換的 Adapter、Declarative Workflow 與 Data Routing Policy 建立可持續演進的個人 AI 工作平台。初期以工程 Review / Release Validation 為主要落地場景，再延伸至需求、SOP、文件與主管方案比較，目標降低重複操作與整理成本，同時提升品質、可驗證性與跨部門複用能力。


## 2026-08-17 Architecture Freeze Update
ADR-001～010 已確認；技術基線為 React/TypeScript/Vite + Python/FastAPI + SQLite/Filesystem + REST/WebSocket + Chrome MV3 Companion + YAML Workflow + SecretRef/OS-backed SecretStore。正式提案 Draft v0.2 已同步更新，但不得將 scaffold 宣稱為已完成 V1 功能。
