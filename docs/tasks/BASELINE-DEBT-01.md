# BASELINE-DEBT-01 — Deterministic Lifecycle Ordering and Timeout Cleanup

## Current closure — final accepted (2026-09-12)

```text
STATUS=FINAL_ACCEPTED
IMPLEMENTATION=COMPLETE
INDEPENDENT_REVIEW=PASS
PUBLICATION_REACCEPTANCE=PASS
BASELINE_DEBT_01=CLOSED

ACCEPTED_CANDIDATE_SHA=
aac597579ee6d369007343930d3a5b3ca7b929c5

MERGE_STATUS=
NOT_YET_AUTHORIZED

PROMOTION_STATUS=
PENDING_GOVERNANCE_TARGET_DECISION
```

- Functional baseline: `86d5939044c1d7ec2a991820f39287481ee9120f`.
- Publication-rejected Candidate: `180432d03f6d423bb3152c233fb4f0a5072868f5`;
  rejection was limited to CRLF working-tree hashes versus canonical Git blob
  hashes. Its publication-only successor passed fresh independent re-acceptance.
- Accepted evidence: focused + migration `47 passed / exit 0`; G14 single
  `1 passed / exit 0`, module `13 passed / exit 0`; Full Core
  `818 passed / 0 failed / 1 existing Windows symlink-policy skip / exit 0`;
  stability `5 rounds × 40 passed / 0 failed / exit 0`; canonical collection
  `771 -> 819`, delta `+48`, explained; publication freeze hashes `20/20`.
- `FINAL_ACCEPTANCE=GRANTED`; accepted functional Candidate is frozen.
- BASELINE-DEBT-01 adds no G24–G30 development points. Current project bounds
  remain `V1_BOUNDED_DEVELOPMENT_ACCEPTANCE_SCORE=95/100`,
  `OVERALL_PROJECT_COMPLETION=NOT_DEFINED`, `WP20=NOT_COMPLETE`, and
  `G30=NEED_ACTION`.
- No merge or promotion is authorized. Product source, tests, migration and
  ADR-014 semantics must not change in this state-sync.

## Historical superseded implementation gate — Human architecture approval (2026-09-12)

RESULT=SCOPE_EXPANSION_REQUIRED. ARCHITECTURE_DECISION=HUMAN_ACCEPTED /
IMPLEMENTATION_AUTHORIZED. ADR-014 implementation is present on the existing
isolated branch, start SHA `86d5939044c1d7ec2a991820f39287481ee9120f`.

- Persistence-only atomic sequence allocation, migration 0003 with rowid backfill,
  immutable metadata and downgrade; independent cleanup deadline and shielded
  cancellation; ExecutionService durable cancellation persistence implemented.
- Focused + migration: 47 passed, exit 0. Full Core: 810 passed, 5 failed, 1 skipped,
  exit 1. No Full Core PASS or deterministic stability PASS claimed.
- Scope blocker: `test_cp06_wp30_clean_install.py`,
  `test_g17_migration_restore_authority.py`, `test_wp23_backup_restore_migration.py`
  hard-code Alembic head=0002. These unauthorized test files remain untouched.
  Human must extend the test allowlist before those expectations can be updated.
- Three backup failures also require a basetemp within the permitted isolated
  temporary root. Production backup policy must remain intact.
- Original 26 debt cases, MCF-01 50, runtime/WP-14/15/16 pass within the full-run
  case evidence; the full command itself fails. Windows symlink policy skip is
  explicitly excluded from pass counts. Fixed 5-run acceptance is not executed.
- Detailed Writer handoff, commands/logs/JUnit:
  `artifacts/verification/baseline-debt-01/implementation/writer-handoff.md`.
  Prior red repro/evidence and all failed implementation attempts remain intact.
- ADR: `docs/35_ADR_014_DURABLE_EVENT_ORDERING_AND_CANCELLATION_CLEANUP.md`.
  No Domain/API/RunState/G30/WP-20/score changes, no staged commit or remote write.
- Immediate owner: Human scope decision. Eventual next role:
  FRESH_INDEPENDENT_CODEX_REVIEWER after all acceptance gates pass.

## Historical pre-approval Current Writer gate — 2026-09-12

`RESULT=ARCHITECTURE_GATE_REQUIRED`. This block supersedes the historical
proposal/start routing below for this task only. Human authorized the start and
named Codex as IMPLEMENTATION WRITER. No independent review is claimed.

- Start/HEAD: `86d5939044c1d7ec2a991820f39287481ee9120f` (terminal docs checkpoint;
  product checkpoint `96ae53537e5501f1ef374182e7e1966b921a7883` is its ancestor).
