# Shared Memory & Context Strategy

## Goal

多套工具共用同一 Repo 時，專案知識必須存在 Git，而不是任一聊天 session。又要避免每個 Agent 每次載入全部文件造成 Token 爆量。Codex、OpenCode、Antigravity、Claude 與後續工具皆遵守相同 repository-first 規則。

## Memory Pyramid

### Tier 0 — Always-on, tiny
- `AGENTS.md`
- Antigravity `.agents/rules/polynexus-core.md`

只放不常變、必須永遠遵守的規則。工具專屬 rule 應保持 thin reference，不複製 repository-level 規則全文。

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

Repository 既有 source-of-truth declarations 已足夠；不新增 `PROJECT.yaml`、Context Manifest、第二套 shared memory 或 automatic AI memory domain。正式跨機狀態來自 approved remote Git checkpoint；Handoff 只是導航，conversation/AI memory 不得替代 Git repository。

## Evidence Memory

AI conclusion 與 deterministic result 分開。長 test log 不直接放 Handoff，只記 command、exit code、failure names、artifact path/hash。

## Token Guard

- 不把完整 conversation export 當開發 context。
- 不在 AGENTS.md 複製 PRD/SA/SD。
- Skills 採 progressive disclosure。
- 每輪 bootstrap 限於 `AGENTS.md`、Project State、Current Handoff、task doc 與直接相關的 1–3 份規格／程式檔；由 diff、failure、call chain 或 acceptance criteria 決定是否擴讀。
- 同一 task/session 中未變更的大型文件不重讀全文；使用 file/section/symbol/commit/artifact reference。
- Writer contract-first；Reviewer diff-first；Browser verifier route/fixture-first；文件整理與 second opinion 使用 `references + current delta`。
- 不讓 Codex、OpenCode、Antigravity、Claude 依序重做相同 full-repo analysis、完整測試或完整方案。切換工具不等於 evidence 自動失效。
- Machine-filter logs before AI；長 log 只帶 command、actual exit code、summary、failure names、必要錯誤片段與 artifact path/hash。
- Routine work 使用足夠完成任務的較低成本模型；architecture、security、high-coupling contract、hard root cause、critical acceptance 才升級高推理模型。
- 到達 acceptance、blocker、Human decision 或 stop condition 即停止，不把剩餘 token 用於未授權的延伸改善。
- Handoff 保持 current operational state + current delta + next routing，不累積完整專案歷史。

### Lossless Context Boundary

任何 summarization、token reduction、context optimization、handoff compression 或 memory compression，都不得遺失、弱化或改寫：

- Acceptance Criteria
- deterministic Evidence 與 acceptance 所依賴的 deterministic result
- Findings
- ADR 與 Policy
- Human Decision
- verification command 與 actual exit code

若 context 必須縮短，優先保留 authoritative file/artifact references 與 current delta；不得用 AI 摘要取代 authoritative material，也不得把 `SKIPPED`、`UNVERIFIED`、歷史結果或環境 blocker 壓縮成 `PASS`。

## Future Personal Memory

V1 先做 deterministic project memory：facts、decisions、run summary、artifact refs、handoff。Semantic/vector auto-memory 後續再做，避免 V1 被 RAG 選型綁死。
