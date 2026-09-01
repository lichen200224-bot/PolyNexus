# V1 Known Limitations

These limitations are intentional boundaries, not hidden compatibility
claims.

## Current RC status — 2026-09-01

- CP04 WP21 is intentionally `DEFERRED / UNVERIFIED` while the operator is
  unavailable for the real browser failure-path check.
- CP06/RC is `PROVISIONALLY_ACCEPTED_WITH_LIMITATIONS` by explicit Human
  decision; current evidence does not certify browser/vendor compatibility and
  must not be upgraded to `SUPPORTED` or `CERTIFIED`.
- The next route is to retain the disclosed limitations. WP21 browser
  acceptance remains optional and requires fresh authorization when an operator
  is available.

- Real ChatGPT, Claude, Gemini, and other vendor browser journeys are
  `UNVERIFIED`; vendor DOM behavior is not certified.
- Browser failure-path acceptance remains dependent on a real browser
  runtime and manual confirmation where required. Automatic send is not
  allowed.
- `LocalModelEndpointAdapter` reports conservative cancellation and cleanup
  capabilities because synchronous HTTP completion cannot prove that a local
  server stopped accepted work.
- The reference workflow executor is a minimal lifecycle boundary; complete
  declarative step execution is future work.
- Windows symlink containment coverage may be skipped when the host policy
  denies symlink creation. The skip must remain visible in acceptance output.
- Runtime Doctor reports are bounded internal diagnostics. They must not be
  promoted to `SUPPORTED` or `CERTIFIED` without current evidence.
- CP06 evidence is local and deterministic only. No cloud fallback, external
  connector, real user database, or raw credential is part of this V1 gate.

Any future change that removes a limitation requires a separately scoped task,
current evidence, and the applicable architecture or human decision gate.
