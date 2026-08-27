# PolyNexus AI Use Case Slide Outline v1.0 — Content Confidence Draft

目標：20 頁內的 internal planning version；8/25 內容 v1；官方簡章記載初審書審資料截止 `2026-08-31`，`2026-09-07` 僅為 repository 歷史規劃日期。官方首頁與簡章已確認 20 頁上限及 `50/30/20` 評分；首頁 Demo `5–10 分鐘` 與簡章初選 Demo `3 分鐘內或截圖`、效益說明表交件方式仍有 `OFFICIAL_CONFLICT / NEED_ACTION`。官方查證 target：<https://ai-challenge-2026.cybersoft.tw/>；簡章：<https://ai-challenge-2026.cybersoft.tw/assets/%E6%B4%BB%E5%8B%95%E7%B0%A1%E7%AB%A0.docx>；逐 claim 來源見 [`competition/G02_SOURCE_TO_CLAIM_MATRIX.md`](../competition/G02_SOURCE_TO_CLAIM_MATRIX.md)。

## Slide outline

1. Cover — PolyNexus：多 AI 協作、交叉審查與可信驗證工作平台（定位）
2. Why Now — AI 工具增加，但工作仍碎片化（problem framing）
3. Current Pain — Context 重複、結果難比較、AI Opinion 與 Evidence 混淆、交接遺失（problem framing）
4. Product Positioning — Model → Runtime → PolyNexus Coordination Plane → Human/Workflow（`IMPLEMENTED` bounded positioning）
5. Three Entrances — Discuss / Review / Validate（`IMPLEMENTED` contract；完整入口 UX 不宣稱完成）
6. Core Workspace — Project / Task / Context / Artifact / History（`IMPLEMENTED` bounded Core/API slice）
7. Council — Independent Analysis → Cross Review → Synthesis（`IMPLEMENTED` WP-12 bounded）
8. Evidence & Assurance — AI Opinion ≠ Evidence；Flexible / Standard / Verified（`IMPLEMENTED` WP-13 bounded；Human decision remains fail-closed）
9. Engineering Golden Path — Review → Cross Review → Test → Evidence → Verdict（`IMPLEMENTED` bounded workflow story）
10. Engineering Output Mock — Findings / Unit Test FAIL / Final FAIL / Evidence（`IMPLEMENTED` output model；visual/app journey QA pending）
11. Web AI Companion — ChatGPT / Claude / Gemini Level 3A + fallback（`IN_DEVELOPMENT`；drivers currently `DEGRADED`，不宣稱 supported）
12. Executive Decision Extension — Consensus / Disagreement / Risk / Missing Info（`PLANNED_V1`／extension framing；不宣稱完整產品流程）
13. Local AI — LM Studio / Ollama / Local-only / sensitive routing（`PLANNED_V1`；adapter/policy implementation evidence不足）
14. Architecture — Local-first Core + Contracts + Adapters + Workflow/Evidence（`IMPLEMENTED` bounded foundation；vendor integration separately gated）
15. Extensibility — Plugin-ready + Declarative Workflow，未來擴展不推倒重來（`IMPLEMENTED` static foundation；dynamic marketplace/install/signing 為 `FUTURE`）
16. Data & Governance — classification / egress / no silent cloud fallback（`PLANNED_V1` policy target；不得宣稱已完整 enforcement）
17. Development Plan — 8/17→8/31 initial-review document submission；9/1→9/24 initial review；9→10/31 V1（official brief schedule + roadmap/planning only；live form/announcement override `[待驗證]`）
18. Value Measurement — time, manual ops, unique findings, evidence coverage, fallback rate（`PLANNED_V1` measurement plan；無實測數字）
19. Enterprise / Department Evolution — Personal → Personal Hub → Department/Team（`FUTURE`／resource-dependent evolution）
20. Closing — From fragmented AI usage to a validated AI workflow platform（bounded claim + limitations）

## Internal scoring alignment

以下 mapping 與官方首頁／簡章評分指標一致；產品成熟度與效益數字仍依 matrix 的 bounded evidence：

- 企業價值 `50%`（official verified）：減少人工切換/整理、提高品質與可追溯、可跨部門複用；不填入未實測的 ROI。
- 落地成熟度 `30%`（official verified）：以 bounded Core evidence、明確 runtime/browser limitations 與 V1 roadmap 說明；不把 real Codex/OpenCode、Web/Local integration 寫成已完成。
- 創新性 `20%`（official verified）：AI collaboration + evidence-based validation + replaceable runtime/model + local-first governance positioning。

## Presentation guardrails

- 只使用 synthetic/public project context。
- 初審 proposal 與 AI Use Case deck 各維持在官方簡章的 `20 頁`上限；proposal 遵循 A4 直式／標楷體 12 級／1.0 倍行距／頁碼要求。
- `IMPLEMENTED` 必須搭配 bounded scope；`IN_DEVELOPMENT`、`PLANNED_V1`、`FUTURE` 不得在圖表中被視覺上省略。
- Browser E2E、Windows symlink containment、true concurrent HTTP 仍標示 `UNVERIFIED`／`SKIPPED`。
- 不展示或暗示 credentials、client data、production runtime success、測量結果或 official form completion；Demo 時長與效益說明表以 `OFFICIAL_CONFLICT` 標示，未經確認不選定。
- G03 才能在 Human 授權下進行 live official form requirement verification；G02 不登入、不填寫、不上傳、不送出。
