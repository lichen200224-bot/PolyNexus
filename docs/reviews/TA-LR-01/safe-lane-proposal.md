# TA-LR-01 Safe Lane Proposal

- STATUS: PROPOSED_NOT_APPROVED
- LATEST_HUMAN_ACCEPTED_PRODUCT_OUTPUT_SHA: `789717fbf4a6b4a36aa71ec1cf7d36f344eccdf7`
- RECOMMENDED_SAFE_IMPLEMENTATION_PREDECESSOR_SHA: `f34e6b29ae9e7326d1d44b9b03756b450809928f`
- REMOTE_CARRIER_BRANCH: `feature/g24-g30-development-completion-routing`
- FROZEN_DESIGN_READ_SHA: `f34e6b29ae9e7326d1d44b9b03756b450809928f`
- HUMAN_PROMOTION_REQUIRED: YES
- PRODUCT_TREE_PRESERVATION: PASS
- FORMAL_DOC_RECONCILIATION_REQUIRED: YES
- REJECTED_DIRTY_PREDECESSOR: `b87a0dc780e5d9a3bba083dbaf9552ca52508f9a`
- GOVERNANCE_ONLY_PREDECESSOR: `a9c6b4d4486fa522912c3fe6c65de70faa1e8132`
- PROPOSED_FUTURE_LANE: `codex/track-a-implementation`

## Evidence

`789717fbf4a6b4a36aa71ec1cf7d36f344eccdf7` is the latest Human-accepted product-changing output. The following three commits through `f34e6b29ae9e7326d1d44b9b03756b450809928f` change only documentation. Exact subtree objects for `apps`, `services`, `schemas`, `workflows`, and `extensions` are identical at both SHAs, so `f34…` preserves the entire accepted product tree plus G28 state-sync and GitHub/cross-machine provenance.

Starting from `730912b5a3e19449c355975485f1fe77350a458a` would omit accepted G25 runtime/Doctor, G26 local-policy/WebSurface, G27 workflow/metrics, and G28 UX bytes. It is rejected as the future predecessor. The exact nine-checkpoint comparison and name-status/tree evidence are in `evidence/predecessor-comparison-r2.json`.

The governance R lineage has no merge base with the product lineage because it begins from an imported review snapshot; it is not an implementation base. The dirty `b87…` checkout is also rejected.

## Required future operation

Human must first explicitly promote exact `f34e6b29…` from DESIGN/READ reference to future implementation predecessor. After TA-LR-01 acceptance and F1-F4, a separately authorized operation may create the proposed isolated branch/worktree at that exact SHA. It must refresh the remote object, protect the dirty primary checkout, and must not merge the governance history by implication.

Existing Human-accepted bytes are preserved, but no new Track A stage is considered freshly verified. S0 and W1–W6 must each revalidate the boundaries mapped in the decision packet and comparison evidence.

## Rollback / preservation

TA-LR-01 creates no product lane, performs no merge/rebase/reset/clean/prune, and pushes no TA-LR-01 candidate. The proposal can be rejected without product-tree rollback.
