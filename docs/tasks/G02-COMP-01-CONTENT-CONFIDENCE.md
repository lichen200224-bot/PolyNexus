# G02-COMP-01-CONTENT-CONFIDENCE

## Task metadata

- `TASK_ID`: `G02-COMP-01-CONTENT-CONFIDENCE`
- `ATTEMPT`: `1`
- `Status`: `G02_HUMAN_APPROVED / G03_DECISION_REQUIRED / INDEPENDENT_REVIEW_NO_BLOCKER`
- `Goal`: complete the Cyber4.0 2026 initial-review proposal/deck content-confidence gate and stop at Human final content decision.
- `Branch`: `feature/first-vertical-slice`
- `HEAD at task start`: `77b1b4b4d36e855dc24f0da07b6f69da2cee03d6`
- `Writer`: Codex — competition content/document delta only
- `Reviewer`: fresh independent Codex, read-only; Writer != Reviewer
- `Antigravity`: `NOT_REQUIRED` for product UI/browser journey; official browser access was attempted as an evidence path but no browser artifact was obtained.
- `Next owner`: Human to decide whether to route G03; this approval does not start G03 or authorize live-form access.
- `G01 prerequisite`: repository records the G01 document/runtime state reconciliation and its clean-clone checkpoint in `docs/11_PROJECT_STATE.md` and the current operational block of `docs/12_HANDOFF_CURRENT.md`. G02 does not create a new G01 acceptance or infer approval beyond those records.

## Scope and exact allowlist

### In scope

- Build a complete repository source-to-claim matrix.
- Correct proposal/deck source wording so `Implemented`, `In Development`, `Planned V1`, and `Future` are explicit and bounded.
- Record the current official-requirements lookup result, including source conflicts and inaccessible/unverified fields.
- Update the existing proposal DOCX in place as the content-confidence draft; do not create a competing formal version.
- Run structural checks, render-capability checks, diff/ownership checks, and obtain an independent read-only review.

### G02 changed-file allowlist

- `docs/tasks/G02-COMP-01-CONTENT-CONFIDENCE.md`
- `competition/G02_SOURCE_TO_CLAIM_MATRIX.md`
- `competition/PROPOSAL_SOURCE.md`
- `docs/13_COMPETITION_SUBMISSION_PLAN.md`
- `docs/14_COMPETITION_SLIDE_OUTLINE.md`
- `competition/PolyNexus_Cyber4_Initial_Proposal_Draft_v0.2.docx`
- `docs/12_HANDOFF_CURRENT.md` — current operational block only; legacy history below `## Legacy History — Reference Only` is protected.

### Protected / excluded

- Existing dirty paths at task start: `docs/15_DOCUMENT_INDEX.md`, `docs/tasks/WP-12.md`, `services/core/src/polynexus_core/runtime/contracts.py`, `services/core/src/polynexus_core/runtime/registry.py`, `docs/tasks/RUNTIME-ADAPTER-CONFORMANCE.md`, `docs/tasks/WP-14.md`, `services/core/src/polynexus_core/runtime/codex.py`, `services/core/tests/test_runtime_registry_conformance.py`, `services/core/tests/test_wp14_codex_runtime.py`.
- Additional untracked paths observed during the task and preserved outside G02 ownership: `competition/PolyNexus_預期功能簡報_v1.pptx`, `competition/PolyNexus_預期功能簡報說明_v1.md`, `scripts/gen_expected_ppt.py`.
- All product source, runtime source, runtime tests, migrations, lockfiles, secrets, `.env`, CI/CD, deployment configuration, WP-16 files, and unrelated worktrees.
- No stage, commit, push, merge, cherry-pick, reset, rebase, clean, delete, Git-history change, login, form fill, upload, or submission.

## Truth and maturity rules

