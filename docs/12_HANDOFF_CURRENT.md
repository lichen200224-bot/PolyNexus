# Current Handoff

## Task
First Vertical Slice

## Status
FVS-01 DOMAIN / EXECUTION SKELETON IMPLEMENTED; VALIDATION BLOCKED BY PYTHON LAUNCHER

## Active Writer
Codex — initial architecture/core bootstrap

## Starting Branch
feature/first-vertical-slice

## Goal
Deliver the first real PolyNexus end-to-end product path:

Project
→ Review Task
→ ContextPackage
→ WorkflowDefinition
→ Reference/Mock Runtime
→ Run Supervisor
→ Finding + Evidence
→ Persist
→ Result
→ Reload History

## Confirmed Baseline
- ADR-001 through ADR-010 frozen.
- Windows development environment accepted.
- OpenCode onboarding PASS.
- Codex onboarding PASS.
- Antigravity onboarding PASS.
- Git backup available at D:\GitBackup\PolyNexus_Backup.git.

## Tool Assignment

### Codex
First writer:
- domain boundaries
- run supervisor
- workflow execution contracts
- evidence/context/artifact integration boundaries

### OpenCode
Second writer:
- persistence implementation
- API wiring
- tests
- routine integration work

### Antigravity
Milestone verifier:
- UI/E2E only after vertical slice becomes runnable

## FVS-01 Update

### Goal
Implement the minimum Domain / Execution Skeleton for Project, Task, Run, Artifact, ContextPackage, Evidence, Finding, normalized Run lifecycle, Runtime Adapter boundary, and Workflow execution boundary.

### Changed files
- `services/core/src/polynexus_core/domain/enums.py`
- `services/core/src/polynexus_core/domain/models.py`
- `services/core/src/polynexus_core/runtime/contracts.py`
- `services/core/src/polynexus_core/runtime/reference.py`
- `services/core/src/polynexus_core/runtime/supervisor.py`
- `services/core/src/polynexus_core/workflows/models.py`
- `services/core/src/polynexus_core/workflows/execution.py`
- `services/core/src/polynexus_core/workflows/loader.py`
- `services/core/tests/test_domain_models.py`
- `services/core/tests/test_runtime_skeleton.py`
- `services/core/tests/test_workflow_loader.py`

### Implemented
- Stdlib-only Domain dataclasses with stable IDs and structured ContextPackage references.
- Reference in-memory RuntimeAdapter only; no Codex/OpenCode runtime integration.
- Core-owned RunSupervisor with normalized start/collect/cancel lifecycle and cleanup verification.
- Canonical WorkflowDefinition normalization while preserving existing raw loader behavior.
- Explicit RUNTIME_EVIDENCE separation from AI_OPINION and tests for evidence/status values.

### Tests and validation
- `git diff --check`: PASS, exit code 0.
- `services/core/tests/test_domain_models.py`, `test_runtime_skeleton.py`, `test_workflow_loader.py` via `.venv` pytest: blocked by Unicode workspace process launch, exit code 1.
- `scripts/test_core.ps1`: blocked when launching `.venv\Scripts\python.exe`, exit code 101.
- `scripts/preflight.ps1`: baseline validator launch blocked by the same issue; wrapper exit code 1, inner Python launch exit code 101.

### Known blocker
The existing `.venv\Scripts\python.exe` cannot be launched from the current Codex Desktop sandbox because the workspace path contains Chinese characters and the process launcher converts it to `????`. No dependency or environment setting was changed. Current pytest and baseline validation results remain UNVERIFIED.

### Next
Rerun `scripts/test_core.ps1` and `scripts/preflight.ps1` from an environment that can launch the existing project Python runtime. After deterministic validation passes, continue with WP-02 persistence/repository work.

## Restrictions
- Do not change ADR-001–010 without a new ADR and explicit human approval.
- Do not add Plugin/MCP infrastructure.
- Do not add unrelated V1 features.
- Do not allow multiple active writers.
- Do not claim PASS without current deterministic evidence.
