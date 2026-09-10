# PolyNexus Formal Contract / ADR Change Plan

- 日期：2026-09-10。
- Authority：Human 已接受 REV1、I-01–I-23 且 Track A V1 Architecture APPROVED / FROZEN。參見[Freeze Record](POLYNEXUS_TRACK_A_V1_ARCHITECTURE_FREEZE_RECORD.md)。
- Canonical read SHA：`f34e6b29ae9e7326d1d44b9b03756b450809928f`。
- **僅規劃如何同步正式文件；本輪不修改 ADR／Scope／PRD／SA／SD／Decision Log，不做 schema 或產品 implementation。**
- 本計畫不重審 R1–R6 或 Product Direction；正式 wording／diff 批准與產品 implementation 授權是後續獨立 gate。

## 1. Authority 與同步邊界

新 Human Freeze 優先於舊文件中的 HOLD／未實作 architecture 描述；既有產品能力仍以實作／實際 evidence 判讀，Freeze 不能把 NOT_IMPLEMENTED 改成產品完成。

目前 authority 定位：
- `docs/00_SCOPE_BASELINE.md`：Product-first/Personal-first 及既有 maturity/範圍。
- `docs/10_DECISION_LOG.md`：D11 Option C；不可信 actor/token 不能核發 Human verification。
- `docs/18_ARCHITECTURE_DECISIONS.md`：ADR-004 UI/Core、ADR-007 Supervisor/Adapter、ADR-008 Artifact/Context、ADR-009 固定 workflow、ADR-010 secret/security。
- `docs/29_ADR_011_RUNTIME_BINDING_AND_TRANSPORT.md`：Run-owned immutable RuntimeBindingSnapshot。
- `docs/01_PRD.md`、`docs/02_SA.md`、`docs/03_SD.md`：產品／logical boundary／實作契約描述；精準同步受影響段落，不全檔重寫。
- 已接受[REV1 §17](GATE_2_CONTRACT_ARCHITECTURE_PACKAGE_REV1.md)：兩個必要 formal contract 集合＋條件式 M-EXECUTION。

下列每組都列 current authority、proposed change、affected documents、理由、compatibility/migration/test impact、ADR 必要性、sequence 與 Human gate。子項矩陣是該組必須全部覆蓋的內容，不是新增各自獨立 ADR。

## 2. A — M-IDENTITY / OUTCOME

### Current authority / proposed change / why required

Current：ADR-008 的 content hash／versioned Context、ADR-007/011 的 Run identity 與 binding、既有 Task/Run／Evidence/gate semantics；未完整規定 WorkGenerationRef、Core-derived Model B 與 acceptance 後撤回。

Proposed：以**一份聚合的 identity/outcome formal contract 決策**保存已 Frozen 的 REV1 §2/3/7/8/9/12，並從 ADR 索引連結；不拆成 Attempt、Packet、Memory 新大型 Domain。將最新 Human 的 same-generation lineage 防重要求明列為 idempotency 之外的 domain acceptance criterion。

Why required：否則 generation 與 command replay 容易混淆、caller manifest 可能污染 identity、舊 Run COMPLETED 可能被误讀為 Accepted、post-acceptance 可能被普通 Reject 覆寫。

### Exact coverage / affected documents / tests

| 子項 | 同步內容 | Affected ADR / Scope / PRD / SA / SD | 直接驗收影響 |
|---|---|---|---|
| A1 WorkGenerationRef | Task-scoped ref、immutable inputs、control revision；Begin/Retry 配發，Abort exact generation；同 generation 不能新 command 另開 unrelated writer lineage | 聚合新 contract＋ADR-007/011 reference；SA identity；SD commands/persistence；PRD retry/stop | g1→g2 late Abort；同 generation 雙 command／多入口 race |
| A2 Task/Run/Candidate separation | Run 屬 generation、publication 連 Candidate；generation/Run 不入 contenthash | 新 contract、ADR-008/011 references；SA/SD；PRD history | oldhistory 不改，重送不新增 unrelated execution |
| A3 Model B / Core-derived ChangeSet | Core 從 snapshots 推導，displaydiff 不 hash，拒絕 caller identity manifest；REV1 §3.5 固定 expected IDs | 新 contract／ADR-008 補充；SD canonical profile；SA artifact flow | fixed goldens，source/path/mode/hash mismatch 負例 |
| A4 Candidate freeze / Verification binding | quiescence→freeze→exact Candidate verification，改內容新 Candidate | 新 contract；SA/SD lifecycle；PRD verification/UX；Scope firstvertical acceptance 指向 | tests 修改 source、stale candidate/policy 不可過 |
| A5 Pre-acceptance Reject | 只對從未 accepted candidate；Stop/Abort 分開 | 新 contract；SD commands；PRD UX；SA decision boundary | Stop 不 Reject，Reject 不 cancel，pre-acceptance races |
| A6 Post-acceptance Revoke/Supersede | exactAcceptanceID、append-only T1/T2，current disposition 導出 | 新 contract；ADR-008 reference；SA/SD decision facts；PRD history | Accepted 不可改普通 Reject，replacement/race/cycle 測試 |
| A7 Evidence/Human Decision exact binding | REQUIRED/OPTIONAL/N/A 與 validity 分離；exact Candidate/EvidenceSet/Verification/Policy view | 新 contract＋與 M-HUMAN 交叉 reference；SA trust；SD gate；PRD 驗證顯示 | required invalid 不可 Accept；optional SKIPPED 不假 FAIL |

