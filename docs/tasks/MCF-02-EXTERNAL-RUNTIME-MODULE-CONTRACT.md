# MCF-02 — External Runtime Module Contract & Compatibility Target Selection

## Control block

- `TASK_ID=MCF-02-EXTERNAL-RUNTIME-MODULE-CONTRACT`
- `STATUS=ARCHITECTURE_PROPOSAL`
- `IMPLEMENTATION_NOT_AUTHORIZED`
- `CANONICAL_START_SHA=f0c0b986380dc21d103d4e856057cb8ac435a8f9`
- `PREVIOUS_REVIEW_CANDIDATE_SHA=6bfa2f8653d0f667979d48a3628a77b15584e11d`
- `PREVIOUS_REVIEW_RESULT=MCF02_ARCHITECTURE_REVIEW_NEED_FIX`
- `CANONICAL_CONTINUATION_BRANCH=feature/mcf-01-static-module-contract`
- `ARCHITECTURE_BRANCH=architecture/mcf-02-external-runtime-routing`
- `MCF02=NOT_STARTED`
- `PRODUCT_CODE_CHANGE=NONE`
- `TEST_CODE_CHANGE=NONE`
- `MIGRATION_CHANGE=NONE`
- `PROJECT_SCORE_CHANGE=NONE`
- `OVERALL_PROJECT_COMPLETION=NOT_DEFINED`
- `NEXT_REQUIRED_ROLE=HUMAN_ARCHITECTURE_GATE`

本文件只提出下一個契約邊界與未來最小實作範圍。它不是 implementation
authorization、vendor certification、production readiness 或 Plugin Platform
完成聲明。

## 1. Architecture decision

`DECISION=PROPOSE_EXTERNAL_RUNTIME_CONTRACT_WITH_CORE_LIFECYCLE_OWNERSHIP`

外部 agent runtime 可以執行工作、維持自己的 conversation/session，並回傳
stream、result 與檔案；它不能取得 PolyNexus 的 Project、Task、Run、
WorkflowDefinition、RunSupervisor、RuntimeBindingSnapshot、Evidence、Finding、
Artifact、Human Gate、egress policy 或 SecretRef 的 authority。

第一個 compatibility target 建議只做：

- `PRIMARY_TARGET=OpenCode via ACP v1 (local stdio child process)`
- `BACKUP_TARGET=Gemini CLI via ACP v1 (local stdio child process)`

第一輪不得同時交付兩個 production target。OpenCode 的既有
`OpenCodeRuntimeAdapter` 只證明 deterministic local conformance；未來的
`opencode acp` 路徑必須是另一個明確命名、明確能力與明確成熟度的 adapter，
不得把既有 conformance PASS 當作 live compatibility evidence。

選擇依據與每個 target 的 current public surface 詳見
[MCF-02 target evaluation](MCF-02-EXTERNAL-RUNTIME-TARGET-EVALUATION.md)。

## 2. Repository facts that constrain the proposal

本次已檢視 `AGENTS.md`、scope/state/architecture 文件、ADR-011/012/013/014、
`ARCH-MODULAR-CORE-01`，以及目前 `extensions/**`、`runtime/**`、
`execution_service.py` 的相關契約。可作為本提案依據的現況如下：

1. `ModuleRegistry` 是 static metadata/enablement registry；它沒有 executable
   loading、install、remove 或 update API。
2. `RuntimeModuleBridge` 只將 guarded factory 註冊到既有 `RuntimeRegistry`；
   `RuntimeRegistry` 仍是唯一 profile/factory resolution authority。
3. `ExecutionService` 先建立 Run、CAS claim、寫入 CREATED→STARTING event 與
   immutable `RuntimeBindingSnapshot`，commit 後才可呼叫 adapter。
4. `RunSupervisor` 是唯一 runtime lifecycle owner；每個 adapter operation 有
   timeout/resource bound，cancel/timeout 只有在 `cancel → cleanup → status`
   精確證明預期 terminal state 時才成功，否則 fail closed 到 `ORPHANED`。
5. Adapter output 會經 `sanitize_runtime_result`；`ExecutionService` 只在真實
   result 存在時持久化 Finding/Evidence/Artifact，workflow gate 在 completion 後
   另行評估。
6. 現有 `RuntimeCapabilities` 只有 cancel、resume、artifacts、
   timeout cleanup、usage visibility、auth ownership；不足以描述 external
   session attach、event stream、permission、egress 與 protocol conformance。
7. 現有 V1 registry policy 只接受 LOCAL/LOCAL 且 `AuthOwnership.NONE` 的
   reference/local endpoint 類型。外部 runtime-managed auth 不可藉由放寬所有
   local profile 偷渡，必須有新的 explicit static policy gate。
