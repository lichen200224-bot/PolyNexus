# GATE_2_INPUT_BASELINE

- 日期：2026-09-09
- 狀態：**READY_FOR_GATE_2 — PLANNING ONLY**
- Human verdict：Gate 1.5 **ACCEPTED AS PLANNING INPUT / HUMAN DECISIONS COMPLETE**。
- 授權來源：本次 Human Decision；HD-1 APPROVED、HD-2 APPROVED WITH BOUNDARY、HD-3 APPROVED WITH CLARIFICATION，以及 Additional Gate 2 Constraints。
- 前置：[Gate 1.5 評估報告](POLYNEXUS_GATE_1_5_HUMAN_DECISION_BASELINE_2026-09-09.md)。該報告的 NEED_MORE_HUMAN_DECISIONS 是決策前歷史，本次批准已解除該三項阻塞；不回寫歷史裁決。
- 本檔只收錄已確認的規劃輸入。不是產品能力驗收、implementation 授權、正式 Scope／ADR／PRD 修訂、architecture frozen 或新的 release baseline。

## 1. Canonical Baseline

```text
BASELINE_SHA: f34e6b29ae9e7326d1d44b9b03756b450809928f
BASELINE_REF: origin/feature/g24-g30-development-completion-routing
BASELINE_PURPOSE: Canonical Design / Read Baseline for Product Re-Foundation Gate 2
AUTHORITY: HD-1 APPROVED
```

Exact SHA 是設計依據；branch ref 日後移動不自動改變本基線。批准不授權 checkout、reset、rebase、merge、覆蓋 dirty working tree、刪除 local overlays、清除 untracked work，或整併 governance／Phase A branches。既有工作繼續保存、個別 reconciliation。

## 2. Product Persona

- Primary：AI-augmented Developer / Technical Lead。
- Secondary：QA / Independent Reviewer。
- 第一個 Working Product 不同時為 PM、一般文件使用者、主管 dashboard 或 generic enterprise workflow 設計產品核心。

## 3. First Vertical

一個小型、可重現的 software bug fix，加至少一次 Failure → Retry / Recovery。

```text
Open Repository
→ Create Task + Goal / Scope / Acceptance Criteria
→ Select Real Agent
→ Establish baseline / workspace ownership + Create PolyNexus Run
→ Launch Agent → Real repository modification → Monitor / Stop / Finish
→ Freeze immutable Candidate
→ Verification against exact Candidate（包含 mandatory deterministic tests）
→ Evidence Set / Verification Record → PASS / FAIL 或明確未滿足原因
→ Human Accept / Reject
→ History retained
```

Writer 可先自測；供正式 verification／acceptance 的證據必須可綁定 frozen Candidate。Freeze 包含 changed files、diff／content artifacts 的固定與 identity capture。

## 4. Product Boundaries

PolyNexus 不重新開發 LLM，也不以成為另一個 Coding Agent 為主要方向。Executor／Provider 可替換；PolyNexus 掌握 execution control、state、context、workspace facts、artifact identity、evidence、verification、acceptance、recovery 與 history。

Git 仍是 Code Truth；PolyNexus 不是 Git replacement。Provider session 是 external reference，不是 canonical Project／Task identity。接受變更不自動授權 commit、merge、push 或 release。

Track A 是 Sovereign Working Product；Track B 是 Goal／Product Brain／intelligent orchestration；Track C 是 future resilience／competitive adaptation。三者共用同一個核心；Track B 不阻塞 Track A。

## 5. Architecture Invariants

- KEEP 現行主要 stack；UI 不直接操作 DB、OS process、Git、Runtime CLI 或 vendor events。
- Core-owned RunSupervisor、Adapter-owned vendor logic；不以單一第三方 agent 平台作 Core 必要依賴。
- `Task != Run`；不將 `Run == Attempt` frozen，也不自行新增 Attempt entity。
- PolyNexus durable state 不採 provider 私有 session format 作 Domain。
- ContextPackage 是版本化 reference manifest，不是 prompt string；Artifact／Evidence 保留內容 identity 與來源。
- Implementation／Execution Complete ≠ Verification Complete ≠ Human Accepted。
- Secret values 不進普通 Domain、Evidence、Artifact、log、Git、export 或 handoff。
- Alembic 是 authoritative schema migration mechanism；不得以 create_all 宣稱 production migration。
- YAML／JSON Schema／Canonical Workflow Model 與 fixed V1 node vocabulary 保留；若需要新 node type，提出 ADR change。
- Product Brain 的 plan／routing 建議必須通過共同 deterministic boundary；不得直接修改 DB、操作 Git、啟動任意 process，或建立第二套 execution truth。
- Frozen ADR 不由本檔修改；Gate 2 可提出具體 change proposal，不能自行 freeze 或實作。

## 6. Candidate Semantics

