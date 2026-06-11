---
id: adr-2605082200-pyzeebe-handler-thin-dispatcher-contract
title: "ADR-2605082200: PyZeebe Handler Thin Dispatcher Contract"
status: active
doc_type: adr
topic: pyzeebe-handler-thin-dispatcher-contract
authoritative: true
last_verified: 2026-05-08
priority: 8.6
axis: architecture
weight: 0.86
priority_note: "PyZeebe job handler を MCP tool dispatcher に縛り込み、L6 の最後の code island を消す。これで actor 自己進化が完成する"
authoritative_for:
  - PyZeebe job handler scope (MCP tool call dispatcher only)
  - prohibited inline logic in handler body
  - tool_id resolution path (BPMN variable → `vertex_mcp_tool_def`)
  - tool body deployment topology (K8s Deployment per primitive tool)
  - MCP transport (HTTP+SSE, mTLS via SPIFFE)
related:
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605082000-langgraph-graph-definition-as-data
  - adr-2605082100-langgraph-checkpointer-storage
  - adr-0087-kotodama-mcp-tool-facade
  - adr-0056-bpmn-as-actor
  - adr-2605081200-spiffworkflow-bpmn-engine-replacement
supersedes: []
superseded_by: []
---

# ADR-2605082200: PyZeebe Handler Thin Dispatcher Contract

**Status**: accepted
**Date**: 2026-05-08
**Deciders**: Jun Kawasaki
**Supersedes**: —

## Context

ADR-2605080000 で L6 Compute / Execution Layer の中心実装として PyZeebe を据えたが、
job handler の中身は **任意の Python コード** が許されていた。これは実態として、
BPMN ServiceTask が新しい振る舞いを得るたびに repo commit を必要とする
code island が L6 に残っていたことを意味する。

ADR-2605082000 で LangGraph topology が data 化され、ADR-2605082100 で
checkpointer 保管先が確定したことで、`actor/agent が data 層への書き込みのみで
進化する` 目標の最後のピースが PyZeebe handler になった。

ADR-2605080000 はすでに次の制約を持っていた:

- `pod = actor runtime (NOT pod = MCP interface)`
- `pod が MCP server を直接 expose しない`
- `MCP は L4 Capability Network として別途 expose する`
- `tool def SSoT は vertex_mcp_tool_def registry (ADR-0087)`

これを徹底すれば、handler は dispatch だけ行う薄い shell に縮約できる。

## Decision

### 1. Handler scope = thin dispatcher

PyZeebe job handler に許される処理は次の 3 段階のみ:

```python
@worker.task(task_type="actor.dispatch")
async def dispatch(job: Job) -> dict:
    tool_id = job.variables["tool_id"]            # BPMN variable から
    tool    = await registry.resolve(tool_id)     # vertex_mcp_tool_def
    result  = await mcp.call(tool.endpoint, job.variables["input"])
    return {"output": result}                     # BPMN variable へ
```

**禁止** (CI hook で機械検査する):

- handler 内で LLM SDK を直接 import / 呼び出し
- handler 内で Kotoba/Datomic / PDS / Hyperdrive に直接 SQL
- handler 内で外部 HTTP (MCP transport 以外)
- handler 内で business 条件分岐 (BPMN gateway / Rego / DMN に押し出す)
- handler 内での state hydration (state は MCP tool 側で読む)

handler は **idempotent** であること。retry は BPMN 側が司る (ADR-0056)。

### 2. Tool body = K8s Deployment per primitive

primitive MCP tool は **1 tool = 1 K8s Deployment** で運用する。

```
[BPMN ServiceTask "actor.dispatch"]
        │  Zeebe job
        ▼
[PyZeebe handler pod] ── thin dispatcher ──┐
                                            │ MCP/HTTP+SSE
                                            ▼
                                  [Capability Service Mesh]
                                    │      │      │
                              tool-A  tool-B  tool-C        ← L4 MCP tool servers
                              Deployment (stateless, HPA)
```

