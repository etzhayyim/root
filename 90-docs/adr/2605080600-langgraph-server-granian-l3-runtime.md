---
id: adr-2605080600-langgraph-server-granian-l3-runtime
title: "ADR-2605080600: LangGraph Server + Granian as L3 Virtual Actor Runtime"
status: active
doc_type: adr
topic: langgraph-server-granian-l3-runtime
authoritative: true
last_verified: 2026-05-08
priority: 9.0
axis: architecture
weight: 0.90
priority_note: "CRITICAL — L3 Virtual Actor Runtime を Zeebe/pyzeebe から LangGraph Server + Granian に置換する"
authoritative_for:
  - L3 Virtual Actor Runtime definition (amends ADR-2605080000)
  - primary L3 runtime selection: LangGraph Server first, Spiff BPMN worker for BPMN-native flows
  - LangGraph Server as activation-oriented async worker runtime
  - resident artificial-organism actor placement
  - Murakumo Mac mini fleet as L8 Somatic Inference Layer
  - Granian as ASGI server for LangGraph Server
  - Redis role: transient dispatch queue only (not a database)
  - Kotoba/Datomic custom BaseCheckpointSaver + BaseStore (sole DB principle)
  - bpmn-dispatcher routing target: /runs API
  - timer-start BPMN replacement: K8s CronJob → POST /runs
  - pyzeebe migration path to LangGraph nodes
  - LangGraph scope expansion: L2 coordination + L3 execution runtime (combined)
  - SpiffWorkflow BPMN worker coexistence boundary
depends_on:
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605072000-langgraph-agent-loop-pattern
  - adr-2605061200-agi-active-inference-artificial-organism-architecture
  - adr-2604251821-vke-murakumo-multicluster-control
  - adr-2604282300
  - adr-0056-bpmn-as-actor
  - adr-2605081200-spiffworkflow-bpmn-engine-replacement
supersedes: []
superseded_by: []
amends:
  - adr-2605080000-distributed-cognitive-actor-system  # L3 layer definition
  - adr-2605072000-langgraph-agent-loop-pattern        # scope: intra-job → L2+L3
---

# ADR-2605080600: LangGraph Server + Granian as L3 Virtual Actor Runtime

**Status**: accepted
**Date**: 2026-05-07
**Deciders**: Jun Kawasaki
**Amends**: ADR-2605080000 (L3 layer), ADR-2605072000 (LangGraph scope)

## Context

ADR-2605080000 は L3 = Zeebe StatefulSet + pyzeebe と定めた。実運用で以下の問題が顕在化した:

- pyzeebe の gRPC チャネル管理が複雑 — watchdog/activation_monitor が別途必要
- Zeebe は Java StatefulSet (~1-2GB RAM)。ランタイム全体のコストが高い
- pyzeebe ↔ LangGraph の二層構造: Zeebe job handler (pyzeebe) の内部で LangGraph を呼ぶ冗長さ
- arm64/amd64 イメージミスマッチ → exec format error が繰り返し発生
- pyzeebe `Maximum number of jobs running` RESOURCE_EXHAUSTED backpressure で actor が starve

並行して、LangGraph 1.x が成熟した:

- **LangGraph Server** (`langgraph-api`) は FastAPI/Starlette ASGI アプリであり、
  Granian (Rust ASGI server) で直接 serve できる
- **`/runs` API** が Zeebe job dispatch の代替として機能する (background execution)
- **`/threads` API** が BPMN process instance の代替 (stateful actor thread)
- **`interrupt()`** が BPMN message-event correlation の代替 (HITL pause/resume)
- **`BaseCheckpointSaver`** / **`BaseStore`** がカスタム実装可能 → Kotoba/Datomic 直接

提案された新アーキテクチャ (`CF Worker → bpmn-dispatcher → FastAPI+Granian+LangGraph → Kotoba/Datomic`)
は既存 ADR と約 75% 適合する。bpmn-dispatcher は既に K8s-internal routing hub として存在する
(ADR-2604282300)。FastAPI+Granian の採用でこれを Zeebe ではなく LangGraph Server への
routing hub として再利用できる。

## Decision

### L3 再定義 (ADR-2605080000 amendment)

```
旧 L3: Zeebe StatefulSet (broker) + pyzeebe (job handler)
新 L3: bpmn-dispatcher (routing) + LangGraph Server / Granian (execution runtime)
```

LangGraph Server は L2 Coordination + L3 Execution Runtime の **main path**
として担う。BPMN 2.0 XML が business process の正本である方が自然な処理は、
ADR-2605081200 の SpiffWorkflow engine host + BPMN worker を併用する。
つまり Zeebe/pyzeebe は退役対象だが、BPMN そのものは LangGraph に無理に
畳み込まない。

