# TA-LR-01 Legacy Reconciliation Decision Packet

Status: REVIEW_CANDIDATE / HUMAN_DISPOSITION_PENDING
Result type: GOVERNANCE_REPOSITORY_RECONCILIATION
Product implementation: HOLD

## CURRENT_REPOSITORY_STATE

- TA-LR-01 isolated branch: `codex/ta-lr-01`, predecessor `a9c6b4d4486fa522912c3fe6c65de70faa1e8132`, clean before Goal writes.
- Primary checkout: `D:/AI_學習教材/PolyNexus`, HEAD `b87a0dc780e5d9a3bba083dbaf9552ca52508f9a`, 21 tracked modifications, 2,036 untracked paths, staged count 0.
- Primary bytes were not reset, cleaned, pruned, merged, staged, or copied into the candidate.

## REMOTE / BRANCH TOPOLOGY

- GitHub remote: `https://github.com/lichen200224-bot/PolyNexus.git`.
- Remote heads observed: governance receipt `a9c6b4d4486fa522912c3fe6c65de70faa1e8132`, operating-model receipt `21f542d61bb6aa0bad3b2a96a74478bb8a3d1224`, frozen/read `f34e6b29ae9e7326d1d44b9b03756b450809928f`.
- Backup refs were fetched read-only under `legacy/*`; the source bare repository was not changed.
- Governance history begins at imported root `902c2719e5f6017f7f019284721f59b126f1375d` and has no merge base with `f34e6b29ae9e7326d1d44b9b03756b450809928f`. It is not a product implementation lineage.

## RELEVANT_LEGACY_BRANCHES

- Product lineage: `legacy/feature/first-vertical-slice` at `730912b5a3e19449c355975485f1fe77350a458a`; GitHub `feature/g24-g30-development-completion-routing` at `f34e6b29ae9e7326d1d44b9b03756b450809928f`; `730912b5a3e19449c355975485f1fe77350a458a` is its ancestor by 26 commits.
- Reconciliation-only refs: goal-governance `5d1bd607...`, goal-objective `2552c454...`, phase-a `8750e7e...`.
- Runtime comparison refs: `runtime-adapters-integration`, `runtime-registry-conformance`, `wp14-*`, `wp15-*`, `wp16-*`; none is auto-merged.

## DIRTY / UNTRACKED INVENTORY

- Tracked: 21 modified paths (9 docs, 8 skill/rule files, 2 runtime files, AGENTS.md, README.md).
- Untracked: 2,036. Of these, 1,953 are under `review_work/*`; only grouped path counts were captured, with no profile/dependency content copied or hashed.
- Relevant non-`review_work` source/docs/scripts are recorded with sizes and SHA-256 in `evidence/dirty-inventory.json`.
- Unknown or Human-owned material remains preserved.

## PREVIOUS_OPEN_WORK_MATRIX

`legacy-items.json` contains 51 uniquely identified items. Inventory count equals classified count; every item has exactly one primary destination.

## LEGACY_CLASSIFICATION_MATRIX

| Classification | Count |
|---|---:|
| ALREADY_COVERED | 7 |
| CARRY_FORWARD | 13 |
| REQUIRES_MIGRATION | 1 |
| REQUIRES_REVALIDATION | 27 |
| SUPERSEDED | 3 |

No item was marked OBSOLETE because current evidence did not justify deletion or loss of history.

## FORMALIZATION_OVERLAYS

F1-F4 must compare dirty formal/navigation documents and legacy governance branches by exact hash. It must not whole-file overwrite `Decision Log`, Scope, PRD, SA, SD, ADR, Project State, Roadmap, or Handoff. Formal wording still follows the accepted Freeze Record and formal contract/ADR change plan.

## IMPLEMENTATION_OVERLAYS

Future S0-W6 intake must compare, not absorb, the dirty tracked runtime contracts/registry, untracked runtime/codex adapter/tests, legacy runtime integration branches, Web assets, and previous workflow/evidence outputs. No product source was changed by TA-LR-01.

## HISTORICAL_EVIDENCE_BOUNDARIES

Prior Gxx/WPxx PASS and provisional acceptance remain historical bounded facts. They are references only and cannot certify the new Track A Candidate, real providers, B01, current browser journeys, production migration, or Working Product maturity.

## UNRESOLVED_FINDINGS

- G08/G09 source or obsolete disposition remains Human-owned.
- Dirty/untracked ownership and adoption remain Human-owned; preservation is complete, disposition is not.
- G30 provider certification remains `HISTORICAL_NEED_ACTION` until fresh physical evidence exists.
- No destructive action or architecture/public-contract change is required by this packet.

## RECOMMENDED_SAFE_PREDECESSOR_SHA

`730912b5a3e19449c355975485f1fe77350a458a` — the last product-lineage provisional RC checkpoint before the 26-commit G19-G30 sequence. It is not the dirty `b87a0dc780e5d9a3bba083dbaf9552ca52508f9a` checkout, not the governance `a9c6b4d4486fa522912c3fe6c65de70faa1e8132` lineage, and not a claim that `f34e6b29ae9e7326d1d44b9b03756b450809928f` is executable.

## RECOMMENDED_IMPLEMENTATION_BRANCH/LANE

Proposed, not approved: create `codex/track-a-implementation` from exact `730912b5a3e19449c355975485f1fe77350a458a` only after TA-LR-01 Human disposition and F1-F4 acceptance. Use an isolated worktree; preserve the primary dirty checkout. Do not create, merge, or push this lane under TA-LR-01.

## CROSS_MACHINE_REPRODUCIBILITY

PASS for exact predecessor object retrieval: a fresh clone of `https://github.com/lichen200224-bot/PolyNexus.git` branch `feature/g24-g30-development-completion-routing` successfully detached-checkout `730912b5a3e19449c355975485f1fe77350a458a` and returned exact HEAD. The remote branch is a carrier, not the future implementation lane and remains frozen/read-only.

## HD-L1 RECOMMENDATION

`ACCEPT_RECOMMENDATION`: keep G30 as `HISTORICAL_NEED_ACTION`; route to `NEXT / separate external release verification`; do not block Track A B01 and do not claim provider certification.

## HD-L2 RECOMMENDATION

`ACCEPT_RECOMMENDATION_WITH_PRESERVATION`: accept the 51-item classification ledger and preservation controls. Never bulk merge/delete/reset/clean/prune/absorb. Human later decides only G08/G09 source and the ownership/adoption of preserved dirty/untracked groups.

## HD-L3 RECOMMENDATION

`ACCEPT_RECOMMENDATION`: exact predecessor `730912b5a3e19449c355975485f1fe77350a458a`; remote carrier `feature/g24-g30-development-completion-routing`; proposed future lane `codex/track-a-implementation`. Keep `f34e6b29ae9e7326d1d44b9b03756b450809928f` frozen/design-read and `a9c6b4d4486fa522912c3fe6c65de70faa1e8132` governance-only.

## REMAINING_HUMAN_DECISIONS

Independent review must first PASS. Human then accepts/rejects HD-L1/L2/L3, determines G08/G09 disposition, and authorizes any future lane creation. These decisions are not implied by this Writer packet.

## NEXT_STAGE

`F1` only after independent PASS, Human acceptance/HD disposition, receipt closure, and separate F1 authorization. Product implementation remains HOLD.
