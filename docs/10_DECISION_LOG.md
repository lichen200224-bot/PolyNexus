# PolyNexus Decision Log

## G30 / WP-20 final governance acceptance (2026-09-12)

DECISION: `WP20_FINAL_ACCEPTANCE_GRANTED`

- `WP20=FINAL_ACCEPTED`; `WP20_SCORE=5/5`.
- `G30=FINAL_ACCEPTED / CLOSED`; `G30_SCORE_DELTA=0`.
- `V1_BOUNDED_DEVELOPMENT_ACCEPTANCE_SCORE=100/100` applies only to the
  existing G24-G30 development denominator.
- `OVERALL_PROJECT_COMPLETION=NOT_DEFINED`; production readiness, completion
  of the Plugin Platform, MCF-02, and external-runtime expansion are not
  claimed.
- Live Level 3A results are `CHATGPT=PASS`, `CLAUDE=PASS`, and `GEMINI=PASS`;
  Human confirmation boundary, 21/21 failure rows, egress review, and
  sanitization passed.
- Claude's truthful result is retained as
  `CLAUDE_RESPONSE_FORMAT_MATCH=NO`, `CLAUDE_CAPTURE=PASS`, and
  `CLAUDE_NORMALIZATION=PASS`; it is not rewritten to `CHECKED`.
- Independent review returned `INDEPENDENT_G30_WP20_REVIEW_PASS`, recommended
  `ACCEPT`, `5/5`, and `READY`; final Human governance acceptance is
  `GRANTED`.
- Historical rejected attempt `chatgpt/invalid-attempt-01` / matrix row
  `CG-01` remains `REJECTED` with `HISTORICAL_UNAUTHORIZED_SENDS=1`, cause
  `HUMAN_MIS_OPERATION`, and `PRODUCT_AUTO_SEND=NO`. Separately,
  `ACCEPTED_ATTEMPT_UNAUTHORIZED_SENDS=0`.
- `BASELINE-DEBT-01=FINAL_ACCEPTED / CLOSED`; `MCF01=CHECKPOINTED`.
- Promotion to `feature/mcf-01-static-module-contract` is not executed by this
  decision and remains a separate governance action.

## BASELINE-DEBT-01 final acceptance (2026-09-12)

DECISION: `BASELINE-DEBT-01 FINAL ACCEPTANCE`

- `ACCEPTED_SHA=aac597579ee6d369007343930d3a5b3ca7b929c5`.
- `REJECTED_SHA=180432d03f6d423bb3152c233fb4f0a5072868f5`.
- Rejected reason: publication integrity used CRLF working-tree hashes instead
  of canonical Git blob hashes.
- Repair: one publication-only successor commit; executable, test, migration,
  ADR-014 and functional-contract trees are exactly unchanged.
- `FRESH_REACCEPTANCE=PASS`; `FUNCTIONAL_RETEST_AFTER_REPAIR=NOT_REQUIRED`
  because the executable/test/migration/functional-contract trees are exactly
  equivalent.
- `FINAL_ACCEPTANCE=GRANTED`; the accepted functional anchor is frozen.
- `MERGE_AUTHORIZATION=NOT_GRANTED`; `PROMOTION_AUTHORIZATION=NOT_GRANTED`.
- BASELINE-DEBT-01 does not change the G24–G30 bounded development score,
  `WP20`, `G30`, overall completion, Plugin Platform or external-runtime status.


## Historical ADR-014 implementation authorization (2026-09-12; superseded by final acceptance above)

Status: HUMAN_ACCEPTED / IMPLEMENTATION_AUTHORIZED. See
[ADR-014](35_ADR_014_DURABLE_EVENT_ORDERING_AND_CANCELLATION_CLEANUP.md).
BASELINE-DEBT-01 may add persistence-only event_sequence, atomic per-Run allocation,
0003 rowid legacy backfill/downgrade, separate cleanup deadlines and durable external
cancellation handling. Domain/API/RunState/runtime binding contracts are unchanged.
This supersedes the earlier BASELINE-DEBT-01 architecture proposal only; G30,
WP-20 and score remain unchanged. At this historical gate, independent code
review was still required.


## Current Human routing override — external verification moved to G30 (2026-09-03)

The Human changed the current Goal routing: authenticated external ChatGPT /
Claude / Gemini Web verification is deferred from G29 to G30. G29 retains only
the isolated-lane preflight, sanitized operator pack, and truthful handoff of
unverified WP-20 evidence. G30 must not be started by this update; its future
start gate must include the deferred external verification before final
reconciliation. This is a governance/routing change only:
`ADR_IMPACT=NONE`, `SCOPE_DEVIATION=NONE`; D02, ADR-006, ADR-010, the explicit
Human-confirmed-send boundary, secret boundary, and no-automatic-send rule are
unchanged.

