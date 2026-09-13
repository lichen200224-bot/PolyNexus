# D0 writer handoff

Candidate identity is the immutable commit containing this handoff; the Controller's external receipt records its exact SHA after commit creation.

Implemented only bounded D0:

- SQLite detection is based on the SQLAlchemy URL/dialect, not filename text. Every SQLite DBAPI connection enables foreign-key enforcement. Startup no longer forces WAL.
- Startup performs a read-only `PRAGMA foreign_key_check` plus fixed application-relationship audit. Damage stops startup without repair or deletion; recovery remains backup-first and Human-controlled.
- Serialized RunResult references are also audited for valid JSON, unique IDs, target existence, and Run/Task ownership without mutation.
- An unclaimed `CREATED` Run survives restart with no binding, event, adapter contact, or launch. A claimed/non-terminal Run still requires its immutable binding. The impossible combination `CREATED` plus a non-legacy claimed binding fails closed.
- The restart proof now uses authenticated Project/Context/Task/CreateRun API calls, closes the app, starts a fresh app, then queries the same CREATED Run and confirms no binding row.
- Health keeps the existing process-liveness fields and adds distinct schema, database-integrity, Core, API-auth, Web-client, and runtime layers. Unobserved Web/runtime readiness remains explicitly `unknown`.
- The approved process-only START launcher generates a 256-bit token, passes only `LOOPBACK_TOKEN` to Core and only `VITE_POLYNEXUS_LOOPBACK_TOKEN` to Vite, never prints it, and clears its own process variables after child launch.
- The development-only Web config retains the token in a closure and sends it only as `X-Loopback-Token`. Startup UI marks Web/client ready only after both layered health and a protected API request succeed. Missing/wrong credentials remain not ready.
- Production builds ignore the development token path; a synthetic sentinel build verified the value was absent from all `dist` bytes.
- START owns and cleans its child process trees. Its collision fallback snapshots pre-existing 127.0.0.1:5173/8765 listeners and stops only new Python/Node listeners created after START, preserving the pre-existing port owner.
- Alembic remains the only schema authority. No migration, dependency, frontend, extension, workflow, schema-contract, Frozen, security, Human, or Assurance file changed.

Review focus:

1. Ensure the fixed relationship queries cover D0's non-FK scalar references without mutating legacy data.
2. Ensure startup fail-closed behavior cannot launch or rebind an unclaimed `CREATED` Run.
3. Ensure health does not overclaim UI/runtime readiness or expose the loopback token.
4. Confirm all changed paths are inside the D0 pre-write allowlist.

One existing full-suite test was skipped because Windows denied symlink creation; its explicit skip text states that sibling-prefix and regex containment tests provide partial coverage. No D0 test was skipped.

Independent review of candidate `894cdc407874099f7c29ffb1b9ea72da4b8073f8` returned NEED_FIX. Its two Core findings were repaired and re-reviewed. Human then approved `D0-PAIRING-ARCHITECTURE-EXCEPTION — PROCESS_ONLY_SHARED_TOKEN`; this handoff includes that bounded implementation and requires fresh independent review of the new exact candidate before D0 may receive a technical PASS.
