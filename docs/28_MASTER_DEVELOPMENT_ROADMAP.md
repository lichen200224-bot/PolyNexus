# PolyNexus Master Development Roadmap & Checkpoint Register

## G28 checkpoint — HUMAN_ACCEPTED / PASS / COMPLETE (2026-09-03)

- Branch: `feature/g28-ux-feature-freeze`.
- Exact predecessor/start SHA: `56c941a6077802e326284f1b70fd9719f146e5b4`.
- G27 product output: `27ff09c224344821868dd8fd36ec2c0eb11504df`; approved
  terminal output/state-sync tip: `56c941a...`.
- Score: `95/100` (`90/100` plus the accepted bounded `+5`).
- Scope: WP-26 UX/accessibility/states; WP-27 Golden Workflow regressions and
  feature-freeze evidence. Independent review PASS with zero findings.
- `G28_DECISION=ACCEPT_AND_COMMIT_PUSH`; `G28_PRODUCT_OUTPUT_SHA=789717fbf4a6b4a36aa71ec1cf7d36f344eccdf7`
  the first checkpoint commit and `G28_OUTPUT_SHA` the later state-sync.
- `NEXT_GOAL_READY=G29`; G29 is not started in this task.

## Current G27 candidate checkpoint — 2026-09-03

- `G27_STATUS=HUMAN_ACCEPTED / PASS / COMPLETE`; isolated branch
  `feature/g27-workflow-guards-metrics` starts at exact predecessor
  `7a7dee67395c8a07f2e5b055a306e63190bbd1f8` from the approved backup remote.
- G26 is `HUMAN_ACCEPTED / PASS / COMPLETE` at `84/100`. G27 accepted
  `WP-22=3`, `WP-24=2`, `WP-25=1`, for `+6` and `90/100`.
- `G27_PRODUCT_OUTPUT_SHA=27ff09c224344821868dd8fd36ec2c0eb11504df`; the
  later docs-only acceptance-provenance checkpoint
  `G27_OUTPUT_SHA=56c941a6077802e326284f1b70fd9719f146e5b4` is the approved
  remote tip and exact G28 predecessor. Both refs are retained for provenance.
- Current deterministic evidence and independent review are recorded in
  `artifacts/verification/g27-workflow-guards-metrics-20260903/`; one
  pre-existing Windows symlink-policy skip is explicit. `ADR_IMPACT=NONE`,
  `SCOPE_DEVIATION=NONE`, primary worktree unchanged, and
  `NEXT_GOAL_READY=G28` is set; G28 is active in its isolated lane.

## Document status

- **Status**: CONFIRMED — Human roadmap confirmation recorded on 2026-08-19
- **Version**: 1.0
- **Baseline date**: 2026-08-19
- **Branch**: `feature/first-vertical-slice`
- **Feature Freeze target**: 2026-10-18
- **V1 Acceptance Complete target**: 2026-10-31
- **Primary source documents**: `docs/00_SCOPE_BASELINE.md`, `docs/04_DEVELOPMENT_PLAN.md`, `docs/10_DECISION_LOG.md`, `docs/18_ARCHITECTURE_DECISIONS.md`

## G26 candidate checkpoint — 2026-09-03

- `G26_STATUS=HUMAN_ACCEPTED / PASS / COMPLETE`; isolated branch `codex/g26-local-policy-acceptance`
  starts from exact G25 state-sync SHA
  `04d37291d45ebbda8453f1b39e30fca523ee1548`.
- Candidate scope is WP-17/18/19 only. Browser companion deterministic tests
  passed 10/10 and Web Vitest passed 80/80 with production build exit `0`;
  targeted Core G26 tests passed 14/14; full Core regression exited `1` only in
  unrelated persistence/lifecycle/council/resource-guard tests.
- Accepted score is `84/100` (`G26_SCORE_DELTA=+12/12`) for bounded internal
  G26 evidence. Live authenticated vendor verification remains G29.
- `ADR_IMPACT=NONE`; `SCOPE_DEVIATION=NONE`; primary checkout remains protected.

This document is the project-level monitoring baseline. It defines sequence, scope, estimated duration, owners, evidence, checkpoints, and progress reporting. A task is not accepted because it is implemented; it becomes progress only after deterministic evidence, independent review, and the required Human decision are recorded.

## 1. Operating rules

- One active Writer per branch. OpenCode is the normal implementation Writer; Codex is the independent Reviewer for architecture, Core, contracts, and acceptance; Antigravity is used for real Browser/E2E and milestone verification.
- Every task follows: plan → task document → implementation → tests → Writer handoff → Codex review → Human acceptance where required → governance update → checkpoint.
- No source implementation starts when the task scope, acceptance tests, protected areas, and handoff fields are not documented.
- ADR-001–010 are frozen. Any contract, lifecycle, evidence, policy, persistence, or scope change requires an architecture proposal and explicit Human approval before implementation.
- Browser E2E previously accepted under waiver remains `UNVERIFIED/SKIPPED`. It must not be relabeled `PASS` until a browser-capable rerun is completed.
- Estimates are calendar-day forecasts for one active Writer and include focused tests, one review cycle, and normal handoff work. They are not guarantees.

