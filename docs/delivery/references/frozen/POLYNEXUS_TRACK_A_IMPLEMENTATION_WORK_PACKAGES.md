# PolyNexus Track A Implementation Work Packages

- 日期：2026-09-10。
- Authority：[Architecture Freeze Record](POLYNEXUS_TRACK_A_V1_ARCHITECTURE_FREEZE_RECORD.md)；[Formal Contract / ADR Change Plan](POLYNEXUS_FORMAL_CONTRACT_ADR_CHANGE_PLAN.md)；Human 已 Frozen 的[REV1](GATE_2_CONTRACT_ARCHITECTURE_PACKAGE_REV1.md)與 I-01–I-23。
- Canonical design/read SHA：`f34e6b29ae9e7326d1d44b9b03756b450809928f`。
- **PRODUCT_IMPLEMENTATION：HOLD。所有 WP 與 B01 目前[未執行]；本文件是 planning，不授權 S0、產品 code、schema、Git 或真實 executor 操作。**
- REV1 檔案 SHA-256：`ACB67374384BC2FEBFF0FF288D739DBA8C92AC93C8A709B43500FC5FA10ED1DE`。W3 固定 Golden Expected IDs 直接採 REV1 §3.5，不重新生成或更換權威。

## 1. 共用 execution / evidence / acceptance 規則

以下每個 WP 具自己的 18 個 required 欄位；本節補充共同限制，不能用它取代任何 WP 的實際 criteria。

1. Human 先批准本規劃，再另授權 exact implementation scope。Formal ADR 修改、schema migration、Git stage/commit/push、真實環境操作需符合各自 gate；Architecture Freeze 不是這些權限。
2. 使用已確認的安全 implementation lane／HEAD，不因 designbaseline 已批准就 checkout 或覆蓋 dirtytree。Expected File Areas 是定位／預期範圍，開工時形成 exact allowlist；新檔名可在已批准責任內決定。
3. 一個 activewriter；reviewer 不是 writer。Review／browser／product acceptance 依 bounded criteria 與 actual evidence，不以多 Agent 數量充當獨立性。此文件不派出任何 Agent 或 Runtime。
4. 每個 command 記錄 exact command/argv、cwd、時間、實際 exitcode／signal、boundedoutput、target/fixture/版本、產物 hash。APIstatus 不是 OSexit；不存在的 exit 標 UNKNOWN。驗證 runnerexit0 與其注入的失敗工具 exit 分開保存。
5. Tests 先 targeted→affectedregression→必要 lint/typecheck/build/browser/real process。不預先跑整庫；negativefault 實際非 0 是證據，不能偽造為 0。無關 optional SKIPPED 與 mandatory SKIPPED 分開；mandatory 缺失不得完成。
6. Concrete test commands 在實作後以真實存在的 test paths/runner 填入 evidence；本文件不捏造尚未建立的測試檔或宣稱已執行。本輪各 WP 的 actual commands/outputs/exitcodes 皆[未執行]，不是 PASS。
7. Rollback 保護 Humanbytes、immutable Candidate／Evidence／decision history；不以 reset/discard/清理 untracked 解決問題。Schema 改動先 backup 與 migration/restore rehearsal，無損性不成立則明示。
8. 完成 WP 只接受其 bounded scope；B01 仍需独立 real product acceptance 與 Human 接受。Simulator/mock 只能支持相應 unit/contractlayer。

### Evidence receipt 最低欄位（每 WP 必要）

TASK_ID、reviewed code/checkpoint SHA＋dirtyallowlist、WRITER/REVIEWER、test/commandID、exact command、cwd/workspace/generation/Run/Candidate refs（適用者）、runtime/adapter/model 可見版本、start/end、actual exit/signal/outcome、actual outputref/hash、actual repo diff 及 file hash、SKIPPED 理由/影響、known limitations、review verdict。任何含 secret 資料以安全 reference／redaction 保存，不曝光值。

### Dependency map

```text
Human review of these planning documents
 → formal-document synchronization authorization / exact M-IDENTITY + M-HUMAN approval
 → separate implementation authorization
 → S0 → W1 → W2 → W3 → W4 → W5 → W6 → B01 Independent Acceptance
 → Human Working Product Acceptance (only if evidence satisfies criteria)
```

M-HUMAN 如果 S0 新 Human authority 需要則提前；W5 必須已正式批准。M-EXECUTION 目前 NOT REQUIRED / IMPLEMENTATION MAPPING ONLY；W2 若證明必須改 public contract 再走 ChangeControl。REST/durablemonitor 融入各 WP，WebSocket 不阻擋 W1–W6。N1 full selected-task portability 不阻擋 B01；W6 的 P0acceptedpackage 不可省略。

## 2. Work Packages

### S0 — Stability Foundation

**STATUS：[未執行] / IMPLEMENTATION HOLD**

**TASK ID**

PN-TA-S0

**OBJECTIVE**

讓 Core 具備正確 SQLite FK、可恢復 CREATED intent、UI/Core pairing foundation 與 START/HEALTH 最小基礎。

**WHY**

既有穩定性缺口會阻擋第一個 real outcome；先處理必要 S0，不能以產品規劃或舊 tests 綠燈跳過。

**PREREQUISITES**

本次規劃獲 Human review，另有 S0 exact implementation 授權；確認安全實作 lane、HEAD 及保留 dirty 工作。若 pairing 子項新增 Human principal/grant/session，formal M-HUMAN 須先批准；既有 client bootstrap mapping 不得臨時提供 Accept 權。

**EXACT SCOPE**

