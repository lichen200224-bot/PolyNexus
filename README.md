# PolyNexus

> Local-first Multi-AI Collaboration & Validation Workspace

版本：Development Baseline v1.0
日期：2026-08-17

PolyNexus Phase 1 的目標是交付可長期自行使用的 `LOCAL_PERSONAL` 多 AI 工作平台，不是只有 Framework。Workspace / Task / Discuss / Review / Validate / Council / Evidence / Workflow / Runtime / Web AI / Local AI 都必須有真實可操作垂直切片；後續再沿同一 Domain / Contract 演進 Personal Hub、部門／Team 與 Enterprise 能力。

## 已凍結技術基線

- UI：Browser-first local web，保留未來 Tauri wrapper 路徑。
- Core：Python + FastAPI + asyncio。
- Persistence：SQLAlchemy + Alembic + SQLite metadata；大型 Artifact 使用 filesystem。
- Frontend：React + TypeScript + Vite。
- UI/Core：REST + WebSocket；重要事件寫入 Durable Event Ledger。
- Test：pytest + Vitest + Playwright；Antigravity 用於真實 Browser/E2E 與獨立驗證。
- Browser Companion：Chrome MV3 thin companion + vendor-specific site drivers + authenticated loopback API。
- Runtime：Core-owned Run Supervisor；Adapter-owned vendor logic。
- Workflow：YAML authoring + JSON Schema validation + canonical internal model。
- Secrets：SecretRef + OS-backed SecretStore boundary；Secret value 不進普通 Domain、Git、Evidence、Export。

完整 ADR：`docs/18_ARCHITECTURE_DECISIONS.md`。

## 新 Session 必讀

1. `AGENTS.md`
2. `docs/11_PROJECT_STATE.md`
3. `docs/12_HANDOFF_CURRENT.md`
4. 與當前 Task 直接相關的規格/程式檔

不要讓 Agent 預先讀完整 `docs/`、完整 log 或完整 repo。

## Git / 三工具共同開發

同一個實體專案目錄由 Codex、OpenCode、Antigravity 依序使用；同一時間只有一個 Active Writer。Branch 以功能命名，不以 AI 名稱命名。

首次建立本機 Git：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_git.ps1
```

若使用已提供的 Git bundle，可直接 clone bundle，保留 Baseline commit。

## Scaffold 驗證

Core scaffold：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test_core.ps1
```

Preflight：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\preflight.ps1
```

目前 scaffold 只建立技術骨架與可驗證 health/workflow schema baseline；第一條正式 Product Vertical Slice 仍依 `docs/04_DEVELOPMENT_PLAN.md` 於 2026-09-06 前完成。
