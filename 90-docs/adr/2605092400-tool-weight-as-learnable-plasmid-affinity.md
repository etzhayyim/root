---
id: adr-2605092400-tool-weight-as-learnable-plasmid-affinity
title: "Tool Weight as Learnable Plasmid Affinity — MCP Tool Selection in Vector Space"
status: active
doc_type: adr
topic: tool-weight-plasmid-affinity
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - 2-embedding tool model (spec embedding + per-cell affinity)
  - vertex_router_weight schema for tool routing
  - tool selection probability formula
  - reward attribution on tool calls
priority: 8.7
axis: model-substrate
weight: 0.87
priority_note: "MCP tool choice becomes part of model weights. Plasmid acquisition seeds new affinity dims."
depends_on:
  - adr-2605092000-ecosystem-as-model-unified-multimodal-fp8-vector-substrate
  - adr-2605091600-plasmid-graft-horizontal-tool-acquisition
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605092200-continuous-metabolic-training
related:
  - adr-0087-kotodama-mcp-tool-facade
supersedes: []
superseded_by: []
---

# Context

agent の "どの tool を呼ぶか" は従来は LangGraph node spec の hard-coded
dispatcher で決めていたが、ecosystem-as-model の前提では **tool selection
自体がモデル重み** であるべき。新規 plasmid (ADR-2605091600) を獲得した
時点では affinity weight = 0 で、利用結果から学習で affinity を上げる。

# Decision

## A. 2-Embedding 構造

各 MCP tool は次の 2 つを持つ:

1. **Spec embedding** (`vertex_organism_embedding(entity_kind='tool')`):
   - description text + signature schema (input/output JSON Schema) を encoder で D 次元に
   - tool 公開時に固定 (新 version で再 embed)
2. **Per-cell affinity** (`vertex_router_weight`):
   - 各 cell × tool で 1 byte FP8 logit + scale
   - online SGD で更新

## B. Schema (再掲)

```sql
vertex_router_weight:
  cell_did       TEXT
  target_kind    TEXT       -- 'cell'|'tool'|'substrate'|'modality'
  target_id      TEXT
  logit_fp8      SMALLINT   -- 1 byte signed
  scale          REAL
  updated_at     TIMESTAMPTZ
  PRIMARY KEY (cell_did, target_kind, target_id)
```

## C. 選択確率

```
P(tool t | cell c, query q) ∝
  exp( s · ( e_c · e_t                       -- semantic affinity
           + λ · w_{c,t}                     -- learned per-cell weight
           + μ · η_{c→t}                     -- nutrient gradient (ADR-2605071200)
           − γ · karma_risk_t                -- tool 自身の karma 履歴
           − δ · cost_t ))                   -- $ / latency / energy
```

- s: 温度 (default 1.0)
- λ, μ, γ, δ: hyperparams (cell 単位で独自学習可)
- karma_risk_t: tool が過去関与した floor violation 件数 / 1y
- cost_t: 1 call あたりの推定 $ + p95 latency 正規化

## D. Reward Attribution

tool call → 結果 fruit が摘まれた / culled / pruned のとき:

```
on edge_gradient_flow(signal_kind='fruit-accept', dst_entity=branch):
  for each tool_call in branch.history:
    Δw_{c, tool_call.tool_id} += η · reward_sign · attribution(tool_call)
```

attribution は LangGraph node 経路上の tool 寄与度を **shapley-lite** で
推定 (full shapley は cost 高 → 1-step ablation で近似)。

## E. Plasmid Acquisition との接続

ADR-2605091600 で新 plasmid 受領した瞬間:
- INSERT vertex_router_weight (cell_did, 'tool', tool_id, logit_fp8 = 0)
- 初期 affinity = 0 → 純粋に spec embedding similarity と η で選ばれる
- 数回の試行で affinity weight が学習され、有用なら +、無用なら − に動く
- `auto-deactivate`: 1 month 0 use かつ logit < threshold で `active=false`

## F. Substrate Routing も同 schema

```
target_kind='substrate'  → k8s|runpod|eth|local
```

cell が同 query に対しどの substrate で実行するかも学習対象。$/latency/privacy で gate。

## G. Modality Routing

```
target_kind='modality'  → text|image|audio|...
```

multimodal query のとき、どの modality encoder を主軸にするかの learned gate。
text query でも graph encoder の similarity が高ければ graph mode に振ることが可。

# Consequences

## Positive
- tool 選択がモデル更新で改善 — hard-coded dispatcher より柔軟
- plasmid 獲得 → 試用 → affinity 確立の自然な学習曲線
- 4 routing target (cell/tool/substrate/modality) を 1 schema で扱える

## Negative
- shapley-lite attribution の精度限界
- cold-start 問題 (新 plasmid は 0 affinity で選ばれにくい) → spec similarity boost で緩和
- karma_risk_t の計測 latency

## Reversibility
- weight 更新は世代追跡可 (updated_at 履歴)
- adapter ごと削除すれば affinity も消える
- 学習結果のレベル: cohort-wide consensus で trunk distill 時に固定

# Alternatives Considered

- **hard-coded dispatcher 維持**: rejected。ecosystem-as-model 原則違反
- **spec embedding のみ**: rejected。cell 個性が出ない
- **per-cohort weight (cell 横断 share)**: rejected。LoRA-per-cell 哲学と矛盾

# References

- ADR-2605092000 vector substrate
- ADR-2605091600 plasmid acquisition
- ADR-2605091400 MCP membrane
- ADR-2605092200 continuous training
- Shapley value approximation: Lundberg & Lee 2017
