# Legacy open work reconciliation

2026-09-10 · LEGACY_RECONCILIATION: NEEDS_HUMAN_DECISION

[Framework](POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) 的 Track A map 是唯一 active planning roadmap。此表停止舊 Gxx/WPxx/CP 派工入口，保存過往 bounded acceptance，不取消歷史事實、不宣告產品 PASS。TA-LR-01在F1前完成decision packet並取得Human disposition；本輪可完成治理交付，不自行執行 reconciliation implementation。

## Sources and inspection boundary

直接讀取本地 [Project State](../11_PROJECT_STATE.md)、[Handoff](../12_HANDOFF_CURRENT.md)、[Roadmap](../28_MASTER_DEVELOPMENT_ROADMAP.md)、[Control Panel](../GOAL_COMPLETION_CONTROL_PANEL.md)、[Gate 1.5 §2/4/5](../reviews/POLYNEXUS_GATE_1_5_HUMAN_DECISION_BASELINE_2026-09-09.md)、[REV1 §19](../reviews/GATE_2_CONTRACT_ARCHITECTURE_PACKAGE_REV1.md)、[Work Packages](../reviews/POLYNEXUS_TRACK_A_IMPLEMENTATION_WORK_PACKAGES.md)。Git 讀取 exact `f34e6b29ae9e7326d1d44b9b03756b450809928f:docs/11_PROJECT_STATE.md`、`docs/tasks/G24-G30-DEVELOPMENT-COMPLETION-ROUTING.md`、`docs/tasks/G30-FINAL-EXTERNAL-VERIFICATION-AND-100-POINT-RECONCILIATION.md`，並列出 task tree、local branches、tracked/untracked inventory。

本地舊 current 的 G19 NOT STARTED/30分與 f34 G28 95分/G30 NEED_ACTION 是不同時間/lineage，不能合併為現況。新版 current pointer優先；未逐一讀全部舊log、review_work profile、未知輸出內容；這些不能宣稱 reconciliation COMPLETE。舊 TODO/file-name 搜尋只供定位，不是所有 source TODO 都已處置的證據。

## Disposition register