### システム図

```
CF Worker (L1)
    │ XRPC POST  com.etzhayyim.apps.{actor}.{method}
    ▼
bpmn-dispatcher  (L3 routing, 既存 ADR-2604282300)
http://bpmn-dispatcher.mitama-udf.svc.cluster.local:8080
    ├─ default: POST /runs  or  POST /threads/{tid}/runs
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  LangGraph Server  (Granian ASGI, K8s Deployment)   │ ← L2+L3
│                                                     │
│  /runs            → background execution            │
│  /runs/stream     → SSE streaming → CF Worker       │
│  /threads         → stateful actor (thread = actor) │
│  interrupt()      → HITL pause / external resume    │
│  /assistants      → graph registry (actor catalog)  │
│                                                     │
│  StateGraph (Pregel)           ← L2 coordination    │
│    ├── node: rw_read    ────────────→ Kotoba/Datomic L5  │
│    ├── node: tool_call  ────────────→ MCP L4         │
│    ├── node: rw_write   ────────────→ Kotoba/Datomic L5  │
│    └── node: interrupt  → 人間承認待ち              │
└─────────────────────────────────────────────────────┘
         │ BLPOP dispatch              │ durable state
         ▼                             ▼
       Redis                       Kotoba/Datomic
  transient queue only         vertex_langgraph_checkpoint
  (~50MB, ephemeral)           vertex_langgraph_store
  障害時は /runs ステータスで    vertex_langgraph_run
  replay可                     (custom BaseCheckpointSaver)

    └─ BPMN-native: POST /v1/instance
       ┌─────────────────────────────────────────────┐
       │ SpiffWorkflow engine host + BPMN workers    │
       │ vertex_spiff_instance/job/timer/history     │
       └─────────────────────────────────────────────┘
```

### Runtime selection rule

LangGraph Server is the default runtime for new L2/L3 actors. Use SpiffWorkflow
BPMN workers when the process definition itself is an operational artifact:

| Use case | Runtime |
|---|---|
| Agent loop, tool planning, HITL interrupt, streaming response | LangGraph Server |
| Short async task with simple branching | LangGraph Server |
| BPMN XML already exists and is reviewed as the process contract | SpiffWorkflow BPMN worker |
| BPMN timers / boundary events / audit-friendly process diagram are required | SpiffWorkflow BPMN worker |
| Human/business operators need BPMN diagram review more than graph-node review | SpiffWorkflow BPMN worker |

Both runtimes use Kotoba/Datomic as the durable state layer and must preserve
at-least-once, idempotent execution. The dispatcher chooses the target from
`vertex_bpmn_lexicon_binding` / actor registry metadata; callers keep the same
XRPC/MCP surface.

### Redis の位置づけ (CRITICAL)

Redis は **transient dispatch queue のみ**。DB ではない。

```
役割: LangGraph Server 内部の job dispatch (BLPOP atomic handoff)
永続化: 不要 — checkpoint は全て Kotoba/Datomic に書く
障害: Redis 再起動 → 未処理 job は /runs status=pending のまま
      bpmn-dispatcher が再 POST → at-least-once で replay
サイズ: ~50MB (K8s ConfigMap ベースの ephemeral Redis でよい)
禁止: Redis を "第2の DB" として使わない。KV store / pub-sub / cache としての使用禁止
```

**Kotoba/Datomic sole DB 原則は維持される** — Redis は transport layer であり storage ではない。

### Artificial organism layer binding

LangGraph Server resident actors are the organism's **Autonomic Active-Inference
Layer**. They own the persistent perception-action loop, thread identity,
checkpoint boundary, and policy selection. The Murakumo Mac mini fleet is not
the actor subject; it is the organism's **L8 Somatic Inference Layer**: a
replaceable local inference organ used by resident actors.

| Component | Organism role | Repo layer | Contract |
|---|---|---|---|
| LangGraph resident actor | Autonomic active-inference loop | L3 Virtual Actor Runtime | `/runs`, `/threads`, checkpoints, action selection |
| Kotoba/Datomic | Belief and memory substrate | L4 state store | `q_i(s,t)`, checkpoint, store, run records |
| Murakumo Mac mini fleet | Somatic inference organ | L8 physical inference substrate | OpenAI-compatible local inference endpoint |
| Zeebe / CronJob | Rhythmic nervous system | L7 process/timer | start/resume/sweep events only |
| AT Protocol / XRPC | Social signaling | L2 protocol | external observation and emission |
| Lexicon / WIT / Rego / BPMN | Normative genome | L0/L1 contract | accepted state and action boundaries |

The ownership rule is strict:

```text
subject identity = DID + LangGraph thread + Kotoba/Datomic checkpoint
inference organ  = Murakumo endpoint selected by deployment configuration
```

