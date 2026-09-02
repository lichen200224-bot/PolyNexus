# G19-G23 Five-Goal Execution Routing

## Program terminal outcome — 2026-09-02

- `G23_DECISION=ACCEPT` was explicitly provided by the Human.
- `PROGRAM_STATUS=HUMAN_ACCEPTED / PASS / COMPLETE`.
- Terminal SHAs: G19
  `1799994514fc5dc46aef752ab61a3d96583ea3ad`; G20
  `48062f1cae608785a39539e1a7bfca5d6726a92e`; G21
  `ada5e9c8b4873aad4c53c74198171740d376d926`; G22/final accepted SHA
  `0eb56a986e97a45854bd6ddd419c114845ce51f4`.
- `CROSS_MACHINE_CONTINUATION_READY=YES` for the accepted bounded checkpoint.
- Formal development progress is `59/100`. A later Human-confirmed reallocation
  preserves this total under CP-00 `8`, CP-02 `22`, CP-03 `27`, CP-04 `20`,
  CP-05 `13`, and CP-06 `10`; Competition is note-only/non-scoring. G19 and G22
  contribute through CP-06 without double counting. Fresh CDP is `NEED_ACTION`; native
  MV3 and authenticated live-vendor journeys remain `UNVERIFIED`; vendor
  certification is `NOT_CLAIMED`.
- This terminal record closes the five-goal routing program. The separate
  successor routing is G24–G30; G24 remains `WAIT_FOR_PLANNING_CHECKPOINT` until
  that package has an approved remote SHA and clean-clone proof. This is not
  recursive delegation permission and does not start another goal or runtime.

## 1. Program objective

Close the remaining gap between the promoted release candidate and a final,
Human-verifiable PolyNexus V1 acceptance checkpoint. The five goals are ordered
by dependency and must preserve truthful provenance, current deterministic
evidence, and the Single Active Writer rule.

This file is the durable routing package for five new Codex conversations. Each
prompt below is self-contained enough to start from repository evidence rather
than conversation memory.

## 2. Authoritative starting memory

- Workspace: `D:\AI學習教材\PolyNexus`.
- Read first: `AGENTS.md`, `docs/11_PROJECT_STATE.md`,
  `docs/12_HANDOFF_CURRENT.md`, and this task file. Then read only the 1–3
  directly relevant specifications or implementation areas.
- Approved promoted checkpoint:
  `backup/feature/first-vertical-slice@730912b5a3e19449c355975485f1fe77350a458a`.
- The promoted checkpoint is backed by a clean-clone verification. Its current
  non-browser evidence is: Core 548 collected, 547 passed and one visible
  Windows symlink-policy skip, exit `0`; browser-companion Node tests 9 passed,
  exit `0`; baseline and governance validators exit `0`.
- Current unresolved acceptance items: clean-clone Web Vitest/build could not
  run because dependencies were absent and registry access was unavailable;
  WP21 real-browser/vendor journeys and browser failure paths remain
  `DEFERRED / UNVERIFIED`; RC status is provisional with disclosed limitations.
- The primary checkout is a protected dirty lane at
  `feature/first-vertical-slice@b87a0dc780e5d9a3bba083dbaf9552ca52508f9a`.
  It contains mixed tracked/untracked ownership. Never reset, clean, overwrite,
  or silently fold it into the promoted checkpoint.
- `docs/31_COMPATIBILITY_MATRIX.md` and `docs/32_KNOWN_LIMITATIONS.md` exist in
  the promoted checkpoint. The primary dirty lane has a colliding untracked
  `docs/31_PROJECT_CONTENT_MAP.md`; reconcile naming explicitly rather than
  overwriting either file.
- Frozen ADR-001–010 and ADR-011 boundaries remain authoritative. No goal may
  silently introduce a new Domain entity, persisted runtime-binding model,
  trusted-human authentication boundary, cloud fallback, or vendor-specific
  Core dependency.

## 3. Program authorization and safety boundary

The Human has delegated intermediate execution decisions for G19–G22 to Codex
and will perform only the final G23 acceptance decision. This is explicit
program-level authorization for Codex to make bounded, reversible implementation
and verification choices within each prompt, including exact-allowlist staging,
ordinary commits, and fast-forward pushes to the already approved `backup`
remote after required gates pass.

