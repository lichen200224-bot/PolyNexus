# Local Workspace Profile — Portable

Status: `MACHINE_LOCAL / NON_AUTHORITATIVE`

## Repository location

PolyNexus does **not** require a fixed drive or directory. Examples such as `D:\AI學習教材\PolyNexus`, `C:\Projects\PolyNexus`, `E:\Work\PolyNexus`, or a Linux path are all valid machine-local choices.

The repository root must be discovered at runtime:

```text
git rev-parse --show-toplevel
```

Tracked source, governance, task, test, or handoff contracts must use repo-relative paths or symbolic names such as `<REPO_ROOT>`, `<TASK_WORKTREE>`, and `<LOCAL_EVIDENCE_ROOT>`. An absolute local path may appear only in ephemeral operational evidence and must never become cross-machine identity.

## Optional machine-local profile

A machine may copy `.flowgov.local.example.toml` to `.flowgov.local.toml` for local worktree/evidence/tool-command preferences. `.flowgov.local.toml` is gitignored, non-authoritative, and must not contain secret values.

## Rules

1. Repository identity is remote repository + exact Git SHA, not filesystem path.
2. Cross-machine continuation uses the canonical remote and exact checkpoint.
3. Single Active Writer remains mandatory per task branch.
4. Task worktrees may live anywhere on the machine.
5. Runtime DB, logs, credentials, browser profiles, generated artifacts, and local evidence stay outside tracked Git unless an approved evidence contract explicitly allows a sanitized small file.
6. Moving or recloning the repository does not require a product ADR.

## Portability gate

From any location inside the repository:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check_workspace_path.ps1
```

Expected semantic result:

```text
Workspace portability PASS
```

No drive-letter or absolute-directory equality is required.
