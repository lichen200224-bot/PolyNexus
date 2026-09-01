# V1 Known Limitations

These limitations are intentional boundaries, not hidden compatibility
claims.

## Current RC status — 2026-09-02 (G22 RC hardening; G21 bounded browser evidence)

- CP04 WP21 is `PASS` only for the controlled synthetic-host real Chrome/CDP
  fixture: 3/3 golden journeys and 28/28 failure paths passed. This does not
  certify live vendor behavior.
- CP06/RC is `PROVISIONALLY_ACCEPTED_WITH_LIMITATIONS` by explicit Human
  decision; current evidence does not certify browser/vendor compatibility and
  must not be upgraded to `SUPPORTED` or `CERTIFIED`.
- G21 independent review found an encoded-loopback traversal gap; G22 adds the
  raw percent-encoded separator guard and regression coverage. Live vendor
  browser acceptance remains deferred/unverified.

- Real ChatGPT, Claude, Gemini, and other vendor browser journeys are
  `UNVERIFIED`; vendor DOM behavior is not certified.
- Browser failure-path acceptance remains dependent on a real browser
  runtime and manual confirmation where required. Automatic send is not
  allowed.
- No vendor login, credential, cookie, token, or external send was used; no
  browser profile was retained. The fixture uses vendor-shaped local pages only.
- G21 `npm ci` was blocked by environment permissions/registry access; that is
  historical G21 evidence. G22 clean dependency restore in this isolated lane
  passed under approved elevation, followed by Web Vitest `80/80` and production
  build exit `0`.
- A fresh G22 browser harness rerun was `NEED_ACTION`: the isolated Chrome
  process did not expose the requested CDP listener and the harness returned
  exit `1`. The G21 HTTPS artifact remains the current predecessor evidence;
  native browser-loaded MV3 worker dispatch and live vendor journeys remain
  `UNVERIFIED`.
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
