---
id: adr-2605082000-langgraph-graph-definition-as-data
title: "ADR-2605082000: LangGraph Graph Definition as Data"
status: active
doc_type: adr
topic: langgraph-graph-definition-as-data
authoritative: true
last_verified: 2026-05-09
priority: 8.8
axis: architecture
weight: 0.88
priority_note: "CRITICAL — actor/agent self-evolution の data-only 進化を達成するための残り 3 ピースのうち最重要。LangGraph topology を repo code から Kotoba/Datomic vertex table に剥がす"
authoritative_for:
  - LangGraph graph topology storage location (Kotoba/Datomic `vertex_langgraph_graph_def`)
  - LangGraph node contract (MCP tool invocation only, no inline Python logic)
  - graph compiler responsibility (def → StateGraph build at runtime)
  - conditional edge SSoT (Rego/DMN ref, not Python lambda)
  - graph version / lineage model (immutable rows, semver-style id)
related:
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605072000-langgraph-agent-loop-pattern
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-0087-kotodama-mcp-tool-facade
  - adr-0056-bpmn-as-actor
  - adr-2605082100-langgraph-checkpointer-storage
  - adr-2605082200-pyzeebe-handler-thin-dispatcher-contract
supersedes: []
superseded_by: []
---

# ADR-2605082000: LangGraph Graph Definition as Data

**Status**: accepted
**Date**: 2026-05-08
**Deciders**: Jun Kawasaki
**Supersedes**: —

## Context

ADR-2605080000 は LangGraph を L2 Cognitive Coordination Layer に固定した。
しかし graph topology そのものは現状 **Python authored code** であり、
node function も Python module として repo に commit されている。

これは `actor/agent が data 層 (Kotoba/Datomic) への書き込みのみで自己進化する`
という platform 目標 (BPMN process / MCP tool registry が既に達成済み) と矛盾する。

具体的に、以下が code island として残っていた:

- graph topology (nodes, edges, conditional routing) が `.py` ファイル
- node function が Python `def` で実装され、その中で LLM call / tool call / business logic が混在
- 新しい reasoning chain を試すたびに repo commit + deploy が必要
- BPMN は data-driven、MCP tool は registry-driven なのに、両者を結ぶ
  LangGraph だけが code-driven という非対称が残っていた

ADR-0056 (BPMN-as-actor) と ADR-0087 (Kotodama MCP Tool Facade) と
同じ design pattern を LangGraph にも適用する。

## Decision

> **2026-05-09 訂正 (iter3)**: 初稿は `vertex_langgraph_graph_def` 並列 table を提案したが、
> 既存 `vertex_langgraph_assistant{,_node}` + `vertex_langgraph_deployment`
> (ADR-2605080600 amendment, migration `r_20260509100000_vertex_langgraph_assistant_registry`)
> が既に topology を data 化しており、parallel SSoT は冗長 (ADR-2605080700 の
> live-RW SSoT 原則違反)。初稿の並列 migration は削除済み。本 ADR は既存 schema を
> 拡張する形に書き直した。

### 1. Graph topology は既存 SSoT table 群に格納する

```
vertex_langgraph_assistant
  vertex_id       PK = assistant_id
  assistant_id    NOT NULL
  version         BIGINT NOT NULL
  kind            'py_factory' | 'topology'        -- 'topology' = data-driven
  factory_path    VARCHAR  (kind='py_factory' のみ)
  spec            VARCHAR  (kind='topology' の JSON: state_keys / entry / edges /
                            conditional_edges)
  description     VARCHAR
  -- ADR-2605082000 lineage 拡張 (migration r_20260509130000):
  checkpointer_mode  VARCHAR DEFAULT 'none'       -- 'none' | 'postgres' | 'rw_vertex'
  authored_by        VARCHAR                       -- DID of authoring agent/operator
  superseded_by      VARCHAR                       -- assistant_id of replacement, NULL = current

vertex_langgraph_assistant_node
  vertex_id       PK = "{assistant_id}:{node_id}"
  assistant_id    NOT NULL
  node_id         NOT NULL
  kind            'sql_udf' | 'rust_udf' | 'py_ext_udf' | 'mcp_tool' | 'llm' | 'py_primitive'
  ref             VARCHAR  -- UDF name / MCP URI(or tool_id) / model tier / dotted path
  config          VARCHAR  (JSON)

vertex_langgraph_deployment
  vertex_id       PK = nsid
  nsid            NOT NULL
  assistant_id    NOT NULL
  version         BIGINT NOT NULL
  status          'active' | 'disabled'    -- active = the live pin for this nsid
  replicas        BIGINT
```