- Branch: `feature/baseline-debt-01-deterministic-lifecycle-cleanup`.
- Isolated worktree created from that exact SHA; original checkout preserved.
- Start gate PASS: direct remote SHA, explicit fetch, local HEAD, repaired remote
  tracking ref, clean state and ancestry verified. All required commands exited 0.
  Cause of missing tracking ref: `LOCAL_FETCH_REFSPEC_SCOPE`; persistent fetch
  config remains scoped to `architecture/modular-core-extension-contract`.
- Implementation: no production source/schema/migration change. Added 13 red
  acceptance repro cases; A implementation stops at the architecture boundary.
- Evidence: `artifacts/verification/baseline-debt-01/` (local, gitignored), including
  JUnit, logs, exact 26 nodeids, per-case failure semantics and Writer handoff.
- G30, WP-20 and score unchanged. No stage/commit/push/merge or self-review.

### CURRENT_SCHEMA

`RunEventRow` / Alembic `0001` declares `id VARCHAR(64) PRIMARY KEY`,
`run_id VARCHAR(64) NOT NULL REFERENCES runs(id)`, `from_state VARCHAR(32) NOT NULL`,
`to_state VARCHAR(32) NOT NULL`, `occurred_at DATETIME NOT NULL`, `reason TEXT NULL`.
No explicit append sequence, predecessor reference or per-run ordering constraint.
Domain event IDs use UUID4. Domain `Run.events` preserves Python append order only.

### ROOT_CAUSE

All four event hydration paths (`get`, `list_by_task`, `list_non_terminal`, and
`SqlRunEventRepository.list_by_run`) sort by `(occurred_at, id)`. Equal timestamp
ties therefore follow random identifier order rather than append/causal order.
`add` and `update` queue events in Python order; `append_event` flushes; standalone
event repository `add` queues a row. None persists an explicit logical ordinal.
The execution CAS protects the CREATED claim, not general event ordering.

### WHY_EXISTING_SCHEMA_CANNOT_PROVE_TOTAL_ORDER

The 12 adversarial tests preserve identical timestamps and reverse lexical IDs,
write STARTING → RUNNING → COMPLETED, commit, close/dispose, and read through a
new engine/session. Every write/read combination returns the terminal event first.
Council also emits same-state events (`_append_stage_event` path near line 1074),
so state-chain reconstruction cannot order arbitrary events. It is also forbidden
by the task. Implicit SQLite physical row identity is not a declared application
ordering contract and is not exported in these persisted fields. Depending on it,
rewriting timestamps, or encoding sequence into IDs would substitute an unapproved
persisted contract. Concurrent inserts have no per-run sequence allocation or
stale-writer check here; a SQLite transaction boundary alone does not encode that
order in the declared event fields. Multi-process adversarial execution remains
UNVERIFIED; no concurrency PASS is claimed.

### MINIMAL_PROPOSED_SCHEMA_CHANGE

Proposal only, NOT AUTHORIZED: add a positive non-null integer `sequence` to
`run_events` with `UNIQUE(run_id, sequence)`. Keep IDs, timestamps, lifecycle states,
Run identity and immutable binding unchanged. Sequence represents committed append
serialization within one Run, not wall-clock chronology or inferred historical
causality. Existing-event updates retain their ordinal; batches reserve consecutive
ordinals atomically in list order. All four readers use sequence as sole ordering
key. No API field addition is proposed; changed history ordering still requires
compatibility review, including existing timestamp/ID tie-breaker assertions.

Allocation must happen within a serialized SQLite write transaction before reading
the maximum sequence (for example an approved BEGIN IMMEDIATE transaction policy).
Do not use unguarded MAX+1. Concurrent writers must either serialize successfully
or receive a bounded, rollback-safe failure; duplicate event identity must not add
another event or renumber history. Exact transaction integration and busy handling
need design review across existing callers. Do not add a second lifecycle owner.

### LEGACY_DATA_POLICY / BACKFILL_POLICY

No automatic reconstruction from timestamp, random ID, physical row position,
state sorting, or reason text. Preserve existing facts exactly. Conservative
proposal: preflight blocks upgrade of every nonempty legacy event ledger unless
an independently verified external ordering manifest exists for every event of
each affected Run. Such a manifest is NOT currently available. Empty ledgers can
upgrade without backfill. Validate manifest completeness/uniqueness and retain its
provenance; perform any approved backfill atomically. Ambiguous history remains
unmodified on the old revision. This intentionally blocks upgrades of populated
databases until Human chooses a legacy policy; do not silently discard events.

