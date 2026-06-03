---
id: adr-2604250836-langgraph-as-zeebe-servicetask
title: "ADR: LangGraph as BPMN ServiceTask — agentic actor placement on the BPMN-as-actor substrate"
status: proposed
doc_type: adr
topic: agentic-actor-placement
authoritative: true
last_verified: 2026-05-08
authoritative_for:
  - agentic-actor-runtime-placement
  - langgraph-zeebe-integration
  - langgraph-bpmn-servicetask-integration
  - cf-worker-vs-k8s-pod-boundary-for-agentic-apps
related:
  - adr-0056-bpmn-as-actor
  - adr-0036-shannon-cleanup-did-actor-topology
  - adr-0081-worker-direct-hyperdrive-persistence
  - adr-0049-python-udf-shared-pool-runtime
  - adr-0044-risingwave-udf-language-strategy
  - adr-0059-tool-runtime-selection-python-udf-default
  - adr-0046
  - adr-0092-every-vertex-as-actor
  - adr-2604231349-timestamp-numbering-policy
  - adr-2604231457-bpmn-security-posture-camunda-alignment
  - adr-2605081200-spiffworkflow-bpmn-engine-replacement
supersedes: []
superseded_by: []
---

# Context

ADR-0056 で T1/T2 actor の 80% を Zeebe + 7 generic primitives に集約し、
新規 actor 追加は `INSERT 2 rows` で済むようになった。残る δ Phase
(本リポジトリの未決領域) は **agentic actor** — multi-step reasoning /
tool-use loop / LLM-driven planning を要する actor の配置先である。

並行して二つの選択肢が提示されている:

1. CF Worker (TS) を K8s pod (Python + LangGraph + external UDF) に置換
2. CF Worker は BFF / フロントとして残し、agentic backend を別経路にする

設計判断は次の 3 案に整理される:

- **A. K8s pod only** — MCP / XRPC を含めて全部 K8s 一本化
- **B. CF BFF + K8s pod (BPMN バイパス)** — agentic は LangGraph 専用 pod
- **C. CF BFF + BPMN ServiceTask (LangGraph 内包)** — ADR-0056 を agentic に拡張

ADR-0056 (BPMN-as-actor)、ADR-0049 (Python UDF shared pool)、
ADR-0046 (yoro triple-witness loop)、ADR-0092 (every-vertex-as-actor) が
既存制約として効いており、新たな orchestration runtime を追加すると
冗長 axis (Shannon η の毀損) が発生する。

# Decision

**C を default 採用する**。

LangGraph は **BPMN ServiceTask** として ADR-0056 の worker runtime
に同居させ、`generic.langgraph.run` を 8 個目の generic primitive として
登録する。BPMN は引き続き orchestration の Single Source of Truth
であり、agentic actor も `INSERT 2 rows` (`vertex_bpmn_process_def` +
`vertex_bpmn_lexicon_binding`) で追加できる。

CF Worker は edge BFF / 認証 / rate-limit / SSR の役割に純化し、
agentic compute は持たない。`POST /xrpc/{nsid}` は従来通り
bpmn-dispatcher (`dispatcher.etzhayyim.com:8080`) に転送される。

case A (K8s only) は edge gateway invariant (ADR-0003 / ADR-0023) を
反故にするため不採用。case B (BPMN バイパス) は escape hatch として
**LangGraph のループが BPMN ServiceTask 粒度に収まらない場合のみ**
許可する (具体条件は本 ADR §Exceptions を参照)。

## Runtime update — 2026-05-08

ADR-2605081200 changes the concrete engine target from Zeebe/pyzeebe to
SpiffWorkflow + RisingWave for new runtime work. The placement decision in
this ADR remains: LangGraph belongs behind the BPMN worker primitive, not
inside CF Workers and not on a separate orchestration path by default.

Implementation mapping after ADR-2605081200:

- `generic.langgraph.run` is a Spiff task type claimed from
  `mv_spiff_ready_jobs`, not a pyzeebe subscription.
