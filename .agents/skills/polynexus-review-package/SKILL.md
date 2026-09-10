---
name: polynexus-review-package
description: Build and validate the mandatory exact-SHA ZIP before any PolyNexus Goal becomes REVIEW_READY, and guide external reviewers through its entrypoint and evidence.
---
# PolyNexus Mandatory Review Package

REVIEW_PACKAGE_CANONICAL_AUTHORITY。適用所有Codex及Human-authorized OpenCode/Antigravity/Claude/Claude Code/其他Writer；不改Architecture、Human authority或產品狀態。其他skills只引用本skill。欄位權威為本skill的 [package-fields.json](references/package-fields.json)；既有 [Review template](../../../docs/reviews/_REVIEW_PACKET_TEMPLATE.md) 是該schema的填寫投影，不建立另一套schema。

## 1. Hard gate and owner

**NO_REVIEW_PACKAGE = NOT_REVIEW_READY**。每個Goal到REVIEW_READY前，Active Writer須自動產生完整Review ZIP並驗證，不需Human逐步確認。流程：bounded work → positive/negative tests → repair → final fresh rerun → evidence → local candidate commit → exact SHA verification → package generation → package self-validation → REVIEW_READY → STOP WRITING。

缺candidate、package incomplete/invalid/stale、mandatory evidence缺漏或unexpected scope：GOAL_STATUS=IN_PROGRESS（可自行修復）或HOLD（真正blocker），REVIEW_READY=NO；不得交Independent Review、要求Human Acceptance、建議APPROVE_TO_PUSH或push accepted checkpoint。已授權Goal包含此收尾工作，不授予新的外部服務/secret傳輸或push權。

只有全部成立才REVIEW_READY：bounded work完成、candidate存在/full SHA正確、allowlist/patch/changed bytes一致、mandatory evidence fresh、negative evidence有記錄、mandatory SKIPPED none（可信contract-defined N/A除外）、environment已記、manifest valid、全部parts完整、required bundle valid、檢查未偵測secret洩漏。結構validator PASS只是必要機械證據；Writer仍須查AC/oracle/freshness/secret scope，不得宣稱工具證明所有語意。

## 2. Identity and immutable delivery

package綁GOAL_ID/PREDECESSOR_SHA/REVIEW_CANDIDATE_SHA/BRANCH/WRITER/HARNESS/MODEL。SHA用完整object ID，禁用latest/current/final code代替。MODEL/version不可觀測寫UNKNOWN，不猜。Reviewer驗exact C，不能用文件snapshot假稱Git commit。

candidate reviewed bytes改變 → new SHA + fresh required evidence + new ZIP；舊包STALE不得沿用。只重新壓縮且payload/C完全相同可新timestamp/ZIP hash，但仍核對全部bytes。新包不得覆寫已交付包，也不得amend交審C。

命名：`PolyNexus_<GOAL_ID>_External_Review_<YYYYMMDD_HHMMSS>.zip`，Goal ID安全字元可簡化但可辨認，timestamp註明timezone。預設ONE ZIP；不是backup。

自引用：C內Goal記package-required/level與completion receipt locator，生成前dynamic path/hash為PENDING，不先標REVIEW_READY。C後在**ZIP外**生成delivery.json，實填GOAL_ID、C、predecessor、branch、REVIEW_LEVEL、REVIEW_PACKAGE_PATH、REVIEW_PACKAGE_SHA256、PACKAGE_VALIDATION_STATUS、GOAL_STATUS。此為Goal completion metadata，不修改C；Human上傳時提供ZIP及其hash/sidecar。ZIP內REVIEW_PACKET可記候選READY待gate核對，只有ZIP驗證成功才發布該包與REVIEW_READY final。失敗包不得交付或自稱ready。C/R acceptance receipt仍依[Framework §5](../../../docs/governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md)，接受後的R可在既定allowlist收錄package ref/hash，不為填ZIP hash改C或造循環。

## 3. Standard content and first read

ZIP root必有以下檔案，START_HERE.md也建議第一個ZIP entry：