修正以 dialect/connection 判斷 SQLite 並於每條連線啟用 FK；建立既有 DB 的 backup-first foreign_key_check 與 application relation audit 策略。處理 API create 未 execute 後 restart，不替未啟動 CREATED 假造 binding。UI/Core 正確連接／pairing foundation；START 及分層 HEALTH（schema、Core、Web/client、executor readiness 分開）。只按 approvedmigrationauthority 準備 DB；本 WP 不對真實使用者 DB 自動 repair。

**OUT OF SCOPE**

WAL 強制切換、換 DB、完整 installer、自動更新、Human Accept endpoint、real executor 品牌選擇、Candidate/W1 模型、大規模 refactor。

**ALLOWED ARCHITECTURE AREAS**

Persistence initialization、startup/reconciliation、既有 auth client wiring、local startup scripts 與 health；保留 Run semantics 與 D11-C。

**EXPECTED FILE AREAS**

services/core/src/polynexus_core/persistence/database.py；runtime/reconciliation.py；api/dependencies.py、api/health.py、app.py；apps/web/src/App.tsx 及 client 配置；scripts/start_core.ps1、scripts/start_web.ps1，必要時新增 scripts/start_dev.ps1；相關 Core/Web 測試。這是 expected areas，非 blanket 寫入授權。

**ARCHITECTURE INVARIANTS**

I-12、I-13、I-17、I-20、I-21、I-23；I-01/15 保護現工作。

**POSITIVE TESTS**

新建及 pool reused SQLite 連線 FK=ON，實際不合法 FK 寫入被拒絕；乾淨 audit 報告。正常 CreateRun→不 execute→Core restart 仍可用；既有 validboundrunning state 依契約 reconcile。Fresh client 從 START 看到分層 health，正確授權可查 API。

**NEGATIVE TESTS**

非 SQLite/普通*.db 路徑不以 filename 誤判；含 dangling reference fixture 報 audit failure，禁止靜默刪資料。Unbound CREATED 不得 crash 全服務，unknown running 不得 duplicate launch。無/錯 token 仍拒絕；port collision、schema 非 head、missing service 可診斷而非顯示 ready。

**FAIL-CLOSED CONDITIONS**

Schema/integrity 不可信時不接受 write/launch；未知 running scope 隔離；pairing 未完成不得開 protectedAPI；audit 不能作自動資料刪除依據。

**ACTUAL EXIT CODE REQUIREMENT**

Targeted Core pytest、affected Web test/typecheck/build 與 startup / health 命令須記 exact command 與 actual exit code。預期 invalid insert/audit 負例的非 0 或 exception 另記；parent 測試通過不把該 failure 改寫 PASS。未執行命令/SKIPPED 不算完成。

**EVIDENCE REQUIREMENT**

連線 PRAGMA 及 invalid insert 實測、audit fixture 前後 hash、API create/status 與 restart error/result、process/service health、pairing 拒絕/成功、targeted test outputs。不要在 log 記 token／DBsecret。

**ROLLBACK / RECOVERY**

先保存安全 DB/artifact snapshot 與設定；只回退本 WPallowlist 變更。資料異常先 read-only audit、Human 決定 repair；restart/cancel 未知狀態保留，不 reset 原 repo 或刪 Run。

**DEPENDENCIES**

S0 必要穩定性結果是 W1/W2 正式 real vertical 前置；新 Human pairing authority 依 formal M-HUMAN gate，不能循環等待 W5 實作。

**COMPLETION CRITERIA**

各 S0 必要項有 fresh positive/negative evidence，無 auth 放寬或 fakebinding；必要 checks 無未解釋 skip；已知 blockers 記錄。不能把 S0 完成說成 Working Product 完成。

**INDEPENDENT ACCEPTANCE GATE**

非 writer reviewer 以新 evidence 重查 FK、create/restart、unauthorized client 及 healthfailure path；涉及 UI 由獨立 browser journey 驗證。Human 只在該 bounded scope 接受後決定下一 WP 授權。

### W1 — Repository + Workspace Foundation

**STATUS：[未執行] / IMPLEMENTATION HOLD**

**TASK ID**

PN-TA-W1

**OBJECTIVE**

建立 repository/input/WorkGenerationRef/control revision 與 managed worktree ownership，保全 Human dirtyworkspace。

**WHY**

沒有 exact generation 與安全 ownership，Retry/Abort 或新 command 會造成重複 writer、錯輪取消或資料覆寫。

**PREREQUISITES**

S0 必要 gate 通過；formal M-IDENTITY/OUTCOME wording 已批准；W1exact scope 實作授權、受管測試 repo 與原 Human repo 隔離。

**EXACT SCOPE**

Logical repository binding、固定 baseline 與 Human 明選 dirty input snapshot；WorkGenerationRef=(TaskID,generation_revision)與 control revision；Begin/Retry 配發及 predecessor；Run/publication 關聯。Managed Git Worktree、四軸 facts、single writer、ownership fence、partialsetup/reconciliation。建立 generation-level writer-lineage claim：不限於 commandid，同一 generation 不得因不同 command 或 API 入口產生另一條 unrelated writer lineage。

**OUT OF SCOPE**

Attempt Aggregate、parallelcoding、多 repo 並行調度、OS sandbox、安全承諾擴張、自动 commit/reset/prune、real provider 集成、Candidategolden 實作。

**ALLOWED ARCHITECTURE AREAS**

Task/Run/domain references、Repository services、workspace/control facts、transaction/CAS、受控 Gitworktree 與 APIcommand boundary。

**EXPECTED FILE AREAS**

Core domain/models.py 及相關 typed ref 區域、persistence/models.py/repository.py 及授權的 Alembic revision；execution_service.py／api/runs.py 與新增最小 workspace services；frontendrepository/input UI 及 tests。禁止修改未批准 RuntimeAdapter/RuntimeBindingSnapshotpublic contract。

