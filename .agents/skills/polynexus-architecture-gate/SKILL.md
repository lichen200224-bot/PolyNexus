---
name: polynexus-architecture-gate
description: Use before changing PolyNexus core domain models, contracts, workflow semantics, evidence/policy rules, persistence boundaries, or other high-coupling architecture.
---

Track A precedence: read [Goal Execution Framework](../../../docs/governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) and [Current Goal](../../../docs/IMPLEMENTATION_CURRENT_GOAL.md) first. This specialized skill cannot authorize implementation, formal sync, delegation or push. Codex is the default Writer; independent reviewer must be a different context. Goal-specific handoff replaces edits to global current pointers on parallel branches. Legacy verdict terms below do not override Track A Goal PASS / NEED_FIX / HOLD or change product enums.

# PolyNexus Architecture Gate

1. Read `docs/00_SCOPE_BASELINE.md`, `docs/10_DECISION_LOG.md`, and the relevant SA/SD section only.
2. Identify whether the request changes a confirmed Decision, a stable Contract, or only an implementation detail.
3. If it changes scope/contract, do not edit code first. Produce a concise proposal: problem, options, compatibility impact, migration impact, test impact, recommended ADR.
4. Prefer extension through existing Contract/Adapter/Workflow/Artifact/Context boundaries over a new subsystem.
5. Reject vendor-specific Core branches such as `if provider == X` unless the normalized contract itself is being evolved.
6. Evaluate V1 time impact and future refactor risk.
7. Only implement after human/owner decision is recorded when the change is architectural.
