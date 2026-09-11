# BASELINE-DEBT-01 — Deterministic Lifecycle Ordering and Timeout Cleanup

- Priority: `P1`
- Status: `SCOPE_PROPOSED / IMPLEMENTATION_NOT_STARTED`
- Created by Human routing: 2026-09-12, `MCF01_DECISION=ACCEPT_WITH_PRE_EXISTING_BASELINE_DEBT`.
- Predecessor/source checkpoint: `96ae53537e5501f1ef374182e7e1966b921a7883` (MCF-01 committed/pushed, remote SHA and clean clone verified).
- Source task: [ARCH-MODULAR-CORE-01](ARCH-MODULAR-CORE-01.md).
- Writer: to be assigned after start/scope gate; Reviewer: fresh independent Codex context (`Writer != Reviewer`).
- 此文件建立獨立追蹤與實作 proposal；本次 Git proposal 不開始 debt implementation，也不預先授權 schema/migration/public contract 變更。

## Evidence and scope

Independent review task `ARCH-MODULAR-CORE-01-INDEPENDENT-REVIEW` (`01a09292-b425-7570-a0ab-989365d9282e`) 確認 Writer 指定的 26 個 failure cases 均可在 baseline 重現；candidate-only=0、baseline-only=0。Reviewer 完整 observed union 為 30 個共同案例（另含事件排序及 reviewer temp-path isolation cases），不得把 30 與原 26-case claim 混淆。

Raw evidence references: `artifacts/verification/mcf01-20260912/baseline-failures-command.json` 提供 26-case nodeids；Reviewer task workspace 的 `mcf01-independent/*.xml` 提供獨立結果。開始前必須核對實際檔案與 exact SHA；不可僅採用摘要。

### A. Durable event / lifecycle deterministic total ordering

Evidence anchors: `services/core/src/polynexus_core/persistence/repository.py` 的 Run/event read paths 使用 `occurred_at, id`；`domain/models.py` 的 RunEvent 與 transition；`persistence/models.py` 的 RunEventRow。同時間或粗粒度 timestamp 下，random ID 排序不能保證 lifecycle 因果順序。

Required outcome:

1. 明確定義 Run 範圍內 durable total ordering 的 invariant，涵蓋 append、get/list/query、reopen/restart、同 timestamp、多 event transaction 與 concurrent append 的相容行為。
2. 保留 Task/Run identity、RunState、事件時間事實、immutable RuntimeBindingSnapshot 與既有 lifecycle ownership；不得為了排序改寫歷史 timestamp 或推造 execution facts。
3. 強制 equal timestamps、逆向 ID ordering 等 adversarial fixtures，驗證 CREATED/STARTING/RUNNING/terminal 順序與 API/persistence/council 一致。
4. 若最小正確解需要新 persisted sequence、schema/migration、legacy backfill 或 public compatibility 變更，先提出精確 contract、legacy ambiguity policy、upgrade/rollback/restore 與驗證計畫，等待 Human Architecture Gate；此 proposal 不预先選定/授權該方案。
5. 不得僅修改 assertion 為 unordered comparison、加入重試，或依 RunState sorting 重建沒有證據的歷史。

### B. Timeout / cleanup deterministic stability

Evidence anchors: `runtime/supervisor.py` 的 `_invoke` / timeout / shared cleanup 邊界，以及 `tests/test_wp24_resource_guards.py` 將 `_DEFAULT_OPERATION_TIMEOUT_SECONDS` 設為 0.01 的 cases。

Required outcome:

1. 分離被刻意阻塞的 operation 與 setup/scheduling 時間，用明確 synchronization、controlled awaitable 或最小可測 clock/deadline seam 驗證指定邊界。
2. 驗證 timeout → cancel/terminate → cleanup → cleanup verification → truthful final state，成功才標 TIMED_OUT/CANCELLED，失敗依合法轉移 fail closed（含 ORPHANED），不得產生錯誤 PASS evidence。
3. 驗證外層 cancellation、cleanup timeout/exception、未停止 resource、狀態不符、無 fabricated result 與 sanitized error；保留現有 RuntimeAdapter 和 RunSupervisor ownership。
4. 不得僅提高 sleep/timeout/retry 數值掩蓋；如認為 timeout 數值本身是正確 contract，須提供可驗證理由與明確 contract decision。