Scope 只同步已批准 Track A firstvertical 優先序與 P0/N1 邊界／references，不自行刪除舊 baseline 能力、重排 CORE/BASELINE/FUTURE 分級或擴張產品範圍。

### Compatibility / migration / test impact

- Compatibility：保留 Task!=Run、既有 Run terminal semantics、Artifact/Evidence 與 frozen workflow vocabulary；新增 typedfacts/read views，不以 reasonstring 補新 truth。
- Migration：未綁 generation/candidate 的 legacy 資料保留 unbound/legacy；不得猜測回填可信 Candidate/Acceptance。新 persistent facts 的 table layout 及 Alembic migration 由後續授權 task 提出；不能現在建 schema。舊 ambiguously-rejected history 不可自動轉成 AcceptanceRevoked。
- Test：A1–A7 矩陣＋REV1 固定 goldens＋W1/W3/W4/W5 integration；migration 須測 legacy 讀取、不假升格、unique ownership／lineage 約束與 reference closure。
- Rollback：正式文件同步可 revert 該次明確 doc allowlist delta，不重寫 Human 批准歷史；實作資料 rollback 另按 matched backup/restore，禁止以刪新資料假裝無損 downgrade。

### ADR requirement / sequence / Human gate

**FORMAL ADR / CONTRACT AMENDMENT REQUIRED：YES。** 只需一個聚合 identity/outcome 決策，對照 ADR-008 及 Run/gate 相關 authority；不替七個子項各建 ADR。

Sequence：先準備精準 decision/contract diff → Human 核對忠於 Frozen REV1 及本輪 lineage criterion → 同步 ADR 索引/SA/SD 與 PRD/Scope 必要 references → 校驗 crossrefs 與 legacy 標示。M-IDENTITY 正式措辭完成且獲准後，方可作 W1/W3/W4/W5 實作依據；implementation 仍要另授權。

Human gate：**formal-document change allowlist 及內容批准**；不是要求重新決定 Model B 或 Product Direction。本輪只列計畫。

## 3. B — M-HUMAN

### Current authority / proposed change / why required

Current：D11-C 明确 loopback token＋actor_id 不足以證明 Human；ADR-010 維持 secret/permission boundary。現行 Core API token 未建立 Human-vs-Agent 權限。

Proposed：正式記錄 Frozen **D11-A-LP＋D11-C fallback**，並與 M-IDENTITY 的 Decision／Acceptance facts 銜接；不把舊 HUMAN_EVIDENCE 翻成可信 Human approval。

Why required：A-LP 產品通道是對現有 D11-C 的精確演進。Architecture 已批准，但正式可實作 contract 需明確授權 principal、challenge、transaction 與安全測試；不能靠「local-personal」繞過身份檢查。

| 子項 | Proposed change | Affected ADR / Scope / PRD / SA / SD | 直接驗收影響 |
|---|---|---|---|
| B1 Principal / credentials | Human-only principal、pairing 與 Agent credential separation，provider/session 不是 Human | D11／ADR-010 formal amendment；SA trust；SD auth；PRD onboarding；Scope 只 referencelocal-personal 邊界 | Agent 不能 self-pair/decide；actor 字串不可升權 |
| B2 Session | bounded/revocable；可安全持久或 re-pair，TTL 值與 restart UX 不 freeze | D11／ADR-010；SD secure policy；PRD UX | expiry/revocation/restart/clock＋W5 Security/UX 比較 |
| B3 Exact-view challenge | Candidate/Acceptance/Evidence/Verification/Policy refs、short-lived nonce／anti-replay | D11＋M-IDENTITY；SA/SD；PRD exact view | stale/mismatch、跨 session 或 action replay 拒絕 |
| B4 Idempotency / concurrency | auth 後 receipt 重查、同 key 異 payload 拒絕、nonce/decision/revision 原子性 | D11；SD transaction；SA facts；PRD conflicts | Accept / Reject / Revoke / Supersede/policy race、response loss |
| B5 CSRF / Origin / output trust | fixed origin/Host、CSRF 與不執行 Agent content；secret 不入 Domain/export | ADR-010/D11；SA boundary；SD transport；PRD pairing failure UX | wrong/null origin、CSRF/XSS、泄密與 unauthorized endpoints |
| B6 Append-only / C fallback | 不可信 legacy 維持 C；Decision 綁 exact Candidate；accepted 後 revoke/supersede | D11＋M-IDENTITY；SA/SD decision；PRD history | noOverride、legacy 不可升格、T1/T2 真實歷史 |