Status: Development Baseline v1.0

## Product / Scope Decisions

### D01 — Work Modes — CONFIRMED
Phase 1 top-level：Discuss / Review / Validate。Develop 是 workflow action，不是第四入口。

### D02 — Web AI — CONFIRMED
ChatGPT / Claude / Gemini Web 採 Level 3A Assisted Automation：Launch / Fill / User-confirmed Send / Capture / Normalize + mandatory manual fallback。Web output = AI_OPINION。

### D03 — Compatibility — CONFIRMED
Broad Compatibility + different depths。只有通過完整 Core Contract 才可 SUPPORTED/CERTIFIED。Integration type 與 maturity 分離。

### D04 — Local AI — CONFIRMED
Local AI 是 first-class AI resource。LM Studio / Ollama / Generic OpenAI-compatible baseline。可 Discuss/Review/Council/Document/Validation Analyst，但不取代 deterministic validator。

### D05 — Data Routing — CONFIRMED
PUBLIC / INTERNAL / CONFIDENTIAL / RESTRICTED + trust profiles + ALLOW/APPROVAL_REQUIRED/DENY。No automatic downgrade / no silent sensitive cloud fallback。

### D06 — Governance — CONFIRMED
Flexible Governance + Assurance：FLEXIBLE / STANDARD / VERIFIED；UNREVIEWED / SELF_REVIEWED / CROSS_REVIEWED / VERIFIED。平台底線不可偽造 Evidence/Provenance。

### D07 — Plugin Architecture — CONFIRMED
Plugin-ready now, Plugin Platform later。V1 built-in/static extensions 使用 versioned contract、manifest、registry、lifecycle、capability、failure isolation、conformance。

### D08 — Workflow — CONFIRMED
Minimal Declarative Workflow Foundation + 9 built-in templates；不做 visual designer / arbitrary script nodes / generic BPM。

### D09 — Competition Golden Path — CONFIRMED
Engineering Review & Validation 為主（70–80%），Executive/Web AI Decision Review 為延伸（20–30%）。

### D10 — Long-term Product — CONFIRMED
Phase 1 必須是可用的 LOCAL_PERSONAL Product，且以同一 Domain/Contract 向 Personal Hub、部門／Team、Enterprise 演進；原始功能範圍保留，以成熟度分級控制深度。

### D11 — WP-13 Human Gate Attribution — CONFIRMED (2026-08-21)
WP-13 暫採 Option C：現有 `Evidence.actor_id` 與 authenticated loopback token
不足以證明 Human principal。無法透過已批准 identity boundary 驗證的
`HUMAN_EVIDENCE` 必須維持 `HUMAN_DECISION` / `NEED_ACTION`，不得產生
`PASS` / `VERIFIED`。不得使用 `human:` prefix、deny-list 或任意 actor string
偽造 Human attribution。若未來需要可驗證的 Human approval，另行提出
authenticated principal mapping（Option A）或 attestation/provenance contract
（Option B）的 architecture decision；本決策不新增 model、migration、endpoint
或 authentication subsystem。

### Pre-WP14 Runtime Foundation Direction — ADR-011 HUMAN ACCEPTED (2026-08-25)

- Governance checkpoint 明確納入本檔與既有 D11；D11 Option C 持續 fail closed，不能由 automation-ready、任意 actor string 或 AI approval 取代 authenticated trusted-human decision。
- 完整 ADR-011 已在獨立文件 review `VERIFIED_PASS` 後由 Human 明確批准為 `HUMAN_ACCEPTED / NOT_IMPLEMENTED`；正式決策見 `docs/29_ADR_011_RUNTIME_BINDING_AND_TRANSPORT.md`，Foundation Gate 見 `docs/30_RUNTIME_CONTRACT_FOUNDATION_GATE.md`。Architecture acceptance 僅接受 contract／migration 方向，不授權產品實作、migration、stage、commit 或 push。
- Pre-WP14-A 驗證 ADR-007 的 timeout、cancel 與 cleanup 契約；Pre-WP14-B 規劃 Run-owned immutable `RuntimeBindingSnapshot`、既有 Run identity、future Alembic `0002` migration、legacy backfill、rollback/restore 與 deterministic coverage。
- `Task != Run`，不得 frozen `Run == Attempt`；不得引入 Attempt、RoutingEnvelope、Packet Domain、Memory Domain、Provider Gateway、vendor-specific Core branch 或 trusted-human authentication subsystem。
- Governance checkpoint `358d263` 已由 Human 批准完成；依後續 Human 授權 curated import docs-only ADR 文件，不得 merge、rebase、checkout 或覆寫互相重疊的 dirty worktrees。
- 後續產品實作角色固定為 OpenCode Writer、fresh independent Codex Reviewer、Human Architecture / Acceptance / Git Gate；`Writer != Reviewer`。
- 本決策只授權 ADR-011 架構接受狀態同步與環境／實作規劃，不授權 stage、commit、push、remote operation、worktree mutation、source/schema/migration 修改或 dependency 安裝；PRE-WP14-A/B 各自需要新的 Human implementation Gate。

