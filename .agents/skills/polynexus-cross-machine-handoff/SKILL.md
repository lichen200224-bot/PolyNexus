---
name: polynexus-cross-machine-handoff
description: Prepare or validate PolyNexus exact-SHA accepted or WIP handoffs, writer transfer and integration dependencies.
---
# polynexus-cross-machine-handoff

Read Framework §§2,5–7 and handoff template. Verify accepted/WIP identity and actual remote SHA; push exit 0 is insufficient. Receiving intake must fetch exact predecessor, verify safe lane/HEAD/dirty/index/dependencies and obtain exclusive ownership before writing. WIP requires explicit Human push/transfer authority and NOT_ACCEPTED/NOT_REVIEWED/DO_NOT_MERGE labels. Unknown writer/process state is not release. Parallel Goals need independent branches/scopes and dependency classification; combined outcomes require an Integration Goal with accepted A/B inputs and reviewed C. Never infer delegation from NEXT_PROMPT.

Canonical [Framework](../../../docs/governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) · [Current Goal](../../../docs/IMPLEMENTATION_CURRENT_GOAL.md) · [Goal template](../../../docs/goals/_GOAL_TEMPLATE.md) · [Handoff template](../../../docs/handoffs/_HANDOFF_TEMPLATE.md) · [Review template](../../../docs/reviews/_REVIEW_PACKET_TEMPLATE.md)
