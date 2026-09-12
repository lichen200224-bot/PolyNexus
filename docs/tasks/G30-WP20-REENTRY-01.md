# G30-WP20-REENTRY-01 — Operator-Pack Revalidation

## Decision

- `TASK_ID`: `G30-WP20-REENTRY-01`
- `ROLE`: `G30_REENTRY_PLANNER_AND_VALIDATOR`
- `CANONICAL_START_SHA`: `08d00294bf826f27eeb82fc799836dbb39f024de`
- `BRANCH`: `feature/g30-wp20-live-vendor-closure`
- `HEAD_AT_REVALIDATION`: `08d00294bf826f27eeb82fc799836dbb39f024de`
- `RESULT`: `G30_WP20_OPERATOR_READY`
- `G30_STATUS`: `READY_FOR_HUMAN_LIVE_VENDOR_EXECUTION`
- `WP20_STATUS`: `0/5_PENDING_LIVE_EVIDENCE`
- `OPERATOR_PACK_DECISION`: `REUSE_AS_IS`
- `BASELINE_DEBT_01_IMPACT_ON_OPERATOR_PACK`: `NONE`
- `NEXT_REQUIRED_ROLE`: `HUMAN_OR_ANTIGRAVITY_LIVE_VENDOR_OPERATOR`

No live vendor account, credential, cookie, token, private page content, or
external send was accessed by Codex. No fixture result is treated as live
acceptance evidence.

## Revalidation evidence

The current `08d0029...` baseline contains the same approved vendor origins and
driver contract used by the pack:

| Pack item | Current | Stale | Conflicts with baseline | Security safe | Requires update | Reason |
|---|---|---|---|---|---|---|
| `G29-EXTERNAL-OPERATOR-PROMPT.md` | Yes | No | No | Yes | No | Launch/detect/fill/confirm/send/capture/normalize/cleanup and stop rules match the current companion boundary. |
| `G29-EXTERNAL-OPERATOR-RUNBOOK.md` | Yes | No | No | Yes | No | Three-vendor procedure, safe payload, failure paths, cleanup and redaction rules remain applicable. |
| `G29-EXTERNAL-TEST-MATRIX.md` | Yes | No | No | Yes | No | ChatGPT, Claude, Gemini and required fallback/failure rows remain covered. |
| `G29-EXTERNAL-REPORT-TEMPLATE.md` | Yes | No | No | Yes | No | Required sanitized fields and `EXIT_CODE: N/A` rule remain compatible. |
| `G29-HUMAN-OPERATOR-TEST-MANUAL.html` | Yes | Historical date/status labels only | No | Yes | No | The 2026-09-03 labels describe prior preparation/probe evidence; they do not weaken the live-send or secret boundary. |
| `G30-FINAL-EXTERNAL-VERIFICATION-AND-100-POINT-RECONCILIATION.md` | Yes | Prior G30 attempt is historical | No | Yes | No | It correctly records missing reports as `NEED_ACTION` and requires fresh Human evidence. |

Current source checks confirm `https://chatgpt.com/*`, `https://claude.ai/*`,
and `https://gemini.google.com/*` are the allowlisted origins; each driver
pauses for explicit confirmation, has no automatic-send path, normalizes to
bounded `AI_OPINION`, and falls back to sanitized manual/clipboard handling.

`BASELINE_DEBT_01_IMPACT_ON_OPERATOR_PACK=NONE`: ADR-014 changes durable event
sequence allocation and cancellation/cleanup persistence. It does not change
vendor origins, driver selectors, confirmation semantics, report fields,
credential restrictions, or live-result interpretation.

## Minimum current execution plan

Run the following per vendor in a fresh tab or isolated test conversation. The
Human account owner owns login consent and every real send.

