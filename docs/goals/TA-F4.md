# TA-F4 — Formal Synchronization Verification

```yaml
GOAL_ID: TA-F4
GOAL_TYPE: GOVERNANCE_FORMALIZATION_VERIFICATION
AUTHORIZATION_ID: TA-F4-HUMAN-AUTH-20260911-01
AUTHORIZATION_DECISION: AUTHORIZED_TO_EXECUTE_TA-F4
AUTHORIZED_PREDECESSOR: 284929a8f5a39df5524ccba7d733aa9161fc91e9
PREVIOUS_CANDIDATE: a0bb7458bab95836c6af066b8d2d12a61917c195
PREVIOUS_CANDIDATE_DISPOSITION: ABANDONED_FOR_PROMOTION
PREDECESSOR_SHA: 284929a8f5a39df5524ccba7d733aa9161fc91e9
REVIEWED_F3_SHA: c4c17924ad568e5ae279fa3632a9960421ba80cb
BRANCH: codex/track-a-f4-remediation
FORMAL_DOC_CHANGES: NOT_AUTHORIZED
PRODUCT_IMPLEMENTATION: HOLD
S0: NOT_AUTHORIZED
S0_PREDECESSOR: UNASSIGNED
REVIEW_LEVEL: L2
PUSH_STATUS: NOT_AUTHORIZED
```

## Objective

Verify the accepted F3 formal synchronization against cross-references, frozen I-01 through
I-23, D11-C fallback, legacy/migration preservation, and P0/N1 delivery phasing. Preserve the
exact before/after formal delta and prepare an independently reviewable local Candidate.

## Exact output allowlist

1. `docs/goals/TA-F4.md`
2. `docs/handoffs/TA-F4/review-ready.md`
3. `docs/reviews/TA-F4/FORMAL_SYNC_VERIFICATION_REPORT.md`
4. `docs/reviews/TA-F4/ENVIRONMENT_FINGERPRINT.md`
5. `docs/reviews/TA-F4/REVIEW_PACKET.md`
6. `docs/reviews/TA-F4/VALIDATION_RESULTS.md`
7. `docs/reviews/TA-F4/evidence/cross-reference-report.json`
8. `docs/reviews/TA-F4/evidence/formal-delta-report.json`

## Acceptance criteria

- Every repository-local formal cross-reference resolves.
- I-01 through I-23 each have an explicit preserved mapping with no conflict.
- D11-C fail-closed fallback and D11-A-LP coexist without ambiguity.
- Legacy and dirty overlays are classified without bulk adoption, deletion, or rewrite.
- Migration remains future separately authorized implementation work; no migration runs.
- P0 remains required and N1 remains non-blocking for B01.
- Exact F3 before/after delta is preserved and independently reconstructable.
- The eight accepted F3 formal files, ADR-011, and all product roots remain unchanged.
- Mandatory checks have no skipped, unknown, or unexecuted entry.

## Stop boundary

Create a local L2 Review Candidate and external review package, then stop at
`READY_FOR_L2_REACCEPTANCE`. Do not push TA-F4, authorize F5 or S0, assign an S0
predecessor, create a Product Implementation branch, or modify product/formal contracts.
