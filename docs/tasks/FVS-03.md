# FVS-03 — CORE API FOUNDATION: PROJECT / TASK / RUN

## 1. Status

PLANNED

本 Task 建立在 FVS-02 checkpoint `1c872de` 之上，預期仍使用 `feature/first-vertical-slice`。

## 2. Background

FVS-01 已完成 Domain、Workflow loader、Reference/Mock RuntimeAdapter 與 Core-owned RunSupervisor 的最小骨架。FVS-02 已完成 SQLite/Alembic persistence、Repository boundary、Run event/history reload 與 migration lifecycle。

目前 Core API 只有既有 `/api/v1/health`；Web scaffold 也明確等待 project persistence/API。First Vertical Slice 計畫中的 WP-03/WP-04 能力已由 FVS-01 提供，因此下一個最小且可獨立驗收的缺口是 WP-05：將 Project / Task / Run 的持久化能力接到薄 REST API boundary，供後續 UI 與整合 Task 使用。

## 3. Goal

在不執行 Runtime 的前提下，建立受 authenticated loopback boundary 保護、使用現有 Repository 的 `/api/v1` Project / Task / Run 建立與查詢 API，並以 temporary database 證明資料可在新 session reload。

## 4. Dependencies

- Branch：`feature/first-vertical-slice`
- Previous checkpoint：`1c872de feat(core): add FVS-02 persistence layer`
- FVS-01 Domain / workflow / runtime contracts and tests
- FVS-02 SQLAlchemy models、Repository ABC/implementation、Alembic initial migration
- `docs/20_FIRST_VERTICAL_SLICE_PLAN.md` WP-05 API 定義
- ADR-002、ADR-004、ADR-007、ADR-008、ADR-010
- Task-specific skills：`polynexus-implement`；若碰到 API/auth contract 或 architecture boundary，先遵循 `polynexus-architecture-gate`

## 5. Active Writer

OpenCode

## 6. Reviewer

Codex

## 7. In Scope

1. 保留現有 `GET /api/v1/health` 行為，並將 API router 納入可測試的 app/dependency composition。
2. 建立 Project endpoints：
   - `POST /api/v1/projects`：接受 `name` 與 optional `description`，回傳 `201` 與建立後 Project。
   - `GET /api/v1/projects`：回傳 `200` 與 Project collection。
   - `GET /api/v1/projects/{project_id}`：回傳 `200`；不存在時 `404`。
3. 建立 Task endpoints：
   - `POST /api/v1/projects/{project_id}/tasks`：接受 `title`、`workflow_id`、`workflow_version`、optional `mode`、optional `context_package_id`，回傳 `201` 與建立後 Task。
   - `GET /api/v1/projects/{project_id}/tasks`：回傳該 Project 的 Task collection。
   - `GET /api/v1/tasks/{task_id}`：回傳 `200`；不存在時 `404`。
   - 建立 Task 前必須驗證 parent Project 存在；若提供 `context_package_id`，必須驗證 ContextPackage 存在且屬於同一 Project。
4. 建立 Run persistence/query endpoints：
   - `POST /api/v1/tasks/{task_id}/runs`：接受必要 `context_package_id`，驗證 Task 與 ContextPackage 關聯後，依 Task 的 `workflow_id` / `workflow_version` 建立 Run。
   - 新建 Run 必須保持 `CREATED`、`ExecutionTarget.LOCAL`、`ResumeMode.NONE`，回傳 `201`；不得在此 endpoint 啟動 Runtime。
   - `GET /api/v1/tasks/{task_id}/runs`：回傳該 Task 的 Run collection。
   - `GET /api/v1/runs/{run_id}`：回傳 Run、已持久化 events 與 optional result；不存在時 `404`。
5. API layer 使用 Pydantic request/response DTO，將 Domain dataclass 與 Repository boundary 隔離；route handler 不得直接操作 ORM model 或 raw SQL。
6. 建立明確的 database/session dependency injection，使 API tests 使用 temporary SQLite database，且不污染 global test state。
7. 所有非 health 的 API route 必須經過 authenticated loopback caller dependency。可以使用明確的 test-only dependency override 證明 route 行為；production default 必須 fail closed。不得把 token、credential 或 Secret value 寫入 Domain、Event、Evidence、DB、log 或 response。
8. 對 invalid payload、Domain validation failure、parent/child 不一致、unknown ID 與未授權 caller 提供可測試的 `422`、`404`、`401/403` 行為；錯誤 response 不洩漏 secret 或內部 credential。

## 8. Out of Scope

- `RunSupervisor.start/collect/cancel/resume` 或任何 Reference Runtime execution。
- Workflow execution、Finding/Evidence orchestration、Run Result 產生邏輯。
- WebSocket live events、background task、queue、scheduler 或 process manager。
- 新增資料表、改寫既有 migration、資料 migration 或 schema redesign。
- SecretStore provider、pairing protocol、token format、caller identity policy 的新決策；若沒有既有可用 boundary，依第 14 節升級。
- React UI、Browser Companion、Chrome MV3、DOM automation、vendor adapter 或真實 Web AI flow。
- Project/Task/Run update/delete、pagination、search、authorization role matrix、multi-user/remote deployment。
- 新增 production dependency、修改 ADR-001～010 或將任何 FUTURE scope 提前納入 V1。

