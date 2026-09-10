# TA-OPERATING-MODEL review and handoff packet

## Identity and scope

GOAL_ID / TASK_ID: TA-OPERATING-MODEL；ATTEMPT: 1；PARENT_WP: DEVELOPMENT_GOVERNANCE；TRACK: Track A V1；EPIC_GOAL: Implementation Operating Model。
TASK_DOC: [Framework](../governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md)；HANDOFF_DOC: [Current Handoff](../12_HANDOFF_CURRENT.md)。
BRANCH: feature/first-vertical-slice；WORKING_HEAD: b87a0dc780e5d9a3bba083dbaf9552ca52508f9a；CANONICAL_DESIGN_READ_SHA: f34e6b29ae9e7326d1d44b9b03756b450809928f。
PREDECESSOR_SHA: UNASSIGNED for implementation；本輪只用已批准設計與既有治理文件規劃。
WRITER: Codex / current governance session；HARNESS: Codex desktop；MODEL: UNKNOWN（Human指派Astra，未有可觀測exact model ID）。
REVIEWER: Human-designated independent ChatGPT Review Context / NOT_RUN。
WRITER_AUTHORIZATION_SOURCE: 2026-09-10 Human Goal input，僅governance/planning/skills/templates；決策已整理於Framework §1–9。
ACTIVE_WRITER_SCOPE: 下列治理文件；delivery後STOP WRITING；ACTIVE_PRODUCT_WRITER: NONE。

REVIEW_CANDIDATE_SHA: NONE — 本輪禁止stage/commit，這是pre-commit文件審查包。不得用b87工作HEAD代表本輪內容，也不宣稱正常exact-SHA Final Review已完成。正式candidate須後續Git授權並review exact SHA。
HANDOFF_STATUS: LOCAL_DOCUMENT_REVIEW_READY / NOT_REMOTE_READY。

## Files created (21)

- [.agents/skills/polynexus-cross-machine-handoff/SKILL.md](../../.agents/skills/polynexus-cross-machine-handoff/SKILL.md)
- [.agents/skills/polynexus-goal-execution/SKILL.md](../../.agents/skills/polynexus-goal-execution/SKILL.md)
- [.agents/skills/polynexus-independent-acceptance/SKILL.md](../../.agents/skills/polynexus-independent-acceptance/SKILL.md)
- [docs/IMPLEMENTATION_CURRENT_GOAL.md](../IMPLEMENTATION_CURRENT_GOAL.md)
- [docs/goals/TA-F1.md](../goals/TA-F1.md)
- [docs/goals/TA-F2.md](../goals/TA-F2.md)
- [docs/goals/TA-F3.md](../goals/TA-F3.md)
- [docs/goals/TA-F4.md](../goals/TA-F4.md)
- [docs/goals/TA-S0-G01.md](../goals/TA-S0-G01.md)
- [docs/goals/TA-S0-G02.md](../goals/TA-S0-G02.md)
- [docs/goals/TA-S0-G03.md](../goals/TA-S0-G03.md)
- [docs/goals/TA-W1-G01.md](../goals/TA-W1-G01.md)
- [docs/goals/TA-W1-G02.md](../goals/TA-W1-G02.md)
- [docs/goals/TA-W1-G03.md](../goals/TA-W1-G03.md)
- [docs/goals/_GOAL_TEMPLATE.md](../goals/_GOAL_TEMPLATE.md)
- [docs/governance/POLYNEXUS_DEVELOPMENT_AGENT_CAPABILITY_MATRIX.md](../governance/POLYNEXUS_DEVELOPMENT_AGENT_CAPABILITY_MATRIX.md)
- [docs/governance/POLYNEXUS_LEGACY_OPEN_WORK_RECONCILIATION.md](../governance/POLYNEXUS_LEGACY_OPEN_WORK_RECONCILIATION.md)
- [docs/governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md](../governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md)
- [docs/handoffs/_HANDOFF_TEMPLATE.md](../handoffs/_HANDOFF_TEMPLATE.md)
- [docs/reviews/TA-OPERATING-MODEL-REVIEW.md](TA-OPERATING-MODEL-REVIEW.md)
- [docs/reviews/_REVIEW_PACKET_TEMPLATE.md](_REVIEW_PACKET_TEMPLATE.md)

## Files modified (16)

