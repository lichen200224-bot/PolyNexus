> Current governance delta: REVIEW_PACKAGE_SKILL，local candidate/mandatory ZIP授權；產品HOLD，R2/TA-LR-01狀態不變。Follow [Goal](goals/REVIEW_PACKAGE_SKILL.md) and [canonical packaging skill](../.agents/skills/polynexus-review-package/SKILL.md). Exact post-commit delivery record accompanies ZIP; no push.

> 2026-09-10 Track A navigation override — CURRENT HANDOFF: TA-OPERATING-MODEL 文件交付，NEXT=INDEPENDENT_REVIEW_REQUIRED。Product HOLD；current authorized implementation NONE；R2只修Receipt C/R與TA-LR-01；NEXT_PROPOSED_GOAL=TA-LR-01，DEFINED_NOT_EXECUTED，LR接受後才F1。Writer Codex本輪文件scope，delivery後STOP。完整delta/tests/exit/limitations/changed-files見本輪review packet；以下保留歷史。
>
> Canonical: [Framework](governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) · [Current Goal](IMPLEMENTATION_CURRENT_GOAL.md) · [Legacy reconciliation](governance/POLYNEXUS_LEGACY_OPEN_WORK_RECONCILIATION.md) · [Current R2 review delta](reviews/TA-OPERATING-MODEL/NEED_FIX_R2.md)

# Current Handoff

## Current Task — INITIAL-REVIEW-DOCUMENT-REFRESH (2026-09-04)

**Status:** `DOCS_COMPLETE / WORD_OPEN_PASS / 15_PAGE_VISUAL_QA_PASS / HTML_BROWSER_PASS`

- `TASK_ID`: `INITIAL-REVIEW-DOCUMENT-REFRESH`
- `ATTEMPT`: `2`
- `OWNER`: `Codex`
- `WRITER`: `Codex` — initial-review DOCX and self-contained HTML evidence appendix
- `REVIEWER`: `Not separately assigned; deterministic structure checks plus Microsoft Word and Edge render QA executed in this turn`
- `ANTIGRAVITY_STATUS`: `NOT_REQUIRED` — no product UI/browser journey was changed; Edge loaded only the local evidence HTML
- `BRANCH`: `feature/first-vertical-slice`
- `GOAL`: replace the unreadable first attempt with a non-technical-reader proposal that explains product purpose, full scope, business flow, evidence meaning, test status, limitations, roadmap, Demo script, FAQ and useful supporting-attachment elements
- `CHANGED_FILES`: `initial-review-v2/PolyNexus_初審提案計畫書_v2.0.docx`; `initial-review-v2/PolyNexus_初審附件與證據說明_v2.0.html`; embedded diagram assets under `initial-review-v2/assets/`; `scripts/build_initial_review_v2.py`; `scripts/verify_initial_review_v2.py`; this current handoff block. The rejected `initial-review-v1/` artifacts remain present but are superseded and must not be submitted.
- `PRODUCT_SOURCE_CHANGES`: `NONE`
- `ADR_IMPACT`: `NONE`
- `SCOPE_DEVIATION`: `NONE`
- `DOCUMENT_CONTENT`: 15-page A4 proposal using restrained PM language for non-technical reviewers; includes plain-language positioning, a concrete release-review scenario, 7-step business flow, four-zone scope map, current functions, simplified architecture, Discuss/Review/Validate modes, five evidence types and hard-gate explanation, current test screen, measurement plan, risks, roadmap, Demo script, FAQ, glossary-style term table and attachment inventory
- `HTML_ATTACHMENT`: one self-contained UTF-8 HTML file with 12 sections and six embedded PNG diagrams; no external network, image folder or script dependency is required
- `TESTS_AND_EXIT_CODES`: `npm test -- --run` exit `0` (`1` test file and `78/78` tests passed); `scripts/build_initial_review_v2.py` exit `0`; `scripts/verify_initial_review_v2.py` exit `0`; Microsoft Word COM opened the DOCX and exported a `15`-page PDF; Edge headless loaded the HTML and wrote the preview image
- `DOCX_QA`: valid OOXML ZIP, required document XML, six embedded images, `117` paragraphs, `15` tables, Word-open/export PASS, 15 rendered PNG pages visually inspected after final table/page-number corrections with no clipping, overlap or unreadable text found
- `HTML_QA`: UTF-8 parse PASS, `12` sections, six data-URI embedded images, navigation anchors present, Edge local-file render PASS
- `VISUAL_QA`: `PASS`; final DOCX pages `1–15` and the HTML first viewport were inspected from current render artifacts under `review_work/v2-render/`
- `KNOWN_ISSUES`: product Browser E2E and Core full-suite verification are not claimed by this document task; the HTML test panel is a faithful visual re-creation of current command evidence, not a product UI screenshot; `review_work/` contains the isolated document runtime and QA artifacts; pre-existing dirty/untracked ownership remains unchanged
- `NEXT_ACTION`: Human reviews the two files under `initial-review-v2/` and uses only v2 for briefing/submission preparation; product UI journey screenshots can be added later only after Browser E2E evidence exists
- `NEXT_OWNER`: Human

### Do Not Change

Do not relabel the current document as complete V1, vendor-certified, Browser E2E verified, Local AI delivered, or measured for ROI. Do not absorb candidate-lane claims into the primary product state. Do not modify protected/foreign dirty paths, ADRs, runtime contracts, tests, migrations, lockfiles, or Git history as part of this document task.

## Current Task — G30 FINAL EXTERNAL VERIFICATION (2026-09-03)

**Status:** `NEED_ACTION / START_GATE_NEED_ACTION`

- `TASK_ID`: `G30-FINAL-EXTERNAL-VERIFICATION-AND-100-POINT-RECONCILIATION`
- `ATTEMPT`: 1
- `WRITER`: Codex (bounded evidence/handoff only)
- `REVIEWER`: Pending independent read-only review
- `ANTIGRAVITY_STATUS`: `REQUIRED` for live browser journey and failure paths
- `BRANCH`: `feature/g30-final-external-verification-and-reconciliation`
- `HANDOFF_DOC`: `docs/12_HANDOFF_CURRENT.md`
- `TASK_DOC`: `docs/tasks/G30-FINAL-EXTERNAL-VERIFICATION-AND-100-POINT-RECONCILIATION.md`
- `OUTPUT_REPORT`: `output/g30-final-external-verification/start-gate-report.md`
## Current Task — G19-G23 FIVE-GOAL EXECUTION ROUTING (2026-09-01)

**Status:** `ROUTED / G19_READY / G20_G23_GATED`

- `TASK_ID`: `G19-G23-FIVE-GOAL-EXECUTION-ROUTING`
- `ATTEMPT`: 1
- `WRITER`: Codex (routing/documentation only)
- `REVIEWER`: Not yet assigned; each implementation goal must satisfy its own
  independent-review requirements
- `ANTIGRAVITY_STATUS`: `G21_REQUIRED` for real-browser journey/failure-path
  evidence; not required for routing documentation
- `BASE_CHECKPOINT`:
  `backup/feature/first-vertical-slice@730912b5a3e19449c355975485f1fe77350a458a`
- `PRIMARY_PROTECTED_LANE`:
  `feature/first-vertical-slice@b87a0dc780e5d9a3bba083dbaf9552ca52508f9a`
  with mixed dirty tracked/untracked ownership
- `TASK_DOC`: `docs/tasks/G19-G23-FIVE-GOAL-EXECUTION-ROUTING.md`
- `CURRENT_TASK_CHANGED_PATHS`: new routing task doc; current blocks/rows in
  `docs/11_PROJECT_STATE.md`, `docs/12_HANDOFF_CURRENT.md`, and
  `docs/GOAL_COMPLETION_CONTROL_PANEL.md`; browser-readable status companion
  `docs/GOAL_COMPLETION_CONTROL_PANEL.html`. These files also contain
  pre-existing dirty ownership; G19 must import only the reviewed routing delta,
  not their entire primary-worktree versions.
- `GOALS`: G19 canonical workspace/provenance → G20 reproducible Web gate →
  G21 real-browser WP21 → G22 RC/cross-machine/delivery closeout → G23 final
  reconciliation and Human acceptance
- `AUTHORIZATION`: Codex may make bounded G19–G22 implementation, verification,
  exact-allowlist commit, and approved-backup fast-forward push decisions. Force
  push/history rewrite/destructive cleanup/remote reconfiguration/real user data,
  credentials or external submission/new architecture remain prohibited or
  require an exceptional Human decision.
- `PARALLELISM`: only read-only G22 pre-audit may overlap G20/G21. One active
  writer at a time; G23 waits for G19–G22 terminal repository evidence.
- `ADR_IMPACT`: none for this routing document; frozen ADR boundaries preserved.
- `SCOPE_DEVIATION`: none.
- `CURRENT_EVIDENCE`: routing is based on promoted exact SHA and fresh acceptance
  recorded in the state/provenance block below. No new product acceptance was
  run for this documentation-only task.
- `ROUTING_CHECKS`: `git diff --check` exit `0`; SOP governance validator exit
  `0`; deterministic task-doc structure check found five prompt headings, ten
  balanced fence markers, G19–G23 IDs, dispatch gate, and final-Human boundary.
  HTML control-panel structure/link check exit `0`: five Goal cards, all required
  state/SHA strings present, four local documentation targets present, progress
  value `30`, and G23 Human final gate present. Post-HTML `git diff --check` and
  SOP governance validator both exit `0`.
  Direct baseline-validator launch was unavailable this turn: `python` absent
  (exit `1`), `py -3` found no installed Python (exit `1`), and the historical
  temp venv launcher could not start (exit `1`). This is recorded as
  `UNVERIFIED_THIS_TURN`, not PASS; it does not replace the promoted exact-SHA
  baseline evidence below.
- `NEXT_ACTION`: open a new conversation with the complete G19 prompt from the
  task doc. G20–G23 conversations must remain gated by predecessor exact SHAs.
- `NEXT_OWNER`: Codex G19 conversation.
- `HUMAN_ACTION_REQUIRED`: none until the G23 final decision, unless a prompt's
  explicit exceptional stop boundary is reached.

### Do Not Change

Do not start five concurrent writers, work from the dirty primary lane, or treat
this routing decision as product acceptance. Do not self-accept G23.

## Current Task — STATE-PROVENANCE-RECONCILIATION (2026-09-01)

**Status:** `PROMOTED / CURRENT_EVIDENCE_PASS / HUMAN_CHECKPOINT_PENDING`

- `TASK_ID`: `STATE-PROVENANCE-RECONCILIATION`
- `WRITER`: Codex
- `REVIEWER`: Not applicable; read-only state/provenance sync
- `PRIMARY_BRANCH`: `feature/first-vertical-slice`
- `PRIMARY_HEAD`: `b87a0dc780e5d9a3bba083dbaf9552ca52508f9a`
- `PRIMARY_STATUS`: dirty; staged state empty; upstream
  `backup/feature/first-vertical-slice`
- `CANDIDATE_ROOT`: `C:\Users\hikar\.codex\visualizations\2026\08\30\01a058ba-4a09-75a1-b5ea-30b55cf91947\pn-g13-g14-acceptance-20260901`
- `CANDIDATE_HEAD`: `730912b5a3e19449c355975485f1fe77350a458a`
- `CANDIDATE_STATUS`: clean; branch ahead 22 of `origin/feature/first-vertical-slice`
- `CANDIDATE_ORIGIN`: local Temp repository, not an approved external remote
- `APPROVED_BACKUP_REF`: `backup/feature/first-vertical-slice@730912b5a3e19449c355975485f1fe77350a458a`
- `PROMOTION_RESULT`: candidate 22-commit range fast-forward pushed to approved
  backup; exit `0`
- `CLEAN_CLONE`: `C:\Users\hikar\.codex\visualizations\2026\09\01\01a05d1b-755c-7d60-abeb-6f2c8aa57967\clean-clone-promotion-20260901`
- `CLEAN_CLONE_RESULT`: exact HEAD `730912b5`, clean, required paths present

### Reconciled provenance

The candidate's current documents report G13–G18 complete, CP04 WP17–WP20
complete, CP04 WP21 deferred/unverified, CP05 complete, CP06 WP28–WP32
nonbrowser complete, and provisional RC acceptance with limitations. The 22
commits are now promotion-backed at the approved backup ref and verified in a
fresh clean clone. This still does not certify browser/vendor support; primary
formal progress remains 30/100 pending the required Human checkpoint acceptance.

### Checks performed

- Primary `git status --short --branch`, `git rev-parse HEAD`, and `git remote -v`:
  exit `0`.
- Candidate status, `HEAD`, `HEAD^`, remote identity, and ahead count:
  exit `0`; candidate clean and ahead 22 before promotion.
- Promotion push to approved backup: exit `0`; backup ref resolves to exact
  `730912b5a3e19449c355975485f1fe77350a458a`.
- Fresh clean-clone status, exact SHA, required paths, and `git diff --check`:
  exit `0`.
- Fresh clean-clone Core: 548 collected; 547 passed, 1 pre-existing Windows
  symlink-policy skip; exit `0`.
- Fresh clean-clone extension tests: 9 passed, exit `0`.
- Fresh clean-clone baseline and governance validators: exit `0`.
- Fresh clean-clone Web Vitest: `NEED_ACTION`, exit `1`; `vitest` is absent from
  the clean clone. Web bundling via `npx vite` also remained unavailable because
  npm attempted registry access and failed with `EACCES`; no dependency install
  was performed.

### Known issues and next exact step

- The primary workspace contains unrelated tracked and untracked ownership and
  must not be overwritten or silently folded into the candidate.
- The candidate's `origin` remains local Temp; approved promotion is recorded on
  the primary `backup` remote, not on that Temp origin.
- WP21 browser/vendor acceptance remains `DEFERRED / UNVERIFIED`; CP06/RC is
  provisional with limitations.
- The primary checkout remains dirty at `b87a0dc` and still has legacy raw
  `str(exc)` paths because it has not been merged; the promoted checkpoint has
  the G15 redaction work.
- Next: Human formal checkpoint acceptance of the promoted exact SHA, followed
  by any separately authorized primary merge/status sync.

### Do Not Change

Do not merge, rebase, reset, clean, stage, or amend either lane without a new
explicit authorization. Do not claim WP21/browser support, vendor support, or
final RC certification; the current result is promotion-backed provisional
acceptance with one deferred browser gate.

## Task
`G13-G14-RUNTIME-SAFETY-REACCEPTANCE` — Council binding, cancellation cleanup, and restart reconciliation acceptance

## Status
Current operational status: `G13_G14_ACCEPTED_CHECKPOINT / CURRENT_EVIDENCE_PASS / G15_SCOPE_AUDIT_PENDING`.

- `TASK_ID`: `G13-G14-RUNTIME-SAFETY-REACCEPTANCE`
- `ATTEMPT`: 1
- Branch: `feature/first-vertical-slice`
- Candidate HEAD: `16cbbb4889396a7bb7e87181ea006de7325d1fb7`
- Accepted commit: `16cbbb4889396a7bb7e87181ea006de7325d1fb7` (`feat(core): accept G13 G14 runtime safety gates`)
- Rollback ref: `382f2831aee39a8ed9330ff8062caae532fb8d26`
- Candidate root: `C:\Users\hikar\.codex\visualizations\2026\08\30\01a058ba-4a09-75a1-b5ea-30b55cf91947\pn-g13-g14-acceptance-20260901`
- Writer: inherited isolated candidate implementation; identity not recorded in candidate
- Active-writer status: `RELEASED`; `ACTIVE_WRITER`: `NONE`
- Reviewer: Codex read-only diff and deterministic acceptance review; candidate Git checkpoint completed under Human authorization
- Antigravity: `NOT_REQUIRED` — Core runtime task; no UI/browser/E2E journey changed
- Human routing decision: G13 Option A and formal G14 task creation authorized on 2026-09-01; exact candidate stage/commit authorized and completed
- Git authorization: exact seven-file stage/commit authorized; push, merge, rebase, reset, clean, ref, repository-configuration mutation, and primary code mutation remain unauthorized
- Next owner: Human for G15 exact-scope authorization after Codex read-only redaction audit

## G13/G14 current operational delta — 2026-09-01

- Canonical task docs: `docs/tasks/G13-COUNCIL-RUN-BINDING-SAFETY-GATE.md` and `docs/tasks/G14-RUNTIME-CANCELLATION-CLEANUP-GATE.md`.
- Candidate exact changed files: `services/core/src/polynexus_core/council/orchestrator.py`, `services/core/src/polynexus_core/execution_service.py`, `services/core/tests/test_wp12_council.py`, `services/core/src/polynexus_core/runtime/reconciliation.py`, `services/core/src/polynexus_core/persistence/repository.py`, `services/core/src/polynexus_core/app.py`, `services/core/tests/test_g14_runtime_reconciliation.py`.
- Focused G13/G14 on accepted commit: `74 passed`, exit `0`; combined G13/G14/runtime-binding: `293 passed`, exit `0`.
- Full Core: `505 passed / 1 skipped`, `506 collected`, exit `0`; the skip is Windows symlink containment policy and remains `UNVERIFIED`.
- Collect-only: `506 collected`, exit `0`; baseline validator exit `0`; governance validator exit `0`; exact seven-file scope exit `0`; staged-file check exit `0`; `git diff --check` exit `0`.
- External acceptance environment: `Python 3.13.14`, `pytest 9.0.2`, `PyYAML 6.0.3`; venv is outside the candidate and repository.
- Known environment warning: pytest reports a non-fatal Windows temporary-directory cleanup `PermissionError`; all required commands still returned exit `0`. Alembic/FastAPI deprecation warnings remain non-blocking.
- Candidate post-commit state: clean, staged-file count `0`, branch `feature/first-vertical-slice` is `ahead 1` of `origin/feature/first-vertical-slice`; no push performed.
- Architecture impact: `NONE`; no new schema migration, ADR, public API, runtime vendor branch, or production maturity claim.

## G15 read-only scope audit — current stop

- Known output-redaction gap: `services/core/src/polynexus_core/runtime/supervisor.py` still contains `reason=str(exc)` in the legacy `start()` and `execute_run()` exception paths; this is not included in the accepted G13/G14 seven-file checkpoint.
- API output surfaces directly serialize RunEvent reasons and RunResult summaries in `services/core/src/polynexus_core/api/runs.py` and `services/core/src/polynexus_core/api/run_outputs.py`; Evidence metadata and Artifact storage references also require one normalized redaction boundary review.
- G15 must first establish an exact allowlist and acceptance tests covering Supervisor, API, persistence/evidence, logging/export surfaces actually present in Core. No G15 implementation has started.

### G13/G14 Do Not Change

- Do not absorb primary-workspace dirty/untracked paths into the candidate; do not push, merge, rebase, reset, clean, alter refs, or modify repository configuration without a new explicit Human authorization.
- Do not claim real vendor/network/credential/production cleanup maturity from deterministic reference-adapter tests.
- Do not convert the Windows symlink skip or pytest cleanup warning into unqualified evidence.

## Previous phase: G03 closure (historical retained)

## Human scope decision recorded in the G03 delta

- G03 covers current homepage, official brief, current announcement, live form, initial-review deadline/fields/upload rules, Demo/benefit-table requirements, proposal/deck/package inventory, missing/readiness judgment, document QA, fresh independent review and Human final submission Gate.
- G03 excludes finals／複審, V1 product delivery, installer/release package, complete SOP, source distribution, deployment, formal product release and G04 project delivery.
- G04 is `G04-PROJECT-DELIVERY-PACKAGE / DEFERRED / DO_NOT_START`; it starts only after G17 hardening and an explicit Human request.
- After G03, the primary product route is G05; G03 approval never authorizes automatic login, upload or submission.
- Human waiver／submission decision on `2026-08-28`: independent reviewer conclusion is not required; Human decided to proceed with direct delivery and final submission today. This is a waiver of the review requirement, not proof that the live form or official conflicts were machine-verified.
- OpenCode routing is specified but not dispatched: only `G03-OC-01-INITIAL-REVIEW-PACKAGE-VALIDATION-PLAN` is safe to start now as `PLAN_ONLY / READ_ONLY`; implementation／assembly packages require a later explicit Human allowlist and isolated worktree.

## G03 closure and active-writer release

- `CLOSURE_RESULT`: `G03_COMPLETE_AFTER_HUMAN_SUBMISSION`
- `INITIAL_AGENT_CLOSURE_RESULT`: `CLOSED_AT_HUMAN_GATE`
- `CLOSURE_DATE`: `2026-08-28` (Asia/Taipei)
- `ACTIVE_WRITER_STATUS`: `RELEASED`
- `ACTIVE_WRITER`: `NONE`
- G03 agent-side initial-review evidence, readiness/package inventory, QA record, Human waiver record and bounded routing specification are complete for this task. No G03 writer remains active.
- `SUBMISSION_CONFIRMATION`: `HUMAN_CONFIRMED_SUBMITTED`
- `HUMAN_CONFIRMATION_DATE`: `2026-08-28` (current-session Human confirmation; exact time, receipt and response ID not retained)
- `HUMAN_GATE_REMAINING`: `NONE_FOR_G03`; this records the Human-reported submission outcome, not Agent post-login evidence, official acceptance, official-conflict resolution or reviewer PASS.
- `NEXT_OWNER`: `G05 Runtime Registry正式驗收`; any later G03 sync or adjustment requires a new explicit routing decision and writer assignment.
- `OPENCODE_DISPATCH`: `NONE`; documented OpenCode packages are not started automatically by this closure.

## Baseline and ownership retained

- G02 inherited SHA-256 baseline is preserved in `docs/tasks/G03-COMP-02-03-INITIAL-REVIEW-READINESS.md`; all seven G03-start hashes remain recorded. The six G02 source／artifact hashes are unchanged; the Handoff hash intentionally differs because only its current operational block carries the G03 delta.
- Existing `README.md`, `docs/31_PROJECT_CONTENT_MAP.md`, `docs/15_DOCUMENT_INDEX.md`, `docs/tasks/WP-12.md`, WP-14/runtime source/tests/task files, and expected-functions PPTX/MD/script remain pre-existing and outside G03 ownership.
- `output/playwright/` is the G03-owned browser-evidence path. Any token/cookie-bearing console artifact created during the Agent login redirect was removed and verified absent; no Agent account data was entered or retained.

