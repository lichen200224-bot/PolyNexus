# Codex 交接與安全啟動

Status: GATED_HANDOFF / NOT_IMPLEMENTATION_START
本文件不是立即叫Codex開始全部產品修改；它先要求確定已發布且獨立審查的設計、必要環境與執行授權。前置文件修改仍由ChatGPT負責。Human既有批准可用則不重問，真正未具条件才集中報例外。

## 一段入口

你接手lichen200224-bot/PolyNexus。唯一前置設計branch為planning/full-delivery-design-consolidation。先以canonical remote核對PR/publication receipt的exact SHA；不得用舊default、聊天memory或local cache作最新truth。讀AGENTS.md、docs/37_CURRENT_ROUTING_INDEX.md、docs/delivery/START_HERE.md、SOURCE_LOCK.json、FEATURE_WORK_PACKAGES.md、FEATURE_SCOPE_MATRIX.json與當前review結果。先做READ_ONLY_START_GATE，不啟動產品Writer、不修改原dirty worktree。

若被指派Fresh Independent Design Reviewer，你不是本patch Writer；依DESIGN_REVIEW.md審查source/功能範圍/限制/契約/測試，執行可用的結構及相容性檢查，將缺陷交回文件Writer，不自動進產品開發。

若被指派正式Controller，必須已有exact documentation review、selected product/integration base、既有MCF候選處置、實際allowlist/roles/有限資源/target權限与start receipt。成立後按GOAL_PLAN連續完成D0→D1a→D2a→D1b→B01-TECH→其餘全功能→T1/T2→交付。每FD/PN所有子項都要核銷；普通bug自行修復/重驗，fresh Reviewer不是Writer。最後輸出READY_FOR_HUMAN_UAT，不宣告Human接受。

## 開工前可重現的文件檢查

```text
python docs/delivery/checks/validate_feature_scope.py --requirements docs/delivery/REQUIREMENTS.md
python docs/delivery/checks/selftest_feature_scope.py
```

這只驗規劃結構，不替代逐source語意審查、Windows/Live可用性或產品tests。fixture/private context不能當Human UAT。

## 回覆欄位

TASK_ID、ROLE、ACTUAL_REMOTE_SHA、EXPECTED_SHA、SOURCE/FEATURE_SCOPE_RESULTS、WORKTREE/OWNER_STATE、DESIGN_REVIEW、EXISTING_CANDIDATE_DISPOSITION、ENVIRONMENT_AND_BUDGET、ACTUAL_COMMANDS_AND_EXITS、BLOCKERS、NEXT_OWNER、NEXT_ACTION、PRODUCT_START_ALLOWED。

沒有獨立設計證據就寫PRODUCT_START_ALLOWED=NO；不要求Human重講初版功能，也不把未解的設計決策直接丟到產品coding過程。
