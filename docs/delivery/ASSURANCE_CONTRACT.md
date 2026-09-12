# Assurance 與 human override 指標：F001／F002 修復契約

Status: WRITER_REPAIRED_PENDING_INDEPENDENT_REVIEW
Task: PREP-FULL-DELIVERY-01；修復前身：1489cd7f7d54800317cc5558c92041a38c229008。
產品版本不變；本文件不實作產品、不解除 PRODUCT_IMPLEMENTATION=HOLD_PENDING_START_GATES。

<a id="authority"></a>
## 1. 來源、責任與不變邊界

F001 的既定來源是 FORMAL@43aa27c8b7a1b950645acc0d41234ec7679b653e：[Scope §2 BASELINE／§5](references/formal/00_SCOPE_BASELINE.md)、[PRD §7 Policy / Assurance](references/formal/01_PRD.md)、[SA §4](references/formal/02_SA.md)。三種 Mode、四種 Status 與不可关闭的來源真實性／Evidence／policy 底線均照原文保留。

新增 **PN-078，唯一 primary owner = FD-12**。FD-02／FD-18 只接 UI/DTO；FD-16 使用已固定的 workflow/profile；FD-13 仍獨立擁有 Human acceptance；PN-052 仍是 verification 四軸，不以它代替 Assurance。FD-12 在 D1b-W4 交付基礎 assessment；D3 串 workflow/Council，D4 串完整 UI；T1/T2/Human UAT 覆蓋全部值。只做缺少或受影響的差額，不重做無關產品。

來源列出 Mode/Status，但沒有完整規定每個轉移、DTO 或實體資料表。本文件以下內容是**本次待獨立審查的實作設計映射**，不是偽稱已被來源逐字定義或已實作。它不刪除原 Assurance、不增加驗收 override、不更改 Frozen identities／Golden／D11。

<a id="modes"></a>
## 2. Mode：要求的審查策略，不是結果或權限

Mode 在 Task input UI 明選，或明確繼承所選 immutable Workflow version 的 default；Core 驗證 selector 的 task-edit scope、expected revision、profile 可用性及資料/執行政策。無明選且 workflow 無 default 時回需選擇，不猜預設值。Agent 僅在既有 task-edit policy 授權內準備輸入，不能把模式設定當 Human 決定。

| 值／PN 子項 | 本次設計的產品行為 | 不可推論 |
|---|---|---|
| FLEXIBLE／PN-078.01 | 使用 workflow/profile 中明列的可選 review 步驟；可只完成自評或討論。未配置獨立/工具檢核時如實呈現實際深度。 | 不移除任何已宣告 required/hard gate，不把自評當 verified。 |
| STANDARD／PN-078.02 | 要求 profile 指定的獨立 cross-review 路徑；Core 核對 role/lineage attribution。工具義務仍來自固定的 workflow/validation contract。 | 同一份答案重貼或換模型名稱不等獨立；缺 reviewer 保持 NEED_ACTION。 |
| VERIFIED／PN-078.03 | 要求明確、非空的 deterministic verification contract 與 hard-gate 集合，及該 contract 宣告的 review 義務；未能解析/配置則不標 verified-ready。 | 選中此 Mode 不自動得到 VERIFIED Status、PASS、Human Accept 或 vendor certification。 |

三模式都維持平台安全/policy 底線與來源真實性。只有 Workflow 指定的 hard-gate Evidence 有 Verified PASS 的證據否決權；普通 advisory finding 不因 Mode 而變成 hard gate。Policy 的 DENY/APPROVAL_REQUIRED 仍由原政策控制面處理，不偽裝成 AI 投票或額外 Evidence 規則。

Mode＋assurance profile/version 的選擇在 BeginWork 時納入既有 Requirement/ValidationContract snapshot 引用，不另造 identity 演算法。未開始的 input 可透過 CAS 編輯；已開始/發布後變更要建立新 input/generation，且變更驗收契約時依 REV1 形成新 Candidate。降低 Mode 不能重新解釋舊 Candidate 的 required gate 或舊 FAIL。

<a id="statuses"></a>
## 3. Status：Core 衍生的已證實審查深度

Status 不接受 caller 直接寫入，不按 Mode、模型名稱、Runtime maturity、Human 接受標籤或人數自動升級。它是針對 exact target/contract 的 current assessment；可用 Candidate 時必須綁 exact Candidate，pre-publication 則綁固定 input/revision，不跨 target 借證。

