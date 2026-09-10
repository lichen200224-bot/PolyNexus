---
name: polynexus-independent-acceptance
description: Independently review a PolyNexus Goal exact review candidate and fresh evidence, producing PASS, NEED_FIX or HOLD and a push recommendation.
---
# polynexus-independent-acceptance

Read Framework §§4–5 and review template. Confirm you are the Human-designated independent reviewer, not the Writer. Start with exact SHA/diff/AC/evidence, then expand only affected contracts. Verify actual exits, negative cases, freshness, immutable target, trusted oracle, invariants and scope. Mandatory SKIPPED/UNKNOWN/stale/mismatched evidence blocks PASS; optional skips keep their explicit limitations. Mock/simulator is not real-executor evidence. Report actionable file/line/evidence/FIX_PROMPT, fixed verdict and APPROVE_TO_PUSH or DO_NOT_PUSH. Never self-authorize Human acceptance or push. NEED_FIX inside original authorization returns to bounded repair with a new SHA and fresh evidence; preserve prior packets.

Canonical [Framework](../../../docs/governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) · [Current Goal](../../../docs/IMPLEMENTATION_CURRENT_GOAL.md) · [Goal template](../../../docs/goals/_GOAL_TEMPLATE.md) · [Handoff template](../../../docs/handoffs/_HANDOFF_TEMPLATE.md) · [Review template](../../../docs/reviews/_REVIEW_PACKET_TEMPLATE.md)

For FINDING-01 follow Framework §5 exactly: REVIEWED_PRODUCT_SHA=C; metadata ACCEPTANCE_RECEIPT_SHA=R, single parent C. Human may approve C and ONE_BOUNDED_ACCEPTANCE_RECEIPT_CLOSURE once. Verify remote C, strict preapproved receipt allowlist, unchanged reviewed scope, resolvable references/hashes and RI-01..RI-10 before R push. No second full product review for compliant R; out-of-scope or failed integrity HOLD. Remote R match closes cross-machine readiness; receiver fetches R first and resolves C. SELF_RECEIPT avoids a self-hash cycle; WIP never creates R.

For FINDING-02 next proposed Goal is TA-LR-01 (governance-only, not authorized/executed), then F1. Its authorized Owner Codex completes inventory/classification/HD-L1-L3 packet without per-item Human interruptions. Do not perform LR inventory or lane changes under R2 repair authorization.

Enter Independent Review only after the Writer has stopped at REVIEW_READY with a validated mandatory ZIP (Framework §4). FIRST READ START_HERE.md from the complete Review ZIP; then verify external hash, manifest, exact C/P, diff, bytes and evidence before any verdict. Do not assume access to the development machine. All packaging details are canonical in [polynexus-review-package](../polynexus-review-package/SKILL.md); do not copy another packaging schema here.
