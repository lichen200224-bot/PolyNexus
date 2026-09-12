# PUBLICATION-INTEGRITY-REPAIR-01 — current publication correction

REJECTED_CANDIDATE_SHA=180432d03f6d423bb3152c233fb4f0a5072868f5
REJECTION_GATE=PUBLICATION_INTEGRITY
REJECTION_CAUSE=working-tree CRLF hashes were used instead of canonical committed blob hashes

Repair lineage: one new commit directly after the rejected Candidate; no rewrite.
Functional content and prior functional PASS history are unchanged. No acceptance,
merge or freeze is claimed. Return the new exact SHA to Fresh Independent Review.

All 20 freeze_hashes are SHA-256 of binary Git blob content extracted from
180432d03f6d423bb3152c233fb4f0a5072868f5:<candidate path>, never checkout bytes.
The repair's own committed blobs must independently match those same 20 values.

Evidence representation is explicit in manifest.json: evidence_sha256 verifies
raw members in writer-evidence.zip; unchanged members retain original bytes/hashes.
Corrected collection and this handoff use UTF-8 LF both as committed blobs and ZIP
members. committed_evidence_sha256 separately verifies direct Git blob copies,
including unchanged files whose original archived CRLF bytes differ from Git LF.
No unrelated evidence content or evidence_sha256 entry is regenerated.
The ZIP is rebuilt deterministically because it contains both corrected files;
all other member contents, including historical failure records, are preserved.

CANONICAL_PREDECESSOR_COLLECTION=771
CANDIDATE_COLLECTION=819
DELTA=+48
REMOVED=0
COLLECTION_ACCOUNTING=EXPLAINED
Prior 816 → 819 accounting is SUPERSEDED_WRITER_INTERMEDIATE_MEASUREMENT.

The Writer functional handoff below is historical to rejected Candidate 180432d.
Its test results are preserved, not rerun or reinterpreted by this publication repair.

---

==================================================
BASELINE-DEBT-01 WRITER HANDOFF — IMPLEMENTATION
==================================================

TASK_ID: BASELINE-DEBT-01
START_SHA: 86d5939044c1d7ec2a991820f39287481ee9120f
BRANCH: feature/baseline-debt-01-deterministic-lifecycle-cleanup
ARCHITECTURE_DECISION: HUMAN_ACCEPTED / IMPLEMENTATION_AUTHORIZED
RESULT: READY_FOR_INDEPENDENT_ACCEPTANCE
ORIGINAL_5_FAILURES: CLOSED
NEW_G14_FAILURE: CLOSED
TEST_COLLECTION_DELTA: EXPLAINED
STABILITY_EVIDENCE: COMPLETE
COMMIT_STATUS: NOT_COMMITTED
PUSH_STATUS: NOT_PUSHED

Writer only. Final acceptance and commit/push authorization are not granted.
This current evidence supersedes prior blocked Writer results preserved below.

## G14 diagnosis and conditional authorization

G14_ROOT_CAUSE: original failed-run safe and provenance Evidence have identical
observed_at=2026-09-12 00:46:51.820511. Existing ORDER BY observed_at,id sorts the
provenance UUID first. Original insertion rowid is safe=1, provenance=2, but reload
is provenance then safe. The test's positional assumption fails; metadata is intact.

Original failed-run EVIDENCE_AFTER_RELOAD count=2:
EVIDENCE_1:
 id=evidence_cc461dfac1a545488c9a3a17c48bb11f
 actor_id=system:restart-reconciliation; source=runtime-adapter
 type=RUNTIME_EVIDENCE; status=PASS
 metadata={reconciled_after_restart:true, provider_id:polynexus, runtime_id:reference,
 adapter_id:builtin.reference, runtime_profile_ref:reference.local, profile_revision:1,
 adapter_version:test-restart-adapter/1}
EVIDENCE_2:
 id=evidence_eebcd7fcda18434c9206c8ec10cb8b93
 actor_id=adapter:normalized; source=normalized-runtime
 type=RUNTIME_EVIDENCE; status=OBSERVED
 metadata={safe_key:safe_value}

SAFE_EVIDENCE_BEFORE_RECONCILIATION (separate, unmodified diagnostic test execution):
 id=evidence_84ed6547a401470394c54d3e0e18086b
 actor_id=adapter:normalized; source=normalized-runtime
 type=RUNTIME_EVIDENCE; status=OBSERVED; metadata={safe_key:safe_value}