**ARCHITECTURE INVARIANTS**

I-02、I-03、I-04、I-14、I-15、I-19、I-20、I-21、I-23；same-generation lineage 為本輪 Human 明示 criterion。

**POSITIVE TESTS**

Human 選 baseline/input 後建立 managed worktree，原 staged/unstaged/untracked 完全不變。g1/R1 失敗安全釋放→Retry 建立 g2/R2；新 generation 有新 ref 與 input/provenance；同 command 重送回原 receipt。

**NEGATIVE TESTS**

必測 g1→Retry g2→late Abort(g1)：R2 仍存活／未被取消、g2control/ownership 不受變動。相同 WorkGenerationRef 換 command_id、不同 start 入口或並發 Create/Start，最多一條 writer lineage 可 claim/launch；其他明確 conflict，不靠 simultaneouswriterlock 釋放後再開第二條。尚未 claimed 的多 intent 也只能讓一條取得 lineage。Foreign Run/generation、stale revision、PID/lease 未知、dirty input 未選、path escape、partialworktree 失敗均拒絕危險動作。

**FAIL-CLOSED CONDITIONS**

Run↔generation↔workspace 不一致、claim/release 不確定、generation 已 aborted、既有 writer-lineage 已 claim 而請求不屬其合法 resume/recovery 時不 launch。真正新 writer retry 需新 generation；不能換 command_id 繞過。

**ACTUAL EXIT CODE REQUIREMENT**

Targeted domain/repository/API concurrency tests 与 Git/OS integration 命令逐筆 actual exit；fault/timeoutcommand 的 exit 與測試 runnerexit 分開。關鍵 lateAbort 與 lineage 負例[未執行]/SKIPPED 即不能 W1PASS。

**EVIDENCE REQUIREMENT**

g1/g2/Run/claim/control revision 與 commandreceipts，並發 launch 計数及實際 process/檔案副作用，Git HEAD/index/staged/untracked 前後 diff/hash、worktree scope、partialfailurefacts。輸出不包含未授權 Human 檔案內容。

**ROLLBACK / RECOVERY**

只處理本 WP 建立且已確認 owner 安全停止的 managed fixture；保留 partial state/receipts。資料遷移先 backup，legacy 不猜 ref；不清除 Human 目錄或整批 prune。

**DEPENDENCIES**

W2 必需 W1authoritative workspace/control mapping；W3 以其 snapshots/provenance 為來源。Retry 新 generation 不能繞過舊 processreconcile。

**COMPLETION CRITERIA**

上述 positive/negative 含 different commandlineage 約束都有實際證據；Human workspace 保全可驗；新 refs 可重啟讀回。無 parallelwriter 或第二 truth。

**INDEPENDENT ACCEPTANCE GATE**

Independent reviewer 用不同 command_id 及競爭入口重現 duplicate-lineage 企圖、lateAbort 並核對真實 side effects 與 DBfacts；browser 確認 dirty input 明選。Writer 文字自評不替代。

### W2 — Real Executor

**STATUS：[未執行] / IMPLEMENTATION HOLD**

**TASK ID**

PN-TA-W2

**OBJECTIVE**

依品牌中立 feasibility 選出並接上一個可控制、可觀測、真正修改 repository 的 executor。

**WHY**

目前 Real Executor NOT YET VERIFIED；只有真實 launch/write/cleanup 證據才能建立 Working Product 前提。

**PREREQUISITES**

S0 必要項及 W1 獨立接受；W2 實作/真實 executor 測試明確授權；可用 runtime/credential 由 Human 授權範圍提供。先完成 M-EXECUTION mapping 檢查；若證明需改 public contract，先取得正式 amendment 批准。

**EXACT SCOPE**

Capability declaration＋當下 readiness＋實测三層；cwd/control、input/context、launch、actual modification、normalized output/status/result、cancel/timeout/child-process cleanup、auth ownership、version/model visibility/provenance、bounded failure taxonomy。保留 binding-first、singlelineage；readiness/Doctor 不偷偷 launch。

**OUT OF SCOPE**

先指定品牌、大量 adapters、以 simulator 充當 PASS、native 跨 provider session 移植、假 usage 精確值、silentfallback、public contract 未授權改動。

**ALLOWED ARCHITECTURE AREAS**

RuntimeAdapter/Driver implementation、registry private composition、RunSupervisor/ExecutionService 內既有契約 mapping、control observation／reconciliation、secret boundary。

**EXPECTED FILE AREAS**

runtime/contracts.py 只作對照（無批准不改 public surface）；runtime/registry.py、supervisor.py、reconciliation.py、execution_service.py、selected adapter 實作與 conformance/real process tests；W1workspace resolver。具體 adapter 檔名在 feasibility 後選定，非預先品牌承諾。

**ARCHITECTURE INVARIANTS**

I-03、I-04、I-14、I-19、I-20、I-21、I-22、I-23 及 I-12credential 隔離。

**POSITIVE TESTS**

真實 executor 在指定 fixturecwd 取得 versionedinput/context，修改預期 source，Core 獨立觀察 diff/output/terminal。Humancancel 及 timeout 皆停止子孫 writer 並可安全釋放；native resume 不必支援。Adapter/provider/runtime/version/auth ownership 可追溯，unknown 資訊誠實標示。

**NEGATIVE TESTS**

Missingexecutable、auth required/expired、provider unavailable、wrong cwd、輸入截斷、permissiondenied、crash、outputlost、child/grandchild 背景寫入、filehandle 殘留、timeout/stop 競爭、Core crashlaunch window。無 fakehealth、無 referencefallback、無 PID reuse 誤認；觀測失聯不得當已 cleanup。

**FAIL-CLOSED CONDITIONS**

