---
id: adr-2604251830-shannon-optimal-layered-architecture
title: "ADR: Shannon-optimal layered architecture — Cloudflare = edge/routing/dispatcher only、actor/MCP/tool 実体は RisingWave registry SSoT、常駐処理は Zeebe BPMN worker + Vultr k8s Python pod worker"
status: active
doc_type: adr
topic: platform-architecture
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - cloudflare-worker-role
  - actor-mcp-tool-ssot
  - residential-compute-placement
  - cron-implementation-layer
related:
  - adr-0036-shannon-cleanup-did-actor-topology
  - adr-0044-risingwave-udf-language-strategy
  - adr-0046
  - adr-0048-risingwave-vultr-b2-primary
  - adr-0056-bpmn-as-actor
  - adr-2604240946-yoro-autonomous-actor-hybrid-loop
  - adr-2604250836-langgraph-as-zeebe-servicetask
  - adr-2604261100-rego-dmn-policy-decision-layers
  - adr-2604261110-wproto-wreactive-wit-retirement
  - adr-2604251801-cron-three-layer-consolidation
supersedes: []
superseded_by: []
amends:
  - adr-0036-shannon-cleanup-did-actor-topology
---

# Context

ADR-2604261110 (wproto/wreactive/WIT retire) と ADR-2604251801 (cron 3
レイヤー集約) で旧 architecture の subtractive 整理が完了した結果、現在
動いている実体だけが残った:

- **Cloudflare**: PDS gateway (atproto.etzhayyim.com), AppView (bsky.etzhayyim.com),
  routing-gateway, 189 actor Worker
- **Backblaze B2**: object storage, RW Hummock backing store (ADR-0048)
- **RisingWave (Vultr)**: streaming SQL + materialized views, Hummock
  on B2 (ADR-0048)
- **RW External Python UDF**: in-stream compute (ADR-0044)
- **Zeebe (Vultr k8s)**: BPMN orchestration, pyzeebe job workers
  (ADR-0056, ADR-2604240946)
- **Vultr k8s Python pods**: tool execution, heavy compute, headless
  browser (Playwright), pandas, ML inference
- **MCP servers**: tool registry currently scattered between CF Worker
  `_app/meta` JSON, `actor-manifest.jsonld` files, BPMN binding rows in
  RW, and 70-tools/scripts catalogs

旧 framing (`Design A〜E reactive pipeline`, `wRPC stream-native`,
`MagatamaApp single-file = actor 実体`, `TS Native + Lexicon Contract`)
は wproto retire と BPMN-as-actor の浸透で**前提が崩れている**。
Shannon η の観点で各 layer の責務が overlap し、「actor が CF Worker と
BPMN process と RW vertex_repo_record の 3 箇所に二重定義される」drift
が発生している。

本 ADR は**新規追加禁止 / forward-only** で各 layer の責務を再宣言し、
既存 actor は当面そのまま動かす (forward-only migration; 一括書き換えは
別 migration として段階実施)。

# Decision

## Layer table (literal)

| Layer | 場所 | 役割 | **してはいけないこと** |
|---|---|---|---|
| **L1 Edge** | Cloudflare (Pages / DNS / Workers AI / Vectorize) | TLS termination, HTTP/3, CDN, geographic routing, edge inference (任意) | actor / MCP / tool 実体定義 |
| **L2 Routing** | Cloudflare Worker (`atproto.etzhayyim.com` PDS gateway, `bsky.etzhayyim.com` AppView) | AT Protocol XRPC entry, OAuth + DPoP verify, Service Auth ES256 JWT verify, NSID → backend lookup (RW registry), pipethrough | business logic, actor state, long-running job |
| **L3 Dispatcher** | Cloudflare Worker (per-app `{nanoid}.etzhayyim.com`) | XRPC → backend translator: PDS write / Hyperdrive direct write (ADR-0036) / Zeebe message-start / k8s pod RPC / MCP invoke | actor の "実体" を保持しない (実体は RW registry が SSoT)。30s/128MB を超える work |
| **L4 Registry SSoT** | RisingWave PostgreSQL (Vultr) via Hyperdrive | `actor_registry` / `mcp_registry` / `tool_registry` / `process_def` / `vertex_bpmn_lexicon_binding` テーブル。actor の DID, capability tags, runtime tier, backend URL, MCP tool list, BPMN binding を持つ唯一の SSoT | 個別 worker の `_app/meta` JSON や repo 内 `actor-manifest.jsonld` を SSoT として扱う (それらは registry の generator/cache に降格) |
| **L5 Storage** | B2 (objects, blobs) + RisingWave Hummock (streaming SQL state) | content-addressed blob (`blobs/{repo}/{sha256hex}`)、MV state、RW snapshot | 別 object store (R2 active write は廃止、ADR-0048) |
| **L6 In-Stream Compute** | RisingWave External Python UDF + Embedded Rust WASM + SQL UDF | per-row enrichment / classifier / hash / ML feature。UDF strategy = ADR-0044 | 高並列 burst web fetch (CF Worker `Promise.all(50..100)` 維持)、長時間 job |
| **L7 Orchestration** | Zeebe (Vultr k8s) + pyzeebe job workers | BPMN-as-actor (1 process = 1 NSID)、R/PT timer、multi-step business workflow、long-running orchestration、cron 第 1 レイヤー (ADR-2604251801) | XRPC entry にしない (entry は L2 PDS gateway)。primitive 実装の重複 (primitive は pyzeebe job worker に集約) |
| **L8 Tool Execution** | Vultr k8s Python pods (CronJob + Deployment) | heavy compute (pandas / RDKit / ML inference)、headless browser (Playwright)、長時間 batch ingest、cron 第 2 レイヤー (ADR-2604251801) | BPMN orchestration を pod 内で再実装する (それは L7 の責務) |