Its reloaded record has the same id, actor, source, type, status and exact metadata.
The diagnostic run has distinct timestamps and naturally passed, exit 0; it is
not a retry-to-green substitute for the original failed DB or post-fix gates.

SAFE_KEY_PRESENT_ANYWHERE=YES
ORDER_CHANGED=YES (original failing database: insertion vs reload)
METADATA_LOST=NO
METADATA_OVERWRITTEN=NO
CONTRACT_CHANGED_BY_ADR014=NO
Evidence: ADR-014 Decision and boundaries applies ordering metadata to Run.events,
not Evidence retention. Reconciliation copies approved metadata, adds a separate
provenance record; Evidence serialization round-trips the dict. Neither this
Evidence repository ordering nor reconciliation production code changed this round.

Full raw before/after records: g14-diagnostic-snapshots.json.
Original failure database read-only inspection: g14-original-failure-db.json.
Structured required diagnosis fields: g14-root-cause.json.
The original failed Python before-object is not retained; its stored record and
insertion rowid are kept separate from the traced diagnostic run. No debug changes
were inserted into source. The diagnostic harness remains only as ignored evidence.

Conditional test-only authorization satisfied. Changed only
services/core/tests/test_g14_runtime_reconciliation.py this round:
lookup original safe evidence by exact id (existing repository test pattern),
then assert actor/source/type/status and safe_key value. Select the single restart
provenance record by actor/source, assert type/status and adapter_version. Original
normalized output ownership, finding/artifact retention and secret/redaction checks
are unchanged. No optional keys, skip/xfail, assertion removal or production fix.

## Collection and verification

CANONICAL_PREDECESSOR_COLLECTION=771
CANDIDATE_COLLECTION=819
DELTA=+48
REMOVED=0
COLLECTION_ACCOUNTING=EXPLAINED
Canonical predecessor: 86d5939044c1d7ec2a991820f39287481ee9120f.
Rejected functional Candidate: 180432d03f6d423bb3152c233fb4f0a5072868f5.
Independent exact-commit git archive snapshots both collected with exit 0.
All 48 added node IDs are recorded losslessly in g14-collection-delta.json:
40 BASELINE-DEBT-01 cases, 7 migration cases, 1 fresh-schema case. No removals.

SUPERSEDED_WRITER_INTERMEDIATE_MEASUREMENT: the former 816 → 819 (+3)
comparison used intermediate working-state Full Core JUnit collections, not the
canonical predecessor. Fresh Independent Review rejected that accounting. Its
historical observations below remain preserved but are not canonical baseline truth.

G14_SINGLE: 1 passed / 0 failed / 0 skipped, ACTUAL_EXIT_CODE=0.
G14_MODULE: 13 passed / 0 failed / 0 skipped, ACTUAL_EXIT_CODE=0.
FOCUSED+MIGRATION: 47 passed / 0 failed / 0 skipped, ACTUAL_EXIT_CODE=0.
FULL_CORE: 818 passed / 0 failed / 1 skipped, FULL_CORE_EXIT_CODE=0.
Exact COMMAND / ACTUAL_EXIT_CODE / EVIDENCE_PATH:
g14-single-result.json, g14-module-result.json, g14-focused-result.json,
g14-full-result.json, each with corresponding .log and .xml evidence.

SKIPPED: services/core/tests/test_wp07_integration.py:799, existing Windows symlink
creation policy denial. Real symlink escape cannot be tested; sibling-prefix and
regex cases provide partial coverage. Same skip in prior full-1 and limited2-full;
not introduced this round, not included in passed count.

All five original failure nodes and G14 passed in Full Core. No backup/temp tests
excluded. Full Core uses a fresh directory under system TEMP without changing
isolation policy, global configuration, fixtures or environment variables.
Original 5 closure matrix: g14-final-five-closure.json. Original red accounting and
failed Full Core logs remain in their original locations.

BASELINE_VALIDATOR: ACTUAL_EXIT_CODE=0
GOVERNANCE_VALIDATOR: ACTUAL_EXIT_CODE=0
GIT_DIFF_CHECK: ACTUAL_EXIT_CODE=0
ALLOWLIST_SCOPE_CHECK: ACTUAL_EXIT_CODE=0
Commands, result, actual exits and evidence paths: g14-validator-results.json.
Scope hash comparison: only G14 test changed this round; all branch modifications
are in accumulated authorization, no staged files. See g14-scope-result.json.

