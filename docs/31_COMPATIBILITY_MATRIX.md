# PolyNexus V1 Compatibility Matrix

This is a bounded V1 release-candidate matrix. It records only capabilities
that have a deterministic local source and does not certify broad vendor or
browser compatibility.

## G26 current candidate boundary — 2026-09-03

- `G26_STATUS=HUMAN_ACCEPTED / CHECKPOINT_PENDING_NEED_ACTION`; bounded G26
  Core/Web checks and independent review are verified, but full Core regression
  is exit `1`, so no G26 compatibility row earns score yet.
- WP-17 LocalModelEndpoint profiles (LM Studio/OpenAI-compatible, Ollama, and
  generic OpenAI-compatible): `EXPERIMENTAL / DETERMINISTIC_LOCAL_CONFORMANCE`
  candidate. Controlled endpoint evidence exists in source/tests; targeted G26
  Core tests are 14/14, exit `0`.
- WP-18 classification/routing/egress: `EXPERIMENTAL /
  DETERMINISTIC_POLICY_CONFORMANCE` candidate. Highest-classification,
  explicit mode, decision, and existing-Evidence audit mapping are implemented;
  targeted Core evidence is 14/14, exit `0`; full Core regression remains exit
  `1`.
- WP-19 WebSurface/loopback: `PREVIEW /
  DETERMINISTIC_WEBSURFACE_CONFORMANCE` candidate. Browser tests passed 10/10 in
  controlled Node fixtures, including service-worker loopback dispatch; Web
  Vitest 80/80 and production build also pass; live authenticated ChatGPT/Claude/Gemini journeys,
  native MV3 dispatch, and certification remain `UNVERIFIED`/`NOT_CLAIMED` for
  G29.
- No row is promoted to a higher maturity by this candidate; exact remote
  clean-clone verification remains required for the checkpoint.

## G24 current reconciliation boundary — 2026-09-02

- `G24_OUTPUT_SHA`: `61cc7420e290cd93eda787c30b54a93edf4ca9a`.
- `G24_STATUS`: `HUMAN_ACCEPTED / PASS / COMPLETE`; `GOAL_SCORE_DELTA=0`;
  development progress remains `59/100`.
- The G24 ledger reconciles implementation/evidence/maturity labels only. It
  does not promote any capability or change the matrix below.

## Planned completion routing — 2026-09-02

- The Human-confirmed G24–G30 program preserves all current maturity labels.
  Planning does not elevate any capability to a higher maturity state.
- G26 covers deterministic/internal WP-17/18/19 compatibility work. The
  Human-operated authenticated WP-20 vendor journeys are intentionally delayed
  to G29, after G28 feature-freeze evidence.
- Until G29 produces current vendor-specific evidence, ChatGPT/Claude/Gemini
  authenticated journeys and native MV3 dispatch remain `UNVERIFIED`, and
  vendor certification remains `NOT_CLAIMED`.
- Formal development progress is `72/100`; Competition is
  `NOTE_ONLY_NON_SCORING` and has no compatibility maturity effect.

## G25 current candidate boundary — 2026-09-02

- WP-14 Codex Runtime Adapter: `EXPERIMENTAL`; deterministic local conformance
  evidence exists, but no live Codex CLI/account or production certification.
- WP-15 OpenCode Runtime Adapter: `EXPERIMENTAL`; deterministic local
  conformance evidence exists, but no live OpenCode CLI/account or production
  certification.
- WP-16 Runtime Doctor: `PREVIEW`; it reports observed health/readiness,
  declarations, probe failures, version, and bounded evidence without promoting
  an observed or preview state to production support.
- `PREVIEW` here describes the Doctor diagnostic/reporting surface: it is not a
  runtime capability claim. The adapter rows use `EXPERIMENTAL` because they
  have deterministic local conformance evidence but no production/live-vendor
  integration evidence; the reference local runtime alone carries the highest
  bounded baseline label.
- These labels are Human-accepted checkpoint evidence; the required independent
  review returned PASS with no severity findings. No
  compatibility claim is made for live vendors, browser-loaded
  MV3 dispatch, network transports, or authenticated sessions.

## Current checkpoint — 2026-09-02 (G23 Human-accepted final reconciliation)

- G23 is `HUMAN_ACCEPTED / PASS / COMPLETE` at exact accepted SHA
  `0eb56a986e97a45854bd6ddd419c114845ce51f4` on the approved G22 remote ref.
- Acceptance covers repository-backed G19–G22 terminal evidence, bounded RC
  hardening, delivery packaging, and cross-machine continuation.
- Compatibility and maturity labels below are intentionally unchanged by G23:
  the acceptance does not certify live vendors, native MV3 dispatch, or an
  authenticated external-send journey.
- Formal project progress is `72/100` under the current development-only
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
