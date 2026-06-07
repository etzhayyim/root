---
id: adr-2604282300
title: "Cloudflare = SvelteKit Edge Proxy のみ; Business Logic = K8s Pod + AgentGateway MCP + LangServer"
status: active
doc_type: adr
topic: runtime-layer-separation
authoritative: true
last_verified: 2026-05-13
authoritative_for:
  - cf-worker-responsibility-boundary
  - cloudflare-sveltekit-edge-proxy-only
  - pruned-worker-tier-topology
  - agentgateway-mcp-pod-routing
  - pod-side-langserver-runtime
  - k8s-runtime-scope
  - python-worker-pod-fastapi-granian-surface
  - kotoba-udf-business-logic-scope
  - cf-worker-sse-pass-through
  - generic-pds-dispatch-k8s-internal-routing
  - maps-worker-thin-edge-boundary
related:
  - adr-2604262000-edge-thin-app-runtime-k8s-zeebe-registry
  - adr-0056-bpmn-as-actor
  - adr-0044-kotoba-udf-language-strategy
  - adr-2604261000-mcp-registry-via-kysely-schema
  - adr-2604251801-cron-three-layer-consolidation
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-2605101200-ai-cxo-roles-lsp-resident
supersedes:
  - adr-2604262000-edge-thin-app-runtime-k8s-zeebe-registry
superseded_by: []
amended_by:
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
---

# Context

既存の ADR-2604262000 (proposed) が「CF Worker は thin edge」という方向性を示したが、
当初の ADR-2604282300 は Cloudflare Worker を T1/T2/T3 に分類する運用表現を残していた。
この分類は migration inventory としては便利だったが、現在の runtime 方針としては過剰である。

2026-05-13 時点の問いは次に更新する:

1. Cloudflare に残すものを **SvelteKit edge proxy** に限定できるか?
2. business logic / execution / DB I/O / LLM call を **K8s pod 側のみ**に閉じられるか?
3. Pod 側の公開面を **AgentGateway MCP** と **LangServer (JSON-RPC/LSP style)** に統一できるか?
4. Kotoba/Datomic UDF はどの種の stateless logic に限るか?

これらを一本の active ADR として確定する。

# Decision

## 2026-05-13 Amendment: Tier topology pruning

T1/T2/T3 を **Cloudflare Worker の実行 tier として扱う考え方は廃止**する。
以後、T1/T2/T3 は古い migration inventory または data sensitivity の文脈でだけ使い、
runtime placement の判断軸にしない。

採用する topology は次の 1 本に絞る:

- Cloudflare は **SvelteKit edge proxy** のみ。UI asset、auth/CORS、request
  normalization、SSE pass-through、AgentGateway MCP への proxy を持つ。
- Business logic、DB read/write、LLM/tool execution、workflow execution は
  **K8s pod 側のみ**で実行する。
- Public MCP/XRPC/HTTP request は Cloudflare で終端後、**AgentGateway MCP**
  に渡す。AgentGateway は actor/tool/NSID を解決し、pod-local LangServer
  へ dispatch する。
- Pod 側の actor 実装は **LangServer** (JSON-RPC 2.0 / LSP-style resident
  server) を標準形とする。LangGraph / Pregel / LangChain / domain Python
  handler は LangServer の method handler または internal runtime として扱う。
- CF Worker から Kotoba/Datomic / Hyperdrive / D1 domain table へ直接接続しない。
  ADR-2605111200 の edge-only/no-RW-connection rule をこの ADR に取り込む。

古い Zeebe/pyzeebe/SpiffWorkflow/T1/T2/T3 記述は migration source topology
としてのみ読む。新規 actor / app / command では採用しない。

## 2026-05-13 Amendment: SpiffWorkflow retirement

SpiffWorkflow は Zeebe 置換先としても採用しない。BPMN XML は process contract /
audit documentation として残してよいが、実行 runtime は LangGraph / Pregel /
LangChain に移す。

- New runtime target: LangServer method → LangGraph StateGraph / Pregel graph /
  LangChain runnable / plain `kotodama` async handler.
