# Development Preparation Profile v1.0.2

Date: 2026-08-17

## Purpose

Align the primary Windows development workspace to:

```text
D:\AI學習教材\PolyNexus
```

No product scope decision or ADR-001–010 changed.

## Changes

- Added local workspace profile documentation.
- Added a workspace-path verification script.
- Updated shared agent context with the canonical local path while explicitly forbidding product hard-coding.
- Prepared a Drive-D installer pack and a ZIP whose top-level folder is `PolyNexus`, so manual extraction to `D:\AI學習教材` lands at the intended path.

## Rule

The absolute path is an operational profile only. Core, adapters, workflows, tests and storage APIs remain portable and repository-relative/configuration-driven.
