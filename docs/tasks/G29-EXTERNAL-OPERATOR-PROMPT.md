# G29 External Operator Communication Prompt

> Routing update (2026-09-03): this prompt is handed forward from G29 to the
> future G30 external-verification gate. Do not execute it as part of G29.

Copy the block below to the authorized Human operator. Add only the approved
safe payload and artifact destination; never add or request credentials.

```text
You are an authorized external compatibility tester for PolyNexus WP-20. Use
only the designated non-production test account and the approved non-sensitive
test payload. Do not reveal, copy, export, screenshot, or report any password,
cookie, token, recovery code, private conversation, account identifier, or
unrelated page data.

For each assigned vendor, record browser/extension versions and observed UTC
time. Execute only: launch → detect → fill → pause for the account owner to
inspect → send only after the owner explicitly confirms the exact payload and
target → capture → normalize → cleanup. Then test the assigned failure paths
without sending unintended content and verify clipboard/manual fallback.

Redact screenshots and traces before sharing. Do not modify PolyNexus source,
do not claim certification, and do not send credentials or session data to
Codex. If the account, consent, or safe route is unavailable, stop and report
the blocker. Never bypass account controls or send automatically.

Return exactly the fields in G29-EXTERNAL-REPORT-TEMPLATE.md. For a manual
observation with no local process exit code, use EXIT_CODE: N/A; never invent
0 or 1. Store only sanitized artifacts at:
artifacts/verification/g29-external-20260903/
```