`vertex_langgraph_deployment.status` が live/disabled の pin、`superseded_by` が
assistant の immutable lineage を表現する。**新 `lifecycle` 列は追加しない** —
`status` で十分 (ADR-2605080700 重複回避)。shadow / canary は別 nsid + 上位 router
で実現する (assistant 行に semantics を持たせない)。

### 2. Node contract: data-resolved kinds only

新規 row が許される `vertex_langgraph_assistant_node.kind` は次の **4 つ** のみ:

| kind | ref が指すもの | data SSoT |
|---|---|---|
| `mcp_tool` | MCP endpoint URI または `mcp://<tool_id>` (registry resolve) | `vertex_mcp_tool_def` |
| `sql_udf` | SQL function 名 | Kotoba/Datomic catalog |
| `py_ext_udf` | External Python UDF 名 (Arrow Flight) | Kotoba/Datomic catalog |
| `llm` | tier 名 (`structured` / `general` / model id) | `llm-model-registry.ts` SSoT |

**禁止**:

- 新規 row で `kind='py_primitive'` を使うこと (ref = Python dotted path = code island)
- `kind='rust_udf'` の新規追加 (既存 row はそのまま、新規はビルド済 UDF を `sql_udf`/`py_ext_udf` 経由で expose)
- conditional edge router を Python lambda にすること (Rego/DMN ref を使う、ADR-2604261100)
- node から複数 tool を呼ぶこと (合成は edge / 別 node で表現)

これにより新しい reasoning chain は **既存の data-resolved kinds の組み合わせを
新 `assistant_id` として insert するだけ** で生まれる。Python ファイルへの
commit は primitive tool / UDF / model 追加の時だけ要る (低頻度)。

### 2.5. py_primitive 段階廃止

| 段階 | 内容 |
|---|---|
| 即時 | CI lint で新規 `py_primitive` row 追加を reject (`lint-langgraph-py-primitive-ban`) |
| Phase 1 | 既存 `py_primitive` row を `mcp_tool` / `sql_udf` / `llm` に書換 (1 ノードずつ) |
| Phase 2 | `langgraph_loader._compile_topology` の `py_primitive` 分岐を削除 |
| 完了 | `langgraph_node_resolvers.resolve_node` から `py_primitive` 削除 |

### 2.6. MCP tool ref の registry resolution

`mcp_tool` kind の `ref` は次のいずれか:

- HTTP URL (legacy / 後方互換) — `https://mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message`
- `mcp://<tool_id>` — `vertex_mcp_tool_def.tool_id` を引いて endpoint を解決

新規は後者を使う。`make_mcp_tool_node` (`langgraph_node_resolvers.py`) が
prefix 判定で resolution path を選ぶ。endpoint 変更は registry insert のみで
反映される (DNS ではなく registry を SSoT に)。

### 3. Conditional edge は Rego/DMN ref で表現する

edge の `condition_ref` は repo 内の Rego policy / DMN decision table の id を指す。
Python lambda は禁止。

```jsonc
{
  "from": "classify_intent",
  "to":   "escalate_to_human",
  "condition_ref": "dmn:com.etzhayyim.policies.intent.escalation@1.0.0"
}
```

これにより authority/policy は ADR-2604261100 の SSoT (Rego/DMN) に集約され、
LangGraph def には参照だけが残る。

### 4. Graph compiler: runtime build (existing)

