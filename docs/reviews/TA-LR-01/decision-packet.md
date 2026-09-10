# TA-LR-01 Legacy Reconciliation Decision Packet

Status: REVIEW_CANDIDATE / HUMAN_DISPOSITION_PENDING
Result type: GOVERNANCE_REPOSITORY_RECONCILIATION
Product implementation: HOLD

## CURRENT_REPOSITORY_STATE

- TA-LR-01 isolated branch: `codex/ta-lr-01`, predecessor `a9c6b4d4486fa522912c3fe6c65de70faa1e8132`, clean before Goal writes.
- Previous Review Candidate `d60da1537f4d93bab10bf325cd4f69f13dec075b` is preserved as `NEED_FIX`; this repair creates a new direct-child candidate and does not amend it.
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

`legacy-items.json` contains 56 uniquely identified items. Inventory count equals classified count; every item has exactly one primary destination. `LR-020` supersedes only old G19–G23 routing semantics; `LR-052`–`LR-056` separately preserve the Human-accepted G23/G25/G26/G27/G28 implementation provenance.

## LEGACY_CLASSIFICATION_MATRIX

| Classification | Count |
|---|---:|
| ALREADY_COVERED | 7 |
| CARRY_FORWARD | 13 |
| REQUIRES_MIGRATION | 1 |
| REQUIRES_REVALIDATION | 32 |
| SUPERSEDED | 3 |

No item was marked OBSOLETE because current evidence did not justify deletion or loss of history.

## FORMALIZATION_OVERLAYS

F1-F4 must compare dirty formal/navigation documents and legacy governance branches by exact hash. It must not whole-file overwrite `Decision Log`, Scope, PRD, SA, SD, ADR, Project State, Roadmap, or Handoff. Formal wording still follows the accepted Freeze Record and formal contract/ADR change plan.

## IMPLEMENTATION_OVERLAYS

Future S0-W6 intake must compare, not absorb, the dirty tracked runtime contracts/registry, untracked runtime/codex adapter/tests, legacy runtime integration branches, Web assets, and previous workflow/evidence outputs. No product source was changed by TA-LR-01.

## HISTORICAL_EVIDENCE_BOUNDARIES

Prior Gxx/WPxx PASS and provisional acceptance remain historical bounded facts. They are references only and cannot certify the new Track A Candidate, real providers, B01, current browser journeys, production migration, or Working Product maturity.

Superseding an old roadmap does not discard accepted bytes. G23 `0eb56a9…`, G25 `f4168c3…`, G26 `4fd73b5…`, G27 `27ff09c…`/`56c941a…`, and G28 `789717f…`/`2bbcb0c…` remain explicit lineage/provenance inputs. Each later Track A stage must reuse, revalidate, migrate, or replace them under its own acceptance criteria.

## UNRESOLVED_FINDINGS

- G08/G09 source or obsolete disposition remains Human-owned.
- Dirty/untracked ownership and adoption remain Human-owned; preservation is complete, disposition is not.
- G30 provider certification remains `HISTORICAL_NEED_ACTION` until fresh physical evidence exists.
- No destructive action or architecture/public-contract change is required by this packet.

## ACCEPTED_PREDECESSOR_COMPARISON

| SHA | Meaning / acceptance | Immediate product change | Preservation consequence |
|---|---|---|---|
| `730912b5…` | CP06 provisional RC, Human accepted with WP21 limitation | docs-only commit | Too early; omits all later accepted G25–G28 product work |
| `0eb56a9…` | G23 Human accepted / PASS / COMPLETE | docs-only commit | Omits accepted G25–G28 product work |
| `f4168c3…` | G25 Human accepted runtime/Doctor output | runtime source + tests | Omits accepted G26–G28 product work |
| `4fd73b5…` | G26 Human accepted local-policy/WebSurface output | Core + extension source/tests | Omits accepted G27–G28 product work |
| `27ff09c…` | G27 accepted workflow/metrics product output | Core source + tests | Omits accepted G28 product work |
| `56c941a…` | G27 accepted docs/evidence checkpoint | docs/evidence only | Omits accepted G28 product work |
| `789717fb…` | G28 Human accepted product output | frontend source + production tests | Preserves all accepted product bytes; lacks later provenance docs |
| `2bbcb0c…` | G28 docs/state-sync checkpoint | docs-only | Preserves accepted product; lacks final GitHub closure docs |
| `f34e6b29…` | G30 GitHub continuation tip / frozen DESIGN-READ | docs-only | Preserves all accepted product and later provenance; requires Human promotion |

Exact changed paths, limitations, remote carrier refs, clean-clone object presence, ancestry distance, and loss analysis are in `evidence/predecessor-comparison-r2.json`.

