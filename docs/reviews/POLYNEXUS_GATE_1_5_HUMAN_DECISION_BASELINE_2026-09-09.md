# PolyNexus Gate 1.5 — Human Decision + Canonical Baseline Reconciliation

- 日期：2026-09-09
- 性質：獨立評估與待 Human 採納的規劃建議；不是 Scope、ADR、PRD 更新，不是 architecture frozen，也不是 implementation 授權。
- 前置報告：[Gate 1 AS-IS Discovery](POLYNEXUS_AS_IS_DISCOVERY_2026-09-09.md)。本輪只重查版本、關鍵邊界及新增決策，不重做整輪 discovery。
- 本輪交付：本報告、精簡 handoff delta；無產品程式修改、無 schema 變更、無 merge/rebase/reset/checkout、無 stage/commit/push。
- 閱讀方式：文中「ACCEPT」表示 Reviewer 支持候選決策，不等於 Human 已批准；「推薦」也不代表已修改正式規格。

## 1. Gate 1.5 Executive Verdict

**裁決：NEED_MORE_HUMAN_DECISIONS。**

技術上已能指出唯一合理的「推薦設計基線」：GitHub 的 `f34e6b29ae9e7326d1d44b9b03756b450809928f`。它包含目前 committed HEAD 的完整 lineage，並包含後续 runtime、migration、doctor、workflow 與 UX bounded work。沒有理由以較舊且混有未提交修改的目錄作為唯一設計版本。

但「最新且可定位」不等於「新的 Product Re-Foundation Canonical Baseline 已獲採納」，更不等於 Working Product 已驗收。仍需 Human 批准第 22 節的三項產品／治理決策：**基線及 overlay 處置、首個 pilot 的 workspace／信任範圍、Candidate／verification／acceptance 語意修正**。一般工程細節不列為 Human blocker。

主要結論：

1. H01、H02 的 developer + small bug fix 定位合理。第一個成果是「可證明、可接受的一份 repository 變更」，不是「Agent session 成功結束」。
2. H03–H06 應收斂為三個分離邊界：immutable Candidate、綁定 Candidate 的 verification records、明確 Human decision。Evidence 持續累積不能改變原 Candidate identity。
3. 推薦 managed Git worktree 作為 Git repository 的 pilot 預設；它提供工作隔離，不提供對惡意程式的 security sandbox。Dirty user workspace 必須留在原處，必要輸入另經明確快照選取。
4. 先以 **local-personal、單一 OS 使用者、一次一位 writer** 證明閉環。Small-team 協作不能靠共用 loopback token 假裝已有個人身分與可信 approval。
5. 保留現行 stack、Task/Run、ContextPackage、Artifact/Evidence、runtime binding、fail-closed gates。優先補產品執行語意，不重建 Domain、不增加 orchestration breadth。
6. SQLite 的 FK 初始化是 Stability P0；`DELETE` journal mode 本身不是 P0。當前判斷為 **WAL_NOT_REQUIRED_YET**，需另以 contention 與 backup/recovery 證據決定。

本輪完成條件是交付可供決策的分析，不是將產品改至 PASS。Gate 2 只在 Human 採納阻塞決策後開始規劃。

## 2. Canonical Baseline Reconciliation

### 2.1 Current state 與 fresh remote state

| 對象 | 本輪確認 | 解讀 |
|---|---|---|
| 工作分支 | `feature/first-vertical-slice` | 未切換分支 |
| 工作 HEAD | `b87a0dc780e5d9a3bba083dbaf9552ca52508f9a` | 不包含後續 48 個 candidate commits |
| 起始 working tree | 9 tracked modified files；2,001 untracked files；staged 為空 | 不是可重現的單一 Git checkpoint；untracked 多為目錄內展開檔案 |
| GitHub `origin` | `feature/g24-g30-development-completion-routing` → `f34e6b29ae9e7326d1d44b9b03756b450809928f` | fresh `ls-remote` 與 fetch 一致；相較 Gate 1 未更新 |
| 本地 bare `backup` 的 first-vertical-slice | `730912b5a3e19449c355975485f1fe77350a458a` | 原本 tracking 停在 b87；fetch 後顯示目前分支 behind 22 |
| backup 的 g24-g30 | `2bbcb0cb2cc6bc39e5a5770f91b9c58c03fed762` | 落後 GitHub 最後兩個文件提交 |
| `baseline` remote | 指向本機安裝包的 Git bundle | 歷史分發來源，不是更新中的協作遠端；未因其名稱就視為本輪 canonical |

本輪 fetch 只更新 Git tracking metadata。沒有將 remote 內容寫進 Human working tree。`origin` 與 `backup` 名稱不表示誰已被 Human 接受，必須看 commit、接受範圍與證據。

### 2.2 Lineage 與 candidate comparison

`merge-base HEAD origin/feature/g24-g30-development-completion-routing` 為完整 b87 SHA；`rev-list --left-right --count HEAD...origin/feature/g24-g30-development-completion-routing` 為 **0 / 48**。因此目前 committed HEAD 是 candidate 祖先，沒有需要先合併的 committed divergence；這個結論不涵蓋未提交檔案。

| Checkpoint | 角色 | 適合作為新設計基線？ |
|---|---|---|
| b87a0dc | 現工作目錄 committed anchor | 不推薦；較舊，且畫面上的 working tree 是混合版本 |
| 730912b | backup first-vertical checkpoint，歷史 CP06 provisional | 不推薦；中間成果，不能取代後續 candidate |
| `789717fbf4a6b4a36aa71ec1cf7d36f344eccdf7` | G28 bounded UX/workflow product checkpoint | 可辨識產品程式版本，但缺後續 provenance／continuation 文件 |
| 2bbcb0c | G28 docs-state-sync／backup g24-g30 | 同一後期產品基礎，但文件較舊 |
| `e65c19bc6df8dd0362749d9016feabacf8acf6dc` | GitHub continuation package；歷史 clean-clone 驗證對象 | 已有歷史 clone evidence，但不是最新記錄提交 |
| f34e6b2 | 加入 continuation verification 記錄的 GitHub tip | **推薦**；可定位且保留最完整 provenance |

本輪 `git diff --name-status 789717f..f34e6b2 -- services/core apps/web extensions workflows schemas scripts` 為空：最後三個提交沒有改變這些產品／工具路徑。這支持沿用 Gate 1 對 candidate 的程式發現，**不**表示已在 f34 fresh clone 重跑所有測試。

### 2.3 正式接受、candidate、未納入分支必須分開

- candidate 的 `docs/11_PROJECT_STATE.md` 記載 G26/G27/G28 為歷史 Human accepted bounded成果；G28 的 95/100 是當時 roadmap 尺度，不能換算為本輪 Working Product 完成度。
- candidate 的 `docs/12_HANDOFF_CURRENT.md` 與 G30 文件仍記載 external verification 未完成、G30 `NEED_ACTION`、live vendor／browser 證據不足。G29 handoff complete 不是 real executor acceptance。
- `docs/tasks/G30-CROSS-MACHINE-GITHUB-CONTINUATION.md` 的 clean-clone 結果指向 e65；f34 是記錄該結果的後續提交。本輪不將歷史 e65 clone PASS 改寫成 f34 的新測試 PASS。
- `codex/goal-governance-v1-2`：相對 candidate 有 1 個不在其 lineage 的文件提交 `5d1bd60`。
- `codex/goal-objective-v1`：有 2 個不在 candidate lineage 的文件提交（含 `2552c45`）；涉及 AGENTS、協作／acceptance 文件及 docs/32、33。
- `codex/phase-a-minimal-requirements`：有 2 個不在 candidate lineage 的文件提交（`d09526d`、`8750e7e`）；涉及 PRD、SA、SD、acceptance、runtime foundation 等。**不得偷偷當作已批准的 Target Architecture 合入。**
- 其他 runtime／review 歷史 refs 保留作追溯來源；不同 branch tip 不必然代表未整合功能，也不能僅因名稱相似就宣稱已整合。採納對象是 exact SHA，不是將全部分支聯集。

### 2.4 Dirty change disposition

原始 9 個 tracked 修改均保留；本輪唯一對其中檔案的追加是 `docs/12_HANDOFF_CURRENT.md` 的 Gate 1.5 delta。