- START_HERE.md：REVIEWER_FIRST_ACTION=READ START_HERE.md；簡潔1–2頁導航，欄位見schema。
- REVIEW_PACKET.md：完整Writer packet，欄位與既有template一致；不是Independent PASS。
- HUMAN_REQUEST.txt：本Goal真實Human request/授權內容，非模型代寫假原文；不依賴聊天存取。敏感值不得附，redaction必記範圍。
- GIT_REVIEW_CANDIDATE.txt：full identities、actual git status/show/diff、無credentials的remote資訊、NOT_PUSHED。
- CHANGED_FILE_ALLOWLIST.txt：AUTHORIZED與ACTUAL分開、MATCH YES/NO；每項CREATED/MODIFIED/DELETED；rename列old/new，不省略舊路徑。合法new-file責任擴充須附authorization ref，不偷偷吸收unexpected。
- THIS_ROUND_DIFF.patch：等價`git diff --full-index --binary <P>..<C>`，支援text/binary/rename/delete/add；由Git固定objects取得，不能以工作目錄diff代替。
- VALIDATION_RESULTS.md、ENVIRONMENT_FINGERPRINT.md：actual evidence/versions，schema見reference。
- MANIFEST_SHA256.txt或MANIFEST.json：machine-readable逐檔PATH/ROLE/SIZE/SHA256。使用JSON時欄位與本skill規定一致。
- changed_files/（或清楚定位的repository/）：每個新增/修改檔由`git show C:path`取actual bytes；deleted只在manifest/diff表達，不能偽造空檔；symlink/mode依Git表達，不跟隨外部連結。
- evidence/：actual outputs/logs/receipts；references/：本bounded review真正需要的unmodified contract/dependency，註明REFERENCE_ONLY及source SHA/section/hash。
- REVIEW_CANDIDATE.bundle：依level/technical applicability。

不存在的evidence不可造placeholder PASS。NOT_AVAILABLE/SKIPPED/NOT_APPLICABLE要有原因及blocking分類；optional資料缺失可記狀態，required evidence缺失阻gate。Folder名稱不是evidence存在證明。references用MINIMAL_SUFFICIENT_EVIDENCE，不預設整庫打包；Reviewer需更多再提出bounded request。

schema欄位是最低集合；用JSON/YAML code block或frontmatter搭配可讀文字，供machine verifier解析。REVIEW_PACKET的REQUESTED_VERDICT是PASS/NEED_FIX/HOLD；PUSH_RECOMMENDATION_REQUEST是APPROVE_TO_PUSH/DO_NOT_PUSH的請求，不是Writer裁決。

## 4. Review levels / bundle

| Level | Scope / required addition |
|---|---|
| L1_NORMAL_GOAL（欄位L1） | 一般bounded Goal；standard package+changed bytes+necessary references/evidence；minimal bundle practical時recommended |
| L2_HIGH_RISK_GOAL（L2） | persistence/schema/migration/auth/security/runtime/process/Git ownership/worktree/Candidate identity/Evidence/Verification/Human Decision/high-risk recovery；另附重要unmodified dependency source、relevant contracts及適用migration/security/process evidence；minimal bundle technically/size practical時必附 |
| L3_INTEGRATION_PRODUCT_ACCEPTANCE（L3） | WP/parallel integration、W6 Golden Path、B01/Working Product/release-like acceptance；L2加relevant bundle、integration ancestry、E2E/browser/environment、handoff/history closure、cross-boundary negative、必要export/reconstruction artifacts |

L2/L3缺bundle必列NOT_AVAILABLE_WITH_REASON及technical/size證據；不可只說太大。L3預設required，無bundle不得READY，除非Goal/contract明確批准可信alternative及可重建/驗SHA來源；若可用拆包解決，應拆包而非省略。L1不用bundle可NOT_REQUIRED並述bounded審查方式。

不得打包整個.git。bundle至少可重建/驗P、C與ancestry/diff；若incremental bundle有prerequisites，必須列exact prerequisite SHAs與Reviewer可取得的approved source/companion bundle；開發機已有objects不代表Reviewer有。驗`git bundle verify`並記command/cwd/exit/output；非0不READY。可行時在空目錄實測bundle clone/import並核对P/C，不能把缺前置的bundle宣稱self-contained。檢查bundle實際攜帶history/blob範圍及secrets；禁止為方便附unrelated history。無法安全提供則HOLD/記限制，不重寫P/C來縮包。

## 5. Fresh evidence, exits, negatives, skipped

VALIDATION_RESULTS每個實際check有TEST_ID/PURPOSE/EXACT_COMMAND/CWD/START_TIME/END_TIME/ACTUAL_EXIT_CODE/ACTUAL_RESULT/OUTPUT_REF/MANDATORY/NEGATIVE_TEST/SKIPPED/SKIPPED_REASON/BLOCKING。候選前測試須以tree/file hashes證明tested bytes==C；若不等或contract要求post-commit rerun，必須重跑。Historical logs標REFERENCE_ONLY，不能替C mandatory evidence。命令成功只證該命令，非整體產品PASS。

負例分HARNESS_EXIT_CODE、TARGET_COMMAND_EXIT_CODE、EXPECTED_NEGATIVE_RESULT、ACTUAL_NEGATIVE_RESULT；expected child nonzero原樣保留，不改exit0。HTTP/protocol結果不冒充OSexit；無OSexit填UNKNOWN/NOT_APPLICABLE，另記protocol。缺mandatory actual exit且無contract允許的protocol替代不能PASS。