任何 mandatory feasibility 未通過即不入選；cleanup 未確認／scope 不符／auth 不可用不 launch 新 writer。若 mapping 需 public contract 變更先阻擋該部分而非藏進 prompt/metadata。

**ACTUAL EXIT CODE REQUIREMENT**

保存 actual executor argv/cwd/exit/signal、cancel/timeout/cleanup 子命令 exit 與測試 harnessexit。Provider 回覆文字不是 exit code。無法觀測則 UNKNOWN/ERROR，[待驗證]不得 PASS。Simulated unit 可支援測試但不能計為 real gate。

**EVIDENCE REQUIREMENT**

Capability matrix（exactversions/OS/time）、命令/輸出、source before/after hash＋Gitdiff、actual process tree 與 cleanup 後無繼續寫入／handle 證據、Run/binding/generation 映射、redactedfailure records。

**ROLLBACK / RECOVERY**

停所屬 process tree 並確認；不確定保留 recoveryrequired、不另 launch。撤回 selected adapter wiring 可恢復原行為但不得 silent 切 reference；保留 run/evidence/history，不 resetfixture 以掩蓋失敗。

**DEPENDENCIES**

W3/W4 依 W2 可證明 quiescence 与 realwrite；W6/B01 需要此 exact executor 通過實測。

**COMPLETION CRITERIA**

至少一個 real executor 通過 mandatorycapabilities 與 failure cases，observed truth 落地；並非整體 B01PASS。必要 real test 未跑不可用 conformance 替代。

**INDEPENDENT ACCEPTANCE GATE**

非 writer independently 重跑 realwrite、cwd、cancel、timeout 與 child cleanup；核對憑證與 controlprovenance，確認沒有 simulator 替身。Human 決定 boundedexecutoracceptance，不自動擴品牌。

### W3 — ChangeSet / Candidate / Artifact

**STATUS：[未執行] / IMPLEMENTATION HOLD**

**TASK ID**

PN-TA-W3

**OBJECTIVE**

以 Core-derived snapshots/changedmanifest 實現 Model B、immutableArtifact publication 與可重建 Candidate。

**WHY**

固定成果是 verification/acceptance/exiting 產品的共同 identity；自帶 manifest 或錯誤 hash 會破壞全部下游。

**PREREQUISITES**

W1authoritativeinput 與 W2quiescence 可用；formal M-IDENTITY 已批准；W3 實作授權。測試 expectedsource 固定 REV1 檔案 SHA 與§3.5，任何變更先 ChangeControl。

**EXACT SCOPE**

Core-derived Snapshot、path/bytes/mode 完整性與 ChangeSetdiff 推導、ChangeSetID/CandidateID、publication/provenance、blob/ref closure、FS/DBpublication 與 recovery、reconstruction；忠實實現 REV1canonical profile 與固定 expectedgoldens。

**OUT OF SCOPE**

讓 Agent/UI/Adapter/caller 決定 identitymanifest、displaydiffhash、重新生成 golden 權威、通用 artifact 平台、擴充 unsupportedLFS/submodule/symlink、安全 sandbox、完整 N1portability。

**ALLOWED ARCHITECTURE AREAS**

Domain value objects／Core capture services、ArtifactStore/repositories、approvedpersistentpublicationfacts、serialization、supportpolicy 與 targetedtests。

**EXPECTED FILE AREAS**

domain/models.py 附近或新 typedmanifestmodule、Core artifact/capture service、persistence/models.py/repository.py 與明確授權 Alembic 變更、artifact store、tests 新增 golden fixture/contract/reconstructioncases；REV1 檔案唯讀。

**ARCHITECTURE INVARIANTS**

I-05、I-06、I-07、I-09、I-15、I-18、I-21；generation/Run 不入 contentID。

**POSITIVE TESTS**

使用 REV1 §3.5 **原封不動固定 Golden Expected IDs**：G01/G02/G03/G04/G05/G06/G07/G08/G10/G11a/G11b/G12a/G12b；Core capture、snapshot 重新推導、package 重建後 capture 比對 same canonical bytes/IDs。UTF-8、Unicode、CRLF、empty、binary、mode、add/delete、pathordering、largeboundary 均覆蓋。

**NEGATIVE TESTS**

G09 casecollision 與 G12c 超限必拒絕；caller 偽造 manifest/op/before/size、missing/corrupt blob、path traversal、wrong mode、partial publish、capture 中來源變動、displaydiff 變化。不同 command/Run/generation 不改同內容 ID；requirements 改變新 Candidate，evidence 新增不改 Candidate。

**FAIL-CLOSED CONDITIONS**

任何 hash/size/ref/scope/canonical 問題不可 publish 或 eligible；來源未 quiescent 不可聲稱 immutable；golden 不符先定位原因，禁止讓 production 自生 expected 再驗自己。

**ACTUAL EXIT CODE REQUIREMENT**

Golden/serialization/store integration/reconstruction 命令需 actual exit0 並列 valid/negativecase 結果；faultinjection 子 exit 保留。G09/G12c 拒絕是預期 result，不是 goldenPASS 以外的真實產品 success；skip 任何 mandatoryvector 不完成。

**EVIDENCE REQUIREMENT**

唯讀 REV1 SHA 及§3.5literal fixture 來源、exactexpected/actualcanonicalbytes/hashes（不由同一 production 算法產 expected）、source/diff/manifest、partial publication 與 recovery、actual testoutputs。不重算取代已 FrozenExpected IDs。

**ROLLBACK / RECOVERY**

不原地改 immutable artifacts；未引用 partial 內容依明確保留 policy 處理，已引用 bytes 保持。Backup DB＋artifacts 相容 snapshot，legacy 無可信 candidate 不升格；無 lossyreset。