## Cloudflare Worker = 3 sublayer (CRITICAL)

CF Worker は **edge / routing / dispatcher** の 3 sublayer のみ。
**actor 実体ではない**。

```
┌────────────────────────────────────────────────────┐
│ L1 Edge (CF Pages / Workers AI / DNS)              │
│   TLS, CDN, geographic routing                     │
└─────────────────────┬──────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────┐
│ L2 Routing (atproto.etzhayyim.com, bsky.etzhayyim.com)         │
│   XRPC entry, OAuth/DPoP, NSID lookup              │
│   - reads L4 actor_registry to find backend        │
│   - pipethrough to dispatcher / direct to L4 / L7  │
└─────────────────────┬──────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────┐
│ L3 Dispatcher (per-app {nanoid}.etzhayyim.com Worker)    │
│   XRPC → translate → L4 PG INSERT (ADR-0036)       │
│                    → L7 Zeebe message-start        │
│                    → L8 k8s pod RPC                │
│                    → L4 mcp_registry lookup → MCP  │
└────────────────────────────────────────────────────┘
```

**ルール**:

- L3 Dispatcher Worker は state を持たない (KV / Hyperdrive cache のみ)
- actor の capability / tool / MCP endpoint 一覧は **L4 registry table を読む** (`_app/meta` JSON は registry の cache view、authoritative ではない)
- 30s / 128MB を超える work は **L7 / L8 にデリゲート**
- 既存の "MagatamaApp single-file" actor (`60-apps/.../wasm/.../src/app.ts`) は **L3 Dispatcher の subset として扱う** (forward-only; 既存挙動維持、新規 actor は L7/L8 を優先)

## Registry SSoT (L4) スキーマ

`30-graph/graph-schema/migrations/` 配下に follow-up migration として
作成 (本 ADR は宣言のみ、schema は別 PR):

| テーブル | カラム概要 | 役割 |
|---|---|---|
| `actor_registry` | `did`, `handle`, `tier` (T0..T4), `backend_kind` (cf-dispatcher / k8s-pod / bpmn-process / external), `backend_url`, `capability_tags[]`, `mcp_endpoint`, `created_at`, `deactivated_at` | actor の唯一の SSoT。CF dispatcher は NSID 解決時にこの table を読む |
| `mcp_registry` | `mcp_id`, `endpoint`, `auth_method` (`session-jwt` / `service-auth-es256` / `none`), `tool_nsids[]`, `actor_did` (FK → actor_registry), `last_health_check_at` | MCP server 一覧。`tools/list` の 3 層 fallback を消し、registry を sole source of truth に |
| `tool_registry` | `tool_nsid`, `execution_backend` (`rw-udf` / `cf-dispatcher` / `k8s-pod` / `bpmn-process`), `backend_ref`, `governance_class` (A/B/C), `approval_required`, `created_at` | tool の execution backend を lookup する。L3 dispatcher の routing decision に使用 |
| `process_def` (既存) | `nsid`, `process_id`, `bpmn_xml_cid`, `deployed_at` | BPMN-as-actor 実体 (ADR-0056) — 既存 |
| `vertex_bpmn_lexicon_binding` (既存) | `nsid`, `process_id`, `write_table_allowlist[]` | BPMN actor の write scope gate — 既存 |

## L7 Zeebe BPMN orchestration

