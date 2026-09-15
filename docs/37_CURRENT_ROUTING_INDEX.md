# PolyNexus 單一目前接續入口

Date: 2026-09-15 (Asia/Taipei)
Canonical repository: `lichen200224-bot/PolyNexus`
Active documentation branch: `planning/enhanced-runtime-control-plane`
Task: `ENHANCED-DELIVERY-REPLAN-01`
State: `HUMAN_DIRECTION_APPROVED / DOCUMENTATION_CANDIDATE / FRESH_DOC_REVIEW_REQUIRED`
Product version: `UNCHANGED`

先讀：

1. `docs/delivery/START_HERE.md`
2. `docs/delivery/CURRENT_PRODUCT_STATE.md`
3. `docs/delivery/STRATEGIC_RUNTIME_FLEET.md`
4. `docs/delivery/GOAL_PLAN.md`
5. `docs/delivery/EXECUTION_CONTRACT.md`

再依 assigned unit 讀 feature/source/frozen contracts。

目前規劃基準不是舊 `PREP-FULL-DELIVERY-01` 的 HOLD/NEXT_GOAL 文字。已知 remote product state 以 `CURRENT_PRODUCT_STATE.md` 記錄並需由每位 Reviewer/Controller 重新 read-back：D1B/current route `e9538f328...`、B01 technical `ca85d22c...`、old MCF-02 `030890b3...` = `REJECTED / NOT_ADOPTED`。

Human 已批准後續收斂方向：Codex 全開發/測試，ChatGPT 獨立驗收 exact product candidate；PASS 後在批准 scope 內直接續下一 dependency-ready unit，不逐 Goal 問 Human。正常只保留一次 final integrated Human UAT / Acceptance；provider login 或 architecture/security exception 才條件式介入。

New product writes 尚未由本文件自動啟動。本 docs candidate 必須先依 `docs/delivery/DESIGN_REVIEW.md` 做 fresh non-writer independent review。PASS 後第一產品動作為 G0 Current/B01 reconciliation，之後依 D2b Strategic Runtime Fleet -> D3 -> D4 -> T1/T2 -> DELIVERY -> FINAL_HUMAN_UAT。

任何歷史分支/文件內舊 routing 只保留 provenance，不得覆蓋此 current entry；actual remote truth 和 current Human decision 優先。
