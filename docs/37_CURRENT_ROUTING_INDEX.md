# PolyNexus Current Routing Index

Status: `AUTHORITATIVE ACTIVE ROUTING INDEX`
Updated: 2026-09-12

This file is intentionally concise. It supersedes stale “current task” wording in older Project State/Handoff sections when they conflict; historical records remain valid provenance.

## Canonical remote

```text
provider: GitHub
repository: lichen200224-bot/PolyNexus
remote truth: git ls-remote
```

## Current accepted anchors

```text
MCF01_PRODUCT_CHECKPOINT=96ae53537e5501f1ef374182e7e1966b921a7883
MCF01_TERMINAL_DOC_CHECKPOINT=86d5939044c1d7ec2a991820f39287481ee9120f
MCF01=CHECKPOINTED / ACCEPTED_WITH_PRE_EXISTING_BASELINE_DEBT
V1_BOUNDED_DEVELOPMENT_ACCEPTANCE_SCORE=95/100
OVERALL_PROJECT_COMPLETION=NOT_DEFINED
WP20=NOT_COMPLETE
G30=NEED_ACTION
```

## Active product lane

```text
TASK_ID=BASELINE-DEBT-01
BRANCH=feature/baseline-debt-01-deterministic-lifecycle-cleanup
ROLE=WRITER (Codex current assignment)
START_SHA=86d5939044c1d7ec2a991820f39287481ee9120f
STATUS=IMPLEMENTING / ARCHITECTURE_GATE_APPROVED
```

Human Architecture Gate authorizes durable per-Run event sequence migration/ordering plus deterministic timeout/cancellation cleanup within the exact task scope. It does not authorize MCF-02, holaOS/OpenHands production integration, G30/WP-20 updates, score changes, or integration into accepted branches.

## Parallel governance lane

```text
TASK_ID=GOV-FLOWGOV-ADOPTION-01
BRANCH=governance/flowgov-adoption-poly
START_SHA=86d5939044c1d7ec2a991820f39287481ee9120f
STATUS=GOVERNANCE_TRANSITION
PRODUCT_SOURCE_CHANGE=NO
```

Purpose: remove fixed local path assumptions and establish remote-first/SHA-first/Role-first cross-machine governance. This branch must not modify BASELINE-DEBT-01 production files.

## Default branch

GitHub current default branch remains:

```text
feature/g24-g30-development-completion-routing
```

Target after dedicated controlled consolidation:

```text
develop (integration/default)
main (release)
```

No default-branch change is authorized by this routing index.

## Session start

Every new tool/machine reads:

```text
AGENTS.md
this file
current task doc
```

Then resolves the canonical remote exact SHA before writing.