### Compatibility / migration / test impact

- Compatibility：保留 ordinary loopback client 所需既有受控能力，但不賦予 Human decision scope；缺 Human proof 仍 fail closed。REST 配對 foundation 不能意外解除原 API 保護。
- Migration：新 security persistence 與 ordinaryDomain 分開；不要將現有 actor/session/token 回填為 verifiedHuman。已撤銷/過期 grant 不得在 restart 或 restore 後復活；具體 secure persistence 方案由 W5 驗證。
- Test：B1–B6 正／負例，含 mandatory required invalid states、optional semantics、exact view、nonce、idempotency、races、兩種 restart 設計及可操作 UX。TTL 數值不是架構驗收硬常數。
- Rollback：停用新 Human mutation 入口可回 D11-C fail closed，保留 decision audit 與資料，不放寬為舊 token 可 Accept；security migration restore 需防 revocation 倒退。

### ADR requirement / sequence / Human gate

**FORMAL ADR / D11 AMENDMENT REQUIRED：YES。** 一份 Human identity/decision amendment，保留 D11-C fallback；不新增 Enterprise IAM 或硬體 attestation 目標。

Sequence：M-IDENTITY 固定 decisionrefs → 準備 M-HUMAN 正式 diff 與 Security/UX criteria → Human 批准 formal M-HUMAN → 同步 ADR-010/D11 及 SA/SD/PRD 受影響段落 → 才允許 W5 implementation（另有實作授權）。

若 S0 pairing foundation 已需新增 Human grant/session 而超出現有 client bootstrap mapping，**M-HUMAN 批准必須提前為該 S0 子項前置**；可分開規劃不涉及新 Human authority 的 S0 穩定性修復，不能先造臨時 Accept 通道。

## 4. C — M-EXECUTION：條件式必要性判定

### Actual bounded contract analysis（不是 executor 驗證）

本輪直接讀 f34 以下 symbols：
1. `runtime/contracts.py::RuntimeAdapter`：create_run(context)、submit(runtime_ref,task)、status/result/cancel/cleanup/resume/version_info；無顯式 cwd 參數。
2. `runtime/registry.py`：AdapterFactory 為`Callable[[], RuntimeAdapter]`；register 以 composition wiring 注入 factory，create_adapter 呼叫 factory()並做 compatibility 驗證。
3. `execution_service.py`：constructor 允許 registry injection；`_construct_adapter_or_fail_closed(run_id,profile)`已有 Core RunID，之後建 RunSupervisor(adapter)；binding-first/CAS 語意需保留。
4. `domain/runtime_binding.py::RuntimeBindingSnapshot`：immutable、Run-owned 1:1 provider/runtime/adapter/target/auth/provenance；並未規定必須把所有 workspace observations 存進這一 snapshot。

因此「public method 無 cwd 參數」**不足以證明必須改 public contract**。既有 factory 可封裝 constructor dependencies；Core 可由 RunID 解析已批准的 workspace/generation/control facts，提供受控、run-scoped resolver／immutable launch context 給 adapter。這是靜態可行的 mapping 方案，[待驗證]實際安全性及 real executor 效果；不是宣稱目前已能執行。

### Current decision

```text
M-EXECUTION: NOT REQUIRED / IMPLEMENTATION MAPPING ONLY
BASIS: no demonstrated necessity to change RuntimeAdapter public contract
       or RuntimeBindingSnapshot for the planned mapping
REAL EXECUTOR / RUNTIME MAPPING VALIDATION: NOT YET VERIFIED
```

| 子項 | Current authority | Planned mapping（不改 public contract） | Compatibility／migration／test impact |
|---|---|---|---|
| C1 cwd authority | ADR-007/011，existingfactory injection | Core 從 RunID→generation/workspace authoritative refs 取得 cwd；run-scoped constructor/resolver 注入，不能由 prompt 或 caller context 指定 privileged path | public signatures 不變；test 錯 cwd、cross-run resolver、caller spoof |
| C2 workspace ownership | Frozen M-IDENTITY／I-03/04/14，binding-first | launch 前 persist claim/control facts；adapter 只用 Core 授予的 scope；private composition 在 claim 後建立，保留 registry 選擇／compatibility | 不改 RuntimeBindingSnapshot provider truth；新 workspace facts 的 migration 屬 M-IDENTITY/W1 |
| C3 control provenance / restart | Run durable identity、Adapter lifecycle＋Run-owned binding | Run 關聯的 durableprocess/control observations 重建 resolver；既有 runtime_ref 仍 externalref，不作 canonicalWork identity | 不偷建第二套 provider binding；testrestart、stalehandle／PID reuse、lateabort、cleanup 與 ref mapping |