| Legacy item / source | Classification | Track A destination | Scope and remaining evidence |
|---|---|---|---|
| G01/G02/G03、CP01 competition、proposal/presentation outputs | CARRY_FORWARD | NEXT | 保留PM文件與對外敘事；submission/外部平台狀態未查，不作產品gate |
| G04 delivery/CP06 packaging；G22相關交付 | CARRY_FORWARD | S0 | 關聯範圍/依賴（非另一primary destination）：S0 / W6 / B01；startup/health、START_HERE、P0 accepted package；完整installer/update不偷列P0 |
| G05/G06/G07/G10/G11/G12、PRE-WP14-A/B、WP14–16 runtime/registry/binding/Doctor | REQUIRES_REVALIDATION | W1 | 關聯範圍/依賴（非另一primary destination）：W1 / W2；accepted bounded facts保留；mapping/binding-first/freshness仍需新exact SHA evidence；conformance不證real executor |
| G08/G09 unknown slots（Control Panel無正式record） | REQUIRES_REVALIDATION | NEXT | 不發明工作內容、不授權dispatch；若Human無來源可決定OBSOLETE |
| G13 Council Run binding、WP12 Council | ALREADY_COVERED | W1 | 關聯範圍/依賴（非另一primary destination）：W1 / W4；breadth NEXT；已有歷史bounded safety；新Candidate/verification需重驗，不擴Council breadth |
| G14/G24 cleanup、WP24/WP28 budget/cancel/timeout | CARRY_FORWARD | S0 | 關聯範圍/依賴（非另一primary destination）：S0 / W1 / W2 / B01；CREATED restart、lateAbort、same-generation lineage、real child cleanup與failure/retry |
| G15/G25 redaction、WP18/WP29 egress/secret/policy | REQUIRES_REVALIDATION | W2 | 關聯範圍/依賴（非另一primary destination）：W2 / W4 / W5；新context/evidence/session路徑需secret exclusion/no silentfallback；舊PASS不能覆蓋新surface |
| G16 selection + G18 Doctor / G26 profiles | REQUIRES_REVALIDATION | W2 | DECLARED/OBSERVED/READY，實際版本、選擇、readiness無launch副作用 |
| G17/G27、WP23/WP30 migration/restore | REQUIRES_MIGRATION | F1-F4 | 關聯範圍/依賴（非另一primary destination）：FORMALIZATION / S0 / W1 / W3 / W5；依正式contract處理legacy refs/untrusted Human facts；Alembic、backup/restore，真實DB不自動repair |
| G19–G23 five-goal routing；舊current的Start G19 | SUPERSEDED | F1-F4 | 關聯範圍/依賴（非另一primary destination）：FORMALIZATION / S0 / B01；歷史來源與bounded成果保留；新的dispatch只走Track A，不能再按舊prompt起動 |
| G28 / CP06 RC bounded acceptance / 95分 | ALREADY_COVERED | B01 | 當時bounded接受不撤回；95/100不換算Working Product成熟度，新B01另驗 |
| G29 handoff/operator runbook | CARRY_FORWARD | NEXT | 可重用外部報告模板；handoff complete不代表external tests/real executor |
| G30 / WP20 三家 external reports缺失 | CARRY_FORWARD | NEXT | 關聯範圍/依賴（非另一primary destination）：NEXT；HD-L1待決；exact f34仍NEED_ACTION，WP20 0/5；不自動取得帳號/送出資料；不冒稱vendor verified |
| G31及後續未授權工作 | SUPERSEDED | NEXT | 沒有active dispatch；需新Goal明確scope |
| WP08A/B、WP09A/B/C/D、WP10、WP11 foundations | REQUIRES_REVALIDATION | S0 | 關聯範圍/依賴（非另一primary destination）：S0 / W1 / W4 / W6；保留existing behavior，針對受影響契約回歸；不得以全量舊測試替代新AC |
| WP17 local endpoint、多provider擴充 | CARRY_FORWARD | W2 | 關聯範圍/依賴（非另一primary destination）：W2 bounded compatibility / NEXT breadth；不自動選品牌，不silent cloud fallback；多executor非B01必要 |
| WP19 WebSurface/MV3、WP20 assistance | CARRY_FORWARD | NEXT | local manual/clipboard compatibility仍保護，live certification保持未驗 |
| WP21 browser waiver / G21 evidence | REQUIRES_REVALIDATION | S0 | 關聯範圍/依賴（非另一primary destination）：S0 / W1 / W5 / W6 / B01；舊waiver不轉PASS；新journey/negative需要實際browser evidence |
| WP22 fixed nine workflows / WP27 four golden flows | ALREADY_COVERED | W4 | 關聯範圍/依賴（非另一primary destination）：W4 / B01 / NEXT breadth；固定vocabulary保留；Track A B01 first vertical不被九流程廣度阻塞 |
| WP25 descriptive metrics / pilot | CARRY_FORWARD | B01 | 九pilot metrics、Direct Agent+Git+CI比較、Failure/Retry、Pivot/No-Go；不編數據 |
| WP26 progressive UX | CARRY_FORWARD | S0 | 關聯範圍/依賴（非另一primary destination）：S0 / W5 / W6；error/loading、Human exact view、Working Copy label、安全與UX共同驗證 |
| WP31/WP32 release/package/final handoff | CARRY_FORWARD | W6 | 關聯範圍/依賴（非另一primary destination）：W6 / B01 / NEXT release；Working Product、bounded compatibility、release各自證據，不自動發布 |
| Gate1.5 S0-1 FK / S0-2 CREATED / client-start health findings | CARRY_FORWARD | S0 | 關聯範圍/依賴（非另一primary destination）：S0-G01/G02/G03；正負criteria完整映射；WAL_NOT_REQUIRED_YET，不強制切換 |
| Gate1.5 Product P0 repository/input/ownership | ALREADY_COVERED | W1 | durable refs、dirty snapshot、single-lineage與lateAbort |
| Gate1.5 real executor/monitor/stop | ALREADY_COVERED | W2 | 真實cwd/write/cancel/timeout/process-tree evidence |
| Gate1.5 Candidate/capture/oracle/verification | ALREADY_COVERED | W3 | 關聯範圍/依賴（非另一primary destination）：W3 / W4；Core推導、fixedgoldens、required invalid、trusted oracle |
| Gate1.5 Human decision/history/recovery | ALREADY_COVERED | W5 | 關聯範圍/依賴（非另一primary destination）：W5 / W6；D11-C fallback、A-LP、append-only revoke/supersede、failure/retry |
| Gate2 pre-REV1 direction/Freeze HOLD labels | SUPERSEDED | F1-F4 | 關聯範圍/依賴（非另一primary destination）：FORMALIZATION；Freeze Record已記Human批准；不重開架構，不回寫舊裁決 |
| N1 selected-task export/history/Continuation/import namespace | CARRY_FORWARD | N1 | 不阻B01；P0必要source閉合留W6 |
| WebSocket、external CI、secondexecutor/B06、B02/B03 depth、standalone patch UX | CARRY_FORWARD | NEXT | REST durablefacts先交付；不得因未實作NEXT說B01未完成 |
| codex/goal-governance-v1-2 @5d1bd60；goal-objective-v1 @2552c45 | REQUIRES_REVALIDATION | F1-F4 | 關聯範圍/依賴（非另一primary destination）：FORMALIZATION；HD-L2；local refs observed；未merge，不能當current authority；本Framework承接Human operating decision，未採納其全部bytes |
| codex/phase-a-minimal-requirements @8750e7e | REQUIRES_REVALIDATION | F1-F4 | 關聯範圍/依賴（非另一primary destination）：FORMALIZATION；HD-L2；未納入baseline的formal/product proposals不可偷偷合入；需逐diff決定採納/歷史 |
| obsolete worktree path metadata（底線路徑差異） | REQUIRES_REVALIDATION | S0 | 關聯範圍/依賴（非另一primary destination）：S0 intake；HD-L3；stale metadata不證資料obsolete；不prune/repair/remove，先確認owner/實體內容 |
| README/Project State/Handoff/Roadmap/Document Index/WP12 dirty docs | REQUIRES_REVALIDATION | F1-F4 | 關聯範圍/依賴（非另一primary destination）：FORMALIZATION；僅新增治理pointer；原bytes保留。舊routing superseded，歷史內容不刪 |
| dirty Decision Log、runtime/contracts.py、runtime/registry.py | REQUIRES_REVALIDATION | F1-F4 | 關聯範圍/依賴（非另一primary destination）：FORMALIZATION / W2；本輪hash保全；不得宣稱本輪修改產品/正式契約；逐項source diff後採納 |
| untracked runtime/codex.py、WP14/conformance tests及其他source overlays | REQUIRES_REVALIDATION | W2 | 關聯範圍/依賴（非另一primary destination）：W2；HD-L2；不因未tracked刪除，不整檔覆蓋f34；actual tests未跑 |
| untracked reviews/planning/task docs、scripts、competition、initial-review/output/docs.zip/dist-review | REQUIRES_REVALIDATION | F1-F4 | 關聯範圍/依賴（非另一primary destination）：FORMALIZATION / NEXT；HD-L2；依責任保留、不stage；generated不等於可刪 |
| review_work依賴/profile/其他未鑑定untracked、unknown TODO/openfinding | REQUIRES_REVALIDATION | NEXT | 關聯範圍/依賴（非另一primary destination）：NEXT；S0前HD-L2 inventory gate；路徑/hash inventory已取；內容未逐一鑑定，不能宣告all backlog closed，也不可整包傳遠端 |

