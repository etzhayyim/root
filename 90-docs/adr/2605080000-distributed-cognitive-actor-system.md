---
id: adr-2605080000-distributed-cognitive-actor-system
title: "ADR-2605080000: Distributed Cognitive Actor System — 6-Layer Architecture"
status: active
doc_type: adr
topic: distributed-cognitive-actor-system
authoritative: true
last_verified: 2026-05-07
priority: 9.0
axis: architecture
weight: 0.90
priority_note: "CRITICAL — LangGraph / MCP / Kotoba/Datomic / Virtual Actor / WASM / Mojo / PyZeebe / RW External UDF の統合アーキテクチャを決定する"
authoritative_for:
  - distributed cognitive actor system overall architecture
  - layer assignment: CF Edge (L1) / LangGraph (L2) / K8s+Zeebe Virtual Actor Runtime (L3) / MCP Capability (L4) / Kotoba/Datomic Memory (L5) / PyZeebe+RW-Ext-UDF+WASM+Mojo Compute (L6)
  - actor taxonomy: Runtime Actor / Virtual Actor / Stream Actor
  - state model: Hot (pod) / Warm (Kotoba/Datomic MV) / Cold (S3/R2/Postgres)
  - PyZeebe layer assignment: L6 Compute (not L3)
  - Kotoba/Datomic External Python UDF layer assignment: L6 Compute (Arrow Flight RPC, not L5)
  - Kotoba/Datomic SQL UDF / Embedded Rust UDF layer assignment: L5 (internal execution)
  - WASM and Mojo role as enzymatic compute layer (L6)
  - LangGraph scope constraint (coordination only, L2)
  - MCP scope constraint (tool protocol, not actor protocol, L4)
depends_on:
  - adr-2605071200-myco-yeast-artificial-organism-jp-naming
  - adr-2605072000-langgraph-agent-loop-pattern
  - adr-2604282300
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-0056-bpmn-as-actor
  - adr-0044-kotoba-udf-language-strategy
related:
  - adr-2605061200-agi-active-inference-artificial-organism-architecture
  - adr-2605071900
  - adr-2605072100
  - adr-2605072000
supersedes: []
superseded_by: []
amended_by:
  - adr-2605080200-pydantic-l6-validation-contract
  - adr-2605082000-langgraph-graph-definition-as-data
  - adr-2605082100-langgraph-checkpointer-storage
  - adr-2605082200-pyzeebe-handler-thin-dispatcher-contract
---

# ADR-2605080000: Distributed Cognitive Actor System — 6-Layer Architecture

**Status**: accepted
**Date**: 2026-05-07
**Deciders**: Jun Kawasaki
**Supersedes**: —

## Context

AI workflow の実装が進む中で、LangGraph・MCP・Kotoba/Datomic・PyZeebe・WASM・Mojo の
各コンポーネントが個別 ADR に散在し、相互の役割境界が曖昧になっていた。

具体的な混乱パターン:
- MCP を actor transport として使おうとする実装が散見された
- LangGraph を DB/queue として使う実装が生まれた
- PyZeebe と LangGraph の責任境界が不明確で両方に同じロジックが書かれた
- WASM/Mojo の適用範囲が決まっておらず Python ML worker に CPU-intensive transform が混在した
- "Always-on actor" pod が増殖しスリープしないまま課金が膨らんだ

このシステムを **Distributed Cognitive Actor System** として再定義し、
各技術の役割を 6-Layer に明示的に固定する。

## Decision

### システム定義

このシステムは **AI workflow system ではなく Distributed Cognitive Actor System** として設計する。