- **常駐**: Zeebe broker (Vultr k8s `mitama-udf-pool` namespace)
- **常駐 job worker**: `pymagatama` dispatcher (F5 watcher) + per-primitive
  pyzeebe worker (`generic.db.*`, `generic.pds.*`, `agent.chat`, `llm.*`,
  `udf.*`)
- **cron 第 1 レイヤー**: BPMN timer-start (`R/PT*` or cron 表記)
- **trigger**: L3 dispatcher が `zeebe message-start` を発行、または
  L1/L2 の subscribeRepos commit が L7 message broker に流れる
- **out-of-band migration**: ADR-2604241342 の `apply-pending.sh`
  pattern を維持 (RisingWave migration は kysely 自動 latest 不可)

## L8 Vultr k8s Python pod tool execution

- **CronJob**: cron 第 2 レイヤー (ADR-2604251801) — backup / batch
  ingest / OSM planet / coverage tally
- **Deployment**: tool execution pod — Playwright browser pool /
  pandas-heavy ETL / ML inference / headless rendering
- **trigger**: BPMN ServiceTask → k8s Job (one-shot) / Deployment HTTP
  RPC、または L3 dispatcher → pod RPC
- **secret**: macOS Keychain → ansible 配布 (ADR-2604251205) または
  k8s Secret (Vault sync)

## Cross-cutting

- **AT Protocol semantics**: AT URI ↔ HTTP `/at/` 1:1, NSID 完全修飾, DID-based identity (ADR-0019)
- **Auth**: OAuth + DPoP (atproto), Service Auth ES256 JWT (worker→worker), Vault zero-knowledge (ADR-2604251200)
- **Policy**: Rego (XRPC AuthZ) + DMN (BPMN gateway / classifier) — ADR-2604261100
- **Monitoring**: triple-witness (PDS commit / RW MV / Zeebe Operate) — ADR-0046
- **Storage**: B2 primary, R2 active write 廃止 (ADR-0048)
- **Identity**: did:web (apps), did:plc (users via plc-private), did:etzhayyim (legacy nanoid grandfather table)
- **3-Tier Write** (ADR-0036, restated):
  - Tier 1 Social = L2 PDS dispatch (`app.bsky.*` / `com.atproto.*`)
  - Tier 2 Domain = L3 dispatcher → L4 Hyperdrive direct write (`com.etzhayyim.apps.*`)
  - Tier 3 State = `Preferences()` server-side state

## Scope (forward-only)

- **新規** actor / MCP / tool: L4 registry に登録、execution backend を
  L3 / L7 / L8 から選択
- **既存 189 CF Worker actor**: 当面そのまま (forward-only)。各 actor の
  挙動が L3 dispatcher として整合する限り migration 不要。新機能追加時
  に L4 registry へ登録 (`backend_kind = "cf-dispatcher"`)
- **既存 BPMN-as-actor (105 NSID, defence cluster + others)**: そのまま
  L7 として動作。`process_def` + `vertex_bpmn_lexicon_binding` は L4
  registry の subset として既存ルールに従う
- **既存 ansible/goose crontab (3 recipe)**: ADR-2604251801 で
  `goose-crontab-retirement-2026-04-25` migration として消化

## Deprecated (本 ADR 採択時点で発効)

| 旧 framing | 状態 | 後継 |
|---|---|---|
| `Design A` (event stream polling + batch) | **禁止** | L7 BPMN timer + L8 k8s CronJob |
| `Design B` (event stream + observe SSE) | **非推奨** | L7 BPMN + L4 MV |
| `Design C` (AT Lexicon EventStream) | 限定許可 | social のみ (`app.bsky.*`) |
| `Design D` (AppBskyFeedPost-only) | 廃止 | 3-Tier Write (ADR-0036) |
| `Design E` (wRPC stream reactive + 3-Tier Write) | **半廃止** | 3-Tier Write 部分のみ存続 (ADR-0036)。"wRPC stream reactive pipeline" 部分は wproto archive で死語化 (ADR-2604261110) |
| `wRPC` / `wproto stream` / `WprotoConvoSendMessage` | 死語 | (transport 不要、L2 XRPC 単独) |
| `handleComAtprotoSyncSubscribeReposCommit` を全 actor の reactive entry とする原則 | 限定 | social commit (`app.bsky.*`) のみ。domain は L3 dispatcher direct |
| `MagatamaApp single-file = actor 実体` framing | **scope 縮小** | L3 dispatcher の subset。新規 actor 実体は L4 registry 登録 + L7/L8 backend |
| `TS Native + Lexicon Contract = SSoT` framing | **scope 縮小** | L3 dispatcher の build pattern。actor SSoT は L4 |

