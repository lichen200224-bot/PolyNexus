---
name: polynexus-runtime-conformance
description: Use when implementing or validating a PolyNexus Runtime Adapter. Enforces normalized lifecycle, cancel/timeout cleanup, evidence, compatibility and truthful maturity.
---

Track A precedence: read [Goal Execution Framework](../../../docs/governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) and [Current Goal](../../../docs/IMPLEMENTATION_CURRENT_GOAL.md) first. This specialized skill cannot authorize implementation, formal sync, delegation or push. Codex is the default Writer; independent reviewer must be a different context. Goal-specific handoff replaces edits to global current pointers on parallel branches. Legacy verdict terms below do not override Track A Goal PASS / NEED_FIX / HOLD or change product enums.

# PolyNexus Runtime Conformance

1. Read ADR-007 and the Core Runtime Contract sections only.
2. Keep vendor-specific behavior inside the adapter; do not branch Core by provider name.
3. Implement/verify: health, readiness, capabilities, create/submit, stable ID, status, result, normalized error, timeout, cancel, resume mode, evidence/artifacts, cleanup, version info.
4. Cancel is not PASS until child/tool/process/resource cleanup is verified.
5. Timeout reuses cleanup semantics but records timeout reason/state.
6. Resume is NATIVE / MANAGED / NONE; never fake native resume.
7. Run targeted conformance tests and record actual exit codes.
8. Maturity cannot exceed the highest level justified by current evidence.
