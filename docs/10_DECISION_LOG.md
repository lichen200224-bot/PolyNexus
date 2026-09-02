# PolyNexus Decision Log

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
