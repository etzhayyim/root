# etzhayyim-project-projector

AI Project Manager — recursive project convo (projector.etzhayyim.com)。

**URL**: `https://projector.etzhayyim.com`
**performerType**: `service`
**Primary DID**: `did:web:projector.etzhayyim.com`

## Architecture

**Projector = AI PM Agent-First Project Management。** 1 project = 1 convoId = 1 PM AI Agent (ops.etzhayyim.com)。Recursive nesting (max depth 10): root project → sub-projects (channels/threads/email-inboxes)。1 concept で Discord channels, Slack threads, Teams channels, email inboxes を統一。

### Core Concepts

| Concept | Implementation |
|---|---|
| **Project** | `com.etzhayyim.projector.newProjectConvo` で作成。convoId = projectId。path-based DID 自動発行 |
| **PM Agent** | `did:web:ops.etzhayyim.com` が全 project の PM。slash commands + MCP tool calling |
| **Recursive Nesting** | parentProjectUri で parent-child。max depth 10。kind: general/channel/thread/email-inbox |
| **Auto Email** | 各 project に `{slug}@etzhayyim.com` メールアドレス自動生成。email-relay が inbound routing |
| **Membership** | `com.etzhayyim.convo.membership` record。auto-enroll on first access |
| **Tasks** | `com.etzhayyim.convo.projectTask` record。/task, /done slash commands |

### NSID (com.etzhayyim.projector.*)

| NSID | Type | Description |
|---|---|---|
| `com.etzhayyim.projector.newProjectConvo` | procedure | Project + DM convo 同時作成 (recursive nesting + email auto-gen) |
| `com.etzhayyim.projector.getProjectConvo` | query | Project convo with context overlay + children |
| `com.etzhayyim.projector.listProjectConvos` | query | Project convo list (parentUri filter for sub-projects) |
| `com.etzhayyim.projector.listProjectTree` | query | Recursive tree traversal (BFS, flat list with depth) |
| `com.etzhayyim.projector.updateProjectConvo` | procedure | Update metadata (name, description, status) |
| `com.etzhayyim.projector.archiveProjectConvo` | procedure | Recursive archive (BFS all children) |
| `com.etzhayyim.projector.sendProjectMessage` | procedure | Slash command routing + LLM + MCP tool calling |
| `com.etzhayyim.projector.listConvoTasks` | query | Task list for project |
| `com.etzhayyim.projector.addConvoTask` | procedure | Add task from convo |
| `com.etzhayyim.projector.completeConvoTask` | procedure | Complete task |
| `com.etzhayyim.projector.addConvoMember` | procedure | Add member to project |
| `com.etzhayyim.projector.getConvoProjectStatus` | query | Project status + metrics + hierarchy |
| `com.etzhayyim.projector.moveProject` | procedure | Re-parent project |
| `com.etzhayyim.projector.loadProjectChat` | query | Load conversation + members via Hyperdrive-backed graph SQL path |
| `com.etzhayyim.projector.resolveProjectEmail` | query | Email → convoId resolution (email-relay inbound) |
| `com.etzhayyim.projector.listProjectNotifications` | query | Cross-project notifications (7d window) |
| `com.etzhayyim.projector.getProjectUnreadCounts` | query | Unread count per project convoId |
| `com.etzhayyim.projector.createProjectConvo` | procedure | Create project convo with peer DID (DM variant) |
| `com.etzhayyim.projector.branchConvo` | procedure | Git-like conversation fork (virtual inheritance, no message copy) |
| `com.etzhayyim.projector.listBranches` | query | List branches for a conversation |
| `com.etzhayyim.projector.exploreThoughts` | procedure | Tree of Thoughts (Yao et al.) — branch-based thought expansion + self-eval |
| `com.etzhayyim.projector.consistentAnswer` | procedure | Self-Consistency (Wang et al.) — N-path sampling + majority vote |
| `com.etzhayyim.projector.addReflection` | procedure | Reflexion (Shinn et al.) — store episodic memory lesson |
| `com.etzhayyim.projector.listReflections` | query | List reflexion episodic memory for a conversation |

