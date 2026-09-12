# PolyNexus Track A V1 Architecture Freeze Record

## 1. Freeze authority / date

- **Freeze authority**：Human 在本輪「CURRENT AUTHORITATIVE HUMAN STATUS」明確宣告；本文件記錄該既有批准，不由 Agent 自行批准。
- **Freeze date（本對話確認日）**：2026-09-10，Asia/Taipei。Human 未提供更早的外部 Freeze Review 精確時間，本文件不推定該時間。
- REV1：ACCEPTED；Gate 2 Contract Closure：PASS；R1–R6：PASS；I-01–I-23：APPROVED。
- **TRACK_A_V1_ARCHITECTURE：APPROVED / FROZEN**。
- 文件性質：Architecture formalization record；不是產品驗收、實作或 release 授權。
- REV1／舊 handoff 內的「Freeze HOLD」「等待 Freeze Review」是當時歷史。以本次 Human 狀態為準，保留原件而不重交／回寫。

## 2. Canonical Design Baseline / accepted inputs

```text
CANONICAL_DESIGN_BASELINE_SHA: f34e6b29ae9e7326d1d44b9b03756b450809928f
DESIGN_BASELINE_REF: origin/feature/g24-g30-development-completion-routing
BASELINE_USE: DESIGN / READ ONLY
```

| Accepted input | SHA-256（本輪讀取檔案） | 權威範圍 |
|---|---|---|
| [GATE_2_INPUT_BASELINE](GATE_2_INPUT_BASELINE.md) | `2BEFA66EE1D847F6B509589C10F3062922BCDDAED5E097884687712A629B7264` | 已接受產品方向與 Gate 2 輸入 |
| [GATE_2_CONTRACT_ARCHITECTURE_PACKAGE_REV1](GATE_2_CONTRACT_ARCHITECTURE_PACKAGE_REV1.md) | `ACB67374384BC2FEBFF0FF288D739DBA8C92AC93C8A709B43500FC5FA10ED1DE` | 已接受完整契約、R1–R6、§3.5 fixed goldens、§17 及§19 |
| REV1 §24 I-01–I-23 | 以上 REV1 的一部分 | Human 全數 APPROVED，以下逐字保留 |

本輪後續 Work Package 的 same-generation writer lineage 防重要求，來自最新 Human 指示，是執行規劃的必要驗收補充，不能僅靠 command_id idempotency 代替。

目前實作 checkout／dirty overlays 不自動變成此 design baseline；branch 移動也不變更 frozen exact SHA。任何後續實作 checkpoint 須另明確辨認。

## 3. Architecture Invariants I-01 through I-23

以下內容直接取自已接受 REV1 §24，不重新審查、改寫或新增 I 編號。

| ID | Approved invariant |
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

## 4. Frozen product boundaries

Primary 為 AI-augmented Developer／Technical Lead；Secondary 為 QA／Independent Reviewer。First vertical 為一個真實、可重現的 Simple Python Bug Fix，加 Failure → Retry／Recovery 證據。

產品鏈：repository → Task／Goal／Scope／AC → WorkGeneration → real executor → repository change → Candidate freeze → deterministic verification → Evidence → Human Accept → Open Accepted Result → P0 Portable Accepted Package → retained history。Implementation、Run completed、verified 與 Human accepted 不合併為 Success。

PolyNexus 不開發 LLM、不以另一個 Coding Agent 為主要方向。公司持有 Task／Run／context／workspace facts／artifacts／evidence／verification／decisions／recovery；provider session 不作唯一 System of Record。

## 5. Frozen architecture boundaries

KEEP 現有 Python／FastAPI／asyncio、SQLAlchemy／Alembic／SQLite、React／TypeScript／Vite 及 Repository interfaces。UI 不直接操作 DB、Git、filesystem/process 或 vendor events。Core-owned RunSupervisor＋Adapter-owned runtime/vendor logic，未來 Brain 也經同一 deterministic boundary。

