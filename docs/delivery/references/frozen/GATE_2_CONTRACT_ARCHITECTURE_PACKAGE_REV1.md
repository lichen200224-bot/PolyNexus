# GATE_2_CONTRACT_ARCHITECTURE_PACKAGE_REV1

- 日期：2026-09-09
- 裁決：**READY_FOR_ARCHITECTURE_FREEZE_REVIEW**。
- Human review：原 package APPROVE_WITH_REQUIRED_AMENDMENTS；Product Direction／Target Logical Architecture ACCEPTED。REV1 僅處理 R1–R6 與 takeover UX；**Architecture Freeze HOLD / IMPLEMENTATION NOT AUTHORIZED**。
- 原件：[Gate 2 Contract Architecture Package](GATE_2_CONTRACT_ARCHITECTURE_PACKAGE.md)。保留未受修正影響的內容；本檔可獨立閱讀，差異表見 §23，正式規範性 invariants 見 §24。此清單是 Freeze Review 對象，不是自行宣布 frozen。
- 本輪唯一產出為本檔；不改原件、handoff、正式規格、產品 code 或 schema。
- 已接受輸入：[GATE_2_INPUT_BASELINE](GATE_2_INPUT_BASELINE.md)；已接受初稿：[Target Product + Architecture Planning](GATE_2_TARGET_PRODUCT_ARCHITECTURE_PLANNING.md)。本次 Human Contract Closure 指示優先於初稿中的未收斂語意。
- Canonical design/read SHA：`f34e6b29ae9e7326d1d44b9b03756b450809928f`；ref：`origin/feature/g24-g30-development-completion-routing`。沒有切換目前 checkout、整併 overlays 或建立 release baseline。
- 本檔中的「必須／不得」是待批准的契約規範，不表示產品已實作。現有正式 Scope／ADR／PRD／Decision Log 未修改。

## 1. Final Target Product Boundary

第一個 Working Product 服務 AI-augmented Developer／Technical Lead，Secondary 為 QA／Independent Reviewer。成果是一個小型、可重現 bug fix：真實 Agent 在受管工作副本修改 repository，固定成果、執行可信驗證、由 Human 接受，再讓 Human 實際開啟並使用該成果；另證明一次 failure → retry／recovery。

本 package 的八项收斂結論：

| 未收斂項目 | 本輪推薦契約 |
|---|---|
| Work termination／rejection | AbortWork target WorkGenerationRef；Cancel target RunID；Reject target 從未 accepted 的 CandidateID；accepted 後使用 revoke／supersede |
| Identity | **Model B**：Core 從 baseline/result Snapshots 推導 ChangeSet；Candidate 綁內容與要求／validation contract；caller 不提供 identity-defining change manifest |
| Verification | Check requirement、applicability、execution outcome、evidence validity 分開；optional SKIPPED 不自動失敗 |
| Accepted result consumption | **Open Accepted Managed Worktree** 為第一 vertical 最小必要方案；後續編輯須明確 Human takeover |
| D11 | **Option A 的 local-personal 修正版 A-LP**：可信配對 principal＋Human 專用 session／decision challenge；不宣稱硬體 attestation |
| Monitor | **REST polling＋durable facts/events** 為 W1–W6 minimum；WebSocket 保留 target capability、NEXT optional delivery；不改 ADR-004 核心方向 |
| Portability | P0 Minimal Portable Accepted Package 可驗 bundle／重建 accepted Candidate；完整 selected-task history／Continuation／import namespace 為 N1 |
| Real executor | 先通過品牌中立的 capability／readiness／真實 side-effect 測試，再選 executor |

KEEP Python／FastAPI／asyncio、SQLAlchemy／Alembic／SQLite、React／TypeScript／Vite、Repository interfaces、RunSupervisor／Adapter、Artifact／Evidence／Context。邏輯責任可在同一 Core 內完成，不是新增 microservices。

Core 掌握 Task／Run、context、workspace facts、artifact identity、evidence、verification、Human decision、recovery 與 history。Git 是 code history truth；provider session 是 external reference。第一 pilot 為 Local-personal、Single Human、Single Active Writer、Managed Git Worktree；不是 hostile-code sandbox 或 multi-user trust system。

## 2. Command Model — WorkGenerationRef 與 Decision Targets

以下為邏輯 commands／events，非新增 HTTP routes、workflow nodes、Attempt Aggregate 或大型 Domain。沿用 Core 的 authority、conditional write 與 idempotency 邊界。

### 2.1 最小 identity／durable reference（R1）

| Identity | 定義與 lifetime | 不等於 |
|---|---|---|
| TaskID | 長期工作目標與歷史容器，可有多次工作意圖 | 某一次可被 Abort 的執行 |
| **WorkGenerationRef = (TaskID, generation_revision)** | Core 在 Task 範圍以 CAS 配發的單調遞增正整數；一輪明確、固定輸入的工作意圖；一經配發不重用 | Run、Attempt Aggregate、Candidate 或 workspace claim generation |
| RunID | 一次 durable execution identity；持久關聯一個 WorkGenerationRef，建立後不轉移 | generation 本身或 acceptance |
| CandidateID | 固定 ChangeSet＋requirements／validation contract identity | Run／generation；相同內容可跨輪重現 |

每個 generation 的最小 durable record：WorkGenerationRef、固定 RequirementSnapshotID／ValidationContractSnapshotID／Context refs、baseline/input snapshot refs、可選 predecessor generation、creation command／reason、control revision，以及 start/abort/closed 事實。由既有 Task 的 revision/reference boundary 承載；不預先決定新 table。

Generation identity 的 revision 與其可變的 control revision 分開：前者定位「哪一輪」，後者序列化該輪的 start／publish／abort。Workspace claim generation 是資源 ownership fence，須能回指 WorkGenerationRef／RunID，不能互相代用。

PrepareTaskInput 只準備版本。**BeginWork** 明確選定輸入並由 Core 配發 g1；**RetryWork(previous_generation_ref, expected_task_revision, selected_input_refs)** 配發新 g2，記 predecessor=g1。即使輸入完全相同，retry 仍是新 generation；重送相同 command 回原 g2，不配發 g3。UI 可顯示「第 2 輪」，但 request 送 exact ref，不送浮動 latest。

Run 必須先有 generation 才可建立／啟動；一個 generation 可保存其執行與驗證關聯，Single Active Writer 不變。人工 restart/retry/new provider managed continuation 開新 generation；原 session 的合法 native resume 可延續原 Run/generation，但不得恢復已 aborted 輪。需求/input 變化需新 generation，舊輪 refs 不原地改。

Candidate publication 保存 TaskID、WorkGenerationRef、RunID（若由 Run 產生）、CandidateID 與 provenance。Candidate 的 hash 不含 generation／Run；相同 Candidate 多次 publication 不合併其工作歷史。

### 2.2 共用 command envelope

Mutation command：command_id、exact target、expected control/resource revision、typed payload；server 從 authenticated channel 取得 principal、scope與時間。相同 principal＋command_id＋payload 回同一 receipt；同 key 不同 payload 拒絕。任何 target mismatch 都 fail closed，不能自動改成「最新輪」。

長操作回 operation reference；command accepted ≠ side effect completed。Typed durable facts 記 event ID、target references、sequence/revision、causation、server time、必要 payload。現有 RunEvent 仍只代表 Run transition，不以 reason string 承載 generation 或 Human Decision truth。

### 2.3 Commands／events／history

| Command / target | Preconditions／效果 | Durable facts | 不隱含 |
|---|---|---|---|
| PrepareTaskInput / TaskID | 固定要求、context、baseline，dirty input Human 明选 | RequirementsRevisionCreated、InputSnapshotSelected | 不修改原 workspace |
| BeginWork / TaskID＋expected revision | Core 配發新的 WorkGenerationRef | WorkGenerationCreated | 不 launch |
| CreateRun / WorkGenerationRef | 存 execution intent，綁 exact generation | Run CREATED | 不證明 ready／已 launch |
| StartRun / RunID＋WorkGenerationRef | generation 可執行、binding／ownership／readiness 通過 | ExecutionClaimed、LaunchRequested／Observed | 不收到 request 就 RUNNING |
| **AbortWork / WorkGenerationRef** | 只撤回指定輪；CAS 阻止該輪新 start／自動 publish，停止該輪 active work | WorkAbortRequested、WorkAborted（確認已停止才完成） | 不停整個 Task 歷史、不擴及新輪、不 Reject／revoke Candidate |
| **RequestCancelExecution / RunID** | 只取消 exact Run；由 server 驗 generation／owner scope | CancelRequested、CleanupObserved、Run transitions | 不撤回 generation 意圖、不拒絕成果 |
| PublishCandidate / WorkGenerationRef＋RunID | generation 未 aborted、writer quiescent；Core 推導 change manifest | ChangeSetPublished、CandidatePublished | 不 VERIFIED／ACCEPTED |
| VerifyCandidate / CandidateID | 固定 policy/checks；不修改來源 | CheckObservationRecorded、VerificationRecorded | 不改候選內容 |
| **RejectCandidate / CandidateID＋review revision** | 已發布且從未有 AcceptanceRecorded；verification 可尚未完成 | CandidateRejected | 不 cancel；不將 accepted 歷史改成 Reject |
| AcceptCandidate / CandidateID＋decision revision | fresh exact view、mandatory policy 滿足、可信 Human action | AcceptanceRecorded（UI：ACCEPTED） | 不 commit／apply／release |
| ReopenCandidateReview / CandidateID | 只適用從未 accepted、先前 rejected 的 review；明確新 round | CandidateReviewReopened | 不撤銷或改寫任何 acceptance |
| **RevokeAcceptance / AcceptanceID＋CandidateID** | exact active acceptance；Human reason／finding/policy refs；不要求新 checks 先 PASS | **AcceptanceRevoked** | 不 ordinary Reject、不改舊 evidence |
| **SupersedeAcceptance / AcceptanceID＋replacement AcceptanceID** | replacement 已有效接受且 Human 明確連結同 Task/scope；拒絕 self/cycle／失效 replacement | **AcceptanceSuperseded** | 不默默接受 replacement、不 auto apply |
| RetryWork / prior WorkGenerationRef | 舊 writer 已安全釋放，明確選擇續用或新 input | RetryRequested、WorkGenerationCreated、新 Run | 不重用前輪 ref |
| OpenAcceptedResult / CandidateID＋AcceptanceID | 顯示當前 disposition，驗證受管副本對應 snapshot | ResultOpened 可稽核 | 不移交 writer |
| TakeOverWorkspace / workspace ref | Human 明確取得 ownership，旧 writer 已停止 | OwnershipTransferred、WorkingCopyOpened | 不把後續工作副本當 immutable result |
| ExportAcceptedPackage / AcceptanceID＋CandidateID | P0 取 exact accepted record及必要 closure | ExportPrepared／Completed | 不要求完整 Task history |
| ExportTaskBundle / TaskID＋selected scope | N1 完整 selected-task export | ExportPrepared／Completed | 不自動授予 imported Human authority |

### 2.4 Targeting 與 race rules

