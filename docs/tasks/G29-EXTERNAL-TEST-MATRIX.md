# G29 External Test Matrix

> Routing update (2026-09-03): execute this matrix only when the future G30
> start gate authorizes the deferred external verification.

All rows require a sanitized report. `LIVE` rows require the authorized Human
operator. `CONTROLLED_FIXTURE` rows may be reproduced by Codex only to isolate
non-secret failures; they do not prove live vendor compatibility.

| ID | Vendor | Route | Scenario | Expected evidence | Send rule |
|---|---|---|---|---|---|
| CG-01 | ChatGPT | LIVE | launch → detect → fill → confirm → send → capture → normalize | Complete Level 3A report; normalized result is `AI_OPINION`; external request observation recorded | Account owner confirms exact payload before send |
| CL-01 | Claude | LIVE | launch → detect → fill → confirm → send → capture → normalize | Complete Level 3A report; normalized result is `AI_OPINION`; external request observation recorded | Account owner confirms exact payload before send |
| GM-01 | Gemini | LIVE | launch → detect → fill → confirm → send → capture → normalize | Complete Level 3A report; normalized result is `AI_OPINION`; external request observation recorded | Account owner confirms exact payload before send |
| CG-02 | ChatGPT | LIVE or controlled safe state | expired login | Bounded unavailable/degraded result; no secret or account data | No send |
| CL-02 | Claude | LIVE or controlled safe state | expired login | Bounded unavailable/degraded result; no secret or account data | No send |
| GM-02 | Gemini | LIVE or controlled safe state | expired login | Bounded unavailable/degraded result; no secret or account data | No send |
| CG-03 | ChatGPT | LIVE or controlled fixture | selector mismatch | Driver failure isolated; manual/clipboard fallback recorded | No send |
| CL-03 | Claude | LIVE or controlled fixture | selector mismatch | Driver failure isolated; manual/clipboard fallback recorded | No send |
| GM-03 | Gemini | LIVE or controlled fixture | selector mismatch | Driver failure isolated; manual/clipboard fallback recorded | No send |
| CG-04 | ChatGPT | LIVE or controlled fixture | cancelled send / no confirmation | `user_confirmation_required` or equivalent; no external send | Must not send |
| CL-04 | Claude | LIVE or controlled fixture | cancelled send / no confirmation | `user_confirmation_required` or equivalent; no external send | Must not send |
| GM-04 | Gemini | LIVE or controlled fixture | cancelled send / no confirmation | `user_confirmation_required` or equivalent; no external send | Must not send |
| CG-05 | ChatGPT | LIVE or controlled fixture | timeout | Bounded timeout/degraded result and cleanup; no unintended send | No send |
| CL-05 | Claude | LIVE or controlled fixture | timeout | Bounded timeout/degraded result and cleanup; no unintended send | No send |
| GM-05 | Gemini | LIVE or controlled fixture | timeout | Bounded timeout/degraded result and cleanup; no unintended send | No send |
| CG-06 | ChatGPT | LIVE or controlled fixture | capture failure | Manual/clipboard fallback; raw response not copied | No additional send |
| CL-06 | Claude | LIVE or controlled fixture | capture failure | Manual/clipboard fallback; raw response not copied | No additional send |
| GM-06 | Gemini | LIVE or controlled fixture | capture failure | Manual/clipboard fallback; raw response not copied | No additional send |
| CG-07 | ChatGPT | LIVE or controlled fixture | normalization failure | Bounded fallback/error; `AI_OPINION` not fabricated | No additional send |
| CL-07 | Claude | LIVE or controlled fixture | normalization failure | Bounded fallback/error; `AI_OPINION` not fabricated | No additional send |
| GM-07 | Gemini | LIVE or controlled fixture | normalization failure | Bounded fallback/error; `AI_OPINION` not fabricated | No additional send |
| CG-08 | ChatGPT | LIVE or controlled fixture | clipboard/manual fallback | Manual handoff completes and is sanitized | No send unless separately confirmed |
| CL-08 | Claude | LIVE or controlled fixture | clipboard/manual fallback | Manual handoff completes and is sanitized | No send unless separately confirmed |
| GM-08 | Gemini | LIVE or controlled fixture | clipboard/manual fallback | Manual handoff completes and is sanitized | No send unless separately confirmed |

## Matrix acceptance

WP-20 may be reported `PASS` only when every required vendor has a complete
sanitized live Level 3A report and fallback evidence, with no open security or
egress BLOCKER/MAJOR. Missing operator/account, missing mandatory row, absent
confirmation, unclear `LIVE`/`CONTROLLED_FIXTURE`, or secret leakage is
`NEED_ACTION`; it is not a PASS.