- [.agents/rules/polynexus-core.md](../../.agents/rules/polynexus-core.md)
- [.agents/skills/polynexus-acceptance/SKILL.md](../../.agents/skills/polynexus-acceptance/SKILL.md)
- [.agents/skills/polynexus-architecture-gate/SKILL.md](../../.agents/skills/polynexus-architecture-gate/SKILL.md)
- [.agents/skills/polynexus-handoff/SKILL.md](../../.agents/skills/polynexus-handoff/SKILL.md)
- [.agents/skills/polynexus-implement/SKILL.md](../../.agents/skills/polynexus-implement/SKILL.md)
- [.agents/skills/polynexus-review/SKILL.md](../../.agents/skills/polynexus-review/SKILL.md)
- [.agents/skills/polynexus-runtime-conformance/SKILL.md](../../.agents/skills/polynexus-runtime-conformance/SKILL.md)
- [.agents/skills/polynexus-workflow-authoring/SKILL.md](../../.agents/skills/polynexus-workflow-authoring/SKILL.md)
- [AGENTS.md](../../AGENTS.md)
- [docs/05_GIT_WORKFLOW.md](../05_GIT_WORKFLOW.md)
- [docs/06_AI_TOOL_COLLABORATION.md](../06_AI_TOOL_COLLABORATION.md)
- [docs/08_ACCEPTANCE_STRATEGY.md](../08_ACCEPTANCE_STRATEGY.md)
- [docs/11_PROJECT_STATE.md](../11_PROJECT_STATE.md)
- [docs/12_HANDOFF_CURRENT.md](../12_HANDOFF_CURRENT.md)
- [docs/28_MASTER_DEVELOPMENT_ROADMAP.md](../28_MASTER_DEVELOPMENT_ROADMAP.md)
- [docs/GOAL_COMPLETION_CONTROL_PANEL.md](../GOAL_COMPLETION_CONTROL_PANEL.md)

完整本輪清單包含原本untracked的Control Panel，沒有把它錯算新檔。既有dirty/untracked inventory與SHA-256保存於本機外部verification目錄，不把未知profile/data打包進Git。原本tracked+untracked共2,185個檔案，只有以上16個既有治理檔案改動；其餘2,169個hash保持不變。新增檔案另計。

DIFF_SUMMARY: 三份治理主文件、current pointer、F1–F4/S0三Goal/W1三Goal詳細契約、三模板、三新skills；既有AGENTS/七skills/工具pointer與七導航文件對齊Human決策。旧SOP/正式contract/歷史紀錄保留；舊docs內容僅前置override，原body bytes保留。

## Actual verification and environment

本機 verification directory: C:/Users/hikar/.codex/visualizations/2026/09/10/01a088f6-b96b-7ea0-a67b-5719ede663b5/。
此處 before.json、original/、validation.json、git-status-after.txt、intake.cjs、validate.cjs 是local evidence/rollback references，尚非Git portable artifacts。未授權上傳；不得把存在本機當另一台已可讀。

| Actual command / check | Actual exit / result |
|---|---|
| node <verification-directory>/intake.cjs | 0；2,185 existing paths/hashes，2,018 pre-existing dirty/untracked entries，staged empty |
| Git without command-scoped safe.directory (initial probe) | ownership rejected；不作PASS，未改global config |
| git -c safe.directory=<verified-repo> rev-parse HEAD / branch --show-current / branch -vv / remote -v | 0；本輪b87 branch與design baseline分開；remote僅配置read，未fetch/push |
| node <verification-directory>/rules.cjs | 初始1：EPERM；授權範圍內提升後0，套用governance/skills；未變更permissions/config |
| bundled-python -m pip install --disable-pip-version-check --target <verification-directory>/validation-deps PyYAML | 0；6.0.3，只供外部驗證；repo dependencies不變 |
| process-local PYTHONPATH=<verification-directory>/validation-deps; bundled-python -X utf8 <skill-creator>/scripts/quick_validate.py <each .agents/skills directory> | 10/10，各actual exit 0；初次缺yaml的1保留為環境失敗，不冒充首次通過 |
| node <verification-directory>/validate.cjs | 初次1：review packet尚未產生的11個missing links；最終執行結果見下方validation seal |
| git -c safe.directory=<verified-repo> diff --check | 0；既有registry CRLF warning保留，未normalize |
| git -c safe.directory=<verified-repo> diff --stat | 0；是整個dirtytree，不是本輪delta；用before hashes區分 |
| git -c safe.directory=<verified-repo> status --short --untracked-files=all | 0；完整輸出存git-status-after.txt，未把大量profile dump當review packet |
| git -c safe.directory=<verified-repo> diff --cached --binary | 0；index與初始相同且empty |

