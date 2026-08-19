# PolyNexus V1 Acceptance Strategy

## 1. Principle

AI Opinion ≠ Evidence。PASS 只認當下真實驗證結果，禁止使用舊 log 或 AI 自述替代。

## 2. Acceptance Layers

### Unit
Domain logic、parser、policy、normalization。

### Contract / Conformance
Runtime/Endpoint/Driver contract semantics。

### Integration
Core ↔ adapter、storage、workflow、browser companion。

### E2E
4 條 Golden Workflow 深度驗收。

### Release
Migration、Backup/Restore、security boundary、packaging、known limitations。

## 3. Four Golden Acceptance Flows

1. Discuss / Council
2. Code / Artifact Review
3. Release Validation
4. Web AI Decision Review

其餘 5 templates 需可運作與 template validation，但不要求同等測試矩陣深度。

## 4. Runtime Conformance Critical Checks

- health/readiness
- stable run ID
- status terminal state
- timeout
- cancel actually stops
- child/tools cleaned
- result/error normalized
- evidence envelope generated
- artifacts traceable
- version/compatibility recorded

Resume 允許 NATIVE / MANAGED / NOT_AVAILABLE，但必須如實 capability 宣告。

## 5. Failure Isolation

任一 Adapter/Web Driver crash 不得使 Core crash；Council 可顯示 partial result / retry。

## 6. Policy Tests

- Restricted / Local-only 不可 silent cloud fallback。
- Highest Classification Wins。
- external egress 前 policy check。
- exception requires audit actor/reason/time。

## 7. Migration Tests

每次 schema migration：backup gate → migrate → verify old data → rollback/restore path documented。

## 8. Evidence Output

每個 Acceptance run 至少記：command、timestamp、exit code、test name/summary、version、artifact ref。長 stdout 放 artifact store，不塞進主報告。

### 8.1 Handoff evidence contract

每次交接的 evidence 必須能被下一工具重跑或定位，至少包含：

- `TASK_ID`、`ATTEMPT`、branch、writer/reviewer、`ANTIGRAVITY_STATUS` 與 next owner。
- changed files（包含 untracked）、protected areas、ADR impact、scope deviation、known limitations 與 unverified items。
- 每個必要 command 的完整文字、實際結果摘要與 actual exit code；歷史結果只能標為 historical，不得當作 current PASS。
- Browser/E2E 需補 route、fixture、browser/environment、journey result、failure-path result 與 screenshot/video/artifact ref。手動驗證沒有 process exit code 時，必須明確寫 `exit_code: N/A`，不可虛構。
- 被 `SKIPPED`、環境限制或外部依賴阻擋的檢查，必須標示原因、影響範圍與重新執行方式。

### 8.2 Result conditions

- `PASS` 只在本輪必要 evidence 全部符合 acceptance criteria、actual exit codes 正確、無 BLOCKER/MAJOR、scope 未越界且 handoff 與 working tree 一致時成立。
- `FAIL` 必須列出 severity、檔案/行號、證據、影響與修正方向，並附可直接交給 OpenCode 的 `FIX_PROMPT`。`FIX_PROMPT` 必須包含要修改的檔案、測試案例、完整驗證命令與預期 exit code。
- `NEED_ACTION` 只用於缺少授權、輸入或環境條件；不得將未驗證項目、工具失敗或 AI 意見轉成 PASS。
