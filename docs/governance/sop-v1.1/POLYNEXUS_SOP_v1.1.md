# PolyNexus 多工具開發／驗收 SOP v1.1

版本：`1.1.0`
狀態：可套用的治理層
適用工具：`OpenCode`、`Codex`、`Antigravity`、`Human`
主要目標：讓每一個 Task 都能以明確狀態、證據、修正提示詞與回驗提示詞形成可自動化的閉環。

## 1. 範圍與不變事項

本 SOP 管理的是「工作如何被交接、驗收、修正、回驗與批准」，不是產品架構或產品實作本身。

本版本明確保護：

- 已完成的 FVS-01 產品實作、測試、設定、資料與相關檔案。
- 已完成的 FVS-02 產品實作、測試、設定、資料與相關檔案。
- `ADR-001` 至 `ADR-010` 的既有檔案與內容。
- 既有 API、資料模型、路由、狀態管理、依賴、CI/CD、secrets 與 deployment 設定，除非某個 Task 明確授權且經過獨立驗收。

本套件只新增治理檔案與只讀驗證工具；不以治理更新為理由修改上述範圍。

## 2. 角色與責任

| 角色 | 主要責任 | 不可做的事 |
| --- | --- | --- |
| Human | 定義需求邊界；在 `HUMAN_APPROVAL_REQUIRED` 時決定是否允許 Commit。 | 不可把模糊的「看起來可以」當成正式 approval。 |
| OpenCode | 依 Task 實作或修正產品；保存檔案清單、測試與 deterministic evidence；產生 Codex 驗收提示詞。 | 不可自行宣告通過獨立驗收；不可省略 known issues 或 scope deviation。 |
| Codex | 讀取需求、handoff、diff、ADR 與證據，執行獨立 Acceptance；失敗時產生可直接交給工具的 FIX PROMPT；通過後產生下一個必要 Gate 的提示詞。 | Acceptance 階段禁止修改產品 source；不可只寫「有問題」而不提供可執行修正提示詞。 |
| Antigravity | 只在 Codex 判定需要時，執行 UI、互動、視覺、整合或其他明確指定的驗證；失敗時產生修正與回驗提示詞。 | 不可把未驗證的畫面或主觀感受標記為 PASS；不可跳過 Codex 的需求與證據。 |

## 3. 來源優先順序

每次驗收至少要讀取下列來源；若某來源不存在，必須在報告中標記 `MISSING_SOURCE`，不得自行補寫內容：

1. `docs/tasks/<TASK_ID>.md`
2. `docs/12_HANDOFF_CURRENT.md`
3. 目前 Git diff 與工作樹狀態
4. Task 指定的 deterministic evidence、測試輸出與驗證記錄
5. Task 引用的 ADR；若沒有引用，不得自行推斷要修改哪個 ADR
6. 本治理層文件與該 Task 已固定的驗收標準

當來源互相衝突時，先停在 `NEED_ACTION`，由 Human 或上層 ChatGPT 決定，不得由執行工具自行擴大範圍。

## 4. 標準工作流程

### 4.1 Task 建立與實作

Task 必須有唯一 `TASK_ID`、目標、非目標、驗收標準、受影響範圍、禁止觸碰範圍與預期 evidence。OpenCode 以 `TASK_HANDOFF_TEMPLATE.md` 接收工作。

OpenCode 完成後必須回報：

- modified files
- implementation summary
- tests、命令與 exit code
- deterministic evidence 的位置與結果
- known issues
- ADR impact（`NONE` 也要明寫）
- scope deviation（`NONE` 也要明寫）
- `RESULT: READY_FOR_CODEX_ACCEPTANCE`
- `NEXT_ACTION: CODEX_ACCEPTANCE`
- `NEXT_PROMPT_FOR_CODEX: <可直接複製的完整提示詞>`

### 4.2 Codex 獨立驗收

Codex 必須在獨立 reviewer 模式下執行：

- 對照 Task、handoff、diff、測試與 deterministic evidence。
- 檢查既有行為、輸入輸出、錯誤處理與相容性是否被保留。
- 檢查是否越過 Task scope 或保護範圍。
- 不得修改產品 source；若要修正，應輸出 `FIX_PROMPT` 交給適當工具。
- 每個 FAIL 都要有 issue ID、嚴重度、證據、根因（若可判定）、目標工具、修正範圍與重新驗收條件。

Codex 的結果只能是：

- `PASS`：所有必要驗收標準都有證據支持。
- `FAIL`：至少一個阻斷問題未解決，並附完整 FIX PROMPT。
- `NEED_ACTION`：來源、環境或權限不足，無法安全判定，並附需要補齊的資料或決策。

### 4.3 失敗修正閉環

若 Codex 回報 `FAIL` 或 `NEED_ACTION`：

1. Codex 產生一份或多份可直接貼給 OpenCode、Codex（僅限獲授權的修正工作）或 Antigravity 的 `FIX_PROMPT`。
2. 目標工具只能依提示詞指定的 scope 修正；若發現需求衝突或需要更大架構變更，回報 `BLOCKED`，不可自行擴張。
3. 修正工具完成後，除了變更摘要與驗證結果，必須回覆 `NEXT_PROMPT_FOR_CODEX_REVERIFICATION`。
4. Codex 使用原始 Acceptance criteria 加上本次修正 issue 重新驗收，不能只看修正工具的自我宣告。
5. 若仍失敗，建立新的 attempt 並重複本流程；不可將同一個未解決 issue 改名後當成新通過。