- **Retry 後 Abort 哪輪？**例如 g1/R1 失敗，Retry 配发 g2/R2；延遲的 AbortWork(g1) 只能關閉 g1，不能取消 R2。Human 要停新輪必須送 AbortWork(g2)。UI 顯示 exact target，server 不用 latest pointer 改寫命令。
- AbortWork(g1) 對 g1 active execution 發出各自 target RunID 的 cancel command，記 causation與cleanup。WorkAborted 只在該輪無未確認 active writer／operation 時成立；未知狀態保持 abort requested／recovery required。
- Abort 與 Publish／Start 在同 generation control revision 序列化。Abort先成立則不自動發表成果；已保存bytes仍保留。Publish先成立則 Candidate留存，Abort不隱含Reject。Retry與Abort舊輪競爭時，仍不得誤殺新 owner。
- Run natural finish 先成立，後到 cancel 回已終止的 receipt，不把 COMPLETED 改為 CANCELLED；cleanup certainty仍另查。
- Reject不cancel verifier；後到 PASS不清除Reject。從未 accepted 的Candidate重開review後，才可重新Accept。
- 一旦有accepted歷史，後續不認可只用AcceptanceRevoked／Superseded。ReopenCandidateReview不能繞過此限制；再驗證不會抹除acceptance。Revoked/superseded後若Human再次接受同Candidate，須freshverification與新decisionrevision，建立**新的AcceptanceID**並連結前次；不先製造ordinaryReject或自動恢復舊acceptance。
- Policy/finding可使eligibility stale／blocked，但不自行偽造HumanRevocation。UI分開顯示「歷史accepted」「目前驗證失效」「目前acceptance disposition」。必要撤回由明確Human command留下新事件。

## 3. Candidate / ChangeSet Identity

### 3.1 Model A／B 比較

| 維度 | Model A：單一 CandidateID 含全部 | Model B：ChangeSetID＋CandidateID |
|---|---|---|
| Identity clarity | 簡單但無法直接表達「程式相同、驗收約定不同」 | 內容與提交供驗收的約定分離，兩者語意清楚 |
| Deduplication | Artifact bytes 可去重，但內容集合只能另行計算 | ChangeSet identity 可重用；不合併不同 Candidate／execution provenance |
| History | 每次要求變更看起來像全新程式成果 | 同內容在不同需求下驗收可追溯 |
| Verification binding | 綁單一 ID，較少欄位 | 必須綁 Candidate，不能僅綁 ChangeSet；需要明確防呆 |
| Re-verification | policy／requirements 改變即新 identity，不易解釋 code 沒變 | Candidate B 可引用同 ChangeSet；仍需新的適用性評估／verification |
| Storage | 一個 manifest，若重複包含內容清單較冗 | 兩個 immutable manifest／索引關聯；內容儲存不必多一份 |
| UX | 單一 ID 易展示，但 diff 空白的新候選難解釋 | UI 顯示 Candidate；「內容相同、驗收條件更新」作補充，隱藏雙 hash 細節 |
| Migration complexity | 最低初期編碼成本 | 多一層 reference validation；目前尚無 durable Candidate，現在採用比日後拆分成本低 |

**推薦 Model B。** 增加的是一個可驗證的 immutable content boundary，不是兩個新大型 Aggregate／DB table。它解決 H03 包含內容與契約兩種 identity 的混淆，並保留未來 verification 與 storage 去重能力。

### 3.2 精確 identity 定義

```text
BlobID       = sha256(exact bytes)
SnapshotID   = hash(versioned complete source manifest: path / kind / mode / BlobID)
ChangeSetID  = hash("pn.changeset.v1", baseline SnapshotID,
                    result SnapshotID, canonical changed-entry manifest)
CandidateID  = hash("pn.candidate.v1", ChangeSetID,
                    RequirementSnapshotID, ValidationContractSnapshotID)
EvidenceSetID = hash("pn.evidence-set.v1", exact immutable Evidence record references)
```

- RequirementSnapshot 包含 Goal／Scope／AC 及影響需求解讀的 context refs。純執行用 context／prompt rendering、runtime/model、時間與 Run ID 放 publication／provenance，不讓無關 session 細節改變內容 ID。
- ChangeSet 的 baseline 是**內容 snapshot**，不是浮動 branch 名；Git commit/tree ref 另以 publication／baseline record 保留。不同 Git commits 若受管 source bytes／mode 相同，可對應相同 SnapshotID；不得藉此丟失原 Git provenance。
- **Canonical changed-entry manifest 只能由 Core 從已驗證的 baseline/result Snapshots 確定性推導。**Agent、Adapter、UI、Caller 提供的清單或 diff 僅作不可信提案／展示，不接受為 identity-defining input。Core 對 path union 排序，按 before/after 是否存在與完整 entry 是否相同產生 add／delete／modify；相同 entry 不產生 change。rename 固定表示 delete＋add，不依賴 heuristic。包含新增檔案、binary、mode；不得漏掉應納入的 untracked。
- Diff／patch 是可閱讀／交付的衍生 Artifact；不同 diff tool、context line 數不應改變 ChangeSetID。重建依內容 manifests／blobs，不僅靠展示 diff。
- Candidate／ChangeSet 是不可變 Value Objects；durable publication 把它們連到 Task／Run／workspace／context。同內容多次產出可共享 ID，publication／費用／失敗歷史仍分開。
- Evidence、Verification、Human Decisions 一律綁 **CandidateID**。只綁 ChangeSetID 的外部結果至多是可評估來源，不能直接滿足 Candidate mandatory policy。

### 3.3 Canonicalization 與支援範圍