- Zeebe, pyzeebe, SpiffWorkflow workers are deprecated execution paths.
- Existing worker files may remain only as migration source until their task
  handlers are wrapped by LangGraph/Pregel/LangChain.
- New Helm/K8s manifests must not introduce `zeebe`, `pyzeebe`,
  `spiffworkflow`, or `spiff-worker` runtime kinds.

## 2026-05-08 Amendment: K8s Runtime Split

This ADR remains authoritative for the **thin CF Worker boundary**: edge
workers keep auth, request normalization, facade routing, and SSE pass-through;
business logic stays off the edge. The Zeebe-specific runtime below is amended:

- Main business runtime: ADR-2605080600 LangGraph Server + Granian.
- BPMN-native flows are compiled or wrapped into LangGraph/Pregel/LangChain;
  SpiffWorkflow is not a target runtime.
- Kotoba/Datomic UDF remains for row-wise/stateless SQL-adjacent logic.
- Zeebe/pyzeebe/SpiffWorkflow are not targets for new work; references below
  describe migration source topology.

## Pruned Layer 分離の原則

```
Browser / MCP client / AT Protocol client
        |
        v  (HTTPS / XRPC / MCP)
┌──────────────────────────────────────────────┐
│  Cloudflare Worker / Pages                   │
│  SvelteKit edge proxy only                   │
│  • SvelteKit SSR/CSR asset shell             │
│  • Auth / DPoP / CORS / Service-token check  │
│  • XRPC/MCP/HTTP facade                      │
│  • Request normalize / Response shape        │
│  • SSE/WebSocket pass-through when required  │
│  ✗ Business logic  ✗ LLM/tool call           │
│  ✗ DB read/write  ✗ workflow execution       │
└──────────────┬───────────────────────────────┘
               |
               v  (MCP Streamable HTTP / internal trust)
┌──────────────────────────────────────────────┐
│  AgentGateway MCP  (K8s ingress/gateway)     │
│  • vertex_actor_registry / vertex_bpmn_*     │
│  • vertex_mcp_tool_def discovery             │
│  • Rego / DMN policy gate                    │
│  • actor_did + nsid + tool name resolution   │
│  • pod-local routing / auth propagation      │
└──────────────┬───────────────────────────────┘
               |
               v  (ClusterIP / Unix socket / JSON-RPC)
┌──────────────────────────────────────────────┐
│  K8s Pod: resident LangServer                │
│  (JSON-RPC 2.0 / LSP-style, Granian/ASGI)    │
│                                              │
│  cxo/*, actor/*, tool/* methods              │
│  LangGraph / Pregel / LangChain runtime      │
│  kotodama domain modules                   │
│  generic.db.* / generic.llm.* / generic.http │
│  audit emit / checkpoint / status stream     │
└──────────────┬───────────────────────────────┘
               |
               v
┌──────────────────────────────────────────────┐
│  Kotoba/Datomic (L4 Graph DB + UDF engine)       │
│  • SQL UDF: rule / regex / aggregate         │
│  • Python External UDF: LLM / IO (io_threads)│
│  • Rust Embedded UDF: hash / protobuf        │
│  Streaming MV (< 100ms) / Iceberg archive    │
└──────────────────────────────────────────────┘
```

---

## Runtime placement rule

Runtime placement は tier ではなく **edge proxy / pod execution** の二択で判断する。

| Placement | 許可される責務 | 禁止 |
|---|---|---|
| **Cloudflare SvelteKit edge proxy** | UI asset/SSR shell、auth/CORS、request shaping、MCP/XRPC facade、SSE pass-through、static/cacheable read-through | business rule、LLM/tool call、domain DB I/O、workflow state、actor-specific command implementation |
| **K8s pod LangServer** | business logic、LLM/tool execution、Kotoba/Datomic read/write、checkpoint、workflow/HITL、audit、stream generation | public unauthenticated exposure、Cloudflare binding 依存、edge-only cache mutation |