**DEPENDENCIES**

W4 exact Candidate、W5 decision view、W6/P0 source reconstruction 依 W3；reconstruction 底層可先測，完整 accepted package 在 W6。

**COMPLETION CRITERIA**

所有固定 valid/negativegoldens 通過、跨執行路徑 sameID、publication 故障後 truth 清楚且 content 可重建；無 caller-definedidentity 或自證 expected。

**INDEPENDENT ACCEPTANCE GATE**

Independent reviewer 從 FrozenREV1 取得 literal expected，比對 testsfixture 未被產物覆蓋；重跑 capture/rebuild/partialfailure，檢查 hashalgorithm/domainseparation 與 ref closure。

### W4 — Verification + Evidence

**STATUS：[未執行] / IMPLEMENTATION HOLD**

**TASK ID**

PN-TA-W4

**OBJECTIVE**

建立 exact Candidate 的 mandatory verification、oracle 保護與 trusted Evidence 收集，不混合 check 需求與結果。

**WHY**

Run 完成／Agent 宣称／一項 test 綠燈都不足以 Human Accept，optional SKIPPED 亦不應被錯判為整體 FAIL。

**PREREQUISITES**

W3immutable Candidate／publication 通過，W2 受控工具/程序邊界可用；formal M-IDENTITY 與 W4scope 已批准。

**EXACT SCOPE**

REQUIRED/OPTIONAL；APPLICABLE/NOT_APPLICABLE/UNRESOLVED；PASS/FAIL/ERROR/TIMEOUT/SKIPPED；MISSING/STALE/MISMATCH/UNTRUSTED 適用性；Claim/AC→required checks→EvidenceSet→VerificationRecord；exact Candidate/context/contract/policy/env 與 producer 綁定；B04/B07/B09。

**OUT OF SCOPE**

AI 投票覆寫 hardgate、Override、genericpolicyengine、provider-specificCore、externalCI 完整接入可 NEXT、跨 Candidate 自動 cachepromotion、所有 tests 強制 mandatory。

**ALLOWED ARCHITECTURE AREAS**

Existing Evidence/Finding/Artifact、workflows/gates 與 TOOL execution semantics、trusted runner/observer、verification publication 與 UI 結果顯示。

**EXPECTED FILE AREAS**

domain/enums.py/models.py 必要向後相容 extension、workflows/gates.py/execution.py、tool/evidence collector 及 persistence、API outputs、Webverification view、pytest/Vitest/必要 browsercases。不得自行改 fixednode vocabulary。

**ARCHITECTURE INVARIANTS**

I-05–I-10、I-12、I-20、I-21；特別 I-08 三種 check/validity 層分離。

**POSITIVE TESTS**

required applicable trustedfreshmatchingPASS 滿足該 check；optional SKIPPED/MISSING 不自動 FAIL；policy 明確 N/A 有 predicate/reason 並保留 originalrequirement；fixedCandidate 產 immutableEvidenceSet/VerificationRecord。必需 oracle 真實 catchbug。

**NEGATIVE TESTS**

Required FAIL/MISSING/ERROR/TIMEOUT/SKIPPED/STALE/MISMATCH/UNTRUSTED 與 UNRESOLVED 均不滿足；全部 required 被空轉不可 vacuousVERIFIED。Writer 刪/弱化 tests、偽造 TOOL_EVIDENCE、verifier 改 source、wrongCandidate、staleAC/policy、不同 CImergetree 不可升格；optional FAIL 若觸發獨立 mandatory blocking finding 依明確 policy 處理。

**FAIL-CLOSED CONDITIONS**

必需來源不可信／缺 ref／錯 hash／不適用不 VERIFIED；N/A 不能 writer 自稱豁免；無實際 exit 不可轉 PASS；verificationsource 變化先 newCandidate。

**ACTUAL EXIT CODE REQUIREMENT**

每個 required tool 保存 actual command/exit/signal/timeout；runnerpytest0 不取代 childtool 結果。Skipped 逐 check 明示 OPTIONAL 或 REQUIRED 與影響；無 reportedexit 即 UNKNOWN/ERROR，mandatory 不通過。

**EVIDENCE REQUIREMENT**

Versionedrequirements/policy/oracle、CandidateID/EvidenceSet/VerificationRecord、command/cwd/env/producer/time/exit、rawboundedoutputs 與 artifact hash；B04/B07/B09 實測。Importedclaim 與 trusted fact 明確分開。

**ROLLBACK / RECOVERY**

新 verification 追加不覆寫舊結果；policy 回退建立新 revision，舊 certification 適用性另評。Collector 失敗留 partial/missing，不補造 PASS；保留 Candidate 與失敗 log。

**DEPENDENCIES**

W5Accepteligibility 必須依 W4servertruth；W6/B01 以同一 verifier，不另建 demo 判斷。

**COMPLETION CRITERIA**

Mandatorytruthmatrix、oracle 防弱化與 B04/B07/B09 皆有正負證據；UI 顯示部分完成不冒充 verified；沒有 required invalid 被 accepteligibility 吞掉。

**INDEPENDENT ACCEPTANCE GATE**

Independent reviewer 使用 writer 未持有的可信 oracle／falseimplementationfixture 驗證；比對 Candidate 與 test target，審查 evidence trust 而非只查 status 字串。

### W5 — Human Decision / D11

**STATUS：[未執行] / IMPLEMENTATION HOLD**

**TASK ID**

PN-TA-W5

**OBJECTIVE**

在 Frozenlocal-personal 範圍提供可信 Human Accept/Reject 及 post-acceptance Revoke/Supersede，不降低 D11fail closed。

**WHY**

普通 loopbacktoken/actor 字串不證明 Human；沒有 exact view/replay/concurrency 保護就無法安全接受成果。