### UPGRADE_PLAN

Approve ordering/legacy/transaction contract and exact allowlist first. Stop writers,
create and verify an existing supported backup, preflight the legacy ledger, then
run an Alembic migration on an isolated copy. Apply constraints and approved
backfill atomically; verify every existing field, binding and event count, reopen,
and validate history/API behavior. Promote only through separate authorized gates.
`create_all()` in repro tests is fixture setup, never production migration authority.

### DOWNGRADE/RESTORE_PLAN

Do not claim dropping sequence preserves append order. Prefer restoring the verified
pre-upgrade backup and compatible application version with writers stopped. Any
post-upgrade writes require a separately approved preservation/replay plan before
restore; no silent data loss. A schema-only downgrade would lose ordering evidence
and must be refused or explicitly approved as lossy. None was implemented/executed.

### AFFECTED_FILES / TEST_PLAN

Proposed future allowlist: persistence `models.py`, `repository.py`, a new Alembic
revision, transaction owners if serialization cannot be contained in repository,
and focused persistence/API/council/migration tests. Domain/API schemas remain
unchanged unless later demonstrated necessary and separately approved. ADR-004/007/008
compatibility addendum is proposed; frozen ADR text is untouched. V1 delivery timing
is gated by legacy policy and migration validation; no completion-date claim.

Required tests after approval: all four readers; add/update/append/event-repository;
same/coarse/backward timestamps; reverse IDs; same-state council events; multiple
batches; reopen/restart; duplicate/stale/concurrent writers with explicit barriers;
rollback and constraint failures; empty/verified/ambiguous legacy ledgers;
upgrade/backup/restore and existing-field/binding preservation. Then exact 26-case
matrix, affected suites, MCF-01/runtime/WP-14/15/16, Full Core and validators.

### ROOT_CAUSE_B investigation (not repaired)

`_invoke` starts its timeout after acquiring the semaphore, while `_execute_workflow`
wraps the entire setup in another timeout of the same duration. The shared 30-second
constant also bounds cancel, cleanup and status verification separately. Cleanup
bypasses the operation-count budget but not the timeout. Existing WP-24 tests reduce
all of these to 0.01 seconds; even setup `_delay()` yields through `sleep(0)`.
Both target cases in this run fail in `start()` before collect/cancel, proving they
do not isolate the intended deadline. Exact event-loop scheduling contributions are
not profiled; 0.01 is a test override, not the production deadline.

Cleanup requires cancel → cleanup truthy → exact post-cleanup status; mismatch or
ordinary exception fails closed to ORPHANED. The new Event-based outer-cancellation
test also proves a separate gap: cancellation reaches the blocked status operation,
but `collect` propagates CancelledError and leaves the Run RUNNING with no cleanup.
CancelledError is not handled by its ordinary Exception clauses. This proof concerns
the direct Supervisor path, not a claim that all service/council paths lack recovery.

Preferred next B work: a deadline seam scoped to the deliberately blocked call,
Event synchronization before expiry, and cancellation-safe bounded cleanup with
truthful terminal persistence. Cover cleanup timeout/exception, resource still active,
wrong status, repeated outer cancellation and sanitized/no-fabricated output.
No timeout increase, retry, weakened assertion, or production workaround was applied.

### Current evidence and stop

- Initial focused attempt: exit 1, 12 setup errors due to inaccessible default
  pytest temp root; retained in `ordering.log/xml`, not product failures.
- Fresh task-specific temp directory: exit 1, 12 ordering failures, no errors/skips.
- Event-controlled cancellation: exit 1, 1 failure (12 deselected), no errors/skips.
- Five fixed combined executions: each exit 1, 13 failed / 0 passed / 0 skipped;
  all five logs/XML retained. This proves reproducible defects, not repaired stability.
- Exact original 26 nodeids: exit 1, 11 passed / 15 failed / 0 skipped.
- Resource guards + runtime skeleton: exit 1, 21 passed / 2 failed / 0 skipped.
- Baseline validator: exit 0. Governance validator: exit 0.
- Full Core, broader affected suites, MCF-01 and WP-14/15/16: NOT_RUN at Architecture
  Gate; no acceptance or regression PASS claimed. No Windows symlink case was run.
- NEXT_REQUIRED_ROLE: `HUMAN_ARCHITECTURE_GATE`. Writer stops with red repro tests
  retained. Independent review and Git promotion remain separate future gates.

## Historical scope proposal (superseded start authorization above)

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
