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
4. 可安全 checkpoint 時 commit。
5. 下一工具先 Review handoff + diff，不重讀完整 repo。

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
