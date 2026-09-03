# G27 independent review — 2026-09-03

`VERDICT=PASS`; `BLOCKER=0`; `MAJOR=0`; `MINOR=0`.

The independent read-only reviewer inspected the G27 diff against
`7a7dee67395c8a07f2e5b055a306e63190bbd1f8`, the WP-22/24/25 records, workflow
schema/templates, supervisor cleanup paths, metrics identity binding,
scope/ADR/security constraints, and the recorded verification evidence.

Confirmed findings:

- Exactly nine V1 built-in templates are enforced by
  `services/core/tests/test_workflow_loader.py:28`.
- Setup failures preserve an allocated runtime reference and use fail-closed
  cleanup in `services/core/src/polynexus_core/runtime/supervisor.py:240-268`.
- Cross-task evidence is rejected even when `run_id` matches in
  `services/core/src/polynexus_core/evaluation/metrics.py:78-82`.
- Existing redaction/failure behavior remains compatible; no migrations,
  persisted entities, secrets, vendor integrations, arbitrary script nodes,
  or G28 scope were introduced.

The reviewer could not independently start pytest in its separate review
environment. Therefore test claims in this review refer only to the current
isolated-lane commands and their actual exit codes in
`commands-and-exit-codes.md`.