| 值／PN 子項 | 成立條件 | 負向條件 |
|---|---|---|
| UNREVIEWED／PN-078.04 | 尚無可用且綁定正確的有效 review/verification observation。 | 不因已選 VERIFIED Mode、Run COMPLETED、舊 target 有 review 而升級。 |
| SELF_REVIEWED／PN-078.05 | 至少一份可追溯的 writer/self review；沒有符合更高層條件的事實。 | 自評不得自行宣告 CROSS_REVIEWED 或 deterministic Evidence。 |
| CROSS_REVIEWED／PN-078.06 | 有符合 profile 的獨立 cross-review observations，來源/目標/角色可驗；不是只看 reviewer 數量。 | 同 lineage、自評重貼、foreign/stale review 不成立。 |
| VERIFIED／PN-078.07 | 對 exact target/contract 的 required applicable deterministic checks 已完成且證據有效，所需 review 義務也滿足；來源/內容/契約/freshness 均可核對。 | 缺證、UNKNOWN/ERROR/TIMEOUT、required SKIPPED、STALE/MISMATCH 或不可解析的 applicability 不成立。 |

**Status 描述證據深度，verification outcome 描述結果。**完整且有效的檢核若證實產品 FAIL，可以呈現 `Assurance Status=VERIFIED；verification outcome=FAIL；acceptance eligible=false`，不能把它改為 PASS。若失敗的是驗證基礎設施而非可判定的產品檢核，證據不足時不得顯示 VERIFIED。UI 必須同時呈現 outcome/eligibility，不能只給一個綠色 VERIFIED 圖示。

衍生順序是檢查 VERIFIED 條件，其次 CROSS_REVIEWED、SELF_REVIEWED，否則 UNREVIEWED；不強制每一級都走過。可由 UNREVIEWED 直接到 VERIFIED，但只能由完整有效證據支持，不是 API 直接改 enum。任何層級在證據失效、policy/contract/target 改變後，重新推導到目前可證實的層級並記理由；保留先前 assessment，不能原地抹掉歷史。新 target 不沿用舊 Status。Status 變動不建立/撤銷/取代 Human acceptance；歷史接受、目前 disposition 與 eligibility 仍分開。

<a id="data-api"></a>
## 4. 資料、API、UI 與失敗責任

以下是 proposed internal DTO/持久化映射，並非已存在的 public API：

- Input：`assurance_mode`、`assurance_profile_ref`、source workflow version、expected input revision；循既有 Task input mutation/auth/CAS，不另建可寫 Status endpoint。
- Immutable input/contract 保存 effective mode/profile 引用；不得修改已發布 snapshot 或 RuntimeBindingSnapshot。
- Query assessment：exact target/contract refs、mode/profile、`assurance_status`、review observation refs、verification ref、evaluation revision/time、validity/reason；outcome、runtime maturity、Human acceptance/current disposition 是不同欄位。必要時經 Repository 保存 append-only assessment；cache 只可用 target/contract/evidence revision key，失效必重算。
- 未知 Mode、非法 enum、stale revision、跨 target refs、caller 提交 `assurance_status` 或 acceptance 欄位皆拒絕；不默默映射 STANDARD/VERIFIED。
- Legacy 若缺 mode/profile/可信 observations，明示未配置或不可判定；無可證明 review 時 Status=UNREVIEWED 並帶 legacy reason。不能根據歷史 score、Human evidence 字串或 Run success backfill VERIFIED。
- UI 在 Task setup 顯示模式選擇及其 review 要求；Candidate/Result 同時顯示要求模式、實際 Status、check outcome/validity、acceptance eligibility 與 Human disposition。read-only badge 不是按鈕或權限。
- 選模式/讀 assessment/變 Status 不 launch、不外傳、不寫 Human source repo、不 commit/merge/push、不產生 Human decision；真正副作用仍走原 Core command/policy。

Shared areas：FD-12 提供 assessment/repository/DTO 契約，FD-16 consumer 不能重造 evaluator；FD-18 做 view；需要資料承載時循 FD-20.MIG 的既有 linear migration/restore 設計。只列後續實作責任，本次不改這些產品區域。

<a id="metric"></a>
## 5. F002：`human override` 的唯一受限定義

保留 FORMAL PRD §10 的歷史名稱 **human override**，canonical telemetry key 建議 `human_ai_recommendation_disagreement_count`：在已界定 scope/time window 內，對具可信 Human attribution 的合法決策/選擇，記錄其與被引用 AI recommendation 不同的次數。它是**觀測上的人機建議分歧**，不是 acceptance override。

PN-038／FD-19 仍是唯一 primary owner。資料至少引用 source audit event ID、Human principal reference、AI recommendation/artifact version、target/scope、observed choice、server time；不得含 secret。以 `(metric_key, source_event_id)` 去重，只有已通過原授權/attribution 邊界的事實可計入。純 client `human=true`、Agent 自述、沒有可定位建議或無法歸因的事件不算已確認 Human 分歧；不可觀察時顯 UNKNOWN/null，不猜0。0只能代表有完整可觀察 coverage 的指定區間內零件有效分歧事件。

FD-19 從合法 audit event/append-only facts **單向讀取/衍生**這個 metric，不反向寫入 FD-13 decision service、eligibility、verification outcome 或 Candidate。不得新增 `Override Accept` route/action/permission，不得因計數增加建立、推論、授權、撤銷或繞過 Human Accept。既有 Human Decision 是上游事實，不由 metric 建立。原 no-Override 權威：[D11-A-LP](references/formal/35_D11_A_LP_LOCAL_HUMAN_DECISION_PROTOCOL.md)。