| 路徑／群組 | 分類與判讀 | 建議 disposition |
|---|---|---|
| `README.md` | 舊 CP 進度与導航修改 | 保留；日後只挑仍正確的導航，不把舊 current status 覆蓋 candidate |
| `docs/10_DECISION_LOG.md` | G13/G14 歷史 routing 追加 | 保留、逐段核對既有歷史；本輪不編輯正式 Decision Log |
| `docs/11_PROJECT_STATE.md` | 混合舊 current state／provenance | 保存原件；不得全檔移植作新基線 |
| `docs/12_HANDOFF_CURRENT.md` | 大量 local handoff 歷史 | 保存原件；本轮仅追加導航，不改寫過往記錄 |
| `docs/15_DOCUMENT_INDEX.md` | 兩個 task links | 後續確認目標存在後可挑取；不是產品能力 |
| `docs/28_MASTER_DEVELOPMENT_ROADMAP.md` | 舊 checkpoint／分數更新 | 保留歷史，不能覆蓋 f34 roadmap |
| `docs/tasks/WP-12.md` | 舊 acceptance/provenance 修訂 | 作歷史補充待比對；不視為當前驗收 |
| `runtime/contracts.py` | 15 行 conformance docstring；未改 method signature | 語意註記候選，不是新的 frozen 權威；可獨立人工 review |
| `runtime/registry.py` | 舊 registry sanitization／fail-closed 修改與註解 | 與 f34 blob 不同；candidate 已有後續 G05/G25 演進，禁止直接覆蓋或假定完全等價 |
| untracked `runtime/codex.py` | 與 f34 同名檔案內容不同 | 保留為歷史實作 overlay；不能代表 real Codex executor 已完成 |
| untracked `test_wp14_codex_runtime.py` | 與 f34 同名測試不同 | 保留、之後按行為挑取有用 coverage；不整檔覆蓋 |
| untracked `test_runtime_registry_conformance.py` | f34 沒有此路徑；歷史 refs 曾有同名測試 | 明確列為未納入測試資產，不因 candidate 無此檔就刪除；後續查驗是否已被其他測試涵蓋 |
| docs 的 11 個 untracked 檔案 | Gate 1 報告、內容索引、控制面板、G03/G12/G13/G14/G19/WP14/conformance 文件 | 保留為 evidence／planning overlay；不可全部冒充已接受規格 |
| competition 的 3 個檔案 | 參賽材料／簡報 | 保留；對外敘事不支配產品核心 |
| scripts 的 6 個檔案 | 簡報／審查 artifact 產生與檢查腳本 | 保留，按實際用途分類，不自動納入產品 startup |
| `initial-review-v1` 2、`initial-review-v2` 8、`output` 11、`docs.zip` 1 | 輸出／封存，可能有 Human 有效成果 | 即使 generated 也不刪除；先確認來源與可重建性 |
| `apps/web/dist-review` 3 | build output | 不納入 source baseline；保留原件 |
| `review_work` 1,953 | 大量依賴、review output／profile 等混合工作檔 | 未逐一鑑定內容；不 blanket stage、移植、打包或清除 |

完整起始路徑及 SHA-256 inventory 位於本機 ignored evidence：`artifacts/verification/gate1_5-20260909/preserved-files-before.json`，共 **2,010** 個既有 modified／untracked 檔案。此檔用於本輪 preservation 檢查，不是 portable product baseline，也不是批准公開其中內容。

### 2.5 Obsolete worktree metadata

`git worktree list --porcelain` 顯示多個登記路徑仍是舊的 `D:/AI學習教材/PolyNexus/...`，目前 repo 路徑含底線：`D:/AI_學習教材/PolyNexus/...`。若干 entry 標示 `prunable gitdir file points to non-existent location`，但相應內容可能仍在新位置，例如 ignored candidate directory。

**prunable 是 metadata 診斷，不是「工作可丟棄」。** 本輪不執行 prune／repair／remove。後續若需啟用 worktree，先盤點實體目錄與 `.git` pointer、保全未提交內容，再做個別 repair；不把整批清除當成環境整理。

### 2.6 Recommended baseline record

```text
CANONICAL_BASELINE_CANDIDATE: GitHub g24-g30 exact checkpoint; RECOMMENDED_PENDING_HUMAN_ADOPTION
BASELINE_SHA: f34e6b29ae9e7326d1d44b9b03756b450809928f
BASELINE_BRANCH: origin/feature/g24-g30-development-completion-routing
WHY_THIS_BASELINE: descendant of current committed HEAD; latest fetched GitHub checkpoint;
  preserves G28 product work and subsequent provenance; no product delta after 789717f
WHAT_IS_NOT_INCLUDED: local dirty/untracked overlays; independent governance/Phase A branches;
  ignored runtime data/artifacts; uncompleted G30 external/live-provider verification
DIRTY_CHANGE_DISPOSITION: preserve in place; inventory; selective future reconciliation;
  no blanket overwrite, discard or merge
KNOWN_BLOCKERS: Human baseline adoption pending; real Working Product absent;
  known Stability P0 defects; historical acceptance has bounded scope
MIGRATION_RISK: older local runtime/tests can regress newer behavior if copied wholesale;
  docs branches conflict in authority; moved worktree pointers; existing DB/artifact state not migrated
```

此处不標 `CANONICAL_BASELINE_NOT_READY`，因 Git lineage／遠端 identity 已足以安全提出候選；**formal adoption 尚未完成**，故總體仍不進 Gate 2。批准後也不代表可以直接切換／覆寫目前工作目錄。Gate 2 可直接以 Git snapshot 閱讀設計；實作 checkout、資料 migration 與 Git checkpoint 是後續獨立操作。

### 2.7 本輪證據與限制

以下 Git 命令均使用 `git -c safe.directory=D:/AI_學習教材/PolyNexus`；未寫入 global safe.directory。

| 本輪操作 | 實際結果／exit code |
|---|---|
| `status --short --branch`、`diff --cached --name-only` | exit 0；上述 dirty state；staged 空 |
| `ls-remote --heads origin` | exit 0；f34 的 g24-g30 branch |
| `ls-remote --heads backup` | exit 0；發現 first-vertical tracking 過期 |
| `fetch --no-tags --no-recurse-submodules origin` | 沙箱初次 exit 1（FETCH_HEAD 寫入受限）；批准後 exit 0 |
| 同參數 `fetch ... backup` | 批准後 exit 0；更新 tracking refs；無 checkout |
| `merge-base HEAD origin/feature/g24-g30-development-completion-routing` | exit 0；b87 完整 SHA |
| `rev-list --left-right --count HEAD...origin/feature/g24-g30-development-completion-routing` | exit 0；0、48 |
| `diff --name-status 789717f..f34e6b2 -- services/core apps/web extensions workflows schemas scripts` | exit 0；空輸出 |
| governance／Phase A `rev-list` 與 `log` | exit 0；分別 1／2／2 個獨有文件提交 |
| local 五個 runtime／test 檔案 `hash-object`，與 f34 `rev-parse SHA:path` 比較 | 同名四檔不相同；registry-conformance test 在 f34 不存在，該次 rev-parse 回報 fatal，不算查驗 PASS |
| PowerShell 路徑 wildcard `rg schemas/workflow*` | 路徑語法錯誤；改用 `rg ... schemas -g '*workflow*'`，exit 0，確認 node set |
| 既有工作檔案 inventory | exit 0；2,010 路徑，SHA-256 |

Gate 1 的 Core pytest（兩個 checkout，exit 0，均有 skip）、Web 78 passed／build exit 0、CREATED restart 重現與 PRAGMA 結果，**在本輪均為歷史 evidence**。本輪以 Git product delta 與直接 source read 確认發現仍適用；沒有重跑 full suite、real provider、browser journey、live DB audit、fresh f34 clone 或 WAL loss experiment。不得宣稱這些本輪 PASS。

### 2.8 Repo evidence locator

下列 `C-*` 全指 **f34 exact snapshot** 的 repo-relative path；不能默認目前 b87 工作目錄同名檔案內容等同。可用 `git show f34e6b2:<path>` 閱讀。既有本機 candidate 副本不是新的 canonical identity。