SKIPPED每項記CHECK/WHY_SKIPPED/REQUIRED或OPTIONAL/BLOCKING。Required skipped→REVIEW_READY NO；只有Frozen/Goal contract明確N/A predicate與可信applicability evidence才可不阻塞，不能用「not needed」代替理由。L2/L3未適用的browser/migration等也需contract-based判斷，不因level自造無關測試。

Environment記OS/version、Git/Python/Node/npm/shell、actual Writer harness/version/model、branch/HEAD/P、core.autocrlf、.gitattributes與relevant lockfile hashes、environment variable NAMES ONLY。不可觀測UNKNOWN；ENV drift包含path/case/Unicode/CRLF/dependency/runtime差異及其candidate/evidence影響，不silent normalize。

## 6. Manifest, safety and split

manifest每payload entry含PATH、ROLE（CREATED/MODIFIED/REFERENCE/EVIDENCE/CONTROL/GIT_BUNDLE）、SIZE、SHA256；額外記REPO_PATH、C/P identities、deletions與rename old/new。封ZIP後重讀每entry bytes/hash/size、完整性/CRC、unique normalized path、無path traversal/絕對路徑/case collision；file set必與manifest完全相等（manifest自身例外見下）。changed bytes/patch再對Git C/P，非只信Writer hash。

manifest不能hash自身。唯一例外是manifest本身不列自身SHA；其bytes以**ZIP外**delivery.json的manifest SHA256及整ZIP SHA256固定。其餘每個package檔都列manifest。不要在ZIP內放自身ZIP hash或創造無限seal；delivery sidecar不屬ZIP payload。tampered manifest與包一起改動必須由已提供的外部ZIP hash發現，Reviewer first確認外部hash與identity。

禁止password/token/API key/cookie/session secret/private key/credential DB/browser profile/unredacted env values；預設排除node_modules/.venv/dist/cache/coverage cache/model weights/large unrelated binaries/IDE cache/temp/user profile/unrelated history。對plain payload、patch、evidence及bundle reachable blobs做適用secret檢查與scope inspection，記檢查方法/限制；regex未匹配不等於零風險保證。有可疑值先HOLD、移除敏感payload或授權安全redaction；如secret在candidate歷史，不偷偷改C或提供無法review的包。

預設一包；必要資料過大可PART1 core、PART2..N evidence。START_HERE列ALL_REQUIRED_PARTS每part filename/size/SHA256/purpose；part1自身用SELF_CORE，actual bytes/hash記外部delivery index，避免ZIP自引用。各part manifest獨立驗證。缺任何required part PACKAGE_COMPLETE NO，不得完整PASS，不得靜默省略。單包ALL_REQUIRED_PARTS記ONE_ZIP（自身hash取外部delivery）。

可用 [validate_package.py](scripts/validate_package.py) 檢查單包manifest/identity/bytes/patch/allowlist；額外semantic/secret/bundle gates由Writer記actual evidence。split時逐part驗hash再依index驗complete，工具不支援的模式不得宣稱已驗。失敗修復後重建包，保持C不變或new C按變更性質決定。

## 7. Delivery / independent review

Goal contract必有REVIEW_LEVEL、REVIEW_PACKAGE_REQUIRED=YES、FORMAT=ZIP、PATH、SHA256、C、PACKAGE_VALIDATION_STATUS及minimum content/bundle/fresh evidence/environment/completeness/REVIEW_READY_GATE。Planning欄位可PENDING；Independent Review前dynamic值必以外部delivery record實填，不能用placeholder完成gate。

Writer final至少：GOAL_ID、GOAL_STATUS REVIEW_READY、REVIEW_LEVEL、BRANCH、PREDECESSOR_SHA、C、REVIEW_PACKAGE exact path、SHA256、PACKAGE_MANIFEST PASS、PACKAGE_COMPLETENESS PASS、MANDATORY_SKIPPED NONE、UNEXPECTED_CHANGED_FILES NONE、GIT_BUNDLE path/NOT_REQUIRED/NOT_AVAILABLE_WITH_REASON、PRODUCT_IMPLEMENTATION_SCOPE、GIT_PUSH NO、NEXT UPLOAD_REVIEW_PACKAGE_FOR_INDEPENDENT_REVIEW。提供Human可直接上傳ZIP與hash，STOP；不自行做Independent PASS。

Reviewer第一動作READ START_HERE.md，再核對外部hash、manifest/parts、C/P、allowlist/diff/actual bytes/fresh evidence/limitations，必要時重跑。Writer != Independent Reviewer；final VERDICT PASS/NEED_FIX/HOLD，recommendation APPROVE_TO_PUSH/DO_NOT_PUSH；Human仍FINAL_ACCEPTANCE_AUTHORITY/FINAL_PUSH_AUTHORITY。Package validation PASS不授權push。Accepted跨機handoff仍要求independently reviewed + Human accepted + remote verified的C/R closure，不能用ZIP取代。