```
                Cloudflare Edge          ← L1: User / Edge Layer
                      │
                      ▼
            Actor Activation API
                      │
                      ▼
           Kubernetes Pod Workers        ← L3: Virtual Actor Runtime Layer
          (pod lifecycle / Zeebe worker)
                      │
                      ▼
             LangGraph Runtime           ← L2: Cognitive Coordination Layer
                      │
                      ▼
             MCP Capability Bus          ← L4: Capability Network Layer
                      │
        ┌─────────────┼──────────────┬──────────┬─────────────┐
        │             │              │          │             │
   WASM Worker   Mojo Worker   Python ML   PyZeebe   RW Ext UDF  ← L6: Compute / Execution Layer
        │             │              │          │             │
        └─────────────┴──────────────┴──────────┴─────────────┘
                      │                               ▲
                      ▼                               │ Arrow Flight RPC
                 Kotoba/Datomic             ← L5: Streaming Memory Layer
          (Streaming Cognition Substrate)
```

---

### Layer 1 — User / Edge Layer (Cloudflare Workers)

**役割**: global ingress / websocket+session / auth / cache / lightweight routing / actor activation trigger

**制約**:
- CF Worker は Edge Layer のみ (ADR-2604282300 参照)
- business logic を持たない
- actor activation signal を Virtual Actor Runtime へ転送するだけ

---

### Layer 2 — Cognitive Coordination Layer (LangGraph)

**役割**: planning / conditional routing / retry / checkpoint / HITL / graph state transition

**制約 (CRITICAL)**:
- LangGraph は **coordination only**。DB・queue・transport・tool registry として使わない
- LangGraph を Zeebe の代替として使わない
- intra-job graph (≥3 LLM steps with branching) にのみ使用 (ADR-2605072000)
- `checkpointer=None` が原則。長期 HITL が必要な場合のみ `SqliteSaver` / `PostgresSaver`

---

### Layer 3 — Virtual Actor Runtime Layer (Kubernetes Pod + Zeebe)

**役割**: actor activation / state hydration / pod lifecycle management / passivation / Zeebe job dispatch

**Virtual Actor モデル**:
```
event
 ↓
activate actor (Zeebe job dispatch)   ← L3: K8s pod 起動 / 再利用
 ↓
hydrate state (Kotoba/Datomic MV read)    ← L5 から読む
 ↓
LangGraph execute (intra-job, if ≥3 steps)  ← L2
 ↓
PyZeebe job handler execute           ← L6: 実際の compute
 ↓
persist state (Kotoba/Datomic insert)     ← L5 に書く
 ↓
passivate (pod sleep / job complete)  ← L3: pod を戻す
```

**L3 の責務 (Zeebe + K8s)**:
- K8s Pod の scheduling / scaling / restart
- Zeebe BPMN process instance の lifecycle 管理
- retry / timeout / compensation の BPMN 定義 (application code に書かない)
- long-running process (日・週単位) の Zeebe BPMN timer 管理
- multi-actor fan-out / fan-in の BPMN parallel gateway

**pod = actor runtime (NOT pod = MCP interface)**:
- pod が MCP server を直接 expose しない
- pod は Zeebe job を L6 (PyZeebe) に渡して cognition を実行し結果を persist する
- MCP は L4 Capability Network として別途 expose する

**Actor 分類**:

| 種別 | 用途 | Runtime |
|---|---|---|
| Runtime Actor | realtime session / active planning / UI interaction | TS/Bun Worker (L6) |
| Virtual Actor | user memory / ingest pipeline / retrieval / document cognition | PyZeebe Python Worker (L6) |
| Stream Actor | aggregation / summarization / feature derivation / analytics | Kotoba/Datomic SQL/Rust UDF (L5) + External Python UDF (L6) |

---

### Layer 4 — Capability Network Layer (MCP)

**役割**: tool discovery / capability exposure / schema negotiation / tool invocation

**MCP の位置づけ**: `tool/capability membrane`

**制約 (CRITICAL)**:
- MCP は **tool protocol** であり **actor protocol ではない**
- MCP は mailbox / supervision / actor lifecycle を持たない
- actor 間通信に MCP を使わない (Zeebe message correlation を使う)
- tool def SSoT は `vertex_mcp_tool_def` registry (ADR-0087)

---

### Layer 5 — Streaming Memory Layer (Kotoba/Datomic)

**役割**: event accumulation / derived memory / materialized cognition / incremental context / stream joins / temporal memory

