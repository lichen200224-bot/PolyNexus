# PolyNexus V1 Acceptance Strategy

## 1. Principle

AI Opinion ≠ Evidence。PASS 只認當下真實驗證結果，禁止使用舊 log 或 AI 自述替代。

## 2. Acceptance Layers

### Unit
Domain logic、parser、policy、normalization。

### Contract / Conformance
Runtime/Endpoint/Driver contract semantics。

### Integration
Core ↔ adapter、storage、workflow、browser companion。

### E2E
4 條 Golden Workflow 深度驗收。

### Release
Migration、Backup/Restore、security boundary、packaging、known limitations。

## 3. Four Golden Acceptance Flows

1. Discuss / Council
2. Code / Artifact Review
3. Release Validation
4. Web AI Decision Review

其餘 5 templates 需可運作與 template validation，但不要求同等測試矩陣深度。

## 4. Runtime Conformance Critical Checks

- health/readiness
- stable run ID
- status terminal state
- timeout
- cancel actually stops
- child/tools cleaned
- result/error normalized
- evidence envelope generated
- artifacts traceable
- version/compatibility recorded

Resume 允許 NATIVE / MANAGED / NOT_AVAILABLE，但必須如實 capability 宣告。

## 5. Failure Isolation

任一 Adapter/Web Driver crash 不得使 Core crash；Council 可顯示 partial result / retry。

## 6. Policy Tests

- Restricted / Local-only 不可 silent cloud fallback。
- Highest Classification Wins。
- external egress 前 policy check。
- exception requires audit actor/reason/time。

## 7. Migration Tests

每次 schema migration：backup gate → migrate → verify old data → rollback/restore path documented。

## 8. Evidence Output

每個 Acceptance run 至少記：command、timestamp、exit code、test name/summary、version、artifact ref。長 stdout 放 artifact store，不塞進主報告。
