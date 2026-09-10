---
name: polynexus-workflow-authoring
description: Use when adding or changing PolyNexus declarative workflow definitions/templates under the frozen V1 workflow model.
---

Track A precedence: read [Goal Execution Framework](../../../docs/governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) and [Current Goal](../../../docs/IMPLEMENTATION_CURRENT_GOAL.md) first. This specialized skill cannot authorize implementation, formal sync, delegation or push. Codex is the default Writer; independent reviewer must be a different context. Goal-specific handoff replaces edits to global current pointers on parallel branches. Legacy verdict terms below do not override Track A Goal PASS / NEED_FIX / HOLD or change product enums.

# PolyNexus Workflow Authoring

1. Read ADR-009 and the relevant workflow requirement only.
2. Author YAML that validates against the current versioned schema.
3. Use only V1 nodes: CONTEXT, AI_TASK, PARALLEL_AI, CROSS_REVIEW, TOOL, EVIDENCE_CHECK, HUMAN_GATE, SYNTHESIS, limited CONDITION.
4. Do not embed arbitrary Python/JavaScript, loops, provider-specific branches, or hidden prompt-only control logic.
5. Workflow requirements should name capabilities/roles/policies, not vendors when avoidable.
6. Never overwrite semantics of a workflow version already referenced by historical runs; create a new version.
7. Add validation/smoke tests and record actual results.