Therefore Murakumo nodes must remain stateless with respect to actor identity.
They may cache model weights and serve `/v1/chat/completions`, but they must not
hold the authoritative actor memory, checkpoint, DID, governance state, or
objective function.

### Resident actor inference routing

For resident artificial-organism actors, the preferred inference route is:

```text
LangGraph node
  -> etzhayyim_LLM_URL / LLAMA_BASE_URL
  -> Murakumo OpenAI-compatible endpoint
  -> Kotoba/Datomic checkpoint/store write
```

When LangGraph Server is placed on `murakumo-k3s`, the local endpoint is:

```text
http://llama-vulkan-fleet.murakumo-system.svc.cluster.local:8080/v1
```

When LangGraph Server remains on `vke-primary`, cross-cluster Service DNS is not
assumed. The endpoint must be an explicit WireGuard, Cloudflare Tunnel, or other
declared gateway URL per ADR-2604251821. Do not silently fall back to public
`llm.etzhayyim.com` for resident organism loops; a missing Murakumo route is a
degraded organism capability and should be observable.

### Kotoba/Datomic custom storage 実装

#### BaseCheckpointSaver (Kotoba/Datomic 向け)

```python
# langgraph_checkpoint_rw.py — ~500 LOC
class Kotoba/DatomicCheckpointSaver(BaseCheckpointSaver):
    """
    Kotoba/Datomic-native LangGraph checkpoint.
    vertex_langgraph_checkpoint (既存テーブル, agents/__init__.py 参照) に書く。

    Kotoba/Datomic 制約への対応:
      - FOR UPDATE SKIP LOCKED なし → 楽観ロック (UPDATE WHERE status='pending')
      - LISTEN/NOTIFY なし          → polling (SELECT WHERE thread_id=X ORDER BY checkpoint_ns DESC)
      - ON CONFLICT なし            → PK overwrite (RW implicit upsert)
      - db.transaction() なし       → DELETE + INSERT (RW は OLTP TX 非対応)
    """
    async def aput(self, config, checkpoint, metadata, new_versions): ...
    async def aput_writes(self, config, writes, task_id): ...
    async def aget_tuple(self, config): ...
    async def alist(self, config, *, filter=None, before=None, limit=None): ...
```

#### BaseStore (Kotoba/Datomic 向け)

```python
# langgraph_store_rw.py
class Kotoba/DatomicStore(BaseStore):
    """
    cross-thread long-term memory.
    vertex_langgraph_store テーブルに namespace + key → value で保存。
    Actor identity (actor_did) を namespace に含める。
    """
    async def aput(self, namespace, key, value): ...
    async def aget(self, namespace, key): ...
    async def asearch(self, namespace_prefix, *, query=None, limit=10): ...
    async def adelete(self, namespace, key): ...
```

### bpmn-dispatcher → LangGraph Server routing

bpmn-dispatcher (`dispatcher_main.py`) の routing target を変更する:

```python
# 旧: Zeebe gRPC job activate
await zeebe_client.run_process(bpmn_process_id, variables=body)

# 新: LangGraph Server /runs POST
async with httpx.AsyncClient() as c:
    resp = await c.post(
        f"http://langgraph-server.mitama-udf.svc.cluster.local:8080/runs",
        json={"assistant_id": nsid_to_graph(nsid), "input": body},
        headers={"x-internal-trust": internal_secret},
    )
```

NSID → graph name のマッピングは `vertex_bpmn_lexicon_binding` から解決する
(既存テーブル、F5 watcher と同じ registry)。

Phase 3 implementation contract:

- `vertex_bpmn_lexicon_binding.routing_target = 'langgraph'` selects the
  LangGraph route; all other rows continue to use Zeebe.
- The dispatcher promotes `actorDid` / `actor_did` and `threadId` /
  `thread_id` from XRPC variables into top-level `/runs` fields while preserving
  the original variables under `input`.
- The dispatcher forwards `x-internal-trust` to LangGraph Server when
  `DISPATCHER_INTERNAL_SECRET` is configured.
- `/bindings` exposes `routingTarget` so rollout status is visible without
  querying Kotoba/Datomic manually.

### timer-start BPMN の代替

```text
旧: <timerEventDefinition><timeCycle>R/PT4H</timeCycle></timerEventDefinition>
    → Zeebe broker が管理

新: K8s CronJob
    schedule: "0 */4 * * *"
    command: ["curl", "-XPOST",
      "http://bpmn-dispatcher.mitama-udf.svc:8080/xrpc/com.etzhayyim.apps.{actor}.{method}"]
```

CronJob は bpmn-dispatcher を経由して `/runs` を POST する。
Zeebe timer のコードベース上の BPMN XML は削除せず `status = "cron-replaced"` でマークする。