1. `IMPLEMENTED` means only the bounded capability supported by the cited repository evidence. It does not mean full V1 or production integration.
2. `IN_DEVELOPMENT` includes separate runtime/browser implementation work and verification boundaries that are not accepted as current product support.
3. `PLANNED_V1` means a documented target without sufficient current implementation evidence.
4. `FUTURE` means outside the current V1 baseline.
5. Historical test counts and prior checkpoint results remain historical/checkpoint evidence unless this task reruns them; they cannot be silently converted to G02 PASS.
6. `SKIPPED`, `UNVERIFIED`, environment failure, and unavailable official sources remain explicit.
7. D11 Option C remains fail closed: arbitrary `Evidence.actor_id` cannot prove a Human; unverified approval remains `HUMAN_DECISION`／`NEED_ACTION`.

## Official-requirements check

Target: <https://ai-challenge-2026.cybersoft.tw/>; check date `2026-08-27` (Asia/Taipei).

The official homepage was retrieved on 2026-08-27 with Node `fetch` (HTTP `200`) and identified as `2026 Cyber4.0 AI創新競賽`; it exposes the initial-review form link, the organizer, four deliverables, and `50/30/20` scoring. The linked official brief was also retrieved (HTTP `200`, DOCX, `43640` bytes; cover date `中華民國115年6月`) and states the initial-review document deadline `2026.08.31`, proposal/deck `20 頁` limits, proposal formatting rules, and initial-review Demo `3 分鐘內或截圖`. The homepage states Demo `5–10 分鐘` and separately lists an `效益說明表`, so those requirements remain `OFFICIAL_CONFLICT / NEED_ACTION`; current form fields, file size/naming, and announcement overrides remain `[待驗證]`. The repository `2026-09-07` date is internal historical planning only. No login, form fill, upload, or send was performed.

The complete record is in `competition/G02_SOURCE_TO_CLAIM_MATRIX.md`, section **Official requirement verification**.

## Evidence collected before editing

- `git status --short --branch`: exit `0`; branch `feature/first-vertical-slice`; 4 modified and 5 untracked pre-existing paths listed above.
- `git rev-parse HEAD`: exit `0`; `77b1b4b4d36e855dc24f0da07b6f69da2cee03d6`.
- `git remote -v`: exit `0`; only local `backup` and `baseline` remotes were configured; no GitHub status was inferred.
- `git diff --name-status`: exit `0`; G02 changed-document paths were tracked separately from the preserved prior project-content and foreign dirty paths.
- `git diff --cached --name-status`: exit `0`; empty at task start.
- `git ls-files --others --exclude-standard`: exit `0`; only the 5 pre-existing untracked paths.
- `Resolve-DnsName ai-challenge-2026.cybersoft.tw`: exit `0`; DNS resolved.
- PowerShell `Invoke-WebRequest -UseBasicParsing https://ai-challenge-2026.cybersoft.tw/`: exit `1`; `基礎連接已關閉: 接收時發生未預期的錯誤`.
- `rg --files`: unavailable in this Windows environment (exit `1`); PowerShell `Get-ChildItem`/`Select-String` fallback was used.
- Bundled workspace runtime discovery: no bundled runtime configured.
- Controlled Python process attempt: exit `1`, process creation failure; no system Python or dependency installation was used.
- Canonical `render_docx.py` attempt via `C:\Windows\py.exe -3 -B`: exit `112`, output `No installed Python found!`; no page images were produced.
- LibreOffice/`soffice`: unavailable; canonical DOCX rendered-page visual QA remains `[待驗證]`; a prior hidden read-only Word COM check confirmed page count `8`, while the current COM recheck hit the Windows logon-session error recorded below.
- Preliminary DOCX marker check: exit `1`; its predicates incorrectly inspected only direct body paragraphs and required underscore/percent marker spellings that are not the document's actual wording. No DOCX edit was made in response to that checker result.
- Corrected current DOCX structural check: exit `0`; `word/document.xml` parsed successfully, all 18 ZIP entries were read, 134 body paragraphs were found (86 direct body paragraphs plus 48 table paragraphs), 2 tables were found, all required v0.3/matrix/maturity/official-conflict markers were present, and the tested stale positive-claim strings were absent.
- Node official homepage fetch: exit `0`; HTTP `200`, final URL unchanged, HTML length `167140`, SHA-256 `F1FDCA69B4B98A6DC3F9E8FF9D2A55A46D8D99EB69D68DBE6649172A9538CEC7`, H1 `2026 Cyber4.0 AI創新競賽` (HTML whitespace normalized by the extractor); form URL and brief link extracted.
- Node official brief fetch: exit `0`; HTTP `200`, DOCX content type, `43640` bytes; read-only `ZipArchive`/OOXML extraction: exit `0`; using a 1-based enumeration of all `//w:body//w:p` nodes, eligibility/deliverables were found at P078–P082, schedule at P140–P154, scoring at P176–P189, and Attachment 1 fields plus Attachment 2 format/content at P242–P308. SHA-256: `EFBB80A1F8D86CD3E496DF633D80F7BB2B5B08A139F1477AD31E8D9509CD8A42`.

