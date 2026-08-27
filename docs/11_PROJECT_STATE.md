# Project State

Date: 2026-08-27
Version: Development Baseline v1.0 + Dev Preparation Profile v1.0.2
Milestone: First Vertical Slice — WP-08A/WP-08B/WP-09B/WP-09C/WP-09D/WP-10/WP-12/WP-13 ACCEPTED; CP-02 complete; CP-03 in progress; PRE-WP14-A HUMAN_ACCEPTED / IMPLEMENTATION_ACCEPTED at `28196c9`; PRE-WP14-B HUMAN_ACCEPTED / IMPLEMENTATION_ACCEPTED (Human decision 2026-08-26; checkpointed at `c615733`) on baseline `934a219`

## Confirmed
- Product Scope Decisions D01–D10 confirmed.
- ADR-001～ADR-010 confirmed and frozen; ADR-011 Human-accepted as architecture; PRE-WP14-B implementation separately Human-authorized and accepted after fresh independent Codex `VERIFIED_PASS`.
- Stack: React/TypeScript/Vite + Python/FastAPI/asyncio + SQLAlchemy/Alembic/SQLite + REST/WebSocket + pytest/Vitest/Playwright + Chrome MV3 companion.
- Runtime process model: Core-owned Run Supervisor; Adapter-owned vendor logic.
- Artifact: SQLite metadata + filesystem content + SHA-256 identity.
- Context: versioned reference manifest, not prompt-only storage.
- Workflow: YAML authoring + JSON Schema + canonical model; fixed node set.
- Secret boundary: SecretRef + OS-backed SecretStore; secret values excluded from Git/Evidence/Export.
- Development target: Feature Freeze 2026-10-18; V1 acceptance 2026-10-31.
- Competition latest notice: initial-review deadline 2026-09-07.
- Development tools: Codex + OpenCode Go + Antigravity + Claude (on-demand bounded role), same Git project directory, Single Active Writer.

## Local Workspace
- Primary Windows path: `D:\AI學習教材\PolyNexus`
- Absolute path is a local profile only; product code remains repo-relative.

## Current Priority
1. Preserve the two excluded pre-existing dirty files (`docs/15_DOCUMENT_INDEX.md`, `docs/tasks/WP-12.md`) and their ownership; PRE-WP14-A remains accepted at `28196c9`.
2. PRE-WP14-B is checkpointed at `c615733`; WP-14/WP-15 component acceptance remains separately gated. The Human-confirmed G01 runtime checkpoint is `backup/runtime-adapters-integration@65c6582c70c4e724005adb983d65aba10ea3e8be` for Registry, WP-14, and WP-15 only.
3. WP-14/WP-15 component acceptance remains separately gated; WP-16 is excluded from the G01 canonical runtime reference and remains an independent review task. GitHub enablement and Browser E2E remain independent future gates.

## Current Product Slice
First Vertical Slice target by 2026-09-06:
`Project → Review → Runtime → Finding/Evidence → Result → History`.

## Remaining Non-blocking Decisions
- Final UI visual design system/components.
- Exact Windows SecretStore provider implementation detail.
- Final Python/Node dependency lock strategy after first local install.
- GitHub URL, remote rename/add, initial branch/tag push allowlist, and clean-clone verification path require separate Human approval.
- Actual competition upload-form fields/demo requirement still require recheck before submission.
## Next Gate

PRE-WP14-B is HUMAN_ACCEPTED / IMPLEMENTATION_ACCEPTED on baseline `934a219` under the Human-approved 15-file allowlist after fresh independent Codex `VERIFIED_PASS`. Review history: Attempt 1 FAIL remediated; Attempt 2 Codex FAIL (4 findings) remediated in Attempt 3; Attempt 3 Codex FAIL (false log-capture PASS label / missing migration-path trigger acceptance / stale docstring) remediated in Attempt 4. Log capture remains NOT_IN_SCOPE/UNVERIFIED, the migration-installed `trg_runs_reject_delete` was dynamically verified across upgrade/downgrade/re-upgrade, and the ExecutionService docstring matches actual lifecycle ownership. Current gate: exact-allowlist Git checkpoint authorized by Human; checkpoint SHA is recorded after commit.

## Current Development State

Phase: First Vertical Slice — CP-03 in progress; PRE-WP14-A accepted at `28196c9`; PRE-WP14-B Human-accepted / implementation-accepted (Attempt 4)
Next Phase: Registry/WP-14/WP-15 component acceptance remains separately gated; WP-16 requires independent review. No production-runtime support claim is authorized by this state reconciliation.

