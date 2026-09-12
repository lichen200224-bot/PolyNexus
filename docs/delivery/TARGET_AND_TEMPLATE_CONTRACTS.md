# 多目標與九範本的展開契約

Status: DESIGN_DRAFT。此表將集合型PN展開，避免一個target成功就把整列標PASS。功能范围來自原Scope/PRD及已保存MCF提案；不宣稱任何第三方當前版本已通過。實際版本/權限/協定由獨立設計及實機Gate核對。

## 1. 九個範本：FD-16 / PN-007

| Template | 必要輸入 | 正常輸出/行為 | 必測失敗與限制 |
|---|---|---|---|
| Code Review | exact source/Artifact、範圍、review checks | Findings定位到檔案/行或symbol、severity、依據與修復建議 | 缺source/cross-ref拒絕；AI opinion不變TOOL Evidence |
| Release Validation | frozen Candidate、requirements、validation contract、runner profile | 各required check有效結果與Verified eligibility、證據索引 | build/test FAIL、STALE/MISMATCH不能被投票蓋過 |
| Bug / Incident Analysis | incident描述、已批准log/artifact、版本/時間與scope | 區分確認事實/推論、重現步驟、根因及修復/驗證建議 | 缺log不腦補；分析不自動修改production或重跑批次 |
| Technical Design Review | 設計文件、ADR/source基線、非功能要求 | 架構/契約/安全/相容性finding與取捨 | 不偷改frozen ADR；缺依賴列未確認 |
| Requirement Review | PRD/use cases/AC、角色與範圍 | 缺漏/歧義/衝突、可驗收性finding | 不自動加入不在scope的功能或替Human決策 |
| Change Impact Review | exact baseline＋proposed change、依賴/contract refs | 受影響模組/資料/API/測試/相容/回退及風險 | proposed diff不是Candidate truth；缺source列缺口 |
| Document Review | 選定文件版本、目的、檢核準則 | 有段落定位的內容/一致性/來源finding | 不引入未提供的事實，不傳未授權內容 |
| SOP Review | SOP版本、前置/角色/權限、例外/恢復規則 | 可操作性、缺步驟、責任與失敗處置finding | 危險操作僅模擬/分析，不因SOP文字就執行真實副作用 |
| Decision / Proposal Comparison | 明列方案、標準、約束及source | 各方案差異、共識/分歧/風險/缺資料、理由 | 不假造分數/效果；最終Human decision不由synthesis冒簽 |

各模板至少有独立正常輸入及一個主要錯誤/缺輸入案例；四Golden flows依TEST_PLAN深入端到端。共用workflow machinery，角色輸出/partial/error/policy/Artifact版本逐一保留。九個有效YAML不代表九個真實可用結果。

## 2. Runtime / Endpoint / Web目標

| 目標 | 本次範圍與主責 | 證據粒度與限制 |
|---|---|---|
| Codex | CORE深度Runtime，FD-08 / PN-020 | 真實executable/版本/cwd/change/result/cancel/timeout/cleanup；舊deterministic adapter保留不同maturity |
| OpenCode | CORE深度Runtime，FD-07/08 / PN-021 | ACP候選先獨立審查；first real external target按MCF設計；有效config/必要寫入可行性需證據，deny-all不算完成 |
| LM Studio | BASELINE Local endpoint，FD-09 / PN-022 | 至少一個合法可用實際endpoint/model profile的discovery/submit/result及失敗；不是所有模型認證 |
| Ollama | BASELINE Local endpoint，FD-09 / PN-022 | 獨立於LM Studio保存live profile/版本/模型/能力與測試 |
| Generic compatible endpoint | BASELINE，FD-09 / PN-022 | 指定相容API surface及server/model；同一fixture不能假成三個live provider |
| ChatGPT Web | Level3A，FD-17 / PN-024 | 使用者confirmed send、capture或mandatory fallback；不當official API/runtime |
| Claude Web | Level3A，FD-17 / PN-024 | 單獨的driver/真實操作/失敗與fallback記錄 |
| Gemini Web | Level3A，FD-17 / PN-024 | 單獨的driver/真實操作/失敗與fallback記錄 |
| Claude Code | 原COMPATIBILITY，FD-19 / PN-033 | 可驗偵測/相容路徑與實際maturity，不承諾同兩CORE深度；不是已支援宣告 |
| Gemini CLI | 原COMPATIBILITY及MCF backup | backup不代表與primary同時production實作；偵測/接入/能力逐項按證據 |
| Antigravity Runtime | 原COMPATIBILITY | 需辨認合法公開/可支持的execution surface；不能把桌面程式存在當Runtime契約成立 |
| DeepSeek Harness / Framework Runtime | 原COMPATIBILITY | 要鎖定具體harness及source/版本；不能把DeepSeek model endpoint當完整Runtime；未辨識則該整合未就緒 |
| ACP-compatible agents | 原COMPATIBILITY類別 | 明列具體受測agent與protocol，不由一個ACP成功推全部相容 |

其他常見Runtime是可擴充分類，不是無限新增本次required targets的授權。新的named target或改變成熟度/費用/安全要求要有明確scope mapping；既有原定named targets不得無聲刪除。無安裝/無帳號/無公開surface不等N/A成功，而是not-ready/unsupported及其影響，最終review按原契約處置。

## 3. target profile必要欄位

target_id/category、source authority、adapter/module identity、bound executable/version/digest（適用）、protocol/contract、observed configuration sources、auth ownership（只存reference）、destination/egress/effect allowlist、workspace mode、model可見identity、capability宣告、真實observations、host/browser/時間、actual command/result、limitation、成熟度。

沒有資料不要填估算價格、未知版本或假的zero usage。開工需取得必要profile，但不把帳號或秘密放Git。Live require Human操作者集中操作；自行在fixtures造Human操作不滿足live gate。

## 4. 設計仍需驗證的邊界

本文件固定要完成的目標集合與判準，不把尚未取得的第三方surface/版本可用性偽裝成已確認。Fresh design review必須核對真實接入路徑及scope可行性；如果原required結果無合法可行路徑，提出具體設計/範圍例外，而不是讓Codex到最後才發現只有名稱沒有方法。