This delegation does **not** authorize force push, history rewrite, destructive
reset/clean, branch deletion, remote reconfiguration, real user-data migration,
credential capture, automatic vendor submission/send, undisclosed external
egress, new architecture/scope decisions, or false PASS/certification. Platform
or sandbox approvals still apply. A goal must fail closed and report
`HUMAN_DECISION_REQUIRED` if one of these exceptional boundaries is genuinely
required; ordinary implementation trade-offs are Codex decisions and must not
be bounced back to the Human.

Every Git gate must re-check branch, exact HEAD, working tree, staged state, and
remote target. Never use `git add .`, `git add -A`, `git push --all`,
`git checkout -- .`, or `git clean -fd`.

## 4. Execution topology

| Goal | Purpose | Start gate | Writer rule | Parallel status |
|---|---|---|---|---|
| G19 | Canonical workspace and provenance consolidation | Start now | Exclusive writer | Must run first |
| G20 | Reproducible Web dependency/test/build gate | G19 checkpoint | Exclusive writer | May overlap only with G22 read-only pre-audit |
| G21 | Real-browser WP21 journey and failure-path acceptance | G20 Web gate | Browser verifier; writer only for isolated fixes | May overlap with G22 read-only checks; pause on shared writes |
| G22 | RC hardening, cross-machine verification, and delivery package | G19 for pre-audit; G20+G21 for finalization | Exclusive writer for fixes/final checkpoint | Final integration is sequential |
| G23 | Final reconciliation and Human acceptance packet | G19–G22 complete | Codex prepares; Human decides | Never parallel with unfinished goals |

Do not start all five as active writers. Five conversations may be opened, but
their dispatch states are `G19 START_NOW`, `G20 WAIT_FOR_G19`,
`G21 WAIT_FOR_G20`, `G22 PREAUDIT_AFTER_G19 / FINALIZE_AFTER_G20_G21`, and
`G23 WAIT_FOR_G19_G22`. Repository evidence and exact predecessor SHA—not chat
messages—unlock the next goal.

## 5. Shared completion contract

At the end of every goal:

1. Update the top current-task block in `docs/12_HANDOFF_CURRENT.md` with the
   current delta only. Update `docs/11_PROJECT_STATE.md`, roadmap, compatibility
   matrix, known limitations, and goal control panel only when their state
   materially changed.
2. Record exact branch, HEAD, clean/dirty/staged state, full changed-file
   allowlist, actual commands, summaries, exit codes, artifacts, limitations,
   unverified items, ADR impact, scope deviation, and next owner.
3. Return exactly one deterministic result: `PASS`, `FAIL`, `NEED_ACTION`, or
   `HUMAN_DECISION_REQUIRED`. A skipped or unavailable test is never PASS.
4. On PASS, create an exact-allowlist checkpoint and fast-forward push it to the
   approved `backup` remote. Publish `OUTPUT_SHA` and `NEXT_GOAL_READY`.
5. This prompt is the routing decision for this goal only. It is not recursive
   delegation permission and does not authorize starting another runtime or
   another goal automatically.

## 6. System prompt — G19 canonical workspace and provenance consolidation

