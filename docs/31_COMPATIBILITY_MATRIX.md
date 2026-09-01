# PolyNexus V1 Compatibility Matrix

This is a bounded V1 release-candidate matrix. It records only capabilities
that have a deterministic local source and does not certify broad vendor or
browser compatibility.

## Current checkpoint — 2026-09-02 (G21 bounded browser evidence)

- Candidate documentation reconciliation is based on the exact G20 predecessor
  `48062f1cae608785a39539e1a7bfca5d6726a92e` plus the G21 bounded checkpoint.
- Current non-browser CP06 evidence and the G21 handoff are recorded in
  `docs/12_HANDOFF_CURRENT.md`.
- CP04 WP21 has a bounded `PASS` for the synthetic real-browser fixture only;
  this is not a live browser, vendor, or certification PASS.
- Human decision `ACCEPT_RC_WITH_WP21_DEFERRED_UNVERIFIED` is recorded; CP06/RC
  is `PROVISIONALLY_ACCEPTED_WITH_LIMITATIONS` and is not browser/vendor
  certification.

| Surface | Current maturity | Current evidence source | Boundary / limitation |
|---|---|---|---|
| Reference local runtime | `PREVIEW` | Core runtime skeleton and CP06 failure-injection tests | Deterministic reference adapter; not a production model provider. |
| Loopback LocalModelEndpoint | `EXPERIMENTAL` | CP04 local routing tests and WP29 policy tests | Loopback-only; cancellation and cleanup of accepted HTTP work are not proven. |
| Runtime selection and policy | `PREVIEW` | G16/G18 and CP06 WP29 tests | Unknown profile, capability mismatch, credentialed endpoint, and external endpoint fail closed. |
| Alembic migration and isolated SQLite restore | `PREVIEW` | G17/WP23 and CP06 WP30 tests | Temporary isolated SQLite only; no user or production database is touched. |
| Browser companion / vendor drivers | `IN_DEVELOPMENT` | Static driver tests plus bounded Chrome/CDP synthetic-host fixture (`3/3` golden, `22/22` failure paths) | Live vendor DOM/login/send compatibility remains unverified; no vendor certification or automatic send. |
| Web UI | `PREVIEW` | Current Vitest and build evidence | No claim of production deployment or external connector support. |

## Routing boundary

V1 is `LOCAL_ONLY`; there is no external connector and no silent cloud fallback,
silent downgrade, or automatic policy bypass. Maturity labels are descriptive and
must be re-evaluated from current evidence at each release checkpoint.

## Evidence rule

The authoritative exact commit, UTC timestamp, command, exit code, and
freshness state for the current checkpoint are recorded in
`docs/12_HANDOFF_CURRENT.md`. Historical roadmap statements are not current
acceptance evidence.