**PREREQUISITES**

**正式 M-HUMAN contract 已 Human 批准**；formal M-IDENTITY 已批准；W4eligibility 與 W3immutable artifacts 可用；W5exact implementation 授權。S0 配對 foundation 符合相同 contract。

**EXACT SCOPE**

A-LPprincipal/pairing、Human/Agentseparation、bounded/revocable sessions、short-liveddecisionchallenge、exact Candidate/Acceptance/Evidence/Verification/Policy view、CSRF/Origin、nonce/anti-replay/idempotency、append-onlyAcceptanceRecorded/Revoked/Superseded、preacceptReject、race/expiry/restart、D11-Cfallback、noOverride。

**OUT OF SCOPE**

EnterpriseIAM、smallteamattribution、hostile-same-OS 安全宣稱、硬體 attestation 必選、固定 TTL 或 restart 必須 re-pair、autoaccept、autoapply、改 tooloutcome。

**ALLOWED ARCHITECTURE AREAS**

Human-onlyauthentication/authorization/security storage、decision commandtransactions/repositories、existingHumanGateintegration、UIexplicitdecision/refresh/disposition/history。

**EXPECTED FILE AREAS**

api/dependencies.py 及 Human-specificauth/decision boundary、新最小 security/session 實作、decision persistence 與 approvedmigrations、workflows/gates.py、人類 decisionUI、Core/API/browser security/racetests；正式 ADR 不隨程式順手改。

**ARCHITECTURE INVARIANTS**

I-09–I-13、I-16、I-17、I-20、I-21。

**POSITIVE TESTS**

Human pairing 後對 exacteligibleview 接受並保存 receipt；尚未 accepted 者可 Reject 即使 verification 未完成；acceptedT1 後 Revoke/SupersedeT2 歷史保留。Expiredsession 重新取得可信 session 可查原 receipt；選定 persistent 或 re-pair 方案通過同安全/UX 門檻。

**NEGATIVE TESTS**

Agent token/selfpair/actorprefix、wrong/nullOrigin/Host/CSRF、rawAgentHTML/XSS、expired/reused nonce、不同 Candidate/action/session/view、同 key 異 payload；Accept/Reject/policy 競爭最多正確一方 commit。已 accepted 後 Reject/Reopen 拒絕；Revoke/Supersede 爭 sameAcceptance 與 replacement 失效/self/cycle；restart/clock 不得 reviveexpired/revokedgrant；required invalid 不得 Accept。

**FAIL-CLOSED CONDITIONS**

Auth 或 exact view 不能驗證即拒絕；nonce/decision/receipt transaction 不完整不可 accept。Persistentsecuritystate 不確定不恢復 authority。D11-C 留作 fallback，不讓 legacyevidence 自動可信。

**ACTUAL EXIT CODE REQUIREMENT**

Auth/API/race tests 及 realbrowser journey 記 exact commands/actual exit；HTTPstatus、transactionresult、session state 亦保存（不把 HTTP 當 process exit）。Security mandatory SKIPPED 不能 W5PASS；各測試 runnerexit0 不足以隱藏缺失負例。

**EVIDENCE REQUIREMENT**

Redactedprincipalscope／viewdigest／Candidate/Acceptance/Evidence/policyrefs、decision timestamps/revisions/receipts、races 真實 transaction 結果、browser routes/artifacts、expiry/restart 方案比較及 actual commands。禁止輸出 token/nonce/session 秘密。

**ROLLBACK / RECOVERY**

停用 Humanmutation 通道回 D11-Cfail closed，保留 append-onlydecisions；security restore 不恢復已撤銷權限；不刪 T1/T2 以回滾 UI 狀態。

**DEPENDENCIES**

W6/B01Human Accept 必須走 W5，不能手動 DB 更改或 AIapproval 替代。

**COMPLETION CRITERIA**

正式 contract 已批准且實作 scope 已授權；選定 session 方案通過 Security＋UX、exacteligibility 与全部必要 races；無 Override／權限混用／歷史覆寫。

**INDEPENDENT ACCEPTANCE GATE**

獨立 security/API reviewer 與非 writerbrowser 驗證；使用 Agent credential 實際攻擊 ordinaryendpoint／replay/races，確認只能 Humanchannel 決策。Human boundedacceptance 不等於 B01 產品驗收。

### W6 — Working Product Completion

**STATUS：[未執行] / IMPLEMENTATION HOLD**

**TASK ID**

PN-TA-W6

**OBJECTIVE**

串接第一個可用 Golden Path：accepted 成果取用、Humanworking copy、failure/retry 與 P0portable accepted package，加 START_HERE。

**WHY**

Accept 按鈕成功但無法使用/取回成果仍不是 Working Product；失敗後需保全 truth 與 Human 工作。

**PREREQUISITES**

S0 與 W1–W5 已獨立驗收；W6scope 授權；real executor/version 已通過 feasibility。沿用相同 Core、policies、identity 與 Human 通道。

**EXACT SCOPE**

OpenAcceptedManagedWorktree，開啟前驗 bytes/acceptancedisposition；TakeOverWorkspace 明確 ownership 轉移及 Working Copy label；failure→retry/recovery、RESTpolling/durable history；P0MinimalPortableAcceptedPackage 的 Task/AC/ChangeSet/Candidate/requiredsource/Evidence/Verification/Human Decision/manifesthashclosure；bundleverify 及空目錄 reconstruction；START_HERE 與 SETUP/START/HEALTH/STOP 安全 UX。

**OUT OF SCOPE**

Auto commit/merge/push/release/apply、N1 完整 selected-taskhistory/Continuation/fullartifact/environment/offlineUI/importnamespace、WebSocket 必先完成、通用 interchange、繞過任何 W5/verification。