## RECOMMENDED_SAFE_PREDECESSOR_SHA

LATEST_HUMAN_ACCEPTED_PRODUCT_OUTPUT_SHA: `789717fbf4a6b4a36aa71ec1cf7d36f344eccdf7`.

RECOMMENDED_SAFE_IMPLEMENTATION_PREDECESSOR_SHA: `f34e6b29ae9e7326d1d44b9b03756b450809928f`.

They differ because `789717fb…` is the last commit that changed product bytes, while `f34e6b29…` adds three docs-only commits containing G28 state-sync and GitHub/cross-machine provenance. Exact `apps/`, `services/`, `schemas/`, `workflows/`, and `extensions/` subtree hashes match between the two SHAs. Starting at `f34…` therefore preserves the accepted G28 product tree and all later provenance. This is a technical recommendation only: Human must explicitly promote `f34…` from DESIGN/READ to future implementation predecessor.

The nine-checkpoint comparison is machine-readable in `evidence/predecessor-comparison-r2.json`. Starting at `730912b5…` would omit accepted G25/G26/G27/G28 product changes and is no longer recommended.

## RECOMMENDED_IMPLEMENTATION_BRANCH/LANE

Proposed, not approved: create `codex/track-a-implementation` from exact `f34e6b29ae9e7326d1d44b9b03756b450809928f` only after TA-LR-01 Human disposition, explicit promotion from DESIGN/READ, and F1-F4 acceptance. Use an isolated worktree; preserve the primary dirty checkout. Do not create, merge, or push this lane under TA-LR-01.

## CROSS_MACHINE_REPRODUCIBILITY

PASS: `https://github.com/lichen200224-bot/PolyNexus.git` branch `feature/g24-g30-development-completion-routing` resolves to exact `f34e6b29ae9e7326d1d44b9b03756b450809928f`; a fresh clone contains every compared checkpoint and cleanly reproduces the accepted product lineage. The remote branch is a carrier, not an approved implementation lane.

## PRODUCT_TREE_PRESERVATION

PASS. Exact name-status diff from `789717fb…` to `f34e6b29…` contains only documentation paths; the five product subtree object IDs match exactly. No product source, production test, schema, workflow, extension, or runtime implementation changed after G28 product output.

## FORMAL_DOC_RECONCILIATION_REQUIRED

YES. The three post-product commits contain accepted state-sync/cross-machine documentation. F1-F4 must reconcile formal meaning without treating historical implementation PASS as fresh Track A verification.

## FRESH_REVALIDATION_REQUIRED_BY_STAGE

| Stage | Required fresh boundary |
|---|---|
| S0 | startup/health/CREATED/cancel-timeout and affected foundation regressions |
| W1 | repository/workspace identity, bindings, dirty snapshot and ownership |
| W2 | real executor, adapters, policy, redaction, local endpoint and process lifecycle |
| W3 | Core-derived ChangeSet/Candidate/artifact identities and capture |
| W4 | deterministic verification, evidence, workflow guards and metrics |
| W5 | trusted Human decision, exact view/history/revoke/supersede and secrets |
| W6 | Working Product UX, accepted-result opening, portable package and recovery |

## HD-L1 RECOMMENDATION

`ACCEPT_RECOMMENDATION`: keep G30 as `HISTORICAL_NEED_ACTION`; route to `NEXT / separate external release verification`; do not block Track A B01 and do not claim provider certification.

## HD-L2 RECOMMENDATION

`ACCEPT_RECOMMENDATION_WITH_PRESERVATION`: accept the 56-item classification ledger and preservation controls. Old routing may be superseded while accepted G23/G25/G26/G27/G28 outputs remain explicit provenance and stage inputs. Never bulk merge/delete/reset/clean/prune/absorb. Human later decides only G08/G09 source and the ownership/adoption of preserved dirty/untracked groups.

## HD-L3 RECOMMENDATION

`ACCEPT_RECOMMENDATION`: latest accepted product output `789717fbf4a6b4a36aa71ec1cf7d36f344eccdf7`; exact recommended predecessor `f34e6b29ae9e7326d1d44b9b03756b450809928f`; remote carrier `feature/g24-g30-development-completion-routing`; proposed future lane `codex/track-a-implementation`. Human promotion of `f34…` from DESIGN/READ is mandatory; `a9c6b4d…` remains governance-only.

## REMAINING_HUMAN_DECISIONS

Independent review must first PASS. Human then accepts/rejects HD-L1/L2/L3, determines G08/G09 disposition, and authorizes any future lane creation. These decisions are not implied by this Writer packet.

## NEXT_STAGE

`F1` only after independent PASS, Human acceptance/HD disposition, receipt closure, and separate F1 authorization. Product implementation remains HOLD.