## 2. Scope boundary

### Included in the current V1 plan

- CORE: Project/Task/Run/History, Discuss/Review/Validate, ContextPackage, Workflow, Run Supervisor, Finding/Evidence/Decision, Artifact metadata, Event Ledger, Codex/OpenCode runtime contracts, Doctor/Conformance, migration and backup foundations.
- BASELINE: local AI profiles, data classification/routing, assurance/governance, timeout/concurrency guard, minimal evaluation/usage metrics, Context and Artifact lifecycle, progressive disclosure UX.
- COMPATIBILITY: real detection or integration evidence for additional runtimes, marked `SUPPORTED`, `PREVIEW`, or `EXPERIMENTAL` according to actual maturity.
- Competition note track: proposal/deck truthfulness, actual upload-form checks,
  and required demo materials are Human-owned delivery notes and are explicitly
  excluded from required development progress.

### Explicitly excluded from this roadmap

- Dynamic plugin marketplace, remote install/signing/auto-update, visual workflow designer, multi-device sync, multi-user/Enterprise IAM, distributed scheduler, full RAG/knowledge graph, and fully autonomous agent teams.
- Vendor-specific branches in Core, silent cloud fallback for sensitive data, fabricated AI/Evidence/Artifact records, and secret values in Domain, Evidence, logs, Git, handoff, export, or telemetry.

## 3. Progress model

The project uses a 100-point checkpoint-weighted progress model. Only `ACCEPTED` or `CHECKPOINTED` work earns project progress. `IMPLEMENTING`, `READY_FOR_CODEX_REVIEW`, `NEED_ACTION`, and `UNVERIFIED` are reported as status but earn zero points until the acceptance condition is met.

### G24–G30 Human-confirmed development completion program — 2026-09-02

- G23 remains accepted at exact SHA
  `0eb56a986e97a45854bd6ddd419c114845ce51f4`; the accepted total before G25
  was **59/100**, now raised to **72/100** by the verified G25 checkpoint.
- The current denominator contains development work only. Competition is
  `NOTE_ONLY_NON_SCORING`, Human-owned, and cannot add, subtract, or block
  development points.
- Current weights are CP-00 `8`, CP-02 `22`, CP-03 `27`, CP-04 `20`, CP-05
  `13`, and CP-06 `10`; detailed WP weights are in
  `docs/33_DEVELOPMENT_PROGRESS_AND_GOAL_EXECUTION_STANDARD.md`.
- Goal order is `G24 → G25 → G26 → G27 → G28 → G29 → G30`. G29 intentionally
  holds authenticated external-vendor validation until after deterministic and
  internal product work. Every Goal uses a new Codex task with
  `gpt-5.6-luna`, reasoning effort `high`.
- The approved G24 checkpoint is verified at exact
  `G24_OUTPUT_SHA=61cc7420e290cd93eda787c30b54a93edf4ca9a` on the approved
  remote ref `feature/g24-g30-development-completion-routing`. G24 is
  `HUMAN_ACCEPTED / PASS / COMPLETE` and the project score is `59/100`.
- The current per-WP evidence ledger is
  `artifacts/verification/g24-development-ledger-20260902/ledger.json`.
  Existing implementation/test presence for later WPs is recorded as
  `IMPLEMENTED_PENDING_REVIEW` and earns zero until WP-level review, Human
  acceptance, and checkpoint evidence exist.

#### Current development-only allocation and remaining routing

| Checkpoint / WP | Weight | Earned | Goal / state |
|---|---:|---:|---|
| CP-00 baseline/governance | 8 | 8 | Accepted |
| CP-02 First Vertical Slice | 22 | 22 | Accepted |
| WP-11 work modes | 4 | 4 | Accepted |
| WP-12 Council | 5 | 5 | Accepted |
| WP-13 workflow gates | 5 | 5 | Accepted with disclosed limitation |
| WP-14 Codex Runtime adapter | 5 | 5 | G25 — HUMAN_ACCEPTED / CHECKPOINTED |
| WP-15 OpenCode Runtime adapter | 5 | 5 | G25 — HUMAN_ACCEPTED / CHECKPOINTED |
| WP-16 Doctor/conformance | 3 | 3 | G25 — HUMAN_ACCEPTED / CHECKPOINTED |
| WP-17 local endpoint profiles | 4 | 4 | G26 — HUMAN_ACCEPTED / PASS / CHECKPOINTED |
| WP-18 classification/routing | 4 | 4 | G26 — HUMAN_ACCEPTED / PASS / CHECKPOINTED |
| WP-19 WebSurface/MV3 boundary | 4 | 4 | G26 — HUMAN_ACCEPTED / PASS / CHECKPOINTED |
| WP-20 authenticated Level 3A vendor flow | 5 | 0 | G29 — IMPLEMENTED_PENDING_REVIEW; external/Human-operated |
| WP-21 bounded browser fixture | 3 | 3 | Accepted through G21–G23 |
| WP-22 workflow templates | 3 | 3 | G27 — HUMAN_ACCEPTED / PASS / CHECKPOINTED |
| WP-23 backup/restore/migration | 2 | 2 | Accepted through G17/G22/G23 |
| WP-24 resource guards | 2 | 2 | G27 — HUMAN_ACCEPTED / PASS / CHECKPOINTED |
| WP-25 evaluation/usage metrics | 1 | 1 | G27 — HUMAN_ACCEPTED / PASS / CHECKPOINTED |
| WP-26 UX progressive disclosure | 2 | 2 | G28 — HUMAN_ACCEPTED / PASS / COMPLETE |
| WP-27 Golden Workflow regression | 3 | 3 | G28 — HUMAN_ACCEPTED / PASS / COMPLETE |
| CP-06 bounded RC hardening/closeout | 10 | 10 | Accepted through G19/G20/G22/G23 |
| **Development total** | **100** | **90** | **10 points remain** |
| Competition | **—** | **—** | `NOTE_ONLY_NON_SCORING` |