| ID | Path／symbol | 本報告依據 |
|---|---|---|
| C1 | `services/core/src/polynexus_core/domain/models.py`：Project、Task、ContextPackage、Artifact、Evidence、Finding、Run | 有核心模型；無完整 repository/candidate/acceptance identity |
| C2 | `services/core/src/polynexus_core/domain/enums.py` | RunState 與 ResumeMode 已存在；ResumeMode 為 NATIVE/MANAGED/NONE |
| C3 | `services/core/src/polynexus_core/runtime/registry.py`、`codex.py`、`opencode.py` | reference default；conformance adapter 不能當真實 CLI 執行證據 |
| C4 | `services/core/src/polynexus_core/api/runs.py`：create_run（83 起）與 execute route | 建立 CREATED 不執行；execute 是另一操作 |
| C5 | `services/core/src/polynexus_core/runtime/reconciliation.py`：111 起 | non-terminal reconciliation 要求 immutable binding；與未執行 CREATED 路徑衝突 |
| C6 | `services/core/src/polynexus_core/persistence/database.py`：27 起；`backup.py`：126、154 | filename 判斷 SQLite；copy2 backup/restore 路徑 |
| C7 | `apps/web/src/App.tsx`：24；`services/core/src/polynexus_core/api/dependencies.py`：17–50 | UI 空 auth headers；Core loopback token fail-closed |
| C8 | `services/core/src/polynexus_core/workflows/execution.py`：ReferenceWorkflowExecutor | reference execution 不等於各 node 的真實 side effects |
| C9 | `services/core/src/polynexus_core/workflows/gates.py`：TOOL_EVIDENCE、HUMAN_GATE／D11 | evidence hard gate 與 Human gate 已有保守語意，未具可信 Human 完成閉環 |
| C10 | `schemas/workflow.schema.json`、`services/core/tests/test_cp05_wp27_golden_workflows.py` | 固定 node vocabulary；reference runtime 的 golden completion 非 real product proof |
| C11 | `docs/11_PROJECT_STATE.md`、`docs/12_HANDOFF_CURRENT.md`、`docs/tasks/G30-CROSS-MACHINE-GITHUB-CONTINUATION.md` | bounded acceptance／external verification／clone provenance |

不以 C10 的測試名稱推導不存在的 runtime side effect；應檢查 fixture 使用的 adapter 與實際 assertions。

## 3. Human Decision Review Matrix

| Decision | 裁定 | 理由與收斂方向 |
|---|---|---|
| H01 Primary Persona | ACCEPT | C1、C4、C8 的中心是 Task/Run、software workflow；developer/lead 與 reviewer 能直接使用現有能力。通用 business persona 會增加尚未驗證的需求 |
| H02 First Vertical | MODIFY | 接受小 bug fix 與 failure/retry；將「固定 Candidate」移至獨立 tests 之前，避免測試對象與最後 diff 不同（C1、C9） |
| H03 Acceptance Target | MODIFY | immutable change set 合理；採 content-addressed manifest Value Object + durable publication/reference。Evidence manifest 另外固定，不參與循環變動的 Candidate identity（C1） |
| H04 Independence | MODIFY | 不需要不同 provider；但 independent process 身分或 deterministic 字樣本身不足，必須控制 test oracle、candidate immutability 與 evidence ingestion（C9） |
| H05 State semantics | MODIFY | 保存底層事實／決策，導出大部分標籤；IMPLEMENTED 是待驗證 claim，RELEASE_READY 是另個 policy certification，不增七個 Run enum（C2） |
| H06 Evidence | MODIFY | KEEP 現有 Evidence/Finding/Artifact；EXTEND candidate、requirement、provenance binding；REFACTOR gate 的適用性判定；不重寫 Evidence Domain（C1、C9） |
| H07 Continuity | ACCEPT | ResumeMode 已符合 NATIVE/MANAGED/NONE；MANAGED 必須定義為新 run 的受控再建構，不是假装原 session 續命（C2、C3） |
| H08 Handoff | MODIFY | ContextPackage 保留；另定 immutable continuation manifest 引用不可變版本，workspace observation 具 freshness；不複製整個歷史 DB（C1） |
| H09 Workspace states | MODIFY | 候選列表混合 Git facts、操作狀態與風險；採少數正交欄位／導出 UI 標籤，不做七態 enum（C1、C5） |
| H10 Single Writer | ACCEPT | 有助先證明 ownership/recovery；限制的是受管 workspace mutation owner，verifier 的 read-only 工作可並行；同 OS unrestricted process 仍是威脅 |
| H11 Workspace strategy | MODIFY | 推薦 managed worktree，但須明確 dirty capture、shared Git、Windows lifecycle 與非 sandbox 限制；不將全部 repository feature 支援列首輪承諾 |
| H12 Source of Truth | ACCEPT | Git 管已提交 source history，PolyNexus 管 execution／evidence／decisions；未提交 change bytes 需 capture，provider session 僅 external ref（C1、C3） |
| H13 Provider Independence | ACCEPT | 架構 invariant 與產品驗證等級分開；一個 real executor 先閉環，第二個再證明共用核心（C3） |
| H14 Product Brain | MODIFY | 支持 Track B；共同邊界須涵蓋所有 side-effect commands、policy authorization 與 tool delegation，不只畫一條 RunSupervisor 箭頭 |
| H15 Workflow | ACCEPT | 保留 vocabulary；只落實第一 vertical 需要的五種 node，不以 definition coverage 充當 execution maturity（C8–C10） |
| H16 CI Evidence | MODIFY | exact Candidate 必要但不足；加 trusted retrieval、workflow/test oracle、source tree 對應、attempt／環境／artifact provenance，不能只比 SHA 字串 |
| H17 Human Acceptance | MODIFY | Local-personal 可免 Enterprise IAM；small-team 不自動等價。需獨立 Human action boundary，普通 Core/Agent token 不能接受成果（C7、C9） |
| H18 Startup | ACCEPT | setup/start/health/stop 與安全 reset 的可理解路徑是 pilot gate；一鍵正式 installer、自動更新不阻塞首個 vertical（C6、C7） |

H06 的正式 decision status 是 **MODIFY**；KEEP/EXTEND/REFACTOR 是其內部 architecture classification，不是新的人類決策狀態。

### 有修改的決策：替代方案與影響

| 項目／Repo evidence | Product reason 與 alternative | Short-term impact | Long-term impact | Migration impact | Risk |
|---|---|---|---|---|---|
| H02；C1/C9 | 先 publish candidate，再以該 snapshot 驗證；writer 自測可在 publish 前，但不是最終驗證 | 增加 freeze／hash 檢查 | 可重現驗證與 audit | 不改舊 RunState；新增關聯語意待 Gate 2 | tests 若改 tracked source，必須新 candidate，避免誤認 immutable |
| H03；C1 | Candidate manifest 與 EvidenceSet manifest 分離 | 多一個清楚的 reference boundary | 避免 evidence 追加導致 identity 循環 | 舊 artifact 可保留為 legacy unbound，不回填假 hash | path／CRLF／binary canonicalization 要明確 |
| H04；C9 | 以獨立 oracle／執行／觀測組合定義最低獨立性 | 保護驗證命令與可信結果收集 | 不被 provider 同質化破壞價值 | 舊 AI_OPINION 不升格為 TOOL_EVIDENCE | writer 可修改 tests 或偽造 log |
| H05；C2 | records + projections；保留 run lifecycle | UI 顯示 execution、checks、decision 分開 | 支援失效／重驗而不重寫歷史 | 舊 COMPLETED 只代表舊 execution outcome | 過度簡化綠燈會再引入混淆 |
| H06；C1/C9 | 在既有 Evidence 上加適用性／trust binding | 有限 extension／gate matching | 能多來源收證而不鎖 provider | 舊 evidence 標 legacy scope；不得直接 certify 新候選 | metadata hash 不等於 producer authenticity |
| H08；C1 | content-addressed continuation manifest + immutable refs | 定義必要欄位與 missing-ref 行為 | 避免重複存整個 context/history | ContextPackage id/version 延用；不預設建新 table | dangling refs／retention 導致接續失敗 |
| H09；C5 | Git observation + ownership + recoverability axes | 少量明確狀態與 freshness | 支援 recovery，不綁死 UI wording | 舊 Run 無 workspace facts 時 UNKNOWN | CLEAN 不代表無其他 writer／安全可覆蓋 |
| H11；C5/本輪 worktree metadata | managed worktree + explicit supported repo envelope | 多 checkout lifecycle／磁碟管理成本 | 可重用於 retry、candidate replay、provider switch | 原 workspace不搬動；既有未提交成果另處理 | 共用 .git、submodule／LFS／Windows path 問題 |
| H14；C4/C8 | typed proposal 經受控 command boundary；Brain 不持 privileged credentials | Track A 不增加 Brain 系統 | Track B 可共用同一 truth | 之後只加 client/planner，不分叉 execution DB | 只限制主路徑卻放任 delegated tools bypass |
| H16；C1/C9 | trusted importer 校驗 candidate＋workflow＋producer＋artifact | 外部 CI 可 NEXT；local verifier 先完成 | 保持公司可持有證據，不綁特定 CI | adapter/importer 層擴充 evidence envelope | fork CI／過期rerun／merge SHA／可竄改 artifact |
| H17；C7/C9 | 先單使用者 pilot、分離 Agent 與 Human decision channel；不宣稱 enterprise assurance | 需 pairing／explicit intent；不做 IAM 平台 | 若進 small-team，需真正 per-person identity | D11 現狀維持 fail closed，待批准才能演進 | 同 OS principal 任意程式可冒用，必須揭露 threat boundary |