**ALLOWED ARCHITECTURE AREAS**

Existingfrontendjourney、Corecommands/queries、workspaceconsumption/ownership、Artifact/P0exportservices、安全 reconstruction 工具、startup/onboardingdocs 與 tests。

**EXPECTED FILE AREAS**

apps/web/src/components/RunDetail.tsx、RunPreparation.tsx、CreateTaskForm.tsx 及 accepted/working copy/verification/history views；Coreoutputs/workspace/artifactexport/rebuild 區域；scripts/start_dev.ps1 或既有 startscripts；START_HERE 文件位置依 repo convention；E2E/P0tests。

**ARCHITECTURE INVARIANTS**

I-03、I-06、I-10–I-19、I-21–I-23。

**POSITIVE TESTS**

Freshsupportedsetup 完成真實 Golden Path；Human Accept 後 OpenAcceptedResult 可用；TakeOver 後立即顯示 Working Copy based on Accepted Candidate <ID>，新編輯不改舊 Candidate。至少一次 failure→safeRetry 新 generation 完成。P0 bundle 在無 providerprivate session／原 remote／runningCore 條件下 verify 並重建 exactaccepted source/IDs。

**NEGATIVE TESTS**

受管目錄漂移不能沿用 immutableAcceptedResult；原 Human dirty 不得 autoapply。缺必需 blob/ref、corrupt/oversize/traversal、secret 禁止輸出、wrongacceptancerecord 須 INCOMPLETE/reject；不可用 partialpack 冒充完整。Polling 掉線不改 RunFAILED；unknownwriter 不 takeover/retry；已撤銷 accepted 歷史不假裝 currentvalid。

**FAIL-CLOSED CONDITIONS**

Candidate/Acceptance/hash 不一致不顯示可信 accepted result；P0ref closure 不完整不標 portable；ownership／auth／policy 不確定不繼續寫或接受。NoOverride。

**ACTUAL EXIT CODE REQUIREMENT**

Golden Path/browser/Core/P0 verify/rebuild 命令逐筆 actual exit 與 outputs；支持的 P0 verify/reconstruct 須 exit0 且重新算 ID 相同。資料/路徑負例預期非 0 另列。真正 export/rebuild/browser 未跑不能用 unitgreen 完成。

**EVIDENCE REQUIREMENT**

端到端 route/fixture/version、beforeafterrepo/status/hash/diff、Candidate/Acceptance/verificationlinks、takeover 前後畫面、failure/retryg1/g2 歷史、bundlemanifest/refhash、offlineverify/rebuildoutputs 及 actual exit、START_HERE 可操作紀錄。

**ROLLBACK / RECOVERY**

只停止本次 managed process；保全 Humanworking copy 與 immutableacceptedartifacts。Export 失敗保留錯誤不發布完整 badge；restore 需 DB/artifactclosure 一致；不 resetHuman workspace 或刪 history。

**DEPENDENCIES**

完成 W6 才進獨立 B01 產品驗收；N1 不阻擋。這是內部 boundedcompletion，不自行宣布 WorkingProductAccepted。

**COMPLETION CRITERIA**

Golden Path 可操作、至少一條真實 failure/retry、accepted 取用/working copy UX 正確、P0 verify/rebuild 同 ID 與 onboarding 完整；N1 缺席不能當 P0 缺口，也不能反向假稱 N1 完成。

**INDEPENDENT ACCEPTANCE GATE**

非 writerreviewer 從 START_HERE 重走、不靠 writer 臨時手動 DB 修復；獨立 browser/failure path/P0artifact 驗證，然後提交 B01independent acceptance。

### B01 — Independent Product Acceptance

**STATUS：[未執行] / IMPLEMENTATION HOLD**

**TASK ID**

PN-TA-B01

**OBJECTIVE**

以真實 Simple Python Bug Fix 驗收第一個 Working Product outcome，而非接受 Agent Session 或 writer 自評。

**WHY**

只有 actual repochange、mandatoryverification、Humanaccept、可使用/重建成果與 failurehistory 串起來，才能改變 NOT YET ACCEPTED 狀態。

**PREREQUISITES**

S0/W1–W6 獨立 gates 通過；Human 明確授權 B01 實際執行範圍、fixture 與 executor/credential 使用；independent reviewer 與可信 AC/oracle 已指定；不是本輪文件生成時執行。

**EXACT SCOPE**

OpenRepository→Task/Goal/Scope/AC→WorkGeneration→RealExecutor→ActualRepositoryModification→CandidateFreeze→DeterministicVerification→Evidence→Human Accept→OpenAcceptedResult→PortableAcceptedPackage→Failure/RetryEvidence→History。使用小而可重現 Pythonbugfixture，明確允許改動/required oracle；同時證明原 Human dirty 保全。

**OUT OF SCOPE**

Simulator/mock 作 realPASS、writer 文字宣告完成、單純改 DBstatus、人工補不存在的 exit/hash、S0 臨場未審修復、N1/大量 Agents/release/commitpush。

**ALLOWED ARCHITECTURE AREAS**

Read-onlyindependentproductverification＋已授權 fixtureexecution/操作 UI；不與 writer 同時寫產品 code。若發現 bug，停止 acceptance 並回限定 fixpackage。

**EXPECTED FILE AREAS**

已審查 fixture 與 acceptance evidence 目錄（不得置於 Human source 覆蓋位置）；approvedcommands/runlogs/diffs/hashes/artifacts 與 browser evidence；產品 code/schema 不屬此 acceptancewriter 範圍。

**ARCHITECTURE INVARIANTS**

I-01–I-23 全部適用；本輪 Human 附加 same-generationlineagecriterion 也納入 W1gate 證據審核。