#### Ordered Goal forecast

| Goal | Scope | Score delta | Project score after acceptance | Start condition |
|---|---|---:|---:|---|
| G24 | Ledger/evidence reconciliation | 0 | 59 | Planning remote SHA and clean clone |
| G25 | WP-14/15/16 runtime adapters and Doctor | +13 | 72 | Approved G24 checkpoint |
| G26 | WP-17/18/19 local/policy/WebSurface internal work | +12 | 84 | Approved G25 checkpoint |
| G27 | WP-22/24/25 workflows, guards, metrics | +6 | 90 | Approved G26 checkpoint |
| G28 | WP-26/27 UX and Golden Workflow feature-freeze evidence | +5 | 95 | Approved G27 checkpoint |
| G29 | WP-20 authenticated vendor external verification | +5 | 100 | Approved G28 checkpoint + Human-operated environment |
| G30 | Final 100-point reconciliation | 0 | 100 confirmed | Approved G29 checkpoint |

### G25 candidate acceptance state — 2026-09-02

- Candidate lane was based on the exact accepted G24 SHA above. WP-14, WP-15,
  and WP-16 have deterministic local evidence; Carver's distinct bounded
  read-only review returned `PASS` with `BLOCKER=0`, `MAJOR=0`, `MINOR=0`.
  Human authorization `G25_DECISION=ACCEPT_AND_COMMIT_PUSH` is recorded and the
  checkpoint is verified at `f4168c31592ac5c886b49d8878f60b99016fdcaf`.
- Current candidate evidence is WP-14 `31 passed`, WP-15 `36 passed`, WP-16
  `58 passed`, G18 compatibility `7 passed`, packaging `3 passed`, Full Core
  exit `0` with one Windows-policy symlink skip, and baseline exit `0`.
- Governance validation passed with the system Windows PowerShell validator,
  exit `0`; the earlier bundled PowerShell Core module failure remains an
  environment-only historical result. The accepted project score is now
  `72/100` after exact remote and clean-clone checkpoint verification.
- The bounded G25 integration adds a private Registry observation factory and
  a legacy Doctor compatibility module; ADR-012 has an explicit integration
  addendum, while ADR-011, public runtime contracts, persistence/migrations,
  and Run identity remain unchanged.

`NEXT_GOAL_READY=G26`. All sections below this line are `HISTORICAL` predecessor
snapshots and do not override the current G25 section above.

### Historical G23 final acceptance snapshot — 2026-09-02

- The Human explicitly recorded `G23_DECISION=ACCEPT` for the final G19–G22
  reconciliation packet.
- Accepted exact SHA:
  `0eb56a986e97a45854bd6ddd419c114845ce51f4` on
  `origin/feature/g22-rc-hardening-cross-machine-delivery-closeout`; acceptance
  clean clone matched this SHA and was Git clean with staged state empty.
- G19, G20, G21, and G22 are terminal `PASS`; G22 is `CHECKPOINTED`; G23 is
  `HUMAN_ACCEPTED / PASS / COMPLETE` for repository-backed terminal evidence,
  bounded RC hardening, the delivery package, and cross-machine continuation.
- Human-directed reconciliation recognized **59/100** accepted progress. The
  later development-only model keeps the same total while removing Competition
  from the denominator and expanding CP-03/04/05 weights.
- Fresh CDP remains `NEED_ACTION`; native MV3 and authenticated vendor journeys
  remain `UNVERIFIED`; vendor certification remains `NOT_CLAIMED`.
- No next goal is automatically started. A new routing decision is required.

#### Accepted-score allocation after G23