Current Branch: feature/first-vertical-slice
Accepted Baseline Commit: `c6157335069f3df3484030aa772bbf5c2aec248e` (`PRE-WP14-B` implementation and acceptance checkpoint)
Current Checkout HEAD: `c74a69629708f5c4dd03d69fca577ff70cf73297` (working tree dirty; staged state empty at G01 revalidation)
Latest FVS Checkpoint: 330adbc (`feat(core): accept WP-13 workflow gates`)
Current Planned Task: G01 project/runtime/document state reconciliation; next component gates remain separately routed
Active Writer: Codex — G01 factual document reconciliation only; existing runtime task ownership is preserved
Reviewer: Fresh independent Codex context; Writer != Reviewer is mandatory
Antigravity: `NOT_REQUIRED` for this Core-only task; no UI/browser/E2E surface

Architecture:
- ADR-001 through ADR-010 are CONFIRMED / FROZEN FOR V1 IMPLEMENTATION; decision text unchanged.
- ADR-011 remains `HUMAN_ACCEPTED`; this task implements within the accepted architecture without modifying any ADR text.

Development Environment:
- Windows development readiness: PASS for the controlled launcher `C:\temp_pn_venv2\Scripts\python.exe` (used for all PRE-WP14-A Attempt 2 verification on 2026-08-25); plain `.venv\Scripts\python.exe` remains blocked in sandboxed contexts.
- Core pytest: PRE-WP14-A Attempt 2 evidence (2026-08-25, checkpoint basis `8994ef9`) — targeted `test_runtime_skeleton.py` 17 passed (JUnit XML `failures=0`), regression lifecycle+WP07 17 tests / 16 passed / 1 skipped, WP09+WP12+WP13 regression 218 passed, Full Core 390 collected / 389 passed / 1 skipped (`failures=0`, `errors=0`); all exit code 0. Not rerun by this docs-only state-sync task.
- Frontend Vitest: historical accepted-checkpoint evidence only — 78 passed (61 baseline + 17 WP-09D); not rerun.
- Frontend build: historical accepted-checkpoint evidence only; not rerun.
- Local Git backup contains the runtime checkpoint refs; the G01 document delta performed no Git operation. The separately Human-authorized G01 document checkpoint does not change component acceptance, runtime scope, or whole-project cross-machine readiness.

## G01 Current State Reconciliation — 2026-08-27

- Human-confirmed canonical runtime reference: `backup/runtime-adapters-integration@65c6582c70c4e724005adb983d65aba10ea3e8be`, scoped to Registry + WP-14 + WP-15 only. Component acceptance labels are unchanged.
- Main revalidation before this document sync: branch `feature/first-vertical-slice`, HEAD `c74a69629708f5c4dd03d69fca577ff70cf73297`, staged state empty, 5 modified paths and 5 untracked paths. After the approved G01 document delta, the current working tree is 7 modified paths and 5 untracked paths; the two additional modified paths are the allowlisted `docs/11_PROJECT_STATE.md` and `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`. Protected and unknown dirty paths remain excluded.
- Component refs remain separately observable: Registry `b395be8619f7e97d8e2b1951cb928500175ea506`, WP-14 `20004a78d58b95d2cb017188ddb906a242b8a0ff`, and WP-15 `c26e10becb04da868cdc0038f5d99cc6ea3d21a1`.
- Fresh independent Codex document review returned `VERIFIED_PASS` with `FINDINGS: NO BLOCKER`; the review was limited to the three approved documents and current read-only evidence, and does not establish component acceptance or Git/cross-machine gates.
- Canonical integration clean clone `artifacts/verification/clean-clone-runtime-adapters-integration-65c6582-20260827` is on branch `runtime-adapters-integration`, HEAD `65c6582c70c4e724005adb983d65aba10ea3e8be`, clean, with required project paths present.
- WP-16 remains `IMPLEMENTED_PENDING_INDEPENDENT_REVIEW` in `artifacts/worktrees/wp16-runtime-doctor`, based on `65c6582`, dirty, without a remote `wp16-runtime-doctor` ref or clean clone. It is excluded from the canonical runtime reference.
- Current integration evidence: combined Registry/WP-14/WP-15 targeted tests 87 passed, exit code 0; collect-only 566 collected, exit code 0; Full Core 565 passed / 1 skipped, exit code 0; baseline validator and governance validator exit code 0.
- Separate WP-16 evidence remains non-canonical: targeted tests 16 passed, exit code 0; regression 144 passed, exit code 0; collect-only 582 collected, exit code 0; Full Core 581 passed / 1 skipped, exit code 0; baseline and governance validators exit code 0.
- The first sandbox launcher failure exit code 1, the first ownership-protected Git check exit code 1, and the WP-16 no-upstream query exit code 128 remain recorded as environment/state results. Controlled runtime reruns returned their separate exit codes 0; Full Core retained the non-fatal Windows pytest temporary-directory cleanup warning. The post-sync main baseline validator again failed process creation with exit code 1, and `C:\Windows\py.exe -3 -B scripts\validate_baseline.py` reported no installed Python with exit code 1; both are environment results, not product PASS/FAIL.
- CP-03 remains `IN_PROGRESS`; project progress remains **30/100 = 30%** and accepted FVS remains **22/22 = 100%**. COMP-01～03 remain unchanged planning/submission items.
- G01 changed only the approved current-state documents. No component was marked `HUMAN_ACCEPTED`, `COMMITTED`, `PUSHED`, or `CROSS_MACHINE_CONTINUATION_READY` by this document sync.

