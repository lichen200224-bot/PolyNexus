# D0 writer handoff

Candidate identity is the immutable commit containing this handoff; the Controller's external receipt records its exact SHA after commit creation.

Implemented only bounded D0:

- SQLite detection is based on the SQLAlchemy URL/dialect, not filename text. Every SQLite DBAPI connection enables foreign-key enforcement. Startup no longer forces WAL.
- Startup performs a read-only `PRAGMA foreign_key_check` plus fixed application-relationship audit. Damage stops startup without repair or deletion; recovery remains backup-first and Human-controlled.
- Serialized RunResult references are also audited for valid JSON, unique IDs, target existence, and Run/Task ownership without mutation.
- An unclaimed `CREATED` Run survives restart with no binding, event, adapter contact, or launch. A claimed/non-terminal Run still requires its immutable binding. The impossible combination `CREATED` plus a non-legacy claimed binding fails closed.
- The restart proof now uses authenticated Project/Context/Task/CreateRun API calls, closes the app, starts a fresh app, then queries the same CREATED Run and confirms no binding row.
- Health keeps the existing process-liveness fields and adds distinct schema, database-integrity, Core, API-auth, Web-client, and runtime layers. Unobserved Web/runtime readiness remains explicitly `unknown`.
- Alembic remains the only schema authority. No migration, dependency, frontend, extension, workflow, schema-contract, Frozen, security, Human, or Assurance file changed.

Review focus:

1. Ensure the fixed relationship queries cover D0's non-FK scalar references without mutating legacy data.
2. Ensure startup fail-closed behavior cannot launch or rebind an unclaimed `CREATED` Run.
3. Ensure health does not overclaim UI/runtime readiness or expose the loopback token.
4. Confirm all changed paths are inside the D0 pre-write allowlist.

One existing full-suite test was skipped because Windows denied symlink creation; its explicit skip text states that sibling-prefix and regex containment tests provide partial coverage. No D0 test was skipped.

Independent review of candidate `894cdc407874099f7c29ffb1b9ea72da4b8073f8` returned NEED_FIX. Its two Core findings are repaired in the subsequent commit. Its remaining finding is a governance exception: the unchanged default Web client supplies no auth headers, so Frozen S0's UI/Core pairing and Fresh-client-from-START journey require a bounded `apps/**`/start authorization before D0 can receive a technical PASS.