Scoped factory 不得修改 global registry／共享 mutable「current run」變數；不能以 constructor injection 繞過 profile 選擇、版本檢查、已 persisted binding 或 ownership gate。Readiness/Doctor construction 仍不可偷偷 launch；reconciliation 須能由 persistedRun 及其 workspace/control refs 恢復 scope，不能依賴已遺失的 memory closure。

### Proposed formal change / affected docs / why / gates

- Proposed ADR change：**NONE on current evidence**。保留 ADR-007／011 及 RuntimeAdapter/RuntimeBindingSnapshot 定義。
- Affected ADR／Scope／PRD：不改其方向或新增 provider／transport；只保留相關 contract references。
- Affected SA／SD：後續若獲准同步，只補 composition/resolver、Run→workspace/control facts、restart mapping 與 failure handling。這是 implementation mapping 說明。
- Why no amendment：有上述不改 public surface 的可行 mapping，沒有證據迫使改 frozenpublic contract；不因偏好另一 signature 而引發 ADR churn。
- Compatibility：保留既有 adapter callable signatures、capability truth、binding immutability；新增內部 DI 需 targeted regression。
- Migration：**本 mapping 不要求改 RuntimeBindingSnapshot schema**；W1/control facts 如需 persistence 按 M-IDENTITY plan 審核，不偽裝成無 migration 或複製第二 binding。
- Test impact：W1/W2 boundary tests、observation 無 side effect、per-run 隔離、exactRun↔workspace、restart rehydration 及 real process cleanup。
- Sequence：W1 定義資料 mapping → W2 implementation 前完成 boundedmapping design/negative-test review → 在另行授權的 W2 驗證，不先選品牌。
- Human approval gate：本文件 review 後，mapping 在獲授權 task 內可按既有架構實作；**若實際證明必須更動 public RuntimeAdapter 或 RuntimeBindingSnapshot**，停止該 contract-change 部分，提出具體不可行證據、最小 diff、compatibility/migration/test/rollback 影響，再把 M-EXECUTION 標 REQUIRED 請 Human 批准；不默默改 contract。

觸發例：已批准的 per-run authority 無法透過既有 composition/control facts 持久重建、必須新增或改寫 public method 語意／必填字段／snapshot 字段才能正確運作。單純「加參數比較方便」不是必要性證據。

## 5. Formal-document synchronization sequence

| Step | 工作 | Human gate／禁止事項 |
|---|---|---|
| F0 | Review 本次三份文件；以最新 Freeze Record 定位 authority | 不再交付 REV1／重審方向；implementation HOLD |
| F1 | 準備 M-IDENTITY 與 M-HUMAN 精準 formal contract／decision diff（未執行） | 先 Human 授權正式文件 scope；不全檔覆蓋 dirtyformal docs |
| F2 | Human 批准 formal wording 與 exact allowlist；保留既有歷史實作狀態 | Architecture 已 Frozen 不是 stage/commit/push 授權 |
| F3 | 按批准 diff 同步 Decision Log／必要 ADR entry/index，再 SA/SD，再 PRD/Scope references | 不因同步把 unimplemented 寫成完成，不重編 maturity 為產品 PASS |
| F4 | 驗證 crossrefs、I-01..I-23 一致、D11-C fallback、legacy/migration 與 P0/N1；保留修改前後 delta | independent doc review；不跑產品 migration |
| F5 | Human 另授權 S0/W1 等 exact implementation package | 才可開始相應產品工作；W5 前 M-HUMAN 已正式批准 |

ADR-004 保留 REST＋WebSocket target＋durableevents；REST polling 先交付不需 ADR 核心 amendment。Portability P0/N1 是已批准 deliveryphasing，亦不另建 ADR。正式 Scope 優先序若同步，僅反映已批准 First Vertical，不重新設計產品。

## 6. Status / verification boundary

本輪 source reads、path 定位與 hash inventory 是真實 read-only 操作；上述 formal diff、ADR 同步、schema、runtime mapping、產品測試全部[未執行]。三份新文件檢查屬 document verification，不是 M-EXECUTION conformance 或產品 PASS。

PRODUCT_IMPLEMENTATION：HOLD。NEXT：HUMAN_REVIEW_REQUIRED。不得開始 S0 或修改正式 ADR。

