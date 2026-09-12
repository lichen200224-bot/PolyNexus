# D0 writer handoff

Candidate identity is the immutable commit containing this handoff; the Controller's external receipt records its exact SHA after commit creation.

Implemented only bounded D0:

- SQLite detection is based on the SQLAlchemy URL/dialect, not filename text. Every SQLite DBAPI connection enables foreign-key enforcement. Startup no longer forces WAL.
- Startup performs a read-only `PRAGMA foreign_key_check` plus fixed application-relationship audit. Damage stops startup without repair or deletion; recovery remains backup-first and Human-controlled.
- An unclaimed `CREATED` Run survives restart with no binding, event, adapter contact, or launch. A claimed/non-terminal Run still requires its immutable binding. The impossible combination `CREATED` plus a non-legacy claimed binding fails closed.
- Health keeps the existing process-liveness fields and adds distinct schema, database-integrity, Core, API-auth, Web-client, and runtime layers. Unobserved Web/runtime readiness remains explicitly `unknown`.
- Alembic remains the only schema authority. No migration, dependency, frontend, extension, workflow, schema-contract, Frozen, security, Human, or Assurance file changed.

Review focus:

1. Ensure the fixed relationship queries cover D0's non-FK scalar references without mutating legacy data.
2. Ensure startup fail-closed behavior cannot launch or rebind an unclaimed `CREATED` Run.
3. Ensure health does not overclaim UI/runtime readiness or expose the loopback token.
4. Confirm all changed paths are inside the D0 pre-write allowlist.

One existing full-suite test was skipped because Windows denied symlink creation; its explicit skip text states that sibling-prefix and regex containment tests provide partial coverage. No D0 test was skipped.
