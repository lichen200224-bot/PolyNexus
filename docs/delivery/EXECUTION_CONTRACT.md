# 有界 AI 批次執行契約

Status: DRAFT / INDEPENDENT_DESIGN_REVIEW_REQUIRED
Current task: PREP-FULL-DELIVERY-01
Product implementation: HOLD_PENDING_START_GATES

## 1. 當前授權與目標

Human 已明確授權 ChatGPT 完成本次前置文件、Git/GitHub 發布與單一接續線整併；正式實作交由 Codex，正常開發、UT、SIT、獨立審查及同範圍修復由 AI 完成，Human 做最終檢核。最新補充要求所有功能各自的子項、開發範圍、限制、依賴及驗收先準備好。

本授權不是再要求 Human 逐 GOAL批准。文件準備可以自行提交與 non-force 發布；但文件存在不表示設計已經獨立審查，原未接受程式候選也不因整併文件而被接受。正式開工依本節條件判斷；不得自行刪功能或擴張凍結信任/安全邊界。

## 2. 權限表

| Action | 現在前置工作 | 完成開工 Gate 後 |
|---|---|---|
| 文件、引用、scope、測試契約、Git盤點 | ChatGPT Writer 可執行 | 依責任維護 |
| planning分支docs commit/non-force push/draft PR | 本輪已授權 | 不等設計或產品 acceptance |
| 改產品source/tests/dependencies/migrations | 本次不執行 | Codex在功能包責任與實際allowlist內執行 |
| UT/contract/controlled integration/SIT/review | 設計中；不宣稱產品已測 | 開工契約內持續執行，不逐次問Human |
| 同範圍bug修復/必要回歸/重新審查 | 文件修復可自行進行 | 預先包含於每個工作包 |
| task SYNC/CANDIDATE checkpoint | 文件分支允許 | receipt指定refs內可自主commit與non-force發布 |
| 下一已批准工作包 | 不啟動產品工作 | 技術依賴成立即可接續，無逐GOAL Human gate |
| 未接受MCF程式整合 | 僅保存exact來源及處置 | 獨立審查＋semantic integration evidence後才採用 |
| product Human Accept/真實Web send | 不執行 | 真實Human protocol/確認不能由開發授權代替 |
| release/default branch/ruleset/force/history rewrite | 不執行 | 未有相應明確操作授權則停止該動作 |
| 真實user DB、額外付費、擴大外傳 | 不執行 | 不從批次授權推定；需要既有明確資源/資料權限 |

## 3. 開工 Gate 與receipt

必須記錄：本Human授權來源、exact reviewed documentation commit、獨立設計報告、實際產品/integration base、既有candidate採用/拒絕狀態、每項PN/功能包、允許task/integration refs、allowed/protected path規則、角色、測試環境、target/config/auth ownership/egress範圍、有限budget/time/repair上限、停止條件。

可由現有明確授權及已完成Gate確定者直接填入，不重複要求批准已定稿功能。尚無實證的profile/額度/帳號不捏造；只有涉及不可委派決策的缺項才集中交Human。完成文件或GitHub API回讀不能代替fresh independent design review。Reviewer無法取得足够source或發現重大設計缺口時，留在前置修訂，不發開工PASS。

## 4. 角色與獨立性

ChatGPT是本文件patch Writer；不能自我宣告Independent Review PASS。Codex可分Controller、單一Writer、Fresh Independent Reviewer、Browser/Security/Migration Verifier。工具名、同帳戶或改角色名稱不證明context/寫入隔離；開工時驗證實際能力。

Controller只做依賴/資源/路由，不造Human身份或覆寫hard gate。Reviewer針對exact immutable candidate只讀審查；可在隔離驗證副本執行命令，不能改原candidate、放寬oracle或替Writer修產品。發現缺陷回Writer，新SHA重驗。

只讀分析可有界並行；同一產品接續線只有一個coding Writer。工作包同時ready不等可同時寫共享execution_service、DB、registry或UI入口。確需並行Writer須另變更治理，不由本文件推導。

## 5. 批次內正常工作

每個工作包包含實作、UT、contract、最小整合、文件差額、review、fix、affected regression及交接。已接受source優先重用；新需求造成差額才改。既有檔案的實際allowlist由功能包責任與read-only inventory導出並記錄，新private檔名可在指定責任目錄內選擇，不能借新檔偷加子系統。

禁止刪required功能/測試、改Golden expected ID、降低classification、跳過auth、用mock替live、UNKNOWN當0/PASS、擴target/費用、改受審身份或accepted歷史。一般工程選擇不得全部丟回Human。

## 6. 修復與例外

Finding包含id、severity、source/file/line、actual evidence、預期/實際、影響PN/工作包、fix owner、重驗方式。普通缺陷自動進Writer→新checkpoint→targeted/affected tests→fresh review迴圈。缺陷存在不等需要重批scope。

同root cause預設兩次bounded修復仍失敗，先fresh root-cause review；總批次受實際resource envelope約束。不能換finding ID無限retry。工具、認證或quota阻擋標ENVIRONMENT_BLOCKED/NEED_ACTION，required未驗仍不能完成。

例外packet集中列blocked action、原因/證據、受影響範圍、已保全SHA、可安全接續的獨立工作、最小決策與推薦、費用/權限/安全影響和resume action。只暫停依賴受阻動作，不隨意越過必要前置。

## 7. B01與最終Human檢核

B01產品情境仍要求真實Human Accept/Open/P0及失敗恢復；不得刪掉這些產品驗收。為免開發流程再變逐里程碑人工批准，AI可先形成B01_TECHNICAL_READY，保留Human-only案例為待最終操作。後續不依賴真實Human決定的開發可繼續，但不能標B01_HUMAN_ACCEPTED或把fixture Human principal當使用者真正接受。

自動化測試可使用隔離測試principal驗證協議正負行為，證據明示TEST_ONLY。不得使用Human真實credentials代跑產品接受。最終UAT集中完成必要Human-only操作；未完成前不得宣稱整體交付接受。

## 8. Git、scope drift與接續

每次publication先驗remote tip/expected parent與allowlist；non-force更新。SYNC可以未完成但標紅/未送審；CANDIDATE是review object，不等接受。已review過的SHA不amend/rebase；修復用新commit。Integration需exact候選與語意相容測試，textual merge成功不足。

換context/電腦先讀START_HERE、source lock、task/feature contracts與必要delta，再驗repo/branch/HEAD/ownership。Quota或中斷保存CONTINUATION_READY，不保證工具會在無支援的UI自動重開。NEXT_PROMPT不是遞迴delegation權限。

## 9. 終點

AI終點是required功能完成、必要技術驗證有效、無BLOCKER/MAJOR、套件/手冊/證據一致，以及READY_FOR_HUMAN_UAT。最終接受只由Human。UAT同scope缺陷仍由AI修復回歸，不重啟逐GOAL批准；新需求或凍結語意變動才作change control。
