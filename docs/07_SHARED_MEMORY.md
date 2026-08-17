# Shared Memory & Context Strategy

## Goal

三套工具共用同一 Repo 時，專案知識必須存在 Git，而不是任一聊天 session。又要避免每個 Agent 每次載入全部文件造成 Token 爆量。

## Memory Pyramid

### Tier 0 — Always-on, tiny
- `AGENTS.md`
- Antigravity `.agents/rules/polynexus-core.md`

只放不常變、必須永遠遵守的規則。

### Tier 1 — Session Bootstrap
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`

每次 session 先讀。目標保持精簡，Handoff 只記 Delta。

### Tier 2 — Task Knowledge
按需讀：PRD / SA / SD / Acceptance / Git / specific ADR / Contract。

### Tier 3 — Historical Evidence
舊報告、長 log、raw artifacts、歷史 handoff，只有 Root Cause / Audit 才讀。

## Project State Content

只保存：
- current milestone
- current version
- confirmed architecture baseline
- blockers
- next milestone
- compatibility status summary

不要放逐日工作日誌。

## Handoff Content

最多聚焦一個 current task：Goal / Owner / Branch / Changed / Tests / Known Issue / Next / Do-not-change。

## Decision Memory

重大決策寫入 `10_DECISION_LOG.md` 或 ADR。聊天中的「同意」若影響 architecture/scope，必須在下一個 checkpoint 寫入 Git 文件。

## Evidence Memory

AI conclusion 與 deterministic result 分開。長 test log 不直接放 Handoff，只記 command、exit code、failure names、artifact path/hash。

## Token Guard

- 不把完整 conversation export 當開發 context。
- 不在 AGENTS.md 複製 PRD/SA/SD。
- Skills 採 progressive disclosure。
- Reviewer 以 diff 為主，不重新撰寫完整方案。
- Machine-filter logs before AI.

## Future Personal Memory

V1 先做 deterministic project memory：facts、decisions、run summary、artifact refs、handoff。Semantic/vector auto-memory 後續再做，避免 V1 被 RAG 選型綁死。
