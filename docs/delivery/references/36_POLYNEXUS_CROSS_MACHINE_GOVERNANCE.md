# PolyNexus Cross-Machine & Multi-Tool Governance

Status: `HUMAN_APPROVED / TRANSITION ACTIVE`
Date: 2026-09-12
Model: `FlowGov-compatible PolyNexus Profile`

## 1. Purpose

This document removes machine-path/tool coupling from PolyNexus development and establishes a remote-first, SHA-first collaboration model that can be inherited by future governance tooling.

It does **not** change PolyNexus product architecture, V1 bounded score, G30/WP-20 status, runtime contracts, or the active BASELINE-DEBT-01 implementation scope.

## 2. Canonical identity

Current canonical development remote:

```text
GitHub: lichen200224-bot/PolyNexus
```

Project state is identified by:

```text
canonical remote + exact SHA + task branch
```

Not by drive letter, local folder, AI conversation, local remote-tracking branch, OneDrive copy, or ZIP.

Current governance/product anchors at adoption start:

```text
MCF-01 product checkpoint: 96ae53537e5501f1ef374182e7e1966b921a7883
terminal docs checkpoint: 86d5939044c1d7ec2a991820f39287481ee9120f
```

## 3. Machine-independent paths

Repository location is local preference. Tools discover root with:

```text
git rev-parse --show-toplevel
```

Tracked contracts use relative paths or `<REPO_ROOT>`, `<TASK_WORKTREE>`, `<LOCAL_EVIDENCE_ROOT>`. Optional `.flowgov.local.toml` is gitignored/non-authoritative.

## 4. Remote truth and ref caches

Remote branch existence/SHA must be resolved from the canonical remote, normally:

```text
git ls-remote --heads origin refs/heads/<branch>
```

A missing `origin/<branch>` local ref means only that the local cache/refspec may be narrow. It is not evidence that GitHub lacks the branch.

Developer clones should not use `--single-branch`. Disposable clean-clone verification may use it.

## 5. Checkpoint maturity

Three distinct Git checkpoint classes:

1. `SYNC_CHECKPOINT` — cross-machine/tool continuity; may be incomplete or red.
2. `CANDIDATE_CHECKPOINT` — immutable pushed SHA ready for independent review; not accepted.
3. `ACCEPTED_CHECKPOINT` — independently verified and Human accepted under the task contract.

No commit message, push exit 0, or branch name alone promotes maturity.

## 6. Task branch execution authority

A Human Task Start Gate may issue a bounded execution envelope allowing Writer to create/push non-force SYNC and CANDIDATE checkpoints on the task branch without repeated micro-approval. This authority is restricted to the disclosed task scope and branch.

Human gates remain required for architecture/scope expansion, secrets/authenticated external action, irreversible operations, candidate acceptance, integration, release, force/history rewrite, and remote configuration.

## 7. Reviewer object

Independent review targets the exact pushed Candidate SHA. Dirty Writer worktree is not the portable review object. `Writer != Independent Reviewer`.

Fixes create a new commit/SHA; do not amend or rebase away an already reviewed candidate.

## 8. Worktree strategy

Recommended:

- canonical local clone: coordination/fetch/worktree creation;
- task worktree: Writer changes for one branch;
- disposable verification clone/worktree: independent review/clean-clone verification.

All locations are machine-local.

## 9. Role model

Governance assigns roles, not fixed tools:

```text
HUMAN_AUTHORITY
ARCHITECT
WRITER
INDEPENDENT_REVIEWER
SPECIALIZED_VERIFIER
```

Codex/OpenCode/Antigravity/Claude/future tools can fill a role when explicitly routed. Defaults are recommendations only.

## 10. Start protocol

Every new machine/tool session must resolve:

```text
repo root
canonical remote
expected remote branch + SHA
local fetch/ref state
ancestry
working/staged state
current routing index
current task contract
assigned role
```

Only then can START_GATE pass.

## 11. Handoff design

`docs/37_CURRENT_ROUTING_INDEX.md` is the concise active index. Historical details stay in `docs/11_PROJECT_STATE.md`, `docs/12_HANDOFF_CURRENT.md`, task docs, Git history, and evidence references.

Current routing index should not embed self-referential claims such as “this same commit has already been pushed.” Post-push/clean-clone facts belong to an external receipt/current next checkpoint, avoiding endless docs-sync loops.

## 12. Integration target

Target model after separate controlled consolidation:

```text
task branch -> accepted PR -> develop -> release gate -> main
```

Current GitHub default branch is still legacy `feature/g24-g30-development-completion-routing`. This governance transition does not change it. Establishing `develop`, branch protection/rules, and default-branch change requires a dedicated consolidation gate after current product/debt work is safely checkpointed.

## 13. Git identity

Recommended repo-local PolyNexus commit identity:

```text
lichen200224-bot <288622566+lichen200224-bot@users.noreply.github.com>
```

Global identity is not required. Identity attribution never substitutes for Human acceptance.

## 14. Evidence and CI direction

Git tracks source/tests/governance/small deterministic summaries. Local DBs, secrets, browser profiles, large logs/JUnit/screenshots remain ignored or CI artifacts.

Future phase should add Repo Doctor / Task Start / Sync Checkpoint / Clean Clone helpers and GitHub Actions as a neutral execution environment. Helper implementation is a separate task from this docs transition.

## 15. Fixed vs flexible

Fixed governance core:

- canonical remote + exact SHA;
- no secret values in Git;
- Single Active Writer;
- Writer != Independent Reviewer;
- immutable reviewed candidate;
- actual exit code / truthful evidence;
- no force/history rewrite by inference.

Flexible per-task routing:

- tool/model/reasoning level;
- Writer/Reviewer assignment;
- browser verifier need;
- exact test depth;
- task worktree path;
- migration/architecture gates.

This allows new machines/tools/models without rewriting project governance.
