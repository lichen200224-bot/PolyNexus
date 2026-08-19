# PolyNexus SOP v1.1 狀態機

## 1. 狀態定義

| State | Owner | 意義 | 允許的下一步 |
| --- | --- | --- | --- |
| `TASK_CREATED` | Human / coordinator | Task 已建立但尚未交給 Writer。 | `WRITER_IN_PROGRESS` |
| `WRITER_IN_PROGRESS` | OpenCode | 正在實作或依 FIX PROMPT 修正。 | `READY_FOR_CODEX_ACCEPTANCE`、`BLOCKED` |
| `READY_FOR_CODEX_ACCEPTANCE` | OpenCode | 實作完成，已附完整 handoff 與驗收提示詞。 | `CODEX_ACCEPTANCE_IN_PROGRESS` |
| `CODEX_ACCEPTANCE_IN_PROGRESS` | Codex | Codex 正在讀取來源、diff 與 evidence。 | `CODEX_ACCEPTED`、`CODEX_REJECTED`、`NEED_ACTION` |
| `CODEX_REJECTED` | Codex | Codex 發現阻斷問題，已產生 FIX PROMPT。 | `FIX_REQUIRED` |
| `FIX_REQUIRED` | coordinator / target tool | 等待指定工具接收修正提示詞。 | `WRITER_IN_PROGRESS`、`ANTIGRAVITY_VERIFICATION_IN_PROGRESS` |
| `READY_FOR_REVERIFICATION` | fixer | 修正已完成，已附回驗提示詞。 | `CODEX_REVERIFICATION_IN_PROGRESS` |
| `CODEX_REVERIFICATION_IN_PROGRESS` | Codex | Codex 重新檢查原 criteria 與新增 issue。 | `CODEX_ACCEPTED`、`CODEX_REJECTED`、`NEED_ACTION` |
| `CODEX_ACCEPTED` | Codex | Codex 基礎驗收通過；可能仍需 Antigravity。 | `ANTIGRAVITY_VERIFICATION_REQUIRED`、`FINAL_ACCEPTANCE_IN_PROGRESS` |
| `ANTIGRAVITY_VERIFICATION_REQUIRED` | Codex | 判定需要視覺、互動或整合驗證。 | `ANTIGRAVITY_VERIFICATION_IN_PROGRESS` |
| `ANTIGRAVITY_VERIFICATION_IN_PROGRESS` | Antigravity | 正在執行明確指定的驗證。 | `ANTIGRAVITY_ACCEPTED`、`ANTIGRAVITY_REJECTED`、`NEED_ACTION` |
| `ANTIGRAVITY_REJECTED` | Antigravity | 驗證失敗，已產生 FIX PROMPT 與 Codex 回驗提示詞。 | `FIX_REQUIRED` |
| `ANTIGRAVITY_ACCEPTED` | Antigravity | 指定 Antigravity Gate 通過。 | `FINAL_ACCEPTANCE_IN_PROGRESS` |
| `FINAL_ACCEPTANCE_IN_PROGRESS` | Codex | 彙整所有 Gate 與保護檢查。 | `HUMAN_APPROVAL_REQUIRED`、`NEED_ACTION` |
| `HUMAN_APPROVAL_REQUIRED` | Human | 等待明確 `APPROVED_FOR_COMMIT`。 | `COMMIT_APPROVED`、`BLOCKED` |
| `COMMIT_APPROVED` | Human / git operator | 已取得明確批准，僅可依批准 scope Commit。 | `COMMITTED`、`BLOCKED` |
| `COMMITTED` | git operator | Commit 已完成；需回報 commit id 與 scope。 | `TASK_CLOSED` |
| `TASK_CLOSED` | coordinator | Task 完成並保留完整 audit trail。 | 無 |
| `NEED_ACTION` | Human / coordinator | 缺來源、權限、環境或決策，不能安全判定。 | 補資料後回到前一個工作 state |
| `BLOCKED` | Human / coordinator | 存在未解決衝突、重複失敗或不安全要求。 | 由 Human 決定是否重新規劃 |

## 2. 轉移規則

```text
TASK_CREATED
  -> WRITER_IN_PROGRESS
  -> READY_FOR_CODEX_ACCEPTANCE
  -> CODEX_ACCEPTANCE_IN_PROGRESS
     |-- PASS --> CODEX_ACCEPTED
     |-- FAIL --> CODEX_REJECTED -> FIX_REQUIRED
     |-- NEED_ACTION --> NEED_ACTION

CODEX_ACCEPTED
  |-- 不需要 Antigravity --> FINAL_ACCEPTANCE_IN_PROGRESS
  |-- 需要 Antigravity --> ANTIGRAVITY_VERIFICATION_REQUIRED
       -> ANTIGRAVITY_VERIFICATION_IN_PROGRESS
          |-- PASS --> ANTIGRAVITY_ACCEPTED -> FINAL_ACCEPTANCE_IN_PROGRESS
          |-- FAIL --> ANTIGRAVITY_REJECTED -> FIX_REQUIRED
          |-- NEED_ACTION --> NEED_ACTION

FIX_REQUIRED
  -> WRITER_IN_PROGRESS
  -> READY_FOR_REVERIFICATION
  -> CODEX_REVERIFICATION_IN_PROGRESS
     |-- PASS --> CODEX_ACCEPTED
     |-- FAIL --> CODEX_REJECTED -> FIX_REQUIRED
     |-- NEED_ACTION --> NEED_ACTION

FINAL_ACCEPTANCE_IN_PROGRESS
  -> HUMAN_APPROVAL_REQUIRED
  -> COMMIT_APPROVED  (only with explicit Human approval)
  -> COMMITTED
  -> TASK_CLOSED
```

## 3. 轉移 guard

| 轉移 | 必要條件 |
| --- | --- |
| `WRITER_IN_PROGRESS -> READY_FOR_CODEX_ACCEPTANCE` | 有 modified files、測試／evidence、known issues、ADR impact、scope deviation，以及 Codex prompt。 |
| `CODEX_* -> CODEX_REJECTED` | 有 issue 清單與至少一份完整 FIX PROMPT。 |
| `FIX_REQUIRED -> READY_FOR_REVERIFICATION` | 有修正結果、實際驗證與回驗 prompt。 |
| `CODEX_ACCEPTED -> ANTIGRAVITY_VERIFICATION_REQUIRED` | Codex 明確寫出需要驗證的風險與範圍。 |
| `FINAL_ACCEPTANCE_IN_PROGRESS -> HUMAN_APPROVAL_REQUIRED` | 所有必要 Gate PASS，保護區域檢查有證據，無未處理阻斷 issue。 |
| `HUMAN_APPROVAL_REQUIRED -> COMMIT_APPROVED` | Human 明確提供 `TASK_ID`、`APPROVED_FOR_COMMIT` 與 commit scope。 |
| 任一 state -> `NEED_ACTION` | 缺少必要來源、權限、測試環境或重大決策。 |
| 任一 state -> `BLOCKED` | scope 衝突、保護區域意外變更、無法安全回滾或反覆無進展。 |

## 4. attempt 與迴圈安全

- 每次 Codex Acceptance、Codex Reverification、Antigravity Verification 都要遞增 `attempt`。
- attempt 不是通過條件；它只用於追蹤同一 Task 的修正歷史。
- 若同一 issue 在三次以上 attempt 仍未改善，automation 應轉 `BLOCKED` 或 `NEED_ACTION`，交由 Human／ChatGPT 做規劃判斷；不得自動放寬標準。
- 任何修正都必須保留原 issue ID、修正前後證據與下一個回驗 prompt。
