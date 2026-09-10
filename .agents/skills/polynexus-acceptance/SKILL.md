---
name: polynexus-acceptance
description: Use for PolyNexus milestone or release acceptance. Requires current deterministic evidence, exit codes, failure isolation checks, and honest maturity labeling.
---

Track A precedence: read [Goal Execution Framework](../../../docs/governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) and [Current Goal](../../../docs/IMPLEMENTATION_CURRENT_GOAL.md) first. This specialized skill cannot authorize implementation, formal sync, delegation or push. Codex is the default Writer; independent reviewer must be a different context. Goal-specific handoff replaces edits to global current pointers on parallel branches. Legacy verdict terms below do not override Track A Goal PASS / NEED_FIX / HOLD or change product enums.

# PolyNexus Acceptance

1. Read `docs/08_ACCEPTANCE_STRATEGY.md` and the milestone DoD only.
2. Start from a clean/reproducible state when applicable; record versions.
3. Run required commands/tests now. Do not reuse historical PASS logs as current evidence.
4. Capture command, timestamp, exit code, failed/skipped cases, artifact references.
5. Verify high-risk semantics: cancel really stops, timeout cleans resources, driver/adapter failure is isolated, local-only never silently egresses, migration/backup restore works.
6. AI review result is AI_OPINION; it cannot override tool FAIL.
7. Mark unsupported/preview integrations truthfully; broad compatibility is not certification.
8. Final result must be PASS / FAIL / NEED ACTION / HUMAN DECISION with explicit reasons.
