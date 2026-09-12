# PolyNexus V1 Acceptance Strategy

Status: `SHA-FIRST ACCEPTANCE TRANSITION` (2026-09-12)

## 1. Principle

AI Opinion ≠ Evidence. PASS requires current deterministic evidence, actual exit codes, correct scope, and the required independent/Human gates. Old logs are historical only. `SKIPPED != PASS`.

## 2. Acceptance layers

- Unit: Domain logic/parser/policy/normalization.
- Contract/Conformance: Runtime/Endpoint/Driver semantics.
- Integration: Core ↔ adapter/storage/workflow/browser companion.
- E2E: bounded product journeys / Golden Workflows.
- Release: migration, backup/restore, security, packaging, known limitations.

## 3. Evidence contract

Every governed verification records at least: exact SHA, command/tool action, actual exit code (or N/A for true manual observation), summary, test names/counts, environment, artifact reference, known limitations, and skipped/unverified coverage.

Long stdout/raw artifacts remain outside the main report. Secrets, credentials, cookies, tokens, browser profiles, and private raw data must not enter Git/evidence reports.

## 4. Immutable Candidate Acceptance Model

The preferred sequence is:

```text
Human-authorized task scope
-> Writer implementation
-> deterministic local checks
-> CANDIDATE_CHECKPOINT commit + non-force push on task branch
-> Independent Reviewer verifies exact Candidate SHA
-> NEED_FIX => new Candidate SHA (no amend/history rewrite)
-> VERIFIED_PASS
-> Human accepts exact SHA
-> integration/clean-clone/release gates as applicable
```

Candidate commit/push is publication for review, not acceptance. A Human Task Execution Envelope may pre-authorize bounded SYNC/CANDIDATE commits on that task branch. It never pre-authorizes integration, release, force push, architecture expansion, or external/secret actions.

## 5. Checkpoint semantics

- `SYNC_CHECKPOINT`: continuity only; may be incomplete/red.
- `CANDIDATE_CHECKPOINT`: immutable review object; not accepted yet.
- `ACCEPTED_CHECKPOINT`: independently verified and Human accepted under the task contract.

Review and acceptance must name exact SHA. Dirty/uncommitted workspace evidence alone is not a portable acceptance object.

## 6. Independent review

`Writer != Independent Reviewer` for the same patch. Reviewer is read-only against that candidate, may use isolated clone/worktree, and validates diff/allowlist/protected areas/ADR impact/evidence.

Allowed verdicts: `VERIFIED_PASS`, `NEED_FIX`, `FAIL`, `NEED_ACTION`.

A failing required deterministic check remains FAIL unless the task contract explicitly defines a bounded alternative and Human separately accepts it. MCF-01's historical differential exception is task-specific and creates no global waiver.

## 7. Runtime / lifecycle / policy critical checks

As applicable: health/readiness, stable Run identity, truthful terminal state, timeout, cancellation, process/resource cleanup, normalized errors/results, evidence/artifact provenance, version/maturity, classification/egress policy, secret boundary, backup/migration.

Resume capability must be truthful (`NATIVE`/`MANAGED`/`NONE`). Adapter or browser-driver failure must not fabricate Core success.

## 8. Migration acceptance

Every schema migration requires: approved architecture/scope, backup/restore boundary, upgrade tests, old-data preservation, downgrade/restore semantics, fresh/reopen verification, and actual exit codes. Alembic is migration authority.

## 9. Governance/documentation changes

Governance patch follows the same immutable candidate model. Product and governance checkpoints remain distinguishable. A governance Writer cannot sign its own patch as Independent Reviewer.

Large historical state files need not be rewritten merely to report post-push facts. Prefer immutable candidate/acceptance receipts and current routing index to avoid self-referential commits that forever describe the previous Git state.

## 10. Cross-machine readiness

Remote truth is queried from the canonical remote, not inferred only from local tracking refs. Cross-machine continuation requires an exact pushed SHA. Acceptance/integration checkpoints additionally require clean-clone verification when the task contract requires it.

A SYNC checkpoint can be continued on another machine but must remain labeled SYNC. Conversation history, AI memory, ZIP/manual copy, OneDrive directory, or local absolute path is not a valid accepted cross-machine identity.

## 11. Browser / external evidence

Fixture/browser-controlled evidence and authenticated live vendor evidence are separate maturity classes. No login/send/credential action may be inferred from a test fixture. Manual observations without a process exit code use `exit_code: N/A`.

## 12. Human authority

Human gates are concentrated at high-value boundaries: task/scope authorization, architecture, secret/external/irreversible action, candidate acceptance, integration, release, destructive Git, and remote configuration.

Routine task-branch sync/candidate commit+push can be delegated only through an explicit current Task Execution Envelope.

## 13. PolyNexus development score

`V1_BOUNDED_DEVELOPMENT_ACCEPTANCE_SCORE` remains a G24–G30 bounded model; it is not overall project completion or production readiness. WP scoring requires its own accepted/checkpoint contract. `OVERALL_PROJECT_COMPLETION=NOT_DEFINED` unless a future Human-approved denominator explicitly replaces this rule.

Current external truth remains `WP20=NOT_COMPLETE`, `G30=NEED_ACTION` until their specific acceptance gates complete.