## G03 current delta and changed files

- Added `docs/tasks/G03-COMP-02-03-INITIAL-REVIEW-READINESS.md`.
- Added `competition/G03_SUBMISSION_REQUIREMENTS_AND_CHECKLIST.md`.
- Updated only this current operational block in `docs/12_HANDOFF_CURRENT.md`; `## Legacy History — Reference Only` and all legacy content below it were not modified.
- G03 browser artifacts currently include the homepage/form screenshots, current downloaded official brief, and Playwright snapshot/log files under `output/playwright/.playwright-cli/`; exact paths and hashes are in the G03 task document.
- G03 OpenCode rules and complete package prompts are recorded in the G03 task document and reproduced in this current block; no OpenCode task has modified the shared tree.
- No Product Scope, ADR, runtime maturity, project progress, public API, product source, migration, lockfile, secret, CI/CD or deployment file was changed.

## Verification evidence and current boundary

- G03 start commands: `git status --short --branch`, `git rev-parse HEAD`, `git remote -v`, `git diff --name-status`, `git diff --cached --name-status`, `git ls-files --others --exclude-standard` all exit `0`; staged state was empty at start.
- Current homepage Playwright evidence: HTTP `200`, final URL unchanged, H1 `2026 Cyber4.0 AI創新競賽`, empty HTML title, `167140` bytes, SHA-256 `F1FDCA69B4B98A6DC3F9E8FF9D2A55A46D8D99EB69D68DBE6649172A9538CEC7`; visible current announcement has no date, homepage deliverables show Demo `5–10 分鐘` and separate `效益說明表`, and timeline image shows `2026/08/07 報名截止`.
- Current official brief Playwright evidence: HTTP `200`, DOCX, `43640` bytes, SHA-256 `EFBB80A1F8D86CD3E496DF633D80F7BB2B5B08A139F1477AD31E8D9509CD8A42`; OOXML extraction exit `0` confirms initial-review documents through `2026.08.31`, proposal/deck 20-page cap, Demo <=3 minutes or screenshots, Attachment 1 semantics and Attachment 2 format.
- Live form click exit `0` reached Microsoft organization login during the Agent read-only check; redacted final path `https://login.microsoftonline.com/organizations/oauth2/v2.0/authorize`, title `登入您的帳戶`, visible email/phone input and next control only. No Agent login, input, upload, send or submission occurred; Human later confirmed the actual submission.
- Official status remains `OFFICIAL_CONFLICT / HUMAN_PROCEED_RISK_ACCEPTED` for homepage timeline/deadline, Demo duration and benefit-table independence; live form file type/size/count/naming/required state remains `UNVERIFIED` because no post-login Agent evidence was captured.
- Proposal DOCX current precise OOXML/content audit exit `0`; canonical `render_docx.py` exit `1` with `No installed Python found!`; inherited G02 fallback 8-page visual QA remains tied to the unchanged hash and is not canonical renderer PASS. Candidate PPTX was not absorbed or QA-approved.
- Product tests: `SKIPPED` because G03 changed no product source; this is not a product PASS.

## Current stop and routing

`RESULT: G03_COMPLETE / HUMAN_CONFIRMED_SUBMITTED`
`GOAL_STATUS: GOAL_COMPLETE`
`ACTIVE_WRITER_STATUS: RELEASED`
`ACTIVE_WRITER: NONE`
`REVIEW_RESULT: HUMAN_WAIVED / NOT_REQUIRED_BY_HUMAN_WAIVER`
`SUBMISSION_DECISION: PROCEED_TODAY`
`SUBMISSION_STATUS: HUMAN_CONFIRMED_SUBMITTED`
`NEXT_OWNER: G05 Runtime Registry正式驗收`

Human has confirmed that the final submission was completed. This is a current-session Human-reported outcome; no account, token, response ID or receipt was retained, and it is not an Agent post-login verification or official acceptance. Known conflicts and live-form unknowns remain recorded as accepted risk, not verified facts. `APPROVE G03` never granted automatic submission permission.

`NEXT_PRIMARY_GOAL: G05 Runtime Registry正式驗收`

`PRIMARY_REASON: Human waived the independent reviewer conclusion and has now confirmed direct delivery/final submission; the product line routes directly to G05 rather than G04.`

`PRIMARY_DEPENDENCIES: G05 must use an isolated worktree and fresh deterministic runtime evidence; read Project State, this current block, runtime conformance task and WP-14/WP-15 scope first.`

### OPENCODE_ROUTING

- `OPENCODE_ROUTING_STATUS`: `SPEC_DEFINED / NOT_DISPATCHED`; this handoff does not itself start an OpenCode task.
- `OPENCODE_FIRST_DELEGABLE_GOAL`: `G03-OC-01-INITIAL-REVIEW-PACKAGE-VALIDATION-PLAN`
- `MODE`: `PLAN_ONLY / READ_ONLY`
- `SAFE_TO_START_NOW`: `YES`
- `REQUIRED_BRANCH_OR_WORKTREE`: new isolated worktree or read-only checkout; never the shared dirty working tree
- `OWNED_PATHS`: none; response-only plan and evidence references
- `DEPENDENCIES`: current G03 task/checklist/Handoff, retained browser artifacts, official brief artifact and current Human waiver
- `COLLISION_RISK`: low when read-only; no G03 doc or `output/playwright/` writes permitted
- `STOP_CONDITION`: stop at `NEED_ACTION` if inputs cannot be reproduced, login or post-login access is needed, or a Human decision is required
- Global OpenCode output alignment: a successful package must return `RESULT: READY_FOR_CODEX_ACCEPTANCE` or `READY_FOR_CODEX_REVIEW`, include `NEXT_PROMPT_FOR_CODEX`, and carry its G03 downstream state in `PACKAGE_STATUS`; this is technical routing, not a new independent G03 reviewer conclusion.

Conditional packages remain `SAFE_TO_START_NOW: NO` until their stated Human gate and explicit dispatch are supplied. The G03-OC-04 Human confirmation prerequisite is now satisfied, but no package is dispatched automatically:

- `G03-OC-02-OFFLINE-FINAL-ARTIFACT-QA`: `IMPLEMENT` only with `FINAL_ARTIFACT_ALLOWLIST`, `APPLICABLE_CONSTRAINTS` and `HANDOFF_CURRENT_BLOCK_ALLOWLIST`; new validator/report paths plus current-block-only Handoff update; target artifacts read-only; stop on guessed constraints, missing renderer/dependency or out-of-allowlist target.
- `G03-OC-03-INITIAL-REVIEW-PACKAGE-ASSEMBLY`: `IMPLEMENT` only with an exact selected-file allowlist, packaging constraints and `HANDOFF_CURRENT_BLOCK_ALLOWLIST`; staging only under `output/g03-initial-review-package/` plus current-block-only Handoff update; stop on missing artifact, unresolved form rule or release/installer request.
- `G03-OC-04-POST-SUBMISSION-HANDOFF-SYNC`: `IMPLEMENT` only after an explicit new routing decision and writer assignment; its non-sensitive Human submission-confirmation prerequisite is satisfied; current-block-only documentation update; never store account/token/response ID/personal data.
- `G03-OC-05-POST-SUBMISSION-ADJUSTMENT-PLAN`: `PLAN_ONLY / READ_ONLY` only after confirmed submission and a later-phase question; no product／ADR／scope／runtime writes and no G04.

All four conditional packages use a new isolated worktree, one-hop routing, explicit owned paths, no shared dirty-file writes, no login／upload／submit, no dependency installation, no product／runtime／release work, and no stage／commit／push. Any implementation package must update only the explicitly allowlisted Handoff current block; its complete self-contained prompt is under `### PARALLEL_SESSION_PROMPTS` below.

### PARALLEL_RECOMMENDATIONS:

- `G06-WP14-CODEX-ADAPTER-READONLY-REVIEW`: `READ_ONLY`, safe now `YES`, isolated worktree; review only WP-14 source/tests/task evidence, no shared runtime path edits, stop at independent `PASS`/`FAIL`/`NEED_ACTION` with actionable findings.
- `G07-WP15-OPENCODE-ADAPTER-READONLY-REVIEW`: `READ_ONLY`, safe now `YES`, isolated worktree; review only WP-15 source/tests/task evidence, no shared runtime path edits, stop at independent `PASS`/`FAIL`/`NEED_ACTION` with actionable findings.
- `G10-CROSS-CUTTING-ARCHITECTURE-REVIEW`: `PLAN_ONLY`／`READ_ONLY`, safe now `YES`, isolated worktree; proposal only until Human Architecture Gate, no implementation.

### NEXT_SESSION_PROMPT_PRIMARY:

> 你正在處理 PolyNexus 的獨立目標 `G05-RUNTIME-REGISTRY-FORMAL-ACCEPTANCE`。這是全新對話；repository、current command evidence 與實際檔案才是 source of truth，不得以 conversation history 或 AI memory 當專案事實。請在 isolated worktree 啟動，先讀取 `AGENTS.md`、`docs/11_PROJECT_STATE.md`、`docs/12_HANDOFF_CURRENT.md` current operational block、`docs/08_ACCEPTANCE_STRATEGY.md`、`docs/tasks/RUNTIME-ADAPTER-CONFORMANCE.md`、`docs/tasks/WP-14.md` 與直接相關 runtime source/tests。先唯讀執行 `git status --short --branch`、`git rev-parse HEAD`、`git diff --name-status`、`git diff --cached --name-status`，記錄 dirty/untracked ownership；不得吸收共享 working tree 變更。針對 Runtime Registry 正式驗收重跑必要 deterministic conformance／lifecycle／registry tests，記錄完整 command、actual exit code、failure isolation、capability/maturity 與 artifacts；Writer != Reviewer，fresh independent Reviewer 必須 diff-first 並檢查 protected paths。不得修改 `runtime/contracts.py`、`runtime/registry.py` 或 canonical governance documents；不得 stage、commit、push、reset、rebase、clean 或改 Git history。若證據不足、環境阻塞、WP-14/WP-15 scope 衝突或需要 Human decision，停在 `NEED_ACTION`／`HUMAN_DECISION`，不得把歷史結果轉成 PASS。最後輸出 `RESULT`、`GOAL_STATUS`、branch、HEAD、tests+exit codes、known limitations、unverified、review result、Human action、exact next action 與 rollback-safe handoff；G04 仍是 `DEFERRED / DO_NOT_START`。

### PARALLEL_SESSION_PROMPTS:

#### G06 prompt

> 你正在處理 PolyNexus 的獨立目標 `G06-WP14-CODEX-ADAPTER-READONLY-REVIEW`。這是全新對話；請使用 isolated worktree，先讀取 `AGENTS.md`、`docs/11_PROJECT_STATE.md`、`docs/12_HANDOFF_CURRENT.md` current block、`docs/08_ACCEPTANCE_STRATEGY.md`、`docs/tasks/RUNTIME-ADAPTER-CONFORMANCE.md` 與 `docs/tasks/WP-14.md`。唯讀盤點 branch、HEAD、dirty/untracked ownership，使用 diff-first 檢查 WP-14 Codex Adapter source/tests/task evidence、lifecycle normalization、cancel/timeout cleanup、error/evidence/maturity truthfulness、registry compatibility 與 protected paths。可重跑必要 deterministic checks，但不得修改任何檔案，尤其不得修改或吸收 `runtime/contracts.py`、`runtime/registry.py`、其他 agent dirty paths、Product Scope、ADR 或 governance documents；不得 stage、commit、push、reset、rebase、clean。Writer != Reviewer；輸出 fresh independent `PASS`／`FAIL`／`NEED_ACTION`，FAIL/NEED_ACTION 必須列 severity、file/line、evidence、impact、FIX_PROMPT、測試命令與預期 exit code。遇到 scope 或 Human gate 衝突停下並標示 `HUMAN_DECISION`。

#### G07 prompt

> 你正在處理 PolyNexus 的獨立目標 `G07-WP15-OPENCODE-ADAPTER-READONLY-REVIEW`。這是全新對話；請使用 isolated worktree，先讀取 `AGENTS.md`、`docs/11_PROJECT_STATE.md`、`docs/12_HANDOFF_CURRENT.md` current block、`docs/08_ACCEPTANCE_STRATEGY.md`、`docs/tasks/RUNTIME-ADAPTER-CONFORMANCE.md` 與 `docs/tasks/WP-15.md`。唯讀盤點 branch、HEAD、dirty/untracked ownership，diff-first 審查 WP-15 OpenCode Adapter source/tests/task evidence、lifecycle normalization、cancel/timeout cleanup、error/evidence/maturity truthfulness、registry compatibility 與 protected paths。可重跑必要 deterministic checks，但不得修改或吸收任何 dirty path，尤其不得修改 `runtime/contracts.py`、`runtime/registry.py`、Product Scope、ADR 或 governance documents；不得 stage、commit、push、reset、rebase、clean。Writer != Reviewer；輸出 fresh independent `PASS`／`FAIL`／`NEED_ACTION`，FAIL/NEED_ACTION 必須列 severity、file/line、evidence、impact、FIX_PROMPT、測試命令與預期 exit code。遇到 scope 或 Human gate 衝突停下並標示 `HUMAN_DECISION`。

#### G10 prompt

> 你正在處理 PolyNexus 的獨立目標 `G10-CROSS-CUTTING-ARCHITECTURE-REVIEW`。只能在 `PLAN_ONLY`／`READ_ONLY` 模式與 isolated worktree 工作。先讀取 `AGENTS.md`、`docs/00_SCOPE_BASELINE.md`、`docs/10_DECISION_LOG.md`、`docs/18_ARCHITECTURE_DECISIONS.md`、`docs/11_PROJECT_STATE.md`、`docs/12_HANDOFF_CURRENT.md` current block，以及直接相關 task/source。盤點跨切面 architecture／contract／scope risks，指出是否需要新的 ADR、Human Architecture Gate、migration／rollback 或 separate implementation task；不得實作，不得修改 Product Scope、ADR、runtime source、tests、governance documents 或 Git history，不得 stage、commit、push、reset、rebase、clean。每個提案必須說明 evidence、impact、alternatives、rollback、Human decision question 與 stop condition；未經 Human Architecture Gate 不得把 proposal 當成授權或 PASS。最後交付 bounded plan／`NEED_ACTION`／`HUMAN_DECISION` handoff。

#### G03-OC-01 prompt — safe now

> 你是 PolyNexus 的 OpenCode bounded planner，處理 `G03-OC-01-INITIAL-REVIEW-PACKAGE-VALIDATION-PLAN`。這是全新對話；repository、目前檔案與本提示詞才是 source of truth，不得以 conversation history 或 AI memory 當專案事實。請使用新的 isolated worktree 或 read-only checkout，禁止使用共享 dirty working tree。先讀取 `AGENTS.md`、`docs/11_PROJECT_STATE.md`、`docs/12_HANDOFF_CURRENT.md` current operational block、`docs/tasks/G03-COMP-02-03-INITIAL-REVIEW-READINESS.md`、`competition/G03_SUBMISSION_REQUIREMENTS_AND_CHECKLIST.md`、`docs/05_GIT_WORKFLOW.md`、`docs/06_AI_TOOL_COLLABORATION.md` 與 `docs/governance/sop-v1.1/OUTPUT_CONTRACT.md`。只讀檢查現有 G03 browser artifacts、官方 brief artifact、proposal／deck／Demo／benefit package inventory 與已記錄的 Human waiver；不要重新登入、不要輸入資料、不要讀取或繞過 Microsoft login wall、不要上傳或送出，也不要重新執行已完成的官方查證。不得修改任何檔案，尤其不得修改 G03 docs、G02 inherited files、proposal DOCX、pre-existing expected-functions PPTX／MD／script、Product Scope、ADR、runtime、tests、migrations、lockfiles、secrets、CI/CD 或 deployment。產出一份 response-only offline validation plan：逐項列出 final artifact allowlist 所需欄位、local hash／存在性／副檔名／大小／頁數／影片時長可驗證項目、哪些 constraint 必須由 Human 提供、目前 missing／unknown／conflict、執行順序與 stop conditions；不得裁決 deadline、Demo duration、benefit-table mapping 或 required/optional。最後依 output contract 回覆 `RESULT: READY_FOR_CODEX_ACCEPTANCE` 或 `NEED_ACTION`、`PACKAGE_STATUS: READY_FOR_NEXT_PHASE`、`TASK_ID`、`STATE`、`MODIFIED_FILES: NONE`、每個 command 與 actual exit code、evidence／limitations、`ADR_IMPACT: NONE`、`SCOPE_DEVIATION: NONE`、`PROTECTED_AREAS_CHECK`、`NEXT_OWNER: Codex`、`NEXT_ACTION: CODEX_ACCEPTANCE`、`NEXT_PROMPT_FOR_CODEX` 與完整 `NEXT_PROMPT`。不要求獨立 reviewer 結論，但也不得把 plan 或 Human waiver 寫成 G03 PASS／SUBMITTED。

> Authoritative output addendum for G03-OC-01: follow the global `docs/governance/sop-v1.1/OUTPUT_CONTRACT.md`; on success use `RESULT: READY_FOR_CODEX_ACCEPTANCE` (or `READY_FOR_CODEX_REVIEW`), set `PACKAGE_STATUS: READY_FOR_NEXT_PHASE`, include `NEXT_PROMPT_FOR_CODEX`, and keep `NEED_ACTION` for missing conditions. This technical handoff state is not an independent G03 reviewer conclusion and never authorizes Human submission.

#### G03-OC-02 prompt — conditional implementation

> 你是 PolyNexus 的 OpenCode Writer，處理 `G03-OC-02-OFFLINE-FINAL-ARTIFACT-QA`。只有在本提示詞之後附有 Human 明確批准的 `FINAL_ARTIFACT_ALLOWLIST` 與 `APPLICABLE_CONSTRAINTS` 時才可 IMPLEMENT；若缺少任一項，立即回覆 `NEED_ACTION`，不要猜測、不要建立檔案。請使用新的 isolated worktree，不得使用共享 dirty working tree。先讀取 `AGENTS.md`、`docs/11_PROJECT_STATE.md`、`docs/12_HANDOFF_CURRENT.md` current block、`docs/tasks/G03-COMP-02-03-INITIAL-REVIEW-READINESS.md`、`competition/G03_SUBMISSION_REQUIREMENTS_AND_CHECKLIST.md`、`docs/05_GIT_WORKFLOW.md`、`docs/06_AI_TOOL_COLLABORATION.md` 與 `docs/governance/sop-v1.1/OUTPUT_CONTRACT.md`；若觸碰 DOCX/PPTX，依適用的 documents／Presentations skill 做 structural and visual QA。允許只新增明確 allowlisted validator/report paths，例如 `scripts/g03_validate_initial_review_package.ps1` 與 `output/g03-opencode/`；target artifacts 預設 read-only，不得修改 inherited proposal DOCX 或 pre-existing unowned PPTX。只做 offline deterministic checks：存在性、SHA-256、副檔名、Human 提供的 file size／page／time limits、OOXML／PDF／PPTX 結構與可用的 local media metadata；沒有 constraint 就輸出 `UNKNOWN`，不可推定 live form 規則。不得登入、輸入個資、存取或繞過 Microsoft Form、上傳、送出、安裝新 dependency、修改產品／ADR／runtime／migration／deployment 或 Git。每個 check 回報 actual command、exit code、artifact path、hash、PASS／FAIL／UNKNOWN；local PASS 不代表官方合規或已送件。完成後回覆完整 contract：`RESULT: READY_FOR_HUMAN_SUBMISSION | NEED_ACTION`、`STATE`、`TASK_ID`、`ATTEMPT`、`WRITER: OpenCode`、`REVIEWER: HUMAN_WAIVED_BY_CURRENT_DECISION | NOT_APPLICABLE`、`TASK_DOC`、`HANDOFF_DOC`、完整 `MODIFIED_FILES`（含 untracked）、`IMPLEMENTATION_SUMMARY`、`TESTS_AND_EXIT_CODES`、`DETERMINISTIC_EVIDENCE`、`KNOWN_ISSUES`、`ADR_IMPACT: NONE`、`SCOPE_DEVIATION: NONE`、`PROTECTED_AREAS_CHECK`、`NEXT_OWNER: Human`、`NEXT_ACTION` 與完整 `NEXT_PROMPT`。不要 stage、commit、push，也不要要求獨立 reviewer 結論。

> Authoritative output addendum for G03-OC-02: `IMPLEMENT` also requires an explicit `HANDOFF_CURRENT_BLOCK_ALLOWLIST`; only the current operational block may be updated, never Handoff legacy history. On success use `RESULT: READY_FOR_CODEX_ACCEPTANCE` (or `READY_FOR_CODEX_REVIEW`), `PACKAGE_STATUS: READY_FOR_HUMAN_SUBMISSION`, `NEXT_PROMPT_FOR_CODEX` and `NEXT_ACTION: CODEX_ACCEPTANCE`; missing allowlists remain `NEED_ACTION`. This is technical package routing, not an independent G03 reviewer conclusion or Human submission authorization.

#### G03-OC-03 prompt — conditional package assembly

