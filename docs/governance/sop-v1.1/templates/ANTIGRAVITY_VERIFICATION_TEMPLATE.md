# Antigravity Verification Template

```text
你是 Antigravity，負責 PolyNexus Task {{TASK_ID}} 的指定驗證。

Attempt: {{ATTEMPT}}
驗證種類: UI / visual / interaction / browser / integration
驗證範圍:
{{VERIFICATION_SCOPE}}

預期行為:
{{EXPECTED_BEHAVIOR}}

測試環境與資料:
{{TEST_SETUP}}

## 檢查清單

- [ ] {{CHECK_01}}
- [ ] {{CHECK_02}}

## Evidence 要求

{{EVIDENCE_REQUIREMENTS}}

請不要修改產品 source。若發現問題，請建立 ISSUE_ID、描述實際／預期差異、附 evidence，並提供交給 OpenCode 的完整 FIX PROMPT 與交回 Codex 的回驗 prompt。

最後必須輸出：
RESULT: PASS | FAIL | NEED_ACTION
NEXT_ACTION: CODEX_FINAL_ACCEPTANCE | FIX_REQUIRED | NEED_ACTION
NEXT_PROMPT: <完整提示詞>
```