## Proposed affected files (not an approved implementation allowlist)

先由 root-cause 證據縮小 exact allowlist；不是要求修改以下每個檔案：

- `services/core/src/polynexus_core/persistence/repository.py`
- `services/core/src/polynexus_core/domain/models.py`
- `services/core/src/polynexus_core/runtime/supervisor.py`
- `services/core/tests/test_persistence.py`
- `services/core/tests/test_g14_runtime_reconciliation.py`
- `services/core/tests/test_wp07_integration.py`
- `services/core/tests/test_wp09_execution_api.py`
- `services/core/tests/test_wp09_query_api.py`
- `services/core/tests/test_wp12_council.py`
- `services/core/tests/test_wp14b_runtime_binding.py`
- `services/core/tests/test_wp24_resource_guards.py`
- Focused debt test（如必要）：`services/core/tests/test_baseline_debt_01.py`
- 本 task document、必要 known-limitations delta、本 task evidence。

`persistence/models.py`、Alembic migration、任何 persisted/public contract 調整只可先 read/design；必須另過上述 Architecture Gate 才能納入 implementation allowlist。

## Start and verification gates

- 從 Human-approved MCF-01 checkpoint `96ae53537e5501f1ef374182e7e1966b921a7883` 開始，記錄 exact HEAD、branch、remote、working/staged state，核對 predecessor ancestry；本次僅同步前置 checkpoint，implementation remains NOT_STARTED。
- 使用隔離 implementation lane，保護其他未提交修改；先建立最小 failing repro，再修根因。
- Focused deterministic repro → 26-case debt matrix（按 testcase identity + failure semantics）→ affected persistence/lifecycle/council/API/resource regressions → MCF-01 focused、runtime skeleton/binding、WP-14/15/16 → Full Core pytest → baseline/governance validators → git diff --check。
- 每條 command 記錄 actual exit code、passed/failed/errors/skipped、環境 blocker；同環境 baseline/candidate 比對只能協助診斷，不能沿用 MCF-01 例外取代本 task required suite 成功。
- 必須證明 total ordering 與 cleanup semantics，不以一次綠燈取代契約證據。以 deterministic adversarial cases 為主；重跑如用於診斷要保留全部結果，不採 retry-until-green。
- 完成必須 required executable checks exit 0、兩項 root-cause acceptance evidence 齊全、無新增 regression，並通過 fresh independent review。Skipped/environment-blocked coverage 明列；如必要契約 coverage 仍缺漏，保持 NEED_ACTION，不宣稱 PASS。
- 本 task 不獲授權使用 `ACCEPT_WITH_PRE_EXISTING_BASELINE_DEBT` 例外。Human acceptance 與 Git promotion 另為 gates。

## Protected areas and routing

不得新增 vendor integration、dynamic plugins、新 workflow node、UI/public API redesign、secret subsystem、依賴變更，或修改 G30/WP-20/operator reports/score。MCF-01 extension source 與 manifest/runtime composition contract 預設保護；不順手重構。

本 task 完成並通過 Fresh Independent Review 前，不得開始 holaOS/OpenHands production integration、dynamic plugin platform、MCF-02 external-runtime integration，或任何 Module Architecture production-ready promotion。可文件規劃與 research，不可建立 production support claim。

Current truth: `G30=NEED_ACTION`; `WP-20=NOT COMPLETE`; `V1_BOUNDED_DEVELOPMENT_ACCEPTANCE_SCORE=95/100`; `OVERALL_PROJECT_COMPLETION=NOT_DEFINED`; BASELINE-DEBT-01 不加分。

## Next owner

Human 確認 scope/start gate → 指派單一 Writer → Fresh Independent Codex Reviewer → Human acceptance / separate Git Gate。本輪僅建檔追蹤，不派發實作、不自行啟動下一 task。
