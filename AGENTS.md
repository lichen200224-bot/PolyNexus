# PolyNexus — Current Agent Entry

## Current assignment

Read `docs/delivery/START_HERE.md` and `docs/delivery/SOURCE_LOCK.json` first. This branch is `planning/full-delivery-design-consolidation`, task `PREP-FULL-DELIVERY-01`.

The Human has explicitly authorized ChatGPT to prepare and publish the documentation and organize Git/GitHub for the full original product plus the accepted expansion. This authorizes documentation-only non-force checkpoints on this branch and a draft review PR. It does not authorize product implementation, acceptance of existing code candidates, live provider actions, production database operations, release, historical branch deletion, default-branch changes, or force/history rewrite. Formal product implementation belongs to Codex after the start gate in `docs/delivery/EXECUTION_CONTRACT.md` is satisfied.

## Authority and loading

1. Current explicit Human decision, within its stated scope.
2. Exact reviewed/accepted checkpoint and pinned source authority; scope and approval status are separate.
3. `docs/delivery/START_HERE.md`, `SOURCE_LOCK.json`, `GIT_RECONCILIATION.md`, and `DECISION_AND_GAP_REGISTER.md` for this preparation lane.
4. Frozen source contracts indexed in `docs/delivery/SOURCE_INDEX.md`; qualified aliases distinguish the two historical ADR-013 documents. An alias is not an amendment or new product version.
5. Consolidated delivery specifications, followed by the exact task contract.
6. Original Project State/Handoff/Roadmap sections as historical or source evidence. Their old NEXT_GOAL/NOT_STARTED text is not this lane's active routing.
7. Actual source and fresh deterministic evidence establish implementation facts; document presence never proves implementation.

Read only relevant contracts, diff, call chain and tests after the entry documents. Imported reference documents retain historical stop/approval text for provenance; they cannot start old goals, confer authority, or override the current pause. Do not substitute chat memory, local paths, branch names or writer reports for verified facts.

## Mandatory engineering boundaries

- One active Writer per task/working branch. The Writer is not the Independent Reviewer of the same patch. A controller or renamed subagent does not by itself prove independence.
- Discover the workspace using `git rev-parse --show-toplevel`. Use repo-relative paths. Canonical repository is `lichen200224-bot/PolyNexus`.
- At each write/publication gate verify remote ref, expected parent, working/staged state and exact path allowlist. A local `origin/*` ref is only a cache. GitHub API ref reads are recorded as API evidence, not fabricated `git ls-remote` exit codes.
- No `git add .`, `git add -A`, force push, history rewrite, destructive reset/clean, broad checkout/discard, branch deletion or remote reconfiguration by inference.
- A SYNC/CANDIDATE commit is not acceptance. Never amend/rebase away a reviewed candidate. Changes create new immutable checkpoints.
- Preserve the exact accepted product source; imported planning branches are not product ancestors or accepted implementation merely because their documents are reused.
- Core owns identity, lifecycle, policy, evidence and accepted-result semantics. Vendor logic stays in Adapter/Driver. UI does not directly operate SQLite, Git, filesystem processes or vendor events.
- `Task != WorkGeneration != Run != Candidate`; Run remains durable execution identity, not a newly invented Attempt Aggregate. Canonical identity and Golden values come from the frozen REV1 source, not this file.
- Product Human authorization is distinct from development permission. Agent credentials never become Human credentials. D11-C remains fail-closed; D11-A-LP requires its specified proof. Accept does not imply commit/merge/push/apply/release.
- Secret values never enter ordinary Domain records, Evidence, logs, Git, exports or handoffs. Managed worktrees and PROJECTED_STAGING are not hostile-code sandboxes.
- Alembic remains migration authority. No real user database changes during preparation.
- Real command/tool results and actual exits are required. SKIPPED/NOT_RUN/UNKNOWN/stale evidence are not PASS. Negative child exits and the checking runner's exit are distinct. Fixtures do not establish live conformance.
- Within a subsequently authorized batch, ordinary defects are fixed and re-reviewed without repeated Human micro-approval. Scope, frozen semantics, security expansion, irreversible effects, budget overruns and unresolved ownership are exception gates.

## Publication and next owner

Preparation Writer: ChatGPT. Product implementation: HOLD. Preparation candidate must undergo fresh independent design review and applicable clean-clone/environment verification. This context may report author self-checks and API publication evidence only, not independent acceptance.

Preserved predecessor instructions: `docs/delivery/references/AGENTS.product-baseline.md`. Their requirements apply unless this explicitly scoped preparation instruction changes the routing/publication workflow; product safety semantics are not relaxed.
