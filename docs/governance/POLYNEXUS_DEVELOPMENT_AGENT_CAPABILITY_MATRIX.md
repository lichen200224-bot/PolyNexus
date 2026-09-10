# Development agent capability matrix

2026-09-10 · machine alias `current-windows-checkout` · [Framework](POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md)

這是開發工具的 observed matrix，不是產品 W2 executor conformance。DECLARED 是角色/能力宣告；OBSERVED 是本次實測；CURRENTLY_READY 只適用指定版本/機器/授權/scope，三者不可互換。新機器逐項重驗，不能依品牌推定。

| Tool | DECLARED role | OBSERVED this session | CURRENTLY_READY / limitation |
|---|---|---|---|
| Codex desktop context | Primary Goal Owner/Writer；analysis/test/Git/handoff | 本次repo讀寫、PowerShell、Node、read-only Git實際可用；PATH `codex.exe --version` = `codex-cli 0.153.4`，exit 0（PATH alias warning） | 此governance scope可用；產品Writer NONE；CLI版本不證desktop backing model/runtime同版本。真實executor/long-task resume/cross-machine未驗 |
| OpenCode | 可經Human指定alternate Writer/support | `Get-Command`未在PATH找到；repo有opencode.json，edit ask、commit/push deny | UNKNOWN/NOT_VERIFIED；不能把配置存在當已安裝。若另授權Writer且policy阻止local candidate，需最小工具權限處置，不能繞過 |
| Antigravity | Browser/E2E independent verifier；alternate Writer須Human | 未在PATH找到；有 `.agents/rules/polynexus-core.md` | UNKNOWN；browser/tool connection/version未實測 |
| Claude / Claude Code | Human bounded planner/reviewer/support或alternate Writer | 未在PATH找到；沒有現存CLAUDE.md入口 | UNKNOWN；無repo write/test/Git/resume證據 |

| Capability | Codex current context | OpenCode | Antigravity | Claude Code |
|---|---|---|---|---|
| repo read | OBSERVED | UNKNOWN | UNKNOWN | UNKNOWN |
| repo write | OBSERVED governance only | UNKNOWN | UNKNOWN | UNKNOWN |
| shell | OBSERVED PowerShell 7.6.5 | UNKNOWN | UNKNOWN | UNKNOWN |
| tests | governance checks OBSERVED；product tests NOT_RUN | UNKNOWN | UNKNOWN | UNKNOWN |
| Git | read-only OBSERVED；write prohibited this round | configured commit/push deny；未執行 | UNKNOWN | UNKNOWN |
| local models | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED |
| cloud models | current assistant response observed；exact model ID UNKNOWN | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED |
| cross-machine handoff | records prepared；fresh remote/clone NOT_RUN | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED |
| long task support | 本session持續執行observed；durability未驗 | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED |
| resume after restart | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED | NOT_VERIFIED |

## Environment fingerprint

OS Windows NT 10.0.26200.0；Git 2.45.0.windows.1；Node v22.22.3；npm 10.9.8；PowerShell 7.6.5。`python --version` CommandNotFound，未有native exit，不能記Python可用。只記PATH probe結果，不推定整台機器沒有其他Python/tool。CLI model未查，actual harness=Codex desktop tool context，MODEL=UNKNOWN（Human指派Astra不當作可觀測ID）。

branch `feature/first-vertical-slice`；HEAD `b87a0dc780e5d9a3bba083dbaf9552ca52508f9a`；core.autocrlf=true。設計baseline另為f34全SHA。`.gitattributes`與`apps/web/package-lock.json` SHA-256及完整觀測結果存 [Review packet](../reviews/TA-OPERATING-MODEL-REVIEW.md)；不存在Python lock的搜尋結果不保證無其他dependency authority，實作intake需讀實際manifest/setup。

Relevant environment variable NAMES: PATH, PATHEXT（只列名稱）；不讀/保存secret values。shell CommandNotFound與最後命令exit分開，不以複合command exit 0證明前面全成功。路徑含Unicode且與歷史少底線位置不同、autocrlf=true，跨機器須比較case/path/CRLF/bytes/hash，不silent normalize。未執行登入、provider请求或真實runtime。

追加觀測：本地 `review_work/python-embed/python.exe` 為 Python 3.12.10；Codex bundled Python 為 3.12.14，version probe exit 0。兩者初始均缺 PyYAML（import exit 1）；僅在本輪外部 validation-deps 目錄安裝 PyYAML 6.0.3（pip exit 0），以 process-local PYTHONPATH 執行官方 skill validator，10 個 skills 各 exit 0。不改 project dependencies，PATH上Python仍未配置。版本路徑差異須在新機器重驗。

新觀測row最低欄位：machine alias、tool/exact version、timestamp、capability、declared claim、probe command/cwd/actual exit/output hash、observed outcome、current readiness scope、authorization、known limitations。取得新的工具/模型不自動授權Goal或切換Writer。