沒有建議 REPLACE 現行主要 stack、REMOVE 核心 Domain 或立即大規模遷移；上述現在值得收斂，是因為它們會改變 Gate 2 的身份邊界與驗收設計，不是因為已存在的程式必須被推倒。

## 4. Stability P0

這是「既有操作不應破壞服務／資料」維度，與第 5 節 Product P0 同等重要。以下順序是修復依賴建議，不是降低產品閉環優先度。

| 順序 | 問題與 evidence | 最小修復方向（非本輪實作） | 必須證明 |
|---|---|---|---|
| S0-1 | SQLite init 看 filename 是否含 `sqlite`；普通 `poly.db` 不啟用 FK（C6；Gate 1 probe FK=0） | 以 engine dialect 判斷；每條連線正確啟用 FK；先檢查既有資料 | 新／pool reused connections FK=1；實際 invalid insert 失敗；既有 dangling records 有處理策略 |
| S0-2 | 正常 create Run 留下 CREATED，restart reconciliation 卻要求 binding（C4/C5；Gate 1 重現） | 區分未啟動 intent 與曾啟動 execution；前者不應使整個 startup 失敗，後者不得被重派 | API create→不execute→重啟可用；running/unknown 不 duplicate launch；壞資料隔離可診斷 |
| S0-3 | Web 預設無 auth header，Core 必須 loopback token（C7） | 可信 client pairing/config channel；不放寬 Core auth 作為修復 | Fresh profile 從 START 到 authorized API；缺 token 仍403；不把 secret 寫普通 log／Git |

### SQLite：FK 與 WAL 分開裁決

**初始化條件：BUG。Foreign Key integrity：NOW 必修。WAL：WAL_NOT_REQUIRED_YET。**