推薦 manifest 使用受限制的 JSON：唯一 keys、無浮點／NaN、版本與大小為安全整數、UTF-8、固定 schema；採 JCS canonical serialization，加上述 type/version domain separation。陣列以契約規定排序，source entries 依 path 的 UTF-8 bytes 升序；不依 OS locale。JCS 負責確定的 JSON 表示，不替產品決定哪些欄位屬 identity。[RFC 8785](https://www.rfc-editor.org/info/rfc8785/)

Repository-relative `/` path；拒絕 absolute、`..`、重複／case-collision、無法在支援平台重建的名稱。**不靜默改 Unicode／大小寫／line endings**。Snapshot 表示實际 materialized bytes；Git filters／checkout 的 byte 差異須保留與觀察。首個普通 Git fixture 排除尚未驗證的 LFS、submodule、symlink、特殊 filters／reparse points；preflight 明確 unsupported，而不是忽略後仍宣稱完整。

支援範圍內 baseline manifest 足以 materialize source；generated scratch／dependencies 按已固定 exclude policy 排除。未知檔案必須分類，不能假設所有 untracked 都是垃圾。CRLF 差異會改 source hash；verifier 必須使用同 snapshot bytes，不能重新 checkout 後假定等價。

### 3.4 變化規則

| 變化 | 結果 |
|---|---|
| source bytes／mode／新增刪除變化 | 新 ChangeSet、新 Candidate |
| Goal／Scope／AC 或 validation contract 變化 | 相同內容可共用 ChangeSet；新 Candidate |
| 新 evidence／重跑同一 check | Candidate 不變；新 EvidenceSet／VerificationRecord |
| 環境或 verification policy revision 改變 | 新 verification evaluation；若改變 Candidate 的 validation contract，另建 Candidate |
| Verifier 改寫來源 | 不能繼續核發原驗證；產生新內容／Candidate，再驗證 |

V1 不做跨 Candidate 的自動 check cache promotion。相同 ChangeSet 不足以重用 acceptance；重新對新 Candidate 驗證。未來若重用執行觀察，仍須新 verification record 明確證明 oracle、環境與契約等價。

### 3.5 Core derivation 與 Canonicalization Golden Test Vectors（R3）

下列是契約 fixtures，不是產品實作或 runtime conformance PASS。數值 expected digests 本輪以受限制、canonical JSON fixture及 .NET SHA-256 計算；W3實作必須對**固定 expected bytes/IDs**斷言，不得用被測實作自行產出 expected value。

#### Exact encoding profile

本節將§3.2的hash簡寫具體化：ID = `sha256:`＋lowercase hex SHA-256(UTF-8 canonical JSON bytes)，無 BOM／尾端 newline。BlobID例外是直接SHA-256原始blob bytes。Type domain separation由canonical object中的`format`欄位提供，不額外串接未定義separator。

- Snapshot object：`{"entries":[ENTRY...],"format":"pn.snapshot.v1"}`。
- ENTRY固定keys/值：`{"blob":"sha256:<digest>","kind":"file","mode":"100644","path":"repo/relative","size":N}`；mode為Git風格六位字串，所有size為bytes。
- Change object：`{"after":ENTRY_OR_NULL,"before":ENTRY_OR_NULL,"op":"add|delete|modify","path":"repo/relative"}`。
- ChangeSet object：`{"baseline":"sha256:<Snapshot digest>","changes":[CHANGE...],"format":"pn.changeset.v1","result":"sha256:<Snapshot digest>"}`。
- Candidate object固定為`{"changeset":"sha256:<ChangeSet digest>","format":"pn.candidate.v1","requirements":"sha256:<RequirementSnapshot digest>","validation":"sha256:<ValidationContractSnapshot digest>"}`，同樣採canonical UTF-8 bytes求hash；EvidenceSet保留其獨立identity。本組goldens聚焦R3的Snapshot/ChangeSet，不把generation、Run、display diff或evidence放入其hash。
- Object keys依JCS；ENTRY/CHANGE陣列由Core按path的UTF-8 bytes排序。比對entries以kind/mode/blob/size/path精確相等。size須與blob bytes吻合，重複path／case collision先拒絕，不能在去重後hash。
- Core在verified source snapshot closure上推導changes；identity-defining caller change manifest拒絕。Blob/hash/size錯配、漏檔、額外entry或對不存在path指定delete不能取得published ID。

#### Byte fixtures

| Fixture | Exact bytes／生成方式 | Size | Blob SHA-256（ID需加sha256:） |
|---|---|---:|---|
| utf8 | hex `CF80E6BCA2` | 5 | `1599fb5ed90b726f48af992e913936ff9a70d194212e45e58fa4e66390d1679a` |
| x | hex `58` | 1 | `4b68ab3847feda7d6c62c1fbcbeebfa35eab7351ed5e78f4ddadea5df64b8015` |
| lf | hex `610A` | 2 | `87428fc522803d31065e7bce3cf03fe475096631e5e07bbd7a0fde60c4cf25c7` |
| crlf | hex `610D0A` | 3 | `8e4621379786ef42a4fec155cd525c291dd7db3c1fde3478522f4f61c03fd1bd` |
| empty | empty byte sequence | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| binary | hex `0001FF807F` | 5 | `a7bdecc019b926fd25ab897060a618043e23421448d44e161dbf676fff82e8dc` |
| large1048575 | byte `41` repeated 1048575 times | 1048575 | `04713def0c5de392161b4cfc0ecd49623237c6438bc898d15bb6c55b345b7ccf` |
| large1048576 | byte `41` repeated 1048576 times | 1048576 | `4e29ad18ab9f42d7c233500771a39d7c852b200baf328fd00fbbe3fecea1eb56` |
| large1048577 | byte `41` repeated 1048577 times | 1048577 | `9ef018e955cacc77ab7f2bc97ef79ed1415f0a028b89d026f7bc3551479b1b5c` |

#### Inputs 與預期行為

所有未列出的baseline為empty entries；file kind均file，mode預設100644；ENTRY使用上表fixture的blob及size。

| Vector | Baseline → Result | Core changes／預期 |
|---|---|---|
| G01 UTF-8 | empty → utf8.txt=utf8 | add；π漢的UTF-8 bytes不轉碼 |
| G02 Unicode path | empty → src/測試.txt=x | add；path本身以UTF-8參與identity |
| G03 CRLF | line.txt=lf → line.txt=crlf | modify；LF/CRLF不同bytes，不正規化 |
| G04 Empty file | empty → empty.txt=empty | add；空檔存在不等於不存在 |
| G05 Binary | empty → binary.dat=binary | add；包含00/FF/80，不經文字decode |
| G06 File mode | tool.sh=x/100644 → tool.sh=x/100755 | modify；bytes相同而mode不同也改ID |
| G07 Add | empty → new.txt=x | add |
| G08 Delete | new.txt=x → empty | delete；after=null |
| G09 Case collision | result含A.txt=x及a.txt=x | REJECT_CASE_COLLISION；不發布SnapshotID/ChangeSetID；caller順序不影響拒絕 |
| G10 Path ordering | result由a.txt=x、z.txt=empty、測試.txt=binary組成 | 陣列必為a.txt,z.txt,測試.txt；所有輸入permutations得到下列同一ID |
| G11a Unicode NFC | result的é.txt=x，path首字U+00E9 | add，與G11b不同ID；不做Unicode normalization |
| G11b Unicode NFD | result的é.txt=x，path首字U+0065 U+0301 | add；單獨fixture與G11a分開，不依畫面字形當相同path |
| G12a Large boundary L−1 | large.bin=41 repeated 1,048,575 | fixture policy L=1,048,576 bytes；接受 |
| G12b Large boundary L | large.bin=41 repeated 1,048,576 | 接受；不同stream chunk大小結果一致 |
| G12c Large boundary L+1 | large.bin=41 repeated 1,048,577 | REJECT_SIZE_LIMIT；不發布SnapshotID/ChangeSetID；不得truncate成L |

L是**測試fixture的設定上限**，不是凍結產品檔案上限。實際size limit為implementation policy；同一支援範圍內，使用1、4093、65536 bytes等chunk size、全量或streaming讀取均須產生相同ID。

#### Expected Snapshot / ChangeSet digests

表中為64位lowercase SHA-256；實際ID加`sha256:`。空Snapshot digest為`a60c142d586dfa7a88c8ef64f8e42d6ec6583a4b109f3c7d87759d14b35fac4a`。Baseline entries已由上表固定，完整重建不依caller提交的changes。

| Vector | Baseline Snapshot digest | Result Snapshot digest | ChangeSet digest |
|---|---|---|---|
| G01 | `a60c142d586dfa7a88c8ef64f8e42d6ec6583a4b109f3c7d87759d14b35fac4a` | `daacb451f628d6042d7fa28d5bf0eac0378258d931655908bf1c29b0a7f26bb7` | `06561333b5dacc322925230ef07e10b518a75c0fd97d3cb4476b5df6a2383aef` |
| G02 | `a60c142d586dfa7a88c8ef64f8e42d6ec6583a4b109f3c7d87759d14b35fac4a` | `e8bda7c54291b10053ddf97779c64c8246b9930d3d69dbe120ce5d4ec75bab6c` | `36cf74bede7c7d2941e56b2004bdbffb84f060636988557eaa1705c183115432` |
| G03 | `4bd7a9929b7a8c4a9a58894ea060d3388f3252a6af4ad51afec0af69de11d737` | `349ad0e65158b95b75de7435b636352c6fa29bf708a95b45fc1097cdd973ec4a` | `df87519025d3dd2a1241c08ebe7898fcffc6133d427cf5def6ea3b59d5ffe3fc` |
| G04 | `a60c142d586dfa7a88c8ef64f8e42d6ec6583a4b109f3c7d87759d14b35fac4a` | `3d9ed22d17634ee059e37e8123b5b403cad28e93e9f05ca0571e0b3a94816a17` | `36aff5bf1fe84a43eb025186a8d25290414a04947678359b148bd1876796cea2` |
| G05 | `a60c142d586dfa7a88c8ef64f8e42d6ec6583a4b109f3c7d87759d14b35fac4a` | `e59d1f91e2545e8e4c2426f645482ba73e005bb5ffeac95a89461c6a3684dce8` | `09c603c1dab682b26a3e547f3e0b9a4fa7a4d2c713dab04ba8eb04134d23f1b5` |
| G06 | `b336a578dd09c3f43d4c457bd549f142470ea23dd867f6ffae7475943ed4f944` | `eb1c495968f90f5ad4cf64ca2049827e3510ad2f1196f49fea97d8a4fe6b5bd5` | `2467013ef1d12deadba61e001ea8d8749e3f40a38ad5caafe0902b9bc84add67` |
| G07 | `a60c142d586dfa7a88c8ef64f8e42d6ec6583a4b109f3c7d87759d14b35fac4a` | `55954e17be8d0e58268fd39e7ab1f7b7d398f4d9b6de1df8f505d760586be258` | `81ed3bcaefe7cf8346de2b8e8a39f1305d1af0d3bb92a93a59c8a84b8045aac0` |
| G08 | `55954e17be8d0e58268fd39e7ab1f7b7d398f4d9b6de1df8f505d760586be258` | `a60c142d586dfa7a88c8ef64f8e42d6ec6583a4b109f3c7d87759d14b35fac4a` | `70b3d4243b4864d3cee2f9fa5019f68dfec2405c4a9d92a058c056d6a43048e9` |
| G10 | `a60c142d586dfa7a88c8ef64f8e42d6ec6583a4b109f3c7d87759d14b35fac4a` | `4b2dcf60883789647178f8644393b687d1e71241b2389db31fb9c59d375ea954` | `92a5962a3465a645f862148e117c17dca6903b95031790a70086c685784424d3` |
| G11a | `a60c142d586dfa7a88c8ef64f8e42d6ec6583a4b109f3c7d87759d14b35fac4a` | `914a99330c7e03c227c74c2ac10f4add4fd52745d0b13eb4844cf1f1465d1b1c` | `8d69a923361999a502e888ac12b44ccc2c828a16cd55f916a6a16d2e7f7311af` |
| G11b | `a60c142d586dfa7a88c8ef64f8e42d6ec6583a4b109f3c7d87759d14b35fac4a` | `70a6273c968c6b19fd900b8edb3a2eff8c3643504a76cd80a6ba71d2f6b61ad9` | `9129354566f0e9b6dd8b8a48a8df4d10016bbf36391287fb10c6a8eb689021c4` |
| G12a | `a60c142d586dfa7a88c8ef64f8e42d6ec6583a4b109f3c7d87759d14b35fac4a` | `6ff8c0295bf9578e49839e9bf89ed46830e1cb22939c6b9003a21640770f814a` | `a45dfbc176638e7befb0528cebb4cec581592c1041bd42838174ed009848d09d` |
| G12b | `a60c142d586dfa7a88c8ef64f8e42d6ec6583a4b109f3c7d87759d14b35fac4a` | `ff15704f1fbc4cd0f75b3be1dc36b221c1128b8367f05e3485e01dd65021ee8f` | `d2f37e898070b29492cd71d5e1473efcf5b2dd7ee2a4ce23f177139151b0a3b3` |

#### Golden assertion matrix

每個valid vector在Core capture、從固定snapshots重新推導、P0 bundle重建後重新capture三條路徑，比對相同canonical manifest bytes、SnapshotID及ChangeSetID。另以caller entries順序打亂、display diff工具/行數改變、不同Run/WorkGenerationRef重複；均不得改變identity。G09/G12c在所有路徑皆拒絕，不產生「部分有效」ChangeSet。

Counter-tests：caller刻意刪除change entry、偽造before/mode/size/op、提供看似相符diff但實際snapshot不同，Core不可採信。驗證模式應獨立重算並比固定goldens，不能只檢查manifest內自帶hash。這些execution-path assertions留待W3/P0測試；本輪僅計算fixture expected values。

## 4. Workspace Contract 與 Accepted Result Consumption

### 4.1 四軸與 ownership

| 軸 | 必須可追溯的 facts |
|---|---|
| Identity | logical repo、baseline Snapshot／Git ref、managed workspace reference、support / exclusion policy |
| Git Observation | HEAD/index/worktree/untracked/conflict facts、observation time／revision、source manifest refs |
| Ownership | writer principal／Run、claim generation、操作／process references、transfer／release facts |
| Recoverability | capture completeness、process cleanup certainty、可重建來源、partial operation／blocking reason |

Single Active Writer 限於 pilot 的受管 repo mutation scope（包含相關 worktrees／shared Git metadata）；read-only review 可並行。Human takeover 也是 writer ownership，不可與 Agent 同時改同一 scope。

Ownership claim 以 durable conditional update 防雙 writer，Core 控制的操作附 claim generation，拒絕舊 generation。這無法強制阻止同 OS 權限的失控 process；故 **lease expiry／PID 消失／Core 重啟均不能單獨證明可安全轉移**。不確定時阻擋新 writer，保留 recovery facts。Git CLEAN 不等於 free/safe。

原 Human dirty workspace 不自動帶入／修改。需要 dirty input 時 Human 明選並 freeze snapshot，保留 staged／unstaged／untracked 來源說明；不得為建立 checkpoint 自動 commit 或 reset 原目錄。

### 4.2 成果取用比較

| 方案 | User value／成本 | Integrity／授權 | 第一 vertical |
|---|---|---|---|
| **Open Accepted Managed Worktree** | 可立即在 editor／terminal 查看、測試並接續；最少傳回機制 | 開啟不改原 workspace；編輯須 takeover。受管目錄漂移時不可冒稱 accepted bytes | **選用，必要** |
| Export Patch | 易分享／手動套用，需補 binary／mode／base 相容性 | 僅 patch 不能保證完整 source / history；不自動 apply | 獨立 patch UX 可 NEXT；portability bundle 仍含重建資料 |
| Create Local Commit | Human 易延用 Git 工作流 | commit identity／hooks／branch 寫入需明確 command 與另行授權；Accept 不觸發 | 非最小必要；延後 |
| Apply to Human Workspace | 最直覺回到原 repo | destination 可能 dirty／漂移，需 conflict／rollback／ownership；風險最大 | 延後；不因 Accept 自動做 |

第一 vertical 必須提供「Open accepted result」：顯示 Candidate、接受時間、受管位置、與原 workspace 分離。開啟前校验該副本內容；若已漂移，不能把它標成 accepted result，需從固定 snapshot 在新的安全受管位置 materialize 或回報阻塞。

Human 選「Continue editing here」／TakeOverWorkspace 取得 ownership 後，UI 必須立即切換為 **Working Copy based on Accepted Candidate <ID>**，並顯示目前是否已修改／觀察未知；不得繼續標為 immutable Accepted Result。開始編輯或偵測漂移後也維持此標示；舊 accepted ChangeSet／Candidate 仍不可變。修改需要新 Candidate 才能再次正式驗收。取用後保留目錄，不以一般 temp cleanup 自動刪除有效工作；Human 可在該目錄自行使用 Git，PolyNexus V1 不替其 auto commit／merge／push／release。

P0 Minimal Portable Accepted Package 是另一個最小 exit gate，可在無 provider private session 下驗 hash並重建此 accepted Candidate；完整 selected-task portability 為 N1，不阻塞 B01。OpenAcceptedManagedWorktree 的主流程不要求先 export/import。

## 5. Execution Lifecycle Contract

沿用 Run CREATED → STARTING → RUNNING → terminal，以及既有 CANCEL_REQUESTED；不把 RunState 擴成 acceptance enum。

1. CREATED 是 durable intent。未開始、無 binding 的正常 Run 不應讓全 Core restart 失敗。
2. StartRun 固定 Task／context／workspace identity，校驗 readiness；原有 binding-first／CAS 交易延用。Claim／binding／必要 intent 持久化成功前，Adapter 不得 launch。
3. DB 與 OS launch 無跨資源原子交易。保存 launch intent、可觀察 handle 與結果；不確定窗口必須 reconcile，不承諾 crash 後 exactly-once launch。
4. Handle 至少能區分 process instance（不只 PID）、parent/child containment、啟動時點、owner generation、workspace、adapter/version。平台實作可不同，但不能以新 PID 同號誤認原 process。
5. Run truth、bounded outputs／重要 failure facts 持久化；live progress 可丟棄。DB transaction 不跨整段 Agent execution。
6. Cancel／timeout 共用 bounded terminate→等待→必要 escalation→確認 resource/process tree cleanup，但保留不同原因。完成 cleanup 才釋放 ownership。
7. 既有 CREATED→CANCEL_REQUESTED→CANCELLED 可表達 launch 前取消；不需新增 direct transition。已知 terminal state 不回退。正常完成後若發現 cleanup 未確認，以 workspace recoverability 事實阻擋重派，不假裝 terminal 代表安全。
8. timeout／error 無法確認停止時保存原原因與 unresolved cleanup，經 ADR-007 具體 transition review 處理 ORPHANED 等情況；不得為了選 TIMED_OUT 字樣而遺失 process 仍存活事實。

Startup reconciliation 分類：未啟動 intent 可保留；可辨認且安全可觀測的執行恢復監測；未知／不相符的狀態隔離為 recovery-required。資料完整性或 schema 錯誤仍可阻擋 write readiness，不以「局部隔離」吞掉全域 corruption。

Retry 先保全前次 facts 與內容、確認舊 owner 停止，建立新 Run／publication。Native resume 僅在能力與 workspace/binding 對賬通過時使用；managed continuation 可開新 session，不重寫旧 Run 執行史。

## 6. Real Executor Capability Contract

**先定通過標準，之後選 executor；本輪沒有指定品牌，也沒有執行 real Agent。**

每項能力分成 declared、observed（exact executor／adapter／OS／環境版本與日期）、currently ready。現有 boolean `cancel=true` 或 `health=true` 不構成產品證明。

| 能力 | First executor 必須通過的真實證明 | 失敗分類／動作 |
|---|---|---|
| Launch | 受控啟動具可追蹤 handle，startup 有界；先 persist 後 launch | LAUNCH_FAILED；沒有 launch 成功不標 RUNNING |
| cwd control | 在指定 managed workspace 讀寫；用 fixture marker 與實際 diff 確認 | WORKSPACE_UNSUPPORTED／CWD_MISMATCH；禁止改原 workspace |
| Input/context | 能傳入 versionedtask/context 必要內容；記錄 rendering/source refs 與限制 | INPUT_INVALID／CONTEXT_UNSUPPORTED；不得默默截斷必要 AC |
| Observable output | 至少可查 lifecycle、bounded stdout/stderr 或 normalizedobservations 與 terminalresult | OBSERVATION_LOST；不以無輸出推定停止或成功 |
| Actual repository modification | 能讓故障 fixture 產生真實預期檔案變更；由 Core 獨立觀察 | NO_RESULT_CHANGE／SCOPE_VIOLATION；文字回答不是 change |
| Cancel | Human stop 能達到該 execution 並停止寫入 | CANCEL_FAILED／CLEANUP_UNCONFIRMED；阻擋下一 writer |
| Timeout | 限時到達觸發取消與 cleanup；停不下來仍可保全 truth | TIMEOUT，另記 cleanup outcome；不能只 stop polling |
| Process-tree cleanup | 包含 child／grandchild、持有 filehandle 與背景 writer；平台 integration test 確認 | CLEANUP_UNCONFIRMED；不足者不作 V1 首 executor |
| Version/provenance | adapter 版本、實際 runtime 版本、執行 target；model 可見則記實值，不可見標 UNKNOWN | VERSION_UNSUPPORTED／PROVENANCE_INCOMPLETE，依 mandatory 項阻擋 |
| Auth ownership | 分清 runtime-managed／SecretRef 等；Human 授權的既有登入可用；secrets 不流入 artifact | AUTH_REQUIRED／AUTH_EXPIRED；不靜默改 cloud/provider |
| Failure classification | missing executable、auth、unavailable、permission、invalidinput、crash、timeout、cancel、unknown 可區分 | 固定公開類別；原始例外／憑證不直接公開 |

Authentication 是能力／當下 ready 條件，不保證 provider 永远可用。成本／usage 可為 UNAVAILABLE／ESTIMATED，不為「看起來完整」虛構精確值。Resume NATIVE／MANAGED／NONE 不必為 NATIVE；首 executor 必须满足 stop 與 cleanup 要求。

既有 `RuntimeAdapter.create_run(context)`／`submit(runtime_ref, task)` 沒有明確 cwd／ownership handle 欄位。**不借 prompt string 傳 privileged filesystem authority**。提案以 typed local execution binding／workspace resolver 在 composition／adapter 邊界注入最小 workspace 與 provenance；若必須改公開 Adapter signature 或 persistedbinding，經 ADR-007／011 change 批准。Core 不能出現 `if provider == ...`。

Feasibility 證據：選定候選 executor 後在隔離 fixture 執行 success、prelaunch unavailable、mid-run crash、cancel、timeout、child-writer、wrong cwd／unsupported input cases。任何 mandatory 能力未通過，該 executor 不入選；不是增加 simulator 結果補數。

## 7. Verification Contract

### 7.1 不將 requirement、applicability、outcome 混成 enum

| 維度 | 值／責任 |
|---|---|
| Requirement | REQUIRED／OPTIONAL；由 versionedvalidation contract／mandatory policy 指定，writer 不可降低 |
| Applicability | APPLICABLE／NOT_APPLICABLE／UNRESOLVED；N/A 需受信任規則與理由，不能由 runner 跳過等同 N/A |
| Execution outcome | PASS／FAIL／ERROR／TIMEOUT／SKIPPED；尚未執行為沒有結果 |
| Evidence validity | present／MISSING、current／STALE、matching／MISMATCH、trusted／UNTRUSTED；可同時有多項問題 |

UI 可顯示 REQUIRED、OPTIONAL、NOT_APPLICABLE 標籤，但保存原 requirement 與 N/A 理由，避免將 required 改成 optional 後清掉歷史。

### 7.2 Mandatory satisfaction rules

| Check 情況 | Mandatory verification 影響 |
|---|---|
| REQUIRED＋APPLICABLE＋可信 fresh matching PASS | 該 requirement satisfied |
| REQUIRED＋FAIL／MISSING／ERROR／TIMEOUT／SKIPPED／STALE／MISMATCH，或 untrusted | **不滿足**；Human 無法轉為 VERIFIED |
| REQUIRED＋UNRESOLVED applicability | 不滿足；先解決適用性 |
| Policy 明確核准 NOT_APPLICABLE | 記 policy 版本、predicate 輸入與理由；不列入需執行分母，也不虛構 PASS |
| OPTIONAL＋SKIPPED／MISSING | 顯示未執行；不自動使 mandatory verification FAIL |
| OPTIONAL＋FAIL／ERROR 等 | 保存警示；本身不阻擋 mandatory，除非另有明確 mandatory blocking finding／risk 規則 |
| 零 applicable required checks | 不能 vacuous VERIFIED；首 vertical 至少要求一個可信 bug oracle，除非另經 Human 批准 validation contract 變更 |

**N/A 不是豁免機制。** 適用性必須由 policy 允許的條件推導；required check 沒有該規則就不能改 N/A。OPTIONAL outcome 也不能跨層繞過「有某類缺陷即阻擋」的 mandatory policy。提升 check 要求會形成新 policy／contract 版本並重新評估，不篡改原 check 結果。

### 7.3 VerificationRecord

Immutable record 綁 CandidateID、RequirementSnapshotID、ValidationContractSnapshotID、當時 policy revision、EvidenceSetID、verifierprincipal/type、environment、check evaluations、開始/完成時間與結論。结論區分 verified／not-satisfied／incomplete 或 execution error 原因，不把全部缺證據改成工具 FAIL。

Certification 是「對該 Candidate、該 policy／evidence snapshot 成立」；current eligibility 是 derived view。Policy／requirements 變化、required artifact 不可取回、source 不同、trusted producer 失效、特定時效過期，都可使其 stale。TTL 只是其中一種，不是唯一 freshness 定義。

獨立性最低是可信 oracle 與受控收集，不需不同 provider。Verifier 不得改 Candidate；tests 可寫 scratch，source mutation 使本次 verification 不成立。Writer 更改 tests 不能自行降低 requiredoracle；B04/B07 驗證此邊界。

## 8. Evidence Contract

KEEP 既有 EvidenceType、EvidenceStatus、Finding、Artifact；將新欄位視為 versioned structured binding 契約，不把任意 metadata 視為可信 assertion。

必要 envelope：EvidenceID、CandidateID、check/claim ID 與 revision、producer identity/type、實際 command/target、execution/run 關聯、來源 snapshot、環境摘要、start/end、exit/signal/timeout 與 outcome、artifactrefs/hashes、observer/ingestion provenance。Secrets 僅 reference，不在任何 payload/log/export 中保存值。

- Local tool evidence 由 Core 受控 observer 讀取真實結果；Agent 可以提交 proposal／AI_OPINION，不能核發 trusted TOOL_EVIDENCE。
- External CI evidence 須 trusted retrieval／已定義的 attestation 驗證，綁 repository、實際 checked-out source、workflow/check revision、CI run/job/attempt、runner/provenance 與 artifact bytes。
- CI 測 PR merge tree 不等於測 head；只驗 ChangeSet 或另一 tree，不能直接 certify Candidate。可先作 unbound 來源，明確 mapping 並產新 verification record 後才適用。
- EvidenceSet 是固定 record 集合；追加新證據產新 set。Hash 證明 bytes 不變，不證明誰產生或命令真的跑過。
- Human Decision 不是替代 toolcheck 的 Evidence。Review 意見、Findings 與 testexecution 各保留類型；decision 可引用它們但不改原始結果。

## 9. Human Decision / D11 Contract Proposal

### 9.1 問題、authority 與選項

f34 的 D11 Option C 已明定：`Evidence.actor_id`與 authenticated loopback token 不足以證明 Human principal；未驗證 Human evidence 不可產生 PASS/VERIFIED。現有`api/dependencies.py`主要檢查 127.0.0.1 與共用 token，沒有 Human-vs-Agent authority 分離。

| 選項 | 可信範圍／成本 | 判斷 |
|---|---|---|
| 現有 C 持續不變 | 一律 failclosed；安全但不能完成 HumanAccept 產品閉環 | 保留為未遷移／不可信 request 的 fallback，不能作 W5 完成方案 |
| A：authenticated principal mapping | 可把真正配對的 session 映射到本機 Human，權限清楚；仍非 user-presence 硬體證明 | **推薦 A-LP 修正版**，符合已批准 local-personal scope |
| B：attestation/provenance | 若有可信 authenticator／獨立 broker 可提高 assurance；需 enrollment、key/recovery 與新信任根 | 不列 first vertical 必要；自行簽一份 JSON 不等於獨立 attestation |

**Change proposal D11-A-LP（暫時提案 ID，非已登記 ADR）：**Human approval 只能由明確配對的本機 Human principal，在 Human 專用 session 中對 server 固定的 decision challenge 發出；Core 以 current mandatory policy 與 exact view 再次驗證，原子保存 decision。一般 Agent／extension／loopback token 一律無 Human decision 權限。不可信舊 HUMAN_EVIDENCE 繼續 D11-C。

### 9.2 Trust scope

單一 Human、單一可信 OS 使用者、可信 Core/UI/launcher；防錯誤 client、跨站請求、普通 Agent 憑證越權、重送、stale view 與競爭。**不宣稱**抵抗同 OSprincipal 惡意程式讀取 browser 記憶體、操作 UI、竄改 Core／DB 或憑證；不宣稱 enterprise 身份、多使用者 attribution 或 cryptographic nonrepudiation。

「Human session」只在此邊界內支持 explicit intent；普通 Agent 不得獲配對秘密、Human browser profile 或 Human 專用 session。若產品需要抵抗這些被竊取情況，必須升級 OS／authenticator isolation，不能讓 A-LP 的標籤提供假保證。

### 9.3 Principal 與 pairing

1. 安裝／可信本機啟動流程建立一個 stable opaque `local_human_principal_id`，普通 API 不能靠自填名字創建可信 Human。顯示名稱只是 label。
2. Pairing 由可信 launcher 的明確 Human 動作開始。一次性高熵 code 僅顯示於 Human 啟動介面；不放 URL、普通 logs、Agent context、repository 或 clipboard 自動注入。
3. Code必須短效、一次使用、有嘗試限制；TTL為secure default／implementation policy，不凍結數字。Exchange僅限固定受信任UI origin的loopback endpoint，pairing不繞過origin／CSRF bootstrap。
4. Pairing 後簽發 opaque session，映射 principal、session generation 與允許權限。Publicclient／Agent token 不能呼叫 pairing 管理或 decision endpoints 來自我升級。
5. Logout撤銷相應session/challenges；re-pair／credential reset依scope輪替或撤銷grant/session，保留principal與history。**Core restart不必重新pairing。**允許安全持久pairing grant＋bounded session／短效decision challenge，或重新pairing，由W5 Security＋UX tests決定。

R4保留bounded/revocable session與短效、不可重放challenge，不凍結5 min／15 min／8 hr／2 min或restart重新pairing。Pairing grant、session、challenge是不同lifetime；持久pairing不等於無期限登入或自動授權決策，普通loopback token仍不是Human憑證。

### 9.4 Session 與 browser boundary

- Human UI/API 採受信任 same-origin 入口；開發 proxy 亦固定 allowlist，不開 wildcard CORS。驗證 Host／Origin、拒絕 null/未知 origin 與不預期 contenttype；限制 loopbackbind，不信任 forwarded header 偽造本機來源。
- 建議 Human session 以 HttpOnly、SameSite=Strict cookie 傳遞，不存 localStorage 或提供給 Agent；同步 CSRF token／action challenge 走受控 requestheader。Cookie 不跨不同服務共用，session 需隨配對／重認證 rotation。
- 正式 HTTPS 部署必須 Secure cookie；此 pilot 若採明確 127.0.0.1 HTTP loopback，將無 TLS/無 Secure 保證列為 local-only 例外，不宣稱 SameSite 或 HttpOnly 等於 channel encryption。若平台不能滿足受控 origin 與 cookie 行為，阻擋 W5 而非關閉保護。
- Session須有server-enforced idle/absolute bounds及revocation；具體期限由W5校準。Polling不延長Human活動期限；過期需重新取得可信Human session，可透過安全grant重新認證或重新pairing，保留review畫面。
- Authentication/verifier 資料保存在專用 securityboundary；普通 Domain 只存 principal/session 非秘密 reference。Nonce/session/code 原值不進 Evidence／audit／export。
- Agent／diff／artifact 內容以不執行的文字／安全渲染呈現，不允許 raw HTML/script 在 Human approval origin 執行；防 XSS／clickjacking 是此 decision channel 的必要條件。

Cookie-based session 需要 CSRF 防護與 origin 驗證；XSS 仍可能繞過此類防護，因此不能把 CSRF token 當完整安全邊界。[OWASP CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) Session expiry、rotation 及 cookie 限制採 server enforcement；具體期限屬secure default／implementation policy，不在本輪freeze範圍。[OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

安全持久化選項須在專用security storage保存grant/verifier及必要revocation/generation資料，不進普通Domain、Git或export。Pending challenge可在restart一律失效並重取，或僅在expiry、session binding與nonce消耗狀態安全持久且可驗證時恢復；不確定即fail closed。持久化不得讓已消耗nonce再次有效，或browser重連後自動Accept。這是lifetime實作彈性，不降低local-personal威脅邊界。

### 9.5 Exact view、nonce、anti-replay 與 idempotency

DecisionView 由 server 提供：CandidateID／ChangeSetID、requirements／validation contract、current policy revision、EvidenceSetID、VerificationRecordID（可空）、eligibility revision、review round／decision revision、可檢視的 diff/checks/missingreasons。

Human選Accept／Reject／Revoke／Supersede時，server產生短效單次challenge，綁action、principal/session generation、exact Candidate、必要AcceptanceID／replacement AcceptanceID、view digest及decision revision。期限為implementation policy。Accept只對eligible view；Reject只對從未accepted的Candidate；Revoke／Supersede不要求新checks先PASS，但仍需exact target与Human authority。

提交時校验 session、CSRF、challenge/action/view digest、command id、expected revision；Accept 再查 mandatory policy 與 evidence validity。Nonce 消耗、decision record、idempotency receipt 及 decision revision 變更在同一短 transaction 提交。

相同 command id＋相同 payload 重送：在有效身分驗證下回原 receipt，不再消耗新 nonce 或重新接受。不同 payload 回 conflict。Session過期可重新取得同principal的可信session後查receipt，不要求每次重做pairing；舊 challenge 不得藉新 session 重新發出 mutation。Receipt 回歷史接受時，同時另回目前 stale/disposition，避免誤認仍 eligible。

### 9.6 Review／Acceptance lifecycle 與 races（R2）

- Pre-acceptance：Candidate從未有AcceptanceRecorded時，Accept/Reject競爭同review/decision revision，最多一個commit。Reject先成立則Accept需refresh/reopen；Accept先成立則延遲Reject衝突，不得換round後再Reject。
- Post-acceptance：Human以RevokeAcceptance或SupersedeAcceptance綁exact AcceptanceID／CandidateID，記reason及Finding/Policy/Defect refs。ReopenCandidateReview只適用從未accepted的rejected review，不提供post-acceptance捷徑。
- Append-only：`AcceptanceRecorded(A,C,T1) → AcceptanceRevoked(A,C,T2)`，或`AcceptanceRecorded(A,C,T1) → AcceptanceSuperseded(A,replacementAcceptance=B,T2)`。T1的ACCEPTED保留，不能被改成普通Rejected。
- Current disposition由事件導出active acceptance／revoked／superseded；verification eligibility/stale另列。Policy invalidation可使eligibility失效，但不偽造Human撤銷。Replacement後來撤銷，不自動復活source acceptance。
- 再接受同Candidate：當前revoked/superseded者須新fresh verification及可信Human action，建立**新的AcceptanceID**並連結predecessor；不重用舊nonce、不清除原歷史、不發ordinaryReject。
- Revoke/Supersede/再次Accept以Candidate decision revision＋exact active AcceptanceID序列化；兩個action爭同A僅一個成立。Supersede須同時驗replacement B已有效accepted且同Task/scope，拒絕self/cycle／失效B；不能默默接受replacement。
- Accept與policy/eligibility revision原子檢查。Store pin內容、接受時校驗refs/hash；缺損即阻擋。Revoke不要求mandatory PASS，但仍需Human auth、exact view與anti-replay。同command重送回原receipt，不追加事件。

已accepted的Candidate後續不認可只用AcceptanceRevoked／Superseded。V1無Override Accept；required FAIL/MISSING/ERROR/TIMEOUT/SKIPPED/STALE/MISMATCH不得被Human action改成VERIFIED。

### 9.7 Decision audit、遷移與驗收

保存DecisionID、CandidateID、review round、AcceptanceID／predecessor／replacement AcceptanceID（適用時）、action、prior/current revision、principal reference、authentication method/trust scope、server timestamp、command id、view digest、evidence/verification/policy refs、reason/finding refs／optional note、receipt。Audit 可記拒絕 request 的安全 reason，但不含原 token／nonce／session 秘密或未清理 payload。

Decision與AcceptanceRecorded／Revoked／Superseded都是append-only facts；current acceptance disposition、review狀態與verification eligibility分別導出。HumanAccept 不是一筆被修改成 PASS 的 HUMAN_EVIDENCE。Legacyactor 字串／舊 token 不回填新 trusted principal；import 的外部 decision 為歷史來源，不授予當前 Human 權限。

W5測Human-only authority、Agent credential越權、origin/CSRF/XSS、expiry/replay、exact view mismatch、idempotency及R2 races。Persistent方案須測grant安全儲存、revocation/expiry跨restart有效、已消耗nonce不可重用、receipt可查；re-pair方案須測fail closed與重新認證後history可查。兩者均不得因restart/clock異常恢復撤銷權限或延長challenge。**不以restart必須重新pairing作唯一expected behavior。**未通過維持D11-C，W5不完成。

## 10. Continuity / Handoff Contract

Task／Context／Work／Evidence Continuity，不承諾 Provider-nativeSessionPortability。NATIVE/MANAGED/NONE 仍是 Provider Resume capability。

Continuation manifest 為 immutable reference package：Task 與 requirements、baseline/Git provenance、workspace observation／ownership、ChangeSet/Candidate、completed/pendingwork（claim 與 verified 分開）、Findings、ContextPackage exactrefs、artifacts/evidence/verification/decisions、runtime/environment snapshot、nextaction/scope/stop condition。

ContextPackage 回答「該知道什麼」；Continuation 回答「如何安全接續」。生成時的 CLEAN/ownerfacts 不是接收時真相；receiver 重新驗 refs/hash、input freshness、environment、writer 是否仍存活與可用權限。必要 ref 缺失則 blocked，不以模型補文當正式恢復。

Agent A→B 先確認 A 停止／ownership 轉移，MANAGED 通常建立新 Run/session；session 消失不刪 Task。Package 中的 nextprompt 不是遞迴 delegation 或 filesystem/process/Git 授權。Human 可先開啟成果，並明確執行 TakeOverWorkspace；不能由 package 自行啟動執行器。

## 11. Artifact Publication Contract

SQLite 存 metadata／facts，filesystem 存 content；Core-controlled store 統一驗 hash／解析 ref。Context、ChangeSet、Candidate、EvidenceSet、Continuation 皆可用 Artifact 支撑，不必為每個 manifest 另建大型 storage 系統。

Publication 順序：

1. 在受控 staging 写 blob/manifest，確認完整與 size/hash、path/support policy、必要 refs 可解析；失敗保留有界 diagnostic，不發布 Candidate。
2. 將驗證內容發布到不可變 content 位置；同 hash 既存時驗內容，不覆寫為不同 bytes。
3. DB 短 transaction 加入 publication、references 與 durablefact；成功後才能對外列 published。
4. Crash 在 DB 前只留下未引用內容；Crash 在 DB 後以 manifest/ref 驗证恢復。不存在跨 DB / FS 的假原子 transaction。
5. Missing／corrupt content 使相關 verification/acceptance view 不可用或 stale；不得從最新 workspace 重建後沿用舊 hash。

Acceptance/decision 引用的 artifacts 須 pin 住直到明確 retention 政策允許解除；清理只作用於已證明未引用且超過保留期內容。Secret 檢查／輸出 redaction 不能原地改 immutable blob：產新 derived artifact 並標其來源；若必須移除敏感原件，標 loss/redaction，不能聲稱原 evidence 仍完整可重現。

## 12. Persistence Facts / Derived Views

| Persistent facts／records | Derived view（不作另一套 truth） |
|---|---|
| Task／requirements/context revisions、input selection、WorkGenerationRef及control revisions | Task目標、exact generation意圖、Run歸屬與待辦摘要 |
| Run/binding/lifecycle、launch/stop/cleanup observations | running/stopped/needs-recovery 畫面 |
| Workspaceidentity、claim generation、Git observations | CLEAN/HAS_CHANGES/CONFLICTED 與能否安全接手 |
| Immutable manifests＋publication／source links | Candidate 列表、diff 展示、同內容去重關係 |
| Check observations、EvidenceSets、VerificationRecords、policy revisions | mandatory satisfaction、freshness、TESTED/VERIFIED／warning |
| HumanDecision／AcceptanceRecorded/Revoked/Superseded／review round／receipts | review disposition、current acceptance disposition與append-only history |
| Continuation/export manifests 與 completed operation facts | 可接續／可攜狀態 |

必要的 application facts 可以是 typed record＋append-onlyevents；不把全部 event 當完整 event-sourced 系統要求。當前`RunEvent`僅 Run transition，需另有產品 fact representation；不能以 reasonstring 解析 HumanDecision。

Mutablesecuritysession／nonce 狀態屬專用 authboundary，不混進普通 Domain／portablebundle。將可移動 repo/pathresolver 與 portablelogicalIDs 分開。

本輪不建立 DB schema。後續 schema 設計須證明：唯一 identity／referentialintegrity、CASrevision、idempotency receipt、decision 與 nonce 原子性、retentionreference 與 legacy classification。Alembic 是 migrationauthority，不用 create_all 冒充 upgrade。

## 13. Startup / Shutdown Contract

SETUP 完成可理解的依賴、支援 repo/executor、DB/artifact location 與 Humanpairing。START 入口可為`scripts/start_dev.ps1`，分開顯示：schema ready、Core ready、UI paired、executor ready、workspace recoverable。

Startup 先確認 migrationhead／FK 設定與必要完整性，再 reconcile 非終止 Run／ownership。正常未啟動 CREATED 不阻擋 startup；未知舊 writer 使對應 scope 不可新寫，不伪裝 ready。禁止啟動時默默對 Human repo reset 或清除 worktrees。

Shutdown：拒收新 start，記停止意圖，對 active execution 發 bounded cancel/cleanup，flushdurable facts，再關閉本次服務。停不下來時顯示未安全停止並保留恢復資料；不殺所有同名 python/node 或把 UI 關閉當 cleanup 完成。

Crash 不保證最後一段 live output 保存；不得遺失已 commit 的 intent/decision/evidence 索引。Restart恢復durable history；Human pairing/session依§9安全持久或重新認證方案處理，challenge仍需可驗證expiry與anti-replay。RESET 分 client pairing／appdata／fixtures，破壞性操作另有明確 scope/confirmation；不動原 Human repository。

先處理 StabilityP0：FK initialization 及既有資料 audit、CREATED restart、UI/Corepairing。WAL 仍 WAL_NOT_REQUIRED_YET；journalmode 不替代短交易、backup/ref 一致性或 process recovery。

## 14. Monitor / Event Contract

### 選擇比較

| 方案 | 優點／限制 | 裁定 |
|---|---|---|
| REST polling 只有 memory 狀態 | 容易但重啟丟 truth | 不接受 |
| **REST polling＋durable facts/events** | 最少連線生命週期，容易 refresh/resume；有有界延遲／讀取成本 | **First vertical 選用** |
| WebSocket only | 即時但連線掉線不保 truth | 不接受為 truth 來源 |
| REST/durable＋WebSocket | 可降低延遲，需 reconnect/auth/backpressure 等 | 可 NEXT；不阻塞首 vertical |

提案 polling default：前景 activeRun 約 2 秒、idle 較低頻；失敗 backoff 上限約 10 秒並顯示最後成功觀察時間，避免無界 busyloop。頻率是可調參數，不是成功率／latency 保證。

Query 返回 durable snapshot＋revision／cursor；eventquery 支援 bounded pagination、穩定 sequence 及 aftercursor。客戶端按 eventID 去重，不能用本機時間猜順序。若 event 與 snapshot 分開讀，server 需提供可對齊的 high-water mark 或要求重新取 snapshot，不能混合成不存在的狀態。

Cursor 過期／有缺口，回明確 resyncrequired 並重取 truth；polling 失敗顯示「連線中斷／狀態未知」，不能把 Run 設 FAILED。Cancel／Accept 的 command receipt 可重查，不能因 response 掉線重複執行副作用。

Audit 必需的 lifecycle/decision/evidence facts 持久化；逐 tokenstream、heartbeat 可 live-only。Logs 可作 bounded artifacts 依 offset 讀取；流量／儲存有上限。未來 WebSocket 只是推送同樣 revision/event references，斷線回 RESTresync。

**R5：Target Architecture Capability與First Vertical Exit Criterion分開。** f34的ADR-004原文為「REST commands/queries + WebSocket live events + Durable Event Ledger」，並要求live connection loss不遺失durablehistory；未寫First Vertical或W1–W6必須先完成WebSocket。因此保留其target方向：durable state=truth、REST polling=First Vertical delivery、WebSocket=optional NEXT live delivery。**本輪不提出ADR-004核心或scope amendment。** 此為交付分期說明；只有後續發現正式authority明確要求firstvertical先有WS，才提出精確scope amendment，不能因MVP延後就改ADR。

## 15. Portability / Export Invariant — P0 與 N1（R6）

Company-owned State的可匯出／可重建邊界繼續是Architecture Invariant。**分期降低產品化廣度，不取消portability。** 原package完整selected-task要求移至N1；P0聚焦一份accepted成果與其必要接受依據。

### 15.1 P0 Minimal Portable Accepted Package（B01 exit requirement）

Logical command為ExportAcceptedPackage，綁exact AcceptanceID／CandidateID與export時的已知current disposition；不使用浮動latest。

| 最低內容 | P0要求 |
|---|---|
| Task | Task identity與該accepted成果的關聯；不要求整個Task事件史 |
| Goal／Scope／AC | exact RequirementSnapshot與ValidationContract，含validation所必需的semantic context closure |
| ChangeSet／Candidate | canonical manifests／IDs，Core推導的changed entries、baseline/result snapshot refs |
| Reconstruction-required source bytes | 足以從空目錄重建accepted Candidate的base/result必要bytes；不依賴原remote或provider session；僅有patch＋不可取得base SHA不合格 |
| Evidence | 該Acceptance引用的EvidenceSet、required evidence及必要artifact bytes／provenance；不把完整歷史artifacts塞入P0 |
| Verification | 引用的VerificationRecord、mandatory policy/validation revision及適用性／結果 |
| Human Decision | 該AcceptanceRecorded、trust scope、必要predecessor/revocation/supersession引用closure（若當時存在）；不含credentials |
| Manifest／hashes | format version、scope、object index、size/hash、relationships、completeness／排除說明 |

Selected-scope closure必須完整：候選／接受／驗證必要ref不得dangling；普通未選history可排除並標scope。若必要ref本身指向Context或artifact則帶其必要closure，但不擴成全部Context／Continuation／history。已撤銷的歷史接受可另匯出，但明確標歷史／revoked；不能宣称仍是目前有效accepted成果。

P0必須能：**verify bundle**（hash、required refs、exact Candidate/Acceptance/evidence關聯）及**reconstruct accepted Candidate**（空目錄重建bytes/modes，再由Core規則重新推導Snapshot/ChangeSetID）。不依賴provider private session、原runningCore或原remoteGit。工具／套件／OS/secrets不必打包；重建source與接受依據不等於保證新機器立刻可執行所有tests。

Source/filter／mode不受支援時明確阻擋，不截斷成假完整包。Secret／policy／缺檔使required closure不成立時回INCOMPLETE，不用檔案存在或exit0宣稱完整。Redaction產新artifact並記限制，不冒用原hash。Human選scope/destination，不自動上傳。

### 15.2 N1 Full Selected-task Portability（不阻塞B01）

完整Task/Run/generation/decision history、Continuation package、full selected artifacts、expanded environment metadata、offline history navigation、import namespace及更完整relationship browsing排入N1。此處保留原package的格式版本、stable IDs、source/history來源與trust邊界；**不列為W1–W6/B01必須先完成的產品化功能**。

沒有實測成本證明時不將N1偷偷拉回P0。P0可有最小可讀summary／manifest和檢查／重建工具，不要求完整離線UI、双向import/merge或通用interchange standard。

### 15.3 兩階段共用安全與真實性邊界

資料重建不執行embedded workflow／hooks／scripts；拒絕absolute/traversal/reparse paths、hash/size mismatch、zipbomb／超限內容。重建在新空目錄或明確安全目的地，不覆寫Human dirty workspace。

Imported／exported Human Decisions只保留來源歷史與trust scope，不攜帶配對秘密或賦予新本機Human authority；再次執行／接受須當地policy／可信session。N1 import namespace避免logical ID誤合併；P0不需要先完成平台級import功能。

Retention仍保住被決策引用的必要內容。分期不允許丟失N1所需durable facts；只延後其完整export/navigation產品化。

## 16. Migration Impact

| 範圍 | Before → proposed after | 最小遷移／風險控制 |
|---|---|---|
| Canonical／dirty overlays | f34 只作 designbase；localb87dirty 混合 | 本輪不切換／整併。未來實作 lane 另授權並保全 overlays |
| Candidate identity | 未有正式 durable Candidate → Model B 兩層 manifest | 無需先替不存在 table 改 schema；既有 artifacts 不可猜測回填 trustedCandidate |
| Context/Evidence | shallowfrozenmapping／generic metadata → versionedimmutablebinding | reader 相容 legacy；標 unbound/legacy，不能整批升格 verified |
| Work／decision events | Run transition／模糊generation → exact WorkGenerationRef及分離review/acceptance lifecycle | 不從legacy Run猜generation或把ACCEPTED改Rejected；來源不明標legacy/unbound |
| D11 | C fail closed → A-LP Human-only boundary＋C fallback | pairing/session可安全持久或重新pair；W5驗expiry/revocation/replay，無固定restart UX或TTL |
| Workflow | frozen vocabulary 保留，真實 minimum 語意补足 | 既有 workflowversion 不原地改；unsupportedrealnodes 明確拒絕 |
| Monitor | 保留ADR-004 target；REST/durable first、WS NEXT | 交付分期，不改ADR核心；無firstvertical強制WS原文，不新增amendment |
| Runtimebinding | 現有 0002／binding-first → explicit workspace/control provenance | 修改 typedcontract 前走 ADR；不要用 prompt/metadata 逃避 persistedbinding 審查 |
| SQLite | FK 初始化 bug → 每 connection 正確 enforcement | backup 後 foreign_key_check 及 application relation audit；不自動刪 orphan；WAL 不附帶強制 |
| Artifact／export | P0 accepted package closure/reconstruction；N1 full task portability | P0不強迫完整history/import；pin必要artifacts，既有資料不丟失 |

Migration schema revision／tablelayout 留給被批准契約下的 implementation design，**本輪不建立或執行 schema**。實作前需以 f34 含 0001/0002 的代表性 legacyDB 演練升級／讀取／restore；新 records 一旦有無法向舊 schema 無損表示的資料，rollback 用成對 backup/restore，不做假無損 downgrade。

## 17. 仍需 ADR Change 的最小集合

不把每個command、測試或MVP分期都改成ADR。以下只保留需要正式記錄的高耦合contract變更；本輪不修改正式檔案、不分配新ADR號碼。

| 最小集合 | 需正式記錄的決策 | Existing authority／impact |
|---|---|---|
| **M-IDENTITY / OUTCOME** | WorkGenerationRef与Task/Run/Candidate分界；Core-derived Model B；pre-acceptance Reject與post-acceptance revoke/supersede；exact Candidate verification／typed evidence的關聯 | 以一份聚合的Domain/Artifact/Acceptance contract決策記錄，對照ADR-008及既有gate语意；必要schema／legacy mapping另列。原CP-IDENTITY/COMMAND/VERIFICATION合併，不各建ADR |
| **M-HUMAN** | D11-C之外的A-LP Human-only principal、credential separation、bounded/revocable session、exact-view challenge、anti-replay/idempotency、CSRF/origin、append-only decision | D11與ADR-010的精確演進；不凍結TTL或強制restart re-pair。原CP-DECISION收斂至此 |
| **M-EXECUTION（條件式必要）** | 若明確cwd/workspace control/provenance需改公開Adapter contract或persisted RuntimeBindingSnapshot，記typed contract及compatibility | ADR-007/011既有frozen邊界；若完整以既有contract的composition/resolver安全實現且無語意改變，僅implementation mapping，免新增ADR。W2前完成boundary判定 |

**不再列ADR change：**
- CP-MONITOR移除：ADR-004保留WebSocket target capability；R5只調整firstvertical delivery criterion，原文無mandatory-firstvertical條件。
- CP-PORTABILITY不另成ADR：可匯出可重建invariant已接受；P0/N1是scope／acceptance分期，維持ADR-008 filesystem artifacts＋metadata方向。
- Stack、UI/Core boundary、secret boundary、fixed node vocabulary不變。CONTEXT、AI_TASK、TOOL、EVIDENCE_CHECK、HUMAN_GATE不需新node type。
- Session時間、持久pairing方案、polling頻率、檔案大小上限是有安全bounds的implementation policy與測試參數，不是新增architecture freeze項。

Formal updates須以Human Freeze Review結果為依據；不是本檔寫出名稱就已修改ADR。Implementation仍需後續明確授權。

## 18. Test / Benchmark Mapping

所有以下皆為**未執行的驗收規劃**；不是本輪 PASS。每個 scenario 保存 exactsource、commands、actual exit codes、observedsideeffects 與禁止副作用證據。

| Case | 契約驗證／必須看到的結果 | Dependency |
|---|---|---|
| B01 Python bug fix | 真實修改→freeze→requiredtests→HumanAccept→OpenAcceptedResult；原 dirty workspace 不變 | S0、W1–W6 |
| B02 Multi-file refactor | 多檔／新增刪除／mode／binary capture 與 scope 不漏；same content 不同要求 ID 測試 | W3/W4；NEXT 深度 |
| B03 FE＋BE | 跨層 API/browser oracle、context／contract 一致 | W4/W6 後加深 |
| B04 Failing test repair | Writer 弱化／skip required tests 不能過；optional SKIPPED 不假失敗；N/A 須可信 predicate | W4 |
| B05 Crash recovery | before/afterlaunch、Core crash、childwriter、cancel/timeoutcleanup、acceptcommit 後掉 response | S0/W2/W5 |
| B06 A→B | sequentialownertransfer、同 Task/Evidence continuity，providerA session 不在仍可接續 | W6 後第二 executor |
| B07 False implementation | 文字成功／錯檔／偽造 TOOL_EVIDENCE／Agent 直接 accept 皆被拒絕 | W4/W5 |
| B08 Provider unavailable | readiness 與 launch/auth/midrunfailure 分類；無 silentfallback，Task 保留 | W2 |
| B09 Stale context | requirement 變化產新 Candidate、requiredstale/mismatch 阻擋；Accept 前 policy change conflict | W3/W4/W5 |
| B10 Dirty workspace | staged/unstaged/untracked/conflict、人類 takeover、受管結果漂移；無自動 reset/apply | W1/W3/W6 |

必加 contract cases（沿 Bxx fixture，不擴成 generic benchmark 平台）：

- R1 termination：Begin/Retry配發g1/g2；late Abort(g1)不cancel R2；Cancel精確target RunID；generation/control revision與ownership fence不同。測Abort/Retry/Start/Publish races與同command idempotency，terminal Run不回退。
- R2 acceptance lifecycle：從未accepted的Accept/Reject race只一方成立；accepted後Reject/ReopenCandidateReview拒絕。測Revoke/Supersede爭同AcceptanceID、replacement狀態競爭、自我/循環拒絕、policy invalidation與新Accept、同command重送；歷史維持ACCEPTED at T1 → REVOKED/SUPERSEDED at T2，projection不重寫舊事件。
- R3 identity：§3.5的固定goldens為mandatory；UTF-8/Unicode/CRLF/empty/binary/mode/add/delete/collision/ordering/large boundary。Core capture、snapshot重新推導、P0重建三路比固定expected IDs；caller提供manifest不得定義ID，display diff完全不參與。
- Verification：REQUIRED/OPTIONAL×結果與 N/A 權限矩陣；零 required、optional FAIL 與 mandatory blocking finding 不同語意。
- R4 D11：pairing bootstrap、origin/CSRF/XSS、Human-vs-Agent separation、bounded/revocable session、nonce/replay/idempotency。持久pairing與re-pair候選方案以同安全標準＋UX測試選定；不把固定TTL或restart必須重新pairing寫成架構驗收值。
- Monitor：polling response 遺失／重複／cursor 過期／Core 重啟，truth 及 decision receipt 保留；斷線 UI 不設 Run FAILED。
- R6／UX P0：TakeOverWorkspace立即顯示Working Copy based on Accepted Candidate <ID>；新修改不改accepted hash。無provider private session／原remote／runningCore時驗P0 bundle並重建accepted source/IDs；必要refs缺失不得標完整。完整history、Continuation、expanded environment、offline navigation、import namespace測試為N1，不阻塞B01。

Test layers：unit 做 pureidentity／policy／CAS 模型；integration 做 SQLite/artifact publication/authreceipts；real process 做 cwd/treecleanup；browser 做 pairing／monitor／decisionview；real executor 做 actual modification。Mock/conformance 只支持相應 contract 層，不代表 real executor 通過。

## 19. Freeze 後 Implementation Dependency Map

這是**Human完成Architecture Freeze Review並另行授權implementation之後**的dependency計畫，並非本輪宣告已freeze或授權。

```text
Human Freeze Review of REV1
 → Human批准必要的正式contract/ADR記錄與implementation scope
 → S0 Stability P0
 → W1 repository / input / WorkGenerationRef / workspace ownership
 → W2 real executor feasibility / lifecycle / exact-generation targeting
 → W3 Core-derived Snapshot / ChangeSet / Candidate / golden vectors
 → W4 mandatory verification / evidence trust
 → W5 D11 Human Decision / acceptance revoke-supersede / Security + UX tests
 → W6 OpenAcceptedManagedWorktree + takeover UX + failure/retry
        + P0 Minimal Portable Accepted Package verify/reconstruct
 → B01 Working Product acceptance / pilot
 → N1 full selected-task portability及已排定NEXT能力
```

| Stage | 必要內容／不得跳過 | Exit evidence |
|---|---|---|
| S0 | FK初始化/既有資料audit、CREATED restart、UI/Core auth基礎 | 真實connection/invalid insert、create未execute再restart、paired client與unauthorized拒絕；WAL不附帶強制 |
| W1 | Human dirty保全、baseline/input、WorkGenerationRef durable mapping、control revision／ownership fence | g1→retry g2後late Abort(g1)不得碰g2；Run/generation mismatch拒絕；single writer |
| W2 | 品牌中立feasibility後才選首executor；cwd、launch、cancel、timeout、child cleanup | 不確定process不新派；Abort/Retry/Start races；必要M-EXECUTION boundary已處理 |
| W3 | Core推導changed manifest，caller不能提供identity；Artifact publication | §3.5固定goldens＋所有path equivalence、collision/oversize拒絕；partial capture不可publish |
| W4 | REQUIRED/OPTIONAL/N/A、oracle/provenance、exact Candidate＋freshness | optional SKIPPED不自動FAIL；required invalid阻擋；B04/B07/B09 |
| W5 | A-LP human-only contract、short-lived challenge、revocation/idempotency、R2 events | Security＋UX決定持久pairing或re-pair；期限/clock/restart/replay、Accept/Reject/Revoke/Supersede/policy races |
| W6 | 開啟accepted副本、takeover即切Working Copy label、一次failure/retry；**P0包驗證及accepted source重建** | B01/B05/B10與P0閉合refs/hash/rebuild；原Human dirty不改 |
| N1 | 完整Task/generation/Run/decision history export、Continuation/full selected artifacts、expanded environment、offline history navigation、import namespace | 較完整selected-task closure/navigation/import trust測試；**不阻塞B01** |
| 其他NEXT | 原計畫B02/B03深度、standalone patch UX、external CI、第二executor/B06 | 共用identity/evidence/acceptance；非本輪新增scope |

REST polling＋durable facts/events在W1–W6提供最低monitor；WebSocket保留target，optional NEXT，**不阻塞W1–W6**。S0必要修復先於正式realverticalexecution；purecontract規劃不受P0未修完阻塞。

W5開工前Human-only/D11 contract須已完成正式批准；S0先做pairing也沿用同一邊界，不建臨時接受通道。Secure TTL/defaults、session persistence不得由「方便UX」降低已批准threat scope。

保留原九項Pilot metrics與Direct Agent+Git+CI比較、failure/retry、Pivot/No-Go。N1完整portability不得因沒有實測成本證據而悄悄回到P0；也不得用分期作為丟失durable history的理由。

## 20. Explicit Non-goals

本輪／第一 vertical 不做：大規模 implementation、改 frozenADR、newreleasebaseline、自动 commit/merge/push/release、Accept 自動 apply 原 Human workspace、Override Accept、parallelcodingwriters、Enterprise IAM／small-teamattribution、hostile-code 安全保證、provider-native 跨品牌 session 移植、genericBPM／任意 scriptnode、distributed scheduler、multi-tenant、大量 providers、Council breadth 或 ProductBrain 實作。

也不建立完整interchange standard、雙向merge/import平台、第三方不可竄改認證體系或remote audit service。P0只交付Minimal Portable Accepted Package；N1完整selected-task portability不得成為B01前置。Session固定時間與restart重新pairing流程不列freeze invariant；不取消bounded expiry／revocation或安全邊界。

## 21. Open Human Decisions — Freeze Review 範圍

Product Direction／Target Logical Architecture、Model B原則、D11-A-LP方向、REST/durable First Vertical minimum、Portability invariant已接受；不重新展開Discovery或要求再次選品牌／stack。

本輪沒有待补充的業務資訊。Human只需審查：
1. R1的WorkGenerationRef/control revision與exact-target行為是否符合限定一輪工作的要求。
2. R2的AcceptanceRecorded/Revoked/Superseded與current disposition是否符合append-only，沒有ordinary Reject捷徑。
3. R3的Core-only derivation、exact canonical fixture profile／golden vectors是否可作W3驗收依據。
4. R4–R6的freeze-vs-policy、Target-vs-delivery、P0-vs-N1界線及takeover UX是否精確納入。
5. §17最小ADR集合與§24規範性invariants，是否可進入Human-controlled freeze gate。

不把session persistence實作方案、TTL值、table layout、thread primitive或provider品牌丟回Human作本輪阻塞。這些在freeze後授權的implementation/design tests決定，不能降低已接受invariants。

本檔完成即停止；不自行形成Architecture Frozen／Implementation Authorized或Git操作授權。

## 22. Evidence、Closure Check 與 Final Verdict

本輪只讀原package／已知輸入與R1–R6相關段落；另精確核對f34的ADR-004原文（未規定First Vertical必須先完成WS），未重新展開Product Discovery。沿用原package已接受且未被修訂的能力／限制；原文件不覆寫。

修改前對Git列出的2,181個既有tracked/untracked路徑建立記憶體內SHA-256保全指紋；REV1是唯一新交付，不新增diagnostic檔案或handoff delta。Gate1/1.5/2舊report、正式Scope/ADR/PRD、產品code、Git HEAD／staged state均保持原狀。

§3.5 expected fixture digests已以受限canonical JSON與.NET SHA-256計算，相關診斷命令exit0；只計算規格向量，**未實作Core derivation、未執行cross-path／cross-platform產品測試**。Product tests、real executor、W5 Security＋UX、P0重建、migration均SKIPPED（本輪僅文件）。向量不是用未來被測production程式產生，不以其存在宣稱conformance PASS。

| Required amendment | 收斂位置 | 已完成的契約修正 |
|---|---|---|
| R1 | §2、§12、§18–19 | WorkGenerationRef、Retry/Abort exact target、Run/Task/Candidate分離 |
| R2 | §2、§9、§12、§18 | acceptance revoke/supersede、history projections、races |
| R3 | §3.2／3.5、§18 | Core-only changed manifest＋固定golden inputs／expected hashes |
| R4 | §9、§13、§19、§24 | bounded/revocable security invariant；TTL與restart pairing為policy |
| R5 | §14、§17、§19 | target WS保留、REST first；不作不必要ADR churn |
| R6 | §15、§18–19 | P0 accepted package／N1 full selected-task portability |
| Takeover UX | §4、§18–19 | Working Copy based on Accepted Candidate <ID>，不冒充immutable result |

本輪交付狀態見本檔末尾；以下delta與invariants也是同一份Freeze Review的內容。


## 23. 修改前後 Delta（完整修正索引）

| 項目 | 原package | REV1 | 保留／不擴張 |
|---|---|---|---|
| R1 identity | AbortWork提work generation但無可定位ID | Task-scoped WorkGenerationRef=(TaskID,generation_revision)，另有control revision；Core Begin/Retry配發，Run/publication固定引用 | 不新增Attempt Aggregate／大型Domain，不把generation放入Candidatehash |
| R1 retry target | 可能被解讀為停止Task latest | Retry g1→g2；Abort(g1)只停止g1，Cancel仍RunID | history永不被Abort；新generation不自動繼承旧cancel |
| R2 decision | accepted後可重開review再Reject | Reject/Reopen僅從未accepted者；accepted後Revoke/Supersede，綁AcceptanceID；再接受新AcceptanceID | Acceptance at T1永久保存；policy stale≠自動Human revoke |
| R3 derivation | canonical changed manifest未限定producer | Core從verified baseline/result Snapshots推導，caller manifest不作identity input | Display diff不hash，Model B不變 |
| R3 goldens | 只有測試方向 | exact byte fixtures、canonical object profile、13個valid ChangeSet expected hashes及collision/oversize拒絕cases | 僅文件向量與數值診斷，未新增產品tests/code |
| R4 persistence | Core restart使session失效並要求重新pairing | 可安全持久grant/session或re-pair，由W5測試決定；nonce/expiry/revocation不妥協 | 不降低local-personal threat boundary、不加Enterprise IAM |
| R4 time | 5/15min、8hr、2min建議易被freeze | bounded期限為invariant，具體時間為secure defaults／implementation policy | passive polling不延長Human session；decision challenge仍短效 |
| R5 monitor | WS延後被視為需ADR-004 scope改動 | 讀原文無First Vertical硬要求，保留target WS；REST/durable為W1–W6minimum | 移除CP-MONITOR change，無新realtime infrastructure |
| R6 P0 | 完整selected-task portability都列W6 | 最小accepted package閉合必要refs、驗bundle/重建source為P0 | portability invariant不取消、provider session非必要 |
| R6 N1 | complete history／Continuation／navigation／import在首slice負擔內 | full selected-task artifact/history/environment/navigation/import namespace移N1 | 不丟durablefacts，不新增大interchange標準 |
| UX | takeover後只概稱working copy | 明文顯示Working Copy based on Accepted Candidate <ID>，drift不可沿用immutable badge | OpenAcceptedManagedWorktree不變、原Human dirty不改 |
| ADR/dependency | 七個proposal皆近似需ADR | §17兩組必要contract記錄＋execution條件式；WS/分期不另改ADR | 正式檔未改，freeze與implementation仍需Human後續gate |

其餘原package的Product Persona／First Vertical、logical boundaries、runtime能力門檻、verification required/optional/N/A、Evidence trust、Context/continuity、Artifact publication、SQLite/FK/WAL判斷、pilot metrics與non-goals沿用。沒有重開Discovery或加入新的產品方向。

## 24. 正式 Architecture Invariants — Freeze Review 清單

以下為已接受方向加R1–R6精確化後的**規範性候選清單**。列為invariant不等於本Agent宣布已freeze；最終由Human Freeze Review確立。

| ID | 必須保持的架構規則 |
|---|---|
| I-01 | Exact design/read baseline為f34e6b29ae9e7326d1d44b9b03756b450809928f；採納不授權覆寫dirty/untracked或操作Git歷史 |
| I-02 | Local-personal／Single Human／Single Active Writer／Managed Git Worktree；worktree是workspace isolation，不是hostile-code sandbox |
| I-03 | TaskID、WorkGenerationRef、RunID、CandidateID分開；Abort exact generation、Cancel exact Run、Reject exact pre-acceptance Candidate；不target浮動latest |
| I-04 | Retry新generation，歷史ref不重用；ownership fence可追溯generation/Run且不能被當成Task/候選identity |
| I-05 | Model B：ChangeSet識別固定內容，Candidate綁內容＋要求/validation；Core從snapshots推導identity-definingchanges，caller/display diff不提供truth |
| I-06 | Snapshot/ChangeSet canonical bytes/hash可重現，必要source完整可取回；same supported bytes/manifest跨路徑同ID；collision/invalid/partial不得publish |
| I-07 | Writer quiescence→freeze Candidate→exact verification；Verifier改內容必須新Candidate、重新驗證 |
| I-08 | Requirement／applicability／outcome／validity分離；required不合格不得滿足mandatory；optional SKIPPED不自動FAIL；N/A不可偽造豁免 |
| I-09 | Evidence/Verification/HumanDecision綁exact Candidate；新增Evidence不改Candidateidentity；AI Opinion≠verified tool evidence |
| I-10 | Human Accept僅於當下mandatory policy滿足、fresh exact view成立；無Override；不改FAIL/MISSING/ERROR/TIMEOUT/SKIPPED(required)/STALE/MISMATCH |
| I-11 | Human Decision append-only；accepted後不認可以AcceptanceRevoked/Superseded，不能改成ordinaryReject；current disposition由歷史導出 |
| I-12 | Human-only principal與Agent credential分離；bounded/revocable session、短效exact-view challenge、nonce/anti-replay、idempotency、CSRF/origin、稽核一致性 |
| I-13 | Session安全性不依固定TTL或強制restart重新pairing；持久／re-pair方案須同等保持revocation/expiry/replay與已批准local-personal threat scope |
| I-14 | Identity／Git Observation／Ownership／Recoverability四軸；lease expiry、CLEAN或未知process不代表可安全派新writer |
| I-15 | 原Human dirty預設不带入不修改；dirty input需Human明選snapshot；TakeOverWorkspace轉Working Copy label，accepted artifact不隨workspace漂移 |
| I-16 | Accept不auto commit/merge/push/release/apply；OpenAcceptedManagedWorktree為首vertical取用；新編輯不冒充immutable Accepted Result |
| I-17 | Durable state/facts/events=truth；REST polling為First Verticaldelivery；WebSocket保留target、optional NEXT，掉線不丟Run truth |
| I-18 | Company-owned state可匯出可重建；P0 accepted package必要closure與source重建不依provider private session；N1完整portability不阻塞B01 |
| I-19 | Task/Context/Work/Evidence Continuity≠native session portability；NATIVE/MANAGED/NONE僅provider resume能力；handoff不授予delegation |
| I-20 | Core deterministic boundary掌握副作用；Provider-specific只在Adapter/Driver；Brain不繞過Core、不得第二executiontruth |
| I-21 | 現stack、repository/persistence邊界保留；Alembic authoritative；immutableArtifact與secret隔離；固定workflow vocabulary不擴張 |
| I-22 | Feasibility先於選executor；真實cwd/change/cancel/timeout/process-tree cleanup/provenance/auth/failure證據，不能用simulator成功替代 |
| I-23 | 必要Stability P0先於正式Working Productexecution；P0/N1按§19交付，不以規劃或golden數值宣稱產品PASS |

**明確不凍結為invariant：**具體session／pairing/challenge時間、restart re-pair UX、持久session的實作儲存形式、polling頻率、測試fixture的L檔案上限、DB table layout與library選擇。它們在後續授權範圍用Security/UX/compatibility tests決定，不得違反以上invariants。


**最終裁決：READY_FOR_ARCHITECTURE_FREEZE_REVIEW。**

**Architecture Freeze：HOLD。Implementation：NOT AUTHORIZED。** 完成REV1後停止，等待Human Review。