Exact actual argv/cwd及最終Git輸出存validation.json；上述<...>是可攜定位符，不宣稱literal placeholder已執行。cwd=repo root；腳本以本機已確認safe.directory單次呼叫Git。OS/Git/Node/npm/shell/Python/tool probes與限制见[Capability Matrix](../governance/POLYNEXUS_DEVELOPMENT_AGENT_CAPABILITY_MATRIX.md)。

.gitattributes SHA-256: a704f2107505802586749c1dec8f6a611ad0fb9fd9b07716e119d12783987b0b
apps/web/package-lock.json SHA-256: 56e94b5ad96e3b66c6afbeb6a09f9da58cdff3d582199de080c6d8b7117bdf5f
core.autocrlf=true；PowerShell 7.6.5；Windows 10.0.26200.0；Git 2.45.0.windows.1；Node v22.22.3；npm 10.9.8；bundled Python 3.12.14；Codex CLI 0.153.4。ENV NAMES only: PATH, PATHEXT, PYTHONPATH（validator process only）。Secret values未保存。

## Self-review, negative cases and limitations

以下為Writer文件一致性人工檢查，不是independent verdict或產品negative test：普通bug→bounded repair；NEED_FIX原scope→新SHA/fresh evidence；public contract/trust change→HOLD；第二Writer→HOLD；Reviewer PASS但無Human→DO_NOT_PUSH；WIP→NOT_ACCEPTED/NOT_REVIEWED/DO_NOT_MERGE；remote mismatch→NOT_READY；component A+B→獨立integration C；current S0 authorization→NONE；本輪commit→禁止。對應Framework §§2–6與三skills，規則一致。

FROZEN_INVARIANT_MAPPING: I-01 exactbaseline/dirty保全；I-02/14/15 單Writer/ownership/保全；I-05–11/16 review evidence identity與Human authority僅開發治理類比，產品Candidate/hash/decision原文不改；I-12/13 secret/trust；I-17 durable-source導航不依chat；I-18/19 Git-based handoff非native session；I-20/21 scope及正式sync；I-22 real executor未驗；I-23 S0前置/B01未驗。I-01..I-23來源與原文hash維持不變。

OUT_OF_SCOPE_CHANGE: NONE（以before/after比對，非原始HEAD dirty diff）。ADR_IMPACT: NONE；正式文檔sync NOT_EXECUTED。SCOPE_DEVIATION: NONE。
PROTECTED_AREAS: product source、production tests、schema/migrations、Scope/PRD/SA/SD/Decision Log/Frozen ADR、accepted REV1/Freeze/Work Packages/Change Plan、所有非allowlist dirty/untracked。
PRODUCT_CODE_CHANGED: NO；PRODUCTION_TESTS_CHANGED: NO；SCHEMA_MIGRATION_CHANGED: NO；FORMAL_FROZEN_DOCS_CHANGED: NO。
GIT_STAGE: NO；GIT_COMMIT: NO；GIT_PUSH: NO；HEAD/index不變。

SKIPPED: product tests/real executor/browser/migration/B01（本輪非產品，對文件交付nonblocking，不能證product PASS）；fresh remote/clean clone（本輪未授權Git publication，對cross-machine operational readiness blocking）；independent final review（NEXT gate，blocking acceptance）；exact candidate SHA（本輪禁止commit，blocking normal final acceptance）；完整unknown overlay逐內容盤點（legacy S0前HD-L2 blocking）。
ANTIGRAVITY_STATUS: NOT_REQUIRED — 純治理文件，无UI/product journey claim。
KNOWN_LIMITATIONS: legacy HD-L1/L2/L3需Human disposition，詳[Reconciliation](../governance/POLYNEXUS_LEGACY_OPEN_WORK_RECONCILIATION.md)；新治理目前僅local overlay。OpenCode edit ask/commit deny仍是runtime限制，未修改權限或假裝alternate Writer ready。精確model ID未知，推薦model不是observed readiness。

## New context answer map

