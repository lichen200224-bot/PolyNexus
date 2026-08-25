# PolyNexus Risk Register v1.0

| ID | Risk | Severity | V1 Control |
|---|---|---:|---|
| R01 | Runtime/Version integration matrix explosion | High | Certified matrix + Doctor + Conformance + maturity status |
| R02 | Web AI UI/DOM/login changes | High | Thin WebSurface driver + Level 3A + manual fallback + failure isolation |
| R03 | UX becomes technical control panel | High | Discuss/Review/Validate first, progressive disclosure |
| R04 | Scope expands into enterprise platform before V1 usable | High | CORE/BASELINE/COMPATIBILITY/FUTURE + feature freeze |
| R05 | Three AI dev tools overwrite same work | High | Single Active Writer + Git + delta handoff |
| R06 | Token/quota exhausted by repeated repo reading | High | Memory pyramid + skills + diff review + task routing |
| R07 | AI consensus mistaken for truth | High | Evidence types + hard gates + assurance status |
| R08 | Local AI silently egresses via tools/connectors | High | Route-level policy, not model-only label |
| R09 | Context grows without bound | Medium | ContextPackage/version/source snapshot; future selection/compression |
| R10 | Artifact/log storage grows | Medium | DB metadata + filesystem artifact store + future retention |
| R11 | Schema changes make old workspace unusable | High | schema_version + migration runner + backup before migration |
| R12 | Third-party plugin/MCP supply-chain risk | High | V1 no marketplace; extension source/version/permission metadata |
| R13 | Multi-AI call cost/latency grows | Medium | max agents/rounds/parallelism/timeout; usage metrics |
| R14 | Single maintainer burden | High | standards/adapters/templates; time-to-integrate KPI |
| R15 | Competition rules change | High | verify upload form & latest official announcement before final submission |
| R16 | Demo-only code creates long-term technical debt | Medium | competition uses same product Golden Path; no separate demo architecture |
| R17 | NEXT_PROMPT 被誤當 recursive delegation permission | High | One-Hop Guard；每次跨 Runtime 重新形成 Routing Decision |
| R18 | 壓縮／摘要遺失 acceptance 或 deterministic evidence | High | Lossless Context Boundary + references/current delta |
| R19 | Local backup 被誤稱正式跨機 source | High | local checkpoint remote 與 GitHub/shared remote 分離；clean-clone gate |
| R20 | Dirty tree 或 staged contamination 混入 checkpoint | High | read-only preflight + explicit staged-file allowlist + independent acceptance |
| R21 | GitHub 被寫死成 Product Core dependency | High | Communication Contract First；GitHub 僅為 development collaboration infrastructure |
| R22 | 未驗證 Human decision 被自動推進 | Critical | D11 Option C fail closed；trusted-human architecture deferred |

## Top 3 Continuous Watch
1. Web AI stability
2. Integration/version matrix
3. UX complexity / product usability

## Governance Deferrals / Do Not Add

下列項目不由本 Governance/Documentation patch 施工；既有 Scope Baseline／roadmap 責任不因此取消。未來只能由 Human-approved Architecture Gate／product task 明確啟動：trusted Human authentication/attestation、persisted Runtime Binding、Runtime Registry/Factory、generic idempotency key、Routing Envelope、crash reconciler、full normalized error taxonomy、Backup/Restore implementation、Doctor/conformance implementation、global cost/resource router、retry ceiling implementation、retention worker、MCP、A2A、OmniRoute、LiteLLM、OpenRouter 與 distributed architecture。

不得新增第二套或重複 abstraction：Attempt Domain、`Run == Attempt` frozen rule、persisted TaskPacket/ResultPacket Domain、RoutingEnvelope Domain、RuntimeBindingSnapshot entity、Runtime Selection Metadata second model、Prompt Domain、Context Manifest、`PROJECT.yaml`、second Memory Domain、Provider Gateway、skill registry、skill drift script、distributed queue/lease/heartbeat/scheduler、parallel writers、full BPM、arbitrary Workflow DSL、universal Agent API、automatic shared memory、prompt compression engine、GitHub mandatory Product dependency 或 Google Drive mandatory dependency。
