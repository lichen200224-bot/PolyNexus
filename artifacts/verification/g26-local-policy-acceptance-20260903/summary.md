# G26 Evidence Summary — 2026-09-03

`G26_RESULT=NEED_ACTION` · `G26_STATUS=HUMAN_ACCEPTED / CHECKPOINT_PENDING_NEED_ACTION`
· `PROJECT_SCORE=72/100` · delta `0/12` · `HUMAN_DECISION=ACCEPT_AND_COMMIT_PUSH`.

The candidate branch is `codex/g26-local-policy-acceptance`, based on the exact
G25 state-sync/start SHA `04d37291d45ebbda8453f1b39e30fca523ee1548`. The
protected primary checkout was not modified.

WP-17 and WP-18 targeted G26 Core checks passed 14/14 with exit `0`; the
combined API/local routing regression passed 29/29 with exit `0`. The full Core
regression was rerun with an isolated basetemp and exited `1` with existing
persistence/lifecycle/council/resource-guard failures, so the 12 G26 points
remain unawarded. The request-time local egress gate and safe Evidence identity
checks are Python-executed.

WP-19's controlled Node suite passed 10/10 with exit `0`; Web Vitest passed
80/80 and production build passed with exit `0`; extension syntax, manifest,
and Core caller-auth checks passed. Live authenticated vendor verification,
native MV3 dispatch, and no certification or external send remain claimed.

Independent read-only review returned `PASS` with `BLOCKER=0`, `MAJOR=0`, and
`MINOR=0`. Human authorized the exact checkpoint commit/push; no remote
reconfiguration, secret handling, or G27 start is permitted. Clean-clone
verification remains part of this checkpoint gate.