> 你是 PolyNexus 的 OpenCode Writer，處理 `G03-OC-03-INITIAL-REVIEW-PACKAGE-ASSEMBLY`。只有在 Human 明確提供並批准 proposal／deck／Demo／benefit 等每一個輸入檔案的 exact path、SHA-256 或版本、可接受格式／大小／頁數／時長／命名限制，以及 `FILES_TO_STAGE_FOR_HUMAN_SUBMISSION` 後才可開始；任何缺漏都回覆 `NEED_ACTION`，不得建立 staging。使用新的 isolated worktree／staging directory，不得使用共享 dirty working tree。只允許在 `output/g03-initial-review-package/` 建立初審 staging manifest 與 selected-file copies；不可覆寫 source、不可吸收 pre-existing candidate PPTX、不可創作缺少的 Demo／benefit artifact、不可建立 installer／release package／source distribution／deployment bundle。不要把未知 live-form 規則改寫成 verified；manifest 必須逐檔記錄 source path、SHA-256、size、format、Human-provided constraint、local result 與 unknowns，不得包含帳號、token、cookie、個資或表單 response ID。不得登入、填表、上傳、送出、改 G03 inherited files、Product Scope、ADR、runtime、tests、migration、lockfile、secret、CI/CD 或 deployment；不得 stage、commit、push。完成後回覆完整 contract：`RESULT: READY_FOR_HUMAN_SUBMISSION | NEED_ACTION`、`STATE`、`TASK_ID`、`ATTEMPT`、`WRITER: OpenCode`、`REVIEWER: HUMAN_WAIVED_BY_CURRENT_DECISION | NOT_APPLICABLE`、`TASK_DOC`、`HANDOFF_DOC`、完整 changed/untracked files、manifest path、每個 local command／actual exit code、`DETERMINISTIC_EVIDENCE`、`KNOWN_ISSUES`、`ADR_IMPACT: NONE`、`SCOPE_DEVIATION: NONE`、`PROTECTED_AREAS_CHECK`、`NEXT_OWNER: Human`、`NEXT_ACTION` 與完整 Human final submission prompt；不得宣稱 submission 已完成。

> Authoritative output addendum for G03-OC-03: `IMPLEMENT` requires `HANDOFF_CURRENT_BLOCK_ALLOWLIST` in addition to the selected-file and packaging allowlists; update only the current operational block, never Handoff legacy history. On success use `RESULT: READY_FOR_CODEX_ACCEPTANCE` (or `READY_FOR_CODEX_REVIEW`), `PACKAGE_STATUS: READY_FOR_HUMAN_SUBMISSION`, `NEXT_PROMPT_FOR_CODEX` and `NEXT_ACTION: CODEX_ACCEPTANCE`; missing inputs remain `NEED_ACTION`. Do not treat staging as submission.

#### G03-OC-04 prompt — post-submission sync

> 你是 PolyNexus 的 OpenCode Writer，處理 `G03-OC-04-POST-SUBMISSION-HANDOFF-SYNC`。只有在 Human 提供明確且非敏感的 `SUBMISSION_CONFIRMATION`（submitted／not submitted、日期時間、是否有官方錯誤；不得提供帳號、token、cookie、response ID 或個資）後才可開始；沒有 confirmation 立即回覆 `NEED_ACTION`。使用新的 isolated worktree，依 explicit allowlist 只更新 G03 task、submission checklist 與 `docs/12_HANDOFF_CURRENT.md` 的 current operational block；不得修改 `## Legacy History — Reference Only` 以下內容，不得修改 Project State、Product Scope、ADR、runtime、tests、migrations、lockfiles、secrets、CI/CD、deployment 或任何 pre-existing dirty/untracked ownership。把 Human confirmation 與 evidence path 如實記錄；若沒有可保存的 artifact，只記錄 `HUMAN_CONFIRMED` 與日期，不自行創造 receipt。不得把 waiver 當成 reviewer PASS，不得把 local package check 當成 official acceptance，不得登入、上傳或送出。完成後回覆完整 contract：`RESULT: READY_FOR_NEXT_PHASE | NEED_ACTION`、`STATE`、`TASK_ID`、`ATTEMPT`、`WRITER: OpenCode`、`REVIEWER: HUMAN_WAIVED_BY_CURRENT_DECISION | NOT_APPLICABLE`、`TASK_DOC`、`HANDOFF_DOC`、完整 `MODIFIED_FILES`、`IMPLEMENTATION_SUMMARY`、actual checks／exit codes、legacy-tail verification、`DETERMINISTIC_EVIDENCE`、`KNOWN_ISSUES`、`ADR_IMPACT: NONE`、`SCOPE_DEVIATION: NONE`、`PROTECTED_AREAS_CHECK`、`NEXT_OWNER: Codex | Human`、`NEXT_ACTION` 與完整 `NEXT_PROMPT`；不要 stage、commit、push。

> Authoritative output addendum for G03-OC-04: after the non-sensitive Human confirmation, update only the explicitly allowlisted current operational block and leave legacy history untouched. On success use `RESULT: READY_FOR_CODEX_ACCEPTANCE` (or `READY_FOR_CODEX_REVIEW`), `PACKAGE_STATUS: READY_FOR_NEXT_PHASE`, `NEXT_PROMPT_FOR_CODEX` and `NEXT_ACTION: CODEX_ACCEPTANCE`; this does not create a reviewer conclusion or submit anything.

#### G03-OC-05 prompt — later adjustment plan

> 你是 PolyNexus 的 OpenCode bounded planner，處理 `G03-OC-05-POST-SUBMISSION-ADJUSTMENT-PLAN`。此工作只能在 Human 已確認今日 G03 submission outcome 且主產品線進入後續階段後啟動；現在不可自行開始。使用新的 isolated worktree、`PLAN_ONLY / READ_ONLY`，先讀取 `AGENTS.md`、`docs/11_PROJECT_STATE.md`、`docs/12_HANDOFF_CURRENT.md` current block、G03 task、相關 current source of truth 與 Human-provided post-submission questions。只提出 bounded adjustment options、evidence gap、risk、alternative、rollback、需要的 Human Architecture／Scope／Git Gate 與下一步；不得修改產品、Product Scope、ADR、runtime、migration、deployment、G03 legacy history 或任何 dirty ownership，不得把 proposal 當成 implementation authorization，不得啟動 G04。依完整 contract 回覆 `RESULT: READY_FOR_NEXT_PHASE | NEED_ACTION`、`STATE`、`TASK_ID`、`ATTEMPT`、`WRITER: OpenCode`、`REVIEWER: NOT_APPLICABLE`、`TASK_DOC`、`HANDOFF_DOC`、`MODIFIED_FILES: NONE`、`IMPLEMENTATION_SUMMARY`、actual read-only commands／exit codes、`DETERMINISTIC_EVIDENCE`、`KNOWN_ISSUES`、`ADR_IMPACT: NONE`、`SCOPE_DEVIATION: NONE`、`PROTECTED_AREAS_CHECK`、Human decision questions、`NEXT_OWNER`、`NEXT_ACTION` 與完整 `NEXT_PROMPT`。

> Authoritative output addendum for G03-OC-05: keep `PLAN_ONLY / READ_ONLY` and `MODIFIED_FILES: NONE`. On success use `RESULT: READY_FOR_CODEX_ACCEPTANCE` (or `READY_FOR_CODEX_REVIEW`), `PACKAGE_STATUS: READY_FOR_NEXT_PHASE`, `NEXT_PROMPT_FOR_CODEX` and `NEXT_ACTION: CODEX_ACCEPTANCE`; do not implement an adjustment or start G04.

### DO_NOT_START:

- `G04-PROJECT-DELIVERY-PACKAGE` — `DEFERRED / DO_NOT_START` until G17 hardening is complete and Human explicitly requests formal project delivery.

## Active Writer
`NONE` — G03 is closed at the Human Gate and active-writer ownership is released. Any later G03 work requires a new explicit routing decision and writer assignment.

## Reviewer
Independent reviewer conclusion is waived by Human for today's submission decision. The prior two fresh tasks had no reviewer output; this is recorded as `HUMAN_WAIVED / NOT_REQUIRED_BY_HUMAN_WAIVER`, not as a PASS.

## Antigravity
`NOT_REQUIRED` — official public-source/browser verification was performed by Codex Playwright; no product UI/E2E surface changed.

## Do Not Change

- Do not modify `docs/15_DOCUMENT_INDEX.md`, `docs/tasks/WP-12.md`, WP-14/WP-16/runtime source/tests/task files, expected-functions PPTX/MD/script, Product Scope, ADRs, runtime maturity, project progress, product source, migrations, lockfiles, secrets, CI/CD or deployment configuration.
- Do not stage, commit, push, merge, cherry-pick, reset, rebase, clean, delete or rewrite Git history.
- Do not log in, enter personal data, upload, send or submit the competition form from Agent context; Human must perform the final confirmation.
- Do not start G04 before G17 hardening and explicit Human routing.

## Handoff Retention Rule

The sections above are the only session-bootstrap operational state. `Handoff != Archive` and `Handoff != Complete Project History`. Historical material below is retained temporarily as reference-only legacy content; it must not be loaded by default or treated as current status. Future handoffs replace the operational block above with current state + current delta + next routing instead of appending another complete history.

## Legacy History — Reference Only

## WP-13 Attempt 7 (superseded by Attempt 9) - 2026-08-21

- TASK_ID: WP-13
- ATTEMPT: 7
- STATUS: READY_FOR_CODEX_REVIEW
- DECISION: D11 / Option C
- BRANCH: feature/first-vertical-slice
- WRITER: OpenCode
- REVIEWER: Codex
- ANTIGRAVITY_STATUS: NOT_REQUIRED
- NEXT_OWNER: Codex -> Human
- TASK_DOC: `docs/tasks/WP-13.md`
- HANDOFF_DOC: `docs/12_HANDOFF_CURRENT.md`
- APPROVED_FOR_COMMIT: NO

### Attempt 7 implementation

- Workflow identity: `evaluate_workflow_gates()` validates `run.workflow_version == workflow.version` (was missing).
- Terminal report durable reload: `_validate_evaluation_structure()` skips validation when evaluations are empty (terminal runs produce `evaluations=()`).
- Persist idempotency: `persist_gate_report()` detects corrupted source/type/identity/malformed workflow_version and fails closed with `GateReportTamperedError`.
- Evidence boundary: `extra_evidence` injection parameter removed from `RunSupervisor.execute_claimed_run()`, `_build_execution_from_existing()`, and `_build_execution()`.
- 9 new regression tests (83 total, up from 74).
- Full Core 312 passed, 1 skipped, 313 collected.

## WP-13 Attempt 9 READY_FOR_CODEX_REVIEW - 2026-08-24

- TASK_ID: WP-13
- ATTEMPT: 9
- STATUS: READY_FOR_CODEX_REVIEW
- DECISION: D11 / Option C
- BRANCH: feature/first-vertical-slice
- WRITER: OpenCode
- REVIEWER: Codex
- ANTIGRAVITY_STATUS: NOT_REQUIRED
- NEXT_OWNER: Codex -> Human
- TASK_DOC: `docs/tasks/WP-13.md`
- HANDOFF_DOC: `docs/12_HANDOFF_CURRENT.md`
- APPROVED_FOR_COMMIT: NO

### Attempt 9 Implementation

- D11 Option C: approve and reject HUMAN_EVIDENCE remain `HUMAN_DECISION` / `NEED_ACTION` for every actor value; neither can produce PASS/VERIFIED or deterministic FAIL.
- Reload validates `actor_id` as canonical `system:workflow-gate`; actor tamper raises `GateReportTamperedError`.
- Row-level `task_id`/`run_id` tamper detected via Phase 1 scoped lookup with run-level disambiguation and Phase 2 durable-binding metadata scan. Combined multi-field tamper detected via independent dual-hash provenance (`identity_hash` covers workflow/task/run; `provenance_token` covers actor/source/task/run). Single-field and partial multi-field tamper are fail-closed within the PARTIAL_INTEGRITY threat model; full-consistent 8-field rewrite (including both hashes) is NOT detectable and is an accepted limitation per Human Option B.
- Combined-tamper replay: canonical actor/source are independent markers; if both are damaged, a cross-family workflow-identity/report-payload metadata fingerprint still detects the candidate. Multiple candidates, malformed identity, and corrupted source/type fail closed without duplicates.
- Terminal FAILED/TIMED_OUT/CANCELLED/ORPHANED reports persist and reload with `FAIL`, `authority=none`, and empty evaluations.
- `run.workflow_version == workflow.version` validation added; unused supervisor evidence injection remains absent.

### Attempt 9 Changed Files (actual current Git status)

