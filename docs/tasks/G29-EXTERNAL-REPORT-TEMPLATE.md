# G29 External Report Template

> Routing update (2026-09-03): reports produced from this template belong to
> the deferred G30 external-verification run; no G29 result is implied.

Complete one copy per vendor or assigned route. Do not include secret values,
cookies, tokens, recovery codes, private conversation text, or account
identifiers. Use `EXIT_CODE: N/A` when the observation is manual and has no
local process exit code.

```text
TEST_TARGET: ChatGPT | Claude | Gemini
TEST_ACCOUNT_TYPE: designated non-production test account | no account available
OBSERVED_AT: YYYY-MM-DDThh:mm:ssZ
EXIT_CODE: 0 | 1 | N/A
BROWSER_VERSION: redacted version string
EXTENSION_VERSION: redacted version string
ROUTE: LIVE | CONTROLLED_FIXTURE | MANUAL_FALLBACK
FIXTURE_OR_LIVE: LIVE | CONTROLLED_FIXTURE
LOGIN_STATUS: READY | EXPIRED | UNAVAILABLE | NOT_TESTED
LAUNCH_RESULT: PASS | FAIL | NOT_TESTED
DETECT_RESULT: PASS | FAIL | NOT_TESTED
FILL_RESULT: PASS | FAIL | NOT_TESTED
HUMAN_CONFIRMED_SEND: YES | NO | NOT_APPLICABLE
CAPTURE_RESULT: PASS | FAIL | FALLBACK | NOT_TESTED
NORMALIZE_RESULT: PASS | FAIL | FALLBACK | NOT_TESTED
FALLBACK_RESULT: PASS | FAIL | NOT_TESTED
FAILURE_PATH_RESULTS: scenario=outcome; scenario=outcome
EXTERNAL_REQUESTS: observed count or NOT_OBSERVED; no request bodies/headers
CLEANUP_RESULT: PASS | FAIL | NOT_TESTED
SCREENSHOT_REFS: sanitized relative refs or NONE
TRACE_REFS: sanitized relative refs or NONE
SECRETS_REDACTED: YES | NO; describe categories only, never values
ACTUAL_RESULT: concise bounded observation
BLOCKERS: NONE or concise blocker
```

## Report validation checklist

- Every required field is present and uses an allowed value where specified.
- `ROUTE` and `FIXTURE_OR_LIVE` agree.
- `HUMAN_CONFIRMED_SEND=YES` is present only for an exact, account-owner
  confirmed safe payload; otherwise no send may be reported.
- `EXIT_CODE: N/A` is used for manual observations instead of an invented code.
- Screenshots/traces are relative, sanitized, and contain no account data or
  secrets.
- `EXTERNAL_REQUESTS` is an observation, not a claim derived from a fixed
  constant; request bodies and headers are never attached.
- Cleanup is explicit. Missing cleanup is not PASS.
- A fixture result is not relabeled as live vendor compatibility.