Human 接受 immutable Candidate Change Set，不接受 Agent Session 或 writer 的完成宣稱。

Candidate 採固定內容的 manifest／Value Object identity boundary；可 durable publication／reference，不在此預先建立 DB table。它關聯 repository baseline、changed file set、diff／patch identity、content artifact hashes、需求／context revision 與 test target／validation contract。

Candidate identity **不得因新增 Evidence 自行改變**。Evidence Set 與 Verification Record 分別引用 exact Candidate；不能將持续成長的 evidence 造成循環 hash 依賴。

Verifier 若改寫 A，產生 B；B 必須重新進入 verification。對 A 的結果不可直接變成 B 的 certification。

## 7. Verification Semantics

最低獨立性：Verifier 不只採信 writer 文字，對固定 Candidate 執行／評估可信的驗證，且不偷偷改寫 Candidate。不同 AI Provider 不是 minimum independence 必要條件。

Local deterministic runner、CI、independent process、Reviewer Agent、Human 可依其實際能力提供驗證。獨立 process 或工具名稱本身不證明 oracle／provenance 可信；必須檢查候選綁定、必要驗證要求與結果收集。

EXECUTED、IMPLEMENTED、TESTED、REVIEWED、VERIFIED、ACCEPTED、RELEASE_READY 不是一個 Success，也不直接建立七個 DB enum。保存 execution、check、review、verification、Human decision 事實，導出適用的狀態／certification。IMPLEMENTED claim 不等於 bug fixed 已被證明。

## 8. Evidence Semantics

```text
Claim / Acceptance Criterion
→ Required Evidence
→ Actual Evidence
→ Verification
→ Scoped Certification State
```

KEEP 現有 Evidence／Finding／Artifact 基礎；補 candidate、criteria、provenance 與 applicability binding，必要時調整 gate evaluation。不預設重寫 Evidence Domain。

unit PASS、integration MISSING 可表示已執行部分 tests，不能表示 mandatory verification 已滿足。Hash 證明內容 identity，不單獨證明執行真實性或 producer authenticity。

External CI 可以提供 evidence，須證明 exact Candidate／實際被測 source 與可信 provenance；不要求 PolyNexus 親自執行所有 tests。Local／external evidence 都須保留 target、command／check、producer、環境、outcome、artifact 與適用版本的可查證關聯。

## 9. Human Acceptance Semantics

HD-3 clarification 具最高優先：

- Human Reject 可以在任何必要階段執行；不要求先通過 verification 才能拒絕。
- Human Accept **只有在當下 mandatory verification policy 對該 exact Candidate 已滿足，且 evidence／verification snapshot 未 stale 時，才能成立**。
- Human action 不得將 FAIL、MISSING、ERROR、SKIPPED、STALE、Candidate mismatch 轉成 VERIFIED。
- V1 不提供 Override Accept。
- Decision 必須綁 exact Candidate、evidence／verification snapshot、Human principal、timestamp、decision action 與 reason／optional note。
- 明確 Human action 不等於普通 Agent／Core token、actor string 或 AI approval。D11 現行 fail-closed 保留至正式批准的 boundary 演進完成。

## 10. Workspace / Ownership Strategy

第一個 pilot：**Local-personal / Single Human / Single Active Writer / Managed Git Worktree**。

原 Human dirty workspace 預設不得自動帶入或修改。若任務需要 dirty input，必須由 Human 明確選取並固定輸入 snapshot。

Managed Git Worktree 是 workspace isolation／ownership strategy，**不是 hostile-code security sandbox**。第一版不宣稱抵抗同 OS principal 的惡意 process，不宣稱 Enterprise IAM、small-team attribution 或 multi-user concurrent writers。更強 isolation 另作 architecture decision。

Workspace Integrity 採四個正交維度：

1. Identity。
2. Git Observation。
3. Ownership。
4. Recoverability。

不將 CLEAN／MODIFIED／CONFLICTED／RECOVERY_REQUIRED 等混合成巨大單一 enum。每個真實 Run 須能追溯 baseline、writer、ownership、workspace observations，服務 retry／resume／switch agent／manual takeover／recovery／acceptance。

## 11. Continuity Contract

正式承諾：**Task / Context / Work / Evidence Continuity**，不是 Provider-native Session Portability。

NATIVE／MANAGED／NONE 保留作 Provider Resume capability。Provider session 消失不導致 PolyNexus Task／history 消失。

ContextPackage 表達 Agent 現在應知道什麼；Continuation／Handoff manifest 表達如何安全接續。保存 versioned task requirements、baseline、workspace snapshot、completed／pending work、findings、context refs、artifacts、evidence、decisions 與 environment snapshot；引用固定版本，不複製另一套 truth。接收端須重新檢查 workspace／ownership／freshness。

## 12. Provider Independence Boundary