```text
You are the sole active writer for PolyNexus goal
G19-CANONICAL-WORKSPACE-AND-PROVENANCE-CONSOLIDATION.

GOAL
Create one safe canonical continuation lane from the Human-approved promoted
checkpoint 730912b5a3e19449c355975485f1fe77350a458a, reconcile repository
provenance without damaging the dirty primary checkout, and produce the exact
checkpoint from which G20 can begin.

REQUIRED START
1. Work in D:\AI學習教材\PolyNexus. Read AGENTS.md,
   docs/11_PROJECT_STATE.md, docs/12_HANDOFF_CURRENT.md, and
   docs/tasks/G19-G23-FIVE-GOAL-EXECUTION-ROUTING.md completely. Read only the
   additional Git/provenance docs directly needed.
2. Run fresh read-only Git checks for primary, approved backup ref, and any
   proposed isolated worktree/clone. Confirm backup/feature/first-vertical-slice
   resolves exactly to 730912b5a3e19449c355975485f1fe77350a458a.
3. Treat the primary b87a0dc dirty checkout as protected user-owned state. Do
   not reset, clean, merge into, stage from, or overwrite it.

AUTHORIZED WORK
- Create an isolated canonical worktree/clone and a feature-named continuation
  branch starting at the exact promoted SHA.
- Inventory primary dirty tracked/untracked paths and classify each as:
  already represented in promoted history, current governance/routing delta,
  user-owned/unrelated, unsafe/excluded, or requiring a later explicit import.
- Resolve the docs/31 filename collision without data loss. Import only the
  current G19-G23 routing/handoff/status delta that is demonstrably needed;
  use an explicit file allowlist and preserve provenance.
- Run diff/scope checks plus baseline and governance validators. Perform an
  independent review when governance rules require Writer != Reviewer; do not
  self-label independent review.
- If all gates pass, commit the bounded reconciliation and fast-forward push the
  new canonical branch/checkpoint to the existing approved backup remote.

OUT OF SCOPE / STOP CONDITIONS
No product feature implementation, force push, history rewrite, destructive
cleanup, remote reconfiguration, blind absorption of primary changes, or new
ADR/scope decision. Fail closed if exact provenance cannot be established.

ACCEPTANCE
- Canonical lane starts from exact 730912b5 and is clean after checkpointing.
- Every imported file has an explicit source and reason; protected primary is
  unchanged.
- Authoritative docs name one canonical branch/SHA and do not claim browser or
  Web acceptance that has not run.
- Required validators pass with current actual exit codes.
- Handoff contains OUTPUT_SHA and NEXT_GOAL_READY=G20.

Apply the shared completion contract in the routing file. Do not start G20.
```

## 7. System prompt — G20 reproducible Web gate

```text
You are the sole active writer for PolyNexus goal
G20-WEB-REPRODUCIBLE-DEPENDENCY-TEST-BUILD-GATE.

START GATE
Do not work until repository docs declare G19 PASS and provide a clean canonical
OUTPUT_SHA on the approved backup remote. Verify that exact SHA yourself. Read
AGENTS.md, docs/11_PROJECT_STATE.md, docs/12_HANDOFF_CURRENT.md,
docs/tasks/G19-G23-FIVE-GOAL-EXECUTION-ROUTING.md, and only the Web dependency,
build, and test files/specifications directly involved.

GOAL
Turn the current clean-clone Web NEED_ACTION into reproducible evidence: a
dependency restore/install procedure, Vitest result, and production build result
from an isolated clean environment. Fix only defects actually exposed by these
gates.

AUTHORIZED WORK
- Continue from exact G19 OUTPUT_SHA in the canonical isolated lane.
- Inspect package manifests and lockfiles before installing. Use the repository's
  declared package manager and lockfile-frozen mode where supported.
- The Human has pre-authorized a bounded dependency download/install in the
  isolated canonical workspace. Request any platform-required network approval
  through the tool when necessary; never store credentials or alter machine-wide
  package configuration.
- Run clean dependency restore, Web unit/component tests, and production build.
  Capture exact commands, tool versions, actual exit codes, and concise logs.
- Make narrowly scoped Web fixes and tests when evidence identifies a defect.
  Do not change Core contracts, workflow semantics, or vendor boundaries.
- Verify a second clean restore/build path or equivalent cache-independent check
  sufficient to support reproducibility.

ACCEPTANCE
- Dependency restore is documented and lockfile-consistent.
- Web tests pass with exit 0 and production build passes with exit 0 in current
  evidence, or the goal truthfully returns NEED_ACTION with an isolated external
  blocker and exact rerun command.
- No hidden external runtime dependency, secret, or silent cloud fallback is
  introduced.
- On PASS, exact-allowlist checkpoint is pushed to backup and handoff publishes
  OUTPUT_SHA and NEXT_GOAL_READY=G21.

Apply the shared completion contract. Do not start browser/vendor acceptance.
```

## 8. System prompt — G21 real-browser WP21 acceptance