STABILITY_5_RUNS:
ROUND_1: passed=40 failed=0 skipped=0 exit_code=0
ROUND_2: passed=40 failed=0 skipped=0 exit_code=0
ROUND_3: passed=40 failed=0 skipped=0 exit_code=0
ROUND_4: passed=40 failed=0 skipped=0 exit_code=0
ROUND_5: passed=40 failed=0 skipped=0 exit_code=0
Exact commands: g14-stability-results.json; all five logs/JUnit preserved.
Protocol derives directly from ../commands.json repeat-1..5: same Python executable,
-B, pytest module test_baseline_debt_01.py, -o addopts=, -q, --tb=short. Only unique
basetemp/JUnit/log paths change to retain historical red evidence; same workspace
isolation semantics. No new selection, timeout adjustment, retry or excluded case.
The module now contains the already-authorized 40 tests; it was not reduced to
its original 13 red tests. No platform skips occur in these five rounds.

## Implementation context retained for independent review

ROOT_CAUSE_A: timestamp/UUID does not represent durable Run event append order.
ROOT_CAUSE_B: shared cleanup/operation deadline, setup race and external cancellation
escaping cleanup/durable persistence. See preserved implementation evidence below.
MIGRATION: 0003_run_event_sequence, down_revision=0002.
LEGACY_POLICY: per-Run rowid insertion-order reconstruction, not causal-time proof.
SEQUENCE_CONTRACT: immutable persistence-only event_sequence; atomic allocation,
unique constraint, update excludes counter; no Domain/API expansion.
CANCELLATION_CONTRACT: protected cleanup and verification; truthful CANCELLED or
ORPHANED, durable service persistence, then original CancelledError re-raised.
SCHEMA_CHANGE=YES; RUNSTATE_CHANGE=NO; PUBLIC_API_CHANGE=NO.
G30_CHANGED=NO; WP20_CHANGED=NO; SCORE_CHANGED=NO.

Original 26 matrix, MCF-01 50, affected regressions, runtime skeleton/binding and
WP-14/15/16 are included in the successful Full Core run. No differential PASS is
used. Focused migration/cancellation evidence and ADR-014 remain preserved.
Only isolated test databases migrated; no production deployment/restore performed.
Historical tracked task/handoff notes were not edited this round (latest scope
forbids other files); this explicitly authorized Writer artifact records current
status. Independent Reviewer/Governance must decide acceptance and subsequent routing.

Final git status --short, git diff --name-only, git diff --stat and actual exits:
g14-final-git-state.json. MODIFIED_FILES / NEW_FILES / DELETED_FILES /
UNTRACKED_FILES: g14-final-file-inventory.json. No deleted files; index empty.
Exact G14 delta: g14-test-only.diff. No stage/commit/push/merge/rebase/reset/clean.

NEXT_REQUIRED_ROLE: FRESH_INDEPENDENT_CODEX_REVIEWER

---
# Historical Writer handoffs (preserved)

# Latest Writer handoff — LIMITED_2

RESULT=SCOPE_EXPANSION_REQUIRED
ORIGINAL_5_FAILURES=CLOSED
FINAL_ACCEPTANCE=NOT_GRANTED
STABILITY_PASS=NOT_GRANTED
COMMIT_STATUS=NOT_COMMITTED
PUSH_STATUS=NOT_PUSHED

## Bounded changes and schema contract

This round modifies only:
- services/core/tests/test_cp06_wp30_clean_install.py
- services/core/tests/test_g17_migration_restore_authority.py

All original runs columns (16) and run_events columns (6) are explicitly selected
in their original order, and complete tuple/value equality remains at every
existing upgrade/restore/downgrade assertion. All projects/tasks/evidence columns
remain selected and compared. No test or assertion was removed or weakened.

NEW_METADATA_COLUMNS / DEFAULT / NULLABILITY:
- runs.next_event_sequence: INTEGER NOT NULL DEFAULT 0.
- run_events.event_sequence: INTEGER NOT NULL; no server default (required).
- run_events.sequence_legacy_backfill: BOOLEAN NOT NULL DEFAULT 0.
EXPECTED_VALUE: seeded one-event legacy Run upgrades to counter=1, sequence=1,
legacy flag=1, with exact Run and event IDs asserted. Both re-upgrades repeat it.
RESTORE_BEHAVIOR: restoring 0001 removes all three metadata columns; original
values remain equal. CP06 also proves this after downgrade to 0001.
CLEAN_INSTALL_BEHAVIOR: new CP06 test verifies exact fresh schema, omitted counter
becomes 0, omitted sequence fails, NULL counter/flag fail; atomic UPDATE RETURNING
allocates 1 and new event flag defaults to 0. This adds one test, not a skip.
Migration 0003 and production models were read to derive expectations; unchanged.
No shared fixture/helper layer, config, policy, backup, production or ADR edit.