OBSOLETE 只在有逐項證據/Human disposition時使用；本輪未將未知資料標可刪。ALREADY_COVERED 表示新plan已承接責任，不代表implementation已完成。

## Closure owner and recommended Human dispositions (FINDING-02)

[TA-LR-01](../goals/TA-LR-01.md) 是唯一legacy closure Goal；DEFINED_NOT_EXECUTED / NOT_AUTHORIZED。Operating Model Accepted → TA-LR-01 → F1 → F2 → F3 → F4 → S0 → W1…。R2只定義Goal，不執行inventory或批准legacy處置。

| Decision | RECOMMENDED_HUMAN_DISPOSITION | Authority / completion |
|---|---|---|
| HD-L1 G30 external certification | KEEP historical NEED_ACTION；primary destination NEXT / separate external release verification；不得阻塞Track A B01，不宣稱任何provider external certified | Human最終決定；bounded internal checks保持原語意 |
| HD-L2 legacy branches/dirty/untracked/unknown findings | TA-LR-01 bounded inventory逐項分類、保留原件；不bulk merge/delete/reset/clean/auto absorb | Codex先查完可自行查明項再提完整packet；仍無法安全分類標NEEDS_HUMAN_DECISION |
| HD-L3 safe predecessor/lane | b87 dirty NOT implementation predecessor；f34 DESIGN/READ ONLY；真正lane從Human-approved remote-verifiable exact checkpoint建立 | TA-LR-01提出recommended SHA、branch/lane、dirty保全、cross-machine reproducibility evidence；未授權不得checkout/merge/push該lane |

## Item-level closure contract

上表沿用R1 coarse inventory，只將每列規劃routing收斂為一個primary destination；原跨WP範圍保留為依賴，非額外dispatch。這不是TA-LR-01已完成逐item調查。TA-LR-01須將每個relevant item拆成獨立ITEM_ID/source_ref/hash/previous acceptance/evidence record，指定**恰好一個PRIMARY_DESTINATION**：F1-F4、S0、W1、W2、W3、W4、W5、W6、B01、N1、NEXT；跨WP關係記DEPENDENCIES，不能多選PRIMARY_DESTINATION。每項CLASSIFICATION恰為CARRY_FORWARD/ALREADY_COVERED/SUPERSEDED/OBSOLETE/REQUIRES_REVALIDATION/REQUIRES_MIGRATION之一。Unknown保留並標REQUIRES_REVALIDATION+決策缺口，不刪歷史。

本輪classification completeness指所有R1粗分類列都由TA-LR-01 scope承接，不是假裝完成未授權的逐item調查。TA-LR-01驗收需總inventory數量=分類數量、無未映射/重複ITEM_ID、每保留項一目的地、每unknown有preservation ref/decision。舊roadmap維持HISTORICAL / NOT_ACTIVE_ROUTING；只有Track A map能派工。

TA-LR-01完成REVIEW_READY後Independent Review與Human一次決定HD-L1/L2/L3，accepted C及metadata R closure才供F1 intake。若Human未接受處置則F1不得開始；不因本輪NEED_FIX修復即宣告LEGACY_RECONCILIATION COMPLETE。