L3 actor runtime (LangGraph Server, ADR-2605080600) は既に
`kotodama/langgraph_loader.py` で compiler を持つ:

1. `vertex_langgraph_deployment WHERE status='active'` から (assistant_id, version, kind, factory_path, spec) を取得
2. kind='topology' の場合 `vertex_langgraph_assistant_node` rows を取得
3. `_compile_topology()` が `state_keys` から `TypedDict` schema、`entry`/`edges`/
   `conditional_edges` から `StateGraph` を build、各 node を `resolve_node(kind, ref, config)` で解決
4. `builder.compile()` で StateGraph を produce、ADR-2605082100 の `checkpointer_mode` を
   honor して checkpointer を attach (TODO: 現状 compiler は checkpointer 未対応、Phase 1 で接続)

compiler は stateless。同じ `(assistant_id, version)` から決定論的に同じ実行体を生成する。

### 5. Self-evolution flow

agent が新しい reasoning chain を発明する流れ:

```
agent が hypothesis 生成
  ↓
agent が `vertex_langgraph_graph_def` に新 row を insert
  (新 graph_id = 既存名 + bumped semver)
  ↓
既存 BPMN ServiceTask の graph_id 引数を新 id に切替 (これも data write)
  ↓
次回 actor activation 時に compiler が新 graph を build
  ↓
shadow run / canary で評価 (`vertex_langgraph_run` event log)
  ↓
良ければ旧 graph_id に `superseded_by` を立てる
```

**この間 repo commit は 0 回**。primitive MCP tool が足りない時だけ repo commit する。

## Consequences

**得られるもの**:

- LangGraph topology が agent の自己進化対象になる (BPMN / MCP registry と同列)
- A/B test / canary が graph_id 切替だけで実現する
- code review 不要なので試行回数が桁違いに増やせる
- node 実装が MCP tool 側に集約されるので tool reuse が進む

**制約・注意点**:

- graph compiler は idempotent / deterministic である必要がある
- `state_schema` の JSON ↔ Pydantic v2 変換が必要 (ADR-2605080200 と整合)
- node が 1 tool に縛られるため、micro-tool が増える傾向 (`vertex_mcp_tool_def` のスケール対応が要る)
- agent が graph を破壊するリスク → `authored_by` で trace、Rego policy で
  agent の write 権限を制限、shadow run 必須
- `vertex_langgraph_graph_def` への write は L4 MCP tool (`com.etzhayyim.tools.langgraph.publish`)
  経由のみ許可 (生 SQL 禁止)

## Phase D — Sub-primitive expansion (2026-05-09)

Phase A/B 完了時点で live `py_primitive` が 61 ノード残存。中身を精査すると
ほぼ全てが「LLM 呼出 + db 書込 + audit emit + 時刻スタンプ」の合成。各
node を 1:1 で mcp_tool 化するには、ノード本体内で頻出する **sub-primitive**
が追加で必要。Phase D で 2 つ追加:

- `com.etzhayyim.tools.time.now` — 壁掛け時計 (`iso` / `epoch_s` / `epoch_ms`、
  `tz` 対応)。`tools_time_worker_main:task_time_now`。
  動機: 全 supervisor / agent ノードが `int(time.time()*1000)` /
  `datetime.now(tz=UTC)` を inline で呼ぶ。これを mcp_tool に切り出すと
  合成 node 全体が data-only で再構成可能になる。
- `com.etzhayyim.tools.crypto.hash` — 内容アドレス hash (`sha256` / `sha1` /
  `md5` / `sha512`、`hex` / `base64` 出力)。
  `tools_crypto_worker_main:task_crypto_hash`。
  動機: `_work_blob_vertex_id` 系の sha256 + 名前空間連結が複数 actor に
  存在し、共通 primitive 化することで blob_store 系合成 node の
  decomposition が可能になる。

これで generic primitives は **10** に拡大: `const.echo` / `audit.emit`
/ `llm.chat` / `sql.query` / `sql.exec` / `http.fetch` / `json.extract`
/ `transform.map` / `time.now` / `crypto.hash`。

