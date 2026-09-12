# PolyNexus Agent Instructions

本檔是 Codex / OpenCode / Antigravity / Claude 與後續 AI 工具的短版永久規則。完整規格採 Need-to-know 載入。

## 0. Portable Workspace

Repository 可位於任意磁碟、目錄或支援的 OS 路徑。任何 tracked contract 都不得把 `D:\AI學習教材\PolyNexus` 或其他本機絕對路徑當成專案身份。

Repo root 一律以 `git rev-parse --show-toplevel` 發現。跨機身份是 **canonical remote + exact SHA + task/branch**。`.flowgov.local.toml`（若存在）僅為 gitignored machine-local preference，非 Source of Truth。

## 1. Source of Truth

優先順序：
1. Human explicit current decision / approved Architecture Gate
2. exact Git checkpoint + canonical remote truth
3. `docs/36_POLYNEXUS_CROSS_MACHINE_GOVERNANCE.md`
4. `docs/37_CURRENT_ROUTING_INDEX.md`
5. `docs/00_SCOPE_BASELINE.md`
6. `docs/10_DECISION_LOG.md` / accepted ADRs
7. current task document under `docs/tasks/`
8. `docs/11_PROJECT_STATE.md` / `docs/12_HANDOFF_CURRENT.md`（未同步的舊段落只算歷史）
9. actual source + current deterministic evidence

Conversation history、AI memory、manual ZIP/source copy、local filesystem path、local remote-tracking cache 都不是正式 source of truth。

PolyNexus 的 canonical development remote 目前是 GitHub `lichen200224-bot/PolyNexus`。Remote branch 是否存在與 SHA 真值先用 `git ls-remote`；`origin/<branch>` 只是本機 cache，不得單獨用來判定遠端不存在。

## 2. Context Budget

每個 task 先讀：本檔、`docs/37_CURRENT_ROUTING_INDEX.md`、current task doc，再依需要載入 Project State / ADR / 直接相關程式與 tests。Reviewer 預設 diff/SHA-first；不要因換工具就重做 full-repo analysis。

Token 節省不得弱化 Acceptance Criteria、Human Decision、ADR、Policy、Findings、verification command、actual exit code 或 deterministic evidence。

## 3. Role > Tool

正式角色只有：`HUMAN_AUTHORITY`、`ARCHITECT`、`WRITER`、`INDEPENDENT_REVIEWER`、`SPECIALIZED_VERIFIER`。

Codex / OpenCode / Antigravity / Claude 只是可被指派的工具。工具名稱不自動授予 Writer、Reviewer、Git 或 acceptance 權限。同一 patch 必須 `WRITER != INDEPENDENT_REVIEWER`。

## 4. Single Active Writer / Worktree

同一 task branch 同一時間只允許一個 Active Writer。建議使用 task-specific worktree；canonical local clone 可只做 fetch、branch/worktree 建立與 coordination。不得因工具不同建立彼此無 lineage 的 source copy。

## 5. Scope / Architecture Guard

Scope、Domain、public contract、persistence schema、security/secret boundary、workflow semantics 等高耦合變更依 task/ADR gate。未授權不得順手重構或擴 scope。

- Vendor logic 只在 Adapter/Driver。
- UI 不直接操作 SQLite、OS process、Runtime CLI 或 vendor event。
- Evidence 不得偽造。
- Secret value 不得進 Domain、Evidence、log、Git、export。
- `Task != Run`；Run 是 durable execution identity。
- Alembic 是 authoritative schema migration mechanism。

## 6. Git / Remote Safety

開工前至少確認：repo root、canonical remote、remote exact SHA、branch、HEAD、working/staged state、task scope。

Remote 真值：

```text
git ls-remote --heads origin <branch>
```

Developer clone 不應使用 `--single-branch`；`--single-branch` 僅適合一次性 clean-clone verification。若 remote-tracking ref 缺失，可 explicit fetch exact ref；不得因此宣告遠端 branch 遺失。

禁止未授權 `reset --hard`、force push、branch delete、history rewrite、remote reconfiguration、`git add .`、`git add -A`、`git push --all`、`git clean -fd`。

Task Start Gate 可明確授權 task branch 上的 non-force `SYNC_CHECKPOINT` / `CANDIDATE_CHECKPOINT` commit+push；這些 checkpoint **不等於 acceptance**。Human Acceptance / Integration / Release 仍是獨立 gate。

## 7. Checkpoint Model

- `SYNC_CHECKPOINT`: 跨電腦／跨工具續作；不代表可 review 或 PASS。
- `CANDIDATE_CHECKPOINT`: Writer 認為可送審的 immutable pushed SHA；不代表 PASS。
- `ACCEPTED_CHECKPOINT`: independent review + Human acceptance 後的正式接受狀態。

Independent Reviewer 應驗 exact pushed Candidate SHA，而不是依賴另一台電腦的 dirty working tree。

## 8. Verification

PASS 只認 current deterministic evidence 與 actual exit code。舊 log 只能標 historical；`SKIPPED != PASS`；環境 blocker 必須明列。Mock/fixture evidence 不得冒充 live/production evidence。

## 9. Handoff / Routing

`docs/37_CURRENT_ROUTING_INDEX.md` 是 active routing index；詳細歷史仍可保留在 Project State、Current Handoff 與 task docs。

每次交接至少帶：`TASK_ID`、role/owner、branch、start/candidate SHA、changed files、tests+exit codes、ADR impact、scope deviation、known limitations、unverified、next action、stop condition。

`NEXT_PROMPT != delegation permission`。跨工具/Runtime 必須有新的 Routing Decision。

## 10. Tool Defaults

推薦但不強制：Codex 偏 Architecture/Core/Hard bug/critical review；OpenCode 偏 routine implementation/tests；Antigravity 偏 Browser/E2E；Claude 偏 bounded analysis/second opinion。Task assignment 可覆寫預設，但不能覆寫治理安全邊界。

## 11. Key References

- `docs/05_GIT_WORKFLOW.md`
- `docs/06_AI_TOOL_COLLABORATION.md`
- `docs/08_ACCEPTANCE_STRATEGY.md`
- `docs/36_POLYNEXUS_CROSS_MACHINE_GOVERNANCE.md`
- `docs/37_CURRENT_ROUTING_INDEX.md`
- `governance/POLYNEXUS_PROFILE.yaml`