| Success questions | Project-local answer |
|---|---|
| 1 authority / 2 frozen | Framework §1 + Freeze Record §3，APPROVED/FROZEN |
| 3 implementation / 4 current Goal / 5 authorized | Current Goal：HOLD / operating model review / implementation NONE |
| 6 active writer / 7 SHA / 8 branch / 9 files | Current Goal + 本packet：本輪Codex治理scope delivery後stop；product predecessor/branch/files NONE；b87僅工作位置、f34設計來源 |
| 10 invariants / 11 tests/evidence | Freeze Record原文；各Goal正負criteria＋templates；目前產品全部未執行 |
| 12 autonomy / 13 HOLD | Framework §3 |
| 14 candidate / 15 independent reviewer | Framework §4 + Review template；本輪no-commit例外明示 |
| 16 push authority / 17 remote verify | Framework §5 Human exact SHA批准、ls-remote match |
| 18 machine transfer / 19 WIP vs accepted | Framework §6 + Handoff template |
| 20 parallel / 21 integration | Framework §6，上限2非架構、未授權batch、A+B需C |
| 22 next | Independent operating model review → accepted後F1授權；不啟動S0 |

## Routing and stop

NEXT_ACTION: INDEPENDENT_REVIEW_REQUIRED；NEXT_OWNER: Human-designated independent ChatGPT Review Context。
NEXT_PROMPT: Review this governance-only file set, hashes and preservation evidence against the 22-question map and Frozen sources. Report PASS/NEED_FIX/HOLD plus DO_NOT_PUSH unless exact-SHA review and Human authorization exist. Do not implement product, formal sync, or invoke another Writer.
STOP_CONDITION: 本輪文件交付與self verification後STOP WRITING；不stage/commit/push，不執行F1或S0。NEXT_PROMPT不是delegation permission。
ROLLBACK: 使用外部original/檔案比對，只回退本輪added prefix/explicit edits及可確認本輪新檔；有後續Human edits先merge保全。不得reset/clean、覆蓋整個dirtytree或刪未知untracked。
PUSH_RECOMMENDATION: DO_NOT_PUSH；INDEPENDENT_VERDICT: NOT_RUN。

## Validation seal

Writer document checks: PASS at 2026-09-10T01:56:59.480Z; node validate.cjs actual exit 0; 189 local links valid; 21 created / 16 modified; 2169 other existing file hashes unchanged; HEAD/branch/index unchanged. This is not independent acceptance. Final packet hash is recorded externally in validation.json to avoid self-reference.

### Delivered file identities (SHA-256; excluding this attestation)