- BPMN process registration remains `vertex_bpmn_process_def` +
  `vertex_bpmn_lexicon_binding`.
- Runtime state and job replay use `vertex_spiff_*`; legacy Zeebe instance
  state is not part of new LangGraph execution.
- The old Zeebe 1 MB variable limit is retained as a conservative payload
  budget until Spiff smoke tests prove a larger direct-state envelope.

## Architecture (legacy Zeebe baseline; see Runtime update)

```
Client
  │
  ▼  HTTPS POST /xrpc/{nsid}
┌─────────────────────────┐
│ CF Worker (edge BFF)    │   auth / rate-limit / NSID validation
│  atproto.etzhayyim.com (PDS)  │
└──────────┬──────────────┘
           │  pipethrough (NSID-routed)
           ▼
┌──────────────────────────────────────────────┐
│ bpmn-dispatcher (aiohttp)                    │
│  vertex_bpmn_lexicon_binding[nsid] → process │
└──────────┬───────────────────────────────────┘
           │ gRPC
           ▼
   ┌──────────────────┐         ┌──────────────────────────────┐
   │ Zeebe broker     │ ── job ─│ zeebe-worker (pyzeebe)       │
   │  (8.6 LTS)       │         │   generic.db.select          │
   │                  │         │   generic.db.insert          │
   │                  │         │   generic.llm.chat           │
   │                  │         │   generic.llm.json           │
   │                  │         │   generic.http.fetch         │
   │                  │         │   generic.pds.dispatch       │
   │                  │         │   generic.audit.emit         │
   │                  │         │   com.etzhayyim.shinka.tick        │
   │                  │         │   generic.langgraph.run  ◀─★ │
   │                  │         └──────────────────────────────┘
   └──────────────────┘
```

## `generic.langgraph.run` primitive

| Field | Description |
|---|---|
| `graph_id` | LangGraph 定義の slug (`vertex_langgraph_def` から resolve) |
| `state` | 初期 state (JSON, ≤ 1 MB Zeebe variable 制約) |
| `config` | recursion_limit, checkpoint_namespace, model_overrides |
| `mode` | `"oneshot"` (single ServiceTask) / `"stepwise"` (1 hop = 1 ServiceTask, BPMN 側で展開) |

返り値は `final_state` + `tool_trace[]` + `usage`。エラーは Zeebe の
incident として上がり、Operate UI で再開可能。

### State 配置ルール

- **≤ 100 KB** — Zeebe variable に直接 (`mode=oneshot`)
- **100 KB – 10 MB** — Redis sidecar (`langgraph-state-redis` Deployment, TTL 24 h) +
  Zeebe variable には `state_ref` のみ
- **> 10 MB** — RisingWave `vertex_langgraph_state` table (永続) + `state_ref`

state ref scheme は ADR-0056 の AT URI 流儀を踏襲する:

```
at://did:web:langgraph.etzhayyim.com/com.etzhayyim.langgraph.state/{run_id}
```

### Tool surface

LangGraph の `@tool` は **既存の generic primitive を呼ぶシン**として
実装する。新しい tool は ADR-0056 primitive を増やすのと同義であり、
レビューを通す。これにより agentic loop の各 tool call は
`vertex_repo_commit` (collection `com.etzhayyim.bpmn.audit`) に自動的に
記録され、ADR-0046 triple-witness と同じ audit shape になる。

## Routing 制約 (CF / Pod の境界)

| 関心事 | 配置 |
|---|---|
| TLS termination, edge cache, DDoS shield | CF Worker |
| Auth (Service Auth JWT 検証, ADR-0022/0023) | CF Worker (PDS) |
| NSID lookup → BPMN routing | bpmn-dispatcher (pod) |
| BPMN orchestration | `bpmn-engine-host` / SpiffWorkflow (legacy: Zeebe broker) |
| Tool execution (db / http / llm / pds.dispatch) | Spiff worker pool (legacy: zeebe-worker) |
| LangGraph reasoning loop | Spiff worker task `generic.langgraph.run` |
| Heavy GPU inference (Murakumo) | 既存 Murakumo fleet (CF Tunnel 経由) |
| Per-row UDF (hash, parser, regex) | RisingWave (ADR-0044/0049) |

