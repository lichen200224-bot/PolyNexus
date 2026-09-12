# MCF-02 External Runtime Target Evaluation

## 文件定位

- `REPORT_TYPE=HUMAN_READABLE_ARCHITECTURE_RESEARCH`
- `LANGUAGE=TRADITIONAL_CHINESE`
- `RESEARCH_AS_OF=2026-09-12`
- `CANONICAL_START_SHA=f0c0b986380dc21d103d4e856057cb8ac435a8f9`
- `PREVIOUS_REVIEW_CANDIDATE_SHA=6bfa2f8653d0f667979d48a3628a77b15584e11d`
- `PREVIOUS_REVIEW_RESULT=MCF02_ARCHITECTURE_REVIEW_NEED_FIX`
- `IMPLEMENTATION_AUTHORIZED=NO`
- `LIVE_VENDOR_LOGIN_OR_SEND=NONE`

原建議位置 `docs/research/` 在 canonical repository 中不存在。為維持現有
architecture/governance deliverable 全部集中於 `docs/tasks/` 的慣例，本報告放在
`docs/tasks/`，並與主提案互相連結。

本報告只採用截至上述日期可公開查閱的官方文件、官方 source repository 與
本 repository 實際檔案。無法由這些來源確認者標示 `[待驗證]`；「有 session」
不推論成 resume，「有 cancel request」不推論成 cleanup 成功。

## 1. 結論摘要

- `PRIMARY_TARGET=OpenCode via ACP v1 (local stdio child process)`
- `BACKUP_TARGET=Gemini CLI via ACP v1 (local stdio child process)`
- `GENERIC_PROTOCOL_BASELINE=ACP v1`
- `FIRST_IMPLEMENTATION_TARGET_COUNT=1`
- `FIRST_REAL_EXTERNAL_EXECUTABLE_TARGET=OpenCode via ACP v1`

