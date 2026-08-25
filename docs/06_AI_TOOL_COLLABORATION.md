# Codex + OpenCode + Antigravity + Claude Collaboration Plan

## 1. Roles

### Codex — Architecture / Core Owner
負責：Scope/ADR、Domain、Contracts、Workflow state machine、Evidence/Policy、hard bug、critical review。

### OpenCode — Implementation / Test Workhorse
負責：依已確認 Contract 做大量實作、fixtures、unit/conformance tests、templates、routine refactor、docs sync。

### Antigravity — Browser / E2E / Milestone Red Team
負責：Web Companion、UI journey、browser E2E、failure path、milestone independent verification。

### Claude — On-demand Bounded Collaborator
依 task 明確指派執行文件整理、bounded analysis 或 second opinion。Claude 不因工具名稱自動取得 Writer、Reviewer、acceptance 或 Git 權限；實際角色仍以 current task/handoff 為準。

## 2. Token-aware Escalation

1. Deterministic tools first。
2. Routine implementation → OpenCode。
3. Architecture/high-coupling/hard root cause → Codex。
4. Browser/E2E only when needed → Antigravity。
5. Claude 只在明確分派且不重複既有分析時使用。
6. 多工具共同檢查只在 Milestone / RC 或 Human 明確要求時使用。

## 3. Task Pattern

### Core architecture task
Codex Design → Codex/assigned writer Implement → OpenCode targeted tests/review → deterministic evidence。

### Routine feature
OpenCode Implement + Test → Codex diff-only review if high impact。

### Browser feature
Codex defines boundary → OpenCode driver/support code → Antigravity E2E。

### RC
Codex critical review + OpenCode regression + Antigravity user journey → deterministic acceptance。

## 4. Context Budget

每個 Agent 只取得：`AGENTS.md` + Current Project State + Current Handoff + task doc + relevant spec/files + diff + failing test excerpt。預設直接相關規格／程式檔為 1–3 份；需要擴讀時必須由 diff、call chain、failure 或 acceptance criteria 提供理由。

- Writer：contract-first，載入直接修改面與 targeted tests，不預讀整個 repository。
- Reviewer：diff-first，先看 changed files、acceptance criteria、current evidence，再按風險擴讀。
- Browser verifier：只載入 route、fixture、expected result、failure path 與啟動方式，不載入無關 Core internals。
- 第二意見／文件整理：使用 references + current delta，不重製完整背景或聊天紀錄。
- 同一 task 內未變更的大型文件不重複全文載入；以 path、section、symbol、commit、artifact path/hash 引用。
- 長 log 先機器過濾，只傳 exact command、actual exit code、summary、failure names 與必要錯誤片段。
- 禁止 Codex、OpenCode、Antigravity、Claude 依序重做相同 full-repo analysis、完整測試或完整方案。切換工具本身不是重跑 deterministic evidence 的理由。

Token budget 是成本控制，不是 evidence waiver。不得因 summarization、token reduction、context optimization、handoff compression 或 memory compression 遺失或弱化 Acceptance Criteria、deterministic Evidence、Findings、ADR、Policy、Human Decision、verification command、actual exit code，或 acceptance 所依賴的 deterministic result。

## 5. Ownership Rule

Architecture conflict 回 Codex/人員裁決；OpenCode / Antigravity 不得在驗證途中自行重寫核心 Contract。

最終產品／範圍決策由人決定；AI 建議不自動變更 Scope Baseline。

Single Active Writer 以實際 task/handoff 為準；實際 Writer 不得擔任同一 patch 的 independent Reviewer。若 Codex 實際寫入 Governance patch，必須交給另一個獨立 reviewer/context 驗收，不得自我簽署 `VERIFIED_PASS`。

### 5.1 One-Hop Routing Guard

`NEXT_PROMPT != delegation permission`。收到 NEXT_PROMPT 不代表 Agent 可以 recursive delegation、自動啟動另一 Runtime 或建立 delegation chain。

每次跨 Runtime／工具 delegation 都必須重新產生正式 Routing Decision，至少包含：

- `NEXT_ACTION`
- `NEXT_OWNER`
- `NEXT_PROMPT`
- scope / out-of-scope
- allowed / forbidden actions
- acceptance / stop condition