8. `RuntimeBindingSnapshot` 已有 `adapter_version`、`profile_revision`、
   `auth_ownership` 與 `secret_ref_id`；其 1:1 Run、insert-once、不可 rebinding
   語意必須保留。

## 3. Required ownership boundary

| Concern | PolyNexus Core authority | External module authority |
|---|---|---|
| Project / Task / Run identity | 唯一建立與驗證者 | 只接受 opaque correlation；不得重定義 |
| WorkflowDefinition | 選擇版本、step 與 gate | 只執行已投影的單次工作輸入 |
| Runtime resolution | `RuntimeRegistry` 與 immutable binding | 提供 static factory/descriptor |
| Run lifecycle | `RunSupervisor` | 回報外部 observation，不得寫 Core RunState |
| Session lifecycle | 驗證 scope、attach、cancel、cleanup | 建立/操作 vendor session |
| Human confirmation | Core gate/policy | 只能提出 permission request，不得自行核准 |
| Data classification / egress | Core policy decision | 宣告目的地與實際 egress；不得擴張 |
| Secrets | `SecretRef` 或 runtime-managed boundary | 不得回傳 raw secret、cookie 或 token |
| Artifact / Evidence | Core normalization、hash、provenance、validation | 只回傳 candidate output/blob locator |
| PASS / VERIFIED / CERTIFIED | Core contract/gate/Human governance | 不得自我宣告 |

## 4. Required execution relationship

```text
External Runtime Module (static ModuleManifest + guarded factory)
    ↓
ExternalRuntimeAdapter (specialization of existing RuntimeAdapter)
    ↓
existing RuntimeProfile / RuntimeRegistry
    ↓
immutable RuntimeBindingSnapshot (persisted before external work)
    ↓
RunSupervisor (only Run lifecycle owner)
    ↓
Core Event / Artifact / AI_OPINION / Evidence normalization
```

禁止旁路：

- 不得直接從 module factory 建立或更新 Core Run。
- 不得跳過 `RuntimeRegistry` 或在 unknown profile 時 fallback。
- 不得在 binding commit 前建立外部 session、發送 prompt 或啟動 agent work。
- 不得把 external status 直接寫成 Core `RunState`。
- 不得在 `PolicyDecision.APPROVAL_REQUIRED` 時自動送出。
- 不得以 vendor 的 success 字串代替 Evidence validation。

## 5. Minimum generic external runtime contract

以下名稱是 architecture-level contract shape，不是已核准的 Python schema。
每一欄都對應既有 PolyNexus use case；未列入的 vendor-specific option 留在
target adapter 內部，不進入 Core contract。

### 5.1 Static descriptor

| Proposed field | Minimum shape | PolyNexus use case | Fail-closed rule |
|---|---|---|---|
| `contract_version` | bounded integer | 解析正確的 external contract | unknown version 拒絕註冊 |
| `module_id` / `module_version` | ADR-013 identifier + semver | static composition 與 adapter provenance | 與 `ModuleManifest` 不同即拒絕 |
| `provider_id` / `runtime_id` / `adapter_id` | opaque identifier | 對應 `RuntimeProfile` 與 binding | 與 profile 不同即拒絕 |
| `runtime_profile_ref` / `profile_revision` | existing profile identity | deterministic selection、no fallback | unknown/stale revision 拒絕 |
| `protocol_kind` / `protocol_version` | allowlisted public protocol identity | 例如 ACP v1 wire conformance | unrecognized/incompatible 拒絕 |
| `launch_mode` | `LOCAL_CHILD` 或明確 future value | 區分 local process 與 remote control | V1 只核准 `LOCAL_CHILD` |
| `capabilities` | normalized closed set | create/attach/observe/cancel/resume 等 feature gate | overclaim 或 unknown capability 拒絕 |
| `permissions` | bounded declared classes | 將 tool/file/process/network 權限交給 Core policy | undeclared permission request 拒絕 |
| `egress` | destination class + side-effect flag | 在 input dispatch 前執行 data/egress gate | 缺失、擴張或 approval 未完成即不送 |
| `auth_ownership` | existing `AuthOwnership` | 保留 runtime-managed/SecretRef/no-auth 邊界 | raw secret、ownership mismatch 拒絕 |
| `conformance` | scope + evidence ref, never self-certified | Doctor 區分 declaration 與 accepted evidence | declaration 不產生 PASS |
| `execution_envelope_ref` | Core-owned immutable digest/reference | 綁定有效設定、workspace 與 executable identity | 缺失、未知或 drift 即 readiness false |

不加入 vendor model picker、theme、TUI layout、billing plan、marketplace metadata、
browser DOM selector 或 vendor-only experimental flag；它們沒有跨 runtime 的
PolyNexus lifecycle use case。

