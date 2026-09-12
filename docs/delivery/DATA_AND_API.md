# 資料、API、事件與遷移設計附錄

Status: PROPOSED_IMPLEMENTATION_MAPPING / NOT_IMPLEMENTED_BY_THIS_PREPARATION。以下是詳細設計草稿；API名稱與schema承載須在獨立設計審查確認，不能說目前server已提供。Frozen REV1定義canonical identities；表名與DTO不是第二份canonicalization規格。

## 1. Immutable與mutable資料分離

| Record | Key/relations | 核心欄位與約束 |
|---|---|---|
| work_generation | PK(task_id,generation_revision), FK Task | generation_revision>0；requirements/validation/context/input/base snapshot refs；predecessor同Task；control_revision；creation command；不重用revision |
| generation_writer_claim | UNIQUE(task_id,generation_revision) | writer_lineage_ref、first Run ref、ownership fence、claim/release facts；release不刪lineage或容許無關新writer |
| run_generation_link | UNIQUE(run_id), FK existing Run + generation | 新Run必須可驗證generation；legacy可缺但標LEGACY_UNBOUND，不以猜測補可信鏈 |
| workspace_record | internal workspace ref | repository reference、generation/Run、baseline、Git observations、fence、ownership/recovery facts；本機path只屬local locator |
| command_receipt | UNIQUE(principal_ref,command_id) | payload digest、exact target、operation ref、accepted/completed fact、bounded result；同key不同payload拒絕 |
| operation_intent | internal operation ref | target/fence/effect class、requested/observed/completed、causation、bounded error；Crash uncertainty不自動重做 |
| content_snapshot | SnapshotID from REV1 | manifest/profile/source refs/content availability；immutable；entry/path/mode/bytes規則完全採REV1 |
| changeset | ChangeSetID from REV1 | verified baseline/result snapshot IDs、Core-derived manifest；不可採caller diff作authority |
| candidate | CandidateID from REV1 | immutable ChangeSet＋RequirementSnapshot＋ValidationContractSnapshot；不含generation/Run於hash |
| candidate_publication | internal publication ref | CandidateID＋Task/generation/Run/lineage＋source facts；同Candidate重現仍保留獨立publication，不合併來源歷史 |
| evidence_set / verification | frozen EvidenceSetID/verification record | exact Candidate、contract/check IDs、requirements/applicability、outcome、validity、tool/runtime/env refs、artifact refs；新增set不改Candidate |
| human_decision_event | append-only decision/Acceptance ref | principal、Candidate/view、action、prior/replacement acceptance、server sequence/time、reason、protocol evidence；原event不得改寫 |
| security records | 專用store、非普通domain/export | pairing grant、bounded/revocable session、single-purpose challenge verifier；不保存raw bearer token於普通DB/log |

必要index：generation Task+revision、Run→generation、generation writer unique、Candidate publication scope、verification Candidate+contract+sequence、command idempotency、decision Candidate+sequence與prior/replacement refs。用transaction+FK/CHECK/UNIQUE保護，不只依Python檢查。複合FK要防cross-project/cross-task substitutions。

## 2. 身份與publication映射

REV1 §3.5 canonical bytes/profile/Golden Expected IDs原樣繼承，不在本附錄重定義JSON排序、path normalization、Unicode/mode/file-size上限。支援範圍、invalid/partial/collision判定依原規格。CandidateID相同不代表同一Run/generation；查詢接受與執行provenance時必須返回選定publication context，不能憑內容hash把不同工作的歷史折疊。

新的Evidence可以使既有Candidate重新驗證，不改其ID；Requirement/ValidationContract或source content改變，依REV1生成新Candidate。EvidenceSet本身immutable；新增/替代證據形成新set或新的verification record，不原地改過去結果。

## 3. Mutation DTO

共同request：`command_id`、exact `target`、`expected_revision`、typed `payload`。可選client correlation僅追蹤，不是principal。Server認證來源決定principal/role；body傳`human=true`或actor_id不授權。

共同response：`command_id`、`receipt_id`、exact target、accepted revision、operation ref（長操作）、bounded outcome/error、durable event cursor。HTTP accepted不等於工作完成。Command replay同principal/key/payload回相同receipt；不同payload 409。

Error envelope：`code`、safe message、correlation ref、retryability enum、human_action_required boolean、可安全提供的target ref。不能靠任意文字判斷retryability，不能回raw exception/secret/path dump。

## 4. Route草稿與行為

既有 `/api/v1/projects`、`tasks`、`runs`、context/output APIs保留。下列是提議新增/擴充的route contract；實作先做existing schema/consumer diff，不任意破壞舊呼叫者。所有mutation為POST並驗證auth/scope/revision。

