# PolyNexus — Current Agent Entry

## Current assignment

Canonical repository: `lichen200224-bot/PolyNexus`

Current documentation branch: `planning/enhanced-runtime-control-plane`

Current task: `ENHANCED-DELIVERY-REPLAN-01`

Read first:

1. `docs/37_CURRENT_ROUTING_INDEX.md`;
2. `docs/delivery/START_HERE.md`;
3. `docs/delivery/CURRENT_PRODUCT_STATE.md`;
4. `docs/delivery/STRATEGIC_RUNTIME_FLEET.md`;
5. `docs/delivery/GOAL_PLAN.md`;
6. `docs/delivery/EXECUTION_CONTRACT.md`.

Human has explicitly approved the enhanced-version convergence direction: preserve the existing Core/Generation/Runtime/Evidence/Human architecture, add the company-strategic Runtime Fleet, expose bounded multi-agent Council/Workflow, and deliver a Unified Work Control Plane. Product version remains unchanged.

This branch is documentation/planning only. New product writes do not start until this exact documentation candidate receives the fresh non-writer review required by `docs/delivery/DESIGN_REVIEW.md`.

## Current product routing

Historical PREP/HOLD/NEXT_GOAL text is not active routing when it conflicts with the current entry documents or remote truth.

Expected current facts at plan time, all requiring remote read-back before use:

```text
D1B/current route:
  e9538f328f409e2cb7d6868a8b79cc33ba4bdd87

B01 technical candidate:
  codex/product-b01-tech
  ca85d22c44062d2856ab037a1ee1556ea26c70cc

old MCF-02 candidate:
  030890b30160f1063ac2cef1d36705a9ea70bddb
  REJECTED / NOT_ADOPTED
```

After fresh docs review, the first product action is G0 Current/B01 reconciliation. Subsequent approved route is D2b Strategic Runtime Fleet -> D3 Multi-Agent Council/Workflow -> D4 Unified Work Control Plane -> required remainder -> T1/T2 -> Delivery -> Final Human UAT.

## Product roles after start gate

`Codex = SOLE_PRODUCT_WRITER + TEST_EXECUTOR`

`ChatGPT = PROJECT_PM + ARCHITECTURE_GOVERNANCE_AUTHORITY + INDEPENDENT_PRODUCT_ACCEPTANCE_CENTER`

Codex implements/tests/fixes/publishes immutable product candidates. ChatGPT independently reviews canonical remote exact candidates and does not modify the candidate under review. A ChatGPT PASS may authorize the next already-approved dependency-ready product unit without another Human response.

Normal remaining Human involvement is one concentrated final integrated UAT / acceptance session. Conditional Human involvement is limited to real provider/Windows Hello login need, architecture/security/scope exceptions, or separate release/merge/deploy/payment/production-data side effects.

## Authority and loading

Priority:

1. Current explicit Human decision within its scope.
2. Canonical remote truth + exact accepted/reviewed checkpoints.
3. This `AGENTS.md`, `docs/37_CURRENT_ROUTING_INDEX.md`, `START_HERE.md`, `CURRENT_PRODUCT_STATE.md` and current exact review receipt.
4. Frozen/source authority indexed by `SOURCE_LOCK.json` / `SOURCE_INDEX.md`.
5. Consolidated delivery specifications and the exact assigned unit contract.
6. Historical project state/handoff/roadmap only as provenance when they conflict with current routing.

Do not substitute chat memory, local caches, branch names or Writer self-reports for verified facts.

## Mandatory engineering boundaries

- One active product Writer per task/working branch. Writer is not the independent reviewer of the same product patch.
- This ChatGPT context is the documentation Writer for `ENHANCED-DELIVERY-REPLAN-01`; it cannot self-issue the fresh independent docs review PASS for this docs patch.
- At each product candidate gate verify canonical remote ref, exact SHA/parent/ancestry, actual changed files/source, actual tests/exits and required negative evidence.
- No `git add .`, `git add -A`, force push, destructive reset/clean, history rewrite, branch deletion or default/protection changes by inference.
- A commit/candidate is not acceptance. Reviewed SHA is immutable; repairs use a new SHA.
- Preserve accepted product/history. Do not merge the rejected `030890b3...` MCF-02 branch as a current implementation source.
- Core owns Project/Task/WorkGeneration/Run/Candidate identity, lifecycle, policy, Evidence, Human decision and accepted-result semantics. Vendor logic stays behind adapter/transport boundaries.
- Do not create duplicate AgentSession/AgentMessage/AgentHandoff/AgentWorkspace authority merely to imitate another multi-agent framework.
- `Task != WorkGeneration != Run != Candidate`. Do not invent an Attempt aggregate that replaces these identities.
- Runtime Fleet support is capability-based and evidence-backed. `UNKNOWN`, `UNSUPPORTED`, `ENVIRONMENT_BLOCKED`, `ResumeMode.NONE` are valid truthful states.
- No silent runtime fallback or post-dispatch rebinding.
- Secrets never enter ordinary Domain records, Evidence, logs, Git, exports or handoffs. Do not extract/replay browser cookies/vendor session tokens/private credentials.
- `PROJECTED_STAGING` / managed worktrees are controlled workspaces, not hostile-code sandboxes.
- Alembic remains migration authority. Production/user DB effects require the explicit approved path.
- Real commands and actual exits are required. `SKIPPED`, `NOT_RUN`, `UNKNOWN`, stale evidence and Writer `PASS` are not acceptance. Fixture evidence does not establish real target conformance.
- Vendor exit `0` / `SUCCESS` cannot replace Core postcondition, Artifact/Evidence or cleanup verification.
- Ordinary same-scope defects are fixed by Codex and re-reviewed without Human micro-approval. Scope/frozen/security/trust/irreversible/cost/egress exceptions stop only the affected action and follow `EXECUTION_CONTRACT.md`.

## Runtime Fleet boundary

Enhanced-version fleet includes Codex, OpenCode, Gemini CLI, Claude Code and Antigravity. Use `docs/delivery/STRATEGIC_RUNTIME_FLEET.md` for target-specific requirements.

OpenCode and Gemini should share a generic ACP transport where current supported surfaces permit. Claude and Antigravity may use supported non-ACP structured/headless transports. PolyNexus is a multi-transport Runtime Control Plane, not an ACP-only frontend.

Do not enable arbitrary plugins/MCP/remote skills or dynamic routing simply because a vendor supports them.

## Publication and next owner

Current work is documentation-only publication on `planning/enhanced-runtime-control-plane`. After publication, next required role is `FRESH_INDEPENDENT_ENHANCED_REPLAN_REVIEWER`.

A docs review PASS allows preparation of the G0 product start receipt; it does not itself accept B01, start D2b, merge/release or constitute final Human acceptance.