Modified:
- `docs/10_DECISION_LOG.md` (pre-existing D11 decision)
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- `docs/15_DOCUMENT_INDEX.md` (pre-existing dirty state; excluded and not modified by Attempt 8)
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`
- `docs/tasks/WP-12.md` (pre-existing)
- `services/core/src/polynexus_core/execution_service.py` (pre-existing WP-13 execution integration)
- `services/core/src/polynexus_core/persistence/repository.py` (pre-existing WP-13 update boundary)
- `services/core/src/polynexus_core/runtime/supervisor.py` (pre-existing; unused injection removed in Attempt 7)
- `services/core/src/polynexus_core/workflows/models.py` (pre-existing)
- `services/core/tests/test_wp07_integration.py` (pre-existing WP-13 parity integration adjustment)
- `services/core/tests/test_wp09_query_api.py` (pre-existing WP-13 exact parity adjustment)

Untracked:
- `docs/tasks/WP-13.md`
- `services/core/src/polynexus_core/workflows/gates.py`
- `services/core/tests/test_wp13_workflow_gates.py`
- `workflows/builtin/verified-gate.yaml`

Protected/excluded:
- `docs/15_DOCUMENT_INDEX.md` is pre-existing and excluded; no modification permitted.

### Attempt 9 Protected Areas / ADR / Scope

- Protected: ADR-001-010, D01-D10, D11 decision, Run lifecycle/transitions, WP-08A/B, WP-09B/C/D, WP-10, WP-11, WP-12, migrations, frontend, secrets, and accepted API contracts.
- ADR impact: D11 / Option C only; no new model/table/migration/endpoint/auth subsystem/evidence ledger.
- Scope deviation: NONE.
- Known limitations: Windows pytest cleanup PermissionError is a non-fatal post-test environment warning; no production/vendor runtime is certified; CP-03 point allocation remains deferred.
- UNVERIFIED / SKIPPED: Browser DOM / Playwright E2E `UNVERIFIED/SKIPPED`; Windows symlink containment `UNVERIFIED/SKIPPED`; true concurrent HTTP duplicate-command execution `UNVERIFIED`.

### Attempt 9 Verification (actual commands)

- `C:\temp_pn_venv2\Scripts\python.exe -m pytest -q services\core\tests\test_wp13_workflow_gates.py` -> 135 passed; exit code `0`.
- `C:\temp_pn_venv2\Scripts\python.exe -m pytest -q services\core\tests\test_wp12_council.py services\core\tests\test_wp09_execution_api.py services\core\tests\test_wp09_query_api.py` -> 107 passed; exit code `0`.
- `C:\temp_pn_venv2\Scripts\python.exe -m pytest --collect-only --disable-warnings services\core` -> 375 collected; exit code `0`.
- `C:\temp_pn_venv2\Scripts\python.exe -m pytest -q --disable-warnings services\core` -> 374 passed, 1 skipped; exit code `0`.
- `C:\temp_pn_venv2\Scripts\python.exe scripts\validate_baseline.py` -> PASS; exit code `0`.
- `git diff --check` -> PASS; exit code `0`.
- `git status --short --branch` -> exit code `0`; worktree dirty with ledger above.
- Pytest cleanup `PermissionError` appeared and is non-fatal; symlink test is `SKIPPED/UNVERIFIED` by Windows policy.

## Active Writer
OpenCode — WP-13 Attempt 9 implementation complete; actor_id, bound_task_id, bound_run_id, identity_hash, provenance_token validated in reload and persist with fail-closed; Phase 1 scoped lookup with run-level disambiguation + Phase 2 durable-binding metadata scan; independent dual-hash provenance (identity_hash covers workflow_id/workflow_version/task_id/run_id, provenance_token covers actor_id/source/task_id/run_id); single-field and partial multi-field tamper fail closed within PARTIAL_INTEGRITY; full-consistent 8-field rewrite including both hashes is NOT detectable per Human Option B; D12 deferred to CP-04+; same-task multi-run isolation verified; cross-task isolation verified (corrupted Task A does not block legitimate Task B); 375 current Core tests collected / 374 passed / 1 skipped.

## Reviewer
Codex — WP-13 independent Core/contract review; Human acceptance required.

## Antigravity
`NOT_REQUIRED` — WP-13 is a Core workflow/evidence contract task; Browser DOM / Playwright E2E remains `UNVERIFIED/SKIPPED`.

## WP-13 Attempt 3 (historical; superseded by Attempt 4) — 2026-08-21

- TASK_ID: WP-13
- ATTEMPT: 3
- STATUS: READY_FOR_CODEX_REVIEW
- BRANCH: feature/first-vertical-slice
- WRITER: OpenCode
- REVIEWER: Codex
- ANTIGRAVITY_STATUS: NOT_REQUIRED
- NEXT_OWNER: Codex -> Human
- TASK_DOC: `docs/tasks/WP-13.md`
- HANDOFF_DOC: `docs/12_HANDOFF_CURRENT.md`

### Completed acceptance carried into this handoff

- WP-12 Attempt 8: Codex PASS and Human acceptance recorded on 2026-08-21.
- Evidence carried from the accepted review: WP-12 `45 passed`; full Core `238 collected / 237 passed / 1 skipped`; baseline validation PASS; `git diff --check` PASS.
- Git: `d6823d6` was committed from the exact WP-12 allowlist and pushed to `backup/feature/first-vertical-slice`.
- Project progress remains `30/100`; FVS remains `22/22`; CP-03 point allocation is deferred until CP-03 completion per Human decision.

### WP-13 Attempt 3 goal and scope

- Remediates Codex FAIL findings on Attempt 2.
- Gate evaluation wired into ExecutionService.execute_existing_run() for COMPLETED runs (post-execution evaluation layer).
- persist_gate_report updates existing evidence in place; never returns stale PASS verdict.
- reload_gate_report re-validates stored evaluations against verdict; fails closed on tamper (GateReportTamperedError).
- Unverified actor prefixes (agent:, tool:, test:, system:) rejected for HUMAN_GATE approval.
- TOOL_EVIDENCE command must be non-empty, non-whitespace string; exit_code must be '0'.
- run.task_id == task.id validated before evaluation.
- 13 new regression tests added (54 total, up from 41).
- Integration test through actual ExecutionService.execute_existing_run() path.
- WP-09C test assertions updated to account for additive gate evaluation evidence.
- ADR-007 Run lifecycle unchanged; gate evaluation is additive post-execution layer.
- Current source facts and the verdict mapping are recorded in `docs/tasks/WP-13.md`.

### Changed files for Attempt 3

- Modified: `services/core/src/polynexus_core/workflows/gates.py`, `services/core/tests/test_wp13_workflow_gates.py`, `services/core/src/polynexus_core/execution_service.py`, `services/core/tests/test_wp09_query_api.py`, `docs/11_PROJECT_STATE.md`, `docs/12_HANDOFF_CURRENT.md`, `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`, `docs/tasks/WP-13.md`.
- New: `workflows/builtin/verified-gate.yaml` (pre-existing from Attempt 1).
- Pre-existing and excluded: `docs/15_DOCUMENT_INDEX.md`.
- Product source (API contracts, persistence schema, frontend, migrations, dependencies, ADR): unchanged by Attempt 3.

### ADR / scope / protected areas (Attempt 3)

- ADR impact: `NONE`. Gate evaluation is an additive post-execution layer over existing Evidence boundaries; no new model/table/migration/endpoint/RunState/WorkMode/EvidenceType.
- ADR-007 Run lifecycle unchanged; gate evaluation does not alter Run state or lifecycle events.
- WP-09C test assertions updated to account for additive DOCUMENT_EVIDENCE gate report; contract behavior unchanged.
- WP-12, WP-11, WP-09B/C/D, WP-08A/B, Run lifecycle, WorkMode, migrations, frontend, secrets, and accepted API contracts remain protected.
- WP-13 does not add a new Decision/Verdict persistence contract or public API field.

### Current verification for this transition

- `git diff --check` -> PASS, exit code `0`.
- `git status --short --branch` -> branch synchronized; only the listed governance changes plus pre-existing `docs/15_DOCUMENT_INDEX.md`, exit code `0`.
- No product tests were rerun because this transition changes governance/task documents only; WP-12 acceptance evidence remains the evidence listed above.

### Next exact step

Codex independently reviews WP-13 Attempt 2 changes, re-runs deterministic evidence, and returns PASS/FAIL/NEED_ACTION. Human acceptance required after Codex PASS.

### Do not change

- Do not change ADR-001-010, D01-D10, accepted Run lifecycle/idempotency/failure semantics, or the three top-level WorkModes.
- Do not add a new Decision/Verdict table, migration, endpoint, dependency, frontend/browser path, vendor-specific Core branch, or arbitrary workflow script node without the required decision.
- Do not include pre-existing `docs/15_DOCUMENT_INDEX.md` in the WP-13 allowlist.

## Starting Branch
feature/first-vertical-slice

## Goal
Deliver the first real PolyNexus end-to-end product path:

Project
→ Review Task
→ ContextPackage
→ WorkflowDefinition
→ Reference/Mock Runtime
→ Run Supervisor
→ Finding + Evidence
→ Persist
→ Result
→ Reload History

## Confirmed Baseline
- ADR-001 through ADR-010 frozen.
- Windows development environment accepted.
- OpenCode onboarding PASS.
- Codex onboarding PASS.
- Antigravity onboarding PASS.
- Git backup available at D:\GitBackup\PolyNexus_Backup.git.

## Tool Assignment

### Codex
First writer:
- domain boundaries
- run supervisor
- workflow execution contracts
- evidence/context/artifact integration boundaries

### OpenCode
Second writer:
- persistence implementation
- API wiring
- tests
- routine integration work

### Antigravity
Milestone verifier:
- UI/E2E only after vertical slice becomes runnable

## FVS-01 Update

### Goal
Implement the minimum Domain / Execution Skeleton for Project, Task, Run, Artifact, ContextPackage, Evidence, Finding, normalized Run lifecycle, Runtime Adapter boundary, and Workflow execution boundary.

### Changed files
- `services/core/src/polynexus_core/domain/enums.py`
- `services/core/src/polynexus_core/domain/models.py`
- `services/core/src/polynexus_core/runtime/contracts.py`
- `services/core/src/polynexus_core/runtime/reference.py`
- `services/core/src/polynexus_core/runtime/supervisor.py`
- `services/core/src/polynexus_core/workflows/models.py`
- `services/core/src/polynexus_core/workflows/execution.py`
- `services/core/src/polynexus_core/workflows/loader.py`
- `services/core/tests/test_domain_models.py`
- `services/core/tests/test_runtime_skeleton.py`
- `services/core/tests/test_workflow_loader.py`

### Implemented
- Stdlib-only Domain dataclasses with stable IDs and structured ContextPackage references.
- Reference in-memory RuntimeAdapter only; no Codex/OpenCode runtime integration.
- Core-owned RunSupervisor with normalized start/collect/cancel lifecycle and cleanup verification.
- Canonical WorkflowDefinition normalization while preserving existing raw loader behavior.
- Explicit RUNTIME_EVIDENCE separation from AI_OPINION and tests for evidence/status values.

### Tests and validation
- `git diff --check`: PASS, exit code 0.
- `services/core/tests/test_domain_models.py`, `test_runtime_skeleton.py`, `test_workflow_loader.py` via `.venv` pytest: blocked by Unicode workspace process launch, exit code 1.
- `scripts/test_core.ps1`: blocked when launching `.venv\Scripts\python.exe`, exit code 101.
- `scripts/preflight.ps1`: baseline validator launch blocked by the same issue; wrapper exit code 1, inner Python launch exit code 101.

### Known blocker
The existing `.venv\Scripts\python.exe` cannot be launched from the current Codex Desktop sandbox because the workspace path contains Chinese characters and the process launcher converts it to `????`. No dependency or environment setting was changed. Current pytest and baseline validation results remain UNVERIFIED.

### Next
Rerun `scripts/test_core.ps1` and `scripts/preflight.ps1` from an environment that can launch the existing project Python runtime. After deterministic validation passes, continue with WP-02 persistence/repository work.

## FVS-02 Update

### Goal
Persistence / Repository / Migration — make FVS-01 Domain / Execution Skeleton durable and reloadable.

### Changed files
- `services/core/src/polynexus_core/persistence/__init__.py` (new)
- `services/core/src/polynexus_core/persistence/database.py` (new)
- `services/core/src/polynexus_core/persistence/models.py` (new)
- `services/core/src/polynexus_core/persistence/repository.py` (new, modified in repair)
- `services/core/alembic.ini` (new)
- `services/core/alembic/env.py` (new)
- `services/core/alembic/script.py.mako` (new)
- `services/core/alembic/versions/0001_initial_schema.py` (new)
- `services/core/tests/test_persistence.py` (new, modified in repair)

### Implemented
- SQLAlchemy ORM models mapping Domain dataclasses to SQLite tables (metadata/state/index only per ADR-008).
- Repository interfaces (ABC) for Project, Task, ContextPackage, Run, RunEvent, Artifact, Finding, Evidence.
- SQLite repository implementations with Domain↔ORM conversion boundary.
- `SqlRunEventRepository` concrete implementation with `add()` and `list_by_run()`.
- `SqlRunRepository.list_by_task()` now hydrates RunEvent history for each returned Run.
- Timestamp contract: `_ensure_utc_naive()` normalizes timezone-aware UTC datetimes to naive UTC at the write boundary; read returns naive UTC as-is.
- Alembic initial migration (0001_initial_schema) with 8 tables: projects, tasks, context_packages, runs, run_events, artifacts, findings, evidence.
- JSON serialization for tuple/list fields (instructions, constraints, artifact_refs, evidence_refs, etc.).
- ContextPackage reference-based persistence (no artifact content in SQLite).
- Artifact SHA-256 identity field preserved.
- Run lifecycle state + events + result persistence.
- Full history reload from reopened database.
- Real Alembic lifecycle test: upgrade head → verify → downgrade base → verify → upgrade head → reopen/reload.

### DB schema summary
8 tables: `projects`, `tasks`, `context_packages`, `runs`, `run_events`, `artifacts`, `findings`, `evidence`. All string IDs, datetime fields, JSON-serialized tuple/list fields. No artifact content stored in SQLite.

### Repository boundaries
- Domain dataclasses remain stdlib-only; no SQLAlchemy/FastAPI dependency.
- All persistence goes through Repository ABC interfaces.
- ORM models are internal to `persistence` package only.
- No raw SQL in application code.

### Tests and validation (FVS-02 FINAL — 2026-08-18T22:45:00+08:00)
- `services/core/tests/test_persistence.py`: 38 tests — PASS, exit code 0.
- Full `services/core` pytest: 51 tests — PASS, exit code 0.
- `git diff --check`: PASS, exit code 0.
- Execution environment: temp venv `C:\temp_pn_venv2\Scripts\python.exe` (Python 3.13.14).
- FVS02-AC-001 BLOCKER (Unicode workspace path) remains — environment issue, not product issue.

### Codex acceptance findings (all resolved in `FVS02-AC-002` repair)
- ~~MAJOR: `RunEventRepository` has an ABC but no concrete `SqlRunEventRepository`; list-based Run history does not hydrate events.~~ FIXED.
- ~~MAJOR: timezone-aware Domain timestamps use timezone-unspecified persistence columns; round-trip preservation needs an explicit contract and tests.~~ FIXED.
- ~~MINOR: persistence migration tests use `Base.metadata.create_all()` rather than the Alembic upgrade/downgrade lifecycle.~~ FIXED.

### Test count
- New persistence tests: 38
- Total project tests: 51

### ADR impact
None. ADR-008 fully respected: SQLite stores metadata/state/index only; artifact content boundary preserved; ContextPackage uses reference-based persistence.

### Scope deviation
None. All work within FVS-02 scope (WP-02).

### Next
- **OpenCode**: Read `docs/tasks/FVS-03.md` and implement only the planned API foundation on `feature/first-vertical-slice`.
- **OpenCode**: Run required deterministic tests and record actual counts/exit codes.
- **OpenCode**: Stop and escalate if authenticated loopback behavior needs a new token/pairing/SecretStore decision.
- **Codex**: Independently accept FVS-03 only after the Writer reports `READY_FOR_CODEX_ACCEPTANCE`.

## FVS-03 Update

### Goal
Core API Foundation — persistence-backed Project / Task / Run endpoints with authenticated loopback boundary.

### Changed files
- `services/core/src/polynexus_core/api/dependencies.py` (new, modified in repair)
- `services/core/src/polynexus_core/api/schemas.py` (new, modified in repair)
- `services/core/src/polynexus_core/api/projects.py` (new)
- `services/core/src/polynexus_core/api/tasks.py` (new)
- `services/core/src/polynexus_core/api/runs.py` (new)
- `services/core/src/polynexus_core/app.py` (modified, modified in repair)
- `services/core/tests/test_api.py` (new, modified in repair)

### Implemented
- Authenticated loopback dependency (`require_loopback`) with test-only override; production default fail closed.
- **B-01 repair**: When `LOOPBACK_TOKEN` env var is not set, ALL non-health requests return 403 (fail closed). Arbitrary non-empty token does NOT bypass auth.
- Pydantic request/response DTOs isolating Domain dataclasses from HTTP layer.
- **M-02 repair**: Custom `field_validator` rejects whitespace-only `ProjectCreate.name` and `TaskCreate.title` at the API layer (422), preventing unhandled 500 from Domain `__post_init__`.
- `POST /api/v1/projects`, `GET /api/v1/projects`, `GET /api/v1/projects/{project_id}` — full Project CRUD.
- `POST /api/v1/projects/{project_id}/tasks`, `GET /api/v1/projects/{project_id}/tasks`, `GET /api/v1/tasks/{task_id}` — Task CRUD with parent/child validation.
- `POST /api/v1/tasks/{task_id}/runs`, `GET /api/v1/tasks/{task_id}/runs`, `GET /api/v1/runs/{run_id}` — Run persistence/query; creates CREATED record only, no runtime execution.
- Cross-project ContextPackage reference rejection.
- Invalid payload → 422, unknown ID → 404, unauthorized caller → 403.
- API routes do not import ORM models or raw SQL; no hard-coded secrets.
- `create_app()` backward compatible (no-argument call preserved).
- **M-01 repair**: Lif lifespan handler initialises database engine + creates tables on startup, disposes on shutdown. Default app data routes do not 500 from missing session factory.

### Architecture / boundary summary
- API layer uses Pydantic DTOs; routes call Repository ABCs only.
- DB session injected via FastAPI `Depends`; tests override with temporary SQLite.
- Auth boundary: `X-Loopback-Token` header validated against `LOOPBACK_TOKEN` env var; when not configured, all non-health requests denied (fail closed).
- Run creation is persistence-only — no `RunSupervisor.start()`, no `RuntimeAdapter`, no forged evidence.
- Lifespan lifecycle: `POLYNEXUS_DATABASE_URL` env var → `init_engine()` → `create_all()` on startup.

### Tests and validation (FVS-03 REPAIR — 2026-08-19)
- `services/core/tests/test_api.py`: 32 tests — PASS, exit code 0.
- `services/core/tests/test_health.py`: 1 test — PASS, exit code 0.
- `services/core/tests/test_persistence.py`: 38 tests — PASS, exit code 0.
- Full `services/core` pytest: 83 tests — PASS, exit code 0.
- `git diff --check`: PASS, exit code 0.
- `scripts/validate_baseline.py`: PASS, exit code 0.
- Execution environment: temp venv `C:\temp_pn_venv2\Scripts\python.exe` (Python 3.13.14).

### Test count
- New API tests: 32
- Total project tests: 83

### ADR impact
None. ADR-002 (FastAPI/asyncio), ADR-004 (UI/Core boundary), ADR-007 (RunSupervisor), ADR-008 (SQLite metadata), ADR-010 (loopback auth) all respected.

### Scope deviation
None. All work within FVS-03 scope.

### Known limitations
- FVS02-AC-001 BLOCKER (Unicode workspace path) remains — environment issue, not product issue.
- `scripts/test_core.ps1` and `scripts/preflight.ps1` cannot run from Codex Desktop sandbox due to Unicode path.

### Next
- **Codex**: Independently accept FVS-03 after the Writer reports `READY_FOR_CODEX_ACCEPTANCE`.
- **OpenCode**: After acceptance, proceed with FVS-04 or WP-06 (UI scaffold).

## WP-06 Update

### Goal
Minimal React UI for Project and Task flows on top of the existing FVS-03 API, without changing backend contracts or adding authentication architecture.

### Changed files
- `apps/web/src/api.ts` (new)
- `apps/web/src/App.tsx` (rewritten)
- `apps/web/src/App.test.tsx` (rewritten)
- `apps/web/src/styles.css` (extended)
- `apps/web/src/components/ProjectList.tsx` (new)
- `apps/web/src/components/CreateProjectForm.tsx` (new)
- `apps/web/src/components/TaskList.tsx` (new)
- `apps/web/src/components/CreateTaskForm.tsx` (new)
- `apps/web/src/components/RunPreparation.tsx` (new)
- `apps/web/vite.config.ts` (modified — added `/api` proxy to `127.0.0.1:8765`)
- `apps/web/vitest.config.ts` (new)
- `apps/web/tsconfig.json` (modified — exclude test files from tsc)

### Implemented
- `api.ts`: typed API client with correct response wrappers (`{ projects }`, `{ tasks }`, `{ runs }`), injectable `getAuthHeaders`, configurable `baseUrl` (includes `/api/v1`), no hard-coded token/port/secret.
- `ProjectList`: loading, empty, 403 auth error states; project selection navigation.
- `CreateProjectForm`: name + description form, 422 error display, loading/disabled states.
- `TaskList`: Discuss/Review/Validate mode labels, task selection, empty state.
- `CreateTaskForm`: title, workflow, version, mode form; 404/422/403 error handling.
- `RunPreparation`: ContextPackage ID input (non-empty validation only, real validity from API 422), run creation, Run CREATED/LOCAL/NONE state display, run history list.
- `App.tsx`: `useState`-based view state navigation (`projects` → `tasks` → `run-prep`), no router, props-based.
- Accessibility: `role="status"` for loading, `role="alert"` for errors, `aria-label` on all forms, `aria-required`, `disabled`/`loading` button states.
- Default API base URL: `/api/v1` (same-origin). Vite dev proxy forwards `/api` → `127.0.0.1:8765`. Overridable via `VITE_POLYNEXUS_API_BASE_URL` env var (not a secret). No CORS issue in dev mode.
- `LOOPBACK_TOKEN` is NOT stored, transmitted, or referenced as a value in frontend code. The 403 error hint mentions the environment variable name only — this is an operational hint, not a secret leak.

### Tests and validation
- `apps/web/src/App.test.tsx`: 41 tests — PASS, exit code 0.
- `npm run build` (tsc -b && vite build) — PASS, exit code 0.
- `git diff --check` — PASS, exit code 0.
- Test coverage: api error classes, loading state, empty state, 403 auth error, project list, create form 422 validation, create success (POST 201 + refresh GET), navigation flow (project→task→run-prep, back navigation), task list with Validate/Review/Discuss labels, task list 403/404/422 error branches, CreateTaskForm 403/404/422 error branches, Run CREATED/LOCAL/NONE state display, run list 403/404 error branches, run create 403/404/422 error branches, accessibility (role=status, role=alert, aria-label on forms).

### Test count
- Frontend tests: 41
- Total project tests: 83 (core) + 41 (frontend) = 124

### ADR impact
None. ADR-003 (React/TS/Vite), ADR-004 (UI/Core boundary via REST), ADR-010 (no secret in UI) all respected.

### Scope deviation
- WP-06 scope strictly followed. No backend changes, no new endpoints, no new runtime dependencies.
- Pre-existing untracked files in working tree (`docs/governance/`, `docs/tasks/`, `tools/`) are from prior治理/任務文件 work, unrelated to WP-06. They do not affect WP-06 verification.

### Known limitations
- No `@testing-library/react` installed; tests use direct DOM manipulation with jsdom.
- `jsdom` added as devDependency (not a runtime dependency).
- `vitest.config.ts` added to set `environment: 'jsdom'`.
- Vite proxy (`/api` → `127.0.0.1:8765`) only applies in dev mode (`npm run dev`). Production build (`npm run build`) outputs static files; production deployment needs its own reverse proxy or CORSMiddleware.
- Frontend has no real auth source; when `LOOPBACK_TOKEN` is not set on the backend, all API calls return 403. The UI surfaces "Authentication required" with a hint about `LOOPBACK_TOKEN`.

### Next
- **Codex**: Independently review WP-06 after `READY_FOR_CODEX_REVIEW`.
- **OpenCode**: After Codex review passes, proceed with WP-07 Integration Acceptance or next FVS task.

## WP-07 Update

### Goal
Integration Acceptance — execution persistence and reload. Establish the minimal Core-owned integration that executes a Task through RunSupervisor + ReferenceRuntimeAdapter, persists all results through repositories, and verifies full session-close-reopen reload.

### Changed files
- `services/core/src/polynexus_core/execution_service.py` (new)
- `services/core/tests/test_wp07_integration.py` (new)

### Implemented
- `ExecutionService`: thin orchestration layer connecting Repository layer, Workflow loader, and RunSupervisor.
  - Loads Task and ContextPackage from repositories; validates same-project ownership.
  - Loads WorkflowDefinition from builtin YAML; validates task workflow reference.
  - **Workflow path security**: workflow_id validated against allowlist pattern (`^[a-zA-Z0-9_-]+$`); resolved path containment verified via `Path.is_relative_to()` (not string prefix); rejects sibling-prefix paths and symlink/junction escapes. Containment logic factored into `_check_workflow_path_containment` static helper (called by `_load_workflow`).
  - Executes via `RunSupervisor` + `ReferenceRuntimeAdapter`.
  - Persists Run, RunEvents, RunResult, Finding, Evidence, Artifact through repository ABCs. No direct ORM operations in service layer.
  - Single explicit transaction boundary with commit.
- `test_wp07_integration.py`: 13 integration acceptance tests covering:
  - Full lifecycle: execute → persist → close session → reopen → reload → verify.
  - Cross-project validation (Task/ContextPackage must share project).
  - Workflow reference validation (task workflow must match loaded YAML).
  - Strict run event lifecycle ordering: CREATED→STARTING→RUNNING→COMPLETED with chain integrity and monotonic timestamps.
  - Cancel cleanup persistence verification.
  - Reference runtime network egress guarantee (purely in-memory).
  - **Workflow path traversal prevention**: rejects `../`, `..\\`, URL-encoded, and non-alphanumeric workflow IDs via regex; validates sibling-prefix false positive rejection (regex layer only — not production symlink containment); symlink escape detection test requires symlink-capable environment (currently UNVERIFIED/SKIPPED).

### Architecture / boundary summary
- `ExecutionService` does NOT own Domain logic, persistence schema, or runtime adapter internals.
- All persistence goes through Repository ABC interfaces (no direct ORM operations, no raw SQL).
- Workflow loaded from `workflows/builtin/review-minimal.yaml` via existing `load_workflow_definition`.
- `ReferenceRuntimeAdapter` is purely in-memory; no network/vendor egress.
- Alembic `upgrade head` used for migration lifecycle (not `Base.metadata.create_all()`).

### Tests and validation (WP-07 ATTEMPT 5 — 2026-08-19)
- `services/core/tests/test_wp07_integration.py`: 12 passed, 1 skipped — exit code 0.
  - SKIPPED / UNVERIFIED: `test_symlink_escape_rejected` — Windows symlink permission denied; uses `pytest.skip(reason=...)`. Symlink-based containment verification could not be executed on current environment. Sibling-prefix fallback test verifies regex rejection only; it does NOT exercise production symlink containment.
- `services/core/tests/test_runtime_skeleton.py`: 2 tests — PASS, exit code 0 (regression).
- `services/core/tests/test_persistence.py`: 38 tests — PASS, exit code 0 (regression).
- Full `services/core` pytest: 95 passed, 1 skipped — exit code 0.
- `scripts/validate_baseline.py`: PASS, exit code 0.
- `git diff --check`: PASS, exit code 0.
- Execution environment: temp venv `C:\temp_pn_venv2\Scripts\python.exe` (Python 3.13.14).

### Acceptance result
- Codex independent review: **PASS** on 2026-08-19.
- Human explicitly accepted the Windows symlink containment `UNVERIFIED/SKIPPED` limitation.
- WP-07 implementation checkpoint: `d7060c4` (`feat(core): add WP-07 execution integration`).

### Test count
- New integration tests: 12 passed + 1 skipped (UNVERIFIED) = 13 total
- Total project tests: 95 (core, 1 skipped) + 41 (frontend) = 136

### Acceptance governance files
This acceptance sync includes the following governance/state files; WP-07 source/test are checkpointed at `d7060c4`:
- `AGENTS.md`
- `docs/05_GIT_WORKFLOW.md`
- `docs/06_AI_TOOL_COLLABORATION.md`
- `docs/08_ACCEPTANCE_STRATEGY.md`
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`

### ADR impact
None. ADR-007 (RunSupervisor lifecycle), ADR-008 (SQLite metadata), ADR-010 (no secret in execution) all respected.

### Scope deviation
None. All work within WP-07 scope.

### Known limitations
- `ExecutionService` uses `ReferenceRuntimeAdapter` only; production adapters will need their own integration tests.
- The service does not handle concurrent execution or retry semantics (future work).
- FVS02-AC-001 BLOCKER (Unicode workspace path) remains — environment issue, not product issue.
- `test_symlink_escape_rejected` SKIPPED / UNVERIFIED on current Windows environment (symlink permission denied). Human accepted this limitation for WP-07; full symlink containment verification remains future environment-specific evidence.

### Next
- **Human**: Acceptance of WP-08A is recorded; approve future scope decisions as required.
- **OpenCode**: Do not start WP-08B until its task document and contract/architecture gate are complete.
- **Codex**: Prepare/review the WP-08B gate; WP-08A review and acceptance are complete.
- **Antigravity**: Not required for ROADMAP-01/WP-08A review; rerun Browser E2E only after the development sequence is complete.

## ROADMAP-01 Update

- **TASK_ID**: `ROADMAP-01`
- **STATUS**: `CONFIRMED — HUMAN_ACCEPTED 2026-08-19`
- **OWNER**: Codex
- **BRANCH**: `feature/first-vertical-slice`
- **TASK_DOC**: `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`
- **GOAL**: Record the complete V1 development order, scope, forecast dates, checkpoint weights, delivery sequence, and progress-reporting contract; gate WP-08A acceptance.

### Current progress

- Accepted project progress: **22/100 = 22%**.
- Accepted FVS progress: **14/22 = 63.6%**.
- WP-08A: `ACCEPTED`, **2/2 points earned** after current evidence, Codex review PASS, and Human approval.
- Browser E2E: `UNVERIFIED/SKIPPED`, Human waiver retained and no certification claim made.

### Changed files for ROADMAP-01

- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md` (new)
- `docs/04_DEVELOPMENT_PLAN.md` (roadmap reference and current baseline)
- `docs/11_PROJECT_STATE.md` (current checkpoint/progress state)
- `docs/12_HANDOFF_CURRENT.md` (this handoff)
- `docs/15_DOCUMENT_INDEX.md` (roadmap index entry)
- `docs/tasks/WP-08A.md` (Codex review and Human acceptance recorded)
- Product source changes from OpenCode WP-08A are preserved and accepted within WP-08A scope.

### Tests and validation

- Documentation/planning update: no additional product tests run by the status-sync portion of ROADMAP-01.
- `git diff --check`: exit code 0 after the roadmap document update.
- WP-08A current deterministic evidence and Codex review are recorded in the WP-08A section below.

### ADR and scope

- ADR impact: NONE. The roadmap records existing decisions and explicitly gates future execution API contract changes.
- Scope deviation: NONE for roadmap documentation.

### Next exact step

WP-08A acceptance is complete. Next exact step is the WP-08B task document and contract/architecture gate before implementation.

### Do Not Change

- Do not start WP-08B or WP-09A without a task document and contract/architecture gate.
- Do not modify product source as part of ROADMAP-01.
- Do not stage, commit, or push without explicit Git authorization.

## WP-08A Update

- **TASK_ID**: `WP-08A`
- **STATUS**: `ACCEPTED` — Codex review PASS; Human acceptance recorded on 2026-08-19
- **ATTEMPT**: 1
- **AUTHORIZATION**: Human authorized on 2026-08-19.
- **HUMAN_ACCEPTANCE**: Confirmed on 2026-08-19 after Codex independent review PASS.
- **BRANCH**: `feature/first-vertical-slice`
- **WRITER**: OpenCode
- **REVIEWER**: Codex
- **ANTIGRAVITY_STATUS**: `NOT_REQUIRED` for implementation; Browser E2E remains `UNVERIFIED/SKIPPED`.
- **TASK_DOC**: `docs/tasks/WP-08A.md`

### Goal

Add the minimal authenticated `POST /api/v1/projects/{project_id}/context-packages` command using the existing ContextPackage Domain model and Repository boundary, so a later UI slice can create a versioned reference manifest.

### Changed files

- `services/core/src/polynexus_core/api/context_packages.py` (new)
- `services/core/src/polynexus_core/api/schemas.py` (modified — added ContextPackageCreate/ContextPackageResponse)
- `services/core/src/polynexus_core/app.py` (modified — included context_packages router)
- `services/core/tests/test_wp08_context_packages.py` (new)

### Implemented

- `POST /api/v1/projects/{project_id}/context-packages` endpoint with `AuthLoopback` and fail-closed auth.
- Returns `201 Created` with persisted ContextPackage response.
- Validates parent Project exists (404 if not found).
- Validates `version >= 1` via Pydantic `Field(ge=1)` and Domain `__post_init__` (422 for invalid body/version).
- Uses existing `ContextPackage` domain model and `SqlContextPackageRepository` boundary — no direct ORM operations in route.
- Pydantic `ContextPackageCreate` request DTO with all optional manifest fields (instructions, constraints, project_facts, artifact_refs, prior_decision_refs, memory_refs, source_refs).
- Pydantic `ContextPackageResponse` response DTO returning all persisted fields.
- No changes to existing `POST /tasks/{task_id}/runs` behaviour.
- No calls to `ExecutionService`.

### Tests and validation (WP-08A ATTEMPT 1 — 2026-08-19)
- `services/core/tests/test_wp08_context_packages.py`: 14 passed — exit code 0.
  - 201 create with full fields, 201 create with minimal body, 403 auth, 404 project, 422 version zero, 422 version negative, 422 missing version, 422 empty body, persistence reload, no secret in response, no direct ORM operation, repository boundary, run API unchanged, placeholder regression.
- `services/core/tests/test_api.py`: 32 tests — PASS, exit code 0 (regression).
- `services/core/tests/test_persistence.py`: 38 tests — PASS, exit code 0 (regression).
- `services/core/tests/test_wp07_integration.py`: 12 passed, 1 skipped — exit code 0 (regression).
- API + persistence regression: 70 passed — exit code 0.
- Full `services/core` pytest: 108 passed, 1 skipped — exit code 0.
- `scripts/validate_baseline.py`: PASS, exit code 0.
- `git diff --check`: PASS, exit code 0.
- `create_app()` route inspection: ContextPackage endpoint registered — exit code 0.
- Execution environment: temp venv `C:\temp_pn_venv2\Scripts\python.exe` (Python 3.13.14).

### Test count
- New WP-08A tests: 14
- Total project tests: 108 (core, 1 skipped) + 41 (frontend) = 149

### Protected areas
- ADR-001–010: untouched.
- Existing `POST /tasks/{task_id}/runs` behaviour: untouched.
- `ExecutionService`: untouched.
- Frontend source: untouched.
- Workflow YAML: untouched.
- Dependencies: untouched.
- Database schema: untouched (existing ContextPackage table already supports all fields).

### ADR impact

NONE. ADR-002 (FastAPI/asyncio), ADR-004 (UI/Core boundary), ADR-008 (SQLite metadata / ContextPackage as reference manifest), ADR-010 (no secret in response) all respected.

### Scope deviation

NONE. All work within WP-08A scope.

### Known limitations

- Browser DOM / Playwright E2E remains `UNVERIFIED/SKIPPED` by Human waiver and is deferred until development is complete.
- The existing Run API still creates `CREATED` only; WP-08A does not change that behaviour.
- pytest emitted a Windows temp cleanup `PermissionError` at interpreter exit; all test commands returned exit code 0.
- `test_full_core_regression` is a no-op placeholder; the independent full Core command is the actual regression evidence. Remove or rename it in a later test-quality cleanup.

### Do Not Change

- Do not modify `POST /api/v1/tasks/{task_id}/runs` execution semantics.
- Do not call or modify `ExecutionService`.
- Do not add frontend, WebSocket, vendor, plugin, or browser logic.
- Do not change ADR-001–010 or add dependencies.
- Do not stage, commit, or push during implementation.

### Acceptance result and next

- **Codex**: Independent review `PASS`; no BLOCKER or MAJOR findings.
- **Human**: WP-08A acceptance confirmed on 2026-08-19.
- **OpenCode**: Prepare the next FVS task only after the WP-08B task document and gate are ready.

## FVS-MILESTONE-UI-E2E-01 Update

- **TASK_ID**: `FVS-MILESTONE-UI-E2E-01`
- **ATTEMPT**: 1
- **BRANCH**: `feature/first-vertical-slice`
- **WRITER**: OpenCode (WP-06 frontend already implemented)
- **REVIEWER**: Codex
- **ANTIGRAVITY_STATUS**: Completed read-only verification; Browser E2E `UNVERIFIED/SKIPPED`
- **RESULT**: Accepted with explicit Human waiver; this is not full Browser E2E certification.

### Goal and evidence

Verify the existing UI/Core integration through Project → Task → Run Preparation, including `/api/v1`, Vite proxy, fail-closed auth, mode labels, ContextPackage validation, run-state display, navigation, errors, and accessibility.

- Codex rerun: `cd apps/web && npm test` — 41 passed, exit code 0.
- Codex rerun: `cd apps/web && npm run build` — success, exit code 0.
- Codex rerun: `git diff --check` — clean, exit code 0.
- Codex check: `git status --short --branch` — clean, no untracked files, exit code 0.
- Antigravity reported live Core health and Vite `/api` proxy checks — PASS, exit code 0.
- Browser DOM / Playwright screenshot or video artifact — `UNVERIFIED/SKIPPED`; browser binary unavailable in the verification environment.

### Changed files and protected areas

- Product source changed for this verification: **NONE**.
- Governance sync files: `docs/11_PROJECT_STATE.md`, `docs/12_HANDOFF_CURRENT.md`.
- Untracked files: **NONE** at review baseline.
- Protected: `services/core/`, existing `apps/web/src/` implementation, API contracts, workflow YAML, and ADR-001–010 were not changed.

### ADR impact

None. ADR-003, ADR-004, and ADR-010 remain respected.

### Scope deviation

None for product source. Browser E2E maturity is explicitly deferred, not certified.

### Human waiver and limitation

Human explicitly accepted 41 Vitest tests, live HTTP/proxy checks, and static inspection as the temporary acceptance basis, with Browser E2E marked `UNVERIFIED/SKIPPED`. Browser E2E must be rerun after development is complete.

### Do Not Change
- Do not relabel Browser E2E as PASS before a browser-capable rerun.
- Do not modify ADR-001–010, Core source, API contracts, or frontend source as part of this governance sync.
- Do not start multiple writers on `feature/first-vertical-slice`.

## WP-08B Attempt 2 Update

- **TASK_ID**: `WP-08B`
- **ATTEMPT**: `2`
- **BRANCH**: `feature/first-vertical-slice`
- **WRITER**: Antigravity
- **REVIEWER**: Codex
- **ANTIGRAVITY_STATUS**: `IMPLEMENTATION_COMPLETE`
- **RESULT**: `READY_FOR_CODEX_REVIEW`

### Goal
Implement ContextPackage authoring and selection in the React frontend, strictly validating version integer input, encoding path params, parsing all manifest fields (with whitespace trimming and blank omission), and populating the returned real ContextPackage ID into Run creation.

### Changed files (THIS_ATTEMPT: WP-08B Frontend)
- `apps/web/src/api.ts` (ContextPackage types and `createContextPackage`)
- `apps/web/src/components/RunPreparation.tsx` (authoring form, strict integer validation, ID auto-population)
- `apps/web/src/styles.css` (authoring UI and hints)
- `apps/web/src/App.test.tsx` (61 tests, including strict version, URL encoding, full manifest shape, Run regression)
- `docs/tasks/WP-08B.md` (task status sync)
- `docs/11_PROJECT_STATE.md` (project state sync)
- `docs/12_HANDOFF_CURRENT.md` (handoff sync)
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md` (roadmap sync)

### Protected areas check (PRE_EXISTING_ACCEPTED: WP-08A Core)
- `services/core/src/polynexus_core/api/context_packages.py` (Unchanged by WP-08B)
- `services/core/src/polynexus_core/api/schemas.py` (Unchanged by WP-08B)
- `services/core/src/polynexus_core/app.py` (Unchanged by WP-08B)
- `services/core/tests/test_wp08_context_packages.py` (Unchanged by WP-08B)
- `docs/tasks/WP-08A.md` (Unchanged by WP-08B)
- ADR-001–010 respected. No backend modifications.

### Tests and deterministic evidence
- `cd apps/web && npm test` (`vitest run`): 61 passed across 1 file, exit code 0.
- `cd apps/web && npm run build` (`tsc -b && vite build`): PASS, exit code 0.
- `git diff --check`: PASS, exit code 0.

### Known limitations
- Selection uses manual ID input or the newly created ID from the authoring form (no GET/list endpoint in Core per WP-08A contract).

### Unverified
- Real Headless Browser E2E (Playwright) remains `UNVERIFIED/SKIPPED` under existing Human waiver.

### Next
- Codex independent review of WP-08B Attempt 2.

## WP-08B Acceptance Update

- **TASK_ID**: `WP-08B`
- **STATUS**: `ACCEPTED`
- **CODEX_REVIEW**: PASS; no BLOCKER, MAJOR, or MINOR findings.
- **HUMAN_ACCEPTANCE**: Confirmed on 2026-08-19.
- **ITEM_PROGRESS**: 100% — 2/2 points accepted.
- **PROJECT_PROGRESS**: 24/100 = 24%.
- **FVS_PROGRESS**: 16/22 = 72.7%.
- **TESTS**: 61 frontend tests passed, build passed, and `git diff --check` exited 0.
- **UNVERIFIED**: Browser DOM / Playwright E2E remains `UNVERIFIED/SKIPPED` under the accepted Human waiver.
- **NEXT**: Prepare WP-09A contract/architecture gate; do not implement execution API semantics before approval.

Earlier WP-08B preparation and review text in this handoff is historical; this acceptance update and the top Status section are current.

## WP-09B Acceptance Update

- **TASK_ID**: `WP-09B`
- **ATTEMPT**: 5
- **STATUS**: `ACCEPTED`
- **BRANCH**: `feature/first-vertical-slice`
- **WRITER**: OpenCode
- **REVIEWER**: Codex — PASS
- **ANTIGRAVITY_STATUS**: `NOT_REQUIRED` (Core-only task; no browser/E2E involvement)
- **NEXT_OWNER**: transition completed; current owner is OpenCode for WP-09C
- **HANDOFF_DOC**: `docs/12_HANDOFF_CURRENT.md`
- **TASK_DOC**: `docs/tasks/WP-09B.md`

### Changed files

Modified (WP-09B core):
- `services/core/src/polynexus_core/api/runs.py`
- `services/core/src/polynexus_core/execution_service.py`
- `services/core/src/polynexus_core/runtime/supervisor.py` — now guards `version_info()` before COMPLETED, types `RunExecution.result` as `RunResult | None`
- `services/core/src/polynexus_core/persistence/repository.py`
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- `docs/tasks/WP-09B.md`
- `services/core/tests/test_wp09_execution_api.py` — version_info added to failure matrix, Finding/Evidence/Artifact output test

New (WP-09B):
- `services/core/src/polynexus_core/errors.py`
- `services/core/src/polynexus_core/api/errors.py`

### Implementation summary (Attempt 5 — guards version_info, typed result, production output test)

Durable claim (preserved):

**Durable claim** (preserved from Attempt 3):
- `RunRepository` ABC declares `claim_for_execution()` and `append_event()`.
- ExecutionService uses `RunRepository` ABC — no SqlRunRepository cast.
- Flow: validate all references → CAS claim → append claim event → commit → reload → execute.
- CAS claim + event committed BEFORE adapter invocation.

**Runtime failure isolation** (new in Attempt 4):
- `execute_claimed_run()` wraps each adapter boundary call individually: `workflow_executor.execute()` (which calls `create_run`+`submit`), `adapter.status()`, `adapter.result()`, `adapter.artifacts()`.
- Any runtime exception → `RunState.FAILED` transition with sanitized reason `"Runtime boundary error"`.
- Returns `RunExecution(run=run, result=None, findings=(), evidence=(), artifacts=())` — no fabricated Result/Evidence/Finding/Artifact.
- Programmer/domain validation errors (ValueError) are NOT caught — they propagate to caller.

**Sanitized failure** (new in Attempt 4):
- Fixed public-safe reason: `"Runtime boundary error"`.
- Never contains raw str(exc), vendor payload, path, token, or credential fragment.
- Test uses `_SECRET_MARKER` and asserts it does not appear in response, events, result, evidence, or DB reload.

**No fabricated output** (new in Attempt 4):
- ExecutionService only persists Finding/Evidence/Artifact when `execution.result is not None`.
- On failure: only Run state + events persisted. result=None, no Finding/Evidence/Artifact in DB.
- API returns 202 RunResponse with result=null per contract.

**Layer boundary** (preserved from Attempt 3):
- Exceptions in `polynexus_core.errors` (core layer).
- `api/errors.py` re-exports for backward compatibility.
- `ResourceNotFoundError` docstring says "API maps to HTTP 422".

### Tests and validation (Attempt 5 — accepted evidence)

- `C:\temp_pn_venv2\Scripts\python.exe -m pytest -q services\core\tests\test_wp09_execution_api.py`: 36 tests passed — exit code 0.
- `C:\temp_pn_venv2\Scripts\python.exe -m pytest -q services\core`: 134 tests passed, 1 skipped — exit code 0.
- `scripts/validate_baseline.py`: PASS, exit code 0.
- `git diff --check`: PASS, exit code 0.

### Acceptance and progress

- Codex independent review: `PASS`; no BLOCKER, MAJOR, or MINOR findings.
- Human acceptance: confirmed on 2026-08-20.
- Item progress: `100%`, **2/2 points accepted**.
- Accepted project progress: **26/100 = 26%**.
- Accepted FVS progress: **18/22 = 81.8%**.
- Progress allocation decision: WP-09B 2 points; remaining CP-02 work is WP-09C 1 point, WP-09D 1 point, and WP-10 2 points, preserving the 22-point checkpoint total.

### Protected areas

- WP-08A ContextPackage REST contract and Core tests.
- WP-08B frontend authoring/selection and Run `CREATED / LOCAL / NONE` display.
- ADR-001–010 remain frozen.
- ReferenceRuntimeAdapter no-network behavior and workflow path containment.
- Repository/ORM boundary: routes use dependencies and repositories; no direct ORM/raw SQL in API route logic.

### ADR impact

NONE. ADR-004, ADR-007, ADR-008, ADR-010 respected with no ADR file changes.

### Scope deviation

NONE.

### Known limitations

- True concurrent HTTP execution: UNVERIFIED (sequential regression tested; repository-level CAS one-winner test included).
- Browser E2E: UNVERIFIED/SKIPPED.

### UNVERIFIED

- Browser DOM / Playwright E2E: `UNVERIFIED/SKIPPED`.
- True concurrent HTTP duplicate-command execution: `UNVERIFIED`.

### Do Not Change

- WP-08A/WP-08B contract, ADR-001–010, migration, dependency, existing POST task/runs 201 CREATED semantics.

### Next

- WP-09C task preparation is complete; OpenCode implements `docs/tasks/WP-09C.md` without changing the accepted WP-09B execution command contract.

## WP-09A Architecture Gate Acceptance

- **TASK_ID**: `WP-09A`
- **STATUS**: `ACCEPTED_ARCHITECTURE_GATE`
- **BRANCH**: `feature/first-vertical-slice`
- **WRITER**: Codex (proposal only)
- **REVIEWER / DECISION OWNER**: Codex independent architecture review PASS / Human contract approval confirmed 2026-08-19
- **ITEM_PROGRESS**: `100%` gate complete; no product points assigned or earned from this contract-only task
- **PROJECT_PROGRESS**: `24/100 = 24%`
- **FVS_PROGRESS**: `16/22 = 72.7%`

### Changed files in this gate preparation

- `docs/tasks/WP-09A.md` (new execution command contract proposal and decision gate)
- `docs/11_PROJECT_STATE.md` (current gate/status synchronization)
- `docs/12_HANDOFF_CURRENT.md` (current handoff synchronization)
- `docs/15_DOCUMENT_INDEX.md` (task index entry)
- `docs/04_DEVELOPMENT_PLAN.md` (progress/status note)
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md` (WP-09A gate status; accepted progress unchanged)
- `docs/tasks/WP-09B.md` (approved implementation Writer handoff)

### Critical finding

The accepted Run-create endpoint persists a `CREATED` Run and intentionally does not execute. The current `ExecutionService.execute_task()` and `RunSupervisor.start()` path creates another Run and reads the ContextPackage from `Task.context_package_id`. A direct API wiring would therefore risk duplicate Run records, wrong ContextPackage authority, and non-durable failure state. Human approved Option A and Codex confirmed the contract: execute the existing `run_id`, use the Run ContextPackage reference, return command `202`/durable GET semantics, and prevent duplicate runtime submission.

### Protected areas

- No product source changed under `services/core/` or `apps/web/`.
- ADR-001–010 remain frozen; ADR-004/007/008/010 are marked potentially affected pending decision, not modified.
- WP-08A Core contract, WP-08B UI behavior, and `CREATED / LOCAL / NONE` Run display remain protected.
- Browser DOM / Playwright E2E remains `UNVERIFIED/SKIPPED` under the accepted waiver.

### Required next action

WP-09A gate is complete. OpenCode may implement WP-09B under `docs/tasks/WP-09B.md`; Codex must independently review the resulting source and deterministic evidence before Human acceptance.

### Do not change

- Do not implement an execution endpoint yet.
- Do not change Core/frontend source, API schemas, migrations, runtime adapters, workflow YAML, or ADR-001–010.
- Do not stage, commit, push, or rewrite unrelated working-tree changes without explicit authorization.

## Restrictions
- Do not change ADR-001–010 without a new ADR and explicit human approval.
- Do not add Plugin/MCP infrastructure.
- Do not add unrelated V1 features.
- Do not allow multiple active writers.
- Do not claim PASS without current deterministic evidence.

## WP-09C Acceptance Update (Attempt 4)

- **TASK_ID**: `WP-09C`
- **ATTEMPT**: 4
- **IMPLEMENTATION_ATTEMPT**: 3
- **REVIEW_ATTEMPT**: 4
- **STATUS**: `ACCEPTED`
- **TASK_DOC**: `docs/tasks/WP-09C.md`
- **HANDOFF_DOC**: `docs/12_HANDOFF_CURRENT.md`
- **BRANCH**: `feature/first-vertical-slice`
- **WRITER**: OpenCode
- **REVIEWER**: Codex
- **ANTIGRAVITY_STATUS**: `NOT_REQUIRED` — Core-only task; Browser E2E remains `UNVERIFIED/SKIPPED`
- **NEXT_OWNER**: Codex
- **CODEX_REVIEW**: `PASS`
- **HUMAN_ACCEPTANCE**: Confirmed on 2026-08-20
- **ITEM_PROGRESS**: `100%` — 1/1 point accepted
- **PROJECT_PROGRESS**: `27/100 = 27%`
- **FVS_PROGRESS**: `19/22 = 86.4%`

### Changed files (actual git status)

Modified:
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- `docs/15_DOCUMENT_INDEX.md` — PRE_EXISTING task-preparation change (not WP-09C scope; see SCOPE_DEVIATION)
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`
- `services/core/src/polynexus_core/api/schemas.py` — Modified (wrappers added)
- `services/core/src/polynexus_core/app.py` — Modified (router mount)
- `services/core/src/polynexus_core/persistence/repository.py` — Modified (RunEvent tie-breaker order_by(occurred_at, id); list_by_run ordering)

Untracked:
- `docs/tasks/WP-09C.md` — Untracked (task document, part of WP-09C handoff)
- `services/core/src/polynexus_core/api/run_outputs.py` — Untracked (new, 5 endpoints)
- `services/core/tests/test_wp09_query_api.py` — Untracked (new, now 24 tests)

### Tests (Attempt 4 — current acceptance evidence; implementation baseline Attempt 3 historical)

- `test_wp09_query_api.py`: 24 passed, exit code 0
- `test_wp09_execution_api.py`: 36 passed, exit code 0 (unchanged)
- `services/core` full: 169 passed, 1 skipped, exit code 0 (170 collected)
- `services/core` collect: 170 tests, exit code 0
- `validate_baseline.py`: PASS, exit code 0
- `git diff --check`: PASS, exit code 0

### Protected areas

- WP-09B execution/lifecycle/CAS, WP-08A/B, ADR-001–010, Domain/ORM/Alembic, frontend — all unchanged

### ADR impact

NONE — extends ADR-004 query boundary, preserves ADR-008/010

### SCOPE_DEVIATION

- `docs/15_DOCUMENT_INDEX.md` modification is PRE_EXISTING task-preparation change (cross-attempt historical; not introduced in any WP-09C attempt); no product scope change

