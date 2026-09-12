# Codex 完整交付執行計畫與依賴

Status: PLAN_READY_FOR_DESIGN_REVIEW / PRODUCT_START_HOLD。目標是全初版＋確認擴充，不是只做B01。D0/D1/D2等為本交付包的分組，不改舊WP/Goal身份或計分；精確scope以PN需求＋原來源義務共同構成。

## 1. 正確的依賴順序

```text
PREP docs + source/Git reconciliation
  -> independent design review + bounded start receipt
  -> D0 (S0 stability)
  -> D1a (W1 input/workspace/generation/lineage)
  -> D2a (W2 real-executor feasibility and controlled execution)
  -> D1b (W3 Candidate -> W4 verification -> W5 Human -> W6 accepted result/P0)
  -> B01 independent real working-product verification
  -> D2b (remaining required runtimes/modules/local capabilities)
  -> D3 (full workflow/Council/templates/policy collaboration)
  -> D4 (full daily UX/Web/Doctor/maintenance)
  -> D4-NEXT (N1 and WebSocket target completion under original scope)
  -> T1 full functional SIT
  -> T2 reliability/security/migration/clean-install SIT
  -> DELIVERY rehearsal/package
  -> HUMAN_UAT
```

D1/D2在REQUIREMENTS是責任群，不能解讀成先做完所有D1才做D2。D1b的凍結/驗證/接受可以先實作純邏輯tests，但不得在W2可行性前宣告真實working-product成果。D0必要S0不能被既有BASELINE-DEBT PASS整包替代。D3/D4在dependency成立時可做只讀設計/測試規劃，仍只一個active coding Writer。

## 2. 交付包定義

| Unit | Inputs / scope | Output / exit | 禁止偷渡 |
|---|---|---|---|
| PREP | f0產品＋FORMAL/FROZEN/MOD/GOV/MCF來源 | 唯一文件入口、exact docs candidate、完整需求/設計/測試、independent review | 不匯入未接受MCF source、不改default/history |
| D0 | PN064–067；WORK S0；已有ordering/cleanup成果 | FK每連線、legacy audit、CREATED restart、schema/auth/UI分層health；正負測試與review | 不fakebinding、WAL強制、真DB repair |
| D1a | PN043–048；S0通過 | input snapshots、generation/control、workspace four axes、same-generation lineage；late-Abort/dirty preservation | 不parallelcoding、不以lease/PID當ownership |
| D2a | PN016–021/068–073；WORK W2；D1a | 先real feasibility，再核准單target實作；cwd/change/cancel/timeout/cleanup/Artifact真證據 | 不把deny-all fixture當可改碼、不默認direct Human workspace |
| D1b-W3 | PN010/049/050；D2a真outcome | REV1 snapshots/changeset/candidate/publication、quiescence/source closure、fixed Golden tests | 不重算expected IDs、不混generation入CandidateID |
| D1b-W4 | PN012/015/051/052 | exact Candidate EvidenceSet/verification、四軸結果及validity | 不跨Candidate借PASS、不可改被驗source |
| D1b-W5 | PN053–058；A-LP正式語意 | Human-only enrollment/session/challenge/append history、D11-C fallback、API+UI負例 | 不以Agent/chat/Git auth代Human，無Override |
| D1b-W6 | PN059/060/062；W3–W5 | accepted managed result、explicit takeover label、P0 source重建、durable monitor | Accept不autoapply/Git；N1不擋P0 |
| B01 | PN060/067/072/073及S0/W1–W6必需case | 一個真bug fix＋一次failure→retry/recovery，actual Source/Test/Evidence/Human/Open/P0 | 不當完整release，不靠simulator |
| D2b | PN016–023/030/032/033/040–042；B01 | 完整required Codex/OpenCode、local endpoints、交換module、Doctor/conformance差額 | 無未授權backuptarget/marketplace，無支援成熟度虛報 |
| D3 | PN004–015/027–029 | workflow step execution、Council/cross review/synthesis、九範本、policy/local-mixed | 不造generic BPM、同一答覆冒多角色 |
| D4 | PN001–003/011/024–026/031–039及UX | UI/日用/三Web fallback/guard/metrics/backup/clean install差額 | 不靠人工改DB/重貼log完成正常工作 |
| D4-NEXT | PN061/063；完整目標中的後續階段 | N1 selected-task portability與WS目標，保持durable truth與import信任隔離 | 不變成cloud sync/enterprise或native session保證 |
| T1/T2 | AT001–077與所有source required oracles | 完整SIT、安全/恢復/upgrade/restore/clean install，zero unresolved BLOCKER/MAJOR | 缺必做不改N/A；歷史測試不冒current |
| DELIVERY | 全需求核銷、exact final candidate | 可用套件、繁中手冊、報告、Evidence index及AI rehearsal | 不產生Human Accept/production release |

## 3. 每個執行單元的工作契約

開始時鎖定：unit id、predecessor/selected integration SHA、required PN/source clauses、入口依賴、exact allowed existing paths與新增path rules、protected paths、owner/reviewer、test commands/expected oracles、resource envelope、stop conditions、預期artifact/交接。

Path allowlist由SD責任邊界與actual diff形成，不使用`git add .`。新增private file可以在已批准責任內自行決定，但不能借『新檔』增加子系統。每unit範圍包括實作、UT、contract、integration smoke、review、同範圍defect修復、回歸與sanitized ledger；不得把UT延後至最後SIT才開始。

## 4. 既有候選與差額重用

先讀IMPLEMENTATION_LEDGER。f0的accepted bounded成果保留，只有受影響/required release tests重跑。MCF030890先在其exact source做獨立候選審查，再與D1工作區/identity設計做相容性整合；若有修復新SHA保留舊lineage，不能在已review snapshot上amend。

Formal/Freeze已接受的是契約，不等產品實作。需要改資料schema按DATA_AND_API/additive migration及fixtures演練，原Human DB保持不動。來源分支不符合完整producttree者只作文件來源，不能選成implementationbase。

## 5. Continuation與中斷

Controller保存PN/unit/checkpoint/review/findings/evidence references，不把全部log與歷史塞下一context。Quota/timeout中斷前保存safe SYNC checkpoint及下一精確工作；未驗completed不標PASS。新context先驗base/branch/ownership、只讀必要delta，再接續。某UI沒有自動重啟能力時，結果應是CONTINUATION_READY，不宣稱背景必定自行工作。

同根因多次失敗先改由fresh root-cause review，不重跑無關suite製造活動。接續單元不等自主recursive delegation，只有execution receipt列明的角色與routing可啟動。

## 6. Progress model

分開呈現需求設計覆蓋、功能實作狀態、有效測試、独立審查、Human acceptance五層。原G24–G30分數保留，不將這些新單元自動加進100分分母。B01只是working-product milestone；完整交付須核銷所有required PN和原件義務，不以『七個Goal都跑過』代替。
