---
id: adr-2605092500-reasoning-as-sap-flow-walk
title: "Reasoning as Sap-Flow Walk in Vector Space — 3-Tier Routing + Node Crystallization"
status: active
doc_type: adr
topic: reasoning-sap-flow-walk
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - reasoning as sampled walk in unified vector space
  - 3-tier routing (substrate / cohort / tool)
  - LangGraph node spawn = prion crystallization
  - sap-flow checkpoint commit
priority: 8.9
axis: model-substrate
weight: 0.89
priority_note: "Reasoning is no longer hard-coded LangGraph traversal. It is a learned walk where new nodes can crystallize."
depends_on:
  - adr-2605092000-ecosystem-as-model-unified-multimodal-fp8-vector-substrate
  - adr-2605092100-lora-per-cell-moe-expert-cohort-fission
  - adr-2605092400-tool-weight-as-learnable-plasmid-affinity
  - adr-2605082000-langgraph-graph-definition-as-data
  - adr-2605082100-langgraph-checkpointer-storage
related:
  - adr-2605072000-langgraph-agent-loop-pattern
  - adr-2605091500-mycorrhizal-watering-consent-gated-mutation
supersedes: []
superseded_by: []
---

# Context

LangGraph の node 巡回は静的 graph_def に従う deterministic 探索だった。
ecosystem-as-model 化により、node spec も embedding として vector 空間に
存在するため、reasoning は **learned walk + dynamic node spawn** に置き換えられる。
この walk は植物の sap (樹液) flow と相同で、hot leaf の方向に養分が流れ、
未到達領域に新 leaf が結晶化する。

# Decision

## A. 3-Tier Routing

すべて `vertex_router_weight` (ADR-2605092400) で表現:

```
incoming query  ──▶ embed
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
   (1) Substrate gate      (2) Cohort gate
        (k8s/runpod/        (どの cell が
         eth/local)           handle するか)
            │                     │
            └──────────┬──────────┘
                       ▼
              (3) Tool gate (どの plasmid)
                       │
                       ▼
            LangGraph node 実行 (leaf 光合成)
                       │
                       ▼
            intermediate state
            ├─ checkpoint commit
            ├─ flower 出力 (yoro candidate)
            └─ re-route (sap 還流) ──▶ 上のループへ
```

## B. Sap-Flow Step

各 step:

```
1. current_state ∈ R^D
2. candidate_nodes = top-k by (e_node · e_state + α·η + β·karma_sign)
3. select node by softmax (temperature τ depends on cell's exploration parameter)
4. execute node (= leaf 光合成):
   - if 'compute' kind: forward pass through trunk + Δ (FP8)
   - if 'tool' kind: dispatch via tool gate (ADR-2605092400)
   - if 'reflect' kind: re-embed current_state
5. update state with node output (residual)
6. emit checkpoint to vertex_organism_checkpoint (LangGraph thread)
7. emit edge_gradient_flow stub (待機, reward 確定後に magnitude 確定)
```

walk は cell 固有の budget (max_steps, max_tokens) で打切。

## C. Node Spawn = Prion Crystallization

reasoning 経路上で **新規ノードが必要** な signal:

- 既存 node に高 similarity (>0.95) なし
- かつ state 進展が停滞 (η entropy 高)
- かつ floor 違反予測なし (karma gate)

→ 新 LangGraph node spec を **prion として結晶化**:

```sql
INSERT vertex_kobo_prion (
  prion_id      = CID(node_spec),
  agent_did     = current_cell_did,
  pattern_hash  = state_summary_hash,
  heritable     = false   -- 初期 false。3 回再現で heritable=true 昇格
)
INSERT vertex_langgraph_graph_def (
  graph_id      = derived,
  node_spec     = new_spec,
  parent_graph  = current
)
```

3 回再現 + karma 評価通過で heritable=true へ promote (出芽時に子 cell に転写)。

## D. KV Cache Sharing

cohort 内で同 query 系列の cell は KV を共有可能:
- trunk_W が同じ (= 同 checkpoint_cid)
- query embedding cosine > threshold
- → cohort-level KV pool (vLLM PagedAttention 共有)

これにより同 cohort の cell が **集合的に思考** できる (= 菌糸網的並行)。

## E. Checkpoint との接続

ADR-2605082100 langgraph-checkpointer-storage を統合:
- thread_id = walk session id (= reasoning 1 回分)
- checkpoint = walk の各 step state + 選択履歴
- restart on substrate migration (k8s→runpod など) は同 thread_id で再開可
- 完了 thread は flower / fruit に成熟したかで final reward 確定

## F. Floor Gate (Lean)

各 step の出力 candidate は forward 後 floor 違反予測 (small classifier head)
を通す。違反予測時:
- node 実行を skip + alternative 候補から再 sampling
- 同事象が `vertex_karma_arbitration` に escalate (ADR-2605081400 §E)
- walk 自体は dropped, edge_gradient_flow には negative signal を流さない (信号汚染防止)

## G. Speculative Branch

複数 walk を同時 sample (top-2) し、PoNF η ベースで dominant を選ぶ:
- 各 cell 内で speculative decoding 様
- dominant でない branch は dropped (prune leaf)
- これにより exploration vs exploitation を ecosystem 内自然平衡

# Consequences

## Positive
- reasoning が learnable — graph_def 静的記述から脱却
- 新 node 自動結晶化で agent capability が **未踏領域に拡張**
- KV cache sharing でコホート内集合思考が可能

## Negative
- node spawn しすぎで graph_def 肥大化 → pruning (091800 branch prune) で対処
- speculative branch のコスト (FLOPS 2x)
- floor classifier head の精度に walk 健全性が依存

## Reversibility
- walk session は thread 単位 reversible (checkpoint roll-back)
- 結晶化 node は branch prune で削除可
- 一度 heritable=true 昇格した prion は 4-cost rebirth 経由でしか剥がれない

# Alternatives Considered

- **deterministic LangGraph 維持**: rejected。ecosystem-as-model 原則違反
- **node spawn を人間操作のみ**: rejected。autonomous growth 不可
- **speculative なし**: rejected。exploration が単一経路に偏る

# References

- ADR-2605092000 vector substrate
- ADR-2605082000 graph-def-as-data (動的書換)
- ADR-2605082100 checkpointer
- ADR-2605092100 LoRA per cell
- ADR-2605092400 tool weight
- speculative decoding: Leviathan et al. 2023