例外的に Cloudflare binding (Turnstile, Durable Object, KV/R2 object edge
cache, OAuth callback glue など) が必要な場合でも、そこに business logic を置かない。
binding adapter は request を正規化し、AgentGateway MCP へ渡すだけにする。

---

## Registry Actor の配置

`vertex_actor_registry` + `vertex_mcp_tool_def` に行がある actor は
Cloudflare Worker を持たない。Cloudflare は `/mcp` / `/xrpc/:nsid` を
AgentGateway MCP に proxy し、AgentGateway が registry を見て LangServer
method に変換する。

実行フロー:

```
MCP tools/call or XRPC nsid
  → Cloudflare SvelteKit edge proxy
  → AgentGateway MCP
  → vertex_mcp_tool_def / vertex_actor_registry / policy gate
  → pod-local LangServer method
  → LangGraph / Pregel / LangChain / kotodama handler
  → Kotoba/Datomic write + audit + status stream
```

新規 actor の追加手順:

1. `00-contracts/lexicons/com/etzhayyim/apps/<actor>/<method>.json` 作成
2. `vertex_actor_registry` に行 INSERT
3. `vertex_mcp_tool_def` に行 INSERT (`sync-mcp-registry.py` で sync 可)
4. LangServer method (`actor.<name>.<method>` or `tool.<name>`) を
   `kotodama` / LangGraph / Pregel / LangChain 側に実装
5. 必要なら `vertex_bpmn_process_def` / `vertex_bpmn_lexicon_binding` を
   process contract / audit documentation として追加するが、実行は
   LangServer method に bind する
6. AgentGateway registry reload で `/mcp` / `/xrpc/{nsid}` live

**CF Worker の新規作成・再デプロイは不要**。

---

## Pod-side LangServer の位置づけ

K8s Deployment 内の resident LangServer が唯一の business execution surface。
Zeebe/pyzeebe/SpiffWorkflow worker は historical migration source であり、
新規実装では LangServer method handler として実装する。

責務:

- JSON-RPC 2.0 / LSP-style initialize, capability, request, notification,
  cancellation, streaming partial result
- AgentGateway MCP からの pod-local method dispatch
- `kotodama` / LangGraph / Pregel / LangChain module を import して domain logic 実行
- Kotoba/Datomic への domain read/write (`asyncpg` / psycopg3 / SQLAlchemy Core)
- LLM/tool call と external API fetch
- OCEL audit emit (`generic.audit.emit`)
- Shinka heartbeat (`com.etzhayyim.shinka.tick`)

### FastAPI + Granian / LangServer pod surface

Python worker pod は `kotodama` image 内で **FastAPI + Granian** を標準
ASGI surface として持ち、その中に LangServer endpoint を置く。

用途:

- `/healthz` / `/readyz` / `/metrics` / `/livez` などの Kubernetes probe と
  Prometheus scrape
- AgentGateway MCP からの in-cluster control / async job adapter endpoint
- RunPod / browser / batch worker からの pod-local callback receiver
- long-running task の progress/read model bridge。ただし durable state は
  Kotoba/Datomic / LangGraph checkpoint / B2 に書く

起動形:

```text
python worker pod:
  - process A: granian --interface asgi kotodama.<service>.lsp_server:app
  - optional process B: background scheduler / LangGraph worker
```

ルール:

- FastAPI app は `kotodama` importable module として実装する。
- Granian は production server。`uvicorn --reload` は local dev のみ。
- HTTP endpoint は namespace / ClusterIP / private tunnel 内に閉じる。
- public XRPC / MCP / browser facade は Cloudflare SvelteKit edge proxy が持つ。
- LangServer は request id / cancellation / progress notification を必ず扱う。
- 長時間処理の同期応答は accepted/status/read-model に限定し、進捗は SSE または
  LangServer notification として返す。

禁止事項:

- LangServer pod の外部公開 (public facade は Cloudflare/AgentGateway が持つ)
- pod を Cloudflare Worker の代替として直接 public endpoint 化
- per-actor Cloudflare Worker の作成

---

## Kotoba/Datomic UDF の business logic 配置