- Prior hidden read-only Word COM page-count check: exit `0`; `page_count=8`. Prior Word PDF export: exit `0`; temporary PDF `236461` bytes. Current Word COM recheck: exit `1`; Windows returned `80070520 A specified logon session does not exist. It may already have been terminated.` No DOCX write occurred. Edge headless screenshot attempt produced no PNG; Word page-image fallback: exit `1`, `Clipboard image unavailable for page 1`. Windows `Windows.Data.Pdf` fallback rendered all `8` pages to PNG with exit `0`; the corresponding unchanged DOCX pages were visually inspected with no clipping, overlap, black-square, or unreadable-text defect found. This is a fallback visual-QA PASS, not a canonical `render_docx.py` run.

## Required evidence and acceptance criteria

- Matrix contains every proposal/deck product claim with evidence, maturity, limitation, and correction.
- Official requirements retain URL, check date, retrieval status, source conflicts, and `[待驗證]` where the live form or current announcement was not inspected.
- Proposal source and slide outline do not use unbounded “completed V1” or “real integration” wording.
- Existing proposal DOCX is updated in place and passes structural OOXML checks; its Word-computed page count and rendered every-page visual QA are recorded honestly.
- `git diff --check` and final status/changed-file ownership checks are run with actual exit codes.
- A fresh independent reviewer checks the G02 allowlist and returns `VERIFIED_PASS`, `NEED_ACTION`, `NEED_FIX`, or `FAIL`; any writer finding requires a direct `FIX_PROMPT` and re-review.
- Human must make the final content decision. Agent result cannot be product acceptance or Git authorization.

## Current known limitations / unverified

- Official homepage and linked brief were reverified on 2026-08-27; live form fields/file constraints, current announcement override, and the homepage-versus-brief Demo/benefit-table conflict remain unresolved.
- DOCX page count is confirmed as `8` by hidden read-only Word COM. Canonical `render_docx.py` remains unavailable because no Python/`pdftoppm` is installed, but Word PDF plus Windows `Windows.Data.Pdf` rendered all 8 pages and the latest PNG inspection found no visual defects; canonical renderer equivalence remains `[待驗證]`.
- Current browser DOM/Playwright E2E, Windows symlink containment, and true concurrent HTTP remain `UNVERIFIED`/`SKIPPED` per current project state.
- Real Codex/OpenCode CLI/network/credential/production integration, Local AI adapters, complete routing policy, full workflow breadth, full backup/restore acceptance, and measured outcome data are not current completion claims.
- The G02 writer does not change any protected dirty source/runtime/test paths.

## Independent review result

