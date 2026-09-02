# PolyNexus V1 Compatibility Matrix

This is a bounded V1 release-candidate matrix. It records only capabilities
that have a deterministic local source and does not certify broad vendor or
browser compatibility.

## G24 current reconciliation boundary — 2026-09-02

- `G24_START_SHA`: `fde4c8f1d017992755c6af2bd600c9bd715efd6b`.
- `G24_STATUS`: `VERIFIED_PASS_PENDING_HUMAN`; `GOAL_SCORE_DELTA=0`;
  development progress remains `59/100`.
- The G24 ledger reconciles implementation/evidence/maturity labels only. It
  does not promote any capability or change the matrix below.

## Planned completion routing — 2026-09-02

- The Human-confirmed G24–G30 program preserves all current maturity labels.
  Planning does not convert a capability into `SUPPORTED` or `CERTIFIED`.
- G26 covers deterministic/internal WP-17/18/19 compatibility work. The
  Human-operated authenticated WP-20 vendor journeys are intentionally delayed
  to G29, after G28 feature-freeze evidence.
- Until G29 produces current vendor-specific evidence, ChatGPT/Claude/Gemini
  authenticated journeys and native MV3 dispatch remain `UNVERIFIED`, and
  vendor certification remains `NOT_CLAIMED`.
- Formal development progress is `59/100`; Competition is
  `NOTE_ONLY_NON_SCORING` and has no compatibility maturity effect.

## Current checkpoint — 2026-09-02 (G23 Human-accepted final reconciliation)

- G23 is `HUMAN_ACCEPTED / PASS / COMPLETE` at exact accepted SHA
  `0eb56a986e97a45854bd6ddd419c114845ce51f4` on the approved G22 remote ref.
- Acceptance covers repository-backed G19–G22 terminal evidence, bounded RC
  hardening, delivery packaging, and cross-machine continuation.
- Compatibility and maturity labels below are intentionally unchanged by G23:
  the acceptance does not certify live vendors, native MV3 dispatch, or an
  authenticated external-send journey.
- Formal project progress is `59/100` under the current development-only
  allocation.
  Compatibility labels remain evidence-bounded; recognized points do not turn
  `PREVIEW`, `IN_DEVELOPMENT`, or `UNVERIFIED` capabilities into certification.

### Predecessor compatibility evidence — G22 / G21

- Candidate documentation reconciliation is based on the exact G21 predecessor
  `ada5e9c8b4873aad4c53c74198171740d376d926` plus the current G22 hardening
  delta.
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
| Browser companion / vendor drivers | `IN_DEVELOPMENT` | Static driver tests plus bounded Chrome/CDP HTTPS synthetic-host fixture (`3/3` golden, `28/28` failure paths); G22 encoded-loopback traversal regression | Live vendor DOM/login/send compatibility remains unverified; native browser-loaded MV3 worker dispatch remains unverified; no vendor certification or automatic send. |
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
