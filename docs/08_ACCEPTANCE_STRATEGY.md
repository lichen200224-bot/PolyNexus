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

## 9. Governance Change Acceptance

Governance／Contract／Documentation patch 採以下 progression：

```text
Human-approved scope
-> Single Active Writer patch
-> deterministic diff/scope checks
-> independent review (Writer != Reviewer)
-> VERIFIED_PASS / NEED_FIX / FAIL
-> Human checkpoint approval
-> explicit staged-file allowlist
-> commit
```

Reviewer 必須比對 Human-approved scope、完整 diff、protected areas、ADR impact、duplicate abstraction 與 current Git state。至少執行 `git status --short --branch`、`git diff --name-status`、`git diff --check`、`git diff --cached --name-status`，並記錄 actual exit code。適用時使用既有 docs/baseline validator，不為本 task 新增 validator。

若 Writer 是 Codex，同一 Codex context 不得自我驗收。`NEED_FIX`／`FAIL` 必須提供 Finding、severity、file/line、evidence、impact、fix owner、完整 FIX_PROMPT 與 re-acceptance prompt。只有 independent `VERIFIED_PASS` 後，才可輸出 `GOVERNANCE_CHECKPOINT_READY / HUMAN_APPROVAL_REQUIRED`；Reviewer 不得自行 commit 或 push。

## 10. Automation-ready / Human Trust

`Automation-ready != fully automated trusted-human approval`。D11 Option C 下，未經 approved identity boundary 驗證的 Human approve/reject 維持 `HUMAN_DECISION / NEED_ACTION`，不得被轉成 machine-verifiable PASS/FAIL 或無人化推進。Trusted Human authentication／attestation 是 deferred architecture，不是目前 V1.1 governance alignment blocker。

## 11. Cross-machine Readiness Acceptance

Push 成功本身不是跨機驗收。只有以下全部成立，才能宣告 `CROSS_MACHINE_CONTINUATION_READY`：

- approved remote Git checkpoint 已存在。
- clean clone 成功且 checkout 到 approved branch/checkpoint。
- cloned HEAD 與批准 SHA 相符。
- `AGENTS.md`、Project State、Current Handoff、task docs、canonical skills 與必要 product directories 存在。
- clone 的 Git state clean/expected。
- applicable deterministic baseline validation 通過並記錄 exit code。

否則必須輸出 `CROSS_MACHINE_CONTINUATION_NOT_READY` 與 Findings。若 readiness 在 Governance checkpoint 後才確定，Project State／Handoff 更新必須是獨立 `CROSS-MACHINE-STATE-UPDATE`，不得 amend 或偷偷混入既有 Governance commit。

## 12. Consolidation Final Report

`POLYNEXUS-V1.1-CONSOLIDATION` 只能報告實際完成且已獲 Human 授權的階段。最終報告至少列出：

- Repository branch、HEAD、clean/dirty/staged state。
- WP-13 checkpoint SHA 與 acceptance evidence reference。
- Governance checkpoint SHA 與 independent acceptance evidence；若尚未 commit，明確標示 pending。
- Local backup 的實際 remote name、checkpoint 與 push status。
- GitHub 的實際 remote name、pushed branches/tags、每個 push command/result/exit code。
- Clean-clone verification path、cloned commit、branch、Git state、validation commands/results/exit codes。
- Cross-machine verdict：只能是 `CROSS_MACHINE_CONTINUATION_READY` 或 `CROSS_MACHINE_CONTINUATION_NOT_READY`。
- Deferred architecture／P2 未提前實作確認。
- 由 Repository current state 決定的 next product task；不得依舊 conversation 猜測 WP/FVS 編號。

Routing footer 必須包含 `TASK_ID`、actual `CURRENT_STATUS`、deterministic `RESULT`、`NEXT_ACTION`、`NEXT_OWNER`、complete `NEXT_PROMPT`、`BLOCKERS` 與 `HUMAN_ACTION_REQUIRED`。未執行、未批准或 blocked 的 phase 不得寫成完成。
