---
name: polynexus-independent-acceptance
description: Independently review a PolyNexus Goal exact review candidate and fresh evidence, producing PASS, NEED_FIX or HOLD and a push recommendation.
---
# polynexus-independent-acceptance

Read Framework §§4–5 and review template. Confirm you are the Human-designated independent reviewer, not the Writer. Start with exact SHA/diff/AC/evidence, then expand only affected contracts. Verify actual exits, negative cases, freshness, immutable target, trusted oracle, invariants and scope. Mandatory SKIPPED/UNKNOWN/stale/mismatched evidence blocks PASS; optional skips keep their explicit limitations. Mock/simulator is not real-executor evidence. Report actionable file/line/evidence/FIX_PROMPT, fixed verdict and APPROVE_TO_PUSH or DO_NOT_PUSH. Never self-authorize Human acceptance or push. NEED_FIX inside original authorization returns to bounded repair with a new SHA and fresh evidence; preserve prior packets.

Canonical [Framework](../../../docs/governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) · [Current Goal](../../../docs/IMPLEMENTATION_CURRENT_GOAL.md) · [Goal template](../../../docs/goals/_GOAL_TEMPLATE.md) · [Handoff template](../../../docs/handoffs/_HANDOFF_TEMPLATE.md) · [Review template](../../../docs/reviews/_REVIEW_PACKET_TEMPLATE.md)