TaskID、WorkGenerationRef、RunID、CandidateID 各有責任；Run 不是 Attempt，WorkGenerationRef 不是大型 Attempt Aggregate。固定 workflow vocabulary 保留；firstvertical 映射 CONTEXT／AI_TASK／TOOL／EVIDENCE_CHECK／HUMAN_GATE。

Durable state 是 truth；REST polling 是 W1–W6 delivery；WebSocket 保留 target capability、optional NEXT，不需為 MVP 延期重寫 ADR-004 核心方向。SQLite FK 初始化須修，WAL 不是自動 P0；Alembic 是 schema migration authority。

## 6. Frozen security / trust boundaries

Local-personal、Single Human。D11-A-LP Human-only principal、Human/Agent credential separation、bounded/revocable session、short-lived exact-view challenge、nonce/anti-replay、idempotency、CSRF/Origin、append-only decisions 已批准；D11-C 對舊／不可信 Human attribution 持續 fail closed。

秘密值不進普通 Domain、Evidence、Artifact、log、Git、export 或 handoff。配對／session verifier 屬專用 security boundary。持久 pairing 不代表無期限登入，也不表示 Agent 可取得 Human 權限。

不宣稱抵抗同 OS principal 惡意 process、Enterprise IAM、小團隊個人歸因或 multi-user concurrency。更強 security isolation 需 Architecture Change Control；不能以 UI 便利降低既有威脅邊界。

## 7. Frozen workspace / intent strategy

Managed Git Worktree＋Single Active Writer；原 Human dirty workspace 預設不帶入或修改。必要 dirty input 由 Human 明確選取並固定 snapshot。四軸為 Identity／Git Observation／Ownership／Recoverability，不混成巨大單一 enum。

WorkGenerationRef=(TaskID,generation_revision)，另有 control revision；Abort 精確 target generation，Cancel target RunID，Candidate rejection target CandidateID。Retry 建立新 generation；late Abort(g1)不停止 g2。相同 generation 不能因換 command_id 而產生第二條 unrelated writer lineage。

Lease 過期、PID 變化、Git CLEAN 或沒有新 log，不單獨證明 writer 已安全釋放。TakeOverWorkspace 須先確認 ownership 轉移，UI 標示 **Working Copy based on Accepted Candidate <ID>**；已漂移副本不能再顯示 immutable Accepted Result。

## 8. Frozen Candidate / Verification / Evidence / Acceptance semantics

- **Model B**：ChangeSetID 識別 fixed content；CandidateID 綁 ChangeSet＋Requirement/Scope/AC snapshot＋Validation Contract snapshot。
- Identity-defining changed manifest 由 Core 從 verified baseline/result Snapshots 確定性推導；Agent／Adapter／UI／Caller manifest 與 display diff 不定義 ID。REV1 §3.5 為固定 golden authority，不重新計算替換其 expected IDs。
- Writer quiescent 後 freeze；Verifier 對 exact Candidate 驗證。改寫來源形成新 Candidate 並重新驗證；新增 Evidence 不改 Candidate identity。
- REQUIRED/OPTIONAL、APPLICABLE/NOT_APPLICABLE/UNRESOLVED、execution outcome、evidence validity 分開；optional SKIPPED 不自動 FAIL，required invalid 無法滿足 mandatory。
- Evidence／Verification／Human Decision 引用 exact Candidate；可信來源與 oracle 不可由 writer 自評取代。
- Accept 須當下 mandatory policy 滿足、evidence/verification fresh、exact Human view 成立。V1 沒有 Override Accept。
- Reject 僅用於從未 accepted 的 Candidate review；accepted 後以 AcceptanceRevoked／AcceptanceSuperseded 記錄新事實。ACCEPTED at T1 及 T2 撤銷／取代 append-only 保存；current disposition 導出，不改舊結果為普通 Reject。
- Accept 不 auto commit／merge／push／release／apply 原 Human workspace。P0 取用為 Open Accepted Managed Worktree；P0 Portable Accepted Package 須可 verify 並重建 accepted source，無需 provider private session。完整 selected-task portability 為 N1。

