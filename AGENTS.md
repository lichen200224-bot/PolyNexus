# PolyNexus Agent Instructions

本檔是 Codex / OpenCode 的短版永久規則。完整規格採 Need-to-know 載入，避免 Token 浪費。


## 0. Workspace Profile

主要 Windows 開發工作目錄為 `D:\AI學習教材\PolyNexus`。這只是本機開發位置；禁止把絕對路徑寫入 Domain、Runtime Contract 或可攜式設定。除非任務明確是安裝／本機環境設定，程式碼應使用 repo-relative path。

## 1. Source of Truth

優先順序：
1. `docs/00_SCOPE_BASELINE.md`
2. `docs/10_DECISION_LOG.md`
3. `docs/18_ARCHITECTURE_DECISIONS.md`
4. `docs/01_PRD.md` / `docs/02_SA.md` / `docs/03_SD.md`
5. `docs/11_PROJECT_STATE.md`
6. `docs/12_HANDOFF_CURRENT.md`
7. 實際程式碼與當前測試 Evidence

若文件互相矛盾，停止擴大修改；先指出衝突並要求 Decision/ADR 更新。

## 2. Token-aware Context

每個任務先讀：
- 本檔
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- 與任務直接相關的 1–3 份規格／程式檔

禁止預先讀完整 docs、完整 log、完整 repository。先使用 Git diff、失敗測試名稱、必要 log 片段。

## 3. Single Active Writer

同一個 feature branch 同一時間只允許一個 Agent 寫入。其他工具只做 Review / Verify。Branch 以功能命名，不以 AI 名稱命名。

## 4. Scope Guard

Phase 1：Product-first, Personal-first, Local-first, Evolution-ready。CORE / BASELINE / COMPATIBILITY / FUTURE 分級不得自行改寫。新完整子系統若不在 baseline，先列 Future 或提出 scope trade-off。

## 5. Architecture Guard

ADR-001～010 已 frozen。修改前必須明確提出 ADR impact。

- Vendor-specific logic 只存在 Adapter / Driver。
- UI 不直接操作 SQLite、OS process、Runtime CLI 或 vendor event。
- Persist PolyNexus intent/evidence，不以 vendor session format 當 Domain Model。
- AI Opinion 不得偽裝成 Verified Evidence。
- ContextPackage ≠ prompt string。
- Secret value 不得進普通 Domain、Evidence、log、Git、export。

## 6. Git Safety

修改前執行：
```bash
git status --short --branch
```

禁止未經要求 `git reset --hard`、force push、刪 branch、覆寫他人未提交內容。

## 7. Verification

- PASS 只認真實 command/tool evidence 與 actual exit code。
- 不可用舊 log 宣稱目前 PASS。
- Tool FAIL 若為 Workflow hard gate 不能被 AI 投票轉成 PASS。
- SKIPPED 必須明確標示。
- 長 log 先機器過濾，再交必要片段給 AI。

## 8. Handoff

重要任務結束前更新 `docs/12_HANDOFF_CURRENT.md`：Goal / Branch / Changed files / Tests+exit codes / Known issues / Next / Do Not Change。

每次工具或人員交接都必須另外提供：`TASK_ID`、`ATTEMPT`、`TASK_DOC`、`HANDOFF_DOC`、`BRANCH`、`WRITER`、`REVIEWER`、`ANTIGRAVITY_STATUS`、`NEXT_OWNER`、完整 changed-files（含 untracked）、protected areas、ADR impact、scope deviation、known limitations、unverified items、current test commands/results/exit codes 與下一步。

- OpenCode：負責實作與測試；完成後更新 handoff，回報 `READY_FOR_CODEX_REVIEW`；不得自行把歷史測試或工具失敗宣告為 PASS。
- Antigravity：涉及 UI、browser、E2E 或 milestone 時執行獨立 journey/failure-path verification；回報 route、fixture、實際結果、artifact/screenshot ref 與 blocker。若不適用，必須明確寫 `NOT_REQUIRED` 及理由；不得修改 Core contract 或與 Writer 同時寫入。
- Codex：以只讀方式獨立 review、重跑必要 evidence，輸出 `PASS`、`FAIL` 或 `NEED_ACTION`；FAIL 必須附 severity、檔案/行號、證據與可直接貼給 OpenCode 的 `FIX_PROMPT`（含測試命令）。
- Human：負責 scope/ADR/產品決策與 Git 授權；只有在 Codex PASS 後，才可明確授權 stage、commit 或 remote push。

PASS 只接受本輪真實 command/tool evidence 與 actual exit code；`SKIPPED`、環境 blocker、未驗證項目與歷史結果必須明確標示，不得轉寫成 PASS。詳細欄位與角色交接規則見 `docs/05_GIT_WORKFLOW.md`、`docs/06_AI_TOOL_COLLABORATION.md`、`docs/08_ACCEPTANCE_STRATEGY.md`。

## 9. Tool Routing

- Codex：Architecture/Core/Hard bug/critical review。
- OpenCode：Implementation/Tests/Templates/routine work。
- Antigravity：Browser/E2E/Milestone verification。
- 每個 task 原則上最多 1 Writer + 必要 Reviewer；只有 milestone/RC 才考慮三工具交叉驗證。

## 10. Skills

Repo skills：
- `polynexus-architecture-gate`
- `polynexus-implement`
- `polynexus-review`
- `polynexus-acceptance`
- `polynexus-handoff`
- `polynexus-runtime-conformance`
- `polynexus-workflow-authoring`