ADR-0044 の language strategy を business logic 分類と対応させる:

| Logic 種別 | Kotoba/Datomic UDF 種別 | 例 |
|---|---|---|
| 分類ルール / regex / keyword match | **SQL UDF** (plan-time inline) | yabai phishing classifier |
| COUNT / SUM / GROUP BY aggregation | **SQL UDF** or streaming MV | mv_actor_social_stats |
| hash / protobuf decode / WASM compat compute | **Embedded Rust UDF** | vertex_id hash generation |
| LLM 推論 / 外部 API fetch / heavy Python lib | **Python External UDF (`@udf(io_threads=100)`)** | embedding UDF, classify gray-zone |
| 複数ステップの業務フロー / retry が必要な処理 | **LangServer + LangGraph / Pregel / LangChain** (UDF 不可) | sentinelAnalyze, crawlAds |

**CRITICAL**: Python External UDF の `io_threads` 省略時は serial (`io_threads=1`) になり 10× 遅い。IO-bound UDF は必ず `io_threads=50..200` を明示する (ADR-0044 §D3)。

Pod-side LangServer と Kotoba/Datomic UDF の使い分け:

- **UDF**: Kotoba/Datomic MV の SELECT 時に同期実行。行単位 transform / classify。状態なし。
- **LangServer**: 複数ステップ / retry / pause / LLM multi-turn / 外部 API cursor が必要な処理。状態あり。

---

## Cloudflare / SvelteKit edge proxy の責務 (確定リスト)

### 残すもの

| 責務 | 実装 |
|---|---|
| SvelteKit edge routing | SvelteKit adapter-cloudflare / Worker entry |
| SvelteKit SSR/CSR asset shell | build 成果物と route shell |
| Auth / DPoP / CORS / Service-token validation | `10-protocol/xrpc/src/ServiceAuth` |
| XRPC facade (`/xrpc/:nsid`) | AgentGateway MCP への proxy |
| MCP facade (`/mcp`) | AgentGateway MCP への Streamable HTTP proxy |
| Response shaping / error normalization | edge layer のみ |
| SSE pass-through | `text/event-stream` を stream のまま返す |
| `/_app/meta` health | Worker 自身の liveness |

### 出してはいけないもの

| 禁止 | 理由 |
|---|---|
| LLM call (direct `fetch` to murakumo / RunPod) | pod-side LangServer の責務 |
| Kysely domain DB read/write (`vertex_...`) | pod-side LangServer / Kotoba/Datomic UDF の責務 |
| BPMN / workflow engine direct call | AgentGateway / LangServer internal routing の責務 |
| per-actor cron (`triggers.crons`) | K8s CronJob → AgentGateway/LangServer run に移行 |
| Actor-specific business rule コード | `kotodama` / LangGraph / Pregel / LangChain module の責務 |
| 長時間処理の同期 JSON 待ち | SSE / async workflow の責務 |
| SSE response の `resp.text()` / `resp.json()` buffering | heartbeat が潰れ Cloudflare/client timeout を再発させる |

## Long-running response contract — 2026-04-29

CF Worker 全体の前提を次の通り更新する。

1. **長時間処理は HTTP 同期 JSON を前提にしない。** LLM、RAG、画像/動画、
   crawler、外部 API retry、pod-side backlog の影響を受ける actor は
   `Accept: text/event-stream` または `?stream=1` で SSE を使う。
2. **CF Worker は SSE を終端しない。** Worker は auth / routing / trust header
   付与までを行い、origin の `ReadableStream` body をそのまま `Response` に
   渡す。`resp.text()` / `resp.json()` / full buffering は禁止。
3. **Heartbeat は origin 側が送る。** AgentGateway MCP / LangServer は
   `started` → periodic `heartbeat` → `complete` / `error` を送る。Worker は
   その byte stream を維持するだけ。
4. **Business logic は stream の中で実行しない。** CF Worker は token 生成、
   RAG retrieval、LangGraph node、workflow job polling を持たない。すべて
   AgentGateway MCP + pod-side LangServer + Kotoba/Datomic に置く。
