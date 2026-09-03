# G26 Evidence Summary — 2026-09-03

`G26_RESULT=PASS` · `G26_STATUS=HUMAN_ACCEPTED / PASS / COMPLETE` ·
`PROJECT_SCORE=84/100` · delta `+12/12` ·
`HUMAN_DECISION=ACCEPT_AND_COMMIT_PUSH`.

The candidate branch is `codex/g26-local-policy-acceptance`, based on the exact
G25 state-sync/start SHA `04d37291d45ebbda8453f1b39e30fca523ee1548`. The
protected primary checkout was not modified.

WP-17 and WP-18 targeted G26 Core checks passed 14/14 with exit `0`; the
combined API/local routing regression passed 29/29 with exit `0`. The request-
time local egress gate and safe Evidence identity checks are Python-executed.
The full Core regression was rerun with an isolated basetemp and exited `1`
with failures in unrelated persistence/lifecycle/council/resource-guard tests;
these are explicitly outside the bounded G26 WP acceptance scope.

WP-19's controlled Node suite passed 10/10 with exit `0`; Web Vitest passed
80/80 and production build passed with exit `0`; extension syntax, manifest,
and Core caller-auth checks passed. Live authenticated vendor verification,
native MV3 dispatch, and no certification or external send remain claimed.

Independent read-only review of the bounded WP behavior returned `PASS` with
`BLOCKER=0`, `MAJOR=0`, and `MINOR=0` after provenance remediation. The product
checkpoint is `G26_PRODUCT_OUTPUT_SHA=4fd73b5ac3b59ae1f948f8d95ad795112552b1b2`.
The subsequent docs/evidence state-sync is
`G26_STATE_SYNC_SHA=07ebdb8a691997dc33fd6368507b707a6c0f4597`; its clean clone
is verified at the recorded path. The two SHAs are intentionally distinct per
the G25 product-output/state-sync provenance model. No remote reconfiguration,
secret handling, or G27 start is permitted.
