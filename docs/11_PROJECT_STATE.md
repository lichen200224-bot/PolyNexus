# Project State

Date: 2026-08-25
Version: Development Baseline v1.0 + Dev Preparation Profile v1.0.2
Milestone: First Vertical Slice — WP-08A/WP-08B/WP-09B/WP-09C/WP-09D/WP-10/WP-12/WP-13 ACCEPTED; CP-02 complete; CP-03 in progress; Governance v1.1 consolidation in progress

## Confirmed
- Product Scope Decisions D01–D10 confirmed.
- ADR-001～ADR-010 confirmed.
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
1. Complete Governance v1.1 documentation alignment, including the explicitly Human-approved D11 ownership decision, WP-13 status synchronization and independent acceptance; preserve the three excluded pre-existing dirty files.
2. After an independently accepted and Human-approved Governance checkpoint, perform a separately authorized curated import of the existing docs-only ADR-011 worktree; do not merge overlapping dirty worktrees.
3. Complete Pre-WP14-A ADR-007 lifecycle/cleanup and Pre-WP14-B FULL ADR-011 Runtime Binding architecture gates before separately authorized OpenCode implementation; GitHub enablement and Browser E2E remain independent future gates.

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

WP-13 is accepted at checkpoint `330adbc`. Current gate is the uncommitted Governance v1.1 consolidation patch -> independent review by a reviewer other than the current Writer/context -> Human checkpoint decision. GitHub/cross-machine enablement remains not ready and must be handled by later gated steps.

## Current Development State

Phase: First Vertical Slice — WP-10 final deterministic acceptance PASS; Human acceptance recorded on 2026-08-20; CP-02 complete
Next Phase: Governance v1.1 alignment -> fresh independent acceptance -> Human checkpoint -> curated ADR-011 document integration -> Pre-WP14-A/B Human Architecture Gates -> separately authorized OpenCode implementation / independent Codex review

Current Branch: feature/first-vertical-slice
Current Baseline Commit: 330adbc (`feat(core): accept WP-13 workflow gates`)
Latest FVS Checkpoint: 330adbc (`feat(core): accept WP-13 workflow gates`)
Current Planned Task: `POLYNEXUS-V1.1-CONSOLIDATION` — Governance/Contract/Documentation patch only; no Product Core changes
Active Writer: Codex — Human-authorized Governance v1.1 documentation patch; cannot independently accept its own work
Reviewer: Independent reviewer other than the current Writer/context; verdict required before Human checkpoint
Antigravity: `NOT_REQUIRED` for this documentation-only patch; no UI/browser/E2E surface

Architecture:
- ADR-001 through ADR-010 are CONFIRMED / FROZEN FOR V1 IMPLEMENTATION.

Development Environment:
- Windows development readiness: `ENVIRONMENT_BLOCKED` for current Python execution; both `.venv\Scripts\python.exe --version` and `C:\temp_pn_venv2\Scripts\python.exe --version` cannot create a process, actual exit code `1` each on 2026-08-25.
- Core pytest: historical WP-13 accepted-checkpoint evidence only — 374 passed, 1 skipped (375 collected); not rerun in the current governance session.
- Frontend Vitest: historical accepted-checkpoint evidence only — 78 passed (61 baseline + 17 WP-09D); not rerun in the current governance session.
- Frontend build: historical accepted-checkpoint evidence only; not rerun in the current governance session.
- Local Git backup: historical checkpoint transport; no current push or cross-machine readiness claim.

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

Governance v1.1 status:
- WP-13 checkpoint exists at `330adbc`; no WP-13 source/test changes are part of the current patch.
- Current Governance patch is uncommitted and not yet independently accepted.
- Local backup remains a local checkpoint transport; GitHub remote configuration, push and clean-clone verification are separate future Human Gates.
- `CROSS_MACHINE_CONTINUATION_READY` is not yet established.
- Human explicitly includes pre-existing D11 in the Governance checkpoint ownership/staged-allowlist decision; `docs/15_DOCUMENT_INDEX.md`, `docs/tasks/WP-12.md` and `services/core/src/polynexus_core/runtime/supervisor.py` remain excluded.
- ADR impact: ADR-001～010 unchanged. FULL ADR-011 / Run-owned immutable persisted Runtime Binding is approved for document integration and implementation planning only; the separate docs-worktree proposal remains `PROPOSED / NOT_IMPLEMENTED` until its own Architecture Gate. Attempt, RoutingEnvelope and trusted-human authentication remain deferred.
- Future runtime implementation requires a separately approved Alembic migration, legacy backfill/rollback coverage, OpenCode Writer and fresh independent Codex Reviewer; no product source/schema/migration change is authorized by this governance task.

OpenCode Model Routing:
1. Default: DeepSeek V4 Flash
2. If unavailable / policy-blocked: MiMo V2.5
3. If MiMo V2.5 repeatedly fails deterministic validation: MiMo V2.5 Pro
4. Architecture / security / lifecycle / hard root cause: escalate to Codex

## Latest Verification

WP-13 accepted-checkpoint verification (historical evidence for commit `330adbc`): 375 Core tests collected, 374 passed, 1 skipped, exit code 0; baseline and diff checks passed at acceptance. Browser DOM / Playwright E2E remains `UNVERIFIED/SKIPPED`; Windows symlink containment remains `UNVERIFIED/SKIPPED`; true concurrent HTTP duplicate-command execution remains `UNVERIFIED`.

- WP-13 targeted: 135 passed, exit code 0; pytest cleanup PermissionError is a non-fatal Windows warning.
- WP-12/WP-09 regression: 107 passed, exit code 0; pytest cleanup PermissionError is a non-fatal Windows warning.
- Full Core: 375 collected, 374 passed, 1 skipped, exit code 0; symlink test is `SKIPPED/UNVERIFIED` by Windows policy; pytest cleanup PermissionError is non-fatal.
- `scripts/validate_baseline.py`: PASS, exit code 0.
- `git diff --check`: PASS, exit code 0.
- Current governance-session environment preflight: both Python launchers failed to create a process, actual exit code `1` each; `scripts/validate_baseline.py` and product pytest were not executed and are `UNVERIFIED`, not current PASS.
- Current project progress remains **30/100 = 30%**; accepted FVS remains **22/22 = 100%**.
- ADR impact: D11 / Option C; no new model/table/migration/endpoint.
- Scope deviation: NONE; `docs/15_DOCUMENT_INDEX.md` remains pre-existing, unstaged, and excluded.

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
- Current gate: Governance v1.1 documentation patch -> independent reviewer other than the current Writer/context -> Human checkpoint approval. No stage, commit, push or remote operation is authorized.
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
