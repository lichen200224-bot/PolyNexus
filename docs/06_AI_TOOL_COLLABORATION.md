# Codex + OpenCode + Antigravity Collaboration Plan

## 1. Roles

### Codex — Architecture / Core Owner
負責：Scope/ADR、Domain、Contracts、Workflow state machine、Evidence/Policy、hard bug、critical review。

### OpenCode — Implementation / Test Workhorse
負責：依已確認 Contract 做大量實作、fixtures、unit/conformance tests、templates、routine refactor、docs sync。

### Antigravity — Browser / E2E / Milestone Red Team
負責：Web Companion、UI journey、browser E2E、failure path、milestone independent verification。

## 2. Token-aware Escalation

1. Deterministic tools first。
2. Routine implementation → OpenCode。
3. Architecture/high-coupling/hard root cause → Codex。
4. Browser/E2E only when needed → Antigravity。
5. 三工具共同檢查只在 Milestone / RC。

## 3. Task Pattern

### Core architecture task
Codex Design → Codex/assigned writer Implement → OpenCode targeted tests/review → deterministic evidence。

### Routine feature
OpenCode Implement + Test → Codex diff-only review if high impact。

### Browser feature
Codex defines boundary → OpenCode driver/support code → Antigravity E2E。

### RC
Codex critical review + OpenCode regression + Antigravity user journey → deterministic acceptance。

## 4. Context Budget

每個 Agent 只取得：Current Handoff + relevant spec + relevant files + diff + failing test excerpt。
禁止三套工具依序做 full-repo analysis。

## 5. Ownership Rule

Architecture conflict 回 Codex/人員裁決；OpenCode / Antigravity 不得在驗證途中自行重寫核心 Contract。

最終產品／範圍決策由人決定；AI 建議不自動變更 Scope Baseline。
