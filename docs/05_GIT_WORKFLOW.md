# PolyNexus Git Workflow — Remote-first / SHA-first

Status: `HUMAN_APPROVED TRANSITION MODEL` (2026-09-12)

## 1. Core identity

PolyNexus development identity is:

```text
canonical remote repository + exact commit SHA + task branch
```

Local path and local `origin/<branch>` refs are caches/conveniences, not authority. Canonical remote is currently GitHub `lichen200224-bot/PolyNexus`.

## 2. Portable path model

Repository may live anywhere. Discover root with:

```text
git rev-parse --show-toplevel
```

Do not commit machine-specific absolute paths as contracts. Optional `.flowgov.local.toml` is gitignored and non-authoritative.

## 3. Remote truth

Before trusting a local remote-tracking ref, query the real remote:

```text
git ls-remote --heads origin refs/heads/<branch>
```

`origin/<branch>` missing locally does **not** prove the GitHub branch is missing. Explicit exact-ref fetch is allowed when needed. Developer clones should fetch normal branch namespace; `--single-branch` is reserved for disposable verification clones.

## 4. Branch model

Current repository history is transitional. Long-term target:

- `main`: accepted RC/release only.
- `develop`: accepted integration line and future default branch.
- `feature/<scope>` / `fix/<scope>` / `architecture/<scope>` / `governance/<scope>` / `docs/<scope>`: task branches.

Current GitHub default branch remains `feature/g24-g30-development-completion-routing` until a separate controlled consolidation proves the correct lineage. This document does not authorize changing default branch, merging histories, force push, or rewriting accepted checkpoints.

## 5. Worktree model

Recommended:

```text
canonical local clone -> fetch / coordination / worktree creation
separate task worktree -> actual Writer changes
```

Worktree directory is machine-local. One task branch has one Active Writer at a time. Different tools may sequentially use the same task worktree.

## 6. Three checkpoint types

### SYNC_CHECKPOINT
Purpose: cross-machine/cross-tool continuation. It may be incomplete or red. It is not review PASS and earns no acceptance.

### CANDIDATE_CHECKPOINT
Purpose: immutable review object. Writer has completed the authorized candidate and pushed an exact SHA. Candidate != accepted.

### ACCEPTED_CHECKPOINT
Purpose: independent review and Human acceptance have approved the candidate/receipt under the task contract.

Commit existence alone never means acceptance.

## 7. Task Execution Envelope

A Human Start Gate may grant bounded authority for the current task branch to:

- edit exact authorized scope;
- run tests/validators;
- create non-force SYNC commits for machine/tool handoff;
- create/push a CANDIDATE commit for independent review.

This authority never includes `develop/main`, other task branches, force push, remote config, secrets/external send, architecture/scope expansion, integration, or release unless separately stated.

This replaces repeated low-value approvals for every task-branch sync while preserving Human gates at architecture, acceptance, integration, release, secrets/external actions, and destructive Git operations.

## 8. Start protocol

Every Writer/Reviewer on every machine resolves the task from the canonical remote:

```text
1. git rev-parse --show-toplevel
2. git remote -v
3. git ls-remote --heads origin <expected branch>
4. verify expected exact predecessor SHA
5. fetch exact branch/ref
6. verify ancestry
7. verify branch / HEAD / status / staged state
8. read AGENTS + Current Routing Index + task doc
9. START_GATE
```

A local remote-tracking mismatch is diagnosed before declaring remote failure.

## 9. Candidate review protocol

Writer publishes an immutable Candidate SHA on the task branch. Independent Reviewer verifies:

- exact SHA and parent/predecessor;
- diff/allowlist/scope;
- deterministic evidence with actual exit codes;
- protected areas/ADR impact;
- known limitations/unverified items.

Reviewer does not depend on Writer's uncommitted working tree. `Writer != Independent Reviewer`.

A `NEED_FIX` result adds new candidate commit(s); do not amend/rewrite an already reviewed SHA.

## 10. Integration model

Long-term target:

```text
task branch -> reviewed/accepted PR -> develop -> release gate -> main
```

Task branch may preserve detailed history. Integration may use squash merge when the Human/PR gate explicitly chooses it. Accepted evidence must still point to the reviewed candidate SHA and integration result.

Until controlled consolidation finishes, no task may infer that current GitHub default branch is `develop`.

## 11. Git identity

Recommended PolyNexus repo-local identity:

```text
user.name  = lichen200224-bot
user.email = 288622566+lichen200224-bot@users.noreply.github.com
```

Configure at repository local scope when needed; do not require or overwrite global identity. Identity does not grant acceptance authority.

## 12. Safety

Never use broad destructive shortcuts to resolve governance mismatches:

- no force push / force-with-lease without explicit destructive gate;
- no `reset --hard`, `clean -fd`, branch deletion, or remote reconfiguration by inference;
- no `git add .`, `git add -A`, `git push --all` for governed checkpoints;
- no secret values, private browser profiles, raw credentials, local DB, or large raw evidence in Git.

## 13. Cross-machine continuation

A machine may continue only from an exact remote SHA. Conversation, AI memory, local path, OneDrive copy, or ZIP is not a valid cross-machine handoff.

A pushed SYNC checkpoint is valid for continuation but not for acceptance. A pushed CANDIDATE checkpoint is valid for review. Clean-clone verification is required for accepted/integration/release checkpoints where the task contract requires it.

## 14. Local backup

A local bare remote may exist as `backup`, but it is not canonical cross-machine truth. `origin` should resolve to the canonical GitHub remote after controlled local configuration reconciliation. Remote-name changes are operational changes and must not be guessed by an Agent.

## 15. Controlled consolidation target

After BASELINE-DEBT-01 and current governance transition are safely checkpointed, perform a dedicated consolidation task to:

- determine authoritative accepted lineage;
- establish/verify `develop`;
- reconcile legacy default branch;
- add branch protection/rules where available;
- change GitHub default branch only after clean-clone/ancestry validation.

No step above is authorized merely by this workflow document.