### 5.2 Effective runtime configuration boundary

`EFFECTIVE_RUNTIME_CONFIGURATION_BOUNDARY` 是每次 external Run 的 Core-owned
execution envelope。OpenCode 會依 working directory 合併 configuration、plugins、
models、agents、commands、skills、instructions 與 MCP configuration，因此只綁定
provider/runtime/adapter/profile/contract version 不足以證明同一執行環境。

第一個 implementation 必須使用：

- `POLYNEXUS_CONTROLLED_EXECUTION_ENVELOPE=REQUIRED`
- `WORKSPACE_SCOPE_MODE=PROJECTED_STAGING`
- `DIRECT_PROJECT_WORKSPACE=NOT_AUTHORIZED`

Core 必須在建立 immutable binding 與啟動 external work 前，先以無副作用 preflight
解析並驗證下列 canonical envelope；可把 digest/reference 放入既有 binding metadata
或 conformance evidence，不要求新增 Core Domain：

| Envelope field | Required value/shape | Purpose | Fail-closed rule |
|---|---|---|---|
| `workspace_scope_mode` | V1 exactly `PROJECTED_STAGING` | 只暴露 projected ContextPackage/approved files | unknown、DIRECT 或 path escape 拒絕 |
| `effective_runtime_configuration_fingerprint` | strong digest of normalized effective non-secret config + precedence | 偵測 global/project/default 合併後的真實設定 | 無法解析、來源不明或 drift 即 readiness false |
| `permission_policy_fingerprint` | digest/reference to Core-approved normalized permission policy | OpenCode default `allow` 不等於 Human authorization | 缺失、permissive expansion 或 mismatch 即不 dispatch |
| `enabled_plugin_set` | sorted identity/version/digest set or explicit `NONE` | 防止 project/global plugin side-loading | 未核准項目、npm/package declaration 或 load drift 拒絕 |
| `enabled_mcp_set` | sorted server identity/transport/destination digest or explicit `NONE` | 將 MCP tool/egress 納入 Core policy | local/remote unknown server 均拒絕 |
| `remote_skill_catalog_state` | approved catalog snapshot digest/reference or explicit `NONE` | 防止 instructions/skills 形成 remote code/data path | remote/unknown catalog 拒絕 |
| `executable_identity` | canonical resolved path + content SHA-256/equivalent strong identity | 區分 same path + changed executable | path/digest missing或 mismatch 即 readiness false |
| `observed_runtime_version` | bounded output from the bound executable's version probe | 將版本觀察連回已 hash 的 binary，而非信任 descriptor | missing、unparseable或 policy mismatch 即 readiness false |

fingerprint input 可以包含 normalized non-secret configuration identity、source precedence、
approved item identities 與 content digests；不得把 raw configuration、credential、token、
cookie、auth header、SecretRef value 或完整 private instruction body 存入 binding。若原始
設定含 secret，binding 只記錄 bounded source reference與不可逆 digest，實值留在既有
secret/runtime-managed boundary。

`PROJECTED_STAGING` 由 Core 建立新的受控 staging workspace，只 materialize allowlisted
ContextPackage/approved files，並以 canonical path containment 驗證 input/output。不得將
真實 project root、parent directory、global config home 或任意 symlink target 默認暴露給
OpenCode。未來 `DIRECT_PROJECT_WORKSPACE` 必須另過 architecture/security/Human gate，
不是 MCF-02 第一版 capability。

### 5.3 Session handle

外部 handle 只應含：

- `external_session_id`：opaque、bounded；不得含路徑、cookie、token 或 account id。
- `project_scope_digest`：由 Core 對 project/workspace scope 計算的不可逆關聯值。
- `binding_fingerprint`：provider/runtime/adapter/profile revision/contract version 的
  canonical digest。
- `execution_envelope_fingerprint`：上述 effective configuration、permission、plugin、
  MCP、skill/catalog、workspace mode 與 executable identity 的 Core-owned digest。
- `created_by_run_id`：Core Run correlation。
- `attach_generation`：每次合法 attach 遞增，防 stale attachment。

它不是 Core Run identity，也不能單獨證明 resume、ownership 或 cleanup。

### 5.4 Required operations and mapping