## 9. Architecture Constraints

### ADR impact

- ADR-002：使用既有 FastAPI/asyncio、SQLAlchemy/Alembic/SQLite stack；Domain 不得依賴 FastAPI 或 SQLAlchemy。
- ADR-004：API 是 UI/Core boundary；UI/API 不直接擁有 DB/process/vendor state，durable persistence 不依賴 WebSocket。
- ADR-007：本 Task 只能建立 `CREATED` Run record；Runtime lifecycle 仍由 Core-owned RunSupervisor 管理，不能從 route 直接呼叫 vendor/process。
- ADR-008：沿用 SQLite metadata/state/index 與 reference-based ContextPackage；不把 artifact content 或 prompt blob 寫入 SQLite。
- ADR-010：非 health API 必須有 authenticated loopback boundary；secret value 不得進 Domain、Event Ledger、Evidence、Artifact、log、export、handoff 或 Git。

### Boundary rules

- API route 只處理 HTTP DTO、輸入驗證、dependency wiring、錯誤映射與 Repository/service 呼叫。
- Repository implementation 是 persistence boundary；不得在 route 散落 SQL、ORM mapping 或 transaction workaround。
- `create_app()` 的既有無參數呼叫必須維持相容；若增加 optional app/session provider，既有 health test 不得失效。
- Production server 維持 loopback bind `127.0.0.1`；本 Task 不得新增 remote bind 或未驗證的 fallback。
- API 不得製造或宣稱 `AI_OPINION`、`TOOL_EVIDENCE`、Finding、Result 等尚未執行的證據。

## 10. Implementation Guidance

1. 先檢查 branch/status，讀取本文件、`AGENTS.md`、Project State、Current Handoff 與 `polynexus-implement`；只讀取實作需要的 API、Domain、persistence source/test。
2. 優先沿用現有 Repository ABC 與 `database` session lifecycle。可調整 app factory/dependency composition，但不要把 global engine 初始化藏入 route handler，也不要為測試共享實體 `poly.db`。
3. 可以新增 API router、schema、dependency 或薄 service module；檔名與內部拆分可由 Writer 決定，但 public route contract、狀態碼、security gate 與 scope 不可自行改動。
4. API test 應以 Alembic `upgrade head` 建立 temporary database，或明確證明其 fixture 使用與 production 相同的 schema lifecycle；測試後清理 temporary resource，不修改使用者資料庫。
5. Relationship validation 必須在寫入前完成：Project→Task、Project→ContextPackage、Task→Run/ContextPackage。不得接受跨 Project 的 reference。
6. Auth implementation 只可沿用現有 contract 或建立可注入的 boundary seam。若必須選擇新的 bearer token、pairing、SecretStore 或 caller policy，立即停止並回報 `ARCHITECTURE_DECISION_REQUIRED`，不可用 `allow all` 或 hard-coded production credential 繞過。
7. 不要為了讓測試通過而放寬 validation、吞 exception、移除 auth dependency、跳過 migration 或直接改測試期待。

## 11. Required Deterministic Tests

Writer 必須實際執行可用的命令，並記錄完整 command、摘要結果與 actual exit code；舊 handoff 或舊 screenshot 不得代替本輪 evidence。

### Targeted tests

- `C:\temp_pn_venv2\Scripts\python.exe -m pytest -q services\core\tests\test_api.py services\core\tests\test_health.py`
- 若測試檔案採不同命名，需在 Handoff 列出實際等價 command。

### Persistence/API regression

- `C:\temp_pn_venv2\Scripts\python.exe -m pytest -q services\core\tests\test_persistence.py services\core\tests\test_api.py services\core\tests\test_health.py`
- `C:\temp_pn_venv2\Scripts\python.exe -m pytest -q services\core`

### Project preflight / baseline

- `C:\temp_pn_venv2\Scripts\python.exe .\scripts\validate_baseline.py`
- `.\scripts\preflight.ps1`
- `.\scripts\test_core.ps1`

若 bundled `.venv` 受 Unicode path 問題阻擋，必須記錄 `BLOCKED_BY_EXECUTION_ENVIRONMENT`、實際 exit code，並補跑上列可用的 temp-venv 命令；不得把 blocked 當 PASS。

### Task-specific verification

- fresh temporary DB + Alembic head：建立 Project → reload session 查詢 Project。
- 建立同 Project Task → list/get → reload session 查詢 Task。
- 建立 ContextPackage fixture 後建立 Run；驗證 Run 是 `CREATED`、無 Runtime side effect，並可由新 session 讀回 events/result 欄位。
- 驗證 unknown Project/Task/Run、跨 Project ContextPackage、空 name/title、無效 workflow version 及未授權 caller 的 deterministic status code。
- 靜態檢查 API route 未 import/操作 ORM model 或 raw SQL，沒有 hard-coded secret/token，沒有新增 migration 或無關 scope 檔案。
- `git diff --check`