## Amends

- **ADR-0036 (Worker-direct Hyperdrive Persistence)**: CF Worker
  Hyperdrive direct write は **L3 Dispatcher の責務として継続**
  (handler は薄い translator)。actor の "実体" は L4 registry が SSoT。
  189 既存 worker は forward-only 維持。

# Rationale

## Shannon η 集計

各 layer は単一責務、隣接 layer 以外への直接書き込みなし:

| 計測軸 | Before (drift) | After (本 ADR) |
|---|---|---|
| actor SSoT 候補数 | 4 (`_app/meta` / `actor-manifest.jsonld` / `process_def` / 個別 CF Worker) | **1** (L4 `actor_registry`) |
| MCP tool discovery 経路 | 3 層 fallback (graph / ActorCard / `_app/meta`) | **1** (L4 `mcp_registry`) |
| cron 実装層 | 6 (CF cron / k8s CronJob / Zeebe / GH Actions / launchd / goose) | **3** (k8s CronJob / Zeebe BPMN / Python pod、ADR-2604251801) |
| 残存 transport | 2 (AT XRPC + wproto wRPC stream) | **1** (AT XRPC) |
| Worker dispatcher と actor 実体の重複 | あり (CF Worker = 両方) | **なし** (CF L3 = dispatcher のみ、実体は L4) |

## Forward-only の根拠

189 既存 CF Worker actor を一括 migrate するコストは新 architecture
の利益を上回る。L3 Dispatcher として整合する限り共存可能、新機能を
L4 registry + L7/L8 backend で書き、徐々に L3 へ縮退させる。

# Migration plan (follow-up)

本 ADR 採択後、別 PR で実施:

1. **L4 schema migration**: `actor_registry` / `mcp_registry` / `tool_registry` の `30-graph/graph-schema/migrations/` 追加
2. **registry generator**: 既存の `_app/meta` / `actor-manifest.jsonld` / `process_def` を読んで L4 へ INSERT する one-shot bootstrap script
3. **L2 routing-gateway 改修**: NSID 解決時に L4 registry を読むよう変更 (現行は static map)
4. **L3 dispatcher SDK**: `@etzhayyim/magatama-host-sdk` に `tool_registry` lookup helper を追加
5. **doc rewrite**: `60-apps/CLAUDE.md` §239-324 を本 ADR への pointer に縮約
6. **convention pruning**: `deps.toml [[conventions]]` の `Design E 3-Tier Write` を `3-Tier Write (ADR-0036)` にリネーム、`Inter-App Communication (W Protocol over wRPC)` 系を削除

各ステップは `deps.toml [[migrations]]` に分割登録。

# Consequences

- 新 architecture は 8 層が明確に分離、Shannon η が回復
- L4 registry SSoT 化により "tools/list" / capability discovery / MCP routing が単一クエリに収束
- CF Worker 30s/128MB 制約に縛られない work が L7/L8 に集約、scaling が k8s 側で完結
- 既存 189 CF Worker は壊れない (forward-only)、ただし新機能ガイダンスは L7/L8 優先
- doc rewrite (60-apps/CLAUDE.md, root CLAUDE.md, deps.toml conventions) が follow-up に必要

# Alternatives Considered

- **CF Worker actor 実体維持 (現状追認)**: drift 続行、L4 registry 不在のまま `_app/meta` 3 層 fallback が残る。却下
- **L3 Dispatcher を別 layer (Hono server on k8s) に移す**: edge latency 増、CF の global PoP を活かせない。却下
- **Zeebe を CF Container で動かす**: broker は state が大きく container 不向き、Vultr k8s broker 維持
- **MCP registry を CF KV に置く**: TTL drift, regional consistency 弱、RW PG が他の registry と同居するため統一

# References

- ADR-0036 Worker-direct Hyperdrive Persistence (amended by this ADR — scope narrowed to L3)
- ADR-0044 RisingWave UDF Language Strategy (L6)
- ADR-0046 Triple-Witness Monitoring
- ADR-0048 RisingWave + Vultr + B2 primary (L5)
- ADR-0056 BPMN-as-actor (L7)
- ADR-2604240946 yoro autonomous BPMN R/PT4H cadence (L7 reference)
- ADR-2604250836 LangGraph as Zeebe ServiceTask (L7 inference primitive)
- ADR-2604261100 Rego + DMN policy decision layers (cross-cutting policy)
- ADR-2604261110 wproto / wreactive / WIT retirement (subtractive predecessor)
- ADR-2604251801 cron three-layer consolidation (cross-cutting cron rule)