SQLite FK enforcement 是 connection 行為；檢查現有資料應包含 `PRAGMA foreign_key_check`，不能只以 `integrity_check` 替代。只啟用 FK 也不會神奇修復歷史 dangling references；未宣告 FK 的關係仍需 application consistency audit。審查真實 DB 前先備份，不能將 orphan data 自動刪掉。[SQLite Foreign Key Support](https://sqlite.org/foreignkeys.html)

| 因素 | 現階段判斷 |
|---|---|
| Concurrency | Single active coding writer 不等於單一 DB writer，但目前無 pilot contention 量測；不能從 supervisor concurrency 數字直接推論 WAL 必要 |
| Long-running runs | Agent 可跑很久，DB transaction 不應跟著持有很久；優先短 transaction／bounded event persistence |
| Read/write contention | Dashboard polling／event writes 若量測到 busy 或 latency，可提升為 WAL_RECOMMENDED；不足以現在宣稱 required |
| Crash recovery | Rollback journal 本來就有交易恢復機制；WAL 不是修正 application ownership／orphan process 的方法 |
| Backup/restore | C6 的 copy2 不是 live DB 一致 snapshot 協定；啟 WAL 前必须驗證 db/wal/相關 artifact 的一致性 |
| Deployment | Local disk pilot 可評估 WAL；不要直接承諾 network filesystem、多 host 或同步雲資料夾支援 |

WAL 能讓讀者與 writer 更好並行，但仍只有一位 writer；長 read transaction 會影響 checkpoint，且需要處理 WAL/SHM 與本機 shared-memory 條件。這些是 trade-off，不是無條件升級。[SQLite WAL](https://sqlite.org/wal.html)

Live backup 優先評估 SQLite online backup 的一致 snapshot 機制，或明確停機／quiescent backup；還需記錄 DB 對 Artifact references 的保全範圍。不能只讓檔案複製 exit 0 就宣稱 disaster recovery 成立。[SQLite Online Backup API](https://sqlite.org/backup.html)

## 5. Working Product P0

**缺少任一必要項，就不能完成第一個真實 Product Outcome。** 不以「server 會不會 crash」排序這些價值。

| 依賴階段 | Product P0 | AS-IS／最小可行範圍 | 是否牽涉 architecture boundary |
|---|---|---|---|
| P0-W1 | 可啟動／paired client | C7 有缺口；setup、Core/Web health、正確連線與關閉 | 主要 composition／UX，Human action auth 另有邊界 |
| P0-W2 | Repository binding＋Goal/Scope/AC | C1 Project/Task 不足；先一個 Git repo／明確 baseline 與 criteria version | EXTEND 現有 context/task/project 邊界，不預先決定新 table |
| P0-W3 | Workspace ownership | 無完整工作目錄 identity／claim/release/recovery | NEW 最小受控 ownership 語意；與 deterministic runtime 共用 |
| P0-W4 | 第一個 real executor | C3 conformance 不等於 real launch；一個可取得且可用的 executor | Adapter 內 provider-specific；Core 不新增 vendor branch |
| P0-W5 | 真實修改＋monitor/stop | 需證明指定 cwd、process tree、exit、cancel與殘留；Agent status 不夠 | EXTEND Supervisor/Adapter lifecycle，不另建 scheduler |
| P0-W6 | Candidate capture | freeze、changed set、binary/source content、diff/artifact hash | NEW identity 語意，reuse Artifact |
| P0-W7 | Deterministic verification | 可信 runner 對 exact candidate 執行必要 tests，保留 command/exit/environment | EXTEND TOOL execution 與 evidence ingestion |
| P0-W8 | Evidence／independent verification | C9 有 fail-closed 基礎，缺 candidate/oracle/provenance 閉環 | EXTEND + gate matching REFACTOR |
| P0-W9 | Human Accept/Reject | C9 D11 沒有產品完成閉環；明確人類行為綁 candidate＋evidence | 需經批准的 acceptance boundary 演進 |
| P0-W10 | Failure→Retry/Recovery＋history | 未知 workspace 不自動重派；新 run／新 candidate 保留前次失敗 | 延用 Run identity；不自行引入 Attempt entity |

這是同一個 vertical 的依賴序，不是十個獨立大型子系統。First provider 的具體選擇可在 Gate 2 依 availability／可控制性決定；不要求 Human 現在承擔 SDK 或 subprocess 工程選型。

## 6. Acceptance Target Definition

Human 接受的是：**在明確需求／scope 下、內容已固定、可檢視且已有指定 verification 結果的一份 Candidate Change Set**。

不接受 provider session、不接受裸 `Run.COMPLETED`，也不把「writer 說 fixed」當已驗證 bug fixed。Acceptance 不自动等於 merge、commit、push、deploy 或 release；這些是分開的受控行為與授權。

推薦第一條真實流程：

```text
Open repository → Task + versioned Goal/Scope/AC → choose real executor
→ pin baseline + acquire workspace ownership → create Run → launch
→ modify / monitor → writer finish or stop; confirm quiescence
→ capture and publish immutable Candidate A
→ run required checks against A → collect trusted evidence
→ independent verification decision for A → Human Accept / Reject
→ retain candidate, evidence, decision and history

Failure / rejection → preserve observations → reconcile workspace
→ explicit retry with new Run → Candidate B if content/requirements changed
→ re-evaluate applicability and verification → new Human decision
```

Writer 在 freeze 前可自測；最終 acceptance 用的測試必須可證明對應 frozen A。Human 在看完畫面後若 A／evidence snapshot 改變，原按鈕 action 應拒絕並要求重新檢視，不能接受「最新版」這個浮動指標。

## 7. Independent Verification Definition

最低獨立性是**獨立於 writer 的完成宣稱，且驗證 oracle、候選與結果收集具足夠可信邊界**。不是「換一家 AI」或「另開一個 process」就成立。

最低要求：

1. 指定 Candidate ID，materialize/check hash；前後皆確認來源未被改寫。測試產物放在允許的 scratch/output 區，source mutation 另成 B。
2. Required checks／AC 與命令由受信任的 policy／Human／固定測試定義決定，writer 不能刪掉測試後自評 PASS。
3. Runner 實際 exit、timeout、signal、logs、test target、環境與產物由受控 observer 收集；writer 可提交 evidence proposal，不能自行核發 trusted result。
4. Verifier 結論只涵蓋其真的檢查的 claim。單一 deterministic test 可以對狹窄 claim 足夠，不能代表安全、效能、需求完整性全部通過。
5. 任何修改 Candidate 的 reviewer 都成為該修改的 writer；建立 B，前次對 A 的證據保留但不直接 certification B。

| 來源 | 可以提供什麼 | 不可直接推論 |
|---|---|---|
| Local deterministic runner | 受控 command 對固定候選的結果 | 測試本身正確／需求完整已被證明 |
| CI | trusted workflow 對精確 tree 的 checks | 名為 CI 的 JSON 就可信 |
| Independent process | 隔離 writer 的結果收集／執行 | 同 OS 權限且受 writer 操控仍不是强隔離 |
| Reviewer Agent | findings、審查觀察、建議；若執行工具可另產 tool evidence | 文字 APPROVED 直接替代 hard checks |
| Human | 視覺／行為 review 與明確接受決策 | 親自按 Accept 可以把 hard FAIL 改成 VERIFIED |

Different provider 是 optional assurance dimension，與 test oracle、process isolation、artifact integrity 分別記錄。V1 不建立複雜 assurance score；顯示實際檢查者與未覆蓋部分。

## 8. Candidate Identity Model

### 8.1 產品語意與 identity boundary

推薦 **immutable content-addressed manifest Value Object**；其 publication／來源關聯是 durable facts。它不是當前 workspace 的 Derived View，也不需立即宣告為新的 Aggregate／DB table。若後續要管理保留／撤回／索引，那是 publication record lifecycle，不是讓 Candidate 內容可變。

| Candidate manifest 內，固定後不可改 | 另行引用／記錄 |
|---|---|
| Repository logical identity、baseline commit/tree | Task/Run publication links／產生時間 |
| 明確 changed file set：新增／修改／刪除、path、mode、content hash | Runtime/model/adapter provenance：由 run binding／execution records 引用 |
| Patch/diff artifact identity 與支持重建所需 content artifacts | EvidenceSet manifest：單獨 hash、可有多次版本 |
| Requirement/Scope/AC revision、ContextPackage immutable version/hash | VerificationRecord：candidate＋criteria＋evidence set＋verifier/environment |
| Test target 與 validation contract/version | Human decision：candidate＋verification/evidence snapshot＋principal/time/reason |
| Manifest format/canonicalization 與包含／排除規則版本 | 新證據、撤銷、重驗事件：追加歷史，不改 Candidate |

Candidate ID 對 manifest 的 canonical representation 求 hash；artifact references 必須能解到相符 bytes。**只存 hash 沒存可取回內容，不算可恢復的 candidate。**

Git revision 是 baseline reference，不足以識別所有未提交變更。第一版至少處理允許範圍內的 untracked/new、deleted、binary、file mode；CRLF／Git filters／case sensitivity 要定義比較的是 Git tree bytes 還是 materialized bytes。Unsupported symlink、submodule、LFS 或特殊 repository 情況應 preflight 明確拒絕／標示，不靜默忽略。

### 8.2 Identity 何時改變？

- Code／changed file set／需求或 validation contract 改變：新 Candidate B，即使同 Task 或同 Run。
- 重跑相同 tests、加入 reviewer report、替換環境：仍可對 A 產生新的 verification record；不改 A 的內容 ID。
- 相同內容由另一 Run 產生：可共用內容 identity，但保留不同 publication／execution provenance，不抹去成本與失敗歷史。
- Evidence manifest hash 不納入會循環依賴的 Candidate hash。Candidate→verification 可以由索引查詢；verification 固定引用 Candidate 與 evidence set。

### 8.3 H05 狀態分類

| 用語 | 應保存的事實／event | 顯示／判定方式 |
|---|---|---|
| EXECUTED | Run lifecycle、terminal outcome、exit、結束時間 | Derived execution status；FAILED/CANCELLED 也可能已實際執行，不等於成功 |
| IMPLEMENTED | Writer claim、Candidate publication | 待驗證 claim／顯示標籤，不能作為真實 bug fixed certification |
| TESTED | 每個 check 的 command、target、outcome、provenance | Derived coverage；部分執行也可顯示 tested，但要列 MISSING/FAIL |
| REVIEWED | Review record、findings、reviewer、candidate | Derived，依 policy 指定 review 是否必需 |
| VERIFIED | Verification evaluation record、policy/requirements/evidence snapshot | Scoped certification：必需可信 checks 完整且符合；不等於永遠正確 |
| ACCEPTED | 明確 Human decision record／event | Persistent decision fact；current accepted view 由 decision history 導出 |
| RELEASE_READY | Release policy evaluation／certificate | LATER；不因 acceptance 自動成立 |

保留現有 RunState；不增加七個混合 enum。後續 evidence stale／新 finding 可使「目前有效 certification」失效，但歷史 accepted fact 不應被偷偷重寫。另追加 revoke／supersede／needs-reverification 記錄。

## 9. Evidence Trust Model

```text
Versioned Claim / Acceptance Criterion
→ required checks + applicability + trust policy
→ actual evidence bound to Candidate
→ completeness / integrity / provenance / outcome evaluation
→ scoped VerificationRecord / certification
→ Human decision (separate)
```

unit PASS + integration MISSING：顯示「已執行 1/2 checks」，整體 **NOT VERIFIED**。test tool ERROR、SKIPPED、timeout、無可信來源、candidate mismatch、stale evidence 都不是 PASS。必要 evidence 缺失不是「沒有發現 bug」。

| 既有能力 | 分類 | 保留與補足 |
|---|---|---|
| EvidenceType／EvidenceStatus | KEEP | AI_OPINION、TOOL_EVIDENCE 等來源區別值得保留 |
| Artifact identity/reference | EXTEND | 驗證 content hash、可取回性、manifest membership、retention；不能只檢查 hash 字串非空 |
| Finding | KEEP + EXTEND | 缺陷／審查結論，綁 Candidate 與狀態；不拿 Finding 替代原始測試證據 |
| Existing gate fail-closed | KEEP | Tool hard FAIL 不能被 AI 投票翻轉；Human gate 未驗證不前進 |
| Gate evidence matching | REFACTOR | 從 gate-id／metadata／PASS 增加 candidate、criteria、producer、environment、freshness applicability |
| Claim→required evidence mapping | NEW 最小語意 | 先針對第一 vertical 的 AC/checks；不是新 generic policy engine |
| Certification／Human decision binding | EXTEND 現有邊界，具體 persistence 待 Gate 2 | 不以 event text 模擬可靠 decision transaction |

最低 evidence envelope：candidate ID、requirement/check ID＋version、producer identity/type、實際 command/target、cwd identity、source/test revision、環境摘要、start/end、exit/outcome、artifact hash refs、收集方式、run/attempt ref（外部 CI 的 attempt，不是新增 PolyNexus Attempt entity）、ingestion time。

Hash 證明相同 bytes，不證明誰產生、命令真的跑過、tests 有效。Metadata 自我雜湊仍可由造假者一起重算。信任來自受控收集／可信來源與可驗證綁定；秘密值不進 manifest、log、DB ordinary metadata 或 export。

## 10. Cross-Agent Continuity Contract

**V1 承諾 Task／工作狀態連續，不承諾 provider 私有 session 可移植。**

最小 continuity facts：Task identity；versioned goal/scope/AC；ContextPackage；repository baseline；workspace observation／ownership；candidate/changed files；已完成與待辦（標示 claim 或 verified）；open findings；artifacts/evidence；Human/runtime decisions；environment snapshot。

| Resume capability | 產品行為 |
|---|---|
| NATIVE | Provider 宣告且實測支援原 session resume；仍需驗證 workspace/binding/freshness，不能因 session id 存在就恢復 writer |
| MANAGED | PolyNexus 從保存的工作事實建立新的 executor session／Run；顯示為「接續工作」，不是「還原原 session」 |
| NONE | 不支援自動 continuation；仍可保留 task/history、提供 Human takeover/export |

Switch Agent 前必須停下並確認舊 writer ownership 已結束／隔離；未能確定 process 是否存活時進 recovery-required，不讓第二 Agent 同時寫。Native resume failure 不刪 Task；fallback 到 managed 需能力與 policy 允許並留下 route decision，不偷偷改 executor。

Red-Team：若使用者很少換 Agent，continuity 可能只是一份較昂貴的 handoff summary。必須用 B05/B06 的接續時間、遺漏率與重做成本证明價值，不以存了更多欄位當價值。

## 11. Handoff / Continuation Contract

ContextPackage 回答「現在應知道什麼」；ContinuationPackage 回答「接續前要驗證什麼、從哪個工作狀態接續」。兩者不能只是同一個大 prompt 改名。

| 內容 | Immutable／reference 策略 |
|---|---|
| Package id、格式版本、生成時間、來源 task/run | immutable manifest |
| Goal/Scope/AC | 引用 exact revision/hash，不引用浮動 latest |
| ContextPackage | exact id/version/hash；不复制成另一套 context truth |
| Repository baseline／Candidate | 引用 Git revision 與可取回的 candidate manifest |
| Workspace state／changed files／ownership | 生成時 observation snapshot immutable；接收端重新觀察，不把舊 CLEAN 當現在 CLEAN |
| Completed／pending work | snapshot，標來源及 claim/verified 差異；新進度建立新 package |
| Open findings、evidence、artifacts、decisions | exact refs／hash；可攜 export 必須帶 resolver／必要 bytes，不能只有本機絕對路徑 |
| Runtime／environment | 版本、平台、依賴 lock/hash、必要能力／限制；secret 僅 reference／重配需求，不含值 |
| Next action、scope、stop condition、接續限制 | immutable proposal；不是自動執行／遞迴 delegation 授權 |

接續前校驗：refs 可取回且 hash 正確、baseline 可 materialize、workspace 無未知 writer、環境相容、context 未失效、required authority 仍有效。缺任一必要項，顯示阻塞與可修復動作；不悄悄填補假的完成狀態。

Retention 必須保住 decision 所引用的 evidence／candidate；若清理政策移除了必要 bytes，明確標記不能重現，不能仍宣稱完整 continuity。

## 12. Workspace Integrity Model

不採用 `CLEAN/MODIFIED/UNCOMMITTED/CONFLICTED/PARTIAL/RECOVERY_REQUIRED/UNKNOWN` 單一 enum。它們可同時成立、也有重複。

| 維度 | 最小事實 | 導出 UX |
|---|---|---|
| Identity | repo id、baseline commit/tree、workspace ref | 「正在修改哪份工作副本」 |
| Git observation | HEAD、index/worktree diff、untracked、conflict／merge state、觀察時間/hash | CLEAN；HAS_CHANGES；CONFLICTED；UNKNOWN |
| Ownership | owner Run/actor、claim/release、最後可驗證 process/control observation | FREE／OWNED／UNCERTAIN，不以空 PID 等於 FREE |
| Recoverability | capture 完整性、process cleanup、baseline/candidate 可取回、operation journal | READY 或 RECOVERY_REQUIRED；PARTIAL 作原因碼 |

`MODIFIED` 與 `UNCOMMITTED` 合併為畫面「有未提交變更」，細節區分 staged／unstaged／untracked；`PARTIAL` 描述 capture／操作未完成，不是另一個 Git 狀態。`UNKNOWN` 是觀測不足，禁止 destructive recovery／第二 writer 自動接手。

每個真實 Run 必須可追溯 baseline、writer、ownership、workspace facts；啟動、freeze、驗證、接受與接續前均依操作需要重新觀察。不能只在 Run creation 記一次 CLEAN。

Retry 保留失敗痕跡；Resume 先對賬；Switch Agent 轉移 ownership；Manual takeover 暫停自動 writer，Human 編輯後重新 capture；Rollback 是明確選定範圍的恢復行為，不以 reset --hard 作通用錯誤處理。

## 13. Workspace Strategy Recommendation

**推薦 B：Managed Git Worktree，限制在第一個已支援的 local Git repository envelope。** A 可作未來 advanced opt-in；C isolated clone 為必要時的相容／較強儲存隔離方案，不在 V1 同時支援全部。

| 比較 | A Direct User Workspace | B Managed Git Worktree | C Isolated clone／受控獨立 copy |
|---|---|---|---|
| Dirty safety | 最易碰到 Human staged/untracked，需重防護 | 原工作目錄保持原狀；dirty input 需顯式選入 | 原工作目錄保留；copy 要正確保留來源與排除規則 |
| Performance | 無 checkout setup | 共用 Git objects，仍需 checkout/build | clone／複製成本較高，local clone可優化但須查隔離方式 |
| Disk | 最省 | 工作檔與依賴仍可重複，不等於零成本 | object/檔案重複較多 |
| Windows | 既有 cwd 相容最好 | path length、Unicode、locks、移動後 pointer repair 需測；本輪已有 metadata 例子 | 少 linked-worktree pointer 問題，仍有 path/lock/filter 問題 |
| Git complexity | index與Human操作直接競爭 | shared refs/git common dir、branch checkout限制、cleanup管理 | remote/branch與同步更複雜 |
| Agent compatibility | CLI通常容易指向現目錄，但仍需實測 | Executor 必須尊重 cwd；不能假定所有 agent 支援 worktree | 大多只需普通 repo，但credentials/hooks/config也需處理 |
| Manual takeover | 直接，容易與agent同時寫 | 打開指定受管目錄，明確移交 ownership | 打開clone，結果另匯入 |
| Retry | 容易疊加半成品與人類變更 | 可從固定 baseline/candidate 建乾淨重試 | 可重建但成本高 |
| Recovery | 不能輕易捨棄 workspace | 可保留失敗 worktree，對賬後另建；不是直接刪 | 可保留clone再建立新副本 |
| Candidate identity | 可做，但 snapshot 易受外部編輯競爭 | 較容易 quiesce／capture，仍需 hash checks | 較易隔離，仍需證明 source snapshot |
| Acceptance | 與使用者未提交工作混合風險最高 | acceptance 與套用回原分支分離，明確展示 candidate | 類似B，需輸出patch/commit傳回 |
| Mental model | 「就在我正在編輯的地方改」 | 「PolyNexus 建一份工作副本，我接受其中變更」 | 「另複製一個專案」，同步成本較顯著 |

Git worktree 共用 repository data，具有各自 HEAD/index；其官方工具提供 move/repair/prune，但 linked worktree 與 submodule 支援有額外限制。這些能力不能推論為 OS 安全隔離。[Git worktree documentation](https://git-scm.com/docs/git-worktree)

推薦 pilot policy：原 workspace dirty 時預設 **不帶入**；UI 說明「從哪個 committed baseline 建立工作副本」。若任務依賴 dirty changes，要求明確選取並固定 input snapshot，或由 Human 自行建立所需 checkpoint；不得默默丟棄或把所有未追蹤檔案複製進去。

Worktree 中的 Agent 若與 Core 同 OS 權限，仍可能操作共用 `.git`、其他路徑或 process。需要 hostile-code containment 的場景應另評估不同 OS principal／sandbox／VM，不以 B 的選擇宣稱已滿足。V1 compatibility preflight 明確列 supported／unsupported；不把所有特殊 repo 都推給第一 vertical。

## 14. Source-of-Truth Boundary

| 權威 | 擁有什麼 | 不擁有什麼 |
|---|---|---|
| Git | committed code/tree/history、revision identity | Task acceptance、外部 evidence、尚未保存的工作目錄 bytes |
| PolyNexus durable core | Task/Run intent與lifecycle、Context refs、workspace observations、artifact identity、verification、Human decision、recovery/handoff facts | 不改寫 Git 成為第二個 source-control system |
| Artifact storage／manifest | 固定 Candidate與證據內容；可校验與取回 | 不因存有一段 PASS log 就成為可信 certification |
| Provider | execution session及其私有能力 | canonical Project/Task identity、唯一工作歷史、最終接受權 |
| Human | scope、risk acceptance、明確成果接受與治理決策 | 不能以自然語言將不存在的 tool execution 變成 verified fact |

DB記錄與Git/workspace觀測不一致時，保留兩者事實並標示需對賬，不武斷以其中一邊覆寫另一邊。Acceptance 必須能回指当時 exact Candidate 與 evidence snapshot，而不是查現在 branch tip。

## 15. Provider Independence Definition

Architecture invariant：vendor-specific session/event/CLI/auth behavior 留在 adapter/driver，Core 保存 PolyNexus identity、intent、evidence 與決策。模型與執行器更強時可替換，避免重寫 Task／Acceptance。

產品證明分級：

- **設計可替換**：有 normalized contract；目前至少具此基礎，不代表真實 executor 可用。
- **單 executor 閉環成立**：一個 real executor 完成 B01＋failure/recovery 及 Human acceptance；仍不宣稱跨 executor 已驗證。
- **跨 executor 已驗證**：第二種不同 executor 共用 Task/Run/Context/Candidate/Evidence/Acceptance，完成 B06；無新增 provider-specific Core truth。

不為預想的十種 provider 預先建立最小共同能力平台。capability 可不同，unsupported 顯示清楚；不能 silent reference fallback，也不能為統一介面把未知 usage/cancel/resume 假裝支援。

Red-Team：若所有實際客戶只用單一 provider，provider abstraction 的維護成本可能高於切換收益。V1 僅保留窄邊界，等第二 executor 的可量測需求再擴展；公司值得掌握的是成果／決策與恢復的可攜性，不是複刻每家 session 功能。

## 16. Workflow Minimum Real Execution Scope

保留 YAML、JSON Schema、canonical model 與 fixed V1 vocabulary。**Definition accepted ≠ node side effect implemented**；C8 的 reference execution 不能代替實際 TOOL／Human gate。

| MINIMUM_REAL_NODE_SET | 第一 vertical 必須具備的實際語意 |
|---|---|
| CONTEXT | 固定適用 goal/scope/AC/context references，檢查必要資訊與 freshness |
| AI_TASK | 透過共同 runtime boundary 啟動 real executor、指定受管 workspace，監測與停止，保留來源 |
| TOOL | 對 fixed candidate 執行 required deterministic checks，記錄 exit/timeout/artifacts；禁止 writer自行宣告toolPASS |
| EVIDENCE_CHECK | 判斷 required evidence 完整、可信、對應候選且結果合格；hardFAIL fail closed |
| HUMAN_GATE | 暫停等待可信 Human action，綁 candidate/evidence snapshot；Reject/Accept留下獨立歷史 |

**DEFERRED_NODE_SET：PARALLEL_AI、CROSS_REVIEW、SYNTHESIS、CONDITION 的完整真實 orchestration semantics。** Independent verification 可以由可信 TOOL／Human review 完成，不必先做多 Agent cross-review。結果摘要可以是普通 projection，不必啟用 SYNTHESIS agent node。

Candidate capture、workspace claim/release與reconciliation 是共用 Core 生命周期操作；不為它們立即新增 workflow node type。Retry 可由明確 user command 創新 Run，不先擴充循環／動態路由 language。未實作 node 在真實執行入口應拒絕或明確 unsupported，不能吞掉後回 COMPLETED。

## 17. External CI Evidence Policy

| 最低要求 | LOCAL_TOOL_EVIDENCE | EXTERNAL_CI_EVIDENCE |
|---|---|---|
| Target binding | materialized Candidate hash、baseline/tree、test target；前後確認未變更 | repository identity、實際 checked-out tree/revision與Candidate內容對應；不只branch名 |
| Producer trust | 受控 runner／observer，Agent沒有核發trustedPASS權限 | 受信任 CI endpoint/API或可驗證attestation；不要採信任意上傳JSON／webhook字串 |
| Oracle trust | 版本化命令、保護的required checks；writer更改tests需review | workflow/config/test revision、執行權限與來源；fork PR不自動具相同trust |
| Provenance | run/check、command、env、time、exit、logs/artifact hashes | CI run/job/attempt、workflow版本、trigger/source、runner環境、outcome與artifact來源/hash |
| Integrity | artifact bytes/hash可核對；輸出限權收集 | authenticated retrieval或簽章驗證依產品policy；保留可稽核來源與必要bytes |
| Applicability | criteria/context/testspec與candidate相符 | 同左；PR merge commit與head可能不同，需檢查實際tree而非假定等價 |
| Failure | missing/error/timeout/stale不能PASS | rerun、cancel、partial jobs、expired artifacts必須顯式處理 |

CI 驗證 integration merge tree 時，可產生「該 integration tree」的 evidence；若與 Candidate A 不同，不能直接授予 A 的 exact-tree certification。可以另有明確的 integration claim／Candidate，但不隱藏此差異。

V1 可先完成 local evidence；external importer 的工程時機可 NEXT。架構不得假定所有 trusted evidence 必須由 PolyNexus 親自執行，因此不用自己建 CI 平台。對外來源細節由 provider-specific importer 處理，共同 evidence semantics 不變。

## 18. Human Acceptance Minimum Boundary

推薦 V1 baseline：**local-personal，一位已配對的本機 Human 使用者**。這是最小 trust scope，不是 Enterprise IAM，也不是多使用者可靠 attribution。

最低 decision record：Candidate ID、evidence-set／verification snapshot、action（Accept/Reject）、principal reference、timestamp、reason code／optional note、decision id與防重送關聯。Accept 顯示當時缺口；Reject 可有選填說明。Exception/Override 若未被批准，V1 不提供入口。

最低邊界：

1. 明確 UI／受信任本機 human channel 的單次行為，不能把 chat裡的「看起來可以」或 Agent payload 當 authorization。
2. Human action 與 Agent/executor 一般 credentials 分離；server 驗證 exact candidate/evidence view、origin/CSRF與nonce/expiry/replay等適用防護。
3. Common Core API token 只證明 client 知道 token，不證明真人在場。Pairing 也不能單獨提供強 user-presence attestation。
4. 若 threat model 要抵抗同 OS 使用者下任意惡意 process，需更強 OS／authenticator／privilege boundary；本輪不假裝已具備。Gate 2 選具體機制，Human 先確認可接受的 pilot信任範圍。
5. 保留 D11 現有 fail-closed 行為；只有經正式批准的 contract變更後才能讓可信 Human decision 推進，不以 local-personal為理由移除gate。

推薦 **不在首個 vertical 提供 Override**。未來若允許接受已知風險，記成例外決策與原始FAIL，不能更改 tool result／VERIFIED。Small-team若要多人可追責接受，必須再有 per-person identity、授權、decision attribution；不能共用token後將actor字串當證據。

## 19. Startup / Onboarding Gate

| 使用者概念 | Working Product Gate 必需 | 可後續產品化 |
|---|---|---|
| SETUP | 清楚 prerequisites／supported executor／DB位置；依 Alembic authority 初始化／升級；不以create_all冒充migration | 安裝精靈、多OS正式installer |
| START | 單一可理解入口，例如 `scripts/start_dev.ps1`；啟DB readiness→Core→Web→health；可重複執行且辨別已啟動／port conflict | background service、自動更新 |
| HEALTH | 分清 Core alive、schema ready、Web pairing、executor ready；未登入provider不能顯示ready | 長期support bundle／telemetry服務 |
| STOP | 停止本次啟動的服務；active Run需明確處理、保存狀態；不殺所有同名python/node程序 | tray與系統服務管理 |
| RESET | 清楚區分重設client pairing／app data／demo data；預設不動使用者repository；破壞性reset需明確範圍與確認 | 一鍵修復多種環境 |
| START_HERE | 從全新使用者視角走到第一項bugfix，遇到缺依賴／auth／port／DB錯誤有可行處置 | 完整產品教學與多persona文件 |

Startup script 是串接入口，不負責繞過安全或自動接受migration風險。Fresh profile + supported environment能完成B01，才算onboarding gate成立；unit tests檢查script存在不夠。

## 20. Benchmark B01–B10 Review

共同量測單位是 **accepted candidate／失敗任務結果**，不是 Run count。每個 benchmark固定 fixture baseline、Goal/Scope/AC、允許修改範圍、可信oracle、期望失敗路徑、保存 artifacts；不能在 writer看完答案後用同一題評估推理成效。

| Case | Review／必要修訂 | 驗證產品能力 | 時機／成功標準 |
|---|---|---|---|
| B01 Simple Python bug fix | 保留；小型可重現回歸，另有未提供給writer的oracle | 全閉環、fixedcandidate、tests/evidence、Humanaccept/history | 首個pilotgate；exactcandidate通過requiredchecks且明確接受 |
| B02 Multi-file refactor | 保留；先固定behavior invariant與允許範圍，不用主觀「clean code」當PASS | 多檔change capture、scope控制、regression evidence | NEXT；無漏檔，行為守恆，由可信測試證明 |
| B03 Frontend + Backend API change | 保留；加schema/client一致、必要browser/API contract checks | 跨層context、artifact與驗證組合 | NEXT；不是前後端unit各自綠燈就算journey成功 |
| B04 Failing test repair | 修改：區分產品bug／testbug；不能刪assertion或skip騙過 | oracle保護、criteria fidelity、review catches weakened tests | Pilot；若改test需獨立oracle支撐，證據保留前後差異 |
| B05 Agent / process crash recovery | 擴為executor crash、Core restart、cancel/timeout後子process殘留 | durable lifecycle、ownership、no duplicatewriter、recovery | Pilot；未知狀態不重派，明確恢復或安全停止；不要求每次native resume |
| B06 Agent A→B handoff | 保留但必須sequential；session消失仍可接續 | context/workcontinuity、provider independence、provenance | 第二executor proof；不阻塞第一real executor閉環 |
| B07 Reviewer catches false implementation | 加「改錯路徑／自稱成功／弱化測試」固定陷阱 | independentoracle、falseacceptance防護、claim/evidence分離 | Pilot；hardFAIL／缺證據不可被AI或Humangate自動洗成VERIFIED |
| B08 Provider unavailable | 區分launch前不可用、執行中失聯；禁止silentreferencefallback | readiness、boundedfailure、honestUX、保全task | Pilot；保留失敗原因，提供retry／明確改route，無假成功 |
| B09 Incomplete/stale context | 加AC版本改變、baseline漂移、missingartifact | freshness、applicability、safehandoff | Pilot；顯示blocked或重新固定版本；不接受舊evidence套新需求 |
| B10 Dirty workspace recovery | 包含staged/unstaged/untracked、人類並行編輯、conflict | dirtysafety、ownership、capture／manualtakeover | Pilot；原Humanbytes/staging不被破壞，候選來源清楚，未知不自動reset |

每項必須驗證真實 side effects／未发生的禁止side effects：實際repo diff、process狀態、artifact bytes、DB/history。Contract permutations仍有用，但不能取代這組scenario evidence。

## 21. Pilot KPI / Comparison Design

### BASELINE_COMPARISON_METHOD

比較 **Direct Agent + Git + CI** 與 **PolyNexus-managed workflow**。同一executor/model版本、相近環境與tests、相同AC與接受標準、相同工具權限／成本口徑；差別在管理流程。不能讓直接組無CI／review而PN組有，然後宣稱管理更可靠。

採配對的等難度不同任務、隨機分配／交叉平衡操作順序，避免同一人先修過同一bug的學習效應。記錄task難度與participant熟悉度；首次setup成本單列，也報攤提後成本。Reviewer盡可能不知道是哪一組，兩組都用相同hidden oracle與缺陷觀察窗口。

建議先做5–10題instrumentation dry run，再做每組至少約20–30個有代表性的task attempts作初步pilot；這是可行性建議，不是統計power保證。依變異与錯誤風險調整樣本；critical安全缺陷不靠平均分掩蓋。成本、vendor/model版本變動、未完成任務均保留，不能只分析成功樣本。

| KPI | 定義／分母與解讀 |
|---|---|
| Time to Accepted Change | Task開始到Human接受的walltime，含等待／retry；未接受者報completion率與censored duration，不能刪除 |
| Human Active Minutes | 設定、context整理、監測、review、手動修復、接受等實際人工作業時間；idle agenttime另計 |
| First-pass Acceptance | 第一個提交供驗證的candidate即通過requiredchecks並被接受的task比例；不是第一RunCOMPLETED比例 |
| Recovery Success Rate | 預先定義可恢復事件中，在時間預算內保全workspace並接續／安全完成的比例；按crash/provider/dirty分層 |
| Evidence Completeness | Required evidence項目中具有效binding/provenance且可取回者比例；MISSING/SKIP不可算完整PASS；亦報task-level全滿比例 |
| False Acceptance / Escaped Defects | 被接受但獨立oracle／固定觀察窗發現違反AC者／acceptedtasks；記嚴重度、不要只報零樣本事故 |
| Workspace Integrity Incidents | 非授權覆寫、遺失staging/untracked、雙writer、無法辨識baseline等件數／tasks與writerhours |
| Cost per Accepted Task | 全部attempts（含失敗）的provider/compute/CI費用，加分列human與運維成本，除以acceptedtasks；零接受時報不可計算非0 |
| Voluntary Repeat Usage | 非強制期間有可選擇任務的使用者，再次自行選PN的比例與原因；不以自動Runcount代理 |

初步go假設可設定：Human Active Minutes下降約20%，且Time to Accepted Change不明顯惡化、evidence完整度提高、安全指標不劣於直接組。這些是**待pilot校準的門檻建議，不是已驗證成效**；同時報median／tail／分佈與不確定性，不僅平均值。

核心資產的反證：

- Provider Independence：若無實際切換需求、adapter維護費高，維持窄邊界即可，不擴平台。
- Cross-Agent Continuity：若整理package比重新告訴Agent更慢且無可靠性提升，縮成export／recovery助手。
- Evidence/Acceptance：若現有Git+CI+review同樣可靠更簡單，差異不成立；需要證明跨工具追溯與減少falseacceptance的收益。
- Recovery：若罕見且自動化恢復增加workspace風險，優先可靠診斷與Human takeover，不承諾無人自癒。
- Company-owned State：只有可匯出、可還原、refs不失效且使用者真正需要時才有價值；否則只是第二份維護負擔。

**Pivot**：縮成evidence/acceptance層、workspace recovery工具或現有平台integration，若其中一項可證明價值而完整orchestration無法。

**No-Go／暫停擴張**：多輪修正後仍無human time／可靠性優勢、使用者不自願重用、營運成本高於收益，或出現不可接受的falseacceptance／workspace破壞且無可行隔離方案。Agent+Git+CI勝出必須被允許，不能因已投入就擴大scope。

## 22. Decisions Still Requiring Human Approval

只剩以下三項**產品／治理**決策阻塞Gate 2；欄位編碼、DB形式、process library、具體auth機制、provider品牌、WAL調校都不是本輪要Human選的工程細節。

| ID | 需要採納的具體決策 | 推薦值 | 為何阻塞Gate 2 |
|---|---|---|---|
| HD-1 | Canonical baseline與未納入工作邊界 | 採f34完整SHA為設計基線；本機dirty／governance／Phase A分支保留在外，不整批合併；Gate1/1.5作reviewoverlay | 不確認就會對不同版本／衝突規格設計；批准不等於授權覆寫或commit/push |
| HD-2 | 第一pilot的workspace與信任產品範圍 | Local-personal、單一Human、singleactivewriter、managedGitworktree；原dirtyworkspace不默認帶入；不宣稱抵抗同OSprincipal惡意程式或small-team attribution | 直接決定ownership、acceptanceprincipal與recovery設計；目前H11未freeze，H17把personal/small-team合在一起 |
| HD-3 | 成果／驗證／接受語意修正及D11演進方向 | 採H02–H06修正版：先freezecandidate、evidence另成snapshot、verification綁候選、Humanaccept分離；首版不提供override；允許Gate2提出可信HumanGate的正式contract變更方案 | 這是高耦合identity與gate語意；現有frozen邊界不能由Reviewer自行改寫。此批准僅供規劃，非現在修改ADR或實作 |

其他H01–H18的ACCEPT／MODIFY是可一併review的推薦結論；沒有額外隱藏approval gate。若Human否決其中一項，回到該項收斂即可，不需要重做Gate1。

## 23. Gate 2 Entry Criteria

| Entry criterion | 本輪狀態 |
|---|---|
| exact baseline可定位，remote已更新查驗、lineage清楚 | 已完成技術查明；f34推薦待HD-1採納 |
| 本機有效工作不丟失，未納入內容有disposition | 已盤點並保留；不以清理dirtytree為前提 |
| Persona／realvertical與non-goals可收斂 | 建議已成熟：developer/QA、小bugfix＋failure/retry；待Humanreview總體方向 |
| Candidate／verification／acceptance邊界明確 | 本報告已給具體修正版；HD-3待採納 |
| Workspace／principal／trust範圍明確 | B worktree＋local-personal推薦；HD-2待採納 |
| StabilityP0與WorkingProductP0分開 | 已完成；WAL未當成獨立必要P0 |
| TestArchitecture以產品scenario為主、pilot有外部基準 | 已定義B01–B10與DirectAgent+Git+CI比較；沒有執行或宣稱PASS |
| 正式規格與新目標的衝突被承認 | 已列；Scope/ADR/PRD未改、未freeze新架構 |

Gate 2 的入口不要求先修完P0，也不要求先有第二provider或small-teamIAM；那些是設計／交付工作，不能倒置成規劃前提。

本輪不附 `GATE_2_INPUT_BASELINE`，因尚無足夠Human-confirmed的新基線可冒稱正式輸入。HD-1～HD-3確認後，才把已採納項目整理成該輸入，並開始Target Architecture Planning。

**最終裁決：NEED_MORE_HUMAN_DECISIONS。**

本Gate到此停止，等待Human review；不啟動Target Architecture implementation。