| Generic operation/capability | Existing Core mapping | Required semantics |
|---|---|---|
| `health` | `RuntimeAdapter.health()` | 當下 probe；不是 conformance verdict |
| `readiness` | `RuntimeAdapter.readiness()` | effective config與 executable identity 完整匹配才可 ready |
| `create_session` | `create_run(context)` | 只在 binding 已 commit 後建立；回傳 scoped handle |
| `attach_session` | internal to `create_run`/`resume` | 驗證 project digest、binding/envelope fingerprint、generation |
| `dispatch_input` | `submit(runtime_ref, task)` | 只送投影後 ContextPackage/Task；先過 Human/egress gate |
| `observe_events` | adapter internal stream projected by `status()` | bounded ordered observations；未知 event 不改 RunState |
| `capture_result` | `result(runtime_ref)` | 回傳 candidate output；不得自帶 trusted PASS |
| `list/import_artifacts` | `artifacts(runtime_ref)` | content hash、size、source locator、session provenance 必填 |
| `export_input_artifact` | pre-dispatch staging helper | 只匯出 allowlisted refs；不得整個 workspace 隱式掛載 |
| `cancel` | `cancel(runtime_ref)` | request only；成功仍須 cleanup/status 證明 |
| `timeout` | `RunSupervisor` deadline | module 不得延長或關閉 Core deadline |
| `cleanup` | `cleanup(runtime_ref)` | 終止 owned process/stream/handles；bool 不足以單獨證明 |
| `resume` | `resume(runtime_ref, checkpoint)` | 只依 `NATIVE`/`MANAGED`/`NONE` 真實宣告執行 |
| `version_info` | `version_info()` + binding/Doctor evidence | observed version必須與 executable path/content digest 一起驗證 |
| `normalize_failure` | adapter → fixed error category | raw stderr/payload/secret 不進 persistence 或 API |

### 5.5 Capability vocabulary

未來 capability closed set 最少需要：

`session_create`, `session_attach`, `input_dispatch`, `event_stream`,
`result_capture`, `artifact_import`, `artifact_export`, `cancel`, `cleanup`,
`timeout_cleanup_verified`, `resume_native`, `resume_managed`, `health`,
`readiness`, `permission_requests`, `egress_declaration`, `version_probe`。

規則：

- `resume_native` 與 `resume_managed` 互斥；都沒有即 `ResumeMode.NONE`。
- `cancel=true` 不代表 `timeout_cleanup_verified=true`。
- `session_attach=true` 不代表任何 resume mode。
- `artifact_import=true` 不代表 imported artifact 是 Evidence。
- module/adapter/runtime 三方 declaration 的交集才是可用 capability；任何不一致
  都 fail closed，不做 silent downgrade。

## 6. Permission, egress and secret contract

### Permission declaration

只允許 bounded classes，例如 `WORKSPACE_READ`、`WORKSPACE_WRITE`、
`PROCESS_EXECUTE`、`NETWORK_EGRESS`、`MCP_TOOL_CALL`、`EXTERNAL_SIDE_EFFECT`。
Module 宣告是 upper bound；每次 runtime request 仍須交由 Core/Human policy 決定。
未知 class、runtime 臨時擴張或「允許全部」均拒絕。

OpenCode 的 global/project default 即使是 `allow`，也不是 PolyNexus Human
authorization。第一版 controlled envelope 必須將未核准 external side effect、任意
network/tool egress、任意 local/remote MCP server、未核准 plugin、npm/package plugin
安裝、remote skill/catalog 與跨 workspace access 全部設為 deny。無法證明 effective
permission/config 與 Core-approved fingerprint 一致時：

- `READINESS=FALSE`
- `DISPATCH=DENIED`
- 不得以 OpenCode 可以正常執行作為 PASS。

### Egress declaration

最少記錄 destination trust、是否 remote model/service、是否含 side effect，以及
實際 observe 到的 route category。`LOCAL_CHILD` 只代表控制通道在本機，不代表
模型推理或工具流量沒有 external egress。外部 runtime 不得利用 subprocess
身分繞過 `evaluate_egress_policy`。

必須分開建模兩個 channel，不能用一個 `NETWORK_EGRESS` boolean 合併：

1. `PROVIDER_MODEL_EGRESS`：external runtime 自身為 model/provider 發出的必要流量，
   仍受 data classification、destination 與 Human gate 約束。
2. `AGENT_EXTENSION_EGRESS`：agent tool、MCP、plugin、command、skill/catalog 或其他
   side-effect 流量；預設拒絕，逐項 allowlist 後仍須接受 per-operation policy。

### Auth / SecretRef

- OpenCode/Gemini/Claude CLI 的既有登入可宣告 `RUNTIME_MANAGED`；PolyNexus 不讀取、
  複製、輸出或提交其 credential store。
- API-key 型路徑只能由 `AuthOwnership.SECRET_REF` 解析短期注入；snapshot 只保留
  opaque `secret_ref_id`。
- Cookie extraction、browser profile copy、session-token replay、raw auth headers 與
  account takeover 一律為 `NOT_AUTHORIZED_INTEGRATION_PATH`。