## 12. Acceptance Criteria

1. `GET /api/v1/health` 的既有 test 與 response contract 維持通過。
2. Project、Task、Run endpoints 的 route、request fields、response fields、status codes 與第 7 節一致，並有 targeted tests 證明。
3. API 寫入只經由現有 Repository/persistence boundary；API tests 不需要直接依賴 ORM implementation details。
4. 在 fresh temporary DB 上，Project、Task、Run 的 create/query 結果可在關閉並重新建立 database session 後讀回。
5. Run create 不呼叫 RuntimeAdapter/RunSupervisor execution；新 Run 狀態確實為 `CREATED`，沒有偽造 Finding/Evidence/Result。
6. 非 health route 在缺少 authenticated caller 時 fail closed；test-only auth override 必須是明確注入，不能變成 production default。
7. 不存在跨 Project ContextPackage reference；invalid input、unknown ID、unauthorized caller 的錯誤行為有 deterministic assertions。
8. 不新增 schema/migration、vendor integration、UI、WebSocket、secret storage 或其他 Out of Scope 行為。
9. 所有 required deterministic tests 若可執行均 actual exit code `0`；若因 execution environment 無法執行，Handoff 必須標記 `BLOCKED_BY_EXECUTION_ENVIRONMENT` 並提供 Human 精確補跑命令。
10. Writer 更新 `docs/12_HANDOFF_CURRENT.md`，完整列出 files、test counts、actual exit codes、ADR impact、scope deviation、known limitations 與 reviewer attention points，最後狀態只能是 `READY_FOR_CODEX_ACCEPTANCE`。

## 13. Antigravity Requirement

ANTIGRAVITY_NOT_REQUIRED

理由：本 Task 是 backend/API、persistence boundary 與 deterministic HTTP tests；不包含 UI、Browser Companion、Chrome MV3、DOM、CSP、真實 user journey 或 release/milestone hard gate。Real browser 不會提供比 TestClient、temporary DB、static review 更有效的本 Task evidence。Antigravity 保留給 FVS-06 UI 或 FVS-07 milestone integration/E2E。

## 14. Escalation Conditions

Writer 必須停止實作並回報 `NEED_ESCALATION` 或 `ARCHITECTURE_DECISION_REQUIRED`，不得自行取捨，若遇到：

- 需要修改 ADR-001～010，或新增 API contract 與既有 ADR/SD/First Slice 定義衝突。
- 需要改變 Domain dataclass、Repository ABC、Run lifecycle、Evidence semantics 或 migration schema 才能完成。
- 需要選擇新的 token/pairing/SecretStore/caller identity/data-routing policy，或無法在既有 security boundary 下安全提供 endpoint。
- 需要把 API routes 做成未驗證 public/remote endpoint，或需要把 secret value 放入 request、DB、log、event、response、fixture、handoff 或 Git。
- 需要新增 infrastructure subsystem、production dependency、WebSocket、queue、scheduler、browser/vendor integration。
- 同一 deterministic root cause 自行修正兩輪後仍失敗。
- Unicode path、Python runtime、dependency、sandbox 或其他 environment/tool blocker 使 required verification 無法完成。
- 任何 scope conflict、需要修改既有測試期待、跳過測試、吞 exception 或降低 security/validation 才能通過。

## 15. Git Rules

Writer：

- 不 `git add`
- 不 `git commit`
- 不 `git push`
- 不 `git reset`
- 不 `git restore`
- 不 `git clean`
- 不切換 branch
- 只在目前 `feature/first-vertical-slice` working tree 進行本 Task；保留他人既有變更並立即回報重疊衝突。

## 16. Definition of Done

- API implementation completed within In Scope。
- Targeted、relevant regression、preflight/baseline 與 task-specific verification 已執行，或明確記錄 execution blocker。
- 每個 test command 都有 actual result、test count/摘要與 exit code。
- API/auth/persistence/runtime boundary 與 ADR impact 已報告。
- Scope deviation、known limitation、remaining issue 與 reviewer attention points 已報告。
- `docs/12_HANDOFF_CURRENT.md` 已更新為本 Task delta。
- 最終狀態為 `READY_FOR_CODEX_ACCEPTANCE`；Writer 不得宣告 `VERIFIED PASS`，也不得建立 Git checkpoint。

## 17. Handoff Requirements

Writer final handoff 必須包含：

1. Modified / Added files
2. Implementation summary
3. Architecture / boundary summary
4. Tests executed
5. Actual test counts
6. Actual exit codes
7. Known limitations
8. Remaining issues
9. ADR impact
10. Scope deviation
11. Areas requiring Reviewer attention

最後只能輸出：

`READY_FOR_CODEX_ACCEPTANCE`
