# V1 Known Limitations

## Current BASELINE-DEBT-01 acceptance boundary — 2026-09-12

- `BASELINE-DEBT-01=FINAL_ACCEPTED`; `BASELINE_DEBT=CLOSED` for the accepted
  deterministic lifecycle ordering and cancellation-cleanup scope.
- Accepted frozen functional anchor:
  `aac597579ee6d369007343930d3a5b3ca7b929c5`; functional baseline
  `86d5939044c1d7ec2a991820f39287481ee9120f`; publication-rejected Candidate
  `180432d03f6d423bb3152c233fb4f0a5072868f5`.
- Independent re-acceptance and publication integrity passed; freeze hashes are
  `20/20`. Full Core is `818 passed / 0 failed / 1 existing Windows
  symlink-policy skip / exit 0`.
- This closure does not add G24–G30 points or remove other limitations:
  `V1_BOUNDED_DEVELOPMENT_ACCEPTANCE_SCORE=95/100`,
  `OVERALL_PROJECT_COMPLETION=NOT_DEFINED`, `WP20=NOT_COMPLETE`, and
  `G30=NEED_ACTION` remain current.
- Dynamic Plugin Platform, external-runtime integration, live vendor
  verification and production readiness remain outside this acceptance.
- `MERGE_AUTHORIZATION=NOT_GRANTED`; `PROMOTION_AUTHORIZATION=NOT_GRANTED`.

## Historical MCF-01 acceptance with pre-existing baseline debt — 2026-09-12 (superseded for BASELINE-DEBT-01 current state)

The following bullets retain the state at the MCF-01 checkpoint. They are
historical and do not override the current BASELINE-DEBT-01 closure above.

