# 來源權威與引用索引

所有 commit/blob pin 見 [SOURCE_LOCK](SOURCE_LOCK.json)。SOURCE_LOCK 是準備時觀察，後續 ref 漂移須重新核對，不可悄悄以新tip替換 frozen來源。

## 1. 來源代號

- BASE：產品保留錨點的 Scope/PRD/SA/SD/Acceptance/Roadmap/Known Limitations；目前仍可由本repo原路徑閱讀。初版完整功能未被本包縮減。
- FORMAL：[擴充PRD](references/formal/01_PRD.md)、[擴充SA](references/formal/02_SA.md)、[擴充SD](references/formal/03_SD.md)，來源43aa27c8。其修改是正式文義，舊NOT_IMPLEMENTED/state不代表現在整庫實作狀態。
- FROZEN：[Architecture Freeze Record](references/frozen/POLYNEXUS_TRACK_A_V1_ARCHITECTURE_FREEZE_RECORD.md) §3 I-01–I-23及§4–11；[REV1](references/frozen/GATE_2_CONTRACT_ARCHITECTURE_PACKAGE_REV1.md) 包含canonical bytes、Golden expected IDs、commands、four-axis ownership、Human protocol與P0/N1詳細規範。原REV1標Freeze HOLD的歷史文字已被Freeze Record明確覆蓋；原bytes保留。
- WORK：[S0/W1–W6/B01 Work Packages](references/frozen/POLYNEXUS_TRACK_A_IMPLEMENTATION_WORK_PACKAGES.md)。既有範圍/正負測試/18欄位繼承；新的批次授權只重編排流程，不弱化criteria。
- ADR-ID-013：[WorkGeneration/Candidate/Acceptance](references/formal/34_ADR_013_WORK_GENERATION_CANDIDATE_AND_ACCEPTANCE.md)。
- D11-A-LP：[Human-only Protocol](references/formal/35_D11_A_LP_LOCAL_HUMAN_DECISION_PROTOCOL.md)。
- ADR-MOD-013：本repo `docs/34_ADR_013_MODULAR_CORE_EXTENSION_ARCHITECTURE.md`，來源f0c0b986，static module/core boundary。
- ADR-014：本repo `docs/35_ADR_014_DURABLE_EVENT_ORDERING_AND_CANCELLATION_CLEANUP.md`，事件排序/cleanup，不與D11-A-LP混為同文件。
- MCF：[external runtime contract](references/MCF-02-EXTERNAL-RUNTIME-MODULE-CONTRACT.md)來源b317e5d7；candidate030890b3的修復說明/實作另作未接受來源。不能把 proposal control block 或作者後續報告單獨當Human授權證據。
- GOV：[跨機治理](references/36_POLYNEXUS_CROSS_MACHINE_GOVERNANCE.md)來源1ea8ce3d；只繼承可攜性/checkpoint語意，不繼承其過期產品routing。

## 2. 接受與前身的精確位置

Track A TA-F4：`43aa27c8b7a1b950645acc0d41234ec7679b653e:docs/reviews/TA-F4/acceptance-receipt.json`、`docs/reviews/TA-F4/human-decision.md`、`docs/handoffs/TA-F4/accepted.md`；reviewed result為f62d3ec1d0afa72191d1a63ae43f3bfb4089d296。接受只涵蓋formal sync verification，非S0/產品實作。

MCF修復：`030890b30160f1063ac2cef1d36705a9ea70bddb:docs/tasks/MCF-02-I01-REPAIR-REVIEW-NOTES.md`，historical NEED_FIX為18fab2b092911d9dd1f95eccda29b52dfaedff7d。新候選保留舊lineage；fixture測試不證明live支援。

查閱以上未複製檔時用 `git show <exact-commit>:<path>`，必要時先從canonical remote取得該exact ref；不能在錯branch找不到檔就重造。GitHub亦可按 `/blob/<exact-commit>/<path>` 回讀。

## 3. 原件保全與閉包

references內的來源使用原Git blob，不改寫歷史或Golden。直接比對SOURCE_LOCK的blob SHA即可確認byte identity；不能把重新算出的產品Golden expected IDs取代原值。

原件中指向更早proposal、舊tooling或外部研究的歷史連結不自動提升為本包normative dependency。實作必須依Freeze/REV1/F3正式語意；若遇到normative欄位仍需要未取得文件，source closure失敗並阻擋該設計，不從摘要推測。現有來源讀取與本輪完整獨立審查是不同事；Fresh Reviewer仍须逐條核對REQUIREMENTS與source。

## 4. 衝突優先序

當前Human明示範圍 > frozen invariants/Golden與有範圍的後續正式決議 > 經接受的契約增量 > 原初版範圍 > 本次實作設計草稿。較新的日期不能單獨覆蓋高優先權；程序授權不能改產品信任語意；任何真正semantic collision寫入DECISION_AND_GAP_REGISTER，不挑方便的一份照做。
