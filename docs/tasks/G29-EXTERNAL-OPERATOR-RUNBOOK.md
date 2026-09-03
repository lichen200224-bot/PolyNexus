# G29 External Operator Runbook

> Routing update (2026-09-03): this pack was prepared in G29 and is deferred
> for execution in G30. It is not evidence that G29 or G30 has passed.

## Purpose and gate

This runbook is for the authorized Human operator who owns the test account and
every real send action for PolyNexus WP-20 Level 3A assisted Web automation.
It is compatibility evidence only; it does not authorize autonomous send or
vendor certification.

Codex must not receive or retain passwords, cookies, tokens, recovery codes,
private conversation content, account identifiers, or unredacted screenshots.
The operator must stop if a safe test account, consent, or a supported browser
is unavailable and report the blocker without bypassing account controls.

## Safe test payload

Use this harmless, non-personal payload exactly unless the account owner
approves an equivalent non-sensitive variant:

```text
PolyNexus G29 compatibility check. Reply with the single word CHECKED.
Do not include personal, confidential, production, or account data.
```

Do not paste real project context, private conversation text, customer data, or
secrets into a vendor page. Use a fresh test conversation where practical.

## Operator procedure

For each assigned vendor (ChatGPT, Claude, or Gemini), use a fresh tab or
isolated test conversation and record the browser/extension versions and local
observation time.

1. Confirm the account owner is present and explicitly authorizes this test.
2. Launch the vendor route from the companion. Record whether launch succeeds.
3. Detect/health-check the composer. Record the observed result.
4. Fill only the safe payload above. Pause and inspect the rendered content.
5. Send only after the account owner explicitly confirms the exact payload and
   target conversation. Record `HUMAN_CONFIRMED_SEND=YES` only then.
6. Capture the response, normalize it through the companion, and record only a
   redacted summary such as `CHECKED received`.
7. Exercise the assigned failure paths in separate safe sessions. Do not send
   unintended content. Use manual/clipboard fallback when the driver is
   unavailable or capture/normalization fails.
8. Close test tabs, clear the temporary browser profile if one was used, and
   verify no test artifact contains account data or secrets.
9. Return one completed report per vendor using the exact report template.

## Failure-path procedure

Run each failure path independently and record the observed bounded result:

- expired login: use an already expired/non-authenticated test state; do not
  force logout or reveal session data;
- selector mismatch: use a controlled page state or record that the live page
  did not expose the expected composer/button; do not alter vendor pages;
- cancelled send: decline the confirmation or cancel before sending;
- timeout: stop waiting at the agreed local timeout and record no unintended
  send;
- capture failure: use the manual/clipboard fallback and record whether the
  redacted result was imported;
- normalization failure: record bounded fallback/error behavior without copying
  the raw response;
- clipboard/manual fallback: verify the operator can complete the handoff by
  manual paste/import without exposing sensitive data.

## Screenshot, trace, and cleanup rules

- Capture only the minimum UI needed to prove the route and result.
- Redact account name, email, avatar, conversation titles, private content,
  URLs containing identifiers, tokens, cookies, headers, and unrelated tabs.
- Do not capture browser storage, developer-tools network bodies, request
  headers, cookies, authorization values, or full page dumps.
- Name files with vendor, scenario, and UTC date only, for example
  `chatgpt-live-success-20260903.png`.
- Store sanitized evidence only under
  `artifacts/verification/g29-external-20260903/`.
- Before sharing, search the report/evidence for `password`, `cookie`,
  `token`, `authorization`, `bearer`, `api_key`, email addresses, and raw
  account identifiers. Remove the item and report the redaction.
- Do not retain the browser profile, certificates, downloads, or temporary
  session exports after the run.

## G29 evidence boundary

`LIVE` means a real vendor page was used by the authorized operator. A local
synthetic page or controlled fixture must be labeled `CONTROLLED_FIXTURE` and
cannot be substituted for live vendor evidence. `EXIT_CODE: N/A` is required
for manual observations without a local process exit code.

The repository currently has no standalone `docs/tasks/WP-20.md` or
`docs/tasks/WP-21.md`. The available bounded WP-21 predecessor record is
`docs/tasks/G21-WP21-REAL-BROWSER-JOURNEY-AND-FAILURE-PATH.md`; this missing
record condition remains a documentation limitation and must not be silently
filled with invented acceptance claims.