### UNVERIFIED

Symlink containment `UNVERIFIED/SKIPPED`, Browser E2E `UNVERIFIED/SKIPPED`, concurrent HTTP `UNVERIFIED`

### Next

WP-09D task scope and Writer handoff are recorded in `docs/tasks/WP-09D.md`. OpenCode may now implement the scoped frontend task; do not modify protected Core contracts.

### Do not change

- ADR-001–010, Domain/ORM/Alembic, WP-08A/B, WP-09A/B, frontend, dependencies, artifact file content, or secret handling.

## WP-09D Implementation Handoff (Attempt 3)

- `TASK_ID`: `WP-09D`
- `STATUS`: `READY_FOR_CODEX_REVIEW`
- `ATTEMPT`: `3`
- `BRANCH`: `feature/first-vertical-slice`
- `WRITER`: `OpenCode`
- `REVIEWER`: `Codex`
- `ANTIGRAVITY_STATUS`: `NOT_REQUIRED_FOR_IMPLEMENTATION` — no real-browser E2E; waiver remains `UNVERIFIED/SKIPPED`
- `NEXT_OWNER`: `Codex`
- `HANDOFF_DOC`: `docs/12_HANDOFF_CURRENT.md`
- `TASK_DOC`: `docs/tasks/WP-09D.md`

### Changed files

Modified:
- `apps/web/src/App.test.tsx` — add WP-09D assertions for full metadata/reference fields including Finding task_id/run_id and Evidence task_id/run_id (78 tests = 61 baseline + 17 WP-09D, preserve existing; Attempt 3 adds task_id/run_id asserts inside existing full-metadata test)
- `apps/web/src/App.tsx` — add run-detail view state, props-based no-router navigation
- `apps/web/src/api.ts` — add WP-09C 5 query wrappers/types/functions, preserve /api/v1, auth injection, error classes, URL encoding
- `apps/web/src/components/RunPreparation.tsx` — add Result/History detail action per Run, preserve CREATED/LOCAL/NONE and ContextPackage authoring
- `apps/web/src/styles.css` — minimal detail-section styles (detail-section) + RunDetail metadata display
- `docs/11_PROJECT_STATE.md` — WP-09D Attempt 3 READY_FOR_CODEX_REVIEW — implementation complete / awaiting Codex review; 78 frontend tests; Current Next Gate = Codex review / Human acceptance
- `docs/12_HANDOFF_CURRENT.md` — this handoff (Attempt 3) with correct modified/untracked ledger
- `docs/15_DOCUMENT_INDEX.md` — PRE_EXISTING dirty state (not WP-09D scope; see SCOPE_DEVIATION)
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md` — WP-09D Attempt 3 READY_FOR_CODEX_REVIEW; 78 Vitest tests PASS + build PASS

Untracked:
- `apps/web/src/components/RunDetail.tsx` — read-only detail fetching 6 endpoints with full metadata fields (Finding: id/task_id/run_id/title/description/severity/status/evidence_refs/created_at; Evidence: id/task_id/run_id/actor_id/source/type/status/artifact_refs/metadata/observed_at; Artifact: id/project/task/run IDs/artifact_type/mime_type/source_type/storage_ref/sha256/size; History: id/run_id/from_state/to_state/occurred_at/reason), no artifact content read, no download, no fabricated evidence, no secret exposure
- `docs/tasks/WP-09D.md` — status READY_FOR_CODEX_REVIEW Attempt 3 (still untracked until commit) — Progress checkpoint synced to READY_FOR_CODEX_REVIEW, implementation complete / awaiting Codex review, ITEM_PROGRESS 0%, PROJECT_PROGRESS 27/100, FVS_PROGRESS 19/22

### Protected areas

- ADR-001–010 (frozen, no change)
- WP-08A/WP-08B contracts and frontend baseline (preserved, 61 tests retained + 17 new = 78)
- WP-09B execution/lifecycle/CAS/failure isolation (no Core change)
- WP-09C REST query contract (no endpoint/schema/migration change)
- No Core source, REST endpoint, schema, migration, runtime, dependency changes

### Tests

- `cd apps/web && npm test` — 78 passed, exit code 0 (61 baseline preserved + 17 WP-09D, including Attempt 3 finding/evid task_id/run_id asserts: `f_1 — task:t_1 — run:run_1 — FindTitle` and `ev_1 — task:t_1 — run:run_1 — actor_1`)
- `cd apps/web && npm run build` — PASS, exit code 0 (tsc -b && vite build)
- `git diff --check` — PASS, exit code 0 (no whitespace errors)
- `git status --short --branch` — Modified: 9 (apps/web 5 + docs 4) + Untracked: 2 (RunDetail.tsx + WP-09D.md), branch feature/first-vertical-slice, exit code 0
  - `## feature/first-vertical-slice...backup/feature/first-vertical-slice [ahead 1]`
  - ` M apps/web/src/App.test.tsx`
  - ` M apps/web/src/App.tsx`
  - ` M apps/web/src/api.ts`
  - ` M apps/web/src/components/RunPreparation.tsx`
  - ` M apps/web/src/styles.css`
  - ` M docs/11_PROJECT_STATE.md`
  - ` M docs/12_HANDOFF_CURRENT.md`
  - ` M docs/15_DOCUMENT_INDEX.md`
  - ` M docs/28_MASTER_DEVELOPMENT_ROADMAP.md`
  - `?? apps/web/src/components/RunDetail.tsx`
  - `?? docs/tasks/WP-09D.md`

### ADR impact

NONE — extends UI consumption of accepted WP-09C contract; preserves ADR-004/008/010; no services/core, REST contract, ADR, or dependency change

### Scope deviation

NONE

### Known limitations

- None new beyond inherited symlink UNVERIFIED/SKIPPED
- Frontend has no real auth source; 403 hint is operational LOOPBACK_TOKEN name only, not secret value

### Unverified

- Browser DOM / Playwright E2E: `UNVERIFIED/SKIPPED` (accepted waiver, deferred to browser verification work)
- True concurrent HTTP duplicate-command: `UNVERIFIED` (repository-level CAS test covers claim)
- Symlink containment: `UNVERIFIED/SKIPPED` (Windows permission, Human waiver accepted)

### Next

WP-09D Codex PASS and Human acceptance are recorded below. Prepare WP-10 final deterministic acceptance.

### Do not change

- Do not modify `services/core/` WP-09B/C execution, WP-09C REST routes/schemas, WP-08A/B frontend, ADR-001–010, migrations, dependencies, storage, or secret handling.
- Do not count WP-09D toward accepted progress (27/100, 19/22) before Codex PASS and Human acceptance.

## WP-09D Acceptance Update (Attempt 3)

- `TASK_ID`: `WP-09D`
- `STATUS`: `ACCEPTED`
- `ATTEMPT`: `3`
- `CODEX_REVIEW`: `PASS`
- `HUMAN_ACCEPTANCE`: Confirmed on `2026-08-20`
- `ITEM_PROGRESS`: `100%` — 1/1 point accepted
- `PROJECT_PROGRESS`: `28/100 = 28%`
- `FVS_PROGRESS`: `20/22 = 90.9%`
- `APPROVED_FOR_COMMIT`: `YES` — explicit Human authorization recorded in the current session

### Acceptance evidence

- `cd apps/web && npm test` — 78 passed, exit code 0
- `cd apps/web && npm run build` — PASS, exit code 0
- `git diff --check` — PASS, exit code 0
- Browser DOM / Playwright E2E remains `UNVERIFIED/SKIPPED` under the accepted waiver.

### Accepted stage allowlist

- `apps/web/src/App.test.tsx`
- `apps/web/src/App.tsx`
- `apps/web/src/api.ts`
- `apps/web/src/components/RunPreparation.tsx`
- `apps/web/src/components/RunDetail.tsx`
- `apps/web/src/styles.css`
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`
- `docs/tasks/WP-09D.md`

Excluded and preserved: `docs/15_DOCUMENT_INDEX.md` remains pre-existing dirty state and is not part of the WP-09D commit.

### Next

Prepare WP-10 FVS final deterministic acceptance. Do not relabel Browser E2E, symlink containment, or concurrent HTTP limitations as verified.

## WP-10 Acceptance Update (Attempt 1)

- `TASK_ID`: `WP-10`
- `STATUS`: `ACCEPTED`
- `ATTEMPT`: `1`
- `BRANCH`: `feature/first-vertical-slice`
- `WRITER`: `Codex (acceptance runner)`
- `REVIEWER`: `Human`
- `ANTIGRAVITY_STATUS`: `NOT_REQUIRED_FOR_IMPLEMENTATION` (Browser E2E remains `UNVERIFIED/SKIPPED`)
- `NEXT_OWNER`: `Codex/Human` for WP-11 task preparation
- `CODEX_RESULT`: `PASS`
- `HUMAN_ACCEPTANCE`: Confirmed on `2026-08-20`
- `ITEM_PROGRESS`: `100%` — 2/2 CP-02 points accepted
- `PROJECT_PROGRESS`: `30/100 = 30%`
- `FVS_PROGRESS`: `22/22 = 100%`

### Acceptance evidence

- Full Core: `169 passed, 1 skipped`, `170 collected`, exit code `0`.
- Fresh DB / Alembic / reopen-reload focused checks: `4 passed`, exit code `0`.
- Frontend Vitest: `78 passed`, exit code `0`.
- Frontend build: PASS, exit code `0`.
- Baseline validation: PASS, exit code `0`.
- `git diff --check`: PASS, exit code `0`.
- The skipped test is the Windows-policy-limited symlink escape test. A non-fatal pytest temp cleanup `PermissionError` was emitted, but the test exit code remained `0`.

### Protected areas and limitations

- ADR-001–010, WP-08A/WP-08B, WP-09B/WP-09C/WP-09D behavior, REST contracts, migrations, dependencies, storage, and secret boundaries were not changed.
- ADR impact: `NONE`.
- Scope deviation: `NONE`; pre-existing `docs/15_DOCUMENT_INDEX.md` remains unstaged and excluded.
- Browser DOM / Playwright E2E: `UNVERIFIED/SKIPPED` under the accepted waiver.
- Symlink containment: `UNVERIFIED/SKIPPED` under Windows policy.
- True concurrent HTTP duplicate-command execution: `UNVERIFIED`; repository-level CAS coverage remains available.

### WP-10 stage allowlist

- `docs/tasks/WP-10.md`
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`

Excluded and preserved: `docs/15_DOCUMENT_INDEX.md` remains pre-existing dirty state and is not part of the WP-10 checkpoint commit.

### Next (historical)

`docs/tasks/WP-11.md` creation was the next step — now complete (see WP-11 Task Document section below). Do not begin WP-11 implementation before Codex confirms the scope/tests.

## WP-11 Implementation (Attempt 4) — READY_FOR_CODEX_REVIEW

- `TASK_ID`: `WP-11`
- `STATUS`: `READY_FOR_CODEX_REVIEW`
- `ATTEMPT`: `4`
- `BRANCH`: `feature/first-vertical-slice`
- `WRITER`: `OpenCode`
- `REVIEWER`: `Codex`
- `ANTIGRAVITY_STATUS`: `NOT_REQUIRED` — Core/API contract task; no Browser E2E
- `NEXT_OWNER`: `Codex` (independent review) → `Human` (acceptance)
- `HANDOFF_DOC`: `docs/12_HANDOFF_CURRENT.md`
- `TASK_DOC`: `docs/tasks/WP-11.md`
- `ROADMAP_DOC`: `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`

### Goal

Lock `WorkMode` semantics to exactly three top-level modes (`DISCUSS`, `REVIEW`, `VALIDATE`), prove `422` for any other value (including `DEVELOP`, lower-case, whitespace-padded — but **not** `""` which under current code is `201 REVIEW`), record omitted-mode (and `""`/`null` → `REVIEW`) default as `REVIEW` (per `services/core/src/polynexus_core/domain/enums.py:42-46`, `services/core/src/polynexus_core/domain/models.py:49`, `services/core/src/polynexus_core/api/tasks.py:72-80`, `services/core/src/polynexus_core/api/schemas.py:46`), and prove persistence/reload round-trip. No fourth mode, no ADR change, no new Domain/migration/dependency. If `""` must be `422`, stop and report `NEED_ACTION` before modifying `api/tasks.py`.

### Three legal modes

- `DISCUSS` — Independent analysis → Cross Review → Consensus/Disagreement/Risks/Missing Info → Human Decision
- `REVIEW` — Artifact/Code/Document → Findings/Severity/Blockers/Recommendations
- `VALIDATE` — Tool/Command/Rule/Document Check → Evidence → PASS/FAIL/NEED_ACTION/HUMAN_DECISION
- Notes: case-sensitive upper-case only; `Develop` is a Workflow action/Agent role, not a top-level Task mode (scope baseline §3). Any other string is illegal.

### Illegal mode — 422 contract

- Any provided `mode` not in `["DISCUSS","REVIEW","VALIDATE"]` → `422` with detail `Invalid mode: {value}. Must be one of: DISCUSS, REVIEW, VALIDATE` (`services/core/src/polynexus_core/api/tasks.py:77-80`), no row created, no secret leak.
- Covers: `INVALID`, `DEVELOP`, `discuss`, `review`, `validate`, `DISCUSS `, ` REVIEW`.
- Note: `""` (empty string) is **not** `422` under current code — `api/tasks.py:72` checks `if body.mode:` (falsy) → `201` with `mode == "REVIEW"` (see Omitted mode). If `""` must be `422`, report `NEED_ACTION` before modifying `api/tasks.py`.

### Omitted mode — default behavior

- **Current contract**: omitted field, `null`, or `""` (empty string, falsy) → `201` with `mode == "REVIEW"` (`api/tasks.py:72` `mode = WorkMode.REVIEW` if falsy; `domain/models.py:49` default `WorkMode.REVIEW`; `api/schemas.py:46` `mode: str | None = None`; persistence stores `"REVIEW"` string and reloads `WorkMode(r.mode)`).
- **Decision gate**: If Human/Codex requires explicit required mode or a different default (e.g., `DISCUSS`), this task must return `NEED_ACTION` with a Decision/ADR update **before** any code change. Writer will implement tests against `REVIEW` default unless a new decision is recorded in `docs/10_DECISION_LOG.md` / `docs/18_ARCHITECTURE_DECISIONS.md`.

### Persistence / reload and API contract

- Stored as `String(32)` (`persistence/models.py: mode`) via `t.mode.value` / `WorkMode(r.mode)` (`persistence/repository.py`).
- Proof: create Task with each legal mode and omitted, commit, **close → reopen** DB file, `GET /projects/{project_id}/tasks` and `GET /tasks/{task_id}` both return same `mode`.
- `POST /api/v1/projects/{project_id}/tasks`: `201` for legal/omitted, `422` for illegal, `403` without auth, `404` for missing project; `GET` endpoints mirror same `mode` string, with `403`/`404` preserved.

### Test matrix (WP-11)

1. `WorkMode` enum exactly `DISCUSS, REVIEW, VALIDATE` — no `DEVELOP`.
2. `Task(project_id="p_1", title="T", workflow_id="wf", workflow_version=1)` without `mode` (all required params except `mode` supplied) defaults to `REVIEW` in-memory; `Task(..., mode=WorkMode.DISCUSS|REVIEW|VALIDATE)` round-trips.
3-5. `POST` with `DISCUSS`/`REVIEW`/`VALIDATE` → `201` `mode` matches.
6. `POST` omitted → `201` `mode == REVIEW`; `POST` `""` and `null` (both falsy under current code) also → `201` `mode == REVIEW`.
7. (removed — `""` is `201` not `422`; if `""` must be `422`, report `NEED_ACTION`).
8-11. `POST` `INVALID`/`DEVELOP`/`discuss`/` REVIEW ` (whitespace-padded) → `422` with `Invalid mode` detail, no creation.
12-13. Persistence close/reopen round-trip for each legal, omitted, and `""` (all `REVIEW`) → `GET` returns same; `GET /projects/{id}/tasks` and `GET /tasks/{id}` both verified.
14. Cross-project isolation of `mode`.
15-17. Regression: `test_api.py::test_create_task_invalid_mode` stays green, `422` creates no row, auth/existence (`403`/`404`) not bypassed; report this run’s actual Core total / skipped (symlink `SKIPPED` if present) and exit code — do not hard-code fixed totals.

### Changed files (Attempt 4 — implementation)

Modified:
- `docs/12_HANDOFF_CURRENT.md` — sync Status/Active Writer to WP-11 Attempt 4 READY_FOR_CODEX_REVIEW; correct full-Core stats to `193 collected / 192 passed / 1 skipped`, fix changed-files ledger (WP-11.md only Untracked, test file Untracked, 15_DOCUMENT_INDEX pre-existing excluded), and record symlink/skip reasons
- `docs/11_PROJECT_STATE.md` — sync Current Planned Task / Next Gate to WP-11 READY_FOR_CODEX_REVIEW Attempt 4; correct Core stats (`193 collected / 192 passed / 1 skipped`) and clarify WP-10 169 baseline to avoid confusion
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md` — WP-11 row → READY_FOR_CODEX_REVIEW Attempt 4 with `193 collected / 192 passed / 1 skipped`; CP-03 0/25 maintained

Untracked (new):
- `services/core/tests/test_wp11_work_mode.py` — 23 contract tests (tests-only; no product source change): enum semantics, domain default, API valid modes, default contract (omitted/null/"" → 201 REVIEW), illegal modes (422 + no row), persistence/reload round-trip, cross-project isolation, 403/404 not bypassed
- `docs/tasks/WP-11.md` — full WP-11 task document (Attempt 4: STATUS READY_FOR_CODEX_REVIEW; Implementation evidence with corrected Core stats)

Pre-existing (excluded):
- `docs/15_DOCUMENT_INDEX.md` — remains pre-existing dirty state, not WP-11 scope, excluded from commit

No product source, ADR, migration, dependency, or `services/core/src`/`apps/web` change in this Attempt 4 implementation. `git status` confirms only the files above.

### Protected areas

- ADR-001–010 (frozen; no change)
- `services/core/src/polynexus_core/domain/enums.py` `WorkMode` values, `services/core/src/polynexus_core/domain/models.py` `Task.mode` default, `services/core/src/polynexus_core/api/tasks.py` `422` detail, `services/core/src/polynexus_core/api/schemas.py` `TaskCreate.mode`, `services/core/src/polynexus_core/persistence/models.py`/`repository.py` conversion
- WP-08A/WP-08B WP-09B/WP-09C/WP-09D contracts and frontend baseline
- Migrations, Alembic, dependencies, storage, secrets, WebSocket, plugin/MCP infrastructure

### ADR impact

`NONE` — task document records existing `WorkMode` contract and proves it with tests; no enum, schema, persistence, or ADR text change. A change would require a new ADR/Decision Log entry and Human approval.

### Scope deviation

`NONE` for this task-doc creation. `docs/15_DOCUMENT_INDEX.md` is pre-existing and excluded; no product scope change.

### Known limitations

- WP-11 is contract-test scope only; it does not implement Discuss/Review/Validate business logic or Council/hard-gate semantics (WP-12–WP-13).
- Omitted-mode `REVIEW` default is per current code; a stricter policy needs Human/Codex decision before implementation.
- Frontend mode handling is out of scope for WP-11.

### Unverified / skipped

- Browser DOM / Playwright E2E: `UNVERIFIED/SKIPPED` (accepted waiver, deferred to browser-capable environment)
- Windows symlink containment: `UNVERIFIED/SKIPPED` (Windows policy, Human waiver)
- True concurrent HTTP duplicate-command execution: `UNVERIFIED` (repository-level CAS exists but concurrent HTTP not re-proven here)

### Verification (Attempt 4 — implementation, actual evidence)

- `pytest -q services/core/tests/test_wp11_work_mode.py` → **23 passed**, exit code `0`
- `pytest -q services/core/tests/test_api.py -k mode` → **1 passed** (`test_create_task_invalid_mode` regression preserved), exit code `0`
- `pytest -q -rA services/core` (full Core) → **193 collected, 192 passed, 1 skipped, 0 failed**, exit code `0` (1 skipped = Windows symlink creation policy denied; the pytest temp cleanup `PermissionError` at exit is a separate non-fatal environment warning, not a test failure; all WP-11 targets pass)
- `python scripts/validate_baseline.py` → **Baseline validation PASS** (11 required files; workflows valid; MV3 manifest valid), exit code `0`
- `git diff --check` → clean, exit code `0`
- `git status --short --branch` → ` M docs/12_HANDOFF_CURRENT.md`, ` M docs/15_DOCUMENT_INDEX.md` (pre-existing excluded), `?? docs/tasks/WP-11.md`, `?? services/core/tests/test_wp11_work_mode.py`, branch `feature/first-vertical-slice`, exit code `0`
- Product source not modified: `services/core/src` (enums/models/api/schemas/persistence/repository), `apps/web`, ADR, migrations, dependencies unchanged — verified via `git status` (no `services/core/src`/`apps/web` entries)

### Next

Historical pre-acceptance next step: Codex review followed by Human acceptance. That condition was satisfied on 2026-08-20; see the WP-11 Human Acceptance section below.

### Do not change

- Do not add a fourth top-level `WorkMode` (e.g., `DEVELOP`); `Develop` remains a Workflow action/Agent role per scope baseline.
- Do not change `services/core/src/polynexus_core/domain/enums.py`, `domain/models.py`, `api/tasks.py`, `api/schemas.py`, `persistence/models.py`, `persistence/repository.py`, `services/core` tests (except the new `test_wp11_work_mode.py`), `apps/web`, migrations, dependencies, storage, or secret handling.
- Do not stage, commit, push, or rewrite unrelated working-tree changes without explicit authorization.
- Do not relabel `UNVERIFIED/SKIPPED` limitations as `PASS` without a browser-capable rerun.

## WP-11 Human Acceptance and Git Checkpoint (Attempt 4) — ACCEPTED

- `TASK_ID`: `WP-11`
- `ATTEMPT`: `4`
- `BRANCH`: `feature/first-vertical-slice`
- `WRITER`: `OpenCode`
- `REVIEWER`: `Codex`
- `ANTIGRAVITY_STATUS`: `NOT_REQUIRED`
- `RESULT`: `PASS`; Codex independent review completed with no blocker/major finding.
- `HUMAN_ACCEPTANCE`: accepted on `2026-08-20`; Human authorized allowlist-only stage, commit, and push.
- WP-11 item progress: `100%`.
- Accepted project progress: `30/100`; accepted FVS progress: `22/22`. The roadmap does not define a standalone WP-11 point allocation inside CP-03, so no unsupported numeric points are added. CP-03 is `IN_PROGRESS`.

### Accepted Git allowlist

- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`
- `docs/tasks/WP-11.md`
- `services/core/tests/test_wp11_work_mode.py`