**禁止**: CF Worker 内で LangGraph を直接走らせる (Workers AI を呼ぶ
だけならよいが、ReAct ループは isolate の CPU time / 1 request 制約に
適合しない)。CF Worker と pod の双方で agentic state を保持する
(orchestration redundancy → η 毀損)。

# Comparison (Shannon η)

評価軸 (1.0 = 完全、0 = 欠落)、加重 sum:

| Axis | w | A. K8s only | B. CF + pod | **C. CF + BPMN ServiceTask** |
|---|---:|---:|---:|---:|
| Edge latency | 0.15 | 0.30 | 0.95 | **0.95** |
| Orchestration redundancy ↓ | 0.15 | 0.90 | 0.50 | **1.00** |
| 既存 infra 再利用 (ADR-0056) | 0.15 | 0.40 | 0.60 | **0.95** |
| Dispatch path 単一化 | 0.10 | 0.90 | 0.55 | **0.95** |
| 言語直交性 (TS edge / Py compute) | 0.10 | 0.50 | 0.85 | **0.85** |
| Runtime cost ($/月) | 0.10 | 0.40 | 0.75 | **0.80** |
| Observability (trace + audit) | 0.10 | 0.70 | 0.60 | **0.90** |
| LangGraph stateful 親和性 | 0.10 | 0.90 | 0.95 | **0.75** |
| Blast radius / failure axis | 0.05 | 0.50 | 0.80 | **0.85** |
| **加重 η (sum / 1.00)** | | **0.58** | **0.72** | **0.89** |

### 軸ごとの根拠

- **Orchestration redundancy**: A は Zeebe を捨てるので redundancy=0
  だが ADR-0056 投資の毀損コストが大きい。B は LangGraph 独自経路と
  BPMN が並立する (二重 SSoT)。C は BPMN 単一。
- **既存 infra 再利用**: bpmn-dispatcher / zeebe broker / pyzeebe が
  既に live。C は worker handler 1 個追加と Redis sidecar のみ。
- **Observability**: Zeebe Operate の process instance UI は
  agentic loop の各 hop を視覚化でき、`vertex_repo_commit` audit と
  整合する。B では LangGraph 独自 tracer を別途運用する必要。
- **LangGraph stateful 親和性**: C で 0.75 まで下がるのは Zeebe
  variable の 1 MB / instance 制約による。Redis sidecar で緩和できるが
  pure pod 配置 (B) よりは制約が残る。

# Consequences

## Positive

- Agentic actor の追加コストが ADR-0056 と同じ `INSERT 2 rows` 水準に
  揃う (`vertex_bpmn_process_def` + `vertex_bpmn_lexicon_binding` +
  必要なら `vertex_langgraph_def`)。
- BPMN が orchestration の SSoT を維持し、Path F middleware
  (memory / consent / audit / scheduler) が agentic loop にも同じ形で
  適用される。
- CF Worker は edge gateway 純化により ADR-0003 / ADR-0023 の axis を
  保つ。
- Zeebe Operate + `vertex_repo_commit` audit で agentic step が全て
  trace される (ADR-0046 triple-witness と同じ形)。

## Negative / Trade-off

- LangGraph state を Zeebe variable に圧縮するか Redis sidecar に
  逃がす運用ルールが必要。
- pyzeebe worker pod の memory 上限を要再設計 (LangGraph in-process
  state + tool result バッファ)。`zeebe-worker` Deployment の
  `resources.requests.memory` を 1 Gi → 4 Gi 想定で見積もる。
- ServiceTask polling (~50–100 ms) が LangGraph の各 hop に乗る。
  数千 step の loop には不向き → §Exceptions の B 経路に逃がす。

## Migration