5. **SSE は per-actor Worker 作成理由ではない。** 単方向 server-push は
   AgentGateway / LangServer 経由で実現する。固定互換 URL や CF binding が必要な
   場合でも、Worker は adapter/proxy に限定する。

Historical validation: `com.etzhayyim.apps.llm.answerWithKnowledge?stream=1` was served by
`dispatcher.etzhayyim.com` with SSE events while the actual work runs in the
`llm-knowledge-zeebe-worker` pool. PDS/ATProto workers must preserve this stream
when proxying BPMN NSIDs. New validation target is the same stream contract via
AgentGateway MCP and pod-side LangServer.

2026-04-29 phase validation: `llm.etzhayyim.com/xrpc/com.etzhayyim.apps.llm.answerWithKnowledge`
now delegates to the same PDS/BPMN path and preserves SSE (`started`,
`heartbeat`, `complete`) without buffering. The `llm_knowledge` Python primitive
must not synthesize an extractive fallback answer when the LLM backend fails or
returns empty content. It returns `ok=false`, `error`, and `errorKind` so the
caller can surface backend loss explicitly.

2026-04-29 Projector validation: `yoro.etzhayyim.com/projects/*` now routes Pokopia /
Dream Island questions, or explicit `/knowledge ...`, to
`llm.etzhayyim.com/xrpc/com.etzhayyim.apps.llm.answerWithKnowledge?stream=1` using browser
`fetch()` stream parsing. The public `llm.etzhayyim.com` hostname is served by the
RunPod gateway Worker, so that Worker exposes only this knowledge XRPC as a
thin CORS/SSE proxy and calls the `kotodama-llm8cf4ai` Worker by service binding.
The actor Worker then reaches the PDS/BPMN dispatcher path by service binding.
This avoided intra-zone HTTPS subrequest 522/recursion issues and kept all
knowledge retrieval and LangGraph execution off Cloudflare. The 2026-05-13
successor keeps the same property, but the execution target is
AgentGateway MCP → pod-side LangServer, not Python Zeebe workers. LLM backend
failure is reported as error, not hidden behind extractive answer composition.

---

## 既存 Worker の pruning 分類

Worker は tier ではなく、残す理由で分類する。

| Worker class | Action | 理由 |
|---|---|---|
| SvelteKit app shell / UI host | Keep as edge proxy | UI asset/SSR shell、auth/CORS、MCP/XRPC pass-through |
| PDS / AT Protocol federation boundary | Keep as protocol edge adapter | Federation/public protocol boundary。ただし domain business logic は pod へ出す |
| OAuth / auth callback / WebAuthn adapter | Keep as auth edge adapter | Browser/security ceremony と CF binding が必要。権限判定後の業務処理は pod |
| Static/cacheable read-through adapter | Keep only if edge cache materially helps | tile/static/object cache。canonical state mutation は pod |
| `kotodama-g0v*` / app-specific business Worker | Retire | AgentGateway MCP + LangServer method へ移す |
| `bpmn-dispatcher` / legacy dispatcher | Fold or demote | AgentGateway MCP の routing function に吸収し、Zeebe-specific gRPC front を廃止 |

---

## Migration ガイドライン

### 既存 business Worker の退役手順

1. `pnpm --dir 30-graph/graph-schema verify:<actor>` が green になるまで
   LangServer method + `kotodama` / LangGraph / Pregel / LangChain 実装を追加
2. `vertex_actor_registry` + `vertex_mcp_tool_def` 行を確認
3. 退役前チェック: `vertex_page`, `vertex_screenshot`, `vertex_gov_source` 等のドメイン必須行が存在
4. Cloudflare route を SvelteKit edge proxy → AgentGateway MCP に向ける
5. 旧 CF Worker delete (`wrangler delete` or CF API)
6. `deps.toml [[mitama_actors]]` の `execution_tier` は使わず、`runtime = "k8s-langserver"` へ更新

### 新規 actor の作成フロー

