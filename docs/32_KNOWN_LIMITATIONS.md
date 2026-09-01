# V1 Known Limitations

These limitations are intentional boundaries, not hidden compatibility
claims.

## Current RC status — 2026-09-02 (G21 bounded browser evidence)

- CP04 WP21 is `PASS` only for the controlled synthetic-host real Chrome/CDP
  fixture: 3/3 golden journeys and 22/22 failure paths passed. This does not
  certify live vendor behavior.
- CP06/RC is `PROVISIONALLY_ACCEPTED_WITH_LIMITATIONS` by explicit Human
  decision; current evidence does not certify browser/vendor compatibility and
  must not be upgraded to `SUPPORTED` or `CERTIFIED`.
- The next route is to retain the disclosed limitations and complete the G21
  checkpoint review. Live vendor browser acceptance remains deferred/unverified.

- Real ChatGPT, Claude, Gemini, and other vendor browser journeys are
  `UNVERIFIED`; vendor DOM behavior is not certified.
- Browser failure-path acceptance remains dependent on a real browser
  runtime and manual confirmation where required. Automatic send is not
  allowed.
- No vendor login, credential, cookie, token, or external send was used; no
  browser profile was retained. The fixture uses vendor-shaped local pages only.
- G21 `npm ci` was blocked by environment permissions/registry access; Web test
  and build evidence used the dependency tree restored from the exact G20 clean
  clone. This is not a fresh-install PASS.
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
