# PRE-WP14-B — Runtime Binding Contract Implementation

## Task status

- TASK_ID: PRE-WP14-B-RUNTIME-BINDING-IMPLEMENTATION
- STATUS: `HUMAN_ACCEPTED / IMPLEMENTATION_ACCEPTED / GIT_CHECKPOINT_IN_PROGRESS`
- ATTEMPT: 4
- BRANCH: feature/first-vertical-slice
- BASELINE HEAD: `934a2191a78a40c8a68b5195f786b1d9cc8bc0cc` before the authorized checkpoint commit; final checkpoint SHA is recorded after commit
- WRITER: OpenCode
- REVIEWER: Fresh independent Codex context (Writer != Reviewer)
- ANTIGRAVITY_STATUS: NOT_REQUIRED — no UI/browser/E2E surface
- NEXT_OWNER: Codex explicit-allowlist Git checkpoint -> Human retains push/remote and future WP-14 gates
- HUMAN_AUTHORIZATION: PRE-WP14-B Architecture / Acceptance decision approved on 2026-08-26 after fresh independent Codex `VERIFIED_PASS`; exact 15-file stage/commit checkpoint authorized; no push/remote modification or migration-on-real-database authorization
- ADR_IMPACT: ADR-011 implementation within the accepted architecture; ADR-001～ADR-011 decision text unchanged
- DEPENDENCY: PRE-WP14-A HUMAN_ACCEPTED at checkpoint `28196c9`

## Attempt 4 additions (this attempt — Codex Attempt-3 review remediation)

Codex review of Attempt 3 returned Findings 1–3 (no Finding 4 repeat this round; the Reviewer-environment launcher worked). All three fixed within the same 15-file allowlist:

1. **Log secret-exclusion labeling corrected** (Finding 1, MAJOR): the former single "Runtime-facing error/log capture = PASS" row was FALSE PASS for logs. Split into: persisted runtime error capture = PASS (`test_runtime_error_capture_sanitized_in_persistence`, DB-persisted surfaces only); application log capture (logging handlers / stdout / stderr / caplog) = NOT_IN_SCOPE this round, UNVERIFIED — the Core runtime source has no logging surface within this allowlist. Synced in docs/tasks/PRE-WP14-B.md, docs/30_RUNTIME_CONTRACT_FOUNDATION_GATE.md and docs/12_HANDOFF_CURRENT.md. API / exports / handoff remain NOT_IN_SCOPE/UNVERIFIED.
2. **Migration-installed Run-delete guard dynamically accepted** (Finding 2, MEDIUM): new `test_migration_installs_run_delete_guard_and_fails_closed` runs ONLY on a pytest temporary isolated SQLite database: Alembic upgrade 0001 → head; asserts all three triggers exist on the migrated database; direct ORM delete (both with-child-events and without), bulk ORM delete, and raw SQL DELETE all fail closed; Run rows AND snapshot rows preserved; downgrade to 0001 removes the 0002 table and ALL 0002 triggers with runs/events history preserved; re-upgrade restores the deterministic legacy backfill and the guard trigger, which again rejects raw SQL deletion.
3. **ExecutionService docstring synced** (Finding 3, MINOR): `execute_existing_run()` docstring now explicitly splits lifecycle failure ownership — RunSupervisor owns adapter execution-boundary failures; ExecutionService owns post-binding-commit adapter factory construction failure recovery (sanitized STARTING → FAILED). Runtime behavior, RunState, schema, API and supervisor.py untouched.

## Attempt 3 additions

Codex review of Attempt 2 returned FAIL with 4 findings. Attempt 3 fixes Findings 1–3 (FIX_OWNER OpenCode) within the same 15-file allowlist. Finding 4 (Reviewer-environment Python launcher failure) is FIX_OWNER Human/Environment-owner and is NOT fixed here; Writer-side verification below was re-run in the controlled launcher environment.