**本質**: `persistent cognition substrate`

**State モデル**:

| 種別 | 場所 | 特性 |
|---|---|---|
| Hot State | Pod memory (LangGraph state dict) | ephemeral runtime cognition |
| Warm State | Kotoba/Datomic Materialized View | event-derived, always consistent |
| Cold State | S3 / R2 / Postgres | object/document storage |

**Actor state は event-derived**:
- actor state を Pod に persist しない
- 全 state = `immutable events + materialized views`
- actor restart 時は Kotoba/Datomic MV から hydrate

**UDF 分担 (ADR-0044)**:

| UDF 種別 | 実行場所 | Layer |
|---|---|---|
| SQL UDF | Kotoba/Datomic 内部 | L5 |
| Embedded Rust UDF | Kotoba/Datomic 内部 | L5 |
| External Python UDF (`@udf(io_threads=100)`) | 外部 Arrow Flight サーバー | **L6** |

External UDF は Kotoba/Datomic が Arrow Flight RPC で呼び出す外部プロセス。LLM・IO bound な処理を担う。

**DDL 制約**: `rw-health-gate.sh` を先に満たす。`SlowDown` / recovery log がある時は DDL・bulk write・scale-down 禁止

---

### Layer 6 — Compute / Execution Layer (PyZeebe / WASM / Mojo / Python ML)

**本質**: `enzymatic compute layer`

#### PyZeebe

**位置づけ**: K8s Pod (L3) の上で動く job handler フレームワーク。Zeebe job を受け取り compute を実行する実行体。

**用途**:
- BPMN ServiceTask の Python 実装 (`@job_handler("actor.task_name")`)
- intra-job で LangGraph を呼ぶ場合の entry point (≥3 LLM steps)
- MCP tool call の呼び出し元 (L4 への入口)
- WASM / Mojo の呼び出し元 (L6 内の sub-compute)

**実装パターン**:
```python
@worker.task(task_type="actor.run_proposal")
async def run_proposal(job: Job) -> dict:
    state = await rw_read(job.variables["actor_did"])   # L5 hydrate
    result = graph.invoke(state)                         # L2 LangGraph
    await rw_insert(result)                              # L5 persist
    return {"status": "ok"}
```

**制約**:
- retry / timeout の設定は BPMN XML 側で行う (PyZeebe コードに書かない)
- PyZeebe worker は Zeebe broker のみと通信する。他 actor へ直接 HTTP しない

---

#### WASM

**用途**:
- sandboxed compute (untrusted code 実行)
- streaming transforms (chunked text/binary processing)
- portable execution (CF Workers Edge でも同一バイナリ動作)
- lightweight embedding lookup / tokenizer

**実装パターン**:
```python
# PyZeebe worker が WASM module をロードして呼び出す
wasm_instance = wasmtime.Instance(engine, module, imports)
result = wasm_instance.exports(store)["transform"](input_bytes)
```

**制約**: WASM は state を持たない純粋関数 compute のみ。I/O は Python host 経由

#### Mojo

**用途**:
- high-performance SIMD compute
- vectorized embedding generation
- ML inference (CUDA-backed) with Python interop
- tokenization / BPE at native speed

**実装パターン**:
```python
# Python worker から Mojo shared library を呼び出す
from mojo_lib import vectorized_embed  # MAX Engine Python bindings
embeddings = vectorized_embed(texts, model="bge-m3")
```

**制約**: Mojo module は純粋 compute 関数のみ export。Zeebe / Kotoba/Datomic への direct access 禁止

#### Python ML Worker

**用途**:
- OCR (Tesseract / PaddleOCR)
- CUDA inference (transformers / vLLM)
- LLM API call (Anthropic SDK with `resolveModelId()`)
- data processing (pandas / polars)

#### Kotoba/Datomic External Python UDF

**位置づけ**: Kotoba/Datomic (L5) が Arrow Flight RPC で呼び出す外部プロセス。Kotoba/Datomic 本体とは別プロセスで動く compute 実行体。

