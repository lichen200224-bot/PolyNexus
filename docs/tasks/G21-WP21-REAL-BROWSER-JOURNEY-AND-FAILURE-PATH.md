# G21 — WP21 real-browser journey and failure-path acceptance

## Result

`NEED_ACTION` for final checkpoint closure: deterministic bounded fixture gates
passed, but the required independent review has not returned a conclusion.
The bounded evidence itself is `PASS` within the `REAL_BROWSER_LOCAL_FIXTURE`
claim only.

- `TASK_ID`: `G21-WP21-REAL-BROWSER-JOURNEY-AND-FAILURE-PATH`
- `ATTEMPT`: 1
- `BRANCH`: `feature/g21-wp21-real-browser-journey-failure-path`
- `PREDECESSOR_SHA`: `48062f1cae608785a39539e1a7bfca5d6726a92e`
- `WRITER`: Codex, sole writer for the bounded loopback fix and evidence/docs
- `ANTIGRAVITY_STATUS`: `REQUIRED / COMPLETED` by the available real Chrome/CDP browser lane; no live-vendor journey was attempted
- `ADR_IMPACT`: `NONE`; ADR-001–010 remain frozen and ADR-011 is unchanged
- `SCOPE_DEVIATION`: `NONE`; one fail-closed browser-companion traversal guard was fixed
- `REVIEW_STATUS`: `PENDING`; independent review fork was invoked but remained
  active without a result, so no independent PASS is claimed

## Real-browser environment and golden journey

The run used Chrome `152.0.7977.65` (`Protocol-Version 1.3`) with an isolated temporary profile and the unpacked MV3 extension manifest version `0.1.0`. A controlled local HTTPS fixture was host-mapped to `chatgpt.com`, `claude.ai`, and `gemini.google.com`; the browser URL therefore exercised each exact driver matcher while all requests terminated locally.

The Web AI Decision Review route passed for all three profiles:

1. select the exact driver from the host-mapped route;
2. detect the synthetic composer in the real DOM;
3. fill a non-sensitive synthetic review instruction;
4. verify no send before confirmation;
5. verify the confirmation response declares `automatic_send: false`;
6. confirm a send only against the controlled fixture;
7. capture and normalize the synthetic response as `AI_OPINION`, with the marker redacted.

Golden result: `3/3 PASS`, process exit code `0`.

## Failure paths

The matrix records `22/22 PASS`, each with setup, expected/actual result, exit code, cleanup, and maturity impact. Covered paths include unknown vendor, missing target, selector/DOM drift, loopback unavailable and timeout-like transport failure, driver exception, tab close, capture and normalization failure, malformed request, restricted LOCAL_ONLY egress, credentialed/external endpoint rejection, cancel/abort by non-confirmation, Core unavailable, no silent cloud fallback, truthful degraded/partial result, secret/path redaction, MV3 worker lifecycle, and cleanup.

The current contract has no independent browser `CANCEL` action; the abort boundary was verified by `SEND_CONFIRMED` with `confirmed: false`, which produced `user_confirmation_required` and no send.

## Bounded fix

`extensions/browser-companion/src/loopback-client.js` now rejects raw endpoint values containing `..` before URL normalization can erase a path-traversal segment. The existing browser-companion test suite includes the regression input `http://127.0.0.1:4312/../escape`.

## Evidence

- [environment.json](../../verification/g21-browser-20260902/environment.json)
- [journey-matrix.json](../../verification/g21-browser-20260902/journey-matrix.json)
- [failure-path-matrix.json](../../verification/g21-browser-20260902/failure-path-matrix.json)
- [summary.json](../../verification/g21-browser-20260902/summary.json)
- [commands-and-exit-codes.md](../../verification/g21-browser-20260902/commands-and-exit-codes.md)
- [SHA256SUMS.txt](../../verification/g21-browser-20260902/SHA256SUMS.txt)
- screenshots: `chatgpt-com-golden.png`, `claude-ai-golden.png`, `gemini-google-com-golden.png`
- [cdp-trace.json](../../verification/g21-browser-20260902/cdp-trace.json), 1,028 trace events, no network bodies/cookies/headers

All result JSON and trace scans found no raw synthetic marker, token, cookie, authorization, password, or path. Browser profiles and temporary certificates were not retained.

## Live-vendor maturity

| Profile | Classification |
|---|---|
| ChatGPT public/authenticated surface | `DEFERRED / UNVERIFIED`; no login or live traffic |
| Claude public/authenticated surface | `DEFERRED / UNVERIFIED`; no login or live traffic |
| Gemini public/authenticated surface | `DEFERRED / UNVERIFIED`; no login or live traffic |
| Controlled host-mapped fixture | `VERIFIED_WITHIN_BOUNDED_PUBLIC_SURFACE` |

`VENDOR_CERTIFICATION: NOT_CLAIMED` and `AUTOMATIC_SEND: PROHIBITED_AND_VERIFIED_NOT_USED`.