1. **Run deletion fail closed at database level** (Finding 1): new SQLite trigger `trg_runs_reject_delete` (`BEFORE DELETE ON runs` → RAISE ABORT) created by BOTH the create_all path (`models.py`) and Alembic 0002 upgrade() (dropped in downgrade()). Run deletion is now rejected for direct ORM delete, bulk ORM delete, and raw SQL DELETE regardless of FK enforcement; no orphan snapshot can ever exist. The former lenient test was replaced by `test_run_deletion_fail_closed_preserves_run_and_snapshot`, which asserts all three delete paths raise, and that BOTH the Run row and the snapshot row are preserved.
2. **Adapter factory construction failure fails closed** (Finding 2): `ExecutionService._construct_adapter_or_fail_closed()` wraps `registry.create_adapter()` in both `execute_task()` and `execute_existing_run()`. On factory failure AFTER the binding-first commit: the Run legally transitions STARTING → FAILED via the existing lifecycle, a sanitized constant reason/event ("Runtime adapter construction failed") is persisted and committed, and a sanitized `RuntimeBindingError` (raw exception suppressed via `from None`) propagates. Binding failure still constructs zero adapters (factory_calls=0 preserved). New tests: `test_execute_existing_run_factory_failure_fails_closed`, `test_execute_task_factory_failure_fails_closed` — both verify snapshot retention, STARTING→FAILED event sequence, sanitized reason, and marker-free persisted surfaces.
3. **Secret exclusion coverage completed/labeled** (Finding 3): `result_summary` (runs table) added to the DB-surface marker scan; new `test_runtime_error_capture_sanitized_in_persistence` proves runtime-facing adapter exceptions carrying a credential marker never reach run_events.reason / evidence metadata / result_summary / snapshot rows, WITH an explicit positive control proving the scan detects the marker when genuinely present. Coverage matrix now explicitly labeled per surface:

| Surface | Status | Evidence |
|---|---|---|
| DB snapshot rows (all columns) | PASS | `test_snapshot_surfaces_contain_no_credential_markers`; exit 0 |
| Run events reasons | PASS | same test + factory-failure tests; exit 0 |
| Evidence metadata | PASS | same tests; exit 0 |
| Artifact metadata columns | PASS | same test; exit 0 |
| runs.result_summary | PASS | extended scan + factory-failure tests; exit 0 |
| Persisted runtime error capture (DB-persisted reasons/metadata/results from raising adapter exceptions) | PASS | `test_runtime_error_capture_sanitized_in_persistence` (positive+negative samples); exit 0 |
| Application log capture (logging handlers / stdout / stderr / caplog) | NOT_IN_SCOPE this round — Core runtime source has no logging surface in this gate's allowlist; UNVERIFIED |
| API response surface | NOT_IN_SCOPE this round — no new/changed API endpoint in the allowlist; UNVERIFIED by dynamic test |
| Exports/handoff static marker scan | NOT_IN_SCOPE this round — no export/handoff mechanism exists in Core scope; UNVERIFIED |

NOT_IN_SCOPE surfaces are NOT claimed as verified. Persisted error capture and application log capture are distinct surfaces; only the former has deterministic evidence.

## Attempt 2 additions

1. **execute_task() is now binding-first**: Run identity + CAS claim + immutable snapshot insert_once + CREATED→STARTING event commit in ONE transaction BEFORE any adapter invocation; any failure rolls back completely (no adapter construction, no partial Run/snapshot). Proven by an adversarial probe adapter that reads through an INDEPENDENT connection at its first observable point (adapter.create_run) and observes the committed snapshot and STARTING event, plus a bind-failure injection test proving zero adapter construction and zero new persisted Runs.
2. **Error message sanitization**: RuntimeBindingError messages are fixed public-safe constants — identifier validation, unknown profile resolution and unregistered factory failures never echo caller input. Tests inject token/cookie/session/api-key/Bearer markers as identifiers/profile refs and assert the marker never appears in str(exception).
3. **Auth ownership invariant** (ADR-011 §6): NONE / RUNTIME_MANAGED / BROWSER_PROFILE_MANAGED must NOT carry a secret_ref_id; SECRET_REF must carry a grammar-valid opaque secret_ref_id. Enforced in RuntimeProfile AND RuntimeBindingSnapshot constructors, on reload (mismatched persisted rows fail closed), and verified for migration backfill rows. Full 4×2 positive/negative matrix tested.
4. **Immutability hardened to database level**: SQLite triggers (`trg_rbs_reject_update` / `trg_rbs_reject_delete`) reject any UPDATE/DELETE on run_binding_snapshots — covering normal ORM mutation, bulk Query.update()/delete(), and direct raw SQL — in addition to the repository API rejections and ORM mapper listeners. Triggers are created by both Alembic 0002 upgrade() and Base.metadata create_all path; downgrade drops them. Run deletion never cascades a snapshot (tested).