## 9. Explicit non-goals

不新增大量 Agent、Council breadth、generic BPM、新 workflow language、parallel coding writers、distributed scheduler、multi-tenant、Enterprise IAM 或 Product Brain implementation；不保證 native provider session portability 或 hostile-code sandbox。

不 auto commit/merge/push/release；不將完整 history navigation、Continuation export、full selected artifacts、expanded environment metadata 及 import namespace 列 B01 前置。這些為 N1，durable facts 仍保留。

Simulator／mock／reference adapter 成功不代表 real executor 或 Working Product PASS。

## 10. Explicitly NOT frozen implementation-policy items

不凍結 session/pairing/challenge 具體 TTL、Core restart 必須重新 pairing、持久 session 儲存形式、polling 頻率、REV1 測試 fixture 的 L 作產品檔案上限、DB table layout／migration 編號、library／thread primitive／adapter 品牌。

後續獲授權的 implementation 可在 invariants 內選擇以上方式，以 Security＋UX＋compatibility tests 驗證。不得因 TTL 可選就移除 expiry／revocation；不得因 table layout 可選就改 persistent semantics；不得為了測試變綠自行改 golden IDs。

## 11. Architecture Change Control / implementation discretion

**需 Change Control**：改 I-01–I-23、identity／canonicalization profile／golden authority、Human trust/approval 語意、writer ownership scope、public RuntimeAdapter contract 或 RuntimeBindingSnapshot 語意、frozen workflow vocabulary、資料格式 public compatibility、P0 必要產品結果或 non-goals。先提出理由、authority、相容／migration／test／rollback 影響與 Human 批准，不在 implementation 中偷渡。

**不必重開 architecture**：不改契約的內部 module 組織、constructor injection／resolver mapping、query/index 優化、UI 細節、測試 fixture wiring、secure defaults、具體 schema 承載方式及既有規範內的操作參數。Persistent-data migration 與高風險操作仍須任務 scope／授權及驗證；「可自行選工程細節」不等於本輪可開始實作。

正式文件同步計畫見[Contract / ADR Change Plan](POLYNEXUS_FORMAL_CONTRACT_ADR_CHANGE_PLAN.md)。Work Packages 見[Implementation Work Packages](POLYNEXUS_TRACK_A_IMPLEMENTATION_WORK_PACKAGES.md)。

## 12. Product PASS / Implementation / Release status

| Status | Authoritative value／含義 |
|---|---|
| TRACK_A_V1_ARCHITECTURE | APPROVED / FROZEN，由 Human 批准 |
| GATE_2_CONTRACT_CLOSURE | PASS；R1–R6 PASS，是契約審查結果 |
| PRODUCT_IMPLEMENTATION | **HOLD**；本輪未授權 S0 或任何產品實作 |
| WORKING_PRODUCT | **NOT YET ACCEPTED** |
| REAL_EXECUTOR | **NOT YET VERIFIED** |
| B01 | **NOT YET EXECUTED** |
| FORMAL_ADR_SYNC | 本輪只規劃，[未執行]正式文件修改 |
| RELEASE | 未建立新 release baseline，沒有新增 release acceptance／發布授權 |

本轮沒有執行產品 tests、real executor、B01 或 schema migration；不能從 Human Architecture PASS 推導產品 PASS。

## 13. Governance statement

這份記錄保存最新 Human 權威，解決舊文件歷史狀態與當前 Freeze 狀態的時間差，不回寫已接受 REV1。三份新文件只做 architecture formalization＋implementation planning。

Freeze 不授權 checkout/reset/rebase/merge、覆寫 dirtytree、刪 overlays／untracked、建立 release、stage/commit/push 或產品 implementation。正式 ADR 仍須依同步計畫取得文件操作授權；未批准 implementation 前不啟動 S0。

本次唯一允許輸出為這三份文件；因此不追加 handoff、不改 Scope/ADR/PRD/SA/SD。交付後 STOP，NEXT=HUMAN_REVIEW_REQUIRED。