| Checkpoint contribution | Allocation | Earned | Acceptance basis |
|---|---:|---:|---|
| CP-00 baseline/governance | 8 | 8 | Existing accepted checkpoint |
| CP-02 First Vertical Slice | 22 | 22 | Existing accepted checkpoint |
| CP-03 WP-11 work modes | 4 | 4 | Human accepted with deterministic evidence |
| CP-03 WP-12 Council | 5 | 5 | Human accepted with deterministic evidence |
| CP-03 WP-13 workflow gates | 5 | 5 | Human accepted with disclosed integrity limitation |
| CP-03 WP-14 / WP-15 / WP-16 remainder | 13 | 0 | G25 component acceptance/promotion |
| CP-04 WP-21 bounded browser E2E | 3 | 3 | G21 PASS, G22 remediation, G23 Human acceptance |
| CP-04 WP-17–WP-20 remainder | 17 | 0 | G26 internal work and G29 external vendor work |
| CP-05 WP-23 backup/restore/migration | 2 | 2 | G17/G22 deterministic evidence accepted by G23 |
| CP-05 WP-22 / WP-24–WP-27 remainder | 11 | 0 | G27/G28 feature-freeze work |
| CP-06 bounded RC hardening and closeout | 10 | 10 | G19 provenance/clean continuation, G20 reproducible Web, G22 WP-28–WP-31 hardening/delivery, and G23 final Human acceptance |
| **Total** | **100** | **59** | **59/100 accepted progress** |

Allocation rules:

1. Goal completion contributes through its mapped checkpoint and is not counted
   again as a separate bonus. G19 and G22 therefore earn recognized value inside
   CP-06 rather than remaining invisible or being double-counted.
2. Partial checkpoint points require a separately identifiable roadmap item,
   deterministic evidence, and the required acceptance decision.
3. G21 earns only the bounded WP-21 allocation; live vendor/login/send and native
   MV3 remain unverified and earn no additional CP-04 points.
4. CP-06 is accepted as a **bounded RC checkpoint**, not as certification that
   every CP-03–CP-05 feature is complete. The remaining 41 points make those
   incomplete product areas visible.
5. Competition is outside the development denominator and is retained only as
   a Human-owned note/delivery track.

| Work state | Earned progress | Meaning |
|---|---:|---|
| PLANNED / QUEUED | 0% | Scope exists, no implementation evidence |
| IMPLEMENTING | 0% | Writer is active; not accepted |
| READY_FOR_CODEX_REVIEW | 0% | Writer claims completion; independent review pending |
| NEED_ACTION | 0% | Findings or missing evidence remain |
| ACCEPTED / CHECKPOINTED | 100% of item weight | Evidence and required approvals complete |
| HUMAN WAIVER | Item-specific | Only the waived limitation is recorded; no hidden certification |

### Current baseline snapshot — 2026-08-25

### G21 current checkpoint snapshot — 2026-09-02

- G21 WP-21 has a bounded `PASS` from a fresh Chrome/CDP synthetic-host
  fixture: 3/3 golden journeys and 28/28 failure paths passed, with screenshots,
  CDP trace, and cleanup evidence. A narrow loopback URL traversal validation
  fix and regression test were included.
- Live vendor login/DOM/send compatibility remains `DEFERRED / UNVERIFIED`; no
  vendor certification, automatic send, or final Human acceptance is claimed.
- Formal project progress remains **30/100**. The G21 checkpoint does not add
  product points or change frozen ADRs, Core contracts, or Product Scope.

### G22 current RC hardening snapshot — 2026-09-02

- G22 continues from exact G21 SHA
  `ada5e9c8b4873aad4c53c74198171740d376d926` in an isolated lane.
- The encoded-loopback traversal review finding is remediated with raw
  percent-encoded dot/slash/backslash rejection and regression coverage.
- Core, targeted RC, browser-companion, Web install/test/build, baseline, and
  governance checks have current exit-code evidence. The validated product
  checkpoint is `532ce8f1` with clean clone `g22-clean-20260902`; the later
  independently reviewed evidence-state tip is `9a17716f` with final clean clone
  `g22-clean-final-20260902`. The current final branch tip is resolved from the
  approved remote and published in the completion result, not embedded in this
  self-referential snapshot.
- Browser live-vendor, native MV3 worker, and a fresh CDP rerun without a
  listener remain `UNVERIFIED`/`NEED_ACTION`; no certification is claimed.

