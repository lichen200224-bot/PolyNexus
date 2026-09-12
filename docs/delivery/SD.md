# 系統設計：責任、狀態、序列與工作執行

Status: DESIGN_DRAFT。Frozen REV1/正式增量/ADR-MOD-013為語意權威。本文件提出可實作的映射；不擅改既有RuntimeAdapter公開method、RuntimeBindingSnapshot、RunState/Workflow vocabulary或Golden profile。

## 1. 模組責任與變更界面

| 責任 | 建議承載位置/既有邊界 | 輸入/輸出 | 不擁有 |
|---|---|---|---|
| Input/Generation service | Core service＋Repository | Task、pinned input→generation/command receipt | OS process、vendor session |
| Workspace coordinator | Core workspace service | repo scope/baseline/generation→managed workspace facts | Candidate身份、Human Accept |
| ExecutionService | 現execution_service.py | Run claim/binding→Supervisor | vendor-specific options |
| RuntimeRegistry/module bridge | 現registry/bridge | validated static profile/envelope→adapter | 第二套Run或Human權威 |
| RunSupervisor | 現supervisor.py | bound adapter/limits→lifecycle observations/results | 證據的最終acceptance |
| Snapshot/Candidate service | Core immutable artifact/repository boundary | verified inputs/results→REV1 IDs＋publication | caller identity claims |
| Verification coordinator | Core gate/tool boundary | exact candidate/check plan→EvidenceSet/Verification | 改候選內容、Human decision |
| Human Decision service | 專用security＋Repository | exact view/challenge/action→append-only decision | Git commit/apply/release |
| Workflow/Council service | 現workflow/council邊界 | immutable definition/roles→bounded Runs/results | 自授權副作用或覆寫tool FAIL |
| Export/Consumption service | artifact/workspace boundary | exact Acceptance/Candidate→verified copy/P0 bundle | 私有provider session遷移 |

位置為internal mapping，不要求建立同名巨大class；優先重用現模組。Frontend只透過API DTO，不匯入DB/OS/vendor control。

## 2. Command transaction protocol

每個mutation接收command_id、exact target refs、expected revision、typed payload。Server從認證通道取得principal與scope，不信任body的actor。唯一鍵為principal＋command_id；先比較canonical payload digest，相同回既有receipt，不同回CONFLICT。Payload digest只作command防重，不替代REV1 content identity。

在一個SQLite transaction內檢查target ownership、revision與policy，完成CAS/state facts及receipt，再commit。External process/Git/file side effect在交易外執行，但必須由持久operation intent與fence綁定；其completion另以conditional update/append event記錄。失敗不回滾已發生的OS事實，也不宣稱跨DB/OS exactly-once。Crash後以intent＋ownership observation reconcile；無法證明未啟動時不自動再次啟動。

## 3. WorkGeneration與writer lineage

Prepare只固定輸入，不launch。Begin在Task expected revision上配發新正整數generation_revision。Retry保存predecessor、選定input，永不重用generation；相同command receipt回原結果。

Generation-level lineage claim不可只用暫時mutex：durable unique(task_id,generation_revision)保存writer_lineage_ref；同generation第二個不同command/入口/重連若不是同lineage的合法resume/recovery，必須拒絕。即使之前process退出或lock釋放，也不能偷偷生成另一條lineage。真正新writer工作需新generation。

四軸資料分開：Identity(誰/哪輪)、Git Observation(HEAD/index/dirty inventory)、Ownership(fence/claim/observed owned work)、Recoverability(允許的安全動作與理由)。CLEAN、lease expired、PID不存在、無新log都不是單獨的可接手證明。

## 4. End-to-end序列

