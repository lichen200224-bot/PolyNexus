# TA-F1 Human Decision

```yaml
GOAL_ID: TA-F1
DECISION_DATE: 2026-09-11
DECISION_SOURCE: Current explicit Human instructions in the controlling Codex task
REVIEWED_PRODUCT_SHA: 892fb43472bac561d42cfe3a9ee2511fe0e91586
INDEPENDENT_REVIEW: PASS
HUMAN_ACCEPTANCE: APPROVED
F1_PUSH: AUTHORIZED_BY_LATER_EXPLICIT_HUMAN_OVERRIDE
PUSH_AUTHORIZATION: EXACT_REVIEWED_SHA_ONLY
APPROVED_REMOTE: https://github.com/lichen200224-bot/PolyNexus.git
APPROVED_BRANCH: codex/track-a-formalization
ONE_BOUNDED_ACCEPTANCE_RECEIPT_CLOSURE: AUTHORIZED
RECEIPT_SCOPE: METADATA_ONLY
RECEIPT_PUSH: AUTHORIZED
RECEIPT_PARENT_RULE: DIRECT_SINGLE_PARENT_C
RECEIPT_EXACT_ALLOWLIST:
  - docs/reviews/TA-F1/acceptance-receipt.json
  - docs/reviews/TA-F1/independent-review.md
  - docs/reviews/TA-F1/human-decision.md
  - docs/reviews/TA-F1/remote-c-proof.json
  - docs/handoffs/TA-F1/accepted.md
F2_DECISION: APPROVE_EXACT_WORDING_AND_EIGHT_FILE_F3_ALLOWLIST
F3_AUTHORIZATION: AUTHORIZED_AS_NEW_BOUNDED_GOAL
PRODUCT_IMPLEMENTATION: HOLD
S0: NOT_AUTHORIZED
S0_PREDECESSOR: UNASSIGNED
```

The Human first recorded `F1_PUSH: DO_NOT_PUSH`, then explicitly stated `我同意PUSH`. The later instruction controls and authorizes only the exact reviewed Candidate and the bounded metadata Receipt closure; it does not authorize force push, another Candidate, broader metadata, F3 Candidate push, product implementation, or S0.

F3 may start only after this Receipt passes deterministic integrity, is pushed without force, and the remote branch independently resolves to the exact Receipt SHA. Its Candidate is limited to the eight paths approved in the accepted TA-F1 proposal.
