# 安全、Human 信任與負向測試規格

Status: DESIGN_DRAFT。採Frozen Local-personal/Single Human範圍；不宣稱抵抗同OS principal的惡意process、hostile-code sandbox或Enterprise IAM。安全規範來自ADR-010、D11-A-LP、REV1、MCF；此文件不授權實際外傳或讀取帳號秘密。

## 1. 資產與控制面

需要保護：Human原始repository與dirty/index/untracked、managed worktree ownership、source snapshots/accepted bytes、immutable binding、Evidence/Decision歷史、SecretRef對應實值、session/grant/challenge、context分類與外傳目的地。

認證(authenticated identity)、執行權限(effect permission)、資料政策(egress/classification)、Human acceptance trust四者分開。開發Agent的Git/測試批准不變成產品Run許可；policy_decision_ref不是Human signature；D11-C不能靠boolean欄位或參考字串繞過。

## 2. D11-A-LP建議實作邊界

Pairing grant只允許建立限定Human session，不產生decision。Grant由本地Human enrollment流程明確取得，Agent token不能透過同一endpoint升級為Human。Session獨立audience/scope、可撤銷、有期限；其secret verifier放專用security store，不放一般domain/evidence/export。

Challenge由server生成不可預測nonce，綁session principal、CandidateID、exact view digest、decision kind、當下requirement/validation/policy/evidence/decision revision及expiry。提交時同transaction驗證eligibility、nonce未耗用、revision/target/current session、command idempotency，再append decision及消耗challenge。先成功後network中斷重送回原receipt，不追加第二次接受。

安全cookie策略與Origin/CSRF防護依本地HTTP/HTTPS實際部署配置測試；不得把CORS設定當CSRF或Human身份證明。只有明列loopback origin/port可用，拒絕wildcard/unknown origin及cross-origin mutation。使用者進入錯誤Core或pairing範圍不符要拒絕，不能自動fallback trust。

具體TTL、session是否持久化、restart re-pair策略不是Frozen常數。開工profile必須選擇有限值並測expiry/revocation/replay；不以Golden fixture或示例數值假裝產品極限。沒有完整安全實作時回D11-C，不能先放寬接受權再補測。

## 3. Threat / control / evidence

| Threat | Control | 必測oracle |
|---|---|---|
| Agent冒Human / token confusion | 分離credential audience/principal、server取identity | Agent/service/runtime token與body human=true均不能Accept |
| replay/double submit | single-use nonce＋idempotent receipt | 同key同payload只一次decision；same nonce不同target/action拒絕 |
| stale view/policy | view+revision binding、submit重查 | challenge後改policy/evidence/candidate不能用舊challenge接受 |
| CSRF/Origin/DNS rebinding | explicit loopback caller/host/origin校驗＋CSRF | foreign/missing required origin、錯token、另一Core拒絕 |
| source/manifest篡改 | Core snapshots＋REV1 identity＋closure驗證 | caller diff/hash claim、missing blob、path/mode漂移不publish |
| cross-candidate evidence | exact Candidate/contract/scope binding | 其他Candidate、stale/invalid EvidenceSet不滿足mandatory |
| writer競態/late abort | generation CAS＋durable lineage＋fence | 多入口/多command同generation只有一lineage；late abort不殺g2 |
| path escape/symlink/TOCTOU | allowlist、canonical containment、no unsafe follow、re-read/import | traversal/encoded path/link替換/cleanup間改檔被拒絕 |
| config/plugin/MCP擴張 | resolved config來源盤點＋Run envelope＋binary/version pin | unknown config/parent/global injection、binary drift不launch |
| data外傳/silent fallback | 每一步highest classification/mode/destination/effect check | local-only外部tool、敏感檔降級、retry換cloud拒絕 |
| secret洩漏 | OS-backed provider、metadata-only refs、redaction-before-persist | marker秘密不出domain/log/artifact/export/Git；error無raw resolver dump |
| false cleanup/PID reuse | owned process/tree/session observation＋fence | unknown process/清理失敗保留failure/recovery，不以flag成功 |
| accepted history變造 | append-onlydecision/source、current disposition derived | accepted後ordinaryReject/原event update拒絕 |
| malicious package/import | closure/hash/path/size/namespace驗證 | zip slip、缺blob、collision、偽Human session不可匯入 |

## 4. 測試資料與秘密

用synthetic repo與合成secret canary做一般安全測試，不複製使用者真實秘密。需要live target時只使用指定測試scope與runtime-managed auth/SecretRef；不得索取或存入Git的密碼/cookie/session token，勿將完整環境變數/HTTP headers輸出為診斷。

Source URL/commit是研究依據，不是供應商當前合規或live certificate。重新發佈第三方component前記錄license與分發模式檢查；此交付不要求捆綁所有第三方runtime。

## 5. Required security退出條件

每項required安全邊界有真實oracle、正向可用及負向拒絕證據；只測永遠DENY不證明產品可用。使用mock覆蓋邊界後仍要對聲稱支援的real runtime/host證明必要行為。Windows symlink-policy skip若本次required containment無等價實測，屬阻擋，不沿用historical waiver自動通過。

安全失敗不可用skip、降低classification、開全部permissions、關auth或弱化assertion修復。普通bug由Writer修復再獨立重驗；scope/trust/不可逆資料變更由exception gate處理。