**Deployment 仕様**:

- stateless、`replicas` は HPA で自動
- container は MCP server (`/mcp` HTTP+SSE) のみ expose
- mTLS は SPIFFE SVID、capability bus 内のみ accept
- liveness = MCP `initialize` ping
- ConfigMap / Secret は K8s ネイティブ、tool 内部実装

**禁止**:

- 1 Deployment に複数 tool を相乗りさせる (registry の解決粒度を粗くするため)
- actor runtime pod (PyZeebe worker pod) で MCP server を expose する (ADR-2605080000)
- tool 内で他 tool を直接呼ぶ (graph topology は LangGraph / BPMN 側に書く)

### 3. tool_id resolution

BPMN ServiceTask は `tool_id` を変数として持つ。handler は registry を引いて
`endpoint URL` を得る。

```
vertex_mcp_tool_def  (ADR-0087)
  tool_id            TEXT PRIMARY KEY    -- com.etzhayyim.tools.<domain>.<name>@<semver>
  endpoint           TEXT                -- https://<svc>.capability.svc.cluster.local
  input_schema       JSONB
  output_schema      JSONB
  ...
```

`endpoint` 変更は registry insert のみで反映される (DNS 解決ではなく registry 解決を SSoT にする)。
hot deploy 時は新 `tool_id@semver` を追加 → BPMN / LangGraph 側を切替。

### 4. Self-evolution の閉路完成

ADR-2605082000 + ADR-2605082100 + 本 ADR が揃うと、自己進化の閉路は次になる:

```
agent が新しい振る舞いを思いつく
  ↓
(a) 既存 primitive tool の組合せで足りる場合:
      - vertex_langgraph_graph_def に新 row     (ADR-2605082000)
      - or vertex_bpmn_process_def に新 row    (ADR-0056)
      - or vertex_mcp_tool_def に新 composite tool def
      → repo commit 0
  ↓
(b) primitive が足りない場合:
      - 新 K8s Deployment + Dockerfile (repo commit 必要、頻度低い)
      - vertex_mcp_tool_def に endpoint を insert
  ↓
shadow run / canary
  ↓
昇格 or rollback
```

### 5. CI 検査 hook

`lint-pyzeebe-thin-handler` を新設:

- `@worker.task` 直下の関数が `anthropic` / `httpx` / `kysely` / `psycopg` を
  import していたら fail
- handler 関数の AST が `if/match` で business 分岐を持っていたら warn
- handler 関数の cyclomatic complexity > 3 で fail
- handler 関数の LOC > 30 で fail

## Consequences

**得られるもの**:

- L6 の最後の code island が消え、actor 自己進化の data-only 閉路が成立
- primitive tool が独立 Deployment になることで HPA / failure isolation / blue-green が容易
- handler の review 負荷が機械検査に置き換わる
- BPMN / LangGraph / MCP registry の 3 つだけが「振る舞いの SSoT」になる

**制約・注意点**:

- primitive tool 数が増えると K8s Deployment 数も増える (HPA / cost monitoring が必要)
- registry resolve がホットパスに乗るため registry cache 必須
  (CF Worker / actor pod に in-memory cache、TTL 60s)
- thin handler 制約は強い → 既存 PyZeebe worker の段階的 migration が要る
- composite tool (tool が tool を呼ぶ) を禁じたため、合成は LangGraph or BPMN 側に
  必ず現れる。これは意図 (合成 = 振る舞い = data 化対象)。

## References

- ADR-2605080000: Distributed Cognitive Actor System (L4 / L6 制約の出所)
- ADR-2605082000: LangGraph Graph Definition as Data (合成側の data 化)
- ADR-2605082100: LangGraph Checkpointer Storage (補完)
- ADR-0087: Kotodama MCP Tool Facade (`vertex_mcp_tool_def`)
- ADR-0056: BPMN-as-actor (BPMN data 化の precedent)
- ADR-2605081200: SpiffWorkflow BPMN Engine Replacement (BPMN engine 実装)