Excluded and left untouched: `docs/15_DOCUMENT_INDEX.md` (pre-existing dirty governance change).

### Acceptance evidence

- WP-11 contract tests: `23 passed`, exit code `0`.
- Existing mode regression: `1 passed`, exit code `0`.
- Full Core: `193 collected / 192 passed / 1 skipped`, exit code `0`; symlink skip and pytest temp cleanup warning remain explicitly environment-limited.
- `validate_baseline.py`: PASS, exit code `0`.
- `git diff --check`: clean, exit code `0`.

### Next

WP-12 task scope and acceptance tests are prepared below. OpenCode implementation is next. Preserve ADR-001–010, WP-11 contract tests, Browser E2E `UNVERIFIED/SKIPPED`, Windows symlink `UNVERIFIED/SKIPPED`, and concurrent HTTP `UNVERIFIED` records.

## WP-12 Task Document Creation (Attempt 1) — READY_FOR_IMPLEMENTATION

- `TASK_ID`: `WP-12`
- `ATTEMPT`: `1`
- `BRANCH`: `feature/first-vertical-slice`
- `WRITER`: `OpenCode`
- `REVIEWER`: `Codex`
- `ANTIGRAVITY_STATUS`: `NOT_REQUIRED` — Core orchestration/contract task; no Browser E2E scope
- `NEXT_OWNER`: `OpenCode` implementation → `Codex` review → `Human` acceptance
- `TASK_DOC`: `docs/tasks/WP-12.md`
- `STATUS`: `READY_FOR_IMPLEMENTATION`
- `GOAL`: Council 2–4 participant orchestration with independent analysis, Cross Review, Synthesis, bounded execution, and truthful partial-failure semantics.
- `ITEM_PROGRESS`: `0%` until implementation, deterministic tests, Codex PASS, and Human acceptance.
- `PROJECT_PROGRESS`: `30/100`; accepted FVS `22/22`; CP-03 `IN_PROGRESS`. No standalone WP-11 point allocation is defined; no unsupported points are added.

### Changed files for task preparation

- Modified: `docs/11_PROJECT_STATE.md`
- Modified: `docs/12_HANDOFF_CURRENT.md`
- Modified: `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`
- Untracked: `docs/tasks/WP-12.md`
- Pre-existing and excluded: `docs/15_DOCUMENT_INDEX.md`
- Product source, tests, ADRs, migrations, frontend, and dependencies: unchanged.

### Protected areas and architecture gate

- ADR-001–010, WP-08A/B, WP-09B/C/D, WP-11 WorkMode contract, Run lifecycle, evidence/secret boundaries, and Browser waiver remain protected.
- Preferred implementation uses existing WorkflowDefinition, PARALLEL_AI/CROSS_REVIEW/SYNTHESIS, Task/Run, RunEvent, Evidence, and repository boundaries.
- New Domain entities, migrations, public REST contracts, RunState/WorkMode/Evidence authority changes, or WP-09B lifecycle changes require `NEED_ACTION` and a recorded Human/Codex architecture decision before source changes.

### Verification for task preparation

- `git diff --check` — PASS, exit code `0`.
- `git status --short --branch` — branch `feature/first-vertical-slice`; only pre-existing `docs/15_DOCUMENT_INDEX.md` plus the three governance modifications and new `docs/tasks/WP-12.md`.
- No product source or test command was changed or run by this document-only preparation step.

### Known limitations / unverified

- Browser DOM / Playwright E2E: `UNVERIFIED/SKIPPED` and not a WP-12 gate.
- Windows symlink containment: `UNVERIFIED/SKIPPED` under the accepted Human waiver.
- True concurrent HTTP duplicate-command execution: `UNVERIFIED`.
- No production/vendor Council runtime is certified; reference/test adapters must remain deterministic and no-network.

### Next

OpenCode reads `docs/tasks/WP-12.md`, performs the architecture compatibility check, implements only the approved scope, runs the listed tests, updates this handoff with actual evidence, and returns `READY_FOR_CODEX_REVIEW`. No stage/commit/push without later Human authorization.

## WP-12 Implementation (Attempt 6) — READY_FOR_CODEX_REVIEW

- `TASK_ID`: `WP-12`
- `STATUS`: `READY_FOR_CODEX_REVIEW`
- `ATTEMPT`: `6`
- `BRANCH`: `feature/first-vertical-slice`
- `WRITER`: `OpenCode`
- `REVIEWER`: `Codex`
- `ANTIGRAVITY_STATUS`: `NOT_REQUIRED`
- `NEXT_OWNER`: `Codex` (independent review) → `Human` (acceptance)

### Goal

Implement and verify the first durable Council orchestration contract for three top-level work modes. Council supports independent participant analysis, cross review, synthesis, and truthful partial-failure representation without fabricating AI opinion into verified evidence.

### Architecture compatibility (PASSED)

Council is implemented additively using existing Task/Run/RunEvent/Evidence boundaries. No new persisted table, migration, REST endpoint, RunState, WorkMode, EvidenceType, or WP-09B lifecycle change is required.

- Participant analysis = Run executed via RunSupervisor + ReferenceRuntimeAdapter (no network)
- Cross-review = additional Run per completed participant
- Synthesis = final Run with AI_OPINION Evidence (not VERIFIED)
- Stage ordering/participant correlation = RunEvents on council run
- Plan durability = CouncilPlan stored as DOCUMENT_EVIDENCE

### Changed files

