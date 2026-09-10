# TA-F1 — Formal Contract / ADR Exact Sync Proposal

| Field | Value |
|---|---|
| GOAL_ID | TA-F1 |
| NAME | Formal Contract / ADR Exact Sync Proposal |
| GOAL_TYPE | GOVERNANCE / FORMALIZATION |
| STATUS | REVIEW_READY |
| AUTHORIZATION | Human prompt dated 2026-09-10, activated by remote-verified TA-LR-01 receipt |
| FORMALIZATION_BASE | `f34e6b29ae9e7326d1d44b9b03756b450809928f` |
| ACCEPTED_PREDECESSOR | TA-LR-01 receipt `fe2eb2318dc6558afe1aa6c5361756b082c90c74` |
| BRANCH | `codex/track-a-formalization` |
| OBJECTIVE | Prepare exact M-IDENTITY/M-HUMAN formal wording and bounded F3 allowlist; do not apply formal changes |
| PRODUCT_IMPLEMENTATION | HOLD |
| FORMAL_DOC_SYNC | PROPOSAL_ONLY |
| F3 | NOT_AUTHORIZED |
| S0 | NOT_AUTHORIZED |
| S0_PREDECESSOR | UNASSIGNED |
| TRACK_A_PRODUCT_LINEAGE_BASE | `f34e6b29ae9e7326d1d44b9b03756b450809928f` |
| TRACK_A_IMPLEMENTATION_BRANCH | NOT_YET_CREATED |
| REVIEW_LEVEL | L2_HIGH_RISK_GOAL |
| PUSH | NOT_AUTHORIZED / DO_NOT_PUSH_F1_CANDIDATE |

## Exact scope

Allowed Candidate paths:

- `docs/reviews/POLYNEXUS_FORMAL_CONTRACT_ADR_SYNC_PROPOSAL.md`
- `docs/goals/TA-F1.md`
- `docs/reviews/TA-F1/REVIEW_PACKET.md`
- `docs/reviews/TA-F1/VALIDATION_RESULTS.md`
- `docs/reviews/TA-F1/ENVIRONMENT_FINGERPRINT.md`
- `docs/reviews/TA-F1/evidence/source-inventory.json`
- `docs/reviews/TA-F1/evidence/validation-report.json`
- `docs/handoffs/TA-F1/review-ready.md`

Formal target documents and all product paths are read-only. Review-package and delivery artifacts live outside the repository and are not Candidate files.

## Acceptance criteria

- Proposal contains all 25 required sections and an exact per-file F3 allowlist.
- I-01..I-23, M-IDENTITY, M-HUMAN, M-EXECUTION, D11-C, P0/N1, REST/WebSocket, and fixed workflow vocabulary are explicitly covered.
- Formal target documents and product subtrees match f34 exactly.
- TA-LR HD-L1/L2/L3 and preservation rules are represented without provider-certification claims.
- Mandatory validations have no `SKIPPED`, `UNKNOWN`, or `NOT_EXECUTED` result.
- A local immutable Candidate commit and validated L2 package are produced, then writing stops.

## Architecture impact

`ADR_IMPACT: PROPOSAL_ONLY`. F1 proposes one future aggregate identity/outcome ADR and one future D11-A-LP amendment. No accepted ADR or public contract is modified. `M-EXECUTION: NOT REQUIRED / IMPLEMENTATION MAPPING ONLY`.

## Stop condition

Stop at `REVIEW_READY`. Independent review and Human F2 approval are required before any F3 activity. `NEXT_GOAL` is informational and conveys no delegation or authorization.