Tool Onboarding:
- OpenCode Desktop: PASS
- ChatGPT / Codex Desktop: PASS
- Antigravity Desktop: PASS

Primary Workspace:
D:\AI學習教材\PolyNexus

Tool Roles:
- Codex: Architecture / Core / Contract / Hard Bug / Critical Review
- OpenCode: Primary Builder / Tests / Templates / Routine Implementation
- Antigravity: Browser / UI / E2E / Integration / Milestone Red Team
- Claude: task-assigned bounded analysis/documentation/second opinion; no default Writer/Reviewer/Git authority

Development Rule:
- Single Active Writer.
- AI opinion does not override deterministic evidence.
- Existing deterministic evidence is not rerun solely because the active AI tool changes.

Governance v1.1 / Pre-WP14 status:
- WP-13 checkpoint exists at `330adbc`; Governance v1.1 at `358d263`.
- PRE-WP14-A (ADR-007 timeout/cancel cleanup compliance in RunSupervisor) is `HUMAN_ACCEPTED / IMPLEMENTATION_ACCEPTED` and checkpointed at `28196c9`. Sanitization evidence is boundary-scoped to the shared `_cleanup_and_verify()` cleanup/cancel/timeout machinery; generic workflow-executor exception handling elsewhere in `execute_run()` (persisting `str(exc)` and re-raising) remains pre-existing behavior.
- PRE-WP14-B is HUMAN_ACCEPTED / IMPLEMENTATION_ACCEPTED on baseline `934a219` under the Human-approved 15-file allowlist: immutable Run-owned RuntimeBindingSnapshot, TransportKind/AuthOwnership/UsageVisibility enums, fail-closed Registry/Factory (no vendor Core branches), `run_binding_snapshots` table with insert-once/mutation-rejection semantics, Alembic `0002` with deterministic legacy/reference backfill. Status: accepted after fresh independent Codex `VERIFIED_PASS`; exact-allowlist Git checkpoint is authorized and SHA is recorded after commit.
- Excluded pre-existing dirty files with preserved ownership: `docs/15_DOCUMENT_INDEX.md` and `docs/tasks/WP-12.md`; they must not be silently absorbed into any future allowlist.
- Local backup remains a local checkpoint transport; GitHub remote configuration, push and clean-clone verification are separate future Human Gates. `CROSS_MACHINE_CONTINUATION_READY` is not yet established.
- ADR impact: ADR-001～010 decision text unchanged; ADR-011 remains `HUMAN_ACCEPTED` per `docs/29_ADR_011_RUNTIME_BINDING_AND_TRANSPORT.md`; this implementation stays within the accepted architecture. Attempt, RoutingEnvelope and trusted-human authentication remain deferred.
- Future production runtime work (WP-14/WP-15) requires its own gates; no production dependency was added by PRE-WP14-B.

OpenCode Model Routing:
1. Default: DeepSeek V4 Flash
2. If unavailable / policy-blocked: MiMo V2.5
3. If MiMo V2.5 repeatedly fails deterministic validation: MiMo V2.5 Pro
4. Architecture / security / lifecycle / hard root cause: escalate to Codex

## Latest Verification