## 7. Resume model (ADR-007)

| Mode | Truth condition | External declaration rule | Failure behavior |
|---|---|---|---|
| `NATIVE` | 公開介面可由 stable session/checkpoint id 恢復 vendor execution context，且 scope/version 可驗證 | capability + conformance test 都通過才可宣告 | attach mismatch、missing history、版本不相容即 fail closed |
| `MANAGED` | PolyNexus 以自己的 ContextPackage/Artifact/checkpoint 重建新 external session；不是 vendor-native continuation | 必須明示「new external session」與重播邊界 | 不得沿用舊 external session id 或偽稱 native |
| `NONE` | 無可證明的 continuation | default | `resume()` 必須 deterministic reject |

Session record 存在、process 尚在、CLI 有 `--resume` flag 或 workspace 仍存在，都不
足以單獨證明 `NATIVE`。OpenCode ACP 的 load/resume 仍須在 target conformance test
證明 project scope、message replay、active work state 與 version behavior，才能從
proposal 升級為 `NATIVE`。

每次 attach/resume 都必須重新計算並比較 `execution_envelope_fingerprint`，包含
workspace scope mode、effective config、permission policy、plugin set、MCP set、remote
skill/catalog state 與 executable identity。任一 drift 即 fail closed：原 external
session 不得作 `NATIVE` resume；不得藉由建立新 fingerprint 重綁同一 Run。若 future
policy 允許，只能建立新 Run 或以明示的 `MANAGED` 新 session 流程重新經 Human gate。

## 8. Artifact and Evidence boundary

```text
external stream / output / file
    → candidate Artifact and/or EvidenceType.AI_OPINION
    → source session + binding + runtime/adapter version provenance
    → bounded size, path containment, SHA-256, MIME/type validation, sanitization
    → PolyNexus workflow/contract validation
    → Evidence only when the applicable gate accepts it
```

External output 永遠不能自我宣告 `PASS`、`VERIFIED` 或 `CERTIFIED`。即使 vendor
回傳這些文字，也只能是 untrusted content。Core 產生的 runtime observation
Evidence 只能證明「在某 binding/version 下觀察到某 output/lifecycle」，不能證明
output 的實質結論正確。

最低 provenance：Core project/task/run id、external session id 的安全 digest、
runtime/profile/adapter identity、module/adapter/runtime/protocol version、capture
timestamp、source operation/event id、content hash、byte size、sanitization result、
egress decision ref、Human decision ref（若適用）。

## 9. OpenHands / holaOS boundary

### OpenHands-like

- `ARCHITECTURE_CLASSIFICATION=D_COMPOSITE_MODULE`
- Narrow `Software Agent SDK` / Agent Server client 可以形成一個 RUNTIME adapter；
  完整 OpenHands 同時包含 agent lifecycle、workspace、REST/WebSocket surface、
  tools、persistence 與 UI，因此不能整體假裝成單一 runtime module。
- 若日後採用：RUNTIME adapter 只包 conversation execution；workspace/file transfer
  是受 Core policy 管理的 integration seam；UI 是 SURFACE descriptor。
- MCF-02 第一 target 不選 OpenHands，因 scope、dependency、container/workspace 與
  secret surface 大於證明 generic contract 所需。

### holaOS-like

- `ARCHITECTURE_CLASSIFICATION=D_COMPOSITE_MODULE`
- `CURRENT_SUITABILITY=E_NOT_CURRENTLY_SUITABLE_FOR_FIRST_MCF02_TARGET`
- holaOS 自己擁有 workspace identity、runtime database、session/turn、memory、apps、
  browser surface、integration binding 與 harness lifecycle。整體接入會形成雙重
  lifecycle/evidence authority，與本提案不相容。
- 日後只有在 public supported API、auth boundary、license 與 ownership mapping
  獨立通過 architecture/legal/security gate 後，才可拆成 RUNTIME + SURFACE +
  INTEGRATION composite；不得直接讀寫其 `runtime.db` 或私有 desktop IPC。
- 任何 `HOLABOSS_AUTH_COOKIE` 擷取/重放、browser profile takeover、private IPC/API
  reverse engineering 或 unsupported desktop automation：
  `NOT_AUTHORIZED_INTEGRATION_PATH`。

## 10. Security threat model

