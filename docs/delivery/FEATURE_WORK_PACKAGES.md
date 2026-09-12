# 各功能開發契約：範圍、子項、限制與驗收

Status: DRAFT_FOR_INDEPENDENT_DESIGN_REVIEW
Task: PREP-FULL-DELIVERY-01
範圍：Git 已定稿初版＋最後確認的擴充增量；產品版本不變。

[功能契約資料](FEATURE_SCOPE_MATRIX.json)是本文件的逐項附錄：22個FD工作包、78個PN主需求、257個以分號拆分的功能子項。這是本次規劃的分解數量，不是產品完成率，也不是宣稱所有原子來源條款已經獨立審查。每個PN恰有一個primary owner；其他包透過依賴使用其契約，不重造同一能力。

## 1. 三份文件的分工

[REQUIREMENTS](REQUIREMENTS.md)：每個PN的原始來源、行為、原成熟度與驗收索引。

[FEATURE_SCOPE_MATRIX](FEATURE_SCOPE_MATRIX.json)：每個包的依賴、責任區域、禁止事項、输入、交付物、正負SIT、Human UAT，以及每PN的功能子項與限制。不能只讀PN標題就開工。

[GOAL_PLAN](GOAL_PLAN.md)：把功能包按依賴分批執行。FD是責任包，不是要求Human逐個批准的Gate，也不是22個並行coding writers。

規範優先序：Human明示範圍與frozen來源 > 既有正式功能/增量 > 本次整合設計 > 本功能分解。不得因矩陣簡寫而刪除原required義務。

## 2. 每項功能的有效開發契約

每個PN的契約 = 原需求及Source clause + 其功能子項 + primary FD的全部以下欄位 + 對應PRD/SA/SD/API/安全/UX及測試文件。不得只挑允許區域而忽略限制。

| 欄位 | 必須具體記錄的內容 |
|---|---|
| Identity / source | PN-ID、FD-ID、原來源commit/path/section、現design候選SHA |
| Functional items | JSON items的分號子項，依序可用PN-nnn.01等定位；不是新產品版本 |
| In scope | JSON areas及子項對應的既有責任；本次僅做缺少或受影響的差額 |
| Out of scope | JSON forbidden＋每PN limits＋原frozen non-goals；scope不能由Writer自行擴大 |
| Existing / new | 先定位已接受實作與候選；actual symbol/path查明後記reuse/modify/new，不以檔名假設存在 |
| Inputs / outputs | 固定requirements/context/source/contract refs、對外DTO、durable facts、可驗artifact |
| Dependencies | 必要技術介面/資料責任及其ready facet，不是前包所有Human UAT已完成 |
| Data / API | DATA_AND_API的proposed映射需通過設計審查；新增schema在同包遷移/restore責任內 |
| Security / side effects | 寫檔/程序/外傳/秘密/ownership/授權與失敗時應禁止的效果 |
| Positive UT | AT-nnn-P群：每個功能子項都需相應輸入、操作、可觀察oracle與side-effect檢查 |
| Negative UT | AT-nnn-N群：PN limits及FD forbidden各有失敗/拒絕/不變證據，不只確認exception存在 |
| Contract / SIT | JSON sit_positive/sit_negative＋TEST_PLAN對應Scenario，含相鄰模組實際呼叫 |
| UAT | JSON uat對應HU清單；FD-22為開發流程驗證，不產生產品Human接受 |
| Evidence | exact Candidate/source/contract、command/cwd/environment、actual parent/child exits、counts、hash、fixture/live標記 |
| Review / repair | Fresh Reviewer不是Writer；同scope缺陷自動修復、新SHA、受影響重驗 |
| Completion | 子項全核銷、必要正負案例與整合有效、無BLOCKER/MAJOR，不能用檔案存在或自述完成 |
| Stop | 範圍/公開契約/安全/不可逆動作/資源上限/unknown ownership等依EXECUTION_CONTRACT停止相應動作 |
| Handoff | 本包具體產物、版本/相容性差額、未驗項、下一可執行單元及stop條件 |

257個子項不是257份各自重複的主規格；共用安全/事件/驗證規範以引用繼承。不能因共用而只驗一個子項就標整PN PASS。尤其九範本、三Web vendor、三Local endpoint、兩深度Runtime分別保存結果。