- `CP-00` Baseline/Governance: **8/8 points accepted**.
- `CP-02` First Vertical Slice: **22/22 points accepted** for WP-01–WP-10.
- WP-08A is `ACCEPTED` after current deterministic evidence, Codex review PASS, and Human approval; it earns **2/2 points**.
- WP-08B is `ACCEPTED` after current deterministic evidence, Codex review PASS, and Human approval on 2026-08-19; it earns **2/2 points**.
- WP-09A is `ACCEPTED_ARCHITECTURE_GATE` after Human approval and Codex confirmation on 2026-08-19; it has no separate product point weight.
- WP-09B is `ACCEPTED` after Attempt 5 deterministic evidence, Codex review PASS, and Human acceptance on 2026-08-20; it earns **2/2 points**.
- WP-09C is `ACCEPTED` after Attempt 4 deterministic evidence, Codex review PASS, and Human acceptance on 2026-08-20; it earns **1/1 point**.
- WP-10 is `ACCEPTED` after current deterministic evidence, Codex PASS, and Human acceptance on 2026-08-20; it earns **2/2 points** and closes CP-02.
- WP-11 is `ACCEPTED` after Attempt 4 deterministic evidence, Codex review PASS, and Human acceptance on 2026-08-20; item progress is 100%. No standalone WP-11 point allocation inside CP-03 is defined in this roadmap, so project progress remains **30/100** until that allocation is explicitly recorded.
- WP-12 is `ACCEPTED` (Attempt 8): 45 contract tests PASS; full Core 238 collected / 237 passed / 1 skipped; baseline validation PASS; Codex PASS and Human acceptance recorded on 2026-08-21; commit `d6823d6` pushed to `backup/feature/first-vertical-slice`. WP-12 item progress is 100%. CP-03 point allocation is deferred until CP-03 completion per Human decision.
- WP-13 is `ACCEPTED` (Attempt 9), checkpoint `330adbc`: historical accepted-checkpoint Core evidence is 375 collected / 374 passed / 1 skipped; D11 Option C keeps approve/reject HUMAN_EVIDENCE unverified; reload validates actor_id, bound_task_id, bound_run_id, identity_hash, and provenance_token via independent canonical recomputation; persist uses dual-hash provenance for multi-field tamper detection; extended-key candidate detection prevents ordinary DOCUMENT_EVIDENCE false positives; maturity: PARTIAL_INTEGRITY (full-consistent 8-field rewrite NOT detectable; D12 deferred to CP-04+ per Human Option B); cross-task and same-task multi-run isolation verified; no new Decision/Verdict persistence. Historical product tests were not rerun for the current Governance task.
- Governance v1.1 checkpoint `358d263` includes explicitly approved D11 and WP-13 accepted-status synchronization; curated ADR-011 documentation received independent `VERIFIED_PASS`, after which Human explicitly accepted the ADR-011 architecture on 2026-08-25; product implementation remains unauthorized.
- Next ordered gates: fresh independent accepted-state synchronization review -> separate Human docs-checkpoint decision -> separately authorized PRE-WP14-A ADR-007 lifecycle/cleanup gate -> separately authorized PRE-WP14-B accepted ADR-011 Run-owned binding / Alembic migration / legacy-backfill gate -> OpenCode implementation with fresh independent Codex review.
- Current project progress: **30/100 = 30% accepted progress**.
- Current FVS progress: **22/22 = 100% accepted progress**.
- Browser E2E waiver is a limitation record, not additional earned progress.

### G01 Current state reconciliation delta — 2026-08-27

- Human-confirmed canonical runtime reference: `backup/runtime-adapters-integration@65c6582c70c4e724005adb983d65aba10ea3e8be`, scoped to Registry + WP-14 + WP-15 only.
- The canonical integration checkpoint has a clean clone with the approved SHA and required project paths. Current deterministic evidence is 87 combined Registry/WP-14/WP-15 targeted tests passed, exit code 0; 566 collected, exit code 0; Full Core 565 passed / 1 skipped, exit code 0; baseline and governance validators exit code 0. The post-sync main baseline validator process creation failed with exit code 1, and the `py.exe` fallback reported no installed Python with exit code 1; these are environment results, not product PASS/FAIL.
- Fresh independent Codex review of the three-file G01 document delta returned `VERIFIED_PASS` with `FINDINGS: NO BLOCKER`; it did not establish component acceptance, commit, push, or cross-machine readiness.
- This state decision does not change Registry, WP-14, or WP-15 component acceptance labels and does not add accepted project progress. CP-03 remains `IN_PROGRESS`; project progress remains **30/100 = 30%**.
- WP-16 is explicitly excluded from the canonical runtime reference. Its separate dirty checkout remains `IMPLEMENTED_PENDING_INDEPENDENT_REVIEW` with no commit, remote branch, or clean clone.
- The main checkout remains on `feature/first-vertical-slice`; the latest verified G01 document checkpoint before this final handoff update is `e4fd6e300799cab89744966b462b6c4bb25354c4` on `backup:feature/first-vertical-slice`. Pre-existing protected/unknown dirty paths remain preserved; the checkpoint does not change runtime scope or component acceptance.
- The authorized G01 checkpoint has a fresh clean clone at `artifacts/verification/clean-clone-g01-docs-feature-first-vertical-slice-e4fd6e3-20260827` with the exact SHA, required paths, clean status, and no WP-16 files.
- COMP-01～03 remain unchanged planning/submission items. No scope, dates, weights, product claims, ADR text, or merge strategy changed in this delta.

## 4. Checkpoint register

