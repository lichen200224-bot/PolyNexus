# GOV-FLOWGOV-ADOPTION-01 — PolyNexus Portable Git Governance Transition

- Status: `HUMAN_AUTHORIZED / GOVERNANCE_PATCH`
- Start SHA: `86d5939044c1d7ec2a991820f39287481ee9120f`
- Branch: `governance/flowgov-adoption-poly`
- Product source change: `PROHIBITED`
- Active product lane: `BASELINE-DEBT-01` remains separate.

## Goals

1. Remove fixed repository path assumptions.
2. Make GitHub remote + exact SHA the cross-machine identity.
3. Treat remote-tracking refs as local cache; use `git ls-remote` for remote truth.
4. Establish SYNC / CANDIDATE / ACCEPTED checkpoint semantics.
5. Make Role > Tool and preserve Writer != Independent Reviewer.
6. Permit task-scoped non-force sync/candidate pushes when explicitly pre-authorized.
7. Add concise current routing index to avoid giant stale handoff files.
8. Record target `develop/main` model without changing current default branch yet.
9. Prepare PolyNexus to inherit a future standalone FlowGov governance repository.

## Explicit non-goals

- No product/runtime/schema/test behavior change.
- No BASELINE-DEBT-01 implementation change.
- No G30/WP-20/score change.
- No default-branch switch.
- No branch protection/ruleset change in this task.
- No merge/rebase/force push/history rewrite.

## Expected files

Governance/docs only, plus the existing workspace portability script and `.gitignore` local-profile exclusion.

## Next gate

Fresh independent governance review should inspect exact candidate SHA on this branch. Human decides acceptance/integration separately.