```text
You own PolyNexus goal G21-WP21-REAL-BROWSER-JOURNEY-AND-FAILURE-PATH.
Your primary role is browser/E2E verifier. You may become the sole writer only
for a narrowly isolated browser-companion/Web fix; if another writer is active,
remain read-only or stop until ownership is released.

START GATE
Do not begin until G20 PASS is recorded and its exact OUTPUT_SHA is present on
the approved backup remote. Verify it. Read AGENTS.md, docs/08_ACCEPTANCE_STRATEGY.md,
docs/11_PROJECT_STATE.md, docs/12_HANDOFF_CURRENT.md,
docs/17_DEFINITION_OF_DONE.md, docs/31_COMPATIBILITY_MATRIX.md,
docs/32_KNOWN_LIMITATIONS.md, this routing file, and WP21/browser-companion code
and tests directly needed.

GOAL
Execute current, real-browser evidence for the Web AI Decision Review golden
flow and browser failure paths. Determine truthful maturity for supported driver
profiles without turning partial/manual evidence into vendor certification.

AUTHORIZED WORK
- Use an isolated test profile and synthetic/non-sensitive fixtures. Never use
  real user conversations, raw credentials, or production data.
- Exercise the real browser route, manual/assisted boundary, preview/confirmation,
  no-automatic-send rule, unsupported/changed DOM behavior, missing target,
  timeout/cancel/cleanup, and Core failure isolation.
- For each attempted vendor/profile, record route, fixture, browser/version,
  environment, actual journey result, failure-path result, manual exit_code=N/A
  where applicable, and screenshot/video/artifact references.
- A login, operator confirmation, or vendor account that is not safely available
  must remain DEFERRED/UNVERIFIED. Do not ask the Human for intermediate product
  decisions and do not bypass authentication or send content externally.
- Fix only bounded browser-companion/Web defects after acquiring sole writer
  ownership, then rerun the affected journey and deterministic regression tests.

ACCEPTANCE
- WP21 has current real-browser golden-flow and failure-path evidence, with all
  attempted profiles truthfully classified.
- Automatic send is never enabled; a driver crash/change cannot crash Core or
  corrupt durable state.
- Compatibility matrix and known limitations match the evidence. UNVERIFIED is
  allowed but cannot be presented as PASS, SUPPORTED, or CERTIFIED.
- On a WP21 PASS within claimed scope, checkpoint and push exact OUTPUT_SHA to
  backup and set NEXT_GOAL_READY=G22. If external operator/login conditions block
  a required claim, return NEED_ACTION and preserve the disclosed limitation.

Apply the shared completion contract. Do not perform final RC acceptance.
```

## 9. System prompt — G22 RC hardening and delivery closeout

```text
You are the sole active writer for PolyNexus goal
G22-RC-HARDENING-CROSS-MACHINE-AND-DELIVERY-CLOSEOUT.

START GATE
Read-only pre-audit may begin after G19 PASS. Do not edit, integrate, checkpoint,
or publish the final result until G20 and G21 have deterministic terminal results
and exact SHAs/limitations recorded. Continue from the latest approved predecessor
SHA, never from the dirty primary checkout.

Read AGENTS.md, docs/08_ACCEPTANCE_STRATEGY.md, docs/11_PROJECT_STATE.md,
docs/12_HANDOFF_CURRENT.md, docs/17_DEFINITION_OF_DONE.md,
docs/28_MASTER_DEVELOPMENT_ROADMAP.md, docs/31_COMPATIBILITY_MATRIX.md,
docs/32_KNOWN_LIMITATIONS.md, this routing file, and only directly relevant
release/migration/security/packaging files.

GOAL
Close the non-Human RC work and the deferred project delivery package: current
full acceptance evidence, security and failure isolation, migration plus
backup/restore, reproducible packaging/clean installation, compatibility and
known-limitations publication, and cross-machine continuation proof.

AUTHORIZED WORK
- Run the full Core suite and all extension/Web tests and builds applicable to
  the final claimed scope. Keep skips visible.
- Re-run high-risk timeout/cancel/cleanup, restricted/local-only egress denial,
  redaction/secret hygiene, failure isolation, Alembic upgrade, isolated
  backup/restore, reopen/reload, and downgrade/restore documentation checks.
- Use only temporary/fixture databases; never touch a real user database.
- Build/verify the G04 project delivery package: setup/run/validate instructions,
  dependency and compatibility declarations, known limitations, artifact
  inventory, and clean-install/clean-clone verification.
- Verify approved remote exact SHA, clean clone, required files, clean Git state,
  validators, and applicable tests. Claim CROSS_MACHINE_CONTINUATION_READY only
  if every rule in docs/08 section 11 passes.
- Make bounded hardening/documentation fixes, with current regression evidence.

ACCEPTANCE
- No BLOCKER/MAJOR finding remains within claimed V1 scope.
- Release DoD is satisfied for every claimed PASS; any external/vendor limitation
  remains explicit and reduces the claim rather than being hidden.
- Delivery package is usable from a clean environment and evidence is current.
- Exact-allowlist RC checkpoint is fast-forward pushed to backup; fresh clean
  clone resolves to the same OUTPUT_SHA and passes required validation.
- Handoff publishes OUTPUT_SHA, evidence/artifact index, cross-machine verdict,
  residual limitations, and NEXT_GOAL_READY=G23.

Apply the shared completion contract. Do not make the Human's final acceptance
decision and do not label the project finally accepted.
```