### Cross-cutting — CONFIRMED
V1 補足最小必要：Compatibility/Migration、Evaluation/Quality、Cost/Resource Control、Context Lifecycle、Artifact Lifecycle、UX Complexity Control。

### Cross-cutting — Development progress and G24–G30 execution — HUMAN CONFIRMED (2026-09-02)

- 正式專案開發進度採 development-only 100-point ledger；競賽文件、報名與人工交付改列 `NOTE_ONLY_NON_SCORING`，不進入開發分母或扣分。
- G23 接受後的正式分數是 `59/100`。權重固定為 CP-00 `8`、CP-02 `22`、CP-03 `27`、CP-04 `20`、CP-05 `13`、CP-06 `10`；細分 WP 權重與狀態以 `docs/33_DEVELOPMENT_PROGRESS_AND_GOAL_EXECUTION_STANDARD.md` 為準。
- 後續順序固定為 `G24 → G25 → G26 → G27 → G28 → G29 → G30`。外部／真人操作比例最高的 authenticated vendor 驗證延後到 G29；在此之前不得宣稱 live-vendor support 或 certification。
- 每個 Goal 由新的 Codex task 執行，目標模型為 `gpt-5.6-luna`、reasoning effort `high`。模型或推理層級不符時必須在寫入前停止並回報，禁止靜默替換。
- Human 授權 Codex 在單一 Goal 已核准 scope 內自行選擇實作細節、執行測試、修正 findings、重新 review，以及持續處理至最終驗收 Gate。此授權不擴張 Product Scope、ADR、外部送出、秘密資料處理或 Git 權限。
- 每個 Goal 的 Human 介入點原則上只有最後的 `ACCEPT_AND_COMMIT_PUSH`。該語句只授權當輪已揭露的 exact allowlist、branch、commit message 與 approved remote ref；不授權 force push、remote reconfiguration、額外檔案、下一 Goal 或外部傳送。
- Planning package 必須先獨立 checkpoint 並記錄 immutable `G24_START_SHA`；該 SHA 未建立以前 G24 維持 `WAIT`。
- 本決策是治理、進度與 routing 更新，`ADR_IMPACT=NONE`、`SCOPE_DEVIATION=NONE`，不修改 ADR-001～011 或 Core contract。

### D12 — WP-16 Runtime Doctor Reporting — HUMAN ACCEPTED / IMPLEMENTATION AUTHORIZED (2026-08-27)

#### G25 integration addendum — 2026-09-02

The G25 combined lane adds only a bounded private Registry observation factory
and `doctor_legacy.py` compatibility surface. Normal `create_adapter()` keeps
its execution-time capability/auth validation; Doctor uses the observation path
to distinguish declaration/probe failures from factory failures. No public
runtime contract, Run identity, persistence schema, migration authority,
vendor-specific Core branch, or production-support claim changes. The addendum
is subject to the current G25 independent-review and final Human gate.

#### G25 final Git gate authorization — ACCEPT_AND_COMMIT_PUSH (2026-09-02)

Human explicitly authorized `G25_DECISION=ACCEPT_AND_COMMIT_PUSH` for the exact
G25 allowlist, proposed commit message, and approved remote ref recorded in
`docs/12_HANDOFF_CURRENT.md`. Independent Carver review is `PASS` with
`BLOCKER=0`, `MAJOR=0`, `MINOR=0`; baseline and governance validators passed
with exit `0`. The `+13` remains conditional until the exact commit is pushed,
the remote SHA is verified, and the fresh clean-clone verification succeeds.
No force push, remote reconfiguration, extra path, secret handling, external
send, or G26 start is authorized.

