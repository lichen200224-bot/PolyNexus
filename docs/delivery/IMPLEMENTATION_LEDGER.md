# 既有成果與新交付差額 Ledger

Status: SOURCE_BASED_INVENTORY / NOT_FRESH_PRODUCT_VERIFICATION。這份初始表不是本輪產品測試結果。PN-001–PN-077全部仍需逐條建立implementation/evidence映射；不能因列在同一群組就統一判PASS。

| Source/area | 已觀察記錄 | 可以重用什麼 | 不能推論什麼 / next |
|---|---|---|---|
| f0c0b986產品線 | G30/WP20、BASELINE-DEBT-01文件記FINAL_ACCEPTED/CLOSED；bounded100/100 | 已接受source/history與有範圍evidence作baseline | 非全產品完成；本輪未重跑tests |
| MCF-01@96ae5353 lineage | static module checkpoint已有source/test | manifest/registry/bridge與現RuntimeRegistry | 非dynamic Plugin Platform或所有module types完成 |
| BASELINE-DEBT-01 | durable sequence/cleanup修復已有accepted scope | 對S0/W2受影響部分做差額評估 | 不代表S0 FK/CREATED restart/auth health全部完成 |
| Track A FORMAL@43aa27c8 | TA-F4接受receipt記錄；formal PRD/SA/SD/Identity/Human增量 | frozen設計、source Golden、不變條件與工作包 | S0/W1–W6 implementation不是因此accepted |
| FROZEN@fe2eb231 | 詳細REV1/Freeze/Work Packages來源樹 | authoritative design/Golden/WP criteria | sparse docs tree不是完整productbase |
| MCF02@030890b3 | Writer修復候選，READY_FOR_FRESH_INDEPENDENT_REVIEW；未accept | 候選設計、F001–F005修復與測試可供獨立review | 不可直接merge、無live compatibility保證、deny-all不等可改碼 |
| Codex/OpenCode deterministic adapters | f0內明示deterministic/local conformance | unit/contract machinery、binding/registry/Doctor基礎 | 不等真實vendor execution或Working Product PASS |
| 初版workflow/UI/九範本 | source及分項accepted bounded記錄 | 既有介面/engine/schemas/tests依影響重用 | 檔案存在不證明所有step/role端到端完成 |
| Web Level3A | G30接受限定三vendor evidence | 有範圍流程與fallback設計、原evidence | 不擴成native MV3所有情境/永久vendor certification |
| Local endpoints | bounded fixtures與保守cancel能力記錄 | policy/normalization/discovery契約 | 不等三類endpoint所有model真實conformance |
| GOV@1ea8ce3d | 新cross-machine/role/checkpoint語意 | portable routing及候選push模型 | 不採用舊95/100/IMPLEMENTING，也未變default/protection |

## 每項PN的最終記錄格式

```yaml
requirement_id: PN-xxx
source_refs: [exact_commit:path:section]
design_refs: [file:section]
requiredness_and_phase: source_bound_value
implementation_status: NOT_MAPPED
implementation_commit: null
implementation_paths: []
candidate_or_source_tree: null
tests: []
current_evidence: []
historical_evidence: []
independent_review: NOT_RUN
limitations: []
next_action: MAP_EXISTING_AND_VERIFY_DELTA
```

這是格式示例，不新增產品Domain schema。實作ledger可用JSON/YAML產生human摘要，避免同狀態維護八份報告；repo只存sanitized references，不混入user資料。欄位缺失是缺失，不猜測日期、版本、passed數或接受身份。

MCF待審結果、design review與S0實機檢查完成後，依exact結果更新相應項；歷史closed記錄不重開、不抹去，後續新問題另立finding並標受影響scope。