Four earlier same-directory Codex reviewer tasks were dispatched: `01a04311-9041-7dd1-a5db-58896968e1d7`, `01a04316-8b1d-72f2-b18c-dc1e9751b747`, `01a04322-36c3-77c3-8542-e3fbe4cd6435`, and `01a04338-30e6-7d80-8172-a75e18ba5133`; all completed without a readable assistant result. A separate fresh G02-only independent review was completed by `01a04366-9b2b-7560-8135-bf0509a79c38`; its result is recorded below.

`REVIEW_RESULT: NEED_ACTION / FINDINGS: NO BLOCKER` — fresh G02-only independent review `01a04366-9b2b-7560-8135-bf0509a79c38` confirmed the 20 product rows, 6 official rows, non-empty product evidence/limitations, maturity boundaries, official-conflict labeling, protected-path ownership, and DOCX structural consistency. Its `NEED_ACTION` result is caused by the unresolved official-source conflict/live-form unknowns, not by a writer defect. The earlier project-content review is not used as G02 acceptance evidence.

`FIX_PROMPT: N/A for the reviewed content delta. The fresh independent review returned `NEED_ACTION / FINDINGS: NO BLOCKER`; remaining official-source conflicts and live-form unknowns are Human/G03 actions, not silently resolved by G02.`

## Current stop state

The fresh G02-only independent review returned `NEED_ACTION / FINDINGS: NO BLOCKER`; the official sources still contain unresolved Demo/benefit-table conflicts and unverified live-form fields. Human decision `APPROVE G02` was received on 2026-08-27 and accepts the bounded content-confidence package within those stated limitations. The safe next routing state is `G03_DECISION_REQUIRED`: this approval does not resolve official conflicts, authorize live-form access, grant product acceptance, or grant Git authorization.

## Expected stop state

The earlier reviewer-delivery blocker is resolved and Human has approved G02. Official Demo/benefit-table conflicts and live-form unknowns remain. Stop at `G03_DECISION_REQUIRED` with the final proposal filename, matrix, maturity counts, official verification result, DOCX QA result, exact changed-file allowlist, limitations, and the following routing decision:

`APPROVE G02` — recorded on 2026-08-27; accept the bounded content-confidence draft without resolving the official conflicts or authorizing G03/live-form access.

`REJECT G02` — historical alternative only; return a reason and a bounded correction request. No Git authorization is implied.

## Human decision

- `Decision`: `APPROVE G02`
- `Date`: `2026-08-27`
- `Scope`: bounded competition content-confidence package, source-to-claim matrix, proposal/deck wording, and existing proposal DOCX.
- Not approved: official Demo/benefit-table conflict resolution, live-form access or submission, product acceptance, G03 execution, stage/commit/push, or any Git-history operation.
- `Next owner`: Human to explicitly decide whether to route G03.

## Next-session prompt (G03; not executed by G02)

> G03 must verify the official Cyber4.0 2026 page, linked brief, current announcement, and actual upload form under the applicable Human authorization. Reconfirm the official-brief schedule (`2026.08.31` initial-review document deadline; `2026.09.01–09.24` initial review), title, publication/update date, page/file limits, required fields, Demo duration, the homepage `5–10` versus brief `3 minutes or screenshots` conflict, and whether the benefit explanation table is a separate file. Compare each requirement against `competition/G02_SOURCE_TO_CLAIM_MATRIX.md`, `competition/PROPOSAL_SOURCE.md`, `docs/13_COMPETITION_SUBMISSION_PLAN.md`, `docs/14_COMPETITION_SLIDE_OUTLINE.md`, and `competition/PolyNexus_Cyber4_Initial_Proposal_Draft_v0.2.docx`. Do not login, fill, upload, send, or submit without separate Human authorization. Preserve all existing dirty paths. Do not change product/runtime/tests/migrations/lockfile/secrets/CI/deployment. Stop at `NEED_ACTION` for inaccessible/conflicting official requirements and request Human decision; do not infer live-form field/size/naming values.
