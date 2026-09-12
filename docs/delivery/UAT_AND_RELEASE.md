# 最終 UAT 與交付契約

Status: UAT_PLAN / PRODUCT_VERIFICATION_NOT_RUN
目標：AI先完成正常開發、技術測試、獨立審查與修復，再集中交Human檢核實際用途、操作及成果。以下是要交付的契約，不是宣稱目前已有安裝包或測試通過。

## 1. AI交付前入口

全部本次required功能有可定位implementation與exact candidate evidence；來源/設計/功能包/UT/Contract/SIT/UAT追溯成立。必要技術checks通過，沒有未解BLOCKER/MAJOR。Live能力只按實際版本與操作scope宣稱；未支援/未測如實列出，不能把required未完變成known limitation。

AI測試Human協議只用隔離TEST_ONLY principal；實際Human acceptance和必要Web send保留Human操作。B01可先technical-ready供後續開發，真正Human-only條件在本UAT集中完成，未完成不得標B01或整體Human accepted。

## 2. 必交資產

- exact source/候選SHA及build/package hashes；可啟動套件或可重現建置安裝方式、依賴lock和支援環境。
- 繁體中文使用手冊：安裝、啟動、首次連接/配對、三入口、repo/input/工作、結果/證據/接受、Web/Local、取消恢復、Doctor、備份還原。
- 功能核銷：每PN/功能子項/原required條款，source、implementation、test command、current evidence、review、成熟度與限制。
- 技術驗收報告與必要JUnit/log/screenshots索引；大檔不直接推public Git，保留批准位置及hash。
- 最終人工操作表：步驟、輸入、預期結果、實際結果欄、問題位置、失敗回報方式；不要求Human逐份看UT log。
- 安全與操作限制、已知問題、備份/還原/回退指引、P0 accepted-package verify/reconstruct方法。

## 3. Human操作情境

| UAT | 操作 | 必要結果 | 不可接受 |
|---|---|---|---|
| HU-01 | 依手冊在指定乾淨環境啟動/重開 | Core/UI/schema/runtime readiness分層清楚，歷史可讀 | 開發者手動改DB/隱藏global設定才會動 |
| HU-02 | Create Project→Discuss，多角色分析 | 可定位原稿、交叉審查、共識/分歧/風險，partial failure明示 | 同一份回答假裝多AI |
| HU-03 | 文件/程式Review及九範本代表操作 | Finding位置/severity/依據可理解，每範本技術覆蓋已核銷 | 模板只有名稱不可執行 |
| HU-04 | 真實小bug：固定input→Run→diff→tests | 修改在managed/approved workspace，原Human dirty不變 | 只說改了，沒有source或測試 |
| HU-05 | failure/Cancel/Retry與重開 | 舊輪/新輪分明，安全cleanup，late abort不誤停新輪 | unknown owner仍放行新writer |
| HU-06 | Candidate verification及Human Accept/Open | exact view/required有效，接受後開啟對應source | tool fail仍Accept、改內容沿用舊PASS |
| HU-07 | Reject/Revoke/Supersede/takeover | 前後接受歷史保留；Working Copy不冒immutable結果 | 覆寫歷史、Accept即改原repo或push |
| HU-08 | Local-only及核准雲地混用 | 選定route與實際記錄一致、禁止的egress被拒 | 敏感資料靜默走cloud |
| HU-09 | 三Web vendor確認send/capture/fallback | payload/target明確確認、正常與fallback可用 | AI未經必要確認自動send或讀取秘密 |
| HU-10 | 模組/Runtime切換與Doctor | 既定支援範圍可用，不影響歷史；unsupported清楚 | 僅descriptor就標全部SUPPORTED |
| HU-11 | Backup/Restore、P0 verify/reconstruct | 關鍵資料/source可重建，hash一致、secret不出包 | 缺source或依賴provider私有session |
| HU-12 | N1/WS後續能力與日用UX | 本次已納入scope項如實交付，reconnect不丟durable事實 | 以B01已過为由省略完整目標 |

各功能包的UAT cases細分到FEATURE_SCOPE_MATRIX與TEST_PLAN；Human可按風險抽查已由獨立AI實測的普通細節，但不可把必要真實Human-only確認抽查成未做即PASS。

## 4. 問題處置

UAT缺陷分功能不符、操作不可用、資料/安全、環境、需求變更。前四類在原scope內由AI修復、new candidate、affected與required regression、fresh review，再只重驗受影響Human情境；不讓Human重新批每個bug。

需求變更若改已凍結規則、介面、安全/資料權限或驗收約定，要更新requirements/validation snapshot與impact；新Candidate不能冒舊接受。重大問題不得用『使用者可以先忍受』默認waive。Human明確接受的限定例外需記範圍與未達成熟度，不能抹掉工具failure。

## 5. 最終狀態與發布

AI輸出READY_FOR_HUMAN_UAT不是SIGNED/ACCEPTED/PRODUCTION_READY。Human接受exact delivered candidate與限制後才記對應接受。Product Accept不自動Git merge/push/tag/release/apply；release publication是獨立授權副作用。

後續任何source/contract/dependency改動形成新候選和impact驗證；交付包hash必須對上被驗bytes。記錄當前disposition與歷史Human decision，不以日期或branch名推導成功。產品版本不因本文件或前置commit自行增加。