## Ordered verification

Exact commands and actual exit codes: limited2-command-results.json.
AFFECTED: 10 passed / 0 failed / 0 skipped, ACTUAL_EXIT_CODE=0 (limited2-a.xml/log).
Count increased 9→10 because of the fresh schema/default/nullability test.
FOCUSED+MIGRATION: 47 passed / 0 failed / 0 skipped, ACTUAL_EXIT_CODE=0
(limited2-focused.xml/log), same test set and options; fresh artifact paths preserve
prior evidence. Count unchanged.
FULL_CORE: 817 passed / 1 failed / 1 skipped, ACTUAL_EXIT_CODE=1
(limited2-full.xml/log). All Core tests included, including temp isolation tests.
Total 819 versus original 816: two prior cancellation persistence rollback tests
were added after full-1, and this round adds one fresh schema test.

SKIPPED: existing Windows policy skip at test_wp07_integration.py:799:
Symlink creation denied by Windows policy; cannot test real symlink escape via
production containment helper. Sibling-prefix and regex tests give partial coverage.
This file is unchanged this round; the same skip appears in full-1.xml. Not passed.

## Original five closure and NEW_REGRESSION

limited2-original-five-closure.json records all five exact node IDs, original causes,
fix/environment resolution, and passing nodes in both affected and Full Core runs.
All five CLOSED. WP23 backup cases pass naturally with a fresh system TEMP basetemp;
no isolation policy, env variable, test exclusion or fixture change.

NEW_REGRESSION:
services/core/tests/test_g14_runtime_reconciliation.py::test_completed_runtime_retains_owned_safe_normalized_outputs
Failure: KeyError: 'safe_key' at line 330, evidence[0].metadata["safe_key"].
This node passed in full-1 but failed in limited2-full. It is separate from the
original five, and is not treated as a proven regression caused by the two edits.
Root cause remains UNVERIFIED. Read-only inspection shows positional assertions
for two evidence records and repository ordering by observed_at,id; timestamp ties
are a possible hypothesis, not established failure data. No retry or fix performed.

MINIMUM_ADDITIONAL_FILE_ALLOWLIST / authorization request:
services/core/tests/test_g14_runtime_reconciliation.py, bounded diagnosis and test
repair only if evidence proves a positional-order assumption. This latest gate
forbids other tests and production changes. Any production defect requires a new
explicit gate; no production fix is proposed without diagnosis.
PROPOSED_MINIMAL_CHANGE: first inspect the failed-run evidence records; if both
required records and metadata are present, target exact evidence identity while
retaining all ownership, value and provenance assertions. Do not weaken assertions.
RISK_IF_CHANGED: selecting the wrong evidence could mask a provenance defect;
exact identity and unchanged metadata expectations must be preserved.
RISK_IF_NOT_CHANGED: Full Core remains failed; no acceptance/stability progression.

## Stopped gates / final Git

Baseline validator, governance validator, authorized diff check and formal scope
verification: NOT_EXECUTED this round; Full Core exit 0 prerequisite was not met.
Fixed ROUND_1..ROUND_5: NOT_EXECUTED; STABILITY_PASS=NOT_GRANTED.
The historical fixed protocol is in ../commands.json (repeat-1..repeat-5), preserved.

Requested Git status/name-only/stat commands all exited 0; raw outputs in
limited2-final-git-state.json. File categories and before/after content hashes:
limited2-file-inventory.json and limited2-before-hashes.json. Only the two allowed
files changed content this round; no deleted files. Prior implementation remains.
No stage, commit, push, reset, clean, merge, rebase, squash or evidence deletion.
All earlier handoff versions, red repro, implementation, sequence/cancellation,
ADR, validators and failed logs remain preserved below and in their original files.

---
# Historical handoff before LIMITED_2

# Latest limited scope expansion handoff

RESULT=SCOPE_EXPANSION_REQUIRED
FINAL_ACCEPTANCE=NOT_GRANTED
STABILITY_PASS=NOT_GRANTED
COMMIT_STATUS=NOT_COMMITTED
PUSH_STATUS=NOT_PUSHED

Authorized exact paths:
- services/core/tests/test_cp06_wp30_clean_install.py
- services/core/tests/test_g17_migration_restore_authority.py
- services/core/tests/test_wp23_backup_restore_migration.py