```
新規 actor 必要
    ↓
Lexicon + vertex_actor_registry + vertex_mcp_tool_def を追加
    ↓
AgentGateway MCP tool/method を登録
    ↓
pod-side LangServer method を実装
    ↓
必要なら LangGraph graph / Pregel graph / LangChain runnable / kotodama module を追加
    ↓
K8s image rebuild + helm rollout
    ↓
Cloudflare は既存 SvelteKit edge proxy の route 設定だけで公開
```

---

# Consequences

## Positive

- CF Worker 数が app 数に比例しない (300→500+ app でも Worker は bounded)
- Business logic は pod-side LangServer / LangGraph / Pregel / LangChain で可視化 + retry + incident 管理
- Kotoba/Datomic UDF により edge/Python を経由しない行単位 classify が可能
- Python worker は `kotodama` として pip install 可能なモジュール群に収束
- SvelteKit UI は main edge proxy だけで全 app に serve 可能
- AgentGateway MCP が external protocol と pod execution の唯一の membrane になる

## Trade-offs

- Registry/MCP/LangServer method の規律が必要 (Worker scaffold コピペより初期学習コストが高い)
- AgentGateway hop が mutating operation に +1 latency を足す
- AgentGateway MCP は critical infra として SLO / idempotency / audit が必須
- CF binding が必要な protocol glue と business logic の分離をレビューで強制する必要がある

---

# References

- `90-docs/adr/2604262000-edge-thin-app-runtime-k8s-zeebe-registry.md` (superseded)
- `90-docs/adr/0056-bpmn-as-actor.md` — historical BPMN actor source; new execution path uses LangGraph/Pregel/LangChain
- `90-docs/adr/0044-kotoba-udf-language-strategy.md` — UDF language selection
- `90-docs/adr/2604261000-mcp-registry-via-kysely-schema.md` — vertex_mcp_tool_def SSoT
- `90-docs/adr/2604251801-cron-three-layer-consolidation.md` — cron consolidation, now K8s CronJob → LangServer run
- `90-docs/adr/2604251830-shannon-optimal-layered-architecture.md` — L1–L8 layer taxonomy
- `90-docs/adr/2605080600-langgraph-server-granian-l3-runtime.md` — LangGraph Server + Granian runtime
- `90-docs/adr/2605111200-cf-worker-edge-only-no-rw-connection.md` — CF Worker DB I/O prohibition
- `90-docs/adr/2605101200-ai-cxo-roles-lsp-resident.md` — resident LangServer shape
- `90-docs/260408-actor-executor-p5p3-architecture-design.md`
- `90-docs/260425-ingest-orchestration-zeebe-python-k8s-mcp-design.md`

---

# Appendix: Historical CF Worker Inventory (2026-04-28)

This snapshot is retained only as the migration baseline. The `Tier` column is
obsolete for runtime placement after the 2026-05-13 amendment.

| Tier | Count | Criteria | Action |
|---|---|---|---|
| Historical T3 — infra | 27 | Platform Workers (PDS, routing-gateway, actor-resolver, auth, plc, murakumo, appview, signal, relay, …) | Re-review as protocol edge adapters; move any business logic to pod |
| Historical T3 — app complex | 51 | `src/app.ts` > 800 lines OR has D1/KV binding (maps, webpage, media-gamers, public-malak, states, …) | Prune to SvelteKit edge proxy + AgentGateway |
| Historical T2 candidates | 190 | 200–800 lines + HYPERDRIVE; business logic relocatable to kotodama + BPMN | Migrate to pod-side LangServer |
| Historical T1 candidates | 53 | < 200 lines or no `src/app.ts`; thin stubs or simple data adapters | Collapse to registry + AgentGateway MCP |
| **Total** | **321** | | |

Migration path: extract domain logic to `kotodama` / LangGraph / Pregel / LangChain
module → expose LangServer method → register `vertex_mcp_tool_def` →
route through AgentGateway MCP → delete per-actor CF Worker.

Cloudflare boundary conditions (may retain edge adapter, never business logic):
- AT Protocol federation XRPC (PDS-level)
- DPoP / OAuth / CORS / session JWT boundary
- WebSocket / streaming pass-through (relay, chat)
- CF-specific bindings: Turnstile, KV/R2 cache, Durable Objects coordination
- SvelteKit UI asset/SSR shell