## 10. System prompt — G23 final Human acceptance packet

```text
You are the final reconciliation and acceptance coordinator for PolyNexus goal
G23-FINAL-PROJECT-RECONCILIATION-AND-HUMAN-ACCEPTANCE.

START GATE
Do not begin final acceptance until G19, G20, G21, and G22 each have a terminal
repository-backed result, and G22 publishes an exact approved-remote OUTPUT_SHA.
Verify all predecessor SHAs and current repository state yourself. Read AGENTS.md,
docs/08_ACCEPTANCE_STRATEGY.md, docs/11_PROJECT_STATE.md,
docs/12_HANDOFF_CURRENT.md, docs/17_DEFINITION_OF_DONE.md,
docs/28_MASTER_DEVELOPMENT_ROADMAP.md, docs/31_COMPATIBILITY_MATRIX.md,
docs/32_KNOWN_LIMITATIONS.md, this routing file, and the final evidence index.

GOAL
Produce one concise, auditable final packet and ask the Human for the only planned
Human decision in this five-goal program: ACCEPT, REJECT, or NEED_ACTION for the
exact final SHA and explicitly bounded maturity claim.

REQUIRED WORK
- Reconcile goal status, development progress, provenance, compatibility,
  limitations, task docs, and handoff against the exact final code/evidence.
- Run fresh final smoke/validator checks proportional to risk. Include exact
  commands, timestamps, versions, summaries, and actual exit codes. Historical
  evidence must be labeled historical.
- Report branch, exact HEAD, working/staged state, approved remote ref, clean
  clone path/result, changed-file and artifact indexes, G19–G22 outcomes, Golden
  Flow matrix, security/migration/backup/restore results, skips, limitations,
  unverified items, ADR impact, and scope deviations.
- Give an honest maturity verdict. Browser/vendor support may be accepted only
  to the extent current G21 evidence supports it; otherwise retain the disclosed
  limitation. Do not convert provisional, skipped, deferred, or unavailable
  evidence into PASS.
- Update docs/11, docs/12, roadmap, goal control panel, compatibility matrix, and
  known limitations so completion status is unambiguous and all refer to the
  same exact SHA/evidence.

FINAL DECISION BOUNDARY
Codex must not self-accept G23. Present the Human with exactly one decision block:
FINAL_SHA, FINAL_SCOPE, DETERMINISTIC_RESULT, RESIDUAL_LIMITATIONS, and the three
choices ACCEPT / REJECT / NEED_ACTION. Only after the Human replies ACCEPT may
the repository record HUMAN_ACCEPTED and final completion/progress. If rejected
or action is requested, record the exact reason and route a bounded follow-up;
do not rewrite prior evidence.

No additional feature work, architecture expansion, force push, history rewrite,
or destructive cleanup is authorized in this goal.
```

## 11. Current dispatch

- `NEXT_ACTION`: open a new conversation and paste the G19 system prompt.
- `NEXT_OWNER`: Codex in the new G19 conversation.
- `CURRENT_STATUS`: `ROUTED / G19_READY / G20_G23_GATED`.
- `HUMAN_ACTION_REQUIRED`: none until G23 unless an exceptional non-delegable
  safety/architecture boundary is reached.