This round changes only six current/head expectations from 0002 to 0003.
No canonical head helper/constant was found in the targeted tests/persistence search.
No production/migration/backup/restore/shared-fixture/config/policy/ADR edits.
The historical implementation and red evidence below remain preserved.

## Original five-failure accounting

See limited-expansion-failure-accounting.json: all five exact node IDs, signatures,
causes, categories, authorized fix targets and overlap are recorded one-to-one.
Two failures were head assertions (CP06/G17). Three were WP23 temp isolation.
WP23 roundtrip also contained masked head assertions; it is not a sixth failure.

## Affected verification

COMMAND / ACTUAL_EXIT_CODE / paths: limited-command-results.json.
Result: 7 passed, 2 failed, 0 skipped; ACTUAL_EXIT_CODE=1.
Evidence: limited-a.xml, limited-a.log. The five WP23 tests all pass.
The basetemp argument was placed in a fresh system TEMP subdirectory; production
isolation still restricts backup paths to tempfile.gettempdir(). No environment,
policy, fixture or config was changed. Thus the former backup_not_isolated errors
were resolved by valid execution paths, not by revision assertion edits.

## Remaining failure / minimum additional authorization

REMAINING_FAILURE:
- services/core/tests/test_cp06_wp30_clean_install.py::test_backup_restore_downgrade_reupgrade_preserves_old_history
- services/core/tests/test_g17_migration_restore_authority.py::test_isolated_backup_restore_and_reupgrade_preserve_history
ROOT_CAUSE: _history uses SELECT *; 0003 adds runs.next_event_sequence and two
run_events metadata columns, so legacy tuples and migrated tuples differ in shape.
The first observed mismatch is the Run counter column. Original values are not
shown to be lost by this assertion; the comparison has not isolated legacy facts.
MINIMUM_ADDITIONAL_FILE_ALLOWLIST: no additional files; expanded edit authorization
is needed within the two files above for their local _history helpers/assertions.
WHY_CURRENT_ALLOWLIST_IS_INSUFFICIENT: the present change authorization permits
only current/head version expectations, not rewriting historical row comparisons.
PROPOSED_MINIMAL_CHANGE: compare every original 0001 column/value after upgrade,
retain full original-data checks after restore/downgrade, and separately assert
0003 sequence/counter/legacy metadata. No shared helper or production change.
RISK_IF_CHANGED: an incorrect projection could omit original facts; explicitly
preserve all original columns and add metadata assertions to avoid weakening tests.
RISK_IF_NOT_CHANGED: correct schema expansion cannot satisfy SELECT * tuple equality;
affected verification and Full Core remain blocked.

## Gate handling and Git state

B focused/migration, C Full Core, validators and five stability rounds NOT_EXECUTED
this round because A failed. Prior results below are historical, not rerun claims.
No skip/xfail added. No assertion removed or relaxed. No stage/commit/push/merge/
rebase/squash/reset/clean; no independent acceptance claim.
Commands git status --short, git diff --name-only, git diff --stat all exited 0;
outputs in limited-final-git-state.json. Full MODIFIED_FILES / NEW_FILES /
DELETED_FILES / UNTRACKED_FILES in limited-file-inventory.json (no deletions).
Exact six-line test delta: limited-authorized-tests.diff.

---
# Historical Writer handoff before limited scope expansion

==================================================
BASELINE-DEBT-01 WRITER HANDOFF — IMPLEMENTATION
==================================================

TASK_ID: BASELINE-DEBT-01
START_SHA: 86d5939044c1d7ec2a991820f39287481ee9120f
BRANCH: feature/baseline-debt-01-deterministic-lifecycle-cleanup
ARCHITECTURE_DECISION: HUMAN_ACCEPTED / IMPLEMENTATION_AUTHORIZED
RESULT: SCOPE_EXPANSION_REQUIRED

ROOT_CAUSE_A: occurred_at / random UUID sorting cannot represent durable append order.
ROOT_CAUSE_B: operation and cleanup shared a deadline policy; short tests raced setup;
external caller cancellation escaped cleanup and durable state persistence.