| Checkpoint | Scope | Weight | Baseline target | Entry / exit condition | Current status |
|---|---|---:|---|---|---|
| CP-00 | Baseline, governance, environment, frozen ADRs | 8% | 2026-08-19 | Baseline validation, branch/Git rules, source-of-truth docs, tool roles | ACCEPTED |
| CP-02 | First Vertical Slice runnable path | 22% | 2026-09-06 | Project → ContextPackage → Task → Run execution → Finding/Evidence → Result → History, fresh DB repeat, actual exit codes | ACCEPTED |
| CP-03 | Core product baseline | 27% | 2026-09-20 | Work modes, Council, hard gates, deep runtime adapters, Doctor/Conformance evidence | IN_PROGRESS — 14/27 accepted |
| CP-04 | Web, Local, Policy integration baseline | 20% | 2026-10-04 | Local profiles, routing/classification, WebSurface/companion fallback, Browser E2E evidence | IN_PROGRESS — 3/20 accepted |
| CP-05 | Product completion and feature freeze | 13% | 2026-10-18 | Workflow breadth, backup/restore, resource guards, metrics, UX pass, Golden Workflow regression | IN_PROGRESS — 2/13 accepted |
| CP-06 | Hardening and V1 RC acceptance | 10% | 2026-10-31 | Failure injection, security/egress, migration/restore, clean install, compatibility, RC acceptance | ACCEPTED — 10/10 bounded RC |
| COMP-NOTE | Competition content and submission | — | Human schedule | Human-owned material preparation and delivery; never changes development score | NOTE_ONLY_NON_SCORING |

## 5. Ordered work breakdown and forecast

### CP-00 — Baseline and governance

| Item | Scope | Owner / reviewer | Estimate | Target | Evidence / checkpoint |
|---|---|---|---:|---|---|
| BASE-01 | Scope, PRD/SA/SD, D01–D10, ADR-001–010 baseline | Human / Codex | 1 day | 2026-08-17 | Frozen source-of-truth documents |
| BASE-02 | Local workspace, dependencies, baseline validation | OpenCode / Codex | 2 days | 2026-08-18 | Actual validation output and exit codes |
| BASE-03 | Git, handoff, Writer/Reviewer/Antigravity governance | Codex / Human | 1 day | 2026-08-19 | `AGENTS.md`, workflow, acceptance, handoff rules |
| BASE-04 | FVS WP-01–WP-07 implementation and acceptance baseline | OpenCode/Codex | historical | 2026-08-19 | WP-07 checkpoint `d7060c4`, governance commit `eaf847c` |

### Competition note track — non-scoring

Competition work may proceed as a Human-owned documentation/delivery track, but
it is not a required development checkpoint, has no score, must not change
product scope, and must not turn planned capabilities into implemented claims.

| Item | Scope | Owner / reviewer | Estimate | Target | Evidence / checkpoint |
|---|---|---|---:|---|---|
| COMP-01 | Proposal/deck content confidence gate; Implemented / Planned V1 / Future truth labels | Human/ChatGPT / Codex | 3 days | 2026-08-25 | Source-to-claim matrix and approved content v1 |
| COMP-02 | Actual upload-form fields, demo requirements, and package checklist | Human/ChatGPT / Codex | 2 days | 2026-09-02 | Current form/requirement evidence |
| COMP-03 | Final submission readiness package | Human / Codex | 2 days | 2026-09-07 | Required materials and final decision record |

### CP-02 — First Vertical Slice completion

WP-01–WP-07, WP-08A, WP-08B, WP-09B, WP-09C, WP-09D, and WP-10 are accepted. CP-02 is complete; the next sequence begins CP-03.

| Item | Scope | Owner / reviewer | Estimate | Target | Acceptance checkpoint |
|---|---|---|---:|---|---|
| WP-01–07 | Domain, persistence, workflow, runtime, API, UI, integration acceptance | OpenCode/Codex | complete | 2026-08-19 | 12 points accepted; source and governance checkpoints recorded |
| WP-08A | ContextPackage REST create command using existing Domain/Repository boundary | OpenCode / Codex | 2 days | 2026-08-20 | 201/403/404/422, reload, secret boundary, no Run semantic change; Codex PASS + Human accepted 2026-08-19 |
| WP-08B | ContextPackage UI authoring/selection and API client integration | Antigravity / Codex | 2 days | 2026-08-23 | UI can create/select a ContextPackage without direct DB/process access; Attempt 2 complete, Codex PASS + Human accepted 2026-08-19; 2/2 points |
| WP-09A | Execution command API contract proposal and Human/Codex architecture gate | Codex / Human | 1 day | 2026-08-25 | `ACCEPTED_ARCHITECTURE_GATE`; Option A approved 2026-08-19; no separate product point weight |
| WP-09B | Wire approved execution command to `ExecutionService` and RunSupervisor | OpenCode / Codex | 3 days | 2026-08-29 | `ACCEPTED`; Attempt 5 Codex PASS + Human accepted 2026-08-20; 2/2 points; existing Run identity, persisted lifecycle/result, failure isolation, no fabricated evidence |
| WP-09C | Result, Finding, Evidence, Artifact, and History REST queries | OpenCode / Codex | 2 days | 2026-09-01 | `ACCEPTED` Attempt 4 (IMPLEMENTATION_ATTEMPT: 3 / REVIEW_ATTEMPT: 4); 1/1 point; 24 query tests PASS, governance sync recorded |
| WP-09D | Result/History UI with durable reload and error states | OpenCode / Codex | 2 days | 2026-09-04 | `ACCEPTED` Attempt 3; Codex PASS + Human acceptance 2026-08-20; 1/1 point; 78 Vitest tests PASS + build PASS, no Core change |
| WP-10 | FVS final deterministic acceptance | Codex / Human | 2 days | 2026-09-06 | `ACCEPTED` Attempt 1; Codex PASS + Human acceptance 2026-08-20; 2/2 points; 169 Core passed + 1 symlink skip, 4 fresh-DB/Alembic/reload tests, 78 frontend tests, build/baseline/diff PASS |