| Route形狀 | Request目的 | Success | 主要拒絕 |
|---|---|---|---|
| tasks/{task_id}/inputs | 固定requirements/context/baseline與明選dirty input | 201 immutable input refs | 未選dirty/path escape/foreign refs |
| tasks/{task_id}/generations | Begin，expected task revision＋selected input refs | 201 generation ref/receipt | revision conflict、不可用input |
| tasks/{task_id}/generations/{generation}/retry | exact predecessor與selected input | 201新generation，idempotent replay原ref | ownership未釋放、cross-task |
| tasks/{task_id}/generations/{generation}/abort | exact generation＋control revision | 202 operation；安全停止後才完成 | stale target、不替換為latest |
| runs/{run_id}/execute | exact Run/generation＋revision | 202 launch intent/receipt | unbound/stale/第二lineage/policy不允許 |
| runs/{run_id}/cancel | exact Run | 202 cleanup operation或既有terminal receipt | 不取消其他Run/generation |
| tasks/{task_id}/generations/{generation}/publications | frozen outputs與quiescence證據refs | 201 publication/Candidate refs | aborted、dirty/drift、closure不完整 |
| candidates/{candidate_id}/verifications | exact validation contract/check profile | 202 verification operation | unknown contract、source不可取、無可信runner |
| candidates/{candidate_id}/view | GET exact content/requirement/evidence/eligibility視圖 | 200 view revision/digest | 缺closure、foreign scope |
| human/decision-challenges | Candidate/view/action/current revision | 201單用途challenge | 非Human、stale view、ineligible Accept |
| human/decisions | challenge＋nonce response/action/command | 201 append-only decision/receipt | replay、policy/evidence/view drift、wrong Origin |
| accepted/{acceptance_id}/open | exact Candidate及有效disposition | 202準備managed accepted copy | source hash/closure不符、不安全workspace |
| workspaces/{workspace_ref}/takeover | explicit Human取得ownership | 200 WorkingCopy ref/label | writer未知/未停止/fence mismatch |
| accepted/{acceptance_id}/exports | P0 exact package | 202 export operation | accepted closure缺漏、secret contamination |
| tasks/{task_id}/exports | N1明選scope | 202 selected-task package | 未選資料/跨scope/credential export |

400 malformed envelope；401 unauthenticated；403 denied principal/policy；404 unavailable/foreign-scoped object（避免洩露）；409 revision/lineage/idempotency/eligibility conflict；422 schema/unsupported canonical input；429 quota/resource bound；503 not-ready prerequisite。Typed code區分可重試與Human/architecture blocker；不把所有failure轉HTTP200+success。

## 5. Verification四軸

持久化 `requirement_level`(REQUIRED/OPTIONAL)、`applicability`(APPLICABLE/NOT_APPLICABLE/UNRESOLVED)、execution `outcome`、evidence `validity`，其實際enum vocabulary以REV1映射，不新增workflow verdict。N/A是有predicate/evidence支持的呈現，不是一個可以覆蓋required的PASS。

Mandatory eligibility = 所有適用required checks有符合contract且valid/fresh/exact-bound的成功證據；UNRESOLVED/缺證/stale/mismatch不得滿足。Optional skip保留原因但不自動FAIL；fatal policy或安全失效仍依其required gate阻擋。新增驗證不能清除既有Human Reject或憑空revoke歷史Accept。

## 6. Events與monitor

現有Run lifecycle保留ADR-014 sequence。Generation/operation/decision另用typed durable facts與resource revision，不把所有資訊塞RunEvent.reason。REST cursor是opaque server cursor，來源為穩定sequence，不是client timestamp；pagination/replay去重保留範圍。WebSocket後續只推live notification/event，disconnect後以REST/durable cursor補齊，不能丟terminal事實。

## 7. Migration與legacy

先列實際Alembic heads/schema與所有old consumer，從唯一當前head新增linear revision；不在文檔預占revision號、不重用0002/0003。Upgrade前backup與read-only relation audit；每條SQLite connection啟FK，不依檔名判dialect。

Additive tables/nullable legacy link先建立；有deterministic authority才能backfill。沒有可信generation、candidate或Human principal的舊記錄保持可讀、LEGACY_UNBOUND/UNVERIFIED並保留原accepted歷史標籤的範圍，不賦予新A-LP權限。RuntimeBinding insert-once與舊Run身份不變。

測試新DB、代表性舊DB、dangling FK、重複資料、interrupt at each migration step、reopen、backup restore與原content hash。無法lossless downgrade的部分明確拒絕並走tested restore；不擅自drop已接受歷史或repair真實使用者DB。API新字段按相容策略漸進，舊資料不能因新NOT NULL要求導致整庫無法開啟。

## 8. PN-078 Assurance 與 PN-038 metric contract

[ASSURANCE_CONTRACT §2–4](ASSURANCE_CONTRACT.md#data-api)是本附錄的Assurance設計延伸：mode/profile隨固定input保存，Status由Core對exact target/contract衍生，不接受caller寫入；與verification四軸、runtime maturity及Human disposition分欄。未知/legacy/stale依該契約拒絕或明示不可判定，不回填可信狀態。

[§5 metric contract](ASSURANCE_CONTRACT.md#metric)保留human override的受限遙測含義：從合法可歸因audit facts單向衍生、source_event_id去重，coverage不足為UNKNOWN。metric query/recording不能建立或改寫Human decision、eligibility/outcome，也不存在Override Accept。[§6](ASSURANCE_CONTRACT.md#tests)的AT-038-MN02驗證這項無副作用邊界。