| THREAT | CORE_OWNER | MODULE_RESPONSIBILITY | FAIL_CLOSED_RULE | EVIDENCE_REQUIRED |
|---|---|---|---|---|
| executable replacement / runtime impersonation | Registry/binding/readiness validation | 提供 resolved launch target並允許 Core獨立hash/probe | canonical path、content SHA-256/equivalent strong identity、observed version任一缺失或 drift 即 `READINESS=FALSE` / `NO_DISPATCH`；不信任自報名稱/版本 | resolved path、Core-computed content digest、version probe、binding/envelope fingerprint |
| capability overclaim | Module bridge + conformance gate | 只宣告實際支援能力 | declaration/observation 不一致即拒絕 factory 或 operation | negative capability probes |
| external configuration injection | Core envelope/config normalizer | 只使用 approved effective config | malicious/unknown global、project或 working-directory config 即 readiness false | config source inventory、normalized digest、malicious `opencode.json` test |
| plugin side-loading | Core plugin allowlist | 回報實際 loaded plugin set且不自行安裝 | `.opencode/plugins/**`、npm/package declaration或未核准 plugin 一律拒絕 launch/dispatch | approved set、filesystem/package scan digest、negative tests |
| MCP side-channel | Core MCP/egress policy | 完整回報 local/remote MCP endpoint與tool request | 未核准 server、transport、destination或啟動 side effect 即拒絕 | MCP set fingerprint、process/network observation、local/remote fixtures |
| permission-policy drift | Core Human/policy authority | 將 permission request交回 Core | OpenCode default allow、fingerprint drift或auto-approve一律不構成授權並拒絕 operation | approved policy digest、Human decision id、effective permission probe |
| workspace/config drift on session resume | RunSupervisor + envelope validator | attach時回報 session working directory/config identity | project scope、staging path或 envelope fingerprint不符即拒絕 attach/NATIVE resume | original/current envelope comparison、path containment、resume denial event |
| stale session attachment | RunSupervisor + session-scope validator | 回報 session generation | scope digest、binding fingerprint 或 generation 不符即拒絕 attach | attach decision、session digest |
| cross-project session leakage | Core project/context boundary | 不得跨 workspace 回傳資料 | project digest 不符、unknown artifact source 即拒絕 | project-scoped fixture與negative test |
| secret leakage | SecretRef/redaction/persistence boundaries | 不輸出 credential/raw headers | secret-shaped output redacted；raw auth material拒絕持久化 | canary secret scan、sanitized result |
| unexpected egress | Core routing/Human gate | 完整宣告目的地、side effect | undeclared route或approval缺失即不送 | policy decision、declared/observed route |
| external runtime auto-send | Human confirmation owner | permission request後等待 | 無 matching Human decision 不得 dispatch/side effect | confirmation id、pre/post-send event |
| cancel failure | RunSupervisor | 實作 cancel observation | 未證明 exact terminal state即 `ORPHANED` | cancel→cleanup→status trace |
| orphan external process | RunSupervisor/process owner | 提供 owned process handle並可 teardown | process/child/stream 任一存活即 cleanup false | PID/handle digest、post-cleanup probe |
| artifact provenance spoofing | Artifact normalization | 提供來源 locator 與 bytes | hash、scope、size、source不符即拒絕 import | independently computed SHA-256 |
| result/evidence fabrication | Workflow/Evidence gate | 只回 candidate result | vendor PASS文字一律不提升 EvidenceStatus | AI_OPINION/Artifact + gate record |
| runtime version drift | Binding/Doctor/conformance | 回報實際 runtime/protocol version | 不符合 pinned policy即 readiness false、不 dispatch | expected/observed version evidence |
| malicious module metadata | ModuleManifest/bridge validator | bounded static metadata | unknown keys/capabilities、secret marker、conflict即拒絕 | parser rejection tests、manifest digest |

## 11. Minimum future implementation allowlist

`IMPLEMENTATION_AUTHORIZED=NO`。下列只供下一個 Human gate 決定；不代表現在可改。

### MUST_CHANGE

- `services/core/src/polynexus_core/runtime/contracts.py`
  - 以 conservative defaults 擴充 external capabilities，或引用新的 bounded
    external descriptor；不得破壞既有三個 adapter construction。
- `services/core/src/polynexus_core/runtime/external_contracts.py`（new）
  - 放置 vendor-neutral descriptor、session handle、event/result/failure category
    contract，以及 execution-envelope digest/reference shape；不得含 raw config、
    process implementation 或 credential value。
- `services/core/src/polynexus_core/runtime/opencode_acp.py`（new）
  - 唯一第一 target adapter；管理 `opencode acp` local child/stdin/stdout/stderr、
    ACP v1、PROJECTED_STAGING、effective-config/executable verification、session scope、
    cancel/cleanup 與 failure normalization。
- `services/core/src/polynexus_core/extensions/runtime_bridge.py`
  - 驗證 external closed capabilities、manifest/profile/descriptor identity 與 factory；
    仍註冊到同一 `RuntimeRegistry`。