## Scope implemented

- Domain: `RuntimeProfile` (mutable intention, memory/Registry only), immutable frozen `RuntimeBindingSnapshot`, `RuntimeBindingError`, opaque identifier grammar (`^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$`, max 64).
- Enums added: `TransportKind` (LOCAL / NATIVE_SUBSCRIPTION / OFFICIAL_API / WEB_INTERACTIVE boundary-only), `AuthOwnership` (RUNTIME_MANAGED / SECRET_REF / BROWSER_PROFILE_MANAGED / NONE), `UsageVisibility` (UNAVAILABLE / ESTIMATED / EXACT). RunState / ExecutionTarget / ResumeMode untouched.
- Registry / Factory: fail-closed resolution of `reference.local`; unregistered profile or adapter factory fails closed; NO implicit reference fallback; no vendor-specific Core branches (static-check tested).
- RuntimeCapabilities extended backward-compatibly: `timeout_cleanup_verified`, `usage_visibility`, `auth_ownership`. Reference runtime declares timeout_cleanup_verified=True, usage UNAVAILABLE, auth NONE.
- Persistence: `run_binding_snapshots` table (PK run_id FK→runs.id, no cascade); repository insert-once / get-by-run / update-rejected / delete-rejected; ORM before_update/before_delete listeners reject mutation fail-closed; unknown snapshot_schema_version fails closed on reload.
- Execution boundary: `execute_existing_run()` resolves the profile via Registry BEFORE the CAS claim, then claim + immutable snapshot + CREATED→STARTING event commit in ONE transaction before any adapter invocation; any failure rolls back the whole transaction (Run stays CREATED, adapter never constructed). `execute_task()` inserts the binding in the same final transaction as Run persistence.
- Alembic 0002: creates table + two indexes; deterministic legacy/reference backfill for all existing Runs (polynexus/LOCAL/reference/builtin.reference, NULL profile ref/revision/adapter_version/secret_ref, legacy_backfill=true, schema v1, NONE/UNAVAILABLE; resolved_at = earliest STARTING event timestamp with id tie-break, fallback runs.created_at); one-per-run consistency check fails closed. Downgrade drops only 0002 artifacts.

## Legacy backfill truthfulness

Backfilled identities record that a Run predates runtime binding. They are NOT claims about what was actually resolved at execution time.

## Migration target

Migration executed ONLY inside pytest temporary isolated SQLite databases (alembic upgrade 0001 → seed → head → downgrade → re-upgrade → reopen). No real/user/production database touched; no alembic command run outside tests.

## Verification (actual commands, Attempt 4 — all exit code 0)

Launcher: `C:\temp_pn_venv2\Scripts\python.exe` (3.13), per the Attempt-4 Re-Acceptance command set (`-B -rA` variants executed; summary lines quoted from `-rN` runs of identical targets).

- pytest `-B -m pytest -q -rA --disable-warnings services\core\tests\test_wp14b_runtime_binding.py` -> all PASSED incl. new `test_migration_installs_run_delete_guard_and_fails_closed`; `84 passed`; exit code 0
- pytest `-q -rA --disable-warnings services\core\tests\test_persistence.py services\core\tests\test_runtime_skeleton.py` -> no FAILED/ERROR; `60 passed`; exit code 0
- pytest `-q -rA --disable-warnings test_wp07_integration.py test_wp09_execution_api.py test_wp09_query_api.py` -> no FAILED/ERROR; 1 SKIPPED (Windows symlink policy, pre-existing, explicitly labeled); `72 passed, 1 skipped`; exit code 0
- pytest `--collect-only --disable-warnings services\core` -> `479 tests collected`; exit code 0
- pytest `--disable-warnings -rN services\core` -> `478 passed, 1 skipped in 123.41s`; exit code 0
- `.\scripts\validate_baseline.py` -> PASS; exit code 0
- `.\tools\validate-polynexus-governance.ps1 -RepoRoot D:\AI學習教材\PolyNexus` -> PASS; exit code 0
- `git diff --check` -> clean (CRLF/LF warning on test_persistence.py is non-fatal); exit code 0

