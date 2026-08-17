---
name: polynexus-runtime-conformance
description: Use when implementing or validating a PolyNexus Runtime Adapter. Enforces normalized lifecycle, cancel/timeout cleanup, evidence, compatibility and truthful maturity.
---
# PolyNexus Runtime Conformance

1. Read ADR-007 and the Core Runtime Contract sections only.
2. Keep vendor-specific behavior inside the adapter; do not branch Core by provider name.
3. Implement/verify: health, readiness, capabilities, create/submit, stable ID, status, result, normalized error, timeout, cancel, resume mode, evidence/artifacts, cleanup, version info.
4. Cancel is not PASS until child/tool/process/resource cleanup is verified.
5. Timeout reuses cleanup semantics but records timeout reason/state.
6. Resume is NATIVE / MANAGED / NONE; never fake native resume.
7. Run targeted conformance tests and record actual exit codes.
8. Maturity cannot exceed the highest level justified by current evidence.