- `services/core/src/polynexus_core/runtime/registry.py`
  - 新增 explicit static external-profile policy gate與 adapter-version/envelope binding
    metadata；unknown profile仍無 fallback，不可全面放寬 LOCAL profile。
- `services/core/src/polynexus_core/runtime/routing_policy.py`
  - 將 external runtime 自身 egress 與 side-effect declaration 納入 dispatch 前政策；
    local child process 不得被誤視為 loopback-only inference。
- `services/core/src/polynexus_core/execution_service.py`
  - 維持 binding-first transaction，並在 external input dispatch 前套用 policy/Human
    decision；factory/preflight failure沿用 sanitized fail-closed lifecycle。
- `services/core/src/polynexus_core/runtime/doctor.py`
  - 分離 current probe、adapter declaration、protocol/runtime version 與 accepted
    conformance evidence；不得自動標為 SUPPORTED/CERTIFIED。
- `services/core/tests/test_mcf02_external_runtime_contract.py`（new）
- `services/core/tests/test_mcf02_opencode_acp_runtime.py`（new）
  - 只用 deterministic fake ACP child/server；不得登入、外送或使用真實 credential。

### MAY_CHANGE

- `services/core/src/polynexus_core/domain/runtime_binding.py`
  - 僅在無法由 registry static registration 將 adapter version 寫入現有
    `RuntimeBindingSnapshot.adapter_version` 時，才加入最小 profile metadata；不得
    改 1:1、insert-once、immutable semantics。
- `services/core/src/polynexus_core/runtime/redaction.py`
  - 僅新增經 adversarial tests 證明必要的 ACP/vendor output normalization。
- `services/core/src/polynexus_core/runtime/reconciliation.py`
  - 僅在 Human 明確核准 restart attach/cleanup scope 後，加入 external session
    reconciliation；首輪可保守標 `ORPHANED`。
- `docs/29_ADR_011_RUNTIME_BINDING_AND_TRANSPORT.md` 或新 ADR
  - 若 Human 決定新增 transport/auth/persistence 語意，先更新 ADR 再實作。

### DO_NOT_CHANGE

- Project/Task/Run/WorkflowDefinition identity 或 ownership。
- `RuntimeBindingSnapshot` immutable/insert-once/rebinding prohibition。
- Run lifecycle transition authority、durable ordering或 cancellation cleanup standard。
- Evidence/Finding/Artifact 既有 semantics 以迎合 vendor output。
- migrations、public API、UI、browser companion、raw credential storage。
- dynamic plugin loader、remote install、marketplace、package signing、auto update、
  dependency resolver、hot reload、third-party executable download。
- Claude Code、Gemini CLI、OpenHands、holaOS 等第二個 target adapter。

首輪 external executable 必須由 Human/administrator 預先安裝並由 static composition
指定絕對 executable identity；PolyNexus 不下載、不更新、不安裝 vendor binary。

## 12. Future acceptance test plan

### Contract and registration

- valid descriptor parsing、canonical serialization、version negotiation。
- unknown contract/protocol version、unknown/duplicate capability、secret-shaped metadata、
  identity mismatch、conflicting registration 全部拒絕且 registry 無 partial publish。
- module disabled 後不得建立新 adapter；active Run binding history不變。
- no silent fallback to `reference.local`。

### Session and dispatch

- create session 只在 binding commit 後發生，且 Core Run id 不外借為 vendor authority。
- attach 驗證 project scope digest、binding/envelope fingerprint、generation與 stored directory。
- dispatch 只含 projected ContextPackage/Task；unknown field與整個 workspace隱式匯出拒絕。
- streaming chunk、snapshot、tool/permission、unknown event、out-of-order/duplicate event
  均有 deterministic projection；unknown event 不可完成 Run。
- result capture 成功、empty result、malformed JSON-RPC、stdout contamination、stderr
  secret、oversize frame、child EOF、protocol disconnect。

### Cancel, timeout and cleanup

- cancel before dispatch、during stream、after terminal、duplicate cancel。
- timeout during create/attach/prompt/result。
- cancel acknowledgement但 child仍活、cleanup true但 status仍 running、process tree child
  殘留、pipe未關、forced kill失敗，都必須 `ORPHANED`。
- external process loss、unexpected restart、stale PID/handle reuse。
- cleanup deadline獨立於已耗盡 operation budget，且不接受 silent background work。

### Resume

- `NONE` deterministic reject。
- `NATIVE` load/resume 必須重播正確 project-scoped history並保留 vendor session id；
  session存在但 history/workspace不符時拒絕。
- `MANAGED` 建立新 external session，從 Core-owned checkpoint重建，不冒充 native。
- version/profile drift、deleted session、partial transcript、active old session、跨機器缺少
  state 全部 fail closed。