OpenCode 的官方 ACP surface 已公開定義 local child-process/stdin/stdout、protocol
v1、multi-session、load/resume、cancel、streaming、permission 與 auth ownership；
它同時以 MIT 發布，且能用一個具體 agent 證明 vendor-neutral contract。這是
最小而非最熱門的選擇。[OpenCode ACP documentation](https://opencode.ai/v2/docs/cli/acp/)

Gemini CLI 也有官方 `--acp` surface，包含 initialize/auth/new/load/prompt/cancel
與 file-system proxy，因此適合作為同一 adapter contract 的下一個 compatibility
target；但服務存取政策正在轉換，且 cleanup/process-tree 真實性仍需獨立測試，
所以列為 backup，不與 primary 同時實作。
[Gemini CLI ACP mode](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/acp-mode.md)
[Gemini CLI terms and privacy](https://github.com/google-gemini/gemini-cli/blob/main/docs/resources/tos-privacy.md)

此選擇不沿用 repository 既有 deterministic `OpenCodeRuntimeAdapter` 的 acceptance。
MCF-02 的 OpenCode target 是首次受控啟動 real external `opencode acp` executable、解析
其 working-directory effective configuration，並驗證 session/lifecycle/egress 的新路徑。
既有 conformance PASS 不得作為本 target 的 live、readiness 或 conformance PASS。

## 2. 評分方法

每項 `0–2`：`2=公開文件支持且可直接對應`、`1=部分支持/需 adapter 補強或有
重要限制`、`0=不支持、無法證明或與邊界衝突`。總分滿分 30；分數只用於 target
routing，不是產品完成度或 vendor certification。

| # | Criterion |
|---:|---|
| 1 | documented/supported integration surface |
| 2 | local-first compatibility |
| 3 | deterministic process/session control |
| 4 | cancellation/cleanup truthfulness |
| 5 | artifact/result accessibility |
| 6 | session resume capability |
| 7 | observable lifecycle |
| 8 | authentication safety |
| 9 | no private API dependence |
| 10 | no cookie/session-token replay |
| 11 | license/redistribution compatibility |
| 12 | cross-platform support |
| 13 | maintenance burden（高分代表負擔低） |
| 14 | user experience |
| 15 | strategic value to PolyNexus |

| Candidate | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| OpenCode via ACP v1 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | **28** |
| Codex CLI / SDK reference | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | **27** |
| Gemini CLI via ACP | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 1 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | **26** |
| ACP-compatible agent（protocol only） | 2 | 2 | 2 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 2 | **25** |
| Claude Code Agent SDK | 2 | 1 | 2 | 1 | 2 | 2 | 2 | 1 | 2 | 2 | 1 | 2 | 1 | 2 | 2 | **25** |
| OpenHands Agent SDK/Server | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 1 | 0 | 1 | 2 | **24** |
| LM Studio local harness | 2 | 2 | 1 | 0 | 1 | 1 | 2 | 1 | 2 | 2 | 1 | 2 | 2 | 2 | 1 | **22** |
| Ollama local harness | 2 | 2 | 1 | 0 | 0 | 0 | 1 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 1 | **20** |
| holaOS full workspace | 1 | 2 | 1 | 1 | 2 | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 0 | 2 | 1 | **15** |

Codex 的總分很高，但本 repository 現有 Codex path 是 deterministic conformance
reference，且本輪查得的 non-interactive public surface 對「cancel 後外部 process
與 child work 已停止」沒有像 ACP target 一樣形成最小可交換協定。為避免把既有
identity熟悉度當成 target 選擇理由，本輪仍選 OpenCode/ACP。

## 3. Target reports

### 3.1 OpenCode via ACP v1

- `TARGET=OpenCode via ACP v1`
- `SUPPORTED_PUBLIC_INTERFACE=ACP v1 stdio; headless HTTP/OpenAPI server; generated/embedded SDK`
- `CLI=YES — opencode acp, opencode serve, session/export commands`
- `API=YES — loopback HTTP OpenAPI 3.1, sessions/messages/files/events`
- `SDK=YES — generated client and @opencode/sdk embedded host`
- `MCP=YES — client may supply local or HTTP MCP servers for ACP sessions`
- `ACP=YES — protocol version 1 over newline-delimited JSON-RPC/stdin/stdout`
- `LOCAL_PROCESS_CONTROL=YES — client owns child; stdin close ends private server`
- `REMOTE_CONTROL=YES — supported HTTP server; remote exposure requires explicit auth/network policy`
- `SESSION_ATTACH=YES — list/load/resume/fork/close/delete; stored directory is authoritative`
- `STREAMING=YES — text, reasoning, tools, permission, usage; server also exposes SSE events`
- `CANCEL=YES — active prompt cancel; close interrupts; PolyNexus仍須驗證 process/cleanup`
- `RESUME=YES — public load/resume and message replay; PolyNexus classification remains proposed NATIVE until conformance passes`
- `ARTIFACT_ACCESS=YES — session diff/files plus sanitized CLI export; bytes/hash仍由 Core驗證`
- `AUTH_MODEL=Provider credentials remain owned by OpenCode; HTTP server can use Basic auth`
- `SECRET_RISK=MEDIUM — provider credential store and optional server password must remain outside Core output`
- `EFFECTIVE_CONFIG_RISK=HIGH — working directory may activate configuration, plugins, models, agents, commands, skills, instructions and MCP`
- `CONTROLLED_ENVELOPE_REQUIRED=YES — PROJECTED_STAGING; explicit plugin/MCP/remote-skill sets; Core permission/egress policy`
- `EXECUTABLE_IDENTITY_REQUIRED=canonical resolved path + Core-computed content SHA-256/equivalent + observed version`
- `LICENSE_OR_INTEGRATION_CONCERN=MIT; executable must be preinstalled, not downloaded by MCF-02`
- `PRIVATE_API_REQUIRED=NO`
- `COOKIE_OR_TOKEN_REPLAY_REQUIRED=NO`
- `POLYNEXUS_FIT=STRONG — exactly one local process and a standard session/control protocol`
- `MATURITY=HIGH_FOR_PROPOSAL / NOT_YET_POLYNEXUS_CONFORMANT`
- `RECOMMENDATION=PRIMARY_TARGET`

Sources:
[OpenCode ACP](https://opencode.ai/v2/docs/cli/acp/),
[OpenCode server](https://dev.opencode.ai/docs/server/),
[OpenCode CLI](https://opencode.ai/docs/cli/),
[OpenCode embedded SDK](https://opencode.ai/v2/docs/build/sdk),
[OpenCode repository/license](https://github.com/anomalyco/opencode).

### 3.2 Gemini CLI via ACP

- `TARGET=Gemini CLI via ACP`
- `SUPPORTED_PUBLIC_INTERFACE=ACP stdio; headless JSON/stream-json; project-scoped session management`
- `CLI=YES — gemini --acp; gemini -p; --output-format json|stream-json`
- `API=PARTIAL — Gemini services有public API，但 CLI control首選ACP；不以underlying private service代替CLI`
- `SDK=PARTIAL — SDK core session/resume存在；公開設計文件仍標示部分 advanced features未完成`
- `MCP=YES — ACP initialize可提供MCP connection；CLI另有MCP management`
- `ACP=YES — initialize/authenticate/newSession/loadSession/prompt/cancel`
- `LOCAL_PROCESS_CONTROL=YES — stdio child process`
- `REMOTE_CONTROL=NO VERIFIED GENERAL REMOTE DAEMON — [待驗證]`
- `SESSION_ATTACH=YES — loadSession and project-scoped --resume/session IDs`
- `STREAMING=YES — ACP updates and headless JSONL events`
- `CANCEL=YES AT PROTOCOL LEVEL; cleanup/process-tree proof=[待驗證]`
- `RESUME=YES — session UUID/load; must still pass scope/history conformance`
- `ARTIFACT_ACCESS=PARTIAL — file-system proxy/tool results; stable artifact export contract [待驗證]`
- `AUTH_MODEL=Google account, Gemini API key, or Vertex AI; official CLI owns login`
- `SECRET_RISK=MEDIUM — cached credentials/API keys; Core must not read them`
- `LICENSE_OR_INTEGRATION_CONCERN=Apache-2.0 CLI; service terms depend on auth path. Direct third-party access to underlying Gemini CLI services is disallowed, so only official CLI/ACP or documented API-key route is acceptable`
- `PRIVATE_API_REQUIRED=NO`
- `COOKIE_OR_TOKEN_REPLAY_REQUIRED=NO`
- `POLYNEXUS_FIT=STRONG, but current access-policy transition and cleanup evidence reduce first-target certainty`
- `MATURITY=MEDIUM-HIGH / CURRENT SERVICE POLICY REQUIRES PINNED REVIEW`
- `RECOMMENDATION=BACKUP_TARGET`

Sources:
[ACP mode](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/acp-mode.md),
[headless mode](https://geminicli.com/docs/cli/headless/),
[session management](https://geminicli.com/docs/cli/session-management/),
[authentication](https://geminicli.com/docs/get-started/authentication/),
[terms/license](https://github.com/google-gemini/gemini-cli/blob/main/docs/resources/tos-privacy.md).

### 3.3 ACP-compatible agents (generic protocol)

- `TARGET=ACP-compatible agents`
- `SUPPORTED_PUBLIC_INTERFACE=JSON-RPC 2.0 protocol version negotiated at initialize`
- `CLI=NOT A PROTOCOL REQUIREMENT`
- `API=YES — bidirectional RPC/notifications over process transport`
- `SDK=YES — official Rust, TypeScript, Python, Kotlin/JVM and Java resources are listed`
- `MCP=YES AS NEGOTIATED CLIENT/SESSION CAPABILITY; not equivalent to ACP`
- `ACP=YES`
- `LOCAL_PROCESS_CONTROL=YES TYPICALLY — agents通常是client子程序`
- `REMOTE_CONTROL=NOT BASELINE / [待驗證] per implementation`
- `SESSION_ATTACH=OPTIONAL — session/load requires advertised capability`
- `STREAMING=YES — session/update notifications`
- `CANCEL=YES REQUEST — session/cancel is a notification with no response; cleanup proof is outside baseline`
- `RESUME=OPTIONAL — loadSession capability; session存在本身不構成resume`
- `ARTIFACT_ACCESS=PARTIAL — content/resources/fs methods exist, but no universal trusted Artifact/Evidence object`
- `AUTH_MODEL=Negotiated authenticate methods; concrete credential ownership is agent-specific`
- `SECRET_RISK=LOW AT PROTOCOL / IMPLEMENTATION-DEPENDENT`
- `LICENSE_OR_INTEGRATION_CONCERN=Apache-2.0 protocol/schema; agent licenses remain separate`
- `PRIVATE_API_REQUIRED=NO`
- `COOKIE_OR_TOKEN_REPLAY_REQUIRED=NO`
- `POLYNEXUS_FIT=STRONG AS GENERIC PROTOCOL, INCOMPLETE AS A CONCRETE TARGET`
- `MATURITY=STABLE WIRE VERSION 1; optional capabilities vary`
- `RECOMMENDATION=GENERIC_PROTOCOL_BASELINE, paired with exactly one concrete agent`

Sources:
[ACP overview](https://github.com/agentclientprotocol/agent-client-protocol/blob/main/docs/protocol/v1/overview.mdx),
[ACP repository/versioning/libraries](https://github.com/agentclientprotocol/agent-client-protocol).

### 3.4 Claude Code / Claude Agent SDK

- `TARGET=Claude Code Agent SDK`
- `SUPPORTED_PUBLIC_INTERFACE=CLI print mode and Python/TypeScript Agent SDK`
- `CLI=YES — -p, JSON/stream-json, --resume/--continue, permission modes`
- `API=NO SEPARATE CLAUDE CODE HTTP CONTROL API VERIFIED; Agent SDK is the supported programmatic surface`
- `SDK=YES — query()/ClaudeSDKClient, streaming messages, sessions and interrupt`
- `MCP=YES — Claude Code can consume MCP; SDK exposes MCP status/control`
- `ACP=[待驗證] — no official Claude Code ACP surface found in reviewed docs`
- `LOCAL_PROCESS_CONTROL=YES — SDK hosts a long-running Claude Code subprocess`
- `REMOTE_CONTROL=PARTIAL — hosted SDK patterns and product remote-control exist, but a generic PolyNexus remote adapter contract is [待驗證]`
- `SESSION_ATTACH=YES — capture session_id, resume/continue, list/read session messages`
- `STREAMING=YES — async message iterator and streaming input`
- `CANCEL=YES — ClaudeSDKClient.interrupt(); subprocess cleanup proof仍需adapter測試`
- `RESUME=YES — session ID and external SessionStore; conversation history, not automatically filesystem state`
- `ARTIFACT_ACCESS=YES THROUGH CONTROLLED WORKSPACE/FILE CHECKPOINTS; no automatic Evidence semantics`
- `AUTH_MODEL=Claude account/Console, API route, Bedrock or Vertex depending setup; runtime-managed or SecretRef`
- `SECRET_RISK=MEDIUM-HIGH — local credential/session transcripts and provider keys`
- `LICENSE_OR_INTEGRATION_CONCERN=Public SDK/CLI terms available; redistribution/bundling rights [待驗證]`
- `PRIVATE_API_REQUIRED=NO`
- `COOKIE_OR_TOKEN_REPLAY_REQUIRED=NO`
- `POLYNEXUS_FIT=STRONG PROPRIETARY ADAPTER, weaker generic proof than ACP`
- `MATURITY=HIGH PUBLIC SDK / NOT POLYNEXUS-CONFORMANT`
- `RECOMMENDATION=LATER TARGET; do not bundle or automate login in MCF-02`

Sources:
[Claude Agent SDK Python reference](https://code.claude.com/docs/en/agent-sdk/python),
[Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions),
[Claude Code CLI reference](https://docs.anthropic.com/en/docs/claude-code/cli-usage),
[Claude Code authentication setup](https://docs.anthropic.com/en/docs/claude-code/getting-started),
[MCP overview](https://docs.anthropic.com/en/docs/mcp).

### 3.5 OpenHands / OpenHands-like runtime

- `TARGET=OpenHands Software Agent SDK / Agent Server`
- `SUPPORTED_PUBLIC_INTERFACE=Python SDK plus REST/WebSocket Agent Server`
- `CLI=YES — OpenHands CLI/headless paths are public`
- `API=YES — conversations, events, health, workspace commands/files`
- `SDK=YES — Conversation/Agent/Workspace abstractions`
- `MCP=YES — Agent configuration supports MCP`
- `ACP=PARTIAL — current docs mention ACP-capable conversation endpoints in specific remote paths; universal contract/support scope [待驗證]`
- `LOCAL_PROCESS_CONTROL=YES — local SDK/server or Docker workspace`
- `REMOTE_CONTROL=YES — RemoteConversation via HTTP/WebSocket`
- `SESSION_ATTACH=YES — existing conversation_id and persistence restore`
- `STREAMING=YES — callbacks/WebSocket events`
- `CANCEL=PARTIAL — pause takes effect between steps and may wait for current LLM call; exact stop/cleanup proof absent`
- `RESUME=YES — persisted conversation ID/state or pause→run; must distinguish native state from workspace restoration`
- `ARTIFACT_ACCESS=YES — upload/download, workspace files, tool/event log`
- `AUTH_MODEL=LLM provider API key or remote Agent Server/API workspace key`
- `SECRET_RISK=HIGH — conversation persistence can include secret registry/provider configuration; Core must never import raw state`
- `LICENSE_OR_INTEGRATION_CONCERN=Software Agent SDK is MIT; Docker/runtime/cloud service terms and redistribution remain separate`
- `PRIVATE_API_REQUIRED=NO FOR SDK/SERVER PATH`
- `COOKIE_OR_TOKEN_REPLAY_REQUIRED=NO`
- `POLYNEXUS_FIT=COMPOSITE — narrow SDK runner fits RUNTIME; full platform does not`
- `MATURITY=MEDIUM-HIGH PUBLIC SDK, HIGH INTEGRATION SURFACE`
- `RECOMMENDATION=D_COMPOSITE_MODULE; not first target`

Sources:
[Agent Server overview](https://docs.openhands.dev/sdk/guides/agent-server/overview),
[Conversation API reference](https://docs.openhands.dev/sdk/api-reference/openhands.sdk.conversation),
[pause/resume](https://docs.openhands.dev/sdk/guides/convo-pause-and-resume),
[persistence](https://docs.openhands.dev/sdk/guides/convo-persistence),
[SDK MIT license](https://github.com/OpenHands/software-agent-sdk/blob/main/LICENSE).

### 3.6 holaOS / holaOS-like workspace

- `TARGET=holaOS full workspace/runtime`
- `SUPPORTED_PUBLIC_INTERFACE=Open-source workspace/runtime implementation and contributor docs; stable third-party control contract [待驗證]`
- `CLI=[待驗證] as a supported external integration contract`
- `API=PARTIAL — local runtime HTTP routes exist, but reviewed docs primarily describe internal desktop/runtime contracts`
- `SDK=PARTIAL — app SDK/bridge exists for holaOS apps, not verified as external agent lifecycle SDK`
- `MCP=YES — workspace/app MCP registry and allowlists`
- `ACP=[待驗證]`
- `LOCAL_PROCESS_CONTROL=YES INTERNALLY — desktop launches embedded runtime`
- `REMOTE_CONTROL=PARTIAL/INTERNAL — control-plane and bridge paths exist; public support boundary [待驗證]`
- `SESSION_ATTACH=INTERNAL STATE EXISTS; supported external attach contract [待驗證]`
- `STREAMING=INTERNAL UI/runtime path; third-party stable stream contract [待驗證]`
- `CANCEL=INTERNAL lifecycle; exact public cancel/cleanup contract [待驗證]`
- `RESUME=PARTIAL — persisted harness/session continuity exists; cannot infer a PolyNexus-safe NATIVE resume contract`
- `ARTIFACT_ACCESS=YES THROUGH WORKSPACE FILES/outputs; provenance ownership conflicts must be resolved`
- `AUTH_MODEL=Mixed hosted account, BYOK/provider keys, runtime config, integrations and desktop auth cookie`
- `SECRET_RISK=HIGH — browser profiles, integrations, runtime config, auth cookie and shared memory surfaces`
- `LICENSE_OR_INTEGRATION_CONCERN=Modified Apache-2.0 requires commercial license for hosted/embedded commercial distribution in stated cases`
- `PRIVATE_API_REQUIRED=YES IF USING DESKTOP IPC/INTERNAL ROUTES; public supported external API [待驗證]`
- `COOKIE_OR_TOKEN_REPLAY_REQUIRED=NO FOR PURE OSS FILE/PROCESS STUDY; YES-RISK for desktop hosted auth path, therefore forbidden`
- `POLYNEXUS_FIT=LOW AS SINGLE RUNTIME; it already owns workspace/session/memory/integration lifecycle`
- `MATURITY=COMPOSITE PRODUCT, NOT A MINIMAL EXTERNAL RUNTIME CONTRACT`
- `RECOMMENDATION=D_COMPOSITE_MODULE LATER; E_NOT_CURRENTLY_SUITABLE for first MCF-02 target`

Sources:
[workspace model](https://www.holaos.ai/docs/concepts/workspace-model),
[desktop internals](https://www.holaos.ai/docs/contribute/desktop/internals),
[MCP support](https://www.holaos.ai/docs/concepts/agent-harness/mcp-support),
[holaOS repository](https://github.com/holaboss-ai/holaOS),
[modified license](https://github.com/holaboss-ai/holaOS/blob/main/LICENSE).

`NOT_AUTHORIZED_INTEGRATION_PATH`：讀取/重放 `HOLABOSS_AUTH_COOKIE`、複製登入
browser profile、直接改 `runtime.db`、呼叫未承諾為 public 的 desktop IPC/private
route、reverse engineer hosted API，或以 browser account takeover 控制 workspace。

### 3.7 LM Studio local model harness

- `TARGET=LM Studio / llmster local harness`
- `SUPPORTED_PUBLIC_INTERFACE=REST v1, OpenAI/Anthropic-compatible endpoints, Python/TypeScript SDK, CLI daemon`
- `CLI=YES — lms daemon/server/chat`
- `API=YES — local REST with stateful chats and streaming`
- `SDK=YES — lmstudio-js and lmstudio-python`
- `MCP=YES — native v1 API can use configured/remote MCP under explicit settings`
- `ACP=NO VERIFIED`
- `LOCAL_PROCESS_CONTROL=YES — local daemon/server; existing PolyNexus adapter already uses loopback endpoint only`
- `REMOTE_CONTROL=OPTIONAL NETWORK BINDING, not allowed by current PolyNexus loopback policy`
- `SESSION_ATTACH=PARTIAL — stateful chat exists; agent/workspace attach contract [待驗證]`
- `STREAMING=YES`
- `CANCEL=[待驗證] exact accepted-work cancellation/cleanup`
- `RESUME=PARTIAL CHAT CONTINUITY; not execution resume`
- `ARTIFACT_ACCESS=LIMITED — model result/tool content, no generic workspace Artifact lifecycle`
- `AUTH_MODEL=local no-auth or server API token; remote model link is separate`
- `SECRET_RISK=MEDIUM if API token/MCP enabled; low for loopback no-auth inference`
- `LICENSE_OR_INTEGRATION_CONCERN=SDK/API terms and model licenses vary; redistribution [待驗證]`
- `PRIVATE_API_REQUIRED=NO`
- `COOKIE_OR_TOKEN_REPLAY_REQUIRED=NO`
- `POLYNEXUS_FIT=GOOD MODEL ENDPOINT, NOT SUFFICIENT EXTERNAL AGENT RUNTIME`
- `MATURITY=HIGH LOCAL INFERENCE SURFACE`
- `RECOMMENDATION=retain as local endpoint/reference; not MCF-02 first target`

Sources:
[LM Studio developer docs](https://lmstudio.ai/docs/developer),
[REST API](https://lmstudio.ai/docs/developer/rest),
[server settings/security](https://lmstudio.ai/docs/developer/core/server/settings),
[server CLI](https://lmstudio.ai/docs/cli/serve/server-start).

### 3.8 Ollama local model harness

- `TARGET=Ollama local harness`
- `SUPPORTED_PUBLIC_INTERFACE=local HTTP API and CLI`
- `CLI=YES`
- `API=YES — generate/chat/model endpoints`
- `SDK=OFFICIAL LANGUAGE LIBRARIES [待驗證] for this report; HTTP API is sufficient reference`
- `MCP=NO NATIVE AGENT CONTROL SURFACE VERIFIED`
- `ACP=NO`
- `LOCAL_PROCESS_CONTROL=YES at server process level`
- `REMOTE_CONTROL=HTTP bind possible but outside current PolyNexus loopback-only boundary`
- `SESSION_ATTACH=NO VERIFIED AGENT SESSION`
- `STREAMING=YES — NDJSON is default for selected endpoints`
- `CANCEL=[待驗證] accepted model work cleanup; client disconnect不自動證明server work停止`
- `RESUME=NONE VERIFIED`
- `ARTIFACT_ACCESS=NO GENERIC ARTIFACT CONTRACT`
- `AUTH_MODEL=local server; deployment/network authentication depends on operator setup [待驗證]`
- `SECRET_RISK=LOW ON STRICT LOOPBACK; increases if externally exposed`
- `LICENSE_OR_INTEGRATION_CONCERN=server/model licenses must be reviewed separately [待驗證]`
- `PRIVATE_API_REQUIRED=NO`
- `COOKIE_OR_TOKEN_REPLAY_REQUIRED=NO`
- `POLYNEXUS_FIT=MODEL ENDPOINT ONLY`
- `MATURITY=HIGH INFERENCE / LOW AGENT-LIFECYCLE FIT`
- `RECOMMENDATION=not MCF-02 external agent target`

Sources:
[Ollama generate API](https://docs.ollama.com/api/generate),
[Ollama streaming](https://docs.ollama.com/api/streaming).

### 3.9 Codex CLI / current PolyNexus reference path

- `TARGET=Codex CLI / SDK reference`
- `SUPPORTED_PUBLIC_INTERFACE=codex exec JSONL, resume, TypeScript SDK and App Server documentation`
- `CLI=YES — non-interactive codex exec`
- `API=YES VIA DOCUMENTED SDK/APP SERVER; exact MCF-02 session contract [待驗證]`
- `SDK=YES — official Codex SDK documentation`
- `MCP=YES — Codex consumes stdio/Streamable HTTP MCP servers`
- `ACP=NO OFFICIAL SURFACE VERIFIED IN REVIEWED DOCUMENTS`
- `LOCAL_PROCESS_CONTROL=YES — CLI child process`
- `REMOTE_CONTROL=PARTIAL — exec-server remote is documented for credential use; full lifecycle semantics [待驗證]`
- `SESSION_ATTACH=YES — exec resume by last or session ID`
- `STREAMING=YES — JSONL thread/turn/item/error events`
- `CANCEL=[待驗證] at stable session protocol level; OS process kill alone不證明external work cleanup`
- `RESUME=YES — explicit session ID; scope/history conformance still required`
- `ARTIFACT_ACCESS=YES — file changes, command items, structured output/last-message file; Core must recapture/hash`
- `AUTH_MODEL=ChatGPT sign-in, API key, enterprise access token or workload identity depending path`
- `SECRET_RISK=HIGH if auth.json copied; official docs say treat it as a password`
- `LICENSE_OR_INTEGRATION_CONCERN=Open-source Codex client/public docs; service terms/auth path still apply`
- `PRIVATE_API_REQUIRED=NO`
- `COOKIE_OR_TOKEN_REPLAY_REQUIRED=NO — copying auth.json is specifically not an integration design`
- `POLYNEXUS_FIT=STRONG LATER TARGET; current repository adapter is deterministic-only`
- `MATURITY=HIGH PUBLIC AUTOMATION SURFACE / NOT LIVE-CONFORMANT IN POLYNEXUS`
- `RECOMMENDATION=REFERENCE, not first target`

Sources:
[Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode),
[Codex authentication](https://learn.chatgpt.com/docs/auth),
[Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli),
[OpenAI developer documentation](https://developers.openai.com/).

## 4. Selection rationale and rejection boundaries

### Why OpenCode/ACP is primary

1. 一個 local child/stdin/stdout boundary 足以驗證 generic contract，不需要先建
   remote control plane、container platform 或 browser automation。
2. ACP `initialize` 與 capability negotiation 對應 registry/bridge fail-closed需求。
3. session create/load/resume/cancel/update/permission 已有 public protocol，而非解析
   human-oriented terminal text。
4. OpenCode 的 private server 隨 child process 結束，適合建立 process ownership 與
   orphan test；但 cleanup仍必須由 PolyNexus獨立驗證。
5. provider credential 可保持 `RUNTIME_MANAGED`，不需要 SecretRef 值、cookie 或
   browser session replay。
6. Primary 身分只表示最小、公開、可驗證的 real executable/ACP target；不表示可以
   信任 OpenCode global/project defaults。第一版必須由 Core 建立
   `POLYNEXUS_CONTROLLED_EXECUTION_ENVELOPE` 與 `PROJECTED_STAGING` workspace。
7. effective config、permission、plugin、MCP、remote skill/catalog或 executable content
   無法固定／發生 drift 時，readiness/dispatch/attach/NATIVE resume 均 fail closed。

### Why Gemini/ACP is backup

它能重用同一 ACP-oriented contract，並驗證 adapter 沒有偷偷硬編碼 OpenCode
event/session behavior。但在 first implementation 同時加入它會把 authentication、
service terms、access-tier transition 與 vendor-specific output差異帶入同一 gate，
違反「先證明一條正確 path」原則。

### Explicitly not selected

- Claude Code：公開 SDK 很強，但它是另一套 proprietary session/control shape；應在
  ACP contract證明後另做 target gate。
- OpenHands：SDK/Server 合理，但完整 integration 是 composite且 scope太大。
- holaOS：完整產品已擁有與 PolyNexus重疊的 workspace/lifecycle/memory/evidence
  surface，且有 license/auth/private-boundary問題。
- LM Studio/Ollama：是 model endpoint/harness，不是可證明完整 external agent
  session lifecycle 的最小 target。
- Codex：保留為現有 reference與 later target，不以既有 conformance名稱取得優先權。

## 5. Native baseline and non-claims

- PolyNexus Core default 仍必須是 `reference.local`；沒有任何 external executable、
  account、API key 或 network 時仍可使用。
- OpenCode、Gemini CLI、Claude Code、Codex、OpenHands、holaOS、LM Studio、Ollama
  都是 replaceable capability provider，不是 Core dependency。
- `PRODUCTION_READINESS=NOT_CLAIMED`
- `PLUGIN_PLATFORM=NOT_COMPLETE`
- `MCF02=NOT_STARTED`
- `EXTERNAL_RUNTIME_EXPANSION=NOT_COMPLETE`
- `OVERALL_PROJECT_COMPLETION=NOT_DEFINED`
