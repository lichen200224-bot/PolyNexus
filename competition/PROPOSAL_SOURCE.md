# PolyNexus 初審提案計畫書內容來源 v0.3

> 正式 Word 版由本內容轉製；本版為 2026-08-27 的 content-confidence draft。官方首頁與其公開活動簡章已取得部分要求；官方簡章記載初審書審資料截止 2026-08-31，首頁與簡章對 Demo 時長及效益說明表交件方式仍有差異。repository 內部規劃曾記錄 2026-09-07，僅保留為歷史規劃，不是官方截止日。

## 提案名稱

PolyNexus：多 AI 協作、交叉審查與可信驗證工作平台

## 提案摘要

企業與個人在日常工作中同時使用多種 AI 與 runtime，但工具彼此孤立，使用者必須重複搬運脈絡、比較答案與整理結果；更大的問題是 AI 判斷常與真實測試、文件規則或人工核准混在一起，造成結果難以追溯、驗證與接續。PolyNexus 以 Local-first 為原則，提供 Project／Task／Run／Context Package／Artifact／History 的 bounded Workspace，以及 Council、Evidence、Finding、Decision 與 declarative Workflow 的協作與驗證基礎。當前可對外主張的是已接受的 Core slice：`Project → Review → Runtime boundary → Finding/Evidence → Result → History`。Codex/OpenCode vendor runtime、Web AI Level 3A、Local AI adapter、完整 routing policy、完整 V1 template breadth、完整 backup/restore 與 business outcome measurement 仍分別屬於 `IN_DEVELOPMENT` 或 `PLANNED_V1`；dynamic marketplace、multi-user/enterprise IAM、full RAG 與 autonomous team 屬於 `FUTURE`。提案不以未驗證的 AI opinion、歷史測試數字或內部 planning date 冒充 current official requirement。

## Content confidence status

完整來源—claim 對照見 [`G02_SOURCE_TO_CLAIM_MATRIX.md`](G02_SOURCE_TO_CLAIM_MATRIX.md)。目前 20 個產品 claim 的成熟度計數如下：

| Maturity | Count | Boundary |
|---|---:|---|
| `IMPLEMENTED` | 8 | bounded Core/workflow/gate/reference foundation；不等於完整 V1 或 production vendor integration |
| `IN_DEVELOPMENT` | 3 | Codex/OpenCode conformance、Web AI companion、明列的 browser/verification boundary |
| `PLANNED_V1` | 5 | Local AI、routing policy、template breadth、backup/restore、measurement |
| `FUTURE` | 4 | multi-user/enterprise IAM、dynamic marketplace、full RAG/autonomous team、trusted-human identity extension |

上述計數不包含官方要求 rows；官方首頁／簡章已確認初審時程基線、20 頁限制、50/30/20 評分、主要交件物與資料限制；現行表單欄位／檔案限制，以及首頁與簡章的 Demo／效益表差異仍標為 `[待驗證]` 或 `OFFICIAL_CONFLICT`。

## 2026-08-27 Architecture Freeze / factual boundary update

ADR-001～010 已確認；技術基線為 React/TypeScript/Vite + Python/FastAPI + SQLite/Filesystem + REST/WebSocket + Chrome MV3 Companion + YAML Workflow + SecretRef/OS-backed SecretStore。這些是架構／規格基線，不表示所有 component、vendor adapter、browser journey 或 V1 capability 已完成。WP-14/WP-15 runtime work 與 WP-16 仍依 `docs/11_PROJECT_STATE.md` 的 component gate 與 exclusion 狀態處理，不在本提案中合併成 production support claim。

## Official requirement verification

- Target homepage: <https://ai-challenge-2026.cybersoft.tw/>; check date `2026-08-27` (Asia/Taipei)。Node `fetch` retrieved HTTP `200`; H1 為 `2026 Cyber4.0 AI創新競賽`; 主辦單位為 `Cyber4.0 推動任務小組`。
- Official brief: <https://ai-challenge-2026.cybersoft.tw/assets/%E6%B4%BB%E5%8B%95%E7%B0%A1%E7%AB%A0.docx>; retrieved HTTP `200`; cover date `中華民國115年6月`。簡章記載初審書審資料 `2026.07.30–2026.08.31`、初選書審 `2026.09.01–2026.09.24`、結果通知 `2026.09.30`。
- Verified initial-review preparation: proposal plan total `20 頁` maximum；AI Use Case deck PDF/PPT `20 頁` maximum；proposal format is A4 portrait, 標楷體 12 級, 1.0 spacing, with page numbers。簡章要求問題／解法／技術／架構與資源／商業價值與效益及風險等內容。
- Verified scoring: 企業價值 `50%`、落地成熟度 `30%`、創新性 `20%`，與 [`G02_SOURCE_TO_CLAIM_MATRIX.md`](G02_SOURCE_TO_CLAIM_MATRIX.md) 一致。
- Official conflict requiring G03/Human resolution: homepage `繳交內容` says Demo `5–10 分鐘` and separately lists `效益說明表`; official brief initial-review section says Demo `3 分鐘內`或截圖，且初審清單未單列效益說明表。此版不選邊、不把差異當成已解決。
- Form link exposed by the homepage: <https://forms.cloud.microsoft/r/e6PyFrYNR9>。簡章附件可確認部分欄位語意（提案名稱、最多 5 人、代表人部門／員編／姓名、應用領域、300–500 字摘要、同意／正確性／簽署日期），但實際表單欄位、檔案大小／命名及上傳規則仍 `[待驗證]`。
- `2026-09-07` is an internal historical planning record only and must not be presented as the official deadline。未登入、填寫、上傳、送出或提交。

## Source rules

1. AI Opinion 不等於 Verified Evidence；deterministic tool/test evidence、document rule 或 Human decision 必須保留其來源與狀態。
2. 只有 `ACCEPTED`／`CHECKPOINTED` 才計入 project progress；`IMPLEMENTED_PENDING_INDEPENDENT_REVIEW`、`READY_FOR_CODEX_REVIEW`、`SKIPPED`、`UNVERIFIED` 與環境 blocker 不得改寫成已完成。
3. Proposal 只使用 synthetic／public project context，不使用客戶交易、個資、商業資料或交付中客戶專案。
4. 每個對外 claim 必須回到 matrix 的 repository evidence 與 limitation；不能以這份 source document 自行授予 Human acceptance。

## 相關來源

- [`docs/00_SCOPE_BASELINE.md`](../docs/00_SCOPE_BASELINE.md)
- [`docs/01_PRD.md`](../docs/01_PRD.md)
- [`docs/11_PROJECT_STATE.md`](../docs/11_PROJECT_STATE.md)
- [`docs/13_COMPETITION_SUBMISSION_PLAN.md`](../docs/13_COMPETITION_SUBMISSION_PLAN.md)
- [`docs/14_COMPETITION_SLIDE_OUTLINE.md`](../docs/14_COMPETITION_SLIDE_OUTLINE.md)
- [`G02_SOURCE_TO_CLAIM_MATRIX.md`](G02_SOURCE_TO_CLAIM_MATRIX.md)
