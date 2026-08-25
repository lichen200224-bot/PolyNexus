# Git Workflow for Shared AI Project Directory

## 1. Core Rule

Codex / OpenCode / Antigravity / Claude 可以共用同一個 project directory，但採「Sequential Tool Use + Single Active Writer」。不要讓多套工具同時修改同一 working tree。工具名稱本身不授予 Git 權限。

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
git rev-parse HEAD
git diff --name-status
git diff --cached --name-status
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

Claude 與後續接入工具適用相同限制。禁止以 `git add .`、`git add -A`、`git push --all`、`git reset --hard`、`git checkout -- .` 或 `git clean -fd` 取代 explicit target/allowlist。Remote rename/add、GitHub repository creation、branch protection 與 history rewrite 都是獨立 Human Gate；commit approval 不自動包含 push 或 remote approval。

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

### 8.1 Same-machine collaboration

主要 Windows workspace `D:\AI學習教材\PolyNexus` 是同一台電腦的共享 working repository。Codex、OpenCode、Antigravity、Claude 只能依 Single Active Writer 依序接續。

`D:\GitBackup\PolyNexus\_Backup.git` 的定位是 `LOCAL BACKUP / CHECKPOINT REMOTE`。必須先用 `git remote -v` 確認實際 remote name，不得猜測；它不提供正式跨電腦共享能力。

Local backup 更新也是 Git push：read-only 確認 remote 與 proposed branch/tag 後，只能輸出 `LOCAL_BACKUP_PUSH_READY / HUMAN_APPROVAL_REQUIRED`。Human 當輪批准後才可推送明確 checkpoint；不得把 local-backup approval 延伸為 GitHub push approval。

### 8.2 Cross-machine source of truth

正式跨機接續來源是：

```text
approved remote Git checkpoint
+ Git history
+ docs/11_PROJECT_STATE.md
+ docs/12_HANDOFF_CURRENT.md
+ docs/tasks/
+ .agents/skills/
```

Cross-machine handoff 只有在 approved checkpoint 已 push 到 Human-approved GitHub／remote Git，且 clean-clone verification 成功後才有效。Uncommitted local workspace、conversation history、AI memory 或 manually copied source tree 都不是有效跨機 handoff state。

另一台電腦／帳號的標準順序：

```text
clone / fetch
-> checkout approved branch/checkpoint
-> read AGENTS.md
-> read Project State
-> read Current Handoff
-> read Current Task
-> load canonical .agents/skills
-> verify clean/expected Git state
-> continue under Single Active Writer
```

### 8.3 GitHub boundary

GitHub 是 Development Collaboration Infrastructure，不是 PolyNexus Product Core dependency。`Communication Contract != GitHub`；未來改用 GitLab、self-hosted Git 或其他 remote Git，不得迫使 Core Contract 重做。

推薦長期 remote naming 是 `origin = GitHub`、`backup = local bare repository`，但只在 read-only precheck 後提出 plan。若現有 local backup 使用 `origin`，必須另經 Human approval 才可 rename/add remote；不得自行執行。

## 9. Checkpoint and GitHub Enablement Gates

### 9.1 Task checkpoint preparation

先重新執行並記錄 actual exit code：

```bash
git branch --show-current
git rev-parse HEAD
git status --short --branch
git diff --name-status
git diff --check
git diff --cached --name-status
```

直接比對 task doc、Project State、Current Handoff、acceptance report 與實際 changed/untracked files。只提出 `FILES_TO_STAGE`、`FILES_EXCLUDED` 與建議 commit message，不得 stage。證據不足時輸出 checkpoint not ready 並停止。

Human 明確批准 commit 後，才可逐檔 `git add <explicit approved files>`，再檢查 cached name-status/check/status。Staged surface 不一致即停止；commit 完成後重新確認 HEAD 與 working tree。Commit approval 不包含 push。

### 9.2 Governance checkpoint

Product checkpoint 與 Governance checkpoint 必須是可區分的 commits。Governance Writer 不得驗收自己的 patch；只有 independent acceptance 為 `VERIFIED_PASS` 且 Human 明確批准，才可 explicit stage/commit。不得 amend 已完成的 product checkpoint 來混入治理變更。

### 9.3 GitHub enablement precheck

Remote configuration 前只讀收集：

```bash
git remote -v
git branch -a
git tag
git log --oneline --decorate --graph -30
git status --short --branch
```

Working tree 不乾淨即 `GITHUB_ENABLEMENT_BLOCKED_BY_DIRTY_TREE`。GitHub repository 建議 Private 且建立空 repository，不預先產生 README、`.gitignore` 或 License。若 remote 已有不同 history，輸出 `REMOTE_HISTORY_RECONCILIATION_REQUIRED`；禁止 force push。

Remote design、GitHub URL、branches/tags proposed for push 必須先交 Human Gate。Remote configuration approval 不包含 push approval。

### 9.4 Controlled push

Human 再次批准後，只逐項 push approved branch/tag。禁止 `git push --all`；`git push origin --tags` 也必須先確認所有 tracked tags 都獲批准。每個 push 分別記錄 exact command、exit code 與 remote result。

### 9.5 Clean-clone round trip

`push success != cross-machine ready`。在 Human-approved、確認安全且與正式 workspace 分離的 verification directory 執行 clean clone；確認 remote、branch、clean status、HEAD、tags、必要治理檔與 applicable baseline validation。Verification clone 不得修改產品。

只有 clone 成功、approved checkpoint 相符、必要 repository governance files 存在、Git state clean 且 applicable validation 通過，才能宣告 `CROSS_MACHINE_CONTINUATION_READY`。否則輸出 `CROSS_MACHINE_CONTINUATION_NOT_READY` 與 Findings。