## 3. 功能責任總表

| FD | 功能包與PN主責 | 主要開發內容 | 包級不可越界 |
|---|---|---|---|
| FD-01 | Stability；064–066 | FK、CREATED重啟、啟動/配對/分層health | 不repair真DB、不fakebinding、不給Human Accept權 |
| FD-02 | Project/Task/History；001–003 | 專案開啟封存、歷史與三入口 | Archive不刪接受歷史，不新增Develop頂層 |
| FD-03 | Context/Artifact；009–011 | 版本/refs/hash/分類、生命週期與closure保存 | 不RAG、不刪accepted引用、locator非identity |
| FD-04 | Generation/Workspace；043–048 | Begin/Retry/Abort/Cancel、lineage、worktree四軸 | 不並行coding、不動Human dirty、不造Attempt |
| FD-05 | Lifecycle/Binding；016–019 | 副作用前binding、實際cleanup、resume與reconcile | 不改public adapter/binding語意，不猜owner |
| FD-06 | Modules；040–042 | static manifest/registry/bridge、交換及隔離 | 不marketplace/remote loader，不第二resolver |
| FD-07 | External envelope；068–071 | Run隔離config/staging/policy、Core output import | 待審candidate不自動採用，不全部allow |
| FD-08 | Deep runtimes；020/021/067 | 先真實feasibility、逐target可用性與conformance | fixture不等live，兩個target不互相借PASS |
| FD-09 | Local AI；022/023 | 三類endpoint、模型/串流/能力及identity | 不支援取消/格式不假裝支持 |
| FD-10 | Policy/Secret；027–030 | 最高分類、三modes、逐step egress、SecretRef | 不silent fallback，不洩secret，不以local判安全 |
| FD-11 | Snapshot/Candidate；049/050 | REV1 identity、quiescence、freeze/publication | 不重算Golden，不採caller diff作truth |
| FD-12 | Evidence/Verification/Assurance；012/015/051/052/078 | 原Evidence/四軸不變；新增三Mode/四Status、assessment與DTO | Mode/Status不等PASS或Human接受，缺證不當N/A |
| FD-13 | Human Protocol；053–058 | principal/session/challenge、exact view及append-only歷史 | 不Agent冒Human，無Override，不改舊Accept |
| FD-14 | Accepted/P0；059/060 | 開accepted副本、takeover標示、source可重建套件 | Accept不自動Git/apply，P0不靠私有session |
| FD-15 | Council/Findings；004–006/013 | 獨立role、cross review、synthesis、位置/severity | 不偽多AI、不無限輪次、不自動Human接受 |
| FD-16 | Workflow/Templates；007/014 | 固定nodes、step execution、九範本及失敗處置 | 不generic BPM或任意script，不每模板另造engine |
| FD-17 | Web/MV3；024–026 | 三vendor confirmed send/capture與fallback | 不cookie/private API、不代確認send、不DOM入Core |
| FD-18 | UX/Monitor；036/037/062/063 | screens、keyboard/focus、REST、後續WS | UI不DB/OS/Git；WS不是durable truth |
| FD-19 | Doctor/Guards/Metrics；031–033/038 | truthful能力/版本、相容路徑、quota、usage | 不捏費用/ROI或升support，不擅付費 |
| FD-20 | Migration/Ops/N1；034/035/039/061 | linear migration、backup/restore、clean install、selected-task portability | 不改旧migration/真DB，不繼承Human session |
| FD-21 | SIT/Delivery；008/072–074/077 | 四Golden、真bugfix與failure、全技術驗證和交付 | Verifier不改產品，不以AI rehearsal當Human接受 |
| FD-22 | Dev Governance；075/076 | 單線ref/角色/checkpoint、批次內修復與例外 | 不改產品Human trust、不force/rewrite/擴scope |

具體areas、inputs、outputs、每PN子項/限制及正負SIT都在同列FD的JSON條目中，不在表格的縮寫中另定義。

## 4. 共用檔案與接口變更的協調

`execution_service.py`責任依序為FD-04 generation/claim、FD-05 lifecycle/binding、FD-07 external envelope、FD-08 target integration。後包只修改該責任差額；任何前包公開契約變化做impact並重驗，不用整檔覆蓋前包。