- Human decision: `MCF01_DECISION=ACCEPT_WITH_PRE_EXISTING_BASELINE_DEBT`; 僅限 MCF-01 bounded implementation，不是全域 differential acceptance，也不是 release/production readiness。
- `DIFFERENTIAL_REGRESSION=PASS`；`REGRESSION_SUITE_STATE=FAIL`；`FULL_CORE_REGRESSION=FAIL`；reason `PRE_EXISTING_BASELINE_REGRESSION_DEBT`。保留所有非零 exit code 與 Windows symlink skip。
- P1 follow-up: [BASELINE-DEBT-01](tasks/BASELINE-DEBT-01.md)：durable lifecycle event deterministic total ordering，以及 timeout/cancel/cleanup deterministic verification；不得靠放寬 assertion、retry 或任意提高 sleep 掩蓋。
- 在該 task 完成且 Fresh Independent Review 通過前，禁止 holaOS/OpenHands production integration、dynamic plugin platform、MCF-02 external-runtime integration 及 Module Architecture production-ready promotion。僅可文件規劃/research，無 production support claim。
- Module 層維持 static built-in、NO_CONFIG、EXPERIMENTAL；TOOL/SURFACE/INTEGRATION 僅 descriptor vocabulary。沒有 live vendor verification。
- `G30=NEED_ACTION`; `WP20=NOT_COMPLETE`; `V1_BOUNDED_DEVELOPMENT_ACCEPTANCE_SCORE=95/100`; `OVERALL_PROJECT_COMPLETION=NOT_DEFINED`。MCF-01 與 BASELINE-DEBT-01 不加分。
- MCF-01 checkpoint committed and pushed: `96ae53537e5501f1ef374182e7e1966b921a7883`。Remote exact SHA verified；clean-clone verification passed（focused 50/50, exit 0；baseline/governance validators exit 0）。
- `BASELINE_DEBT=OPEN`; `BASELINE-DEBT-01=IMPLEMENTATION_NOT_STARTED`。本次 docs-only state sync 已依 exact allowlist staged，尚未 commit/push，等待 `HUMAN_DOC_GIT_GATE`。
- Acceptance provenance 與原始結果見 [MCF-01 task](tasks/ARCH-MODULAR-CORE-01.md#current-human-acceptance--2026-09-12)；不覆寫下列歷史紀錄。


## G28 candidate limitations — 2026-09-03

- Browser evidence is a local Vite app with an in-page deterministic fetch
  fixture. It is not live vendor, authenticated, native MV3, or certification
  evidence; those remain deferred to G29.
- Core regression evidence covers the four canonical Golden Workflow paths and
  affected failure/cleanup/resource/metric/loader suites. Full Core is not
  rerun as a G28 gate because no Core contract or persistence behavior changed.
- No automatic external send, credential, cookie, token, cloud fallback, or raw
  server error detail is used or retained.

These limitations are intentional boundaries, not hidden compatibility
claims.

## G26 current candidate limitations — 2026-09-03

- G26 targeted Core pytest is now verified at 14/14 and the combined API/local
  routing regression at 29/29, both exit `0`. Full Core regression exits `1`
  with existing persistence/lifecycle/council/resource-guard failures. Web
  Vitest and the production build are verified at 80/80 and exit `0`.
- Local endpoint cancellation and remote cleanup remain conservatively
  unverified: an already accepted synchronous HTTP request cannot be safely
  terminated by this adapter, so its capability remains false.
- LM Studio, Ollama, and generic OpenAI-compatible checks use controlled
  fixtures only; no live vendor certification or cloud fallback is claimed.
- WebSurface drivers remain `PREVIEW`; live authenticated vendor journeys,
  native MV3 dispatch, credentials/cookies/tokens, and external send remain
  deferred to G29.
- G26 is Human-accepted at bounded internal scope with score delta `+12/12`.
  The full Core regression has unrelated exit-`1` failures outside WP-17/18/19;
  those failures remain visible and are not relabeled as G26 failures.

## G24 current reconciliation boundary — 2026-09-02

- G24 records existing limitations and unverified boundaries; it removes none.
- `G24_OUTPUT_SHA=61cc7420e290cd93eda787c30b54a93edf4ca9a`,
  `G24_STATUS=HUMAN_ACCEPTED / PASS / COMPLETE`, and score remains `59/100`.
- Source/test presence for later WPs remains unaccepted until WP-level review,
  Human acceptance, exact checkpoint, and clean-clone evidence.

## Planned limitation-resolution routing — 2026-09-02

- The Human-confirmed G24–G30 plan does not itself remove any limitation.
- Deterministic/internal gaps are addressed before external work: G25 covers
  Runtime adapters/Doctor; G26 local/policy/WebSurface; G27 workflows/guards/
  metrics; G28 UX/Golden Workflow regression.
- Authenticated ChatGPT/Claude/Gemini verification is intentionally delayed to
  G29 because it requires Human operation. The external operator plan forbids
  credential/cookie/token capture and automatic send, and requires a structured
  result for each vendor and failure path.
- Formal development progress is `72/100`. Competition work is
  `NOTE_ONLY_NON_SCORING` and does not create a product limitation or reduce the
  development score.

## G25 current candidate limitations — 2026-09-02

- WP-14 and WP-15 are deterministic local adapter implementations with
  `EXPERIMENTAL` maturity. Their tests use controlled in-process fixtures; no
  live Codex/OpenCode CLI, account, network, or vendor session was used.
- WP-16 Doctor reports declarations and observations conservatively. It cannot
  establish production support, certification, live vendor compatibility, or
  authenticated readiness from local fixtures alone.
- The Registry observation factory is intentionally private and separate from
  execution-time compatibility validation. It exists so Doctor can report a
  capability/auth declaration failure without changing normal execution
  selection.
- A legacy Doctor compatibility module preserves the accepted G18 public API
  while the new runtime Doctor report is introduced. This is a bounded
  integration seam, not a second execution identity or a second Run model.
- Human authorized `G25_DECISION=ACCEPT_AND_COMMIT_PUSH`; WP-14/15/16 are
  checkpointed at `f4168c31592ac5c886b49d8878f60b99016fdcaf` with exact remote
  and clean-clone evidence, earning `+13`. The required independent read-only review returned
  PASS with no BLOCKER, MAJOR, or MINOR findings. Governance validation now
  passes with the system Windows PowerShell validator, exit `0`; the earlier bundled
  PowerShell Core module failure is retained as a historical environment
  result.

## Current RC status — 2026-09-02 (G23 Human-accepted bounded closeout)

G23 is `HUMAN_ACCEPTED / PASS / COMPLETE` at exact SHA
`0eb56a986e97a45854bd6ddd419c114845ce51f4`. The Human accepted the disclosed
bounded G19–G22 evidence and cross-machine delivery checkpoint; this does not
remove or waive any limitation below. Formal project progress is `72/100` under
the Human-directed G23 checkpoint allocation; the remaining 41 points retain the
unaccepted product and live-integration gaps.

### Active residual limitations

- CP04 WP21 is `PASS` only for the controlled synthetic-host real Chrome/CDP
  fixture: 3/3 golden journeys and 28/28 failure paths passed. This does not
  certify live vendor behavior.
- CP06/RC is `PROVISIONALLY_ACCEPTED_WITH_LIMITATIONS` by explicit Human
  decision; current evidence does not certify browser/vendor compatibility and
  must not be upgraded to `SUPPORTED` or `CERTIFIED`.
- G21 independent review found an encoded-loopback traversal gap; G22 adds the
  raw percent-encoded separator guard and regression coverage. Live vendor
  browser acceptance remains deferred/unverified.

- Real ChatGPT, Claude, Gemini, and other vendor browser journeys are
  `UNVERIFIED`; vendor DOM behavior is not certified.
- Browser failure-path acceptance remains dependent on a real browser
  runtime and manual confirmation where required. Automatic send is not
  allowed.
- No vendor login, credential, cookie, token, or external send was used; no
  browser profile was retained. The fixture uses vendor-shaped local pages only.
- G21 `npm ci` was blocked by environment permissions/registry access; that is
  historical G21 evidence. G22 clean dependency restore in this isolated lane
  passed under approved elevation, followed by Web Vitest `80/80` and production
  build exit `0`.
- A fresh G22 browser harness rerun was `NEED_ACTION`: the isolated Chrome
  process did not expose the requested CDP listener and the harness returned
  exit `1`. The G21 HTTPS artifact remains the current predecessor evidence;
  native browser-loaded MV3 worker dispatch and live vendor journeys remain
  `UNVERIFIED`.
- `LocalModelEndpointAdapter` reports conservative cancellation and cleanup
  capabilities because synchronous HTTP completion cannot prove that a local
  server stopped accepted work.
- The reference workflow executor is a minimal lifecycle boundary; complete
  declarative step execution is future work.
- Windows symlink containment coverage may be skipped when the host policy
  denies symlink creation. The skip must remain visible in acceptance output.
- Runtime Doctor reports are bounded internal diagnostics. They must not be
  promoted to `SUPPORTED` or `CERTIFIED` without current evidence.
- CP06 evidence is local and deterministic only. No cloud fallback, external
  connector, real user database, or raw credential is part of this V1 gate.

Any future change that removes a limitation requires a separately scoped task,
current evidence, and the applicable architecture or human decision gate.