The pytest temp-dir `PermissionError` at interpreter exit remains a non-fatal Windows environment warning; every command above returned exit code 0. SKIPPED items: exactly 1 (WP-07 symlink policy test) — labeled SKIPPED, not PASS.

## Verification (historical, Attempt 3 — all exit code 0)

## Verification (historical, Attempt 2 — all exit code 0)

- pytest `-q services\core\tests\test_wp14b_runtime_binding.py` -> JUnit XML `tests=80 failures=0 errors=0 skipped=0`; exit code 0
- pytest `-q services\core\tests\test_persistence.py` -> `tests=43 failures=0 errors=0 skipped=0`; exit code 0
- pytest `-q services\core\tests\test_runtime_skeleton.py` -> `tests=17 failures=0 errors=0 skipped=0`; exit code 0 (PRE-WP14-A regression)
- pytest `-q test_wp07_integration.py test_wp09_execution_api.py` -> `tests=49 failures=0 errors=0 skipped=1`; exit code 0
- pytest `--collect-only --disable-warnings services\core` -> `475 collected`; exit code 0
- pytest `-q --disable-warnings services\core` -> JUnit XML `tests=475 failures=0 errors=0 skipped=1` (474 passed); exit code 0
- `.\scripts\validate_baseline.py` -> PASS; exit code 0
- `tools\validate-polynexus-governance.ps1 -RepoRoot D:\AI學習教材\PolyNexus` -> PASS; exit code 0
- `git diff --check` -> clean (CRLF/LF warning on test_persistence.py is non-fatal); exit code 0

Python runtime: controlled launcher `C:\temp_pn_venv2\Scripts\python.exe` (3.13) creates processes normally in the Unicode repository path; no production dependency installed or added.

## Protected areas respected

Not modified: domain/models.py, domain/run_lifecycle.py, runtime/supervisor.py, persistence/database.py, api/* (schemas/dependencies/runs/app), alembic 0001, apps/web/, workflows/, dependencies/lockfiles, ADR decision text, excluded dirty files `docs/15_DOCUMENT_INDEX.md` and `docs/tasks/WP-12.md`.

## Known limitations

- SQLite FK enforcement is not assumed; snapshot↔run integrity is enforced by the repository contract, ORM listeners, and database-level triggers rather than pragma settings.
- WEB_INTERACTIVE is boundary-only; NATIVE_SUBSCRIPTION / OFFICIAL_API have no execution path in this gate.
- No public API provenance endpoint was added (not in the 15-file allowlist); API response surface for secret exclusion is NOT_IN_SCOPE / UNVERIFIED this round.
- Application log capture (logging handlers / stdout / stderr / caplog) is NOT_IN_SCOPE / UNVERIFIED — no logging surface exists in the Core runtime source within this allowlist.
- Exports/handoff marker scan is NOT_IN_SCOPE / UNVERIFIED (no export/handoff mechanism exists in Core scope).
- Attempt 3 Codex Finding 4 (Reviewer environment could not create processes via `C:\temp_pn_venv2` launcher) did NOT recur in the Attempt-4 review round; if it recurs, evidence remains Writer-side only.

## Unverified items

- Fresh independent Codex re-review verdict for Attempt 4: `VERIFIED_PASS`; Human acceptance granted 2026-08-26.
- API response surface, application log capture, and exports/handoff marker scans: NOT_IN_SCOPE / UNVERIFIED (see matrix above).
- Exact-allowlist Git checkpoint is in progress; final SHA is recorded after commit. Push, remote modification and real/user database migration remain unauthorized.
- Migration against real/user databases (prohibited here).

## Do not change

- Do not expand the accepted 15-file checkpoint into WP-14/WP-15 production adapter work, real-database migration, push or remote changes.
- Do not start WP-14/WP-15 production adapter work from this task.
- Do not modify excluded dirty files or absorb them into any future allowlist.