### pyzeebe からの migration path

```text
Phase 1: Kotoba/DatomicCheckpointSaver + Kotoba/DatomicStore 実装 (kotodama 内)
Phase 2: LangGraph Server + Granian の Helm chart 作成
         (mitama-udf-pool パターンを踏襲)
Phase 3: bpmn-dispatcher routing: Zeebe gRPC → /runs HTTP
Phase 4: pyzeebe primitives を LangGraph nodes に移植 (actor 単位、段階的)
         旧: @worker.task("actor.task") async def handler(job): ...
         新: @graph.node def handler(state: ActorState): ...
Phase 5: timer-start BPMN → K8s CronJob
Phase 6: Zeebe StatefulSet を shutdown (long-running multi-day process がゼロになったら)
```

### BPMN worker 併用条件

### Phase 4 canary rollout

First XRPC canary:

```text
com.etzhayyim.apps.shosha.agentLoop
  -> vertex_bpmn_lexicon_binding.routing_target = 'langgraph'
  -> assistant_id = shosha_agent_loop
```

Rationale:

- `shosha_agent_loop` is already registered in LangGraph Server.
- It is interactive and read-heavy: Kotoba/Datomic context read + LLM response +
  audit, without domain write side effects.
- Other shosha write/check bindings stay on Zeebe until each has a dedicated
  LangGraph graph and rollback evidence.

Migration: `30-graph/graph-schema/migrations/20260508996000_route_shosha_agent_loop_langgraph.ts`.

Smoke verification:

```bash
python -m kotodama.shosha_langgraph_smoke
```

The smoke checks `/bindings` for `routingTarget='langgraph'`, then dispatches
`/xrpc/com.etzhayyim.apps.shosha.agentLoop` and requires the dispatcher to return a
LangGraph async run handle (`202`, `assistant_id=shosha_agent_loop`, `run_id`).

### Zeebe の継続使用条件

Zeebe は新規採用しない。以下の条件のいずれかを満たす actor は、LangGraph
Server へ機械的に移植せず、ADR-2605081200 の SpiffWorkflow BPMN worker を
併用する:

1. BPMN XML が業務・監査・顧客説明上の正本である
2. timer / boundary event / process diagram が運用上のレビュー単位である
3. 既存 BPMN 資産を SpiffWorkflow でそのまま走らせる方が LangGraph node 化より安全
4. LangGraph Server の `interrupt()` / `/threads` より BPMN instance history が必要

現状 (`2026-05-08`) の方針: **LangGraph Server が main path**、BPMN-native flow は
**SpiffWorkflow BPMN worker が正式な並走 path**。Zeebe/pyzeebe は互換移行元としてのみ扱う。

## Consequences

**得られるもの**:
- pyzeebe の gRPC チャネル管理・watchdog・activation_monitor が消える
- arm64/amd64 ビルドミス問題が消える (ASGI server は platform-agnostic)
- Zeebe StatefulSet (1-2GB RAM) が消え、Redis (~50MB) に置換
- LangGraph の `/runs/stream` SSE で CF Worker へのリアルタイム streaming が可能
- `interrupt()` で HITL が BPMN message-event より簡単に実装できる
- cross-thread memory (`BaseStore`) で actor 間の長期記憶共有が可能

**制約・注意点**:
- Redis は transient のみ。永続化を Redis に書くことは禁止
- `Kotoba/DatomicCheckpointSaver` は `langgraph-checkpoint-postgres` を参考に
  RW 非互換箇所 (SKIP LOCKED / LISTEN/NOTIFY / ON CONFLICT) を全て回避すること
- LangGraph Server の `/runs` は at-least-once。冪等性は node 実装側で保証
- BPMN-native flow は SpiffWorkflow BPMN worker に送る。Zeebe を残す判断はしない
- Granian は `langgraph-api` が uvicorn を前提にしている CLI 部分をパッチが必要。
  K8s Deployment では `CMD ["granian", "--interface", "asgi", "langgraph_api:app"]` で起動

## References

- ADR-2605080000: Distributed Cognitive Actor System — 6-Layer Architecture (amended)
- ADR-2605072000: LangGraph Agent Loop Pattern (scope amended: L2→L2+L3)
- ADR-2605081200: SpiffWorkflow BPMN engine replacement (BPMN-native worker path)
- ADR-2604282300: CF Worker Edge Layer (bpmn-dispatcher K8s-internal routing)
- ADR-0056: BPMN-as-actor (Zeebe deploy pattern; migration source)
- ADR-2605080200: Pydantic v2 L6 Validation Contract (node 実装に適用)
- ADR-2605080300: SQLAlchemy Core Usage Contract (Kotoba/Datomic storage 実装に適用)