**foreach は resolver kind として実装 (案 b 採用)**: 残ノード精査で
`for write in result.get("db_writes")` 系の LLM 出力配列 fan-out が
supervisor 系 (`etzhayyim_company_ops` / `lawfirm_marketing_ops` /
`kaisya_member_assistant`) に共通することを確認。foreach は

- ❌ MCP primitive (registry-resolved `mcp://...flow.foreach`) — module-level
  handler 参照 / HTTP self-call が必要で、リーフ抽象を逸脱
- ✅ **resolver kind** (`langgraph_node_resolvers.py` で `kind=foreach`、
  inner node を plan-time に compile)

として実装。inner node は既存 4 kind (`mcp_tool` / `sql_udf` /
`py_ext_udf` / `llm`) いずれか。Config:

```json
{
  "kind": "foreach",
  "config": {
    "items_path": "<dotted path into state, json.extract grammar>",
    "result_key": "<state key for collected outputs>",
    "item_key":   "<key the inner node reads, default 'item'>",
    "node": { "kind": "...", "ref": "...", "config": { ... } }
  }
}
```

実装上の制約:
- 反復は **sequential** (順序依存の supervisor pattern を保つ。並列は
  必要になった時点で別オプションを追加)
- inner node は plan-time に 1 回 compile される (per-iteration compile
  禁止、deterministic 保証)
- 外側 state は inner にそのまま透過し、`item_key` のみ上書き — `org_id` /
  `repo` 等の context を per-iteration shuffle 不要

### Phase D2 — Routing-layer code-island の可視化 + 解消

監査の盲点として、`vertex_langgraph_assistant.config` JSON 内の
`conditional_edges[].router` が Python dotted path を指す状態が存続して
いた (`audit-langgraph-self-evolution-debt.mjs` は `_node` 行のみ scan)。
これを 2 step で解消:

1. **Audit 拡張**: 同 script に `route_island` 軸を追加。live topology
   assistant の config から `"router"` (legacy py_primitive callable) /
   `"field"` (data-driven state lookup) 出現数を計上、live-only も区別。
   結果 (2026-05-09): live router=12 / live field=0 → routing は 0%
   data-share。これまでの node 57.6% 表示はこの分を見落としていた。
2. **`langgraph_loader._compile_topology` 拡張**: `conditional_edges` が
   `router` (legacy) と `field` (Phase D) を同等に受理。`field` は
   `tools.json.extract` と同じ navigator で state から値を取り出し、
   `path_map` で分岐。両方指定 / 両方未指定はエラー。`default` キーで
   missing/unmatched 時の fallback が指定可能。

```json
{
  "from": "supervisor",
  "field": "domain",         // dotted path, state.domain を読む
  "paths": {"hr": "hr", "finance": "finance", ...},
  "default": "governance"     // 任意、未マッチ時のターゲット
}
```

これで supervisor / classifier 系の Python router を 1 行 INSERT で
field 形式に置換できる。同じ topology 行の UPDATE もしくは新 v2
assistant への upsert で deploy。inner node が data-only なら supervisor
全体が code-free になる (例: etzhayyim_company_ops 8 ノードを
mcp_tool 化 + supervisor の `router` を `field: "domain"` に切替で
完全 data-only 化)。

## Phase E — LLM-supervisor Decomposition (planned, 2026-05-09)

Phase D2 完了時点で live `py_primitive` 61 ノード残存。内訳精査の結果、
ほぼ全てが「LLM 呼出 + LLM 出力配列に対する fan-out db_insert + audit」の
合成 node。全て Phase D で landed した primitive (`tools.llm.chat` /
`tools.transform.map` / `tools.sql.exec` / `tools.audit.emit`) と
`kind=foreach` resolver で **原理的に分解可能** だが、いくつか追加要件がある。

### 残ノードの実形 (live 61 件、対象 10 assistants)

