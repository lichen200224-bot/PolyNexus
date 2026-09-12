# 系統分析：完整交付與新版契約整合

Status: DESIGN_DRAFT。詳細frozen semantics見references/frozen/REV1與Architecture Freeze；本檔負責責任、資料流、依賴及差額分析，不修改Golden或凍結不變條件。

## 1. Context與責任

React/Vite local browser UI → authenticated REST（首vertical）/後續WebSocket → FastAPI Core → Task/Workflow/Council/Workspace/Candidate/Verification/Human-decision services → Repository＋SQLite、filesystem immutable store、OS-backed secret/security provider、RunSupervisor＋RuntimeRegistry/static modules → external Runtime/Local endpoint/Web companion。

仍是modular monolith，不加microservices、queue farm或必備Docker。GitHub是開發協作基礎設施，不是產品Core必要依賴。Local-personal/Single Human/Single Active Writer是當前威脅與併發範圍。

## 2. 資料/狀態分層

Task保存長期目的；WorkGenerationRef固定一輪輸入及其control revision；Run保存一次durable execution與immutable runtime binding；Workspace facts保存ownership/fence與Git observation；Snapshot/ChangeSet/Candidate保存content/contract identity；Candidate publication保存某generation/Run/lineage的來源關聯；Verification/EvidenceSet保存exact Candidate的工具結果；Human Decision以append-only歷史保存接受/撤銷等事實。

CandidateID依REV1不混入generation/Run；同內容及同要求/驗證契約可能相同ID，但每次publication的provenance不能合併。不能將accepted source copy、當前mutable worktree或供應商session當Candidate truth。

Legacy source中的NOT_IMPLEMENTED是historical；現product有binding/migrations/source不等full behavior已驗證。Legacy資料缺generation/可信Human principal時要明確LEGACY_UNBOUND/UNVERIFIED，不編造遷移成可信證據。

## 3. 主資料流

### 工作/修改

明選repo baseline及可用input → Core固定requirements/context/validation snapshot → CAS建立generation及writer lineage claim → Core建立isolated worktree／external projected staging → claim Run、commit event/binding/launch intent → runtime preflight → 真實execution → Supervisor觀察結果與cleanup → Core回收並固定result snapshot → Canonical identity生成ChangeSet/Candidate → publication → exact verification → Human exact view／challenge → Accept → OpenAcceptedManagedWorktree／P0 export。

所有副作用前須有durable intent與scope。DB commit和OS process不會被假設成單一原子交易；用outbox/operation intent＋觀察/reconciliation處理中斷。沒有足夠process ownership證據時不自動重啟外部工作。

### 非改碼工作

Discuss/Review/Validate沿用Task/Run/context/evidence與workflow semantics；只讀角色可並行分析，不等於並行coding Writers。文件或AI輸出以Artifact/Evidence來源保留。需要形成可接受成果時走同一content/candidate/verification契約，不另造第二個判定系統。

### 本地/外部混用

對每個step計算effective classification、mode、destination/trust、effect class；作ALLOW/APPROVAL_REQUIRED/DENY。僅投影該步必要context。LOCAL_ONLY限制整個tool/connector egress，不只LLM endpoint；部分步驟失敗保留已執行事實，fallback必須符合原policy及使用者意圖。

## 4. 模組、工作區與Runtime銜接

Module是包裝/註冊metadata；Adapter是行為契約；RuntimeRegistry是唯一profile/factory resolver；RunSupervisor是唯一lifecycle authority。MCF不得取代binding或generation的來源。

Core managed worktree屬內部workspace authority。External runtime PROJECTED_STAGING是更窄的投影，不等於把整個managed/Human目錄交出去；output必須經Core containment/hash/import及ownership/quiescence檢查後才可納入result snapshot。原Human repository的dirty/index/untracked不碰。

MCF-02 candidate的config/permission能力限制是待驗收的具體實作現況；完整產品需要的live/write能力必須透過有界版本/target gate補齊，不能把permission全開或默認trusted以省步驟。

## 5. 跨模組不變條件

- 一個generation只有一條writer lineage；不同command-id不能繞過。
- Abort generation/Cancel Run/Reject pre-accepted Candidate互不替代；晚到命令不瞄準浮動latest。
- writer停止與內容freeze先於verification；Verifier的執行副本若產生build files不改canonical source。
- Candidate identity與EvidenceSet生命週期分離；增加evidence可更新eligibility，但不能變source身份。
- Human challenge綁exact view、Candidate、decision、policy/evidence revision；提交時再次檢查。
- Operational auth與Human acceptance auth分開。Pairing/登入不等於允許任意command，更不等於Accept。
- 當下policy失效不重寫歷史Human決定；表達historical acceptance、current disposition、eligibility三種資料。

## 6. 失敗/恢復分析

FK/schema不符→停止write/launch但可提供sanitized health/audit。CREATED未claim→保持intent可顯示，不補造binding。launch intent已存但process觀察不確定→RECOVERY_REQUIRED facts，不重複launch。timeout/cancel cleanup不確定→保留ownership及diagnostic，不假稱CANCELLED。capture/local endpoint不支援取消→capability明示，UI不把本地等待結束當遠端工作已停。

DB/artifact部分寫入用content staging→hash→atomic publish＋metadata transaction；失敗保留可清理的owned transient entry，不能讓dangling reference進Candidate。Export還原需驗closure/hash，不能憑manifest自評。

## 7. 既有工作與依賴

S0先驗FK/create-restart/auth-health，不重做已接受ordering/cleanup。W1工作區/lineage → W2真實executor可行性 → W3 frozen source identity → W4 verification → W5 Human → W6 open/package → B01。模組/其他初版功能與完整workflow/UI在同一完整計畫的後續群補齊。N1/WebSocket後續交付不作B01擋板，也不從總目標消失。

細部實作需對existing API/DB/registry做compatibility mapping；若需要改public RuntimeAdapter/Binding/Golden而非内部實作，列architecture exception，不能自行擴張。