PRE-WP14-B implementation verification (Attempt 4 current Writer evidence, baseline `934a219`, launcher `C:\temp_pn_venv2\Scripts\python.exe -B`): WP-14B targeted 84 passed; persistence + runtime skeleton 60 passed (43 + 17); WP07+WP09 regression 72 passed / 1 SKIPPED (Windows symlink policy — labeled SKIPPED, not PASS); collect-only 479 collected; Full Core 478 passed / 1 skipped; baseline validator PASS; governance validator PASS — all exit code 0. Migration lifecycle ran only inside pytest temporary isolated SQLite databases. The migration-installed `trg_runs_reject_delete` guard is dynamically accepted across upgrade/downgrade/re-upgrade.

These are Writer-produced results independently verified by fresh independent Codex; Human acceptance was granted on 2026-08-26. They are acceptance evidence for the bounded PRE-WP14-B implementation only; API/log/exports-handoff limitations remain explicitly NOT_IN_SCOPE/UNVERIFIED. The exact-allowlist Git checkpoint is authorized and its SHA is recorded after commit.

- PRE-WP14-B Attempt 2 verification counts (80/43/49/475-collected/474-passed) are **historical/superseded** by the Attempt 4 evidence above and are retained only in task history (`docs/tasks/PRE-WP14-B.md`); they must not be cited as current state.
- PRE-WP14-A Attempt 2 verification (historical evidence for accepted checkpoint `28196c9`): targeted `test_runtime_skeleton.py` 17 passed at the time; superseded counts are recorded in the task history.
- Browser DOM / Playwright E2E remains `UNVERIFIED/SKIPPED`; Windows symlink containment remains `UNVERIFIED/SKIPPED`; true concurrent HTTP duplicate-command execution remains `UNVERIFIED`; application log capture, API response surface and exports/handoff secret-exclusion scans for PRE-WP14-B remain `NOT_IN_SCOPE/UNVERIFIED`. Pytest temp-dir cleanup PermissionError is a non-fatal Windows environment warning (all commands exit 0).
- WP-13 accepted-checkpoint verification (historical evidence for commit `330adbc`): 375 Core tests collected, 374 passed, 1 skipped, exit code 0.
- Current project progress remains **30/100 = 30%**; accepted FVS remains **22/22 = 100%**.

## ROADMAP-01 / WP-08A + WP-08B Acceptance (Historical checkpoint before WP-09B)

- Master roadmap: `docs/28_MASTER_DEVELOPMENT_ROADMAP.md` — CONFIRMED by Human on 2026-08-19.
- Accepted project progress: **24/100 = 24%**.
- Accepted FVS progress: **16/22 = 72.7%**.
- WP-08A: `ACCEPTED`, **2/2 points earned** after Codex review PASS and Human approval.
- WP-08B: `ACCEPTED`, **2/2 points earned** after Codex review PASS and Human approval on 2026-08-19.
- Current source changes are accepted within WP-08A/WP-08B scope; no Git checkpoint was created in this sync.
- Superseded next step: WP-09B review and Human acceptance completed on 2026-08-20.

## WP-09A Architecture Gate Preparation (Historical — gate completed 2026-08-19)

- Task document: `docs/tasks/WP-09A.md`.
- Status: `ACCEPTED_ARCHITECTURE_GATE`; Human approval and Codex confirmation recorded on 2026-08-19; no `services/core/` or `apps/web/` source changes in the gate.
- Key finding: the accepted Run-create API persists a `CREATED` Run, while the current `ExecutionService` / `RunSupervisor` path creates another Run. The execution target, ContextPackage authority, repeat semantics, response status, and failure persistence must be approved before WP-09B.
- Approved decision: Option A — `POST /api/v1/runs/{run_id}/execute`, using the persisted Run identity and Run ContextPackage reference; no duplicate Run.
- ADR impact: Codex/Human contract gate confirmed; ADR-004, ADR-007, ADR-008, and ADR-010 are respected with no ADR file changes. ADR-001–010 remain frozen.
- Item progress: `100%` for the architecture gate; no product points assigned or earned from this contract-only task.
- Accepted project progress remains **24/100 = 24%**; accepted FVS progress remains **16/22 = 72.7%**.
- Historical next owner completed: Codex review PASS and Human acceptance recorded on 2026-08-20.
- Browser E2E: remains `UNVERIFIED/SKIPPED` and is unrelated to this gate.

## WP-08B Development Gate