| Assistant                            | Live nodes | Pattern                                                  |
|--------------------------------------|------------|----------------------------------------------------------|
| `lawfirm_marketing_ops`              | 9          | supervisor LLM + 5 domain agents + compliance + audit    |
| `etzhayyim_company_ops`               | 8          | supervisor LLM + 6 domain agents + audit                 |
| `kaisya_member_assistant`            | 8          | resolve + load_context + supervisor + 3 dispatch + audit |
| `animeka_autopilot`                  | 8          | LLM scene + 4 ComfyUI gen + compose_post + audit         |
| `webmk_proposal`                     | 6          | research + competitors + strategy + copy + quality + store |
| `yoro_product_ingest`                | 5          | crawl + extract + LLM analyze + persist + audit          |
| `coverage_gap_bridge`                | 5          | scan + ingest + infer + generate + statsSync             |
| `tsukuru_isic_pulse`                 | 2          | classify + persist                                       |
| `shosha_agent_loop` (2 assistants)   | 3+3        | fetch_context + LLM + emit (×2 for callLlm flavour)      |
| 残り標準パターン外                    | 5-6        | echo / agent_runtime_lease_autopilot 等の単発ノード         |

### 標準 Decomposition Template

LLM-driven domain agent の典型形 1 ノードは、以下の **5-step chain** に分解する:

```
[supervisor → state.<key>_input]
    ↓ kind=mcp_tool ref=mcp://com.etzhayyim.tools.llm.chat
    ↓ result_key: <key>_llm_out
    ↓ args: {system: "...", user_template: "...", input_keys: [...]}
[<key>_llm_out  ─ {result, action_items, db_writes, ok, error}]
    ↓ kind=foreach
    ↓ items_path: <key>_llm_out.result.db_writes
    ↓ result_key: <key>_inserted
    ↓ inner: kind=mcp_tool ref=mcp://com.etzhayyim.tools.sql.insert_row
    ↓        config: {input_paths: {table:"item.table", row:"item.row",
                                     vertex_id_template: "<convention>"}}
[<key>_inserted ─ list of {vertexId, ok}]
    ↓ kind=mcp_tool ref=mcp://com.etzhayyim.tools.transform.map
    ↓ args: {mapping: {action_items: "$.<key>_llm_out.result.action_items",
                        ok: "$.<key>_llm_out.result.ok"}}
[<key>_summary]
    ↓ edge to next domain or audit
```

合成 node 1 件 = 4 mcp_tool node + 1 foreach node。10 assistants × ~5
domain agents = ~50 合成 node × 4 = **200 新 mcp_tool node** 規模。

### 必要な追加 primitive (1 件)

**`com.etzhayyim.tools.sql.insert_row`** — 動的 row → INSERT。
現行 `sql.exec` は固定 SQL string + bindings。LLM 出力の `db_writes` は
table 名と row の column 集合がランタイム決定なので、これを受け取れる
primitive が要る:

```python
async def task_sql_insert_row(
    table: str,
    row: dict,
    vertex_id_template: str | None = None,
    owner_did: str | None = None,
    collection: str | None = None,
) -> dict:
    """
    INSERT row into table. Auto-derive vertex_id if absent and template given.
    Returns {vertexId, ok, error?}.

    vertex_id_template grammar: same as `transform.map` fmt — supports
    {owner_did}, {collection}, {stamp}, {nanoid8} placeholders.
    """
```

設計責任分界:
- LLM は table と row の中身だけ決める (column 集合は data 駆動)
- vertex_id derivation は primitive 側 (時刻・nanoid 生成は host)
- table/column safety は allowlist (Rego or SQL UDF) で別途担保

generic primitives は 10 → 11 に拡大予定。

### 既知の制約と例外

1. **LLM 出力の安定性**: 同じ task に対し LLM が異なる schema を返すと
   foreach inner node が失敗する。`db_writes[].row` の shape を Pydantic
   v2 schema (ADR-2605080200) で gate すべき。LLM 出力 → `tools.json.extract`
   による schema validation step を chain に挿入する案あり。