---

## Addendum 2026-04-30: generic.pds.dispatch K8s-internal routing

Historical note: `generic.pds.dispatch` は従来 `https://atproto.etzhayyim.com`
(CF edge) を経由して PDS XRPC を呼んでいた。Zeebe/UDF/LangGraph の処理パスが
CF edge を踏むことは ADR 原則 (Business logic は K8s Pod に) に反するため、
当時の zeebe-worker 内で 3-way ルーティングに置き換えた
(commit `39bd3166dbc`, 2026-04-30)。

2026-05-13 以後、この routing responsibility は AgentGateway MCP に吸収する。
以下は migration source として保持する。

### 3-way routing 表

| NSID prefix | ルーティング先 | 実装関数 | 備考 |
|---|---|---|---|
| `app.bsky.*` / `chat.bsky.*` / `com.atproto.repo.*` | C-path: `vertex_repo_record` 直接 INSERT | `_pds_dispatch_c_path` | graph-visible, AT federation なし |
| `com.etzhayyim.*` | bpmn-dispatcher ClusterIP (`x-internal-trust` 認証) | `_pds_dispatch_internal_xrpc` | K8s クラスタ内完結 |
| その他 | legacy PDS HTTP (`https://atproto.etzhayyim.com`) | `_pds_dispatch_legacy` | 後方互換フォールバック |

### C-path 詳細 (social/AT writes)

- `app.bsky.feed.post` → `payload.get("repo") or callerDid` を repo として `build_repo_record()` → `insert_social_post_record(row, flush=False)` (RW_ALLOW_FLUSH=0 対応)
- `com.atproto.repo.*` → `payload.get("record")` または `json.loads(payload["recordJson"])` を record として同上
- 戻り値: `{status: 200, cid, uri, latencyMs}`

### bpmn-dispatcher ClusterIP 認証

- URL: `http://bpmn-dispatcher.mitama-udf.svc.cluster.local:8080`
- ヘッダー: `x-internal-trust: {BPMN_DISPATCHER_INTERNAL_SECRET}`
- 検証: `hmac.compare_digest(provided, INTERNAL_SECRET)` (plain shared-secret — signing なし)
- timeout: 60s

### 環境変数

| 変数 | デフォルト | 設定場所 |
|---|---|---|
| `BPMN_DISPATCHER_INTERNAL_URL` | `http://bpmn-dispatcher.mitama-udf.svc.cluster.local:8080` | `values.yaml zeebeWorker.bpmnDispatcher.internalUrl` |
| `BPMN_DISPATCHER_INTERNAL_SECRET` | — (optional) | K8s Secret `bpmn-dispatcher-auth` key `internal-secret` |

Helm template は `50-infra/vultr/mitama-udf-pool/templates/zeebe-worker.yaml` の `BPMN_DISPATCHER_INTERNAL_URL` / `BPMN_DISPATCHER_INTERNAL_SECRET` env ブロックに追加済み。

### 実装ファイル

- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/zeebe_worker_main.py` — `_pds_dispatch_c_path`, `_pds_dispatch_internal_xrpc`, `_pds_dispatch_legacy`, `task_generic_pds_dispatch`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/yoro_social.py` — `build_repo_record`, `insert_social_post_record` (C-path pattern source)
- `50-infra/vultr/mitama-udf-pool/values.yaml` — `zeebeWorker.bpmnDispatcher.*` section 追加
- `50-infra/vultr/mitama-udf-pool/templates/zeebe-worker.yaml` — env block 追加

### 制約

- C-path write は AT Protocol firehose に乗らない (federable ではない)。AT federation が必要な用途は legacy path を使うこと。
- `insert_social_post_record` は RW_ALLOW_FLUSH=0 のため `flush=False` で呼ぶ。
- `recordJson` (JSON 文字列) と `record` (dict) の両形式を受け付ける (briefing 等の既存 BPMN との互換)。