Routing Decision 是治理紀錄，不新增 `RoutingEnvelope` Domain。未獲新 routing decision 的 Agent 必須停止於 handoff，不得再委派。

### 5.2 Communication Views, not Second Domains

TaskPacket／ResultPacket 只作 transport-independent communication mapping：Task view 對應既有 task goal/context/scope/acceptance/stop/return routing；Result view 對應既有 status/summary/changes/evidence/verification/findings/risks/unresolved/next routing。它們不得成為第二套 persisted Task/Result Domain，也不得複製 Evidence、Artifact、ContextPackage 或 Handoff ledger。

`Communication Contract First. Transport Second.` Manual copy、shared file、Git、CLI、REST、MCP、A2A 只承載相同 communication semantics。Provider/Model Gateway 與 PolyNexus Coordination Plane 是不同責任；optional gateway integration 不得把 provider routing 寫死進 Core。

## 6. Handoff Contract

### 6.1 Every handoff must include

每次 OpenCode、Antigravity、Codex 或 Human 交接都必須提供目前 task delta，不貼完整聊天紀錄或完整 repository。固定欄位如下：

- `RESULT`：`READY_FOR_CODEX_REVIEW`、`PASS`、`FAIL` 或 `NEED_ACTION`。
- `TASK_ID`、`ATTEMPT`、`TASK_DOC`、`HANDOFF_DOC`、`BRANCH`、`WRITER`、`REVIEWER`、`ANTIGRAVITY_STATUS`、`NEXT_OWNER`。
- `Goal`、`Completed`、`Changed files`（new/modified/deleted/untracked 與原因）。
- `Protected Areas Check`：FVS、ADR、API、dependency、secret/config 與其他禁止觸碰區域。
- `Tests`：完整 command、實際 output 摘要、actual exit code、是否為 current run。
- `ADR_IMPACT`、`SCOPE_DEVIATION`、`KNOWN_LIMITATIONS`、`UNVERIFIED`。
- `NEXT_ACTION`、下一工具的 exact prompt，以及 `Do Not Change`。

Handoff 不得包含 secret value、token、credential 或不可公開的原始資料；只可描述環境變數名稱或 operational hint。

### 6.2 Role-specific actions

- **OpenCode**：先讀取 handoff/spec/ADR 與目前 status，依 scope 實作並新增或更新測試；完成後更新 `docs/12_HANDOFF_CURRENT.md`，回報 `READY_FOR_CODEX_REVIEW`。不得自行 commit、push 或把失敗驗證改寫成 PASS。
- **Antigravity**：只在 Web/UI/browser/E2E/milestone 需要時接手；執行指定 route、fixture、user journey、failure path，回報 browser/environment、實際結果、screenshot/video/artifact ref 與 blocker。若不適用，回報 `ANTIGRAVITY_STATUS: NOT_REQUIRED` 及理由。不得在驗證途中修改 Core contract 或與 OpenCode 同時寫入。
- **Codex**：讀取 handoff + diff + 相關檔案，獨立重跑必要 deterministic evidence，保持只讀並輸出 acceptance result。`FAIL` 必須提供 severity、檔案/行號、可重現證據與包含測試步驟的 `FIX_PROMPT`。
- **Claude**：只執行 task 明確指定的 bounded scope；沿用相同 context budget、evidence integrity 與 Single Active Writer 規則。若未被指定為 Writer 或 Reviewer，只能提供 analysis/second opinion，不得修改檔案或執行 Git write。
- **Human**：裁決 scope/ADR/產品取捨；Codex PASS 後確認 staged-file allowlist，才明確授權 commit 或 remote push。

涉及 browser 的任務採 `OpenCode implementation/test → Antigravity browser/E2E → Codex acceptance → Human approval`；不涉及 browser 的任務仍須在 handoff 明確記錄 Antigravity 是否 `NOT_REQUIRED`。

### 6.3 Result gates

- `PASS`：所有必要 current evidence 成功、沒有 BLOCKER/MAJOR、scope/ADR/protected areas 正確，且 handoff 與 working tree 一致。
- `FAIL`：存在 acceptance contract 違反、安全邊界問題、重大測試缺口或未授權 scope；必須回到 Writer 並附 `FIX_PROMPT`。
- `NEED_ACTION`：缺少必要授權、外部輸入或環境條件，無法安全推論；必須列明 blocker、待提供資料與未驗證項目。