- effective config、permission、plugin、MCP、skill/catalog、executable identity 或
  workspace path 任一 drift 後的 attach/NATIVE resume 必須拒絕，且不得 rebind 原 Run。

### Policy, secret and provenance

- PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED × STANDARD/LOCAL_PREFERRED/LOCAL_ONLY ×
  trusted/untrusted destination matrix。
- approval-required path 無 Human decision不得寫 stdin或產生 network side effect。
- runtime-managed auth store不可由 adapter讀取或回傳；SecretRef only、canary token、
  cookie/header/path/exception redaction。
- imported artifact path containment、symlink/traversal、size/MIME/hash mismatch、
  cross-project locator、TOCTOU mutation。
- vendor output含 PASS/VERIFIED/CERTIFIED只成為 candidate Artifact/AI_OPINION。
- fabricated Evidence/Finding/Artifact id、spoofed actor/source、duplicate artifact id拒絕。

### Controlled execution envelope negative tests

下列 deterministic fixtures 即使 OpenCode process 可以正常啟動或回傳成功，也必須
`READINESS=FALSE`、`DISPATCH=DENIED` 或在 drift 時拒絕 attach/resume：

- malicious project `opencode.json` 注入 model、agent、command、instruction 或 egress。
- permissive permission configuration（含 default `allow` / auto-approve）。
- `.opencode/plugins/**` side-loading。
- npm/package plugin declaration或 install/download request。
- MCP local server declaration與未核准 child process。
- MCP remote server declaration與未核准 destination/network egress。
- remote skill/catalog declaration或狀態無法固定。
- global/project config disagreement及 precedence 無法 canonicalize。
- binding 後 effective config drift。
- config drift 後 resume 原 external session。
- same canonical executable path但 executable content SHA-256 改變。
- workspace path substitution、symlink/junction escape或 staging root replacement。
- uncontrolled direct-project workspace access。

另需正向證明 explicit `NONE` plugin/MCP/remote-skill sets、approved projected files與
provider/model egress allowlist；沒有這些正向證據不得只靠 negative scan 宣告 ready。

### Ownership and compatibility

- `RunSupervisor` remains sole RunState writer across success/failure/cancel/timeout。
- `RuntimeBindingSnapshot` remains immutable；retry/resume不 rebind。
- adapter/runtime/protocol version mismatch readiness false；Doctor不提升 maturity。
- legacy reference/Codex/OpenCode conformance/local endpoint tests保持相容。
- native Core 在沒有 OpenCode/ACP/vendor credential時仍可用；default profile仍是
  `reference.local`。

## 13. Architecture gate acceptance criteria

Human gate 只有在下列項目明確成立時才可授權 future implementation：

1. 同意 `PRIMARY_TARGET=OpenCode via ACP v1`，且首輪只做一個 target。
2. 同意 external contract closed set 與 Core ownership table。
3. 同意 local child 仍可能 external egress，必須先過 egress/Human gate。
4. 同意 cancel/cleanup exact-state proof 與 `ORPHANED` fail-closed rule。
5. 同意 output 只為 candidate Artifact/AI_OPINION，不是 Evidence。
6. 同意 explicit static executable provisioning；不建立 Plugin Platform。
7. 同意 `POLYNEXUS_CONTROLLED_EXECUTION_ENVELOPE` 與第一版唯一
   `WORKSPACE_SCOPE_MODE=PROJECTED_STAGING`。
8. 同意 effective config/permission/plugin/MCP/skill/executable drift 對 readiness、
   dispatch及 NATIVE resume 全部 fail closed。
9. 核准精確 implementation allowlist、test fixtures 與任何需要的新 ADR。

在此之前：

- `EXTERNAL_RUNTIME_CONTRACT=PROPOSED`
- `THREAT_MODEL=COMPLETE`
- `RESUME_MODEL=DEFINED`
- `ARTIFACT_EVIDENCE_BOUNDARY=DEFINED`
- `MINIMUM_IMPLEMENTATION_SCOPE=PROPOSED`
- `EFFECTIVE_RUNTIME_CONFIG_BOUNDARY=DEFINED`
- `POLYNEXUS_CONTROLLED_EXECUTION_ENVELOPE=DEFINED`
- `WORKSPACE_SCOPE_MODE=PROJECTED_STAGING`
- `PLUGIN_MCP_BYPASS=FAIL_CLOSED`
- `PERMISSION_EGRESS_BYPASS=FAIL_CLOSED`
- `EXECUTABLE_IDENTITY_BINDING=DEFINED`
- `CONFIG_DRIFT_RESUME_RULE=FAIL_CLOSED`
- `IMPLEMENTATION_AUTHORIZED=NO`
