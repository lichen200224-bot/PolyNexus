---
name: polynexus-cross-machine-handoff
description: Prepare or validate PolyNexus exact-SHA accepted or WIP handoffs, writer transfer and integration dependencies.
---
# polynexus-cross-machine-handoff

Read Framework §§2,5–7 and handoff template. Verify accepted/WIP identity and actual remote SHA; push exit 0 is insufficient. Receiving intake must fetch exact predecessor, verify safe lane/HEAD/dirty/index/dependencies and obtain exclusive ownership before writing. WIP requires explicit Human push/transfer authority and NOT_ACCEPTED/NOT_REVIEWED/DO_NOT_MERGE labels. Unknown writer/process state is not release. Parallel Goals need independent branches/scopes and dependency classification; combined outcomes require an Integration Goal with accepted A/B inputs and reviewed C. Never infer delegation from NEXT_PROMPT.

Canonical [Framework](../../../docs/governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) · [Current Goal](../../../docs/IMPLEMENTATION_CURRENT_GOAL.md) · [Goal template](../../../docs/goals/_GOAL_TEMPLATE.md) · [Handoff template](../../../docs/handoffs/_HANDOFF_TEMPLATE.md) · [Review template](../../../docs/reviews/_REVIEW_PACKET_TEMPLATE.md)

For FINDING-01 follow Framework §5 exactly: REVIEWED_PRODUCT_SHA=C; metadata ACCEPTANCE_RECEIPT_SHA=R, single parent C. Human may approve C and ONE_BOUNDED_ACCEPTANCE_RECEIPT_CLOSURE once. Verify remote C, strict preapproved receipt allowlist, unchanged reviewed scope, resolvable references/hashes and RI-01..RI-10 before R push. No second full product review for compliant R; out-of-scope or failed integrity HOLD. Remote R match closes cross-machine readiness; receiver fetches R first and resolves C. SELF_RECEIPT avoids a self-hash cycle; WIP never creates R.

For FINDING-02 next proposed Goal is TA-LR-01 (governance-only, not authorized/executed), then F1. Its authorized Owner Codex completes inventory/classification/HD-L1-L3 packet without per-item Human interruptions. Do not perform LR inventory or lane changes under R2 repair authorization.

Accepted cross-machine handoff requires independently reviewed + Human accepted + remote verified C/R checkpoint. Review ZIP is mandatory before independent review and cannot substitute for that acceptance chain. All packaging details are canonical in [polynexus-review-package](../polynexus-review-package/SKILL.md); do not copy another packaging schema here.
