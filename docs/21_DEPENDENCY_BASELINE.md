# Dependency Baseline

Date: 2026-08-17

Purpose: record the initial scaffold dependency floor. After the first successful install on the target Windows machine, commit actual lock files and update this document from verified local output.

## Frontend Baseline

- React 19.2.8
- React DOM 19.2.8
- Vite 8.2.0
- @vitejs/plugin-react 6.0.5
- TypeScript 7.0.2
- Vitest 4.1.10
- Node.js requirement: >=22.12.0 for this scaffold

Primary references used at baseline time:
- https://www.npmjs.com/package/react
- https://www.npmjs.com/package/react-dom
- https://www.npmjs.com/package/vite
- https://www.npmjs.com/package/@vitejs/plugin-react
- https://www.npmjs.com/package/typescript
- https://www.npmjs.com/package/vitest
- https://vite.dev/blog/announcing-vite8

## Core Baseline

The generated scaffold was executed with these versions in the generation environment:
- FastAPI 0.128.2
- Uvicorn 0.48.0
- Pydantic 2.13.4
- SQLAlchemy 2.0.50
- Alembic 1.18.4
- PyYAML 6.0.3
- jsonschema 4.26.0
- pytest 9.0.2
- httpx 0.28.1

These are initial exact pins for reproducibility of the baseline scaffold, not a promise that they remain the newest packages. Upgrade only through a deliberate dependency update task with tests.

## Lock-file Rule

- `apps/web/package-lock.json`: generate on first successful `npm install`, review, then commit.
- Python: the current `pyproject.toml` exact pins are sufficient for baseline; add a lock workflow later only if it materially improves Windows reproducibility without expanding scope.
- Do not auto-upgrade dependencies during unrelated feature work.
