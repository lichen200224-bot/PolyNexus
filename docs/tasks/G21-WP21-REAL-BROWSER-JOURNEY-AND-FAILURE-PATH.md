# G21 — WP21 real-browser journey and failure-path acceptance

## Result

`PASS` for the current deterministic bounded evidence-harness gates. The claim
is limited to `REAL_BROWSER_LOCAL_FIXTURE` plus the actual service-worker
listener's equivalent extension-dispatch shim; native browser-loaded
service-worker dispatch and live vendor certification remain `UNVERIFIED`.
The checkpoint commit and push are authorized after the completed gates; the
exact final SHA is recorded in the completion result. No final Human product
acceptance is claimed.

- `TASK_ID`: `G21-WP21-REAL-BROWSER-JOURNEY-AND-FAILURE-PATH`
- `ATTEMPT`: 2
- `BRANCH`: `feature/g21-wp21-real-browser-journey-failure-path`
- `PREDECESSOR_SHA`: `48062f1cae608785a39539e1a7bfca5d6726a92e`
- `WRITER`: Codex, sole writer for the bounded loopback fix and evidence/docs
- `ANTIGRAVITY_STATUS`: `REQUIRED / COMPLETED` by the available real Chrome/CDP browser lane; no live-vendor journey was attempted
- `ADR_IMPACT`: `NONE`; ADR-001–010 remain frozen and ADR-011 is unchanged
- `SCOPE_DEVIATION`: `NONE`; one fail-closed browser-companion traversal guard was fixed
- `REVIEW_STATUS`: `NOT_REQUIRED_FOR_THIS_WRITER_RUN`; this result is based on
  the current deterministic commands only and is not an independent review

## Real-browser environment and golden journey

The run used Chrome `152.0.7977.65` (`Protocol-Version 1.3`) with an isolated temporary profile. A controlled local HTTPS fixture ran on loopback using a SAN certificate for `127.0.0.1` and `localhost`; each browser route selected the ChatGPT, Claude, or Gemini fixture DOM using an explicit `vendor` selector. No live vendor request was made.

The Web AI Decision Review route passed for all three profiles:

1. select the exact driver from the host-mapped route;
2. detect the synthetic composer in the real DOM;
3. fill a non-sensitive synthetic review instruction;
4. verify no send before confirmation;
5. verify the confirmation response declares `automatic_send: false`;
6. confirm a send only against the controlled fixture;
7. capture and normalize the synthetic response as `AI_OPINION`, with the marker redacted.

Golden result: `3/3 PASS`; each matrix row is an in-process assertion with
`exit_code: "N/A"`; the aggregate harness process exit code was `0`.

## Failure paths

The matrix records `28/28 PASS`, each with setup, expected/actual result,
`exit_code: "N/A"` for its in-process assertion, cleanup, and maturity impact.
It includes actual service-worker listener dispatch for unknown action, invalid
tab ID, unknown vendor, missing confirmation, and confirmed-send boundary.
Core unavailable and loopback failure/timeout use an observed request spy;
`external_requests` is computed from the observed calls, not a fixed value.
Cleanup closes browser page targets and the fixture server in `finally`; cleanup
failure changes the aggregate process exit to `1`.

The current contract has no independent browser `CANCEL` action; the abort boundary was verified by `SEND_CONFIRMED` with `confirmed: false`, which produced `user_confirmation_required` and no send.

## Bounded fix

`extensions/browser-companion/src/loopback-client.js` now rejects raw endpoint values containing `..` before URL normalization can erase a path-traversal segment. The existing browser-companion test suite includes the regression input `http://127.0.0.1:4312/../escape`.

## Evidence

- [environment.json](../../artifacts/verification/g21-browser-20260902/environment.json)
- [journey-matrix.json](../../artifacts/verification/g21-browser-20260902/journey-matrix.json)
- [failure-path-matrix.json](../../artifacts/verification/g21-browser-20260902/failure-path-matrix.json)
- [summary.json](../../artifacts/verification/g21-browser-20260902/summary.json)
- [commands-and-exit-codes.md](../../artifacts/verification/g21-browser-20260902/commands-and-exit-codes.md)
- [SHA256SUMS.txt](../../artifacts/verification/g21-browser-20260902/SHA256SUMS.txt)
- screenshots: `chatgpt-com-golden.png`, `claude-ai-golden.png`, `gemini-google-com-golden.png`
- [cdp-trace.json](../../artifacts/verification/g21-browser-20260902/cdp-trace.json), current trace events, no network bodies/cookies/headers

All result JSON and trace scans found no raw synthetic marker, token, cookie, authorization, password, or path. Browser profiles and temporary certificates were not retained.

## Live-vendor maturity

| Profile | Classification |
|---|---|
| ChatGPT public/authenticated surface | `DEFERRED / UNVERIFIED`; no login or live traffic |
| Claude public/authenticated surface | `DEFERRED / UNVERIFIED`; no login or live traffic |
| Gemini public/authenticated surface | `DEFERRED / UNVERIFIED`; no login or live traffic |
| Controlled host-mapped fixture | `VERIFIED_WITHIN_BOUNDED_PUBLIC_SURFACE` |

`VENDOR_CERTIFICATION: NOT_CLAIMED` and `AUTOMATIC_SEND: PROHIBITED_AND_VERIFIED_NOT_USED`.