| File | SHA-256 |
|---|---|
| `.agents/skills/polynexus-cross-machine-handoff/SKILL.md` | `8d4b485d7bce673f58b65892c68fb80d8d5221f6c07a6f6bcdae5844248a6fc3` |
| `.agents/skills/polynexus-goal-execution/SKILL.md` | `8db6488f17961a647b5a3a0aeade835c01db453dfc276dec517facd4343100f4` |
| `.agents/skills/polynexus-independent-acceptance/SKILL.md` | `a4d38b50752da053f7056b3b9b270a669c2a909772db77f3a15ff87e32aeb6b2` |
| `docs/IMPLEMENTATION_CURRENT_GOAL.md` | `490abd2012923b4ac9418eb06daa0602423aefa0cd6cbf3b9384941b26199721` |
| `docs/goals/TA-F1.md` | `2ae978dd5cddfc8a7c239b9ab5b0a3c0640c8df8db6825218d189e25a9e9a1e6` |
| `docs/goals/TA-F2.md` | `cf0a6bdff69abd47b125adf7421e9fb1fda8ad16a4996243f162439f13c9e587` |
| `docs/goals/TA-F3.md` | `5f4a4be9a8b187ef6abb62079cf401577042ae52b3962924bf2e18cea82f0701` |
| `docs/goals/TA-F4.md` | `aa930b6a585b8500a3d96b8ce861b316c55e65693943ff5994bd5951b7085dc3` |
| `docs/goals/TA-S0-G01.md` | `1ceaf3e84bcc56bb40339479c028e6e4ab37bcecffbce850a238b7898ed0d3e7` |
| `docs/goals/TA-S0-G02.md` | `303838d868c37aa5c6015f9aef9fcb27b208bd2e1d360beed177b25623fca8f1` |
| `docs/goals/TA-S0-G03.md` | `c8fb80c218599de2d1f34f46b5bf7bf908412aa87a74d155067c4d4d5a9a9b4f` |
| `docs/goals/TA-W1-G01.md` | `2802afa177c652f95559b65a174c072d8fc94448176b1cf119d94ea25370847d` |
| `docs/goals/TA-W1-G02.md` | `40f4eee35d63285b3dbb92ab95e35156a58c7633b3d5c75ed8faa225678763c3` |
| `docs/goals/TA-W1-G03.md` | `f26c18bfc0098d3bfd3dfa2f69a078d32be5792ef08913a9203b82121b64fb3d` |
| `docs/goals/_GOAL_TEMPLATE.md` | `2ce6bc44a7199502e1c7db3fb1ca4936dfa62934b3081e1a5d40b2ce4d4acfd2` |
| `docs/governance/POLYNEXUS_DEVELOPMENT_AGENT_CAPABILITY_MATRIX.md` | `8ea0d988393e0cb36a635de862748eb74b536b5e5181f9b571cc26c0515d703b` |
| `docs/governance/POLYNEXUS_LEGACY_OPEN_WORK_RECONCILIATION.md` | `8611f4a8b4076c21606fdc31111cfa444c906ae81d0770520e244103d4ce568e` |
| `docs/governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md` | `ae304ef1e6c5b7d07443ff96ce636802fc11da61a7e89160e97b1c1114fabd01` |
| `docs/handoffs/_HANDOFF_TEMPLATE.md` | `b6e03b042972bcc270782fe0cc40b37e77ca6d1783dd07edab40cc700a42616b` |
| `docs/reviews/_REVIEW_PACKET_TEMPLATE.md` | `e718864b0f67517a75d5e98d0f3112ad937e28a743c32d187acca224ae479ef4` |
| `docs/GOAL_COMPLETION_CONTROL_PANEL.md` | `32edd1f70578c390bd3b1fdee1f4974d4531b4787716b4bac71ca1960942ecae` |
| `.agents/rules/polynexus-core.md` | `6aa713e24d3274615099a1de4d86130cc00240aa58bca9d0abb336869a27dd41` |
| `.agents/skills/polynexus-acceptance/SKILL.md` | `8b57f567a109f994989f48cdb70c7fa124f50b1a68a3e19d3208f072005bb527` |
| `.agents/skills/polynexus-architecture-gate/SKILL.md` | `eed6053994983233b528f46ffe2d080e2016e87bb2800f2ed901c80e487a300a` |
| `.agents/skills/polynexus-handoff/SKILL.md` | `f78e36b054f3b8cbd8bb40d92cd2080c21b81d9c62f044e6849a10403c81671f` |
| `.agents/skills/polynexus-implement/SKILL.md` | `e72d33d2199b02d907c261dcdfe84f771812da5f7771714735e1ae0646d1bdfc` |
| `.agents/skills/polynexus-review/SKILL.md` | `fafc65c7fe6863ceca472f7021e829177a0043ca1cae5bc43bcd66965f67b14d` |
| `.agents/skills/polynexus-runtime-conformance/SKILL.md` | `00b3be3aa6cac4d20703ab4134583f7cb96e4a9bb1589b76a9ad417ff34821df` |
| `.agents/skills/polynexus-workflow-authoring/SKILL.md` | `6fce636553b2fa35f106191f9c2750de10a11633e4e00a13d3dac91536e6c226` |
| `AGENTS.md` | `448ecaeb8313cee0c2519d156a8a0c49f31ee15450a1404d8b47559be4139b8b` |
| `docs/05_GIT_WORKFLOW.md` | `0f4518f2fe47396678ae8791acbecd8cb774a1966751b7465e251ef4ee043f68` |
| `docs/06_AI_TOOL_COLLABORATION.md` | `1655ab9dfeebbbdd4855819357a5280cd0e35ce0409e2f848e62c92175333940` |
| `docs/08_ACCEPTANCE_STRATEGY.md` | `90f29a1901ddcdf351ef68ad783cac0ae0af2b2befd7ba41a741f0f02d98dde2` |
| `docs/11_PROJECT_STATE.md` | `7424f6b84b0cabb3327bc4c7d5ee6e3ac97a531eb7b1502133eb143d577b1d60` |
| `docs/12_HANDOFF_CURRENT.md` | `79638d55cb8b53da393487e17e6d0f14d4f15e8b6284b122c259c364972a7927` |
| `docs/28_MASTER_DEVELOPMENT_ROADMAP.md` | `1a359c260dab43c87c43cbf84f64449cb91960a1903d82272f65b85ac72fc174` |
