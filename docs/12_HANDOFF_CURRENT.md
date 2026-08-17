# Current Handoff

TASK: Development Baseline v1.0 → First Vertical Slice
OWNER: Next Active Writer (recommended Codex for architecture/core bootstrap)
BRANCH: feature/first-vertical-slice
PRIMARY_WORKSPACE: D:\AI學習教材\PolyNexus

## Goal
Validate the frozen repository scaffold, then implement the minimum real path:
`Project → Review Task → Reference/Mock Runtime → Finding/Evidence → Result → durable history`.

## Completed
- Scope D01–D10 confirmed.
- ADR-001～010 confirmed.
- PRD/SA/SD promoted to Development Baseline v1.0.
- Shared `.agents/skills` / Antigravity rules / token-aware handoff rules prepared.
- Initial React/FastAPI/MV3/workflow schema scaffold prepared.
- Git safety model = same repo, sequential tools, Single Active Writer.

## Required First Actions
1. `git status --short --branch`
2. Run `scripts/preflight.ps1`.
3. Run `scripts/test_core.ps1`.
4. Read only PRD/SA/SD sections directly relevant to First Vertical Slice.
5. Do not implement Web AI / Local AI / all workflow templates before the slice works.

## Acceptance for Next Handoff
- Core health test PASS with actual exit code 0.
- Workflow schema baseline test PASS.
- First Project/Review domain path persisted through Repository boundary.
- Evidence object cannot be confused with AI opinion.
- Updated `HANDOFF_CURRENT.md` lists changed files, tests, actual exit codes, known issues.

## Do Not Change Without ADR/Decision
- D01–D10.
- ADR-001～010.
- Discuss/Review/Validate top-level modes.
- Evidence truth/provenance rules.
- Plugin-ready/declarative workflow foundations.
- V1 LOCAL_PERSONAL focus and 2026-10-31 acceptance target.