---

## Addendum 2026-04-30: maps.etzhayyim.com business command cutover

Historical note: `maps.etzhayyim.com` の CF Worker (`maps-ui-uqpel6i6`) は、
ADR-2604282300 の thin-edge 原則に合わせて business command surface を
BPMN / Zeebe / Python worker へ移した。2026-05-13 以後の target は
SvelteKit edge proxy → AgentGateway MCP → pod-side LangServer であり、
以下は migration source として保持する。

### Cutover result

| Metric | Count | Meaning |
|---|---:|---|
| BPMN-covered maps commands | 162 | `vertex_bpmn_lexicon_binding` + BPMN XML + pyzeebe task registration |
| CF Worker registered maps commands | 35 | Edge-only exceptions retained in `src/app.ts` |
| BPMN-covered commands still registered in CF Worker | 0 | No duplicate business surface remains |
| Remaining unmigrated business commands | 0 | Business logic cutover complete |

### New BPMN areas

The final migration batch added 86 maps BPMNs:

- `maps-transport-extra`: aircraft, flight operations/offers, waterways, ports,
  airports, stations, bus stops, parking, EV chargers.
- `maps-twin-sensor-sim`: building/twin asset lifecycle, sensors, alerts,
  simulation, forecast, health, maintenance.
- `maps-spatiotemporal`: spatial events, versions, relations, timeline, diff,
  display layers, dashboard, actor locations.
- `maps-registry-media`: post locations, Mapraly import/list, vision import/list,
  satellite import/list/source, web-crawl geo lists, legal/operator/property
  registries, ownership chain, entity history.

### Edge exceptions retained

The following classes remain in the CF Worker because they are request/runtime
adapters, rendering hot paths, or operational triggers rather than canonical
business logic:

- Runtime config and KAMI config.
- Tile/chunk/model reads (`tileGeoJson`, `tileXyz`, `getChunk`,
  `getChunkModels`) for map rendering latency and cache locality.
- Thin external/read-through adapters (`reverseGeocode`, `weatherAt`,
  `weatherGrid`, `ipGeolocate`).
- Realtime or browser-near commands (`nextDeparturesAtStop`,
  `realtimeDelaysAtStop`, `twinScene`, `extractPostLocation`).
- Trigger/proxy commands where the durable state mutation is elsewhere
  (`crawlFlightPrices`, `mapralyIngest`, `analyzeImage`, `satelliteIngest`,
  `satelliteAnalyze`).
- Bootstrap/ops hooks (`seed*`, `pollGeoRecords`, `seedGlobalRegistries`,
  `backfillSocial`).

These exceptions do not restore Worker-owned business state. List/register/
upsert/query/record/history/dashboard logic for maps must now run through
AgentGateway MCP and pod-side LangServer methods. Existing BPMN processes and
`kotodama.ingest.maps_collection` pyzeebe tasks are migration inputs.

### Verification

- `PYTHONPATH=40-engine/kotoba/crates/kotoba-kotodama/py/src python3 -m py_compile ...`
- `xmllint --noout` on all new maps BPMNs.
- `pnpm lint:bpmn:structural` -> 430 covered BPMN files validated.
- `pnpm lint:bpmn:worker-tasks` -> 430/430 covered BPMN files have worker task coverage.
- `pnpm lint:bpmn:lexicon-contract` -> 430 bindings validated.
- `wrangler deploy --dry-run` for `maps-ui-uqpel6i6` succeeds. Remaining
  warnings are pre-existing wasm rule fallback and duplicate keys in
  `src/collection-commands.ts`.

### Implementation references

- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/maps/{transport-extra,twin-sensor-sim,spatiotemporal,registry-media}/`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/ingest/maps_collection.py`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/zeebe_worker_main.py`
- `30-graph/graph-schema/migrations/20260430216400_seed_maps_collection_bpmn_actors.ts`
- `60-apps/etzhayyim-project-maps/appview/maps-ui-uqpel6i6/src/app.ts`
- `70-tools/config/bpmn-coverage-manifest.json`
