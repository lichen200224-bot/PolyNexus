# PolyNexus Agent Instructions

本檔是 Codex / OpenCode / Antigravity / Claude 的短版永久規則。完整規格採 Need-to-know 載入，避免 Token 浪費。


## 0. Workspace Profile

主要 Windows 開發工作目錄為 `D:\AI學習教材\PolyNexus`。這只是本機開發位置；禁止把絕對路徑寫入 Domain、Runtime Contract 或可攜式設定。除非任務明確是安裝／本機環境設定，程式碼應使用 repo-relative path。

## 1. Source of Truth

Track A 開發治理以 [Goal Execution Framework](docs/governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) 為 canonical operating rule，承接 2026-09-10 Human 明確決策；目前實作 HOLD、AUTHORIZED_IMPLEMENTATION_GOAL=NONE。先讀 [Current Goal](docs/IMPLEMENTATION_CURRENT_GOAL.md)。權威順序：Current explicit Human instruction → Frozen I-01..I-23 → approved architecture/governance records → authorized Goal → canonical AGENTS/governance → SKILL → tool adapters → model defaults。下列舊正式文件優先序保留其產品來源用途；formal wording 同步仍走 F1–F4，不可因新治理直接改 frozen 文件。

優先順序：
1. `docs/00_SCOPE_BASELINE.md`
2. `docs/10_DECISION_LOG.md`
3. `docs/18_ARCHITECTURE_DECISIONS.md`
4. `docs/01_PRD.md` / `docs/02_SA.md` / `docs/03_SD.md`
5. `docs/11_PROJECT_STATE.md`
6. `docs/12_HANDOFF_CURRENT.md`
7. 實際程式碼與當前測試 Evidence

若文件互相矛盾，停止擴大修改；先指出衝突並要求 Decision/ADR 更新。

Repository 是完整狀態載體，Handoff 是 current state/delta/routing 導航，不是完整歷史或 source tree 的替代品。Conversation history、AI memory、手動複製的 source tree 皆不是正式 source of truth。

正式跨電腦接續必須基於 Human-approved remote Git checkpoint。GitHub／其他 remote Git 是 Development Collaboration Infrastructure，不是 PolyNexus Product Core dependency；尚未完成 approved push 與 clean-clone verification 前，不得宣稱 `CROSS_MACHINE_CONTINUATION_READY`。

## 2. Token-aware Context

每個任務先讀：
- 本檔
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- `docs/IMPLEMENTATION_CURRENT_GOAL.md`、current Goal/handoff、Freeze Record/REV1/Work Packages，按需讀 relevant contract/skill
- 與任務直接相關的 1–3 份規格／程式檔

以上規則適用於 Codex、OpenCode、Antigravity、Claude 與後續接入的 AI 工具。禁止預先讀完整 docs、完整 log、完整 repository；先使用 Git status/diff、task doc、失敗測試名稱與必要 log 片段。

- 同一 task/session 內，未變更的大型文件不重複全文載入；以 file path、section、symbol、commit 或 artifact reference 接續。
- Writer 只取得實作所需 contract、直接相關檔案與 targeted tests；Reviewer 預設採 diff-first，只擴讀受影響呼叫鏈與 acceptance criteria。
- 不因切換 AI 工具而依序重做相同 full-repo analysis、完整測試或完整方案；既有 current evidence 可引用，只有 stale、缺漏、衝突或 acceptance 要求時才重跑。
- 長輸出先由 deterministic tool 篩選；交給 AI 的內容保留 exact command、actual exit code、summary、failure names 與必要錯誤片段。
- Routine work 優先使用足以完成任務的較低成本模型；只有 architecture、security、high-coupling contract、hard root cause 或 critical acceptance 才升級高推理模型。
- 到達 acceptance、明確 blocker、Human decision 或既定 stop condition 即停止，不自行延伸下一輪分析。
- Token 節省不得失真壓縮 Acceptance Criteria、ADR、Policy、Human Decision、Findings、deterministic Evidence、verification command、actual exit code 或 acceptance 所依賴的 deterministic result。需要縮短時使用 `references + current delta`，不得改寫 authoritative material 的語意。

## 3. Single Active Writer