| Step | 内容 | 完了条件 |
|---|---|---|
| 1 | `generic.langgraph.run` の primitive 仕様確定 (input/output schema, state ref scheme) | ADR review pass |
| 2 | pyzeebe worker に `langgraph_run` handler 追加。`zeebe-worker` image rebuild | integration test green (1 graph, 1 hop, audit emit) |
| 3 | `langgraph-state-redis` Deployment + Service 追加 (1 replica, 256 Mi, TTL 24 h) | ping OK / state round-trip OK |
| 4 | `vertex_langgraph_def` table migration (RisingWave schema 追加) | `etzhayyim graph migrate` clean |
| 5 | PoC 1 actor: yoro autonomy loop (ADR-0046) を BPMN + LangGraph に移植 | 24 h soak + audit consistent |
| 6 | η 実測 (tool call latency p50/p95, trace completeness, cost / 1k loops) | C の 0.89 検証 ± 0.05 以内 |
| 7 | `[[migrations]] agentic-actor-to-bpmn-langgraph` 横展開 | candidate actor list 確定 |

各 Step は独立に rollback 可能 (Step 5 までは既存 actor に影響しない)。

# Exceptions

case B (BPMN バイパス、CF + pod 直結) は次の **すべて** を満たす場合に
限って tactical 採用を許可する:

1. LangGraph の typical run が **500 hop 以上** または **30 分以上**
   持続する (ServiceTask polling overhead が無視できない)
2. State が **10 MB を恒常的に超え**、Zeebe variable / Redis sidecar
   どちらにも収まらない
3. Audit を `vertex_repo_commit` 以外の経路で別途確保する (ADR-0046
   triple-witness 準拠の独立 logger)

採用時は `[[migrations]]` に `escape-hatch` フラグ付きで登録し、
四半期ごとに恒久化 (case C への寄せ戻し) を検討する。

case A (K8s only / CF Worker 全廃) は本 ADR では却下する。
将来 atproto edge gateway invariant (ADR-0003 / ADR-0023) を見直す
ADR が成立した場合のみ再検討する。

# Alternatives Considered

## A. K8s pod only (MCP / XRPC を含め全面 pod 化)

- η ≈ 0.58。
- Edge POP (200+) を喪失し、ユーザ P95 latency が region 数 ms 増加。
- CF Worker 投資 (BFF / 認証 / SSR / Hyperdrive binding) を全廃する
  rewrite コストが大きい。
- ADR-0003 (atproto edge gateway) 違反。

## B. CF BFF + K8s pod, BPMN バイパス

- η ≈ 0.72。
- LangGraph stateful 親和性は 0.95 (最高) だが orchestration が
  BPMN と並立するため、新 actor 追加が `INSERT 2 rows` ではなく
  helm rollout に戻る。
- 数千 hop / 長時間 reasoning に強い → §Exceptions の escape hatch
  として保持する。

## C. CF BFF + BPMN ServiceTask (採用)

- η ≈ 0.89。
- Trade-off は Zeebe variable 1 MB 制約と ServiceTask polling overhead。
  Redis sidecar + state ref で前者を、`mode=oneshot` で後者を緩和。
- ADR-0056 への純粋な拡張で、新 ADR が増やす axis は
  `generic.langgraph.run` primitive 1 個と Redis sidecar 1 pod のみ。

# References

- ADR-0056 — BPMN-as-actor (`90-docs/adr/0056-bpmn-as-actor.md`)
- ADR-0036 / ADR-0081 — Worker-direct Hyperdrive persistence
- ADR-0049 — Python UDF shared pool runtime
- ADR-0044 — RisingWave UDF language strategy
- ADR-0046 — yoro triple-witness autonomy monitoring
- ADR-0092 — every-vertex-as-actor
- ADR-2604231457 — BPMN security posture / Camunda alignment
- ADR-2604231349 — Timestamp-based ADR numbering policy
- Camunda Zeebe 8.6 docs — ServiceTask, variables, incident handling
- LangGraph docs — checkpoint, recursion_limit, ReAct loop
