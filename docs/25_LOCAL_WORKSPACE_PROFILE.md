# Local Workspace Profile — v1.0.2

Date: 2026-08-17

## Primary Development Path

```text
D:\AI學習教材\PolyNexus
```

This path is the canonical workspace on the current Windows development machine for the first PolyNexus V1 development cycle.

## Rules

1. Codex, OpenCode and Antigravity open the same physical repository folder above.
2. Single Active Writer remains mandatory.
3. Git branches/checkpoints are the protection boundary; do not create separate copies per AI tool.
4. PolyNexus product code must not hard-code this path. Use repository-relative or configuration-driven paths.
5. Runtime DB, logs, secrets and generated artifacts remain outside Git according to `.gitignore` and the storage/security ADRs.
6. If the workspace is intentionally moved later, update this profile and environment checks; this does not require a product ADR.

## Local Path Gate

From repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_workspace_path.ps1
```

Expected result:

```text
Workspace path PASS: D:\AI學習教材\PolyNexus
```