此為 `human override` 舊用詞的 D11-compatible telemetry clarification，不刪除原 metric、不替換 Frozen Human/security 語意，不推廣成任何人為豁免 required check 的能力。source-resolution 記錄為 DECISION_AND_GAP_REGISTER 的 D14。

<a id="tests"></a>
## 6. 明確的 UT／Contract／SIT oracle

每列 P/N 是**後續產品測試規格，尚未執行**。prefix 為 AT-078-Pxx/Nxx；共11對。ASSERT必須包含 target、data/decision history 與副作用前後比較，不只確認 exception 存在。

| xx／子項 | 正向 Pxx | 負向 Nxx |
|---|---|---|
| 01／FLEXIBLE | 固定FLEXIBLE/profile；自評後狀態SELF_REVIEWED，optional未跑明示。 | 同target已有required hard-gate FAIL，改用FLEXIBLE請求仍不能PASS/Accept或改舊contract。 |
| 02／STANDARD | 獨立且可追溯cross-review完成，狀態CROSS_REVIEWED、outcome依實際finding。 | 同lineage兩個名字/重貼答案不滿足cross-review；保持不足的實際層級。 |
| 03／VERIFIED Mode | 設定VERIFIED/profile，執行前仍UNREVIEWED，完整check後才衍生結果。 | 空hard-gate集合/未知profile/只送Mode=VERIFIED不產生verified-ready或Status升級。 |
| 04／UNREVIEWED | 新target無observations時read/reload均UNREVIEWED。 | 另一Candidate或舊Run的review不使新target升級。 |
| 05／SELF_REVIEWED | 可追溯自評綁target後read/reload為SELF_REVIEWED。 | 自評payload自稱verified/獨立，不產生更高Status或TOOL_EVIDENCE。 |
| 06／CROSS_REVIEWED | 合法獨立cross observations綁target/profile後成立。 | foreign/stale/mismatched reviewer observation不能成立。 |
| 07／VERIFIED Status | 完整有效deterministic產品FAIL證據仍可顯VERIFIED深度，但outcome=FAIL且Accept阻擋；PASS另測。 | required缺證/skip或infra timeout/mismatch不能顯VERIFIED，也不能滿足mandatory。 |
| 08／Mode快照 | Begin前CAS編輯，新generation使用固定effective mode/profile，舊資料不變。 | Begin/Publish後原地降模式/改validation snapshot拒絕；需新input/generation/Candidate。 |
| 09／衍生轉移 | 逐步新增有效觀察，並測valid direct UNREVIEWED→VERIFIED；每次留assessment原因。 | 證據失效重算到有根據層級，保留舊assessment及Human accepted歷史，不自動revoke。 |
| 10／DTO/UX | UI同時列mode、status、outcome、maturity、Human disposition，與REST query一致。 | caller寫Status或混傳accepted=true拒絕；零launch/egress/Git/HumanDecision增量。 |
| 11／legacy/拒絕 | legacy缺可信facts呈UNREVIEWED＋reason，已合法資料可正常查。 | unknown enum、unauthenticated、stale/cross-scope mutation不改任何受保護事實。 |

SIT-15：Task mode/profile選擇→固定input→review/verification→query/reload→UI分軸→失效重算；對3 Mode×4 Status採適用組合/不可達組合判斷，不把12個組合一律宣稱可達。以具可信來源的合成facts驗證分支，再由真正workflow提供observations整合；fixture不是正式Human UAT。

Metric案例：AT-038-MP01=合法可歸因分歧事件計1；MP02=重送同event仍1、完整空window為0。AT-038-MN01=偽造/不可歸因/無recommendation不計已確認分歧，coverage不足為UNKNOWN。MN02=測新增/增量/偽造metric請求，`AcceptanceRecorded`、Human decision history、eligibility、verification result前後完全相同；試圖傳accept/override字段拒絕。SIT-13串FD-19合法audit消費與UI，SIT-06回歸D11 no-Override。

<a id="uat"></a>
## 7. Human UAT 延伸與文件核對

HU-03 增列：依允許流程選三種Mode，觀察四種Status的實際證據深度；查一個VERIFIED+FAIL例，確認不能Accept；失效重算後歷史不消失。HU-06 回歸Human邊界。HU-12 增列：觀察一筆合法分歧與同event重送、UNKNOWN/0區別，並確認metric沒有接受/override操作。這些步驟納入最終Human UAT，不要求Human現在操作。

[ASSURANCE_TRACEABILITY](ASSURANCE_TRACEABILITY.json)逐值綁FORMAL source→PN-078子項→FD-12→本契約→P/N→SIT-15/HU-03；另綁PN-038 metric。文件checker須拒絕刪除任一值/owner/source/oracle/mapping。checker只能驗這些明列結構/文字引用，不代表完整來源語意覆蓋、產品測試或獨立PASS。