**用途**:
- LLM API call (Anthropic SDK / OpenAI) をストリーム処理の一部として実行
- IO-bound な外部サービス呼び出し (Web fetch / embedding API)
- `@udf(io_threads=100)` による高並列 IO 処理

**実装パターン**:
```python
from kotoba.udf import udf, UdfServer

@udf(input_types=["VARCHAR"], result_type="VARCHAR", io_threads=100)
async def llm_classify(text: str) -> str:
    client = anthropic.AsyncAnthropic()
    msg = await client.messages.create(model=resolveModelId(), ...)
    return msg.content[0].text

server = UdfServer(location="0.0.0.0:8815")
server.add_function(llm_classify)
server.serve()
```

**制約**:
- SQL UDF / Embedded Rust UDF は L5 (Kotoba/Datomic 内部実行)
- External Python UDF のみ L6 (外部プロセス)
- External UDF server は stateless。actor state を持たない

---

**Runtime 分担 (L6)**:

| Runtime | 向く用途 |
|---|---|
| TS/Bun Worker | orchestration / lightweight actors / realtime session / websocket / MCP routing |
| PyZeebe (Python) | Zeebe job handler entry point / LangGraph intra-job / WASM・Mojo 呼び出し元 |
| RW External Python UDF | ストリーム処理内 LLM call / IO-bound API (Arrow Flight RPC) |
| Python ML | OCR / CUDA inference / embeddings / transformers / data processing |
| WASM | streaming transforms / sandboxed compute / vectorized execution / portable functions |
| Mojo | high-performance SIMD / ML compute / tokenization / embedding generation |

---

## Biological Metaphor

| 技術 | 生物メタファー |
|---|---|
| Agent | 植物個体 |
| LangGraph | 維管束・成長制御 |
| Virtual Actor (PyZeebe) | 酵母・細胞 |
| MCP | 菌糸・根 |
| Kotoba/Datomic | 腐葉土・発酵層 |
| WASM | 酵素 |
| Mojo | 高速代謝酵素 (SIMD) |
| Cloudflare Edge | 分散神経系 |
| Kubernetes | 生態系維持層 |

---

## Design Principles Summary

1. **LangGraph = coordination only** — state transition / cognition orchestration に限定
2. **Actor と Tool を分離** — Actor = stateful cognitive entity / Tool = capability provider
3. **MCP = tool protocol, not actor protocol** — actor 間通信は Zeebe
4. **Runtime と Memory を分離** — Runtime = ephemeral cognition / Memory = persistent derived state
5. **Always-on actor を避ける** — virtual actor モデル、activation-driven
6. **Compute は enzymatic** — WASM/Mojo は純粋 compute 関数、state 持たない

---

## Consequences

**採用することで得られるもの**:
- layer 境界が明確になり、どのコンポーネントに何を書くか迷わない
- PyZeebe + BPMN による durable retry が LangGraph の checkpointer 不要にする
- WASM/Mojo の適用範囲が決まり Python worker の CPU-bottleneck が解消する
- virtual actor passivation で常駐 pod コストが削減される

**制約・注意点**:
- Mojo は MAX Engine が必要。RunPod GPU pod 推奨 (ADR-2605010000)
- WASM module は Rust / C / AssemblyScript で事前ビルド → R2 に配置
- PyZeebe worker と LangGraph の境界: Zeebe job = 1 PyZeebe handler, 内部 ≥3 LLM branches → LangGraph

---

## References

- ADR-2605072000: LangGraph Agent Loop Pattern (intra-job pattern)
- ADR-2604282300: CF Worker Edge Layer — Zeebe/RW UDF Business Logic
- ADR-2605071200: Myco-Yeast Artificial Organism (biological metaphor source)
- ADR-0056: BPMN-as-actor (Zeebe deploy pattern)
- ADR-0044: Kotoba/Datomic UDF Language Strategy (SQL/Rust/Python UDF 分担)
- ADR-2604251830: Shannon-Optimal 8-Layer Architecture