### CP-03 — Core product baseline

| Item | Scope | Owner / reviewer | Estimate | Target | Acceptance checkpoint |
|---|---|---|---:|---|---|
| WP-11 | Discuss / Review / Validate work-mode semantics and contract tests | OpenCode / Codex | 2 days | 2026-09-09 | `ACCEPTED` Attempt 4: Codex review PASS + Human acceptance 2026-08-20; 23 contract tests PASS, full Core 193 collected / 192 passed / 1 skipped, validate_baseline PASS; 422/201/403/404 verified; no fourth top-level mode; item progress 100%; standalone CP-03 point allocation not defined |
| WP-12 | Council, parallel analysis, cross review, synthesis, partial failures | Codex/OpenCode / Codex | 3 days | 2026-09-12 | `ACCEPTED` Attempt 8: 45 contract tests PASS, full Core 238 collected/237 passed/1 skipped, validate_baseline PASS, Codex PASS + Human acceptance 2026-08-21, commit `d6823d6` pushed; no new table/migration/endpoint/RunState/WorkMode/EvidenceType; CP-03 point allocation deferred until CP-03 completion |
| WP-13 | Workflow hard gates, Evidence_Check, Human gate, verified verdict rules | OpenCode / Codex | 2 days | 2026-09-14 | `ACCEPTED` Attempt 9, checkpoint `330adbc`: historical accepted-checkpoint evidence 135 contract tests passed, full Core 375 collected / 374 passed / 1 skipped; D11 Option C approve/reject fail-closed; PARTIAL_INTEGRITY (full-consistent rewrite NOT detectable; D12 deferred to CP-04+); no new table/migration/endpoint/RunState/WorkMode/EvidenceType; CP-03 point allocation deferred until CP-03 completion |
| PRE-WP14-A | ADR-007 timeout, cancel, lifecycle and cleanup architecture/conformance gate | OpenCode / Codex | Gated | Before WP-14 | `DOCUMENTATION_INTEGRATED / NOT_IMPLEMENTED`; Human-approved existing-contract compatibility; deterministic timeout/cancel/cleanup/failure-isolation evidence; no premature runtime implementation |
| PRE-WP14-B | FULL ADR-011 Runtime Binding architecture, Run-owned immutable snapshot, Alembic migration/backfill/rollback plan | OpenCode / Codex | Gated | Before WP-14 | `ADR-011 HUMAN_ACCEPTED / NOT_IMPLEMENTED / IMPLEMENTATION_NOT_AUTHORIZED`; separate Human source/migration allowlist and deterministic legacy/restore tests; no Attempt or new subsystem |
| WP-14 | Codex Runtime adapter conformance | OpenCode / Codex | 2 days | 2026-09-17 | Human-approved PRE-WP14-A/B; contract, lifecycle, result/error, evidence, cleanup, maturity label; Writer != Reviewer; Human acceptance |
| WP-15 | OpenCode Runtime adapter conformance | OpenCode / Codex | 2 days | 2026-09-19 | Same normalized contract and failure isolation |
| WP-16 | Doctor, capability/version matrix, conformance reporting | OpenCode / Codex | 2 days | 2026-09-20 | Actual health/version/capability evidence; no false certification |

### CP-04 — Web, Local, and Policy integration

| Item | Scope | Owner / reviewer | Estimate | Target | Acceptance checkpoint |
|---|---|---|---:|---|---|
| WP-17 | LocalModelEndpoint profiles: LM Studio, Ollama, generic OpenAI-compatible | OpenCode / Codex | 2 days | 2026-09-23 | Detection, model identity, timeout, local evidence |
| WP-18 | Classification, routing, LOCAL_ONLY, egress decision and audit evidence | Codex/OpenCode / Codex | 2 days | 2026-09-26 | No downgrade or silent cloud fallback |
| WP-19 | WebSurface contract and thin MV3 companion boundary | OpenCode / Codex | 2 days | 2026-09-29 | Manual/clipboard fallback, authenticated loopback, driver isolation |
| WP-20 | ChatGPT/Claude/Gemini Level 3A assisted flow and fallback | Antigravity/OpenCode / Codex | 3 days | 2026-10-02 | Launch/fill/user-confirmed send/capture/normalize evidence |
| WP-21 | Browser E2E rerun after development completion | Antigravity / Codex | 2 days | 2026-10-04 | Bounded PASS: Chrome/CDP synthetic-host DOM journey, 28/28 failure paths, screenshots/trace; live vendor compatibility remains unverified |

### CP-05 — Product completion and feature freeze