MIGRATION: 0003_run_event_sequence (down_revision=0002)
LEGACY_POLICY: per-Run physical rowid insertion-order reconstruction, legacy flag TRUE;
not causal-time proof. Identity/state/timestamp/reason preserved; downgrade loses
ordering metadata but retains events; re-upgrade treats retained rows as legacy.
SEQUENCE_CONTRACT: persistence-only 1-based immutable per-Run durable append order;
atomic UPDATE RETURNING allocation, unique composite guard; ordinary updates exclude counter.
CANCELLATION_CONTRACT: protected bounded cleanup; verified CANCELLED else ORPHANED;
original CancelledError re-raised after service commit; persistence failure rolls back.

CHANGED_FILES:
- docs/10_DECISION_LOG.md
- docs/12_HANDOFF_CURRENT.md
- docs/15_DOCUMENT_INDEX.md
- docs/tasks/BASELINE-DEBT-01.md
- docs/35_ADR_014_DURABLE_EVENT_ORDERING_AND_CANCELLATION_CLEANUP.md
- services/core/src/polynexus_core/persistence/models.py
- services/core/src/polynexus_core/persistence/repository.py
- services/core/src/polynexus_core/runtime/supervisor.py
- services/core/src/polynexus_core/execution_service.py
- services/core/alembic/versions/0003_run_event_sequence.py
- services/core/tests/test_baseline_debt_01.py
- services/core/tests/test_baseline_debt_01_migration.py
- services/core/tests/test_wp09_query_api.py
- services/core/tests/test_wp12_council.py
- services/core/tests/test_wp14b_runtime_binding.py
- services/core/tests/test_wp24_resource_guards.py

MIGRATION_TESTS: 7 passed, combined focused command exit 0 (focused-final.xml/log).
FOCUSED_TESTS: 40 passed, including 24 durable cancellation cases across 3 service
entry paths and 2 persistence-failure rollback cases; combined total 47, exit 0.
DEBT_MATRIX: original 26 exact nodeids all passed within full-1.xml; standalone
matrix-1 exited 1 (21/5), matrix-2 exited 1 (24/2); subsequent fixes retained.
AFFECTED_REGRESSIONS: full-1.xml records no failures in the 8 requested affected
files; Windows symlink skip remains. Prior affected-1 exit 1: 278 passed/1 failed/1 skipped.
MCF01_REGRESSION: all 50 passed within Full Core, no separate command exit claimed.
RUNTIME_REGRESSIONS: within Full Core, skeleton 17, WP-14 31, WP-15 36, WP-16 58 passed;
binding suite passed. This is case evidence, not differential or Full Core PASS.
FULL_CORE: FULL_CORE_EXIT_CODE=1; 810 passed, 5 failed, 1 skipped (full-1.xml/log).
Full run preceded addition of 2 rollback tests; those subsequently passed in focused-final.
BASELINE_VALIDATOR: EXIT_CODE=0
GOVERNANCE_VALIDATOR: EXIT_CODE=0
GIT_DIFF_CHECK: EXIT_CODE=0
STABILITY_5_RUNS: NOT_EXECUTED after scope blocker; no deterministic stability PASS.
Historical pre-approval red runs and all implementation failed logs remain preserved.

SCHEMA_CHANGE: YES
RUNSTATE_CHANGE: NO
PUBLIC_API_CHANGE: NO
G30_CHANGED: NO
WP20_CHANGED: NO
SCORE_CHANGED: NO

KNOWN_LIMITATIONS:
- Full Core cannot pass as-is: tests hard-code head=0002 in
  services/core/tests/test_cp06_wp30_clean_install.py (lines 95,105),
  services/core/tests/test_g17_migration_restore_authority.py (lines 72,83),
  services/core/tests/test_wp23_backup_restore_migration.py (lines 131,144).
  These files are outside the authorized test allowlist and remain untouched.
  Required scope expansion: update head expectations to 0003 while preserving
  explicit historical 0001/0002 backup/downgrade and original-data assertions.
- Three WP23 backup failures in this full run are backup_not_isolated: chosen
  pytest basetemp is outside tempfile.gettempdir(). Subsequent verification needs
  an isolated writable temp root consistent with backup policy; do not change
  production backup protections. WP23's hard-coded head failure is currently masked.
- Windows policy skip: test_wp07_integration.py:799 real symlink creation denied;
  1 skipped, not counted as passed.
- Only isolated databases were migrated; no production migration/restore performed.
- Independent review and final fixed five-run acceptance remain outstanding.

NEXT_REQUIRED_ROLE: FRESH_INDEPENDENT_CODEX_REVIEWER (after authorized repair and
all required acceptance passes); immediate routing: HUMAN scope expansion decision.
No stage/commit/push/reset/clean/rebase or MCF-02. No VERIFIED_PASS claim.