- Task document: `docs/tasks/WP-08B.md`.
- Scope: React UI authoring/selection using the accepted WP-08A ContextPackage POST endpoint; no Core changes.
- Architecture gate: implementation detail only; no new contract, ADR impact, migration, dependency, or endpoint.
- Product source changes: frontend implementation complete and accepted (Attempt 2, 61 tests PASS).
- Accepted project progress: **24/100 = 24%**; WP-08B earns **2/2 points**.
- Required next owner: WP-09A contract/architecture gate.
- Browser E2E: remains `UNVERIFIED/SKIPPED` and is deferred until the current development sequence is complete.

## WP-08A Development Gate

- Task document: `docs/tasks/WP-08A.md`.
- Scope: authenticated `POST /api/v1/projects/{project_id}/context-packages` using the existing Domain and Repository boundaries.
- Product source changes: WP-08A and WP-08B accepted; WP-09A implementation not started.
- ADR impact: NONE; WP-08B execution API remains a separate contract decision.
- Required next owner: WP-09A Codex/Human architecture gate.
- Browser E2E: remains `UNVERIFIED/SKIPPED` and is deferred until the current development sequence is complete.

## Current Next Gate

## Current Governance v1.1 Gate

- WP-12 Attempt 8 is `ACCEPTED`: Codex review PASS and Human acceptance recorded on 2026-08-21.
- Acceptance evidence: 45 WP-12 contract tests passed; full Core reported `238 collected / 237 passed / 1 skipped`; `validate_baseline.py` PASS; `git diff --check` PASS.
- Git checkpoint: commit `d6823d6` (`feat(core): accept WP-12 council orchestration`) pushed to `backup/feature/first-vertical-slice`.
- Accepted project progress remains **30/100** and accepted FVS remains **22/22**. CP-03 point allocation is intentionally deferred until CP-03 completion per Human decision.
- WP-13 is `ACCEPTED` at checkpoint `330adbc` (`feat(core): accept WP-13 workflow gates`). Its D11 Option C and PARTIAL_INTEGRITY limitations remain recorded in `docs/tasks/WP-13.md`; they are not modified by the current Governance patch.
- Governance v1.1 checkpoint is `358d263` after independent review and Human approval. ADR-011 architecture is Human-accepted; current gate: accepted-state synchronization -> fresh independent documentation reviewer -> separately authorized docs checkpoint or PRE-WP14 implementation Gate. No stage, commit, push or remote operation is authorized.
- D11 is explicitly Human-approved for Governance ownership; the three unrelated pre-existing dirty files remain excluded from the future exact staged-file allowlist.
- Product sequence after a separately Human-approved Governance checkpoint: curated ADR-011 docs-only integration -> Human-approved Pre-WP14-A ADR-007 lifecycle gate and Pre-WP14-B FULL ADR-011 binding/migration plan -> separately authorized OpenCode implementation -> fresh independent Codex review -> Human acceptance.
- Separate infrastructure gate: GitHub enablement precheck -> Human-approved remote configuration -> separate Human-approved controlled push -> clean-clone verification; GitHub remains Development Collaboration Infrastructure only.

WP-09B, WP-09C, WP-09D, WP-10, WP-11, WP-12 and WP-13 are accepted. CP-02 is complete; CP-03 point allocation remains deferred until CP-03 completion per Human decision. Product development resumes only after the current governance gate is resolved.

## WP-09B Development Gate

- Task document: `docs/tasks/WP-09B.md`.
- Status: `ACCEPTED` (Attempt 5); Codex independent review PASS and Human acceptance recorded on 2026-08-20.
- Scope: wire `POST /api/v1/runs/{run_id}/execute` to the existing persisted Run using the accepted Option A contract.
- Protected behavior: existing Run-create remains `201 CREATED` and inert; Run identity, ContextPackage reference, lifecycle events, failure persistence, sanitized reason, and no-fabricated-output rules are mandatory.
- Accepted project progress: **26/100 = 26%**; accepted FVS progress: **18/22 = 81.8%**; WP-09B earns **2/2 points**.
- Completed transition: WP-09C and WP-09D were implemented, independently reviewed, and Human-accepted; WP-10 is next.
- Symlink containment remains `UNVERIFIED/SKIPPED`; Browser E2E remains `UNVERIFIED/SKIPPED`; true concurrent HTTP duplicate execution remains `UNVERIFIED`.

## WP-09C Development Gate