`persistence/models.py/repository.py`及Alembic由同一active Writer在schema ledger協調。FD-20.MIG是共享遷移facet，隨FD-04/11/12/13新增資料結構同步完成，不等備份/N1全部完工才開始DB。每次取得真實當前head後新增linear revision，禁止各包預占同migration號或製造未批准多head。

`runtime/registry.py`與bridge由FD-05/06/07依唯一resolver契約串接；不讓各target重建resolver。UI `App.tsx`/client/navigation是共享入口，FD-02/18維護共同shell，其餘screens使用API，非整頁重寫。Test fixtures與mock server共享改動要回歸其既有consumers。

allowed area是責任上限，不是整目錄所有檔都可改。開工前機械列actual changed-file allowlist，標existing/new/protected，Reviewer按責任核對；一般private檔名在批准責任內可自行定，不逐個問Human。

## 5. 技術facet、交付階段與無循環路由

JSON deps表示所依賴的interface-ready技術facet，不要求前包全部功能/Human接受完成：FD-18.BASE為REST與最小UI；FD-18.WS為後續通知。FD-17只依FD-18.BASE，不必等WS。FD-20.MIG early提供schema/restore原則，FD-20.OPS/N1較後交付。FD-10.BASE在外部execution前，FD-10.MIXED與FD-16共同完成workflow層驗證。這些facet繼承同FD限制，不建立新的scope。

B01所需技術subset由FD-01/04/05/07/08/11/12/13/14與FD-21.B01組成；FD-21.FULL在所有required功能群完成後執行全SIT。B01不能稱全功能完成；也不能為等中途Human UAT而阻止所有可獨立開發的後續功能。

這套安排允許同一次批次授權连续處理，不要求同一時間一起寫全部模組。Core ownership、public interfaces、source identity和證據標準不因批次變大而弱化。

## 6. 測試規格如何成為實際案例

每PN有AT-nnn-P/N兩個測試群。對每個子項再落實test name、seed/input、steps、expected result、forbidden effects、actual command及環境。若一行含多target或範本，另按target/template parameter展開。共用negative限制也要驗相應副作用未發生，不能只看exception或HTTP400。

範例FD-04/PN-046：建立g1/R1→觀察實際失敗及owner釋放→Retry產生g2/R2→送晚到Abort(g1)→驗R2仍運作、g2control/fence不變、g1有自己的receipt。這不是僅mock回傳cancelled。範例FD-13/PN-057：取得Candidate A的view/challenge→將payload換B或變更policy→提交→拒絕且無Accept event；使用fresh合法A流程才成功。

UT與Contract先驗局部，SIT驗真實串接；Human UAT按HU情境觀察用途/操作。實作前CASE IDs都是計畫，不是已存在test或已PASS。原TEST_PLAN及frozen正負案例仍完整繼承。

## 7. 完成判準與未決事項

可送實作的條件：來源/設計/功能/限制/依賴/測試全部對得起來，fresh independent design review無BLOCKER/MAJOR，實際base/角色/資源/target權限具備。當前仍是文件候選，產品HOLD。

每包完成：所有in-scope子項有實際行為和測試、source/contract精確、protected areas未越界、獨立review、必要修復與重驗關閉。普通bug不回Human逐項批准；真正scope/安全/不可逆/未知預算例外集中提出。

結構驗證通過不保證所有設計皆正確；尤其MCF real-write/config feasibility、完整source-to-clause核對與Windows/live工具能力仍需獨立設計/實機Gate。不能因本文件有257子項就自行解鎖。


## 8. F001／F002 的逐項契約

PN-078唯一主責FD-12，11子項及三Mode/四Status的來源、行為、持久化/衍生/DTO/UX與正負UT/Contract/SIT/UAT見[ASSURANCE_CONTRACT](ASSURANCE_CONTRACT.md)及[ASSURANCE_TRACEABILITY](ASSURANCE_TRACEABILITY.json)。它是原Formal必做Assurance的恢復，不併入PN-052。FD-16/18只消費共同契約，D1b-W4→D3→D4按技術facet接續，無新並行Writer。

PN-038/FD-19新增human override的受限遙測子項及負例；不能建立、推論或授權Human Accept。舊245子項是前身分解，新矩陣257為245＋PN-078的11項＋PN-038的1項；不是功能完成率。