- WP-16 v1 採 Core-only、deterministic、read-only Doctor MVP；不新增 API、UI、DB、migration、network、credentials、real vendor CLI 或 persistence。
- Doctor 使用專用 composition root 與 immutable ordered inventory，建立 fresh `RuntimeRegistry`；不修改 `build_default_registry()`、`RuntimeAdapter` method set、`ExecutionService`、supervisor、domain 或 persistence，也不新增 general Registry enumeration contract。
- `reference.local` 僅在 `DETERMINISTIC_REFERENCE_RUNTIME` 範圍標示 `SUPPORTED`；Codex/OpenCode 僅標示 `EXPERIMENTAL` 與 `DETERMINISTIC_LOCAL_CONFORMANCE`，不得宣稱 production、`SUPPORTED`、`CERTIFIED` 或實際 vendor detection。
- health/readiness 是 `CURRENT_PROBE`；capabilities/version 是 adapter declaration；conformance evidence 另列 outcome、scope、checkpoint 與 test source。Codex/OpenCode 無獨立 runtime version 時回報 `None` / `UNAVAILABLE`，不得把 adapter version 冒充 runtime version。
- factory、probe、timeout、invalid inventory 均 fail closed；報告只保留固定 error category，不保留 raw exception、message、args、cause、context 或 traceback。factory failure 形成 partial row 並繼續其他 rows；inventory invalid 回報 `FAILED` 且 entries 為空。
- Architecture record 與 implementation exact allowlist 見 `docs/31_ADR_012_RUNTIME_DOCTOR_REPORTING.md` 與 `docs/tasks/WP-16.md`。本決策只授權本輪 implementation；fresh independent Codex review、Human acceptance、stage、commit、named-ref push 與後續 WP-16 work 仍是分離 gates。

### D13 — Modular Core Extension Architecture — HUMAN DIRECTION ACCEPTED (2026-09-11)

- D07 `Plugin-ready now, Plugin Platform later` remains authoritative. This decision formalizes it into a concrete modular Core direction; it is not a product reset.
- PolyNexus must retain a usable native Core baseline while allowing execution engines, tools, surfaces and integrations to be replaceable modules behind versioned contracts.
- `Module` is the packaging/registration/configuration/lifecycle unit; `Adapter` is the normalized programmatic contract. A module may expose one or more adapters.
- V1 remains static/built-in registration only. Dynamic loading, marketplace, remote install/update, signing, hot reload and dependency resolution remain future work.
- Reserved module classes are `RUNTIME`, `TOOL`, `SURFACE`, and `INTEGRATION`; `MEMORY` remains future-only and does not authorize a new V1 Memory Domain or persistence subsystem.
- Runtime modules must reuse ADR-011: Module Registry -> RuntimeProfile/RuntimeRegistry -> RuntimeBindingSnapshot -> RuntimeAdapter -> RunSupervisor. They must not introduce a parallel execution path or bypass immutable Run binding history.
- Complete external agent runtimes/workspaces such as holaOS-like or OpenHands-like systems may be future compatibility targets only through documented/supported integration surfaces and PolyNexus governance. This is not a current support/certification claim.
- PolyNexus Core retains Project/Task/Run, Workflow, lifecycle, ContextPackage, Artifact/Evidence/Finding/RunResult, Event Ledger, policy, SecretRef and validation truthfulness authority.
- Formal architecture record: `docs/34_ADR_013_MODULAR_CORE_EXTENSION_ARCHITECTURE.md`.
- First bounded implementation work item: `docs/tasks/ARCH-MODULAR-CORE-01.md` (`MCF-01`).
- This is a parallel architecture track. G30 remains `NEED_ACTION`, WP-20 remains unchanged, and no development score is awarded by this docs-only decision.
- ADR-013 is `HUMAN_DIRECTION_ACCEPTED / PENDING_INDEPENDENT_DOC_REVIEW`; implementation candidate must use an isolated branch/worktree, then fresh independent Codex review and a separate Human Git promotion gate.

## Architecture Decisions

ADR-001～010 全部 CONFIRMED；詳見 `18_ARCHITECTURE_DECISIONS.md`。

- ADR-001 Browser-first local web; desktop-wrapper-ready.
- ADR-002 Python/FastAPI/asyncio + SQLAlchemy/Alembic/SQLite.
- ADR-003 React/TypeScript/Vite.
- ADR-004 REST + WebSocket + Durable Event Ledger.
- ADR-005 pytest + Vitest + Playwright + Antigravity real-browser validation.
- ADR-006 Chrome MV3 Thin Companion + authenticated localhost API.
- ADR-007 Core-owned Run Supervisor + normalized lifecycle/cancel/cleanup.
- ADR-008 SQLite metadata + filesystem artifacts + hash + versioned ContextPackage.
- ADR-009 YAML workflow + schema validation + canonical model + fixed nodes.
- ADR-010 SecretRef + OS-backed SecretStore + least privilege/redaction.
- ADR-011 Runtime Binding & Transport — `HUMAN_ACCEPTED`; vendor-neutral RuntimeProfile/Registry/Binding contract.
- ADR-012 Runtime Doctor Reporting — `HUMAN_ACCEPTED / IMPLEMENTATION_AUTHORIZED`; truthful capability/version/maturity reporting.
- ADR-013 Modular Core Extension Architecture — `HUMAN_DIRECTION_ACCEPTED / PENDING_INDEPENDENT_DOC_REVIEW`; static module contract foundation and future external-runtime compatibility.
