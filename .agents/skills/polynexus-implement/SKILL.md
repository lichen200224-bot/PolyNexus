---
name: polynexus-implement
description: Use to implement an approved PolyNexus feature or bug fix with narrow context, Git safety, tests, and minimal token usage.
---
# PolyNexus Implement

1. Confirm current branch, `git status`, Project State, and Current Handoff.
2. Read only the relevant specification/contract and affected files.
3. State the smallest implementation slice and tests before editing.
4. Preserve confirmed Domain/Contract boundaries; do not broaden scope to “clean up” unrelated areas.
5. Add/modify targeted tests with the implementation.
6. Run the smallest deterministic tests first; expand only after they pass.
7. For failures, pass the agent only failing test names + relevant excerpts, not the full log by default.
8. Update Current Handoff with actual commands and exit codes.
9. Do not claim PASS if a required test was skipped or did not exit successfully.