**POSITIVE TESTS**

必須實際看到 bugreproduced、真實 executor 的 source 修正、Core-derivedCandidate、可信 required tests、exactEvidence/Verification、Human A-LP 接受、OpenAcceptedResult、P0 bundleverify/reconstruct、failureretry 安全完成及 restart 後 history 保留。Sourcebytes/IDs/acceptanceview 可逐一對應。

**NEGATIVE TESTS**

以 writer falseimplementation、requiredFAIL/MISSING/STALE/MISMATCH 阻擋 Accept；optional SKIPPED 按契約不假 FAIL。Providerunavailable/process crash、lateAbort(g1)對 g2 無副作用、takeoverdrift、bundle 缺檔、Agent credentialaccept/replay 等依 W1–W6 已驗案例挑必要 cross-boundary 再驗，不無限重跑全部。

**FAIL-CLOSED CONDITIONS**

任一必要 realcomponent、mandatory check、可信 Human action、P0reconstruction 或 failure/retry evidence 缺失→NEED_ACTION/FAIL，不宣告 ProductPASS。SKIPPED 逐項列是否 blocking，不能以 simulator 填空。

**ACTUAL EXIT CODE REQUIREMENT**

**Actual commands、Actual outputs、Actual Exit Codes**逐 step 記錄，含 bugrepro 失敗、修復後 tests 成功、Agentexit、cancel/timeout/cleanup、bundleverify/rebuild。預期 bugrepro/fault 非 0 是該步真實結果，不改写 0；actual runner0 也不掩蓋 skip。任一關鍵 step[未執行]則不能 B01PASS。

**EVIDENCE REQUIREMENT**

**Actual file hashes、Actual repo diff、Actual evidence**：fixturebaseline commit/Snapshot、before/after 檔案、manifest/ChangeSet/Candidate、Run/WorkGeneration/control/binding、version/auth ownership、命令 cwd/time/exit/output、Verification / EvidenceSet、Human Decision/AcceptanceID、Open/takeover 觀察、P0 hash/rebuild、failure/retryg1/g2 與 history。全部來源明確，不用測試名稱推論 sideeffects。

**ROLLBACK / RECOVERY**

保存失敗 Candidate/Evidence/history；暫停後續 acceptance 並給 boundedfixprompt，不修改 officialapproval 或 release。對 fixture 的 recovery 在已授權範圍，原 Human workspace 不動；無確證 process 已停不重試。

**DEPENDENCIES**

S0→W1→W2→W3→W4→W5→W6 全部必要出口；N1 不是 B01 前置。B01 之後才由 Human 決定 WorkingProduct 是否接受，不自動進下一版本。

**COMPLETION CRITERIA**

Independent reviewer 有完整 freshactual evidence，必要 flow 與 failure/retry 全部滿足，无 mandatory missing/skip 或 simulatedsubstitution，明確 boundedPASS/FAIL/NEED_ACTION；**只有 Human 正式接受後**才更新 WorkingProductaccepted 狀態。

**INDEPENDENT ACCEPTANCE GATE**

B01 本身就是 Independent Product Acceptance：reviewer≠writer；適用 browser 由獨立 journey 驗證。Reviewer 提供可追溯 verdict，Human 作最終產品接受；ArchitectureFrozen、W6writer 完成、Agent 輸出均不能代替。

## 3. B01 證據不得替代的對照

| Product step | 必要 actual evidence | 不接受的替代 |
|---|---|---|
| Open/Task/AC/Generation | 實際 repo 與需求 snapshot、Core 配發 generation、client 操作 | 只貼流程圖或直接寫 DB |
| Real execution/change | Actualexecutorcommand/version/cwd/output/exit、source hash 與 repo diff | simulator、mock、Agent 說修改了 |
| Candidate freeze | Core-derived manifests、固定 IDs、source artifact bytes | caller 提供 manifest、自產 expected 自測 |
| Deterministic verification | mandatory oracle/check 命令與 actual exit／output、exact Candidate | tests 名稱、舊 log、AI 投票 |
| Human Accept | W5 可信 Human principal/action、exact view、AcceptanceID／receipt | loopbacktoken、actor 字串、writerapproval |
| Open/takeover | 實際 accepted result 匹配；Working Copylabel 及 ownership | 漂移目錄仍叫 immutableAccepted |
| Portable accepted package | actualmanifest/ref/hashverification、空目錄重建 sameSnapshot/ChangeSet | 只有 zip 檔、patch＋不可取得 base、完整 N1 當 P0 藉口 |
| Failure/retry/history | 真實 fault/cleanup、g1/g2、lateAbort 無錯殺、durable history | 忽略 failedruns 或重置 DB 清掉失敗 |

B01 的每個 SKIPPED 逐項揭露。若缺必要 real executor、tool、Human action、P0package 或 failure/retry 結果，verdict 不得是 Working Product PASS。Human Architecture PASS 仍維持既有意義，不被產品 failure 或尚未執行改寫，也不能拿來掩蓋產品缺口。

## 4. Current delivery status / stop condition

- 三份文件只是 Architecture formalization＋implementation planning。
- WORKING_PRODUCT：NOT YET ACCEPTED；REAL_EXECUTOR：NOT YET VERIFIED；B01：NOT YET EXECUTED。
- S0/W1/W2/W3/W4/W5/W6/B01：本輪沒有執行；actual product test exits 不存在，不宣稱 PASS。
- 正式 ADR／schema／code／原 REV1 與 handoff 不修改；未 stage/commit/push，未建立 release baseline。
- 本次交付後 **STOP**。PRODUCT_IMPLEMENTATION：**HOLD**。NEXT：**HUMAN_REVIEW_REQUIRED**。