2. **Read-after-LLM context fetch**: `legal_agent` / `governance_agent` /
   `personnel_agent` は LLM 呼出前に追加 SQL 結果を context に入れる。
   `tools.sql.query` を chain 先頭に追加するだけで対応。
3. **Branching within agent**: 一部 agent は内部に if/else を持つ
   (e.g. `kaisya_member_assistant.dispatch_*`)。これは追加 conditional_edge
   + field routing で吸収。Phase D2 で解決済み。
4. **Native side-effect primitives**: `animeka_autopilot` の ComfyUI 呼出
   は host-binding (Python httpx + binary blob) のため mcp_tool 化が
   そぐわない。これらは **legitimate exception** として py_primitive 残存を
   許容する。完了基準は「全合成 LLM-agent ノードの decomposition」であり
   「live = 0」ではない。
5. **State schema 肥大化**: 1 chain あたり 3-4 個の intermediate state key
   が増える。`state_keys` 上限は事実上 langgraph TypedDict のみで定まり
   性能影響はほぼなし。schema 名の命名規約を統一 (`<node>_llm_out` /
   `<node>_inserted` / `<node>_summary`) する。

### 完了基準 (Phase E)

| Metric                       | Phase D2  | Phase E goal | 例外説明                  |
|------------------------------|-----------|--------------|--------------------------|
| live py_primitive (count)    | 61        | ≤ 8         | host-binding 例外のみ     |
| node data-share (live)       | 57.6%     | ≥ 95%       | exception 8 件で 95%+ 確保 |
| route data-share (live)      | 100%      | 100%        | 維持                     |
| assistant data-share (live)  | 84.3%     | 100%        | 全 assistant topology 化 |

### Migration 順序 (推奨)

1. **新 primitive landing**: `tools.sql.insert_row` 実装 + 単体 tests
   (Phase E0)
2. **小規模パイロット**: `yoro_product_ingest` (5 node) または
   `coverage_gap_bridge` (5 node) — chain template 検証 + e2e_smoke 拡張 (Phase E1)
3. **中規模**: `webmk_proposal` (6) → `etzhayyim_company_ops` (8) →
   `kaisya_member_assistant` (8) (Phase E2)
4. **大規模**: `lawfirm_marketing_ops` (9) → `animeka_autopilot` (8、
   ComfyUI ノード除外で実質 4-5) (Phase E3)
5. **残骸**: `tsukuru_isic_pulse` / `shosha_agent_loop` 系 / single-node
   exception の精査と仕分け (Phase E4)

各 step ごとに audit 値を確認、テスト通過、deps.toml ミルストン記録。
1 step あたり ~1 migration + ~1-2 primitive tests + 1 e2e proof。
total ~10-12 migrations + 1 primitive 追加 + state schema docs。

### Out-of-scope (別 ADR 候補)

- **並列 foreach**: 現行 sequential のみ。`concurrency:N` オプションを
  追加する場合は ordering / state racing semantics を別 ADR で定める
- **Sub-graph composition**: 1 mcp_tool が別 assistant を呼ぶ階層化
  (`agent.invoke`)。Phase E の chain template で済むなら不要、複雑性が
  正当化された時点で別検討
- **Schema-validated LLM output**: Pydantic gate node 自体は Phase E 内で
  chain に追加するが、universal validator primitive は別 ADR で検討

## References

- ADR-2605080000: Distributed Cognitive Actor System (L2 LangGraph 制約)
- ADR-2605072000: LangGraph Agent Loop Pattern (intra-job graph 使用条件)
- ADR-2605080600: LangGraph Server + Granian L3 Runtime (compiler 実行環境)
- ADR-0087: Kotodama MCP Tool Facade (`vertex_mcp_tool_def` registry)
- ADR-0056: BPMN-as-actor (data-as-code precedent)
- ADR-2605082100: LangGraph Checkpointer Storage (補完)
- ADR-2605082200: PyZeebe Handler Thin Dispatcher Contract (補完)