1. UI固定Requirement/AC/Context及repo baseline；未選dirty不投影。API Begin取得g1。
2. Core建立owned managed worktree，記initial Git/hash observation；partial setup仍保存operation receipt。
3. CreateRun(g1)保存CREATED intent。Start要求g1可執行、same-lineage claim、scope/limits/egress可用。
4. 解析runtime profile與Run-scoped envelope，確認secret ownership與必要設定；persist immutable binding和claim事件後才construct/launch external work。
5. Supervisor bounded poll/stream觀察；UI從durable state＋progress讀取，不用socket判斷成功。
6. 完成或停止後驗owned process/tree/resource cleanup；無quiescence不publish。清理不確定保留recovery-required diagnostic，不新增假terminal成功。
7. Core讀回allowlisted output、containment/hash/re-read、建立Core-owned不可變copy；從baseline/result snapshots導出ChangeSet/Candidate。
8. frozen Candidate交Verifier的隔離verification workspace；build/test可能寫出的cache/output在該副本，不回寫Candidate來源。
9. EvidenceSet綁exact Candidate、ValidationContract、工具/版本/命令/cwd/結果與有效性。Eligibility重算，不只看summary PASS。
10. Human看到exact內容/requirements/evidence/view digest；challenge成功與當下eligibility一致才append Accept。
11. OpenAcceptedManagedWorktree和Export是另外的明確command；Accept不連帶改Human repo或Git remote。

## 5. Race與取消

| Race | 必要結果 |
|---|---|
| g1失敗→Retry g2→late Abort(g1) | g2/其Run/ownership保持不變；回g1 receipt |
| g1 Abort與Publish同時 | control revision CAS排序；Abort先成立阻publish，Publish先成立保留Candidate，Abort不Reject |
| completed Run收到cancel | 回已終止結果，不改COMPLETED為CANCELLED |
| start command重送或多入口 | 一條writer lineage、一個合法launch intent；其餘same receipt或conflict |
| verifier完成與Human Reject競爭 | verification結果保留；不能清除Reject或自動Accept |
| challenge簽發後policy/evidence/content變動 | 提交時重新驗證；stale challenge拒絕，重新呈現exact view |
| artifact在cleanup/讀取間改變 | 拒绝該publication/claim，不把新bytes貼舊hash |
| takeover與尚未停止writer | ownership不確定→禁止轉移/新writer，不因UI按鈕就放行 |

## 6. Workflow/Council執行設計

固定definition version及input refs；schema validation與dependency cycle檢查先於任何effect。Node只能使用既有vocabulary；limited CONDITION評估受限資料，不執行任意Python/JS。每步保存input/output/evidence refs和完成/失敗事實，restart按其idempotency與effect contract決定可重試或要求恢復。

PARALLEL_AI/CROSS_REVIEW是只讀角色分析的並行，不放寬single coding writer。各role input隔離且保留model/runtime identity；Cross Review可在獨立初稿形成後分享。角色失敗保留partial；SYNTHESIS必须引用各自finding，不能杜撰共識。TOOL結果透過deterministic runner形成Evidence；EVIDENCE_CHECK按hard-gate/validity評估；HUMAN_GATE不由controller代簽。

九範本共用execution/gate/artefact machinery，不以每個template再造一套服務。Golden flows跨UI/Core/Runtime/Artifact/Policy/Evidence實測，其餘範本至少各一條真實正常路徑及主要失敗處置。

## 7. Restart、cleanup、相容性

CREATED且未claim的Run保持intent，不補造binding。STARTING/RUNNING需從持久claim/envelope/fence與實際owner observation重建判斷；不可信或external state無法恢復則fail closed、不rebind、不relaunch。合法native resume需adapter證明capability/同scope；managed continuation按新generation/new Run規則。

Terminal event排序沿用ADR-014 durable per-Run sequence，不依同timestamp的UUID排序。ORM排序與API cursor使用明確sequence/stable ordering。Legacy records保留可讀與來源標籤；舊資料不可自動成Candidate/可信Human acceptance。

## 8. 實作退出條件

每個批次的required test oracle見TEST_PLAN及原WORK正負案例。沒有same-generation負例、late-Abort、quiescence、exact-candidate binding、legacy/FK、Human credential拒絕等證據不得以happy-path通過代替。任何需要public runtime/Golden語意變更須先停止該變更並提出architecture exception。

## 9. Assurance assessment 實作映射（PN-078）

[ASSURANCE_CONTRACT §2–4](ASSURANCE_CONTRACT.md#modes)定義三模式、四狀態、選擇/CAS/不可變快照、衍生優先序/合法轉移/失效重算及 Repository/DTO 邊界。Status VERIFIED 不把有效 FAIL 改為 PASS；模式變更不能洗掉已發布 required checks。這是待獨立審查的補充設計，不修改 Frozen vocabulary/identity/Human authority。[§6](ASSURANCE_CONTRACT.md#tests)提供每個子項的明確正負 oracle。
