# Source authority / 原件與引用索引

所有原commit、原branch與拷貝blob pin見[SOURCE_LOCK](SOURCE_LOCK.json)。來源的scope/接受狀態與本次review獨立，不因放進同tree就互相提升成熟度。

## 1. 原初版與正式增量

BASE：產品f0c0b986的原docs/00_SCOPE_BASELINE.md、01_PRD、02_SA、03_SD、08_ACCEPTANCE_STRATEGY、28_MASTER_DEVELOPMENT_ROADMAP與32_KNOWN_LIMITATIONS，仍在本repo原路徑且未覆寫。

FORMAL：43aa27c8的[Scope](references/formal/00_SCOPE_BASELINE.md)、[PRD](references/formal/01_PRD.md)、[SA](references/formal/02_SA.md)、[SD](references/formal/03_SD.md)、[Decision Log](references/formal/10_DECISION_LOG.md)、[ADR index](references/formal/18_ARCHITECTURE_DECISIONS.md)，皆按原blob保存。原文舊狀態不代表f0產品現狀；增量語意按接受範圍繼承。

TA-F4來源接受記錄：[receipt](references/formal/TA-F4/acceptance-receipt.json)、[Human decision](references/formal/TA-F4/human-decision.md)、[independent record](references/formal/TA-F4/independent-review.md)、[formal verification report](references/formal/TA-F4/FORMAL_SYNC_VERIFICATION_REPORT.md)。只證明來源所記formal sync acceptance，不是本次前置文件已獨立通過或S0已開工。

## 2. Frozen detailed authority

[Architecture Freeze Record](references/frozen/POLYNEXUS_TRACK_A_V1_ARCHITECTURE_FREEZE_RECORD.md)的I-01–I-23與批准範圍；[REV1完整契約](references/frozen/GATE_2_CONTRACT_ARCHITECTURE_PACKAGE_REV1.md)的canonical bytes/Golden/commands/ownership/Human/P0/N1；[Gate2 input](references/frozen/GATE_2_INPUT_BASELINE.md)；[formal change plan](references/frozen/POLYNEXUS_FORMAL_CONTRACT_ADR_CHANGE_PLAN.md)；[S0/W1–W6/B01 work packages](references/frozen/POLYNEXUS_TRACK_A_IMPLEMENTATION_WORK_PACKAGES.md)。來源fe2eb231，design-read baseline f34e6b29。

REV1的歷史Freeze HOLD已由Freeze Record記錄的批准覆蓋；不改原件bytes或重算Golden Expected IDs。Batch只重編程序與交付，不能改I-01–I-23或把runtime/工作區換成第二個truth。

## 3. ADR消歧與Runtime來源

ADR-ID-013：[WorkGeneration/Candidate/Acceptance](references/formal/34_ADR_013_WORK_GENERATION_CANDIDATE_AND_ACCEPTANCE.md)。D11-A-LP：[Human-only protocol](references/formal/35_D11_A_LP_LOCAL_HUMAN_DECISION_PROTOCOL.md)。

ADR-MOD-013：本repo原docs/34_ADR_013_MODULAR_CORE_EXTENSION_ARCHITECTURE.md。ADR-014：原docs/35_ADR_014_DURABLE_EVENT_ORDERING_AND_CANCELLATION_CLEANUP.md。兩個ADR-013用別名/完整path消歧，不自動重新編號或升版。

MCF：[external contract](references/MCF-02-EXTERNAL-RUNTIME-MODULE-CONTRACT.md)、[target evaluation](references/MCF-02-EXTERNAL-RUNTIME-TARGET-EVALUATION.md)來自b317e5d7；[修復候選notes](references/MCF-02-I01-REPAIR-REVIEW-NOTES.md)來自030890b3。Notes/測試報告是Writer材料，未獨立接受；配置deny-all與live未驗限制不得忽略。

GOV：[Cross-machine governance](references/36_POLYNEXUS_CROSS_MACHINE_GOVERNANCE.md)來自1ea8ce3d。只繼承portable/checkpoint/role語意，不採用過期95分/IMPLEMENTING routing。當前由docs/37與delivery/START_HERE導航。

## 4. 來源完整性與歷史連結

以上22份拷貝來源均保留原Git blob，SOURCE_LOCK可逐byte核對；不將本次文字改寫冒原件。作者文件使用本地存在的入口；原件中更早proposal或historical artifacts的相對連結仍保留原text，不能因此宣稱其所有連結都閉包。

Independent design review需分類normative/historical/external reference。必要原文/Golden/規則若未在固定來源中具備，屬source closure blocker，須回exact source補齊，不能以摘要猜測。歷史不參與當前實作的附件不必全部bulk匯入。

其他未拷貝來源以SOURCE_LOCK的exact commit/path讀取，必要時fetch該ref；找不到不是允許重造或重新批准。Source commit存在、來源receipt存在、作者自檢以及真正獨立設計/產品驗收是不同層次。

## 5. 衝突裁決

Human本次明示範圍 > Frozen invariants/Golden及有範圍的正式後續決議 > 已接受契約增量 > 原初版範圍 > 本次實作映射草稿。日期較新不能單獨覆蓋高優先權；Git/程序授權不改產品Human信任。

本次新SQL表/API/內部service命名是proposed mapping，非聲稱既存API；數值資源/版本要實機profile證據。真正semantic collision進DECISION_AND_GAP_REGISTER，由Fresh Reviewer指出是否需Human change-control，不由Writer選方便的一份。