| Vendor | Preconditions | Human action | Expected visible result | Failure result |
|---|---|---|---|---|
| ChatGPT | Supported browser/companion; designated non-production account; owner present; approved origin `chatgpt.com` | Launch, detect composer, fill only the approved safe payload, inspect exact text/target, explicitly confirm, then send; capture bounded reply and clean up | `LAUNCH=PASS`, `DETECT=PASS`, `FILL=PASS`, `HUMAN_CONFIRMED_SEND=YES`, bounded `CHECKED received`-type result, normalized `AI_OPINION`, cleanup pass | Unavailable/expired auth, selector drift, send rejection, timeout, capture/normalize failure, or cancellation yields bounded degraded/manual fallback and no unintended send |
| Claude | Same; approved origin `claude.ai` | Same sequence and confirmation boundary | Same fields with `TEST_TARGET=Claude` | Same bounded failure handling; no secret/raw response |
| Gemini | Same; approved origin `gemini.google.com` | Same sequence and confirmation boundary | Same fields with `TEST_TARGET=Gemini` | Same bounded failure handling; no secret/raw response |

The per-vendor path minimum is explicit below; every row is required for each
vendor and failure rows must not add a real send:

| Vendor | Success path | Authentication unavailable | UI/DOM drift | Send/dispatch failure | Timeout | Cancellation/recovery | Sanitization check |
|---|---|---|---|---|---|---|---|
| ChatGPT | launch → detect → fill → owner-confirmed send → capture → normalize → cleanup | `LOGIN_STATUS=EXPIRED` or `UNAVAILABLE`; stop before send | bounded driver failure; manual/clipboard fallback | bounded degraded result; no retry or unintended send | agreed timeout; cleanup verified; no send | confirmation declined or cancellation leaves no send and records recovery/fallback | no credentials/cookies/tokens/raw page data; refs and summary redacted |
| Claude | same success sequence on `claude.ai` | same bounded unavailable path; no send | same bounded drift path; no vendor-page modification | same bounded dispatch failure; no additional send | same timeout and cleanup rule | same cancel/recovery rule | same report and artifact redaction rule |
| Gemini | same success sequence on `gemini.google.com` | same bounded unavailable path; no send | same bounded drift path; no vendor-page modification | same bounded dispatch failure; no additional send | same timeout and cleanup rule | same cancel/recovery rule | same report and artifact redaction rule |

Each sanitized report must include:

`TEST_TARGET`, `TEST_ACCOUNT_TYPE`, `OBSERVED_AT`, `EXIT_CODE`, browser and
extension versions, `ROUTE`, `FIXTURE_OR_LIVE`, login/launch/detect/fill/send
fields, capture/normalize/fallback results, failure-path outcomes, observed
external-request count (without bodies or headers), cleanup result, sanitized
screenshot/trace refs, `SECRETS_REDACTED`, bounded actual result, and blockers.

Evidence required for WP-20 acceptance is one complete sanitized `LIVE` report
for each of ChatGPT, Claude, and Gemini, plus the required failure/fallback and
cleanup evidence. `CONTROLLED_FIXTURE` remains useful for isolating failures but
cannot satisfy live vendor acceptance. Missing reports keep `WP20=0/5`.

## Deterministic validation

- `D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe -B scripts/validate_baseline.py`
  → baseline validation PASS, exit `0`.
- `powershell -NoProfile -ExecutionPolicy Bypass -File tools/validate-polynexus-governance.ps1`
  → governance validation PASS, exit `0`.
- `node --test extensions/browser-companion/tests/test_websurface_drivers.mjs`
  → `10 passed`, `0 failed`, `0 skipped`, exit `0`.
- `git diff --check` → clean, exit `0`.

The first baseline command using bare `python` was an environment lookup failure
(`python` not found, exit `1`); the repository's existing virtual environment
was used for the successful validator run. Full Core regression was not rerun,
as this task is re-entry/operator-pack validation and does not modify product
code.

## Scope and handoff

- Product code change: `NO`.
- ADR impact: `NONE`.
- Scope deviation: `NONE`.
- Changed files in this re-entry lane: this document and the current handoff.
- No commit, push, vendor login, credential handling, automatic send, or
  acceptance score change is authorized by this record.
- Next action: Human or explicitly authorized Antigravity operator executes the
  live ChatGPT/Claude/Gemini reports and returns sanitized evidence only.
