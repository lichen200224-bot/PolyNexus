---
name: polynexus-handoff
description: Use when transferring an active PolyNexus task between Codex, OpenCode, Antigravity, or a human. Produces a compact delta handoff rather than a full project summary.
---
# PolyNexus Handoff

Update `docs/12_HANDOFF_CURRENT.md` only with current-task delta:
- TASK / OWNER / BRANCH
- Goal
- Completed / Changed files
- Tests run + actual exit codes
- Known issue/blocker
- Next exact step
- Do Not Change

Keep it compact. Do not paste full logs, full chat history, or full architecture. Put long evidence in artifact/log files and reference their paths/hashes.

If a new architecture decision was made, also update Decision Log/ADR separately; do not hide permanent decisions only inside Handoff.