| Item | Scope | Owner / reviewer | Estimate | Target | Acceptance checkpoint |
|---|---|---|---:|---|---|
| WP-22 | Nine built-in workflow templates and schema regression | OpenCode / Codex | 2 days | 2026-10-07 | Validation and representative execution evidence |
| WP-23 | Backup, restore, migration foundation and fresh-data verification | OpenCode/Codex / Codex | 2 days | 2026-10-10 | Backup-before-migration, restore, secret exclusion |
| WP-24 | Budget, timeout, concurrency, and cleanup guards | Codex/OpenCode / Codex | 2 days | 2026-10-12 | Resource limits, cancel/timeout cleanup, no orphan process |
| WP-25 | Minimal evaluation and usage metrics | OpenCode / Codex | 1 day | 2026-10-14 | Metrics are descriptive, not fabricated success claims |
| WP-26 | UX progressive-disclosure pass | OpenCode / Antigravity | 1 day | 2026-10-15 | Accessibility, error/loading states, no raw runtime control panel |
| WP-27 | Four Golden Workflow deep regression | Codex / Human | 2 days | 2026-10-18 | Feature Freeze gate and evidence bundle |

### CP-06 — Hardening and V1 RC acceptance

| Item | Scope | Owner / reviewer | Estimate | Target | Acceptance checkpoint |
|---|---|---|---:|---|---|
| WP-28 | Failure injection, adapter crash isolation, cancel/timeout/child cleanup | Codex / Human | 2 days | 2026-10-21 | Core remains available; cleanup verified |
| WP-29 | Secret, egress, permission, policy, and evidence provenance review | Codex / Human | 2 days | 2026-10-23 | No secret leakage; no silent policy bypass |
| WP-30 | Migration, backup/restore, clean-install acceptance | OpenCode/Codex / Codex | 2 days | 2026-10-26 | Fresh environment and old-data compatibility evidence |
| WP-31 | Packaging, compatibility matrix, known limitations | OpenCode / Codex | 1 day | 2026-10-28 | Maturity labels supported by real evidence |
| WP-32 | V1 RC acceptance and final handoff | Codex / Human | 2 days | 2026-10-31 | All claims have current evidence; no unresolved critical blocker |

## 6. Standard task delivery sequence

Every work item must produce the following in order:

1. Task document with scope, owner, dependencies, protected areas, acceptance criteria, and estimated dates.
2. Writer prompt and implementation changes limited to the task document.
3. Targeted tests added or updated before claiming completion.
4. Writer handoff with changed/untracked files, exact commands, actual exit codes, ADR impact, scope deviation, limitations, and unverified items.
5. Codex independent review and deterministic rerun.
6. Human decision for acceptance, waiver, scope change, or rework.
7. Update `docs/11_PROJECT_STATE.md`, `docs/12_HANDOFF_CURRENT.md`, and the relevant task document.
8. Record the checkpoint and earned progress. Git stage/commit/push occurs only with explicit authorization.

## 7. Progress reporting contract

After every completed item, report:

```yaml
TASK_ID:
STATUS: PLANNED | IMPLEMENTING | READY_FOR_CODEX_REVIEW | NEED_ACTION | ACCEPTED | CHECKPOINTED
ITEM_PROGRESS: 0% | 100% after acceptance
PROJECT_PROGRESS: accepted_points/100
PHASE_PROGRESS: accepted_phase_points/phase_weight
CHECKPOINT:
CHANGED_FILES:
TESTS: command + result + exit code
ADR_IMPACT:
SCOPE_DEVIATION:
KNOWN_LIMITATIONS:
UNVERIFIED:
NEXT_ACTION:
```

An implementation that is merely `READY_FOR_CODEX_REVIEW` is not counted as accepted progress. A skipped test must remain explicitly `SKIPPED/UNVERIFIED`; a waiver does not certify the skipped capability.

## 8. Schedule risks and control points

- **R1 — Single-writer throughput**: the forecast is tight. If a checkpoint slips by more than two calendar days, stop scope expansion and request a Human trade-off.
- **R2 — Execution contract protection**: WP-09A and WP-09B are accepted. WP-09C/D/10 must not change ADR-004, ADR-007, ADR-008, existing Run-create behavior, or the accepted execution command semantics without a new gate.
- **R3 — Unicode workspace launcher**: Core test execution may require the validated alternate Windows route. Mark environment failures separately from product failures.
- **R4 — Browser boundary**: bounded synthetic-host browser evidence has a
  current G21 result, while native worker dispatch and live vendor journeys
  remain deferred/unverified; do not report a false broad compatibility PASS.
- **R5 — Competition deadline**: COMP-01/02/03 must not silently change V1 product claims or divert a source Writer without a recorded decision.

## 9. Roadmap change control

This roadmap is a planning baseline, not a new ADR. Any change to scope, dates, weights, dependencies, or acceptance maturity must update this document and the current handoff with the reason, impact, replacement work, and Human decision. No task may silently skip a checkpoint.

## 10. Do Not Change

- Do not change the accepted WP-09B execution command outside a new approved contract/architecture gate.
- Do not change ADR-001–010 without a separate architecture proposal and Human approval.
- Do not count Browser E2E waiver as Browser certification.
- Do not stage, commit, push, or rewrite unrelated user changes without explicit authorization.
