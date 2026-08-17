# Tooling Bootstrap — Codex / OpenCode / Antigravity

## 1. Shared Skill Directory

三套工具目前都能使用 repo-scoped `.agents/skills/<skill>/SKILL.md`。因此 PolyNexus 不建立三套重複 Skill；只維護一份共用 Skills，減少漂移與 Token 浪費。

Repo skills：
- polynexus-architecture-gate
- polynexus-implement
- polynexus-review
- polynexus-acceptance
- polynexus-handoff

## 2. Persistent Rules

- Codex：`AGENTS.md`
- OpenCode：`AGENTS.md`
- Antigravity：`.agents/rules/polynexus-core.md`

Rules 保持短；詳細規格由 Skill / task 需要時才讀。

## 3. Plugin / MCP Policy for Bootstrap

V1 開發初期不預裝大量第三方 plugins/MCP。原因：
- 供應鏈與權限風險
- 佔用 Agent context/tools list
- 增加 debugging variable

只在有明確任務價值時 allowlist 加入，並記錄：source、version、permissions、network egress、why needed。

Git 本身先使用 local Git CLI，不因「方便」強制導入 GitHub MCP。

## 4. Recommended Skill Use

- Architecture / Contract 變更：`polynexus-architecture-gate`
- 寫 feature：`polynexus-implement`
- 另一工具 read-only review：`polynexus-review`
- milestone / RC：`polynexus-acceptance`
- 工具切換：`polynexus-handoff`

## 5. Antigravity Use

不要讓 Antigravity 成為每個 commit 的固定第三 reviewer。主要保留 quota 給：Browser Companion、UI E2E、full user journey、milestone red team。

## 6. First-day Setup Checklist

- [ ] Extract project starter into final repo folder
- [ ] Run `scripts/bootstrap_git.ps1`
- [ ] Confirm Codex sees AGENTS.md + `.agents/skills`
- [ ] Confirm OpenCode sees AGENTS.md + `.agents/skills`
- [ ] Confirm Antigravity sees `.agents/rules` + `.agents/skills`
- [ ] Run `scripts/preflight.ps1`
- [ ] Human reviews open ADR list
- [ ] ADR-001～010 are frozen; verify baseline before First Vertical Slice coding


## Development Baseline v1.0 additions

Two durable repo skills were added after ADR freeze:
- `polynexus-runtime-conformance`: normalized Runtime Contract/cancel/timeout/cleanup/maturity validation.
- `polynexus-workflow-authoring`: YAML/schema/fixed-node/versioning guardrails.

Do not add external MCP/plugin dependencies during scaffold unless a concrete task cannot be completed with repo-local tools. Every external tool must record source, version, permission/egress surface, and removal/fallback path.
