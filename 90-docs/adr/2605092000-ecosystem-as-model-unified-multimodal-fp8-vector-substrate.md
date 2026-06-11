---
id: adr-2605092000-ecosystem-as-model-unified-multimodal-fp8-vector-substrate
title: "Ecosystem-as-Model — Unified Multimodal FP8 Vector Substrate"
status: active
doc_type: adr
topic: ecosystem-as-model-vector-substrate
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - unified D-dim multimodal vector space
  - vertex_organism_embedding schema (FP8 storage)
  - vertex_model_checkpoint lineage
  - modality encoder set (text/code/image/audio/bpmn/struct/graph/action)
priority: 9.6
axis: model-substrate
weight: 0.96
priority_note: "CRITICAL — The ecosystem IS the model. Train/inference unified into ecosystem metabolism."
depends_on:
  - adr-2605091300-bonsai-cultivar-layer-above-myco-yeast
  - adr-2605071200-myco-yeast-artificial-organism-jp-naming
  - adr-2605010000
  - adr-2605082000-langgraph-graph-definition-as-data
related:
  - adr-0044-kotoba-udf-language-strategy
  - adr-2605092100-lora-per-cell-moe-expert-cohort-fission
  - adr-2605092300-fp8-train-inference-colocation
supersedes:
  - adr-0096-lda-latent-entity-inference
superseded_by: []
---

# Context

LLM weights / embedding store / routing / tool weights を **別系統** に
持つと、ecosystem (bonsai + myco) と model が二重化し、training signal の
迂回 + drift が発生する。本 ADR は両者を **同一 RW substrate 上の
FP8 vector 空間** に統合し、graph row 自体がモデル状態であるという
原則を確立する。

# Decision

## A. 統一 D 次元空間

- D = 4096 (trunk shared model) / 1024 (per-cell adapter projection)
- dtype: **E4M3** (forward / inference / 永続保存), **E5M2** (gradient / backward)
- storage: 1 byte per dim + per-row FP32 scale, BYTEA in RW
- index: HNSW (Kotoba/Datomic / pgvector); 距離計算は dequant→BF16

## B. Schema (中核)

```sql
vertex_organism_embedding:
  entity_kind     TEXT    -- cell|leaf|branch|fruit|flower|tool|plasmid|prion|karma_edge|human|org|external
  entity_id       TEXT
  modality        TEXT    -- text|code|image|audio|bpmn|struct|graph|action
  vec_fp8         BYTEA   -- D bytes, E4M3
  scale           REAL
  generation      INT
  trained_until   TIMESTAMPTZ
  provenance_cid  TEXT    -- IPFS witness
  PRIMARY KEY (entity_kind, entity_id, modality)

vertex_model_checkpoint:
  checkpoint_cid    TEXT PRIMARY KEY  -- IPFS CIDv1
  parent_cid        TEXT
  fp8_format        TEXT              -- 'e4m3-fwd-e5m2-bwd'|'pure-e4m3-inference'
  param_count       BIGINT
  cohort_did        TEXT
  pruning_rate      REAL              -- 健康指標 (高すぎ = 庭師の手間, 低すぎ = 自律暴走?)
  fruit_accept_rate REAL
  karma_safety      REAL              -- floor violation count (must = 0)
  lean_verified     BOOLEAN
  ipfs_pinned_at    TIMESTAMPTZ[]     -- 5-layer redundancy (ADR-2605081300 §G)
```

## C. Modality Encoders (光受容体)

各 modality 専用 encoder が同一 D に射影:

| Modality | Encoder | FP8 |
|---|---|---|
| text | trunk LLM tokenizer + transformer | TE FP8 E4M3 |
| code | code-llama 系 + AST-aware | E4M3 |
| image | ViT-L/14 FP8 | E4M3 |
| audio | whisper-medium FP8 | E4M3 |
| bpmn | 3-layer GAT (graph attention) | E4M3 |
| struct (atproto record) | struct→serialized text → trunk text path | E4M3 |
| graph (karma edge) | small MLP (src,dst,axis,vul,dir,tier) | E4M3 |
| action (human event) | event tokenizer (click/prune/water) → trunk | E4M3 |

retrieval は modality 横断 (cross-modal cosine)。

## D. 統一原則

1. **All weights are rows.** trunk model checkpoint は RW row + IPFS blob。LoRA adapter (ADR-2605092100) も `vertex_organism_embedding(entity_kind='cell', modality='adapter')` に置く
2. **All training signals are edges.** ADR-2605092200 の `edge_gradient_flow` がすべての勾配源
3. **All routes are softmax over embeddings.** ADR-2605092500 sap-flow walk
4. **All tools are 2-embeddings.** spec embedding + per-cell affinity weight (ADR-2605092400)

## E. ADR-0096 との関係

ADR-0096 LDA 系 latent entity inference は **連続 vector embedding に拡張** する形で吸収。
LDA topic = 低次元 categorical projection の特殊解として残せるが、SSoT は本 ADR。

## F. Soil Layer 接続

- `vertex_organism_embedding` 自体は **土 (RW + IPFS)** に存在
- 検索/書込みは MCP tool (ADR-2605091400) 経由、内部 wire は Kysely + Hyperdrive (ADR-0036)
- 5-layer 永続性は karma constitutional 互換 (ADR-2605081300 §G)

# Consequences

## Positive
- Train/Inference/Routing/Storage が **同じ row 集合** で済む
- 多モーダル横断 retrieval が cohort 内 cell 全体で自然に動く
- code-as-data が **重みレベルでも** 成立 (graph_def = adapter weight)

## Negative
- D=4096 × FP8 でも entity 数が 10^7 に近づくと storage 計画必須 (B2 cold tier)
- HNSW index re-build 頻度設計
- modality encoder 7 種の保守コスト

## Reversibility
- schema 追加なので reversible
- ただし IPFS pin 済み checkpoint は roll-back 不能 (5-layer 永続)

# Alternatives Considered

- **別 vector store (Qdrant/Weaviate) 採用**: rejected。RW + Hyperdrive の SSoT 原則違反
- **BF16 統一**: rejected。RAM/storage 2x、inference 速度低下
- **modality 分離 namespace**: rejected。cross-modal retrieval が複雑化

# References

- ADR-2605010000 RunPod 6000 Ada (FP8 hardware)
- ADR-2605082000 graph-def-as-data
- ADR-2605091300 bonsai cultivar
- 派生: ADR-2605092100..2500
- NV Transformer Engine FP8: Micikevicius et al. 2022