ONE MANAGED GOAL + ONE BRANCH / MANAGED SCOPE = ONE ACTIVE WRITER。Codex 是 default Goal Owner/Implementation Writer；alternate Writer 必須 Human 明確授權。不同 Goal 平行須獨立 branch/workspace/scope，依 Framework 判斷 dependency/shared metadata，初期上限2；不自動授權委派。未知ownership或第二Writer即HOLD。Branch以功能命名。

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
- `Task != Run`；一個 Task 可以有多個 Run，Run 是目前 durable execution identity。不得把 `Run == Attempt` frozen，也不得未經 Architecture Gate 新增 Attempt entity。
- Durable execution 必須保留未來識別實際 runtime/model/adapter/execution target/capability/policy provenance 的能力；優先重用現有 contract。新增 persisted runtime binding 必須另走 Architecture Gate。
- Alembic 是 authoritative schema migration mechanism；`SQLAlchemy create_all()` 不得被宣稱為 production migration authority。其現行 bootstrap/test/local 用途須由獨立 product hardening task 驗證。
- Automation-ready 不等於已具有 authenticated trusted-human approval。D11 Option C 持續 fail closed；未驗證 Human decision 不得無人化推進。

## 6. Git Safety

修改前執行：
```bash
git status --short --branch
```

禁止未經要求 `git reset --hard`、force push、刪 branch、覆寫他人未提交內容。

每個 Git Gate 必須重新確認 branch、HEAD、working tree 與 staged state。禁止使用 `git add .`、`git add -A`、`git push --all`、`git checkout -- .` 或 `git clean -fd` 取代 explicit allowlist。已授權 implementation Goal 包含 explicit-allowlist stage 與 local REVIEW_CANDIDATE commit，不需逐次批准；本輪治理任務明確禁止 stage/commit/push，例外優先。Push 始終需 independent PASS + APPROVE_TO_PUSH + Human exact SHA/remote/branch批准；驗證remote SHA，不只exit 0。其他remote configuration/repository creation及高風險Git操作仍需明確授權；accepted SHA不可amend/rebase/force-push覆寫。

## 7. Verification

- PASS 只認真實 command/tool evidence 與 actual exit code。
- 不可用舊 log 宣稱目前 PASS。
- Tool FAIL 若為 Workflow hard gate 不能被 AI 投票轉成 PASS。
- SKIPPED 必須明確標示。
- 長 log 先機器過濾，再交必要片段給 AI。

## 8. Handoff

Goal handoff 使用 [Framework](docs/governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) 與 docs/handoffs/_HANDOFF_TEMPLATE.md；每 Goal 記完整 changed-files（含untracked）、tests/actual exits、protected areas、ADR impact、scope deviation、limitations、routing與stop condition。current navigation僅main/integration owner更新，parallel branch只更新自身Goal/handoff，不搶唯一current。

Codex/authorized Writer 自行完成 bounded implementation、repair、fresh tests、local review candidate、packet與handoff，REVIEW_READY停止寫入。Final reviewer為Human指定獨立ChatGPT Review Context，不是同一Writer；verdict PASS / NEED_FIX / HOLD。NEED_FIX在原scope內沿用授權，new SHA/new evidence重新review。Human是final acceptance/push authority。Antigravity只有需要UI/browser/E2E/milestone且獲routing時才做獨立驗證；否則NOT_REQUIRED及理由。

舊協作文件的OpenCode-default、每次commit需另批、Codex固定review角色及舊verdict詞彙僅為歷史；Track A採本Framework。產品自身的Evidence/Workflow verdict vocabulary不因此改動。

`NEXT_PROMPT != delegation permission`。每次跨 Runtime／工具 delegation 都必須重新形成明確 Routing Decision，至少包含 `NEXT_ACTION`、`NEXT_OWNER`、`NEXT_PROMPT`、scope 與 stop condition；Agent 不得由 NEXT_PROMPT 推論 recursive delegation 或自動啟動另一 Runtime 的權限。

## 9. Tool Routing

- Codex：Primary Implementation Agent / Default Goal Owner / Default Writer；bounded autonomy直到REVIEW_READY。
- OpenCode、Antigravity、Claude/Claude Code：bounded support；產品Writer須Human明確指定。
- Human-designated ChatGPT Review Context：Independent Final Review；Writer不得自審。
- Astra Medium / Sol Medium / Luna Max按Framework風險routing，不自動切模型或委派。

## 10. Skills

Repo skills：
- `polynexus-architecture-gate`
- `polynexus-implement`
- `polynexus-review`
- `polynexus-acceptance`
- `polynexus-handoff`
- `polynexus-runtime-conformance`
- `polynexus-workflow-authoring`

Track A goal-level skills：`polynexus-goal-execution`、`polynexus-cross-machine-handoff`、`polynexus-independent-acceptance`。既有 specialized skills 仍供實作/contract檢查，不能覆蓋Framework。