- Task document: `docs/tasks/WP-09C.md`.
- Status: `ACCEPTED` (Attempt 4; IMPLEMENTATION_ATTEMPT: 3 / REVIEW_ATTEMPT: 4); Codex review PASS and Human acceptance recorded on 2026-08-20.
- Architecture result: implementation detail under ADR-004/008/010; no new ADR, migration, dependency, Domain model, or frontend change.
- Scope: five authenticated, run-scoped, read-only REST queries for Result, Finding, Evidence, Artifact metadata/reference, and durable RunEvent history.
- Required behavior: stable wrappers, deterministic ordering, `403/404/422`, durable reload, fail-closed ownership validation, and no fabricated output.
- Protected behavior: WP-09B execution command, Run-create semantics, lifecycle/CAS/failure persistence, WP-08A/B, ADR-001–010, and all migration/frontend files.
- Accepted project progress is **27/100 = 27%**; accepted FVS progress is **19/22 = 86.4%**; WP-09C earns **1/1 point**.
- Next owner: Codex/Human prepare and execute WP-10 final deterministic acceptance.
- Antigravity: `NOT_REQUIRED` for this Core-only task; Browser E2E remains `UNVERIFIED/SKIPPED`.

## WP-09D Development Gate

- Task document: `docs/tasks/WP-09D.md`.
- Status: `ACCEPTED` (Attempt 3); Codex review PASS and Human acceptance recorded on 2026-08-20; 78 frontend tests PASS, build PASS.
- Goal: add a read-only Result/History detail view that reloads Run metadata and all five accepted WP-09C query wrappers from REST.
- Scope: `apps/web` API client, props-based view/navigation, Run detail component, minimal styles, and Vitest integration coverage.
- Protected behavior: WP-08A/WP-08B, WP-09B execution/lifecycle/CAS/failure, WP-09C endpoint wrappers/ordering/ownership, ADR-001–010, no storage/secret/direct Core access.
- ADR impact: `NONE`. No endpoint, response, lifecycle, evidence, or dependency change.
- Accepted project progress is **28/100 = 28%**; accepted FVS progress is **20/22 = 90.9%**; WP-09D earns **1/1 point**.
- Browser E2E remains `UNVERIFIED/SKIPPED`; it is not a WP-09D implementation acceptance requirement.
- Next owner: Codex/Human prepare WP-10 final deterministic acceptance.

## WP-10 Final Deterministic Acceptance

- Task document: `docs/tasks/WP-10.md`.
- Status: `ACCEPTED` (Attempt 1); Codex deterministic acceptance PASS and Human acceptance recorded on 2026-08-20.
- Scope: final acceptance-only verification of the First Vertical Slice; no product source, REST contract, schema, migration, dependency, or ADR changes.
- Evidence: Core `169 passed, 1 skipped` from `170 collected` (WP-10 accepted baseline; current WP-11 full-Core run is `193 collected / 192 passed / 1 skipped`), fresh DB/Alembic/reopen-reload `4 passed`, frontend `78 passed`, frontend build PASS, baseline PASS, and `git diff --check` PASS; all exit code 0.
- Skipped/unverified: Browser DOM / Playwright E2E, Windows symlink escape, and true concurrent HTTP duplicate execution remain explicitly `UNVERIFIED/SKIPPED`.
- ADR impact: `NONE`.
- Scope deviation: `NONE`; pre-existing `docs/15_DOCUMENT_INDEX.md` remains unstaged and excluded.
- Accepted project progress is **30/100 = 30%**; accepted FVS progress is **22/22 = 100%**; WP-10 earns **2/2 CP-02 points**.
- CP-02 First Vertical Slice is complete. WP-11 is `ACCEPTED` (Attempt 4): Codex review PASS and Human acceptance recorded on 2026-08-20; `services/core/tests/test_wp11_work_mode.py` has 23 passed, full Core is `193 collected / 192 passed / 1 skipped`, and `validate_baseline.py` is PASS. WP-11 item progress is 100%. The roadmap does not define a standalone WP-11 point allocation inside CP-03, so accepted project progress remains **30/100** until that allocation is explicitly recorded; CP-03 is now in progress. Next owner: WP-12 planning.
- WP-12 is `ACCEPTED` (Attempt 8): 45 contract tests PASS, full Core 238 collected / 237 passed / 1 skipped, `validate_baseline.py` PASS, Codex PASS and Human acceptance recorded on 2026-08-21, and commit `d6823d6` pushed. WP-13 is the next task; CP-03 point allocation remains deferred until CP-03 completion.
