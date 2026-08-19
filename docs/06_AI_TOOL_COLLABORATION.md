# Codex + OpenCode + Antigravity Collaboration Plan

## 1. Roles

### Codex — Architecture / Core Owner
負責：Scope/ADR、Domain、Contracts、Workflow state machine、Evidence/Policy、hard bug、critical review。

### OpenCode — Implementation / Test Workhorse
負責：依已確認 Contract 做大量實作、fixtures、unit/conformance tests、templates、routine refactor、docs sync。

### Antigravity — Browser / E2E / Milestone Red Team
負責：Web Companion、UI journey、browser E2E、failure path、milestone independent verification。

## 2. Token-aware Escalation

1. Deterministic tools first。
2. Routine implementation → OpenCode。
3. Architecture/high-coupling/hard root cause → Codex。
4. Browser/E2E only when needed → Antigravity。
5. 三工具共同檢查只在 Milestone / RC。

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

每個 Agent 只取得：Current Handoff + relevant spec + relevant files + diff + failing test excerpt。
禁止三套工具依序做 full-repo analysis。

## 5. Ownership Rule

Architecture conflict 回 Codex/人員裁決；OpenCode / Antigravity 不得在驗證途中自行重寫核心 Contract。

最終產品／範圍決策由人決定；AI 建議不自動變更 Scope Baseline。

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
- **Human**：裁決 scope/ADR/產品取捨；Codex PASS 後確認 staged-file allowlist，才明確授權 commit 或 remote push。

涉及 browser 的任務採 `OpenCode implementation/test → Antigravity browser/E2E → Codex acceptance → Human approval`；不涉及 browser 的任務仍須在 handoff 明確記錄 Antigravity 是否 `NOT_REQUIRED`。

### 6.3 Result gates

- `PASS`：所有必要 current evidence 成功、沒有 BLOCKER/MAJOR、scope/ADR/protected areas 正確，且 handoff 與 working tree 一致。
- `FAIL`：存在 acceptance contract 違反、安全邊界問題、重大測試缺口或未授權 scope；必須回到 Writer 並附 `FIX_PROMPT`。
- `NEED_ACTION`：缺少必要授權、外部輸入或環境條件，無法安全推論；必須列明 blocker、待提供資料與未驗證項目。