### Conversation Branching (git-like fork)

**Branch = conversation fork with virtual message inheritance.** No message copying. Branch stores `branchSourceConvoId` + `branchPointRkey`. `loadProjectChat` for a branch loads parent messages up to the branch point, then the branch's own messages.

```
Main convo:  msg1 → msg2 → msg3 → msg4 → msg5
                              ↑ branchPointRkey
Branch A:    msg1 → msg2 → msg3 (inherited) → branchMsg1 → branchMsg2
Branch B:    msg1 → msg2 → msg3 (inherited) → branchMsg1 (different direction)
```

| Concept | Implementation |
|---|---|
| **Branch creation** | `com.etzhayyim.projector.branchConvo` or `/branch [name]` slash command |
| **Virtual inheritance** | Branch convo stores `branchSourceConvoId` + `branchPointRkey`. No message duplication |
| **Chat loading** | `loadProjectChat` detects branch → loads parent messages up to branch point (marked `inherited: true`) + branch's own messages |
| **Branch listing** | `com.etzhayyim.projector.listBranches` returns all branches for a source convo |
| **Member inheritance** | Branch inherits all members from source project at creation time |
| **projectKind** | Branch convos have `projectKind: "branch"` |

**Data model (ADR-0036 Phase 2, 2026-04-21):**
- `vertex_convo.branch_source_convo_id` + `branch_point_rkey` + `status` + `display_name` + `created_date` — typed columns on the child convo row, populated by the `com.etzhayyim.convo.convo` PDS write. `listBranches` reads these directly.
- `com.etzhayyim.projector` — project metadata with `branchSourceConvoId` + `branchPointRkey` fields (still PDS-written; pending project-metadata sweep)
- ~~`com.etzhayyim.projector.branch`~~ — **RETIRED**. Write-only AT record (never read) dropped at all 3 call sites (`/branch` slash, `branchConvo` XRPC, `exploreThoughts` ToT). No replacement needed — branch metadata lives on the child convo's typed columns.

### Agentic BPMN (Camunda-aligned, 2026-04-21 Phase 3)

Projector flow runs (`vertex_projector_flow_run`) map onto **Camunda 8.9's agentic BPMN pattern**: the `AI Agent Task` connector paired with an ad-hoc sub-process whose activities are the LLM's tool pool. No new BPMN task type is introduced — Camunda itself uses standard `serviceTask` + connector, not a dedicated `agent.reasoning` type. We follow the same convention.

**`vertex_projector_flow_node.node_type` enum**:

| node_type | BPMN analogue | Role |
|---|---|---|
| `agentLoop` | `serviceTask` + AI Agent connector | The container running the LLM feedback loop. At most one per flow (usually). Reads `model_id` / `temperature_bps` / `max_tokens` / `prompt_template` columns. |
| `tool` | Activity inside the ad-hoc sub-process | Unit of work the LLM can invoke. `name`, `description`, `config_json` define the tool schema exposed to the LLM. When `bpmn_task_id` is set, the node references a Kyber `BPMN_CATALOG` entry and reuses that task's contract (see ADR-0025). |
| `approval` | `userTask` + escalation event | Human-in-the-loop gate (Camunda agentic pattern #3). Runner suspends the run with `status='suspended'`, `resume_at=null`, until a caller completes it. |
| `script` | `scriptTask` | Pure deterministic logic — no LLM call, no human. Used for pre/post-processing. Phase 5d Function Registry (ADR-0045 §D14) |
| `guardrail` | `businessRuleTask` + DMN decision table | Camunda agentic pattern #4. Phase 5d script reuse; script must return `{allow: boolean, reason?: string}`. `allow=false` blocks flow with `agent.guardrail.denied` OCEL event (ADR-0045 §D15) |
| `http` | `serviceTask` | Outbound call via `sdk.Send`. Same shape as tool, but never selected by the LLM — only by deterministic edges. |

`~~agent.reasoning~~` as a leaf node_type was **rejected** during Phase 3 design: Camunda represents LLM reasoning as the **container** (`agentLoop`), not as a leaf. Leaf nodes are tools. This matches Camunda docs: "each BPMN activity inside an ad-hoc sub-process is effectively a tool exposed to the LLM."

**`edge_projector_flow_edge` semantics**:
- **Deterministic sequencing only.** `script` → `agentLoop` → `approval` → `script` sequences are expressed as edges.
- **The LLM's tool selection inside `agentLoop` does NOT use edges.** Tools are discovered by `flow_vertex_id` filter inside the loop; the LLM picks which to call based on its own reasoning.
- `edge_kind ∈ {sequence, conditional, interrupt, fallback}`. `condition_expr` is evaluated against `flow_run.vars_json` only on conditional edges.

**OCEL 2.0 event naming** (emitted to `com.etzhayyim.apqc.apqcEvent` via Kyber projector; the rkey goes into `vertex_projector_flow_step.ocel_event_id`):

| eventType | Emitted when |
|---|---|
| `agent.iteration.start` | `agentLoop` node begins an LLM call |
| `agent.iteration.end` | `agentLoop` LLM call returns (success or error) |
| `tool.called` | LLM selected a `tool` node and the runner dispatched it |
| `tool.completed` | Tool returned a result to the loop |
| `agent.guardrail.denied` | `script` / DMN rule blocked a proposed tool call (Camunda pattern #4) |
| `agent.escalated` | `approval` node suspended the run for human review (Camunda pattern #3) |
| `agent.human.resumed` | Human completed the `approval` and runner resumed |
| `flow.started` / `flow.completed` / `flow.failed` | `vertex_projector_flow_run` status transitions |

**Bridging to the Kyber BPMN_CATALOG (ADR-0025)**:
- `vertex_projector_flow_node.bpmn_task_id` = `BPMN_CATALOG[i].taskId` makes that catalog entry directly invokable as a tool from the `agentLoop`.
- OCEL events emitted by such a tool use the catalog entry's `ocelEventType` (e.g. `journal.posted`, `po.approved`), NOT the projector-generic `tool.called` — the catalog OCEL type is more specific and the correct audit surface.
- This lets the LLM plan a sequence of ERP operations as BPMN catalog tools, with full APQC × OCEL audit by reuse rather than duplication.

**No schema migration required** — the Phase 1 tables (`vertex_projector_flow` / `_node` / `_run` / `_step` / `edge_projector_flow_edge`) already carry every column this design uses. Phase 4 (runner) wires the semantics live.

### Reasoning Frameworks (agent loop 統合)

4 つの論文ベース推論フレームワークを agent loop (`sendProjectMessage`) に統合。

| Framework | 論文 | Integration | Slash Command | NSID |
|---|---|---|---|---|
| **Chain-of-Thought** | Wei et al. 2022 | Always-on: system prompt に `<reasoning>` 構造化推論を注入。LLM 応答から CoT を抽出し response.reasoning に返却 | (自動) | — |
| **Self-Consistency** | Wang et al. 2022 | N 個の推論パスを temperature=0.7 で並列サンプリング → majority vote で最も整合的な回答を選択 | `/consistent {question}` | `com.etzhayyim.projector.consistentAnswer` |
| **Tree of Thoughts** | Yao et al. 2023 | Branch infra を活用し thought tree を展開。各 approach を branch として作成 → self-evaluation (score 0-10) → best path 推薦 | `/explore {question}` | `com.etzhayyim.projector.exploreThoughts` |
| **Reflexion** | Shinn et al. 2023 | 失敗/次善の試行を episodic memory buffer として AT record 化。次回の system prompt に自動注入し同じ失敗を回避 | `/reflect {text}` | `com.etzhayyim.projector.addReflection` |

**Data flow:**
```
User message → sendProjectMessage
  ├── Reflexion: load episodic memory → system prompt injection
  ├── CoT: <reasoning>...</reasoning> in LLM output → extracted to response.reasoning
  ├── /consistent → Self-Consistency: N parallel LLM calls → majority vote
  ├── /explore → ToT: generate approaches → branch each → self-evaluate → rank
  └── /reflect → Reflexion: store lesson → available in next invocation
```

**Reflexion format:** `/reflect attempt | outcome | lesson` (structured) or `/reflect {free text lesson}` (auto-extracts context from chat history)

### PM Built-in Tools (LLM text-based tool calling)

| Tool | Description |
|---|---|
| `pm.search_agents` | Platform AI agent semantic search (embedding + keyword) |
| `pm.invite_agent` | Invite agent to project → member + tools available |
| `pm.web_research` | site.etzhayyim.com gateway URL fetch → Markdown |
| `pm.create_entity_did` | Create path-based DID for discovered entity |
| `pm.graph_search` | Knowledge graph search (duplicate prevention) |

### Slash Commands

| Command | Model | Description |
|---|---|---|
| `/task {title}` | — | Add task |
| `/done {taskId}` | — | Complete task |
| `/status` | — | Project status |
| `/mcp` | — | MCP tool list |
| `/invite {DID}` | — | Invite member |
| `/members` | — | Member list |
| `/image {prompt}` | Murakumo WAI-REAL | Image generation |
| `/think {prompt}` | qwq-32b | Deep reasoning |
| `/new` | — | New sub-project |
| `/branch [name]` | — | Git-like conversation fork at current point |
| `/explore {question}` | Murakumo | Tree of Thoughts (Yao et al.) — multi-path exploration |
| `/consistent {question}` | Murakumo | Self-Consistency (Wang et al.) — N-path sampling + majority vote |
| `/reflect {text}` | — | Reflexion (Shinn et al.) — store episodic memory lesson |

### Data Flow

```
yoro /projects FAB tap
  → com.etzhayyim.projector.newProjectConvo({name, members, parentProjectUri?, kind?})
  → PDS handler:
    1. Create convo record (com.etzhayyim.convo.convo, projectBound: true)
    2. Register project DID (did:web:{host}:project_{convoId})
    3. Register profile (app.bsky.actor.profile)
    4. Create project metadata (com.etzhayyim.projector.project)
  → response: {convoId, projectId, did, name, email, depth, kind}
  → yoro navigates to /projects/{projectId}
```

```
User sends message in project chat
  → com.etzhayyim.projector.sendProjectMessage({convoId, text})
  → PDS handler:
    1. /image → Murakumo WAI-REAL fleet
    2. /think → qwq-32b deep reasoning
    3. Normal → Save user msg → Load chat history → Discover member tools
       → Build system prompt + tools → Murakumo LLM
       → Parse [TOOL_CALL: name(args)] → Execute tools → Reply
  → response: {reply, messages, imageB64?, thinking?}
```

### Integration Points

| System | Integration |
|---|---|
| **yoro.etzhayyim.com** | `/projects` route (list), `/projects/{projectId}` route (chat) |
| **ops.etzhayyim.com** | PM Agent DID (`did:web:ops.etzhayyim.com`) |
| **email-relay** | Inbound email → `resolveProjectEmail` → `sendProjectMessage` |
| **dispatcher** | Email forward → `newProjectConvo` + `sendProjectMessage` |
| **browser-host** | Browser session → project convo creation |
| **mangaka** | Manga project convo record creation |

## WIT

- Contract WIT: `_archive/00-contracts/wit/wit/deps/etzhayyim-projector/package.wit` (archived 2026-04-12)
- Ops domain WIT: `60-apps/etzhayyim-project-ops/wit/ops/package.wit` (`projector` interface)

## Runtime

T1 MCP-Compose — handler logic は PDS (`pds-handlers-etzhayyim.ts`) に co-located。独立 Worker なし。yoro UI が client。

**Migration in progress (ADR-2604271600)**: Phase 1+2 で reasoning + tool calling を L7 (LangServer + LangServer + LangGraph) に移行中。Phase 3 cutover 完了後は CF Worker は L3 dispatcher (XRPC accept → `sdk.zeebe.publishMessage` → 202) のみとなる。詳細は §L7 LangGraph Migration を参照。

## L7 LangGraph Migration (Phase 1+2, ADR-2604271600)

**目的**: 30s/128MB の CF Worker 制約を外し、N-path Self-Consistency や ToT 展開を durable orchestration で実行する。設計詳細: `90-docs/adr/2604271600-projector-l7-langgraph-integration.md`。

### BPMN 構成 (4 process definitions)

| BPMN | NSID | 役割 |
|---|---|---|
| `sendProjectMessage.bpmn` | `com.etzhayyim.apps.projector.sendProjectMessage` | Root router。XOR gateway で slash command を dispatch |
| `agentLoop.bpmn` | `com.etzhayyim.apps.projector.agentLoop` | Default path (LangGraph ReAct + CoT + Reflexion + tool calling) |
| `treeOfThoughts.bpmn` | `com.etzhayyim.apps.projector.treeOfThoughts` | `/explore` (ToT expand → evaluate → rank) |
| `selfConsistency.bpmn` | `com.etzhayyim.apps.projector.selfConsistency` | `/consistent` (parallel sample + majority vote) |

`/reflect` は `projector.reflexion.write` 単発 task で完結 (sub-process なし)。`/image` `/think` は Phase 3 で BPMN 化、Phase 1+2 では deferred shim を返して CF Worker direct path を維持。

### LangServer primitives

`40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/projector.py` に 11 task type を実装:

| Task type | 役割 | LangGraph |
|---|---|---|
| `projector.command.parse` | 先頭 slash 抽出 | — |
| `projector.command.deferred` | /image・/think の defer 応答 | — |
| `projector.reflexion.load` | `vertex_projector_reflection` から最大 5 件読込 | — |
| `projector.reflexion.write` | `/reflect attempt | outcome | lesson` 永続化 | — |
| `projector.tools.discover` | PM built-in tools + member MCP tools 連結 | — |
| `projector.tool.call` | 単発 PM tool dispatch | — |
| `projector.agent.loop` | **ReAct (reason → guardrail → dispatch → reason)** | StateGraph |
| `projector.tot.expand` | **expand → evaluate → finalize** | sequential |
| `projector.sc.parallel` | **N path parallel + Counter majority vote** | asyncio.gather |
| `projector.persist.message` | `vertex_projector_message` INSERT + `edge_projector_convo_message` | — |

LLM transport は `kotodama.llm.call_tier` (Vultr Serverless + RunPod fallback、ADR-2604231328)。LangChain `ChatOpenAI` は不採用 — `langchain-openai` を加えると worker image が倍増し、`langchain-core` (langgraph 0.2 経由で transitively 利用可能) のメッセージ envelope だけで設計が完結するため。

### Camunda 8.9 agentic-pattern alignment

| Camunda pattern | 実装 |
|---|---|
| #1 AI Agent Task connector | `Task_AgentLoop` serviceTask (taskDefinition `projector.agent.loop`) |
| #2 ad-hoc sub-process tools | LangGraph `dispatch` node が tool catalog から動的選択 (BPMN tool task は持たない、tool catalog は per-conversation) |
| #3 escalation / human-in-the-loop | (未実装) Phase 5 で `Task_AgentLoop` に approval boundary event を追加 |
| #4 guardrail | `BE_GuardrailDenied` boundary error event (`agent.guardrail.denied`)。LangGraph `guardrail` node が deny-list で block |

### データモデル

- `vertex_bpmn_process_def` × 4 + `vertex_bpmn_lexicon_binding` × 4 (migration `20260427160000_seed_projector_bpmn_actors.ts`)
- `vertex_projector_reflection` (既存、migration `20260421010000_*`) — Reflexion episodic memory
- `vertex_projector_message` + `edge_projector_convo_message` — projector reply と conversation containment
- `vertex_projector_flow_run/_step` (既存、Phase 1) — Camunda agentic flow audit (Phase 5 で OCEL emit に拡張)

### Phase status

| Phase | 状態 | 内容 |
|---|---|---|
| **1** | ✅ scaffolded | BPMN 4 + LangServer primitives + migration + worker registration |
| **2** | ✅ scaffolded | ToT + SC sub-processes |
| **3** | ✅ flag-gated, default off | `PROJECTOR_USE_BPMN=1` で CF Worker `handleSendProjectMessage` が `dispatcher.etzhayyim.com:8080/xrpc/com.etzhayyim.apps.projector.sendProjectMessage` に `waitUntil(fetch())` で委譲し 202 + convoId を返却。yoro Worker が `GET /sse/projects/:convoId` (90s budget) を提供、`/projects/[projectId]/+page.svelte` が `EventSource` で append。`PROJECTOR_PERSIST_VIA_PDS=1` で reply を `generic.pds.dispatch` 経由 federate (default は `vertex_projector_message` 直書き)。`projector.auth.mint` task type で BPMN flow が Service Auth JWT を取得可能 |
| **4** | pending | TS reasoning path (`pds-handlers-etzhayyim.ts` 約 1500 LoC) 削除 — Phase 3 canary が clean に通った後 |
| **5** | pending | DMN guardrail + per-tool RACI + 5% canary A/B + `/image` `/think` の専用 BPMN sub-process 化 |

### Cutover の前提

- F5 watcher (`dispatcher.etzhayyim.com:8080`) が `vertex_bpmn_process_def` の `status='active'` row を 30s 以内に LangServer deploy
- LangServer pod 再起動が必要 (新 task type 認識: `projector.*` × 11)
- Phase 3 適用前は CF Worker の reasoning path がそのまま動作 (BPMN seed 適用だけでは behavior は変わらない)
- Phase 3 cutover は **PDS Worker `PROJECTOR_USE_BPMN` env を 1 にして再 deploy のみ**。rollback は flag を 0 (or unset) に戻す 1 deploy

### Phase 3 環境変数

| Env | Worker | 効果 |
|---|---|---|
| `PROJECTOR_USE_BPMN` | atproto.etzhayyim.com (PDS) | `=1` で `sendProjectMessage` が BPMN dispatcher に委譲 + 202 即返却 |
| `BPMN_URL` | atproto.etzhayyim.com (PDS) | dispatcher base URL (default `https://dispatcher.etzhayyim.com`) |
| `DISPATCHER_INTERNAL_SECRET` | atproto.etzhayyim.com (PDS) | dispatcher の internal-trust check 用 (Secret binding 推奨) |
| `PROJECTOR_PERSIST_VIA_PDS` | LangServer pod | `=1` で reply を `generic.pds.dispatch` 経由 PDS write (federable)。default は `vertex_projector_message` 直 INSERT (graph-visible) |
| `PDS_SERVICE_AUTH_MINT_URL` / `..._SECRET` / `..._TTL_SEC` | LangServer pod | 既存 Service Auth mint。`projector.auth.mint` task が共有

### 禁止事項

- LangServer primitive 内から `com.atproto.repo.createRecord` を直叩き (ADR-2604240946 既知の 401)。Projector reply は `vertex_projector_message` 直接 INSERT、federation が必要な場合のみ Phase 3 Service Auth JWT mint を使う
- `/explore` `/consistent` を CF Worker から並行実装 (BPMN seed 適用後は Phase 3 までは旧 TS が引き続き動くが、二重実装の改修禁止)
- `langchain-openai` 依存追加 — `kotodama.llm.call_tier` が canonical transport

## Conventions

- **NSID**: `com.etzhayyim.projector.*` (4 segment, WIT 完全修飾)
- **Collection**: `com.etzhayyim.projector.project` (project metadata record)
- **AT URI**: `at://{did}/com.etzhayyim.projector/{rkey}`
- **camelCase**: All NSID methods are camelCase
