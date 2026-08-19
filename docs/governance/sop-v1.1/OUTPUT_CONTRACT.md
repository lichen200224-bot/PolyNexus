# PolyNexus Agent Output Contract v1.1

本文件定義 OpenCode、Codex、Antigravity 的共同回覆介面。它是給人讀的格式，也是未來 automation parser 的最低契約。

## 1. 必填三段

每次完成、失敗、等待或被阻塞的回覆，都必須包含：

```text
RESULT: <PASS | FAIL | NEED_ACTION | BLOCKED | READY_FOR_*>
NEXT_ACTION: <明確下一個狀態或動作>
NEXT_PROMPT: <可直接複製給下一個角色的完整提示詞>
```

`NEXT_PROMPT` 不能是空白、不能只寫「請驗收」、不能依賴本回覆以外的隱含上下文。

## 2. 建議機器可讀欄位

以下 YAML 不是產品設定檔；它是回覆內容的固定欄位示例：

```yaml
task_id: "{{TASK_ID}}"
state: "READY_FOR_CODEX_ACCEPTANCE"
result: "READY_FOR_CODEX_ACCEPTANCE"
actor: "OpenCode"
writer: "OpenCode"
reviewer: "Codex"
attempt: 0
modified_files:
  - "path/to/file"
implementation_summary: ""
tests:
  - command: ""
    exit_code: 0
    result: "PASS"
evidence:
  - id: "EVID-001"
    type: "test-output"
    path: ""
    summary: ""
known_issues: []
adr_impact: "NONE"
scope_deviation: "NONE"
protected_areas_check:
  fvs_01: "NOT_TOUCHED"
  fvs_02: "NOT_TOUCHED"
  adr_001_to_010: "NOT_TOUCHED"
next_action: "CODEX_ACCEPTANCE"
next_prompt: |
  <完整提示詞>
```

## 3. OpenCode 完成輸出最低欄位

```text
RESULT: READY_FOR_CODEX_ACCEPTANCE

TASK_ID:
STATE:
MODIFIED_FILES:
IMPLEMENTATION_SUMMARY:
TESTS_AND_EXIT_CODES:
DETERMINISTIC_EVIDENCE:
KNOWN_ISSUES:
ADR_IMPACT:
SCOPE_DEVIATION:
PROTECTED_AREAS_CHECK:

NEXT_ACTION: CODEX_ACCEPTANCE
NEXT_PROMPT_FOR_CODEX:
<完整 Codex Acceptance Prompt>
```

## 4. Codex 失敗輸出最低欄位

```text
RESULT: FAIL
STATE: CODEX_REJECTED
TASK_ID:
ATTEMPT:

ISSUES:
- ISSUE_ID:
  SEVERITY: BLOCKER | HIGH | MEDIUM | LOW
  EVIDENCE:
  IMPACT:
  TARGET_TOOL: OpenCode | Codex | Antigravity
  ACCEPTANCE_AFTER_FIX:

FIX_PROMPT_FOR_TARGET:
<完整可直接貼給目標工具的提示詞>

NEXT_ACTION: FIX_REQUIRED
NEXT_PROMPT:
<同一份或 coordinator 可直接使用的 FIX PROMPT>
```

## 5. 修正工具完成輸出最低欄位

```text
RESULT: READY_FOR_REVERIFICATION
STATE: READY_FOR_REVERIFICATION
TASK_ID:
ATTEMPT:
FIXED_ISSUES:
MODIFIED_FILES:
TESTS_AND_EXIT_CODES:
EVIDENCE:
KNOWN_ISSUES:
SCOPE_DEVIATION:

NEXT_ACTION: CODEX_REVERIFICATION
NEXT_PROMPT_FOR_CODEX_REVERIFICATION:
<完整回驗提示詞>
```

## 6. Codex 通過與人工 Gate 輸出最低欄位

```text
RESULT: READY_FOR_HUMAN_APPROVAL
STATE: HUMAN_APPROVAL_REQUIRED
TASK_ID:
ACCEPTANCE_ATTEMPTS:
REQUIRED_GATES:
GATE_RESULTS:
ACCEPTANCE_CRITERIA_EVIDENCE:
PROTECTED_AREAS_CHECK:
UNVERIFIED_ITEMS:
RESIDUAL_RISKS:

NEXT_ACTION: HUMAN_APPROVAL_REQUIRED
NEXT_PROMPT_FOR_HUMAN:
<指定 TASK_ID、commit scope 與 APPROVED_FOR_COMMIT 格式>
```

## 7. 解析與拒絕規則

automation 若遇到以下任一情況，應停止轉移並回報 `NEED_ACTION`：

- `RESULT` 與 `state` 不一致。
- 有 `FAIL` 但沒有 `FIX_PROMPT`。
- 有修正檔案但沒有回驗 prompt。
- `PASS` 沒有 evidence。
- `HUMAN_APPROVAL_REQUIRED` 沒有明確 commit scope。
- 任一受保護區域被列在 modified files 中但沒有授權例外。
