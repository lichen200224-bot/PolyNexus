# PolyNexus Antigravity Workspace Rule

Before any write operation:
1. Read root `AGENTS.md`.
2. Read `docs/11_PROJECT_STATE.md` and `docs/12_HANDOFF_CURRENT.md`.
3. Read only task-relevant specification/ADR/code.
4. Check Git branch/status and confirm Antigravity is the current Active Writer. If not, remain read-only.

ADR-001～010 are frozen for V1. Architecture changes require explicit human decision.

Primary Antigravity role: Browser/E2E/milestone independent verification. Do not perform a third full review on every small change.

Verification rules:
- Real command/tool evidence decides PASS/FAIL.
- Never use historical logs as current PASS.
- Never convert Tool FAIL to PASS by AI consensus.
- Web driver failure must not be treated as Core failure unless the tested workflow explicitly requires that driver.
- No secret/credential may enter log/evidence/handoff.

End substantial tasks by updating `docs/12_HANDOFF_CURRENT.md` with delta only.