Provider Independence 保留為 architecture invariant，不因已有 adapter interface 就宣稱完成產品驗證。

先讓一個 real executor 跑通 Working Product；第二個不同 executor 再證明能沿用相同 Task、Run、Context、Candidate、Evidence、Acceptance 核心。不得 silent simulated/reference fallback。不要為第二 provider 過早建立最低共同能力平台。

## 13. Stability P0

| 必要問題 | 規劃要求 |
|---|---|
| CREATED Run restart blocker | 區分未啟動 intent 與曾啟動 execution；正常 create 後重啟不阻塞整個服務，未知執行不重複啟動 |
| UI／Core authentication mismatch | 補 paired client 的真實入口；不移除 Core fail-closed auth |
| SQLite integrity initialization bug | 修正 dialect／connection 初始化，確保 FK enforcement，檢查既有資料一致性 |

WAL 與 FK 分開：當前規劃結論為 WAL_NOT_REQUIRED_YET；不能因 `journal_mode=delete` 自動判為缺陷。後續根據 contention、backup／restore、recovery、deployment evidence 決定。

**Gate 2 planning 可在 P0 未修完時開始；正式 Working Product Vertical execution 必須依 dependency plan 先處理必要 Stability P0。**

## 14. Working Product P0

- 可理解的 SETUP／START／HEALTH／STOP／安全 RESET 與 START_HERE。
- Repository binding、versioned Goal／Scope／Acceptance Criteria。
- Workspace ownership、第一個 real executor、指定 repository 真實修改與 monitor／stop。
- Freeze Candidate、diff／content Artifact capture。
- Deterministic test execution、trusted Evidence provenance。
- 對 exact Candidate 的 independent verification。
- Human Accept／Reject 與歷史保存。
- Failure／Retry／Recovery，保全 Human work 與前次事實。

這些是第一個 Product Outcome 的必要條件，不能因不會 crash server 而降為次要。Workflow 最小真實語意優先映射既有 CONTEXT、AI_TASK、TOOL、EVIDENCE_CHECK、HUMAN_GATE；不藉此新增 language。

## 15. Benchmark Requirements

| Case | 驗證能力 |
|---|---|
| B01 Simple Python bug fix | 第一個真實閉環、fixed Candidate、mandatory tests、Human acceptance／history |
| B02 Multi-file refactor | 完整多檔 capture、scope、behavior regression |
| B03 Frontend + Backend API change | 跨層 context、contract 與 journey verification |
| B04 Failing test repair | 修復可信度；防止刪／弱化 tests 冒充成功 |
| B05 Agent／process crash recovery | Executor／Core crash、cleanup、ownership、避免 duplicate writer |
| B06 Agent A → Agent B handoff | Sequential continuity 與第二 executor 共用核心 |
| B07 Reviewer catches false implementation | Independent oracle、防止 false acceptance |
| B08 Provider unavailable | 誠實 readiness／failure、保留工作、不 silent fallback |
| B09 Incomplete／stale context | Freshness、missing refs、criteria／baseline 漂移處置 |
| B10 Dirty workspace recovery | Staged／unstaged／untracked／conflict 保全與安全接手 |

以 scenario 的真實 side effects、禁止發生的副作用、證據與成果為驗收依據，不只增加 unit／contract permutations。第二 executor 不阻塞第一 executor 閉環；具體測試排程由 Gate 2 dependency plan 定義。

## 16. Pilot Metrics

比較基準：**Direct Agent + Git + CI vs PolyNexus-managed workflow**。

採相同接受標準、相近任務難度、相同 executor／model／test／environment 條件，控制順序與學習效應；納入失敗／未完成任務，分列 setup、人力、provider／compute 成本。不能只量 PolyNexus Run count。

指標：Time to Accepted Change、Human Active Minutes、First-pass Acceptance、Recovery Success Rate、Evidence Completeness、False Acceptance／Escaped Defects、Workspace Integrity Incidents、Cost per Accepted Task、Voluntary Repeat Usage。

如果直接組同樣可靠且更簡單，保留 Pivot／No-Go。Gate 1.5 提出的樣本數、百分比與時間門檻只是 pilot 校準建議，**不是本檔已批准的數值承諾**。

## 17. Explicit Non-goals

第一個 vertical 不擴張到多 Agent Council、release management、documentation workflow、generic BPM 或 Product Brain。首輪不追求大量 Agent、parallel coding writers、distributed scheduler、multi-tenant、Enterprise IAM、small-team attribution、native session portability 或 hostile-code sandbox 保證。

不將 simulated adapter／demo path 成功當 real product 成功；不以測試名稱推論 runtime side effects。

本次只授權 **Gate 2 Target Product + Target Architecture Planning**。不授權大規模 implementation、修改 frozen ADR、建立 release baseline，或任何 HD-1 禁止的 Git／working-tree 操作。