### 4.4 Antigravity Gate

Codex 只有在驗收標準包含 UI/visual/interaction/integration，或 deterministic evidence 無法安全涵蓋該風險時，才輸出 `ANTIGRAVITY_VERIFICATION_REQUIRED`。

Antigravity 必須收到明確的驗證範圍、預期行為、測試資料、畫面／互動證據格式與停止條件。結果：

- `PASS`：所有指定視覺或互動條件都有證據。
- `FAIL`：產生交給 OpenCode 或指定修正工具的 FIX PROMPT，以及交回 Codex 的回驗提示詞。
- `NEED_ACTION`：環境、瀏覽器、測試資料或權限不足，列出缺口，不可猜測。

Antigravity 的 PASS 不是最終批准；仍需回到 Codex Final Acceptance。

### 4.5 Codex Final Acceptance

必要的 Codex 與 Antigravity Gate 都通過後，Codex 產生 `Final Acceptance Report`，至少包含：

- Task ID、commit base、驗收 attempt
- 實際檢查的檔案與命令
- 每一項 acceptance criterion 的 PASS 證據
- FVS-01/FVS-02 與 ADR-001–010 保護檢查結果
- 未驗證項目與殘餘風險
- `RESULT: READY_FOR_HUMAN_APPROVAL`
- `NEXT_ACTION: HUMAN_APPROVAL_REQUIRED`
- `NEXT_PROMPT_FOR_HUMAN`：清楚列出批准範圍與預期 commit scope

### 4.6 Human approval 與 Commit

只有 Human 明確回覆包含以下資訊，才可進入 Commit：

- 指定 `TASK_ID`
- 明確寫出 `APPROVED_FOR_COMMIT`
- 指定允許的 commit scope，或明確同意 Final Acceptance Report 的 scope
- 若有例外，逐項列出例外與到期／後續處理方式

若沒有明確 approval，狀態保持 `HUMAN_APPROVAL_REQUIRED`。任何工具都不得因「驗收通過」而自動 Commit、Push、建立 PR 或修改 Git history。

## 5. 三段輸出介面契約

每個工具的每次完成回覆都必須可被 parser 讀取，且至少有：

```text
RESULT: <狀態結果>
NEXT_ACTION: <下一個狀態或動作>
NEXT_PROMPT: <可直接交給下一個角色的完整提示詞>
```

推薦同時提供機器可讀欄位：`task_id`、`state`、`actor`、`attempt`、`modified_files`、`evidence`、`issues`、`protected_areas_check`、`next_prompt`。

`NEXT_PROMPT` 不得只寫「請驗收」或「請修正」；必須包含 Task ID、來源路徑、具體範圍、驗收／修正條件、禁止事項與預期輸出格式。

## 6. 修正提示詞最低要求

每份 `FIX_PROMPT` 必須指定：

1. 目標工具與角色。
2. Task ID、目前 state 與 attempt。
3. 失敗 issue ID 與嚴重度。
4. 可觀察證據與重現方式。
5. 允許修改的檔案／模組。
6. 明確禁止修改的檔案／模組，包括 FVS-01、FVS-02 與 ADR-001–010。
7. 完成條件與測試命令。
8. 修正後必須輸出的 `NEXT_PROMPT_FOR_CODEX_REVERIFICATION`。
9. 若無法安全修正時要回報 `BLOCKED`，不可靜默 fallback。

## 7. 自動化不變量

下列規則可直接轉成 automation guard：

- 沒有 `NEXT_PROMPT` 不得自動轉移到下一個角色。
- `FAIL` 沒有 `FIX_PROMPT` 不得進入修正工作。
- 修正完成沒有 `NEXT_PROMPT_FOR_CODEX_REVERIFICATION` 不得回驗。
- 任一必要 Gate 未通過，不得進入 `READY_FOR_HUMAN_APPROVAL`。
- 沒有 Human `APPROVED_FOR_COMMIT`，不得執行 Commit。
- `source_checkout_verified=false` 時，套件交付只能聲明「新增檔案已驗證」，不得聲明已檢查目標 repo 的既有產品檔案。
- 若工具發現 scope、權限、來源或架構衝突，狀態為 `BLOCKED` 或 `NEED_ACTION`，不是 PASS。

## 8. 完成定義

一個 Task 只有在下列條件全部成立時，才可交給 Human 決定 Commit：

- OpenCode 已提供完整 handoff 與 Codex acceptance prompt。
- Codex 已對每項 acceptance criterion 產生 evidence-backed 結果。
- 所有 FAIL/NEED_ACTION 都已修正並回驗，或已由 Human 明確接受例外。
- 必要的 Antigravity Gate 已通過。
- Codex Final Acceptance Report 已完成。
- 受保護區域沒有非授權 diff。
- 狀態是 `HUMAN_APPROVAL_REQUIRED`，而不是 `COMMITTED`。

本 SOP 不授權任何自動化流程替 Human 做最後的產品責任決策。