Modified:
- `docs/11_PROJECT_STATE.md` — sync WP-12 status
- `docs/12_HANDOFF_CURRENT.md` — WP-12 implementation handoff
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md` — WP-12 row → READY_FOR_CODEX_REVIEW

Untracked (new):
- `services/core/src/polynexus_core/council/__init__.py` — package exports
- `services/core/src/polynexus_core/council/models.py` — CouncilPlan (adds `round` + runtime `max_concurrency_observed`), CouncilParticipant, CouncilSpec, CouncilStage, ParticipantOutcome
- `services/core/src/polynexus_core/council/orchestrator.py` — CouncilOrchestrator (run_council, rerun_council, reload_council); bounded-parallel analysis via `asyncio.gather` + `asyncio.Semaphore` + per-participant isolated sessions, serialized SQLite persistence via `asyncio.Lock`
- `services/core/tests/test_wp12_council.py` — **36 contract tests** covering all WP-12 acceptance criteria (2 added in Attempt 6: timeout isolation, failure sanitization)
- `docs/tasks/WP-12.md` — task document

Pre-existing (excluded):
- `docs/15_DOCUMENT_INDEX.md` — pre-existing dirty state, excluded from commit

Stage allowlist / exclusions (Attempt 6):
- `__pycache__/*.pyc` (and any `*.pyc`) are **explicitly excluded** from changed-files and from any stage allowlist. The `council/` directory is enumerated **per source file** (above), never staged as a whole directory blob, so generated artifacts can never be swept in.

### Verification (Attempt 6 — actual evidence; statistics from this round's command output)

- `pytest -q services/core/tests/test_wp12_council.py` → **36 passed**, exit code `0`
- `pytest -q services/core/tests/test_wp09_execution_api.py services/core/tests/test_wp09_query_api.py` → **passed**, exit code `0`
- `pytest -q services/core` → **229 collected, 228 passed, 1 skipped**, exit code `0`
- `python scripts/validate_baseline.py` → **Baseline validation PASS**, exit code `0`
- `git diff --check` → clean, exit code `0`
- `git status --short --branch` → M docs/11_PROJECT_STATE.md, M docs/12_HANDOFF_CURRENT.md, M docs/15_DOCUMENT_INDEX.md (pre-excluded), M docs/28_MASTER_DEVELOPMENT_ROADMAP.md, ?? docs/tasks/WP-12.md, ?? services/core/src/polynexus_core/council/__init__.py, ?? services/core/src/polynexus_core/council/models.py, ?? services/core/src/polynexus_core/council/orchestrator.py, ?? services/core/tests/test_wp12_council.py; exit code `0`

### Protected areas

- ADR-001–010 (frozen; no change)
- RunState lifecycle rules in `run_lifecycle.py` (not modified; orchestrator respects them)
- WP-08A/B, WP-09B/C/D contracts and frontend baseline
- Migrations, dependencies, secrets, apps/web unchanged

### ADR impact

`NONE` — Council uses existing Run/RunEvent/Evidence boundaries; no enum, schema, persistence, or ADR change.

### Scope deviation

`NONE` — implementation stays within the approved WP-12 task document scope.

### Known limitations

- Browser DOM / Playwright E2E: `UNVERIFIED/SKIPPED`
- Windows symlink containment: `UNVERIFIED/SKIPPED`
- True concurrent HTTP duplicate-command execution: `UNVERIFIED`
- No production/vendor Council runtime certified; reference/test adapters remain deterministic and no-network

### Next

Codex independently reviews `services/core/tests/test_wp12_council.py` and the deterministic evidence (WP-12 36 passed, full Core 229 collected/228 passed/1 skipped, validate_baseline PASS, git diff/status clean). If Codex returns `PASS`, Human may authorize stage/commit/push and accept WP-12. Do not stage, commit, or push without explicit Human authorization. Generated `__pycache__/*.pyc` are excluded from any stage allowlist; the `council/` directory is listed per source file.

## WP-12 Attempt 7 — Codex FAIL repair (READY_FOR_CODEX_REVIEW)

- `TASK_ID`: `WP-12`
- `ATTEMPT`: `7`
- `STATUS`: `READY_FOR_CODEX_REVIEW`
- `BRANCH`: `feature/first-vertical-slice`
- `WRITER`: `OpenCode`
- `REVIEWER`: `Codex`
- `ANTIGRAVITY_STATUS`: `NOT_REQUIRED`
- `NEXT_OWNER`: `Codex` (independent re-review) → `Human` (acceptance)

### Codex FAIL → fix summary

Codex review of Attempt 6 returned `FAIL` with two MAJOR issues. Both are fixed in Attempt 7.

**MAJOR Issue 1 — non-COMPLETED Run mislabeled COMPLETED.**

`CouncilOrchestrator._run_analysis_stage()` previously unconditionally set
`participant.outcome = COMPLETED`, `participant.output_ref = run.id`, and
`evidence_to_persist = execution.evidence` after `RunSupervisor.execute_run()`
returned. `execute_run()` may return `RunExecution` with
`run.state in {FAILED, TIMED_OUT, CANCELLED}`.

Fix (`services/core/src/polynexus_core/council/orchestrator.py`):
- `RunState.COMPLETED` → `ParticipantOutcome.COMPLETED`, set `output_ref`, persist execution evidence only.
- `RunState.FAILED` → `ParticipantOutcome.FAILED` + sanitized fixed reason; no `output_ref`.
- `RunState.TIMED_OUT` → `ParticipantOutcome.TIMED_OUT` + sanitized fixed reason; no `output_ref`.
- `RunState.CANCELLED` → `ParticipantOutcome.CANCELLED` + sanitized fixed reason; no `output_ref`.
- Unexpected intermediate state → contained as FAILED.
- Non-COMPLETED participants never set `output_ref`, never enter Cross Review (the cross-review stage only selects `outcome is COMPLETED`), and never produce fabricated consensus (synthesis stays truthful partial or truthful failed).

**MAJOR Issue 2 — sanitized failure breaking Run event lifecycle.**

`_apply_sanitized_failure()` previously did `run.state = RunState.FAILED` directly and
only replaced an already-existing FAILED event. When the adapter-boundary exception
occurred while the Run was still CREATED/STARTING/RUNNING (no FAILED event), the
persisted Run state became FAILED while the last event stayed RUNNING, violating
ADR-007 durable event history.

Fix (`services/core/src/polynexus_core/council/orchestrator.py`):
- Added `_sanitize_terminal_reason(run, reason)` to replace the reason on an
  already-legal terminal event (FAILED/TIMED_OUT/CANCELLED) while preserving the
  original event id / occurred_at / ordering and terminal state. Used for terminal
  states returned by `execute_run()` (whose reason may come from raw `status.error`).
- Rewrote `_apply_sanitized_failure(run, reason)`:
  - If `run.state in {COMPLETED, TIMED_OUT, CANCELLED}` → returns WITHOUT regressing
    a terminal Run to FAILED (lifecycle protected).
  - If a raw FAILED event already exists → sanitizes it in place (id/occurred_at/order preserved).
  - Otherwise applies the legal lifecycle CREATED→STARTING→RUNNING→FAILED (or the
    available prefix) so exactly one FAILED terminal event is appended and
    `state`/`updated_at` stay consistent with the last event.

**Supervisor hardening (WP-09B scope impact noted).**

`services/core/src/polynexus_core/runtime/supervisor.py::execute_run()` previously
called `version_info()` inside `_build_execution_from_existing()` *after* the
`COMPLETED` transition, so a `version_info()` failure could leave a COMPLETED event
with the Run state later regressed to FAILED. Aligned `execute_run()` with the
already-safe `execute_claimed_run()` pattern: fetch `runtime_version` via a guarded
`try/except` *before* `run.transition(RunState.COMPLETED)`, transitioning to FAILED
with the public-safe reason on failure. No new RunState/EvidenceType/migration/contract.

### Changed files (Attempt 7)

Modified (product source):
- `services/core/src/polynexus_core/council/orchestrator.py` — `_run_analysis_stage` outcome mapping; rewritten `_apply_sanitized_failure`; new `_sanitize_terminal_reason`.
- `services/core/src/polynexus_core/runtime/supervisor.py` — `execute_run()` fetches `version_info()` before COMPLETED (mirrors `execute_claimed_run`).

Modified (governance):
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`
- `docs/tasks/WP-12.md`

Untracked (new/changed):
- `docs/tasks/WP-12.md`
- `services/core/src/polynexus_core/council/` (package: `__init__.py`, `models.py`, `orchestrator.py`)
- `services/core/tests/test_wp12_council.py` — now **43 contract tests** (7 new deterministic adapter-boundary failure tests, each verifying close/reopen reload, state/terminal-event consistency, single terminal event, no raw secret, no fabricated Finding/Evidence/Artifact, failed participant without `output_ref`, no Cross Review entry, truthful partial/failed synthesis).

Pre-existing (excluded):
- `docs/15_DOCUMENT_INDEX.md` — pre-existing dirty state, excluded from commit.

### Verification (Attempt 7 — actual evidence; statistics from this round's command output)

- `pytest -q services/core/tests/test_wp12_council.py` → **43 passed**, exit code `0`
- `pytest -q services/core/tests/test_wp09_execution_api.py services/core/tests/test_wp09_query_api.py` → **passed**, exit code `0`
- `pytest -q services/core` → **236 collected, 235 passed, 1 skipped**, exit code `0`
- `python scripts/validate_baseline.py` → **Baseline validation PASS**, exit code `0`
- `git diff --check` → clean, exit code `0`
- `git status --short --branch` → M docs/11/12/15/28, M services/core/src/polynexus_core/runtime/supervisor.py, ?? docs/tasks/WP-12.md, ?? services/core/src/polynexus_core/council/, ?? services/core/tests/test_wp12_council.py; exit code `0`

(The pytest temp-dir `PermissionError` at interpreter exit is a non-fatal Windows
environment warning; all test commands returned exit code `0`.)

### Protected areas

- ADR-001–010 (frozen; no change)
- RunState lifecycle rules in `run_lifecycle.py` (not modified; orchestrator respects them)
- WP-08A/B, WP-09B/C/D contracts and frontend baseline
- Migrations, dependencies, secrets, apps/web unchanged
- No new RunState / WorkMode / EvidenceType / REST endpoint / migration introduced

### ADR impact

`NONE` — Council uses existing Run/RunEvent/Evidence boundaries; the supervisor change
is an internal lifecycle hardening that mirrors the already-accepted `execute_claimed_run`
pattern (WP-09B Attempt 5). No enum, schema, persistence, or ADR text change.

### Scope deviation

`NONE` for product source. The supervisor `execute_run()` change is within WP-09B
runtime-adapter lifecycle containment scope and was required to satisfy Issue 2
("version_info() 若可能在完成後失敗… 在 terminal completion 前先取得"); documented here per the
handoff rule requiring explicit scope-impact disclosure for WP-09B supervisor edits.

### Known limitations

- Browser DOM / Playwright E2E: `UNVERIFIED/SKIPPED`
- Windows symlink containment: `UNVERIFIED/SKIPPED`
- True concurrent HTTP duplicate-command execution: `UNVERIFIED`
- No production/vendor Council runtime certified; reference/test adapters remain deterministic and no-network

### Next

Codex independently re-reviews the Attempt 7 fixes and the new deterministic boundary
tests. If Codex returns `PASS`, Human may authorize stage/commit/push and accept WP-12.
Do not stage, commit, or push without explicit Human authorization. Generated
`__pycache__/*.pyc` are excluded from any stage allowlist.

## WP-12 Attempt 8 — Codex FAIL repair (READY_FOR_CODEX_REVIEW)

- `TASK_ID`: `WP-12`
- `ATTEMPT`: `8`
- `STATUS`: `READY_FOR_CODEX_REVIEW`
- `BRANCH`: `feature/first-vertical-slice`
- `WRITER`: `OpenCode`
- `REVIEWER`: `Codex`
- `ANTIGRAVITY_STATUS`: `NOT_REQUIRED`
- `NEXT_OWNER`: `Codex` (independent re-review) → `Human` (acceptance)

### Codex FAIL → fix summary (Attempt 7 → Attempt 8)

Codex review of Attempt 7 returned `FAIL` with two further MAJOR issues. Both fixed in Attempt 8.

**MAJOR Issue 1 — raw `status.error` leaked into persisted `run.result`.**

`RunSupervisor.execute_run()` returned `RuntimeResult(summary=status.error or status.state)`
for `FAILED`/`TIMED_OUT` terminal statuses, and `SqlRunRepository` persisted
`run.result.summary` into `RunRow.result_summary` (raw secret). The orchestrator
previously only sanitized the terminal event reason and set `evidence_to_persist` to
empty, but left `run.result` populated.

Fix (`services/core/src/polynexus_core/council/orchestrator.py`): in the analysis
`else` branch, every non-`COMPLETED` outcome (`FAILED`/`TIMED_OUT`/`CANCELLED` and the
fallback) now sets `run.result = None` before persistence. The sanitized terminal event
reason is preserved. No dangling `finding_ids`/`evidence_ids`/`artifact_ids` survive
because `run.result` is `None` (the repository serializes those from `run.result`).
`evidence_to_persist` remains empty, so no `RUNTIME_EVIDENCE` is written for failed runs.

**MAJOR Issue 2 — generic exception handler rewrote an already-terminal TIMED_OUT/CANCELLED participant to FAILED.**

The generic `except Exception` handler unconditionally called `_apply_sanitized_failure`
(running its no-regress guard) and set `ParticipantOutcome.FAILED`. When
`status()` returned `TIMED_OUT`/`CANCELLED` and a *later* boundary (`version_info()`)
raised inside `RunSupervisor._build_execution_from_existing`, `run.state` was already
`TIMED_OUT`/`CANCELLED`; the participant outcome became `FAILED` while the Run stayed
`TIMED_OUT`/`CANCELLED` — inconsistent.

Fix (`services/core/src/polynexus_core/council/orchestrator.py`): the generic handler
now maps the participant outcome to the Run's ACTUAL terminal state:
- `run.state == FAILED` → `ParticipantOutcome.FAILED` + sanitized FAILED reason
- `run.state == TIMED_OUT` → `ParticipantOutcome.TIMED_OUT` + sanitized timeout reason
- `run.state == CANCELLED` → `ParticipantOutcome.CANCELLED` + sanitized cancel reason
- `CREATED`/`STARTING`/`RUNNING` → legal lifecycle to a single FAILED terminal event
In all branches `run.result` is set to `None`. An already-terminal `TIMED_OUT`/`CANCELLED`
Run is never regressed to `FAILED`, and its terminal event reason is sanitized in place
(id/occurred_at/order preserved).

### Changed files (Attempt 8)

Modified (product source):
- `services/core/src/polynexus_core/council/orchestrator.py` — analysis `else` branch nulls `run.result` for non-COMPLETED; generic exception handler maps outcome to `run.state`.

Modified (governance):
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`
- `docs/tasks/WP-12.md`

Untracked (new/changed):
- `docs/tasks/WP-12.md`
- `services/core/src/polynexus_core/council/` (`__init__.py`, `models.py`, `orchestrator.py`)
- `services/core/tests/test_wp12_council.py` — now **45 contract tests** (2 new: `test_status_error_not_persisted_in_result` [parametrized FAILED/TIMED_OUT with secret in status.error, close/reopen verified], `test_status_then_version_info_raises_keeps_terminal` [parametrized TIMED_OUT/CANCELLED with later version_info secret exception]; the 7 Attempt-7 boundary tests now also assert `child.result is None`).

Pre-existing (excluded):
- `docs/15_DOCUMENT_INDEX.md` — pre-existing dirty state, excluded from commit.

### Verification (Attempt 8 — actual evidence)

- `pytest -q services/core/tests/test_wp12_council.py` → **45 passed**, exit code `0`
- `pytest -q services/core/tests/test_wp09_execution_api.py services/core/tests/test_wp09_query_api.py` → **passed**, exit code `0`
- `pytest -q services/core` → **238 collected, 237 passed, 1 skipped**, exit code `0`
- `python scripts/validate_baseline.py` → **Baseline validation PASS**, exit code `0`
- `git diff --check` → clean, exit code `0`
- `git status --short --branch` → M docs/11/12/15/28, M services/core/src/polynexus_core/runtime/supervisor.py, ?? docs/tasks/WP-12.md, ?? services/core/src/polynexus_core/council/, ?? services/core/tests/test_wp12_council.py; exit code `0`

(The pytest temp-dir `PermissionError` at interpreter exit is a non-fatal Windows
environment warning; all test commands returned exit code `0`.)

### Protected areas

- ADR-001–010 (frozen; no change)
- RunState lifecycle rules in `run_lifecycle.py` (not modified; orchestrator respects them)
- WP-08A/B, WP-09B/C/D contracts and frontend baseline
- Migrations, dependencies, secrets, apps/web unchanged
- No new RunState / WorkMode / EvidenceType / REST endpoint / migration introduced

### ADR impact

`NONE` — Council uses existing Run/RunEvent/Evidence boundaries; no enum, schema, persistence, or ADR text change.

### Scope deviation

`NONE` for product source. The `supervisor.py` change (version_info before COMPLETED) was made in Attempt 7 within WP-09B lifecycle-containment scope and remains in effect; no additional supervisor change in Attempt 8.

### Known limitations

- Browser DOM / Playwright E2E: `UNVERIFIED/SKIPPED`
- Windows symlink containment: `UNVERIFIED/SKIPPED`
- True concurrent HTTP duplicate-command execution: `UNVERIFIED`
- No production/vendor Council runtime certified; reference/test adapters remain deterministic and no-network

### Next

Codex independently re-reviews the Attempt 8 fixes and the new deterministic tests
(result-leak prevention; terminal-state/outcome consistency under a later boundary
exception). If Codex returns `PASS`, Human may authorize stage/commit/push and accept
WP-12. Do not stage, commit, or push without explicit Human authorization. Generated
`__pycache__/*.pyc` are excluded from any stage allowlist.

## WP-13 Attempt 1 — READY_FOR_CODEX_REVIEW

- `TASK_ID`: `WP-13`
- `ATTEMPT`: `1`
- `STATUS`: `READY_FOR_CODEX_REVIEW`
- `BRANCH`: `feature/first-vertical-slice`
- `WRITER`: `OpenCode`
- `REVIEWER`: `Codex`
- `ANTIGRAVITY_STATUS`: `NOT_REQUIRED`
- `NEXT_OWNER`: `Codex` (independent review) → `Human` (acceptance)
- `TASK_DOC`: `docs/tasks/WP-13.md`
- `HANDOFF_DOC`: `docs/12_HANDOFF_CURRENT.md`

### Goal

Implement the first deterministic workflow-gate contract: EVIDENCE_CHECK hard-gate
evaluation, HUMAN_GATE explicit decision handling, verified-verdict rules, and
truthful durable results. AI opinion, synthesis, or council output must never
convert a failed/missing/pending gate into PASS/VERIFIED.

### Architecture compatibility (PASSED)

WP-13 is implemented additively over existing Task/Run/Evidence boundaries.

- **WorkflowStep extended** (`services/core/src/polynexus_core/workflows/models.py`):
  added `parameters: Mapping[str, object]` to retain EVIDENCE_CHECK `hard_gates`,
  HUMAN_GATE `human_gate` id, TOOL `profile`, PARALLEL_AI `roles`, etc. This is
  an additive field with `default_factory=dict` — all existing workflows without
  extra params continue to load unchanged (review-minimal, release-validation
  validated by `validate_baseline.py`). No new model/table/migration.

- **Gate evaluation engine** (`services/core/src/polynexus_core/workflows/gates.py`):
  new module providing `validate_workflow_gates()`, `evaluate_workflow_gates()`,
  `persist_gate_report()`, and `reload_gate_report()`. Uses existing
  `EvidenceRepository.list_by_run()` to read `TOOL_EVIDENCE`/`HUMAN_EVIDENCE`
  scoped to the current Task/Run. Verdict stored as `DOCUMENT_EVIDENCE` with
  source `"workflow-gate-evaluation"` (same durable boundary as CouncilPlan).
  No new REST endpoint, schema, or public field.

- **No changes to**: ADR-001–010, RunState/WorkMode/EvidenceType enums, WP-09B
  lifecycle/idempotency, WP-12 council, ExecutionService, RunSupervisor,
  migrations, dependencies, frontend, or secrets.

### Gate semantics implemented

| Scenario | Gate outcome | Verdict | Authority |
|---|---|---|---|
| TOOL_EVIDENCE PASS + matching gate id | PASS | continues | continues |
| TOOL_EVIDENCE FAIL | FAIL | FAIL | none |
| Missing / malformed / cross-task / cross-run | NEED_ACTION | NEED_ACTION | none |
| AI_OPINION claims PASS | NEED_ACTION (not satisfied) | depends | none |
| HUMAN_GATE absent | HUMAN_DECISION | HUMAN_DECISION | none |
| HUMAN_GATE approve + all gates PASS | PASS | PASS | verified-deterministic |
| HUMAN_GATE reject | FAIL | FAIL | none |
| HUMAN_GATE ambiguous decision | HUMAN_DECISION | HUMAN_DECISION | none |

### Changed files

**Modified (product source):**
- `services/core/src/polynexus_core/workflows/models.py` — added `parameters` field to `WorkflowStep`; `from_mapping()` captures all non-identity step keys.

**Modified (governance):**
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- `docs/15_DOCUMENT_INDEX.md` (pre-existing dirty state, excluded from commit)
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`
- `docs/tasks/WP-12.md`

**Untracked (new):**
- `services/core/src/polynexus_core/workflows/gates.py` — deterministic gate evaluation engine (validate, evaluate, persist, reload)
- `services/core/tests/test_wp13_workflow_gates.py` — **25 contract tests** covering the full acceptance matrix
- `workflows/builtin/verified-gate.yaml` — builtin workflow with EVIDENCE_CHECK + HUMAN_GATE steps (validated by `validate_baseline.py`)
- `docs/tasks/WP-13.md` — task document

### Verification (Attempt 1 — actual evidence)

- `pytest -q services/core/tests/test_wp13_workflow_gates.py` → **25 passed**, exit code `0`
- `pytest -q services/core/tests/test_wp12_council.py services/core/tests/test_wp09_execution_api.py services/core/tests/test_wp09_query_api.py` → **107 passed**, exit code `0`
- `pytest -q services/core` → **264 collected, 264 passed, 1 skipped**, exit code `0`
- `python scripts/validate_baseline.py` → **Baseline validation PASS**, exit code `0`
- `git diff --check` → clean, exit code `0`
- `git status --short --branch` → (listed above); exit code `0`

(The pytest temp-dir `PermissionError` at interpreter exit is a non-fatal Windows
environment warning; all test commands returned exit code `0`.)

### Test coverage mapping (acceptance matrix items 1–15)

| Item | Test | Behavior |
|---|---|---|
| 1 | `test_valid_workflow_preserves_gate_config` | Load verified-gate.yaml; assert hard_gates, human_gate, validate returns [] |
| 2 | `test_invalid_gate_config_fails_closed` | 5 parametrized cases: duplicate gate id, empty hard_gates, missing depends_on, unsupported type, duplicate step id |
| 3 | `test_required_tool_evidence_pass_satisfies_gate` | Two TOOL_EVIDENCE PASS → both gates PASS |
| 4 | `test_tool_evidence_fail_blocks_pass` | TOOL_EVIDENCE FAIL blocks; AI opinion override rejected |
| 5 | `test_missing_evidence_is_need_action` + `test_cross_run_evidence_rejected` + `test_cross_task_evidence_rejected` + `test_malformed_tool_evidence_is_need_action` | Missing/cross-run/cross-task/malformed → NEED_ACTION |
| 6 | `test_ai_opinion_never_satisfies_gate` | AI_OPINION PASS → NEED_ACTION, not PASS |
| 7 | `test_human_gate_pending_without_decision` | No HUMAN_EVIDENCE → HUMAN_DECISION |
| 8 | `test_human_approval_yields_verified_pass` + `test_human_rejection_blocks_verified` | Approve → verified-deterministic PASS; Reject → FAIL |
| 9 | `test_verified_impossible_with_ai_only_evidence` | AI-only → verdict not PASS |
| 10 | `test_council_cannot_mutate_gate_verdict` | Council run on same task; gate verdict unchanged |
| 11 | `test_gate_report_close_reopen_durable` | Evaluate → persist Evidence → close → reopen → reload → equal |
| 12 | `test_idempotent_replay_no_fabricated_evidence` | Two evaluate calls → equal; no evidence fabricated by evaluation |
| 13 | `test_terminal_required_run_no_verified_verdict` | Parametrized FAILED/TIMED_OUT/CANCELLED → not PASS; run state unchanged |
| 14 | `test_secret_not_in_gate_result_or_persisted` | TOOL_EVIDENCE with secret → secret absent from report + persisted record |
| 15 | WP-12 + WP-09 regression | 107 passed (existing tests green) |

### Protected areas

- ADR-001–010 (frozen; no change)
- RunState lifecycle rules in `run_lifecycle.py` (not modified)
- WP-08A/B, WP-09B/C/D contracts and frontend baseline (unchanged)
- WP-11 WorkMode contract (unchanged)
- WP-12 council orchestration (unchanged)
- Migrations, dependencies, secrets, apps/web (unchanged)
- No new RunState / WorkMode / EvidenceType / REST endpoint / migration introduced

### ADR impact

`NONE` — gate evaluation uses existing `EvidenceType`/`EvidenceStatus` values and
persists verdict as `DOCUMENT_EVIDENCE` (same boundary as CouncilPlan). The
`WorkflowStep.parameters` extension is additive (default `{}`), schema-valid
(`additionalProperties: true`), and backward-compatible. No ADR text change.

### Scope deviation

`NONE` — implementation stays within the approved WP-13 task document scope. The
`WorkflowStep` extension is the minimal change required to retain gate config
(`hard_gates`, `human_gate`) that the YAML schema already permits but the old
`from_mapping()` dropped.

### Known limitations

- Browser DOM / Playwright E2E: `UNVERIFIED/SKIPPED`
- Windows symlink containment: `UNVERIFIED/SKIPPED`
- True concurrent HTTP duplicate-command execution: `UNVERIFIED`
- No production/vendor runtime is certified; reference/test adapters remain deterministic and no-network
- CP-03 point allocation is deferred until CP-03 completion per Human decision

### UNVERIFIED / SKIPPED

- Browser DOM / Playwright E2E: `UNVERIFIED/SKIPPED` under accepted Human waiver
- Windows symlink containment: `UNVERIFIED/SKIPPED` under accepted Human waiver
- True concurrent HTTP duplicate-command execution: `UNVERIFIED`

### Next

Codex independently reviews the WP-13 gate evaluation engine, workflow schema
extension, and deterministic contract tests. If Codex returns `PASS`, Human may
authorize stage/commit/push and accept WP-13. Do not stage, commit, or push
without explicit Human authorization. Generated `__pycache__/*.pyc` are excluded
from any stage allowlist.

---

## Gate 1.5 — Human Decision / Canonical Baseline Review（2026-09-09 delta）

- TASK_ID: PRODUCT-REFOUNDATION-GATE-1.5; ATTEMPT: 1
- TASK_DOC: docs/reviews/POLYNEXUS_GATE_1_5_HUMAN_DECISION_BASELINE_2026-09-09.md
- HANDOFF_DOC: docs/12_HANDOFF_CURRENT.md
- Goal: reconcile canonical baseline and review H01–H18; planning review only.
- BRANCH: feature/first-vertical-slice; HEAD: b87a0dc780e5d9a3bba083dbaf9552ca52508f9a
- WRITER: Codex（本輪報告）；REVIEWER: Codex（architecture review；文件未經第二位獨立 reviewer 驗證）
- ANTIGRAVITY_STATUS: NOT_REQUIRED — 本輪僅分析／文件，未修改 UI，未宣稱 browser journey PASS。
- Verdict: NEED_MORE_HUMAN_DECISIONS. Recommended baseline: f34e6b29ae9e7326d1d44b9b03756b450809928f, origin/feature/g24-g30-development-completion-routing; pending Human adoption.
- Completed: fresh origin/backup inspection and fetch; lineage and dirty-work inventory; 23-section report, H01–H18, B01–B10, separate Stability/Product P0, SQLite FK vs WAL review.
- This-task changed files: new report above; appended this handoff delta. No product code, Scope Baseline, ADR or PRD edits. Existing tracked/untracked work is preserved.
- Full pre-existing changed-files including untracked: artifacts/verification/gate1_5-20260909/preserved-files-before.json (2,010 paths with SHA-256); report §2.4 provides grouped disposition. This local ignored inventory is not a portable Git checkpoint.
- Tests/results: Git status/remote/lineage/product-diff commands exit 0; origin fetch first sandbox attempt exit 1, approved retry exit 0; backup fetch exit 0. Pre-handoff hash comparison exit 0, 0 existing-file changes. Full product tests, real providers, live browser, live DB audit and fresh f34 clone SKIPPED this Gate; Gate 1 results remain historical only. Report validation/preservation result: artifacts/verification/gate1_5-20260909/validation.json.
- Known blockers: HD-1 exact baseline/overlay adoption; HD-2 local-personal + managed-worktree/trust scope; HD-3 candidate/evidence/acceptance semantics and Human gate planning direction. Known product Stability/Working P0 remain unfixed.
- ADR impact: proposals only; no frozen contract changed. Scope deviation: none. Remaining limitations/unverified items: report §2.7, §18 and §23.
- NEXT_ACTION: Human reviews HD-1–HD-3; NEXT_OWNER: Human.
- NEXT_PROMPT: Review the Gate 1.5 report and explicitly adopt or revise HD-1–HD-3. Do not start implementation or overwrite local work.
- Scope / stop condition: Gate 1.5 is complete as an assessment deliverable; stop and wait for Human direction before Gate 2 planning. This prompt is not delegation permission.
- Do Not Change / protected areas: preserve all existing dirty/untracked work; do not reset/discard, blanket merge overlays, repair/prune worktrees, change formal Scope/ADR/PRD, stage/commit/push or start Target Architecture implementation under this task.
---

## Gate 1.5 Human approval → Gate 2 planning（2026-09-09 delta）

- TASK_ID: PRODUCT-REFOUNDATION-GATE-2-PLANNING; ATTEMPT: 1
- TASK_DOC: docs/reviews/GATE_2_TARGET_PRODUCT_ARCHITECTURE_PLANNING.md
- INPUT_BASELINE: docs/reviews/GATE_2_INPUT_BASELINE.md
- HANDOFF_DOC: docs/12_HANDOFF_CURRENT.md
- Goal: record approved HD-1–HD-3 and begin Target Product / Architecture Planning; no implementation.
- BRANCH: feature/first-vertical-slice; working HEAD: b87a0dc780e5d9a3bba083dbaf9552ca52508f9a (unchanged).
- Canonical design/read SHA: f34e6b29ae9e7326d1d44b9b03756b450809928f. Human adoption is now APPROVED; it does not authorize checkout/reset/rebase/merge, dirty/untracked cleanup or branch integration.
- Human status: Gate 1.5 ACCEPTED AS PLANNING INPUT; HD-1 APPROVED; HD-2 APPROVED WITH BOUNDARY; HD-3 APPROVED WITH CLARIFICATION. Previous Gate 1.5 NEED_MORE_HUMAN_DECISIONS is historical and superseded for planning entry.
- Current status: READY_FOR_GATE_2 (input); Gate 2 PLANNING DRAFT / NOT FROZEN. Product capabilities not accepted; implementation not authorized.
- WRITER: Codex (documents); REVIEWER: independent planning review NOT_RUN; local document/preservation checks only.
- ANTIGRAVITY_STATUS: NOT_REQUIRED — no product/UI changes or browser acceptance claims.
- Completed: 17-part approved input; target journey, responsibility/identity/transaction/recovery proposals, frozen-node mapping, dependency plan, migration/ADR impact, benchmark/pilot integration.
- This-task changed-files allowlist: docs/reviews/GATE_2_INPUT_BASELINE.md (new); docs/reviews/GATE_2_TARGET_PRODUCT_ARCHITECTURE_PLANNING.md (new); docs/12_HANDOFF_CURRENT.md (append only).
- Complete pre-existing modified/untracked inventory: artifacts/verification/gate2-planning-20260909/preserved-files-before.json (2,011 existing paths). Added files are the two above. Local ignored diagnostics are not a portable baseline.
- Checks: status/show/ls-tree/rev-parse/cat-file commands exit 0; schema minimum nodes all present at exact SHA. Document coverage, relative links, original-file hashes and handoff prefix preservation checked by artifacts/verification/gate2-planning-20260909/validation.json. Product tests / real executor / browser / DB migration: SKIPPED (planning only).
- Known issue: formal Scope and historical SA/ADR status paragraphs differ from new priorities/current code; see planning impact matrix. Necessary Stability/Product P0 remain unfixed.
- ADR impact: proposals for existing boundaries only; frozen ADR/Scope/PRD/Decision Log unchanged. Human-approved direction is recorded in INPUT_BASELINE, not hidden in handoff. Scope deviation: none.
- Unverified/pending design: candidate encoding, detailed command/schema contracts, concrete D11 principal/attestation proposal, process recovery handle, real executor compatibility, migration rehearsal. These do not reopen HD-1–HD-3.
- NEXT_ACTION: review/refine Gate 2 draft into the concrete contract and migration planning package; NEXT_OWNER: Human / Codex planning, according to Human direction.
- NEXT_PROMPT: Continue Gate 2 planning from the approved input and exact read baseline; resolve the draft contract/auth/recovery/migration design items without product implementation or formal ADR edits.
- Stop condition: this input + initial planning deliverable is ready for review; not a declaration that Gate 2 final architecture is approved. NEXT_PROMPT is not delegation permission.
- Do Not Change / protected areas: preserve existing dirty/untracked/historical overlays, Gate 1/1.5 reports and frozen official specs; no checkout/reset/rebase/merge/cleanup, worktree creation/repair, stage/commit/push, new release baseline or implementation under this turn.
---

## Gate 2 Contract Closure — 2026-09-09 delta

- TASK_ID: PRODUCT-REFOUNDATION-GATE-2-CONTRACT-CLOSURE; ATTEMPT: 1
- TASK_DOC: docs/reviews/GATE_2_CONTRACT_ARCHITECTURE_PACKAGE.md
- HANDOFF_DOC: docs/12_HANDOFF_CURRENT.md
- Goal: close the eight Human-specified contracts and provide the architecture review package; planning only.
- Human input: GATE_2_INPUT_BASELINE ACCEPTED; target planning ACCEPTED AS PLANNING DRAFT; CONTINUE; architecture NOT FROZEN; implementation NOT AUTHORIZED.
- BRANCH: feature/first-vertical-slice; working HEAD: b87a0dc780e5d9a3bba083dbaf9552ca52508f9a (unchanged).
- Canonical design/read SHA: f34e6b29ae9e7326d1d44b9b03756b450809928f; no checkout, fetch, merge, rebase, reset or overlay cleanup this turn.
- WRITER: Codex (contract document); REVIEWER: independent architecture-package review NOT_RUN; local consistency/document/preservation checks only.
- ANTIGRAVITY_STATUS: NOT_REQUIRED — planning only; no UI implementation/browser PASS claim.
- Verdict: READY_FOR_GATE_2_HUMAN_ARCHITECTURE_REVIEW. This is not architecture freeze, product acceptance or implementation authorization.
- Completed: termination vs candidate rejection; Model A/B comparison with Model B recommended; requirement/applicability/outcome/validity separation; accepted managed-worktree consumption; D11-A-LP proposal; REST polling + durable facts/events; portability/reconstruction invariant; brand-neutral real executor feasibility; migration/ADR/test/dependency mapping.
- This-task changed-files: docs/reviews/GATE_2_CONTRACT_ARCHITECTURE_PACKAGE.md (new); docs/12_HANDOFF_CURRENT.md (append only).
- Full pre-existing modified/untracked inventory: artifacts/verification/gate2-contract-closure-20260909/preserved-files-before.json (2,013 paths). The new package is additional; all existing source/spec/review files are protected. Ignored local validation artifacts are not a portable baseline.
- Checks: Git status/show/ls-tree and inventory commands exit 0; document sections/links, exact SHA, original-file hashes, handoff prefix and empty staged state verified in artifacts/verification/gate2-contract-closure-20260909/validation.json.
- Product tests / real executor / browser/auth integration / migration / export reconstruction: SKIPPED — contracts not implemented; no product PASS claimed.
- ADR impact: proposed CP-IDENTITY/DECISION/COMMAND/EXECUTION/MONITOR/VERIFICATION/PORTABILITY, recorded in package, not official ADR entries. Scope/ADR/PRD/Decision Log and accepted input/draft unchanged. Scope deviation: none.
- Known limitations: necessary Stability/Product P0 unfixed; exact runtime feasibility and D11 defenses still require implementation evidence after authorization; local-personal scope excludes hostile same-OS-principal protection.
- Open Human review items: HC-1 Model B; HC-2 D11-A-LP; HC-3 consumption/monitor scope; HC-4 package contract/migration/test plan. These are adoption choices, not new requirements elicitation or implementation permission.
- NEXT_ACTION: Human architecture review of the package; NEXT_OWNER: Human.
- NEXT_PROMPT: Review the Gate 2 contract architecture package and adopt or revise HC-1–HC-4. Preserve architecture NOT FROZEN and implementation NOT AUTHORIZED unless separately and explicitly changed by Human.
- Stop condition: package delivered; stop and wait for Human Review. NEXT_PROMPT is not delegation permission.
- Do Not Change: preserve dirty/untracked/historical overlays and prior reports; no code/schema, official frozen-spec edits, new release baseline, worktree mutations, stage/commit/push or automatic continuation into implementation.