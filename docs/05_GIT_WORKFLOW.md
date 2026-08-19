# Git Workflow for Shared AI Project Directory

## 1. Core Rule

Codex / OpenCode / Antigravity 可以共用同一個 project directory，但採「Sequential Tool Use + Single Active Writer」。不要讓三套工具同時修改同一 working tree。

## 2. Branch Model

- `main`：可驗收版本／release candidate。
- `develop`：整合分支。
- `feature/<scope>`：功能分支，例如 `feature/workflow-engine`。
- `fix/<issue>`：缺陷修正。
- `docs/<topic>`：純文件變更。

Branch 依功能命名，不依工具命名。

## 3. Session Start Checklist

```bash
git status --short --branch
git log -5 --oneline
```

確認：
- 正確 branch。
- working tree 是否有別的 Agent 留下的變更。
- `docs/12_HANDOFF_CURRENT.md` owner / task 是否一致。

若有不明未提交變更：停止寫入，不可自行 reset。

## 4. Commit Discipline

建議小而可回退的 commit：
- `feat(workflow): add fixed node parser`
- `test(runtime): add cancel cleanup conformance`
- `docs(sa): record context package boundary`

禁止把大範圍格式化、文件、功能、測試混成一個超大 commit。

## 5. AI Handoff

切換工具前：
1. run targeted tests。
2. update `HANDOFF_CURRENT.md`。
3. `git diff --stat` / `git status`。
4. 檢查 changed files，包含 untracked、protected areas、ADR impact、scope deviation、known limitations 與 unverified items。
5. 下一工具先 Review handoff + diff，不重讀完整 repo。

### 5.1 Role handoff actions

- **OpenCode → Antigravity**：僅於 UI/browser/E2E/milestone task 使用；OpenCode 必須提供 start command、route、fixture/test data、expected result、failure-path checklist、目前測試 evidence 與 `Do Not Change`。不涉及 browser 時，handoff 必須記錄 `ANTIGRAVITY_STATUS: NOT_REQUIRED` 及理由。
- **Antigravity → Codex**：提供實際 browser/environment、route、journey 結果、failure-path 結果、screenshot/video/artifact ref、blocker 與未驗證項目；不得宣稱未執行的 E2E 為 PASS。
- **OpenCode → Codex**：提供 implementation summary、完整 changed-files（含 untracked）、current tests + exit codes、scope/ADR/protected-area check 與下一步；Codex 接手後只讀 review。
- **Codex → Human**：只有 `PASS` 才能提出 Human approval；`FAIL` 必須附 issue evidence 與可貼回 OpenCode 的 `FIX_PROMPT`；`NEED_ACTION` 必須列出缺少的授權或外部條件。

### 5.2 Git authorization

OpenCode、Antigravity、Codex 預設不得自行 `git add`、commit、push、rebase、reset 或 force push。Human 必須在當前 task 明確授權後，才能依 verified staged-file allowlist 執行 Git 操作；歷史授權不自動延伸到新 task。

交接輸出至少要有：`RESULT`、`TASK_ID`、`ATTEMPT`、`BRANCH`、`WRITER`、`REVIEWER`、`ANTIGRAVITY_STATUS`、`NEXT_OWNER`、`CHANGED_FILES`、`TESTS`、`ADR_IMPACT`、`SCOPE_DEVIATION`、`KNOWN_LIMITATIONS`、`UNVERIFIED`、`NEXT_ACTION`、`NEXT_PROMPT_FOR_HUMAN` 與 `FIX_PROMPT`。

## 6. Rollback

優先：
- revert 單一 commit。
- checkout specific file from known good commit（需人工確認）。

避免：
- `git reset --hard`
- force push
- 未確認就 clean untracked files

## 7. Tags / Release

Milestone 建議 tag：
- `development-baseline-v1.0`
- `v0.2-core`
- `v0.3-integrations`
- `v1.0-rc1`
- `v1.0.0`

Tag 前必須有對應 Acceptance evidence。

## 8. Remote

初始 Repo 可先 local Git；決定公司允許的 remote 後再加。Secrets / local DB / artifact raw data 不得 push。
