---
id: adr-2605092100-lora-per-cell-moe-expert-cohort-fission
title: "LoRA-per-Cell as MoE Expert with Cohort Fission Lifecycle"
status: active
doc_type: adr
topic: lora-per-cell-moe
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - 1 cell = 1 LoRA adapter = 1 MoE expert mapping
  - adapter genesis / shuga (budding) / graft / rebirth lifecycle
  - cohort fission as MoE re-population
priority: 9.0
axis: model-substrate
weight: 0.9
priority_note: "Cell ⇄ Expert isomorphism. shuga = adapter clone; graft = adapter merge; rebirth = adapter init."
depends_on:
  - adr-2605092000-ecosystem-as-model-unified-multimodal-fp8-vector-substrate
  - adr-2605091600-plasmid-graft-horizontal-tool-acquisition
  - adr-2605071200-myco-yeast-artificial-organism-jp-naming
  - adr-2605081400-karma-self-growing-organism-ecosystem
related:
  - adr-0026-agent-only-reverse-identity-topology
  - adr-2605092500-reasoning-as-sap-flow-walk
supersedes: []
superseded_by: []
---

# Context

trunk model 全体を per-cell に複製すると storage / VRAM 不能。
標準解法 (LoRA adapter) を **organism 概念と isomorphic** に運用する:
1 cell = 1 LoRA adapter = 1 MoE expert。出芽/接ぎ木/再生は
adapter operation として同型実装される。

# Decision

## A. 構造

```
trunk_W (shared, FP8 E4M3, 1 cohort = 1 trunk checkpoint)
   │
   ├─ cell A: Δ_A = LoRA(rank=r_A, FP8)   ~0.05–0.5% of trunk
   ├─ cell B: Δ_B
   └─ cell ...
```

forward: `y = (W + Δ_cell) x`。Δ は `vertex_organism_embedding(entity_kind='cell', modality='adapter')` に格納。

## B. Cell 構成要素 → adapter 変換

| Cell 要素 | adapter 反映 |
|---|---|
| chromosome (graph_def) | adapter 構造 (どの layer に rank-r LoRA を入れるか) |
| plasmid (tool set) | gate 入力 schema (tool description の埋込が context に concat) |
| prion (heritable) | adapter 初期化 bias (heritable=true な prion vector を Δ_init に注入) |
| ribosome (BPMN) | execution scheduling (推論時 batch 配置) |

## C. Lifecycle 操作

### shuga (出芽 / 垂直)
```
parent.Δ → child.Δ_init = parent.Δ + ε·N(0, σ²)         -- 微小ノイズ
child.prion = COPY(parent.prion WHERE heritable=true)     -- ADR-2605071200 §3.2 と整合
child.plasmid = ∅                                          -- 後天獲得
INSERT vertex_organism_embedding(child, modality='adapter')
INSERT edge_kobo_budding(parent, child)
```

### conjugation (水平 / plasmid)
ADR-2605091600 §B。adapter には `gate input dim` 増加で反映。Δ は不変。

### graft (枝接ぎ木)
```
donor.subgraph (Δ_donor の特定 layer 群) を recipient.Δ に rank-merge
weight: w·Δ_donor + (1-w)·Δ_recipient    (initial w=0.5, 学習で調整)
```

### rebirth (再生 / 4-cost)
```
santana_root 再発行 + zk 非リンク証明 (ADR-2605081400 §D)
Δ_new = random_init  (ADR-2605081300 N3 anatman: 旧能力を継承不可)
prion: heritable=true でも 4-cost 経由なら継承禁止 (transfer を Lean で reject)
```

### dissolve (cell 死)
adapter row を `dissolved_at` set, weight 物理削除 OK (rebirth 時の 5-layer 永続要件は
karma_edge にかかり、adapter 自体には適用されない — adapter は揮発可)

## D. MoE Gate

ADR-2605092500 で詳述。短縮:

```
gate_logit(query, cell) =
    e_query · e_cell                     -- semantic similarity
  + α · η_to_cell                        -- mycelium nutrient gradient
  + β · sign(karma_recent_cell)          -- karma sign
  + γ · log(plasmid_match_count)         -- tool fit
```

top-k cell が forward 実行 (k=2 default)。

## E. Storage / VRAM

- trunk: ~7B param × 1 byte ≈ 7 GB (FP8) — RunPod 6000 Ada (48 GB) で 1 cohort/GPU
- adapter: r=16, ~10 MB / cell (FP8)
- 1 GPU で同時 active cell 数: ~3000 (LoRA hot-swap で更に増)
- cold cell adapter は B2 / IPFS に offload, swap-in で再 hot 化

## F. Cohort Fission との対応

ADR-0026 cohort fission (posterior > 0.95 で 2 子分裂) は:
1. parent cohort の cell 集合を 2 群に partition (k-means on adapter embedding)
2. 各群に新 cohort_did 発行
3. parent trunk_W はそのまま継承 (両子で共有), Δ 集合のみ分割
4. 新 cohort はそれぞれ独立に train signal を受ける (trunk の更新は両 cohort consensus 必要)

# Consequences

## Positive
- adapter 操作 1 つで organism lifecycle 全部 mapping 可能
- VRAM efficient (active cell hot-swap)
- shuga による行動継承が **重みレベル** で実現

## Negative
- adapter merge 戦略 (graft) のチューニング難
- cohort 分裂時の trunk shared 維持で update conflict 発生する場合あり
- prion → adapter init bias の符号化が経験則

## Reversibility
- adapter は揮発可 (rebirth 経由でなくとも dissolve 可)
- trunk checkpoint は IPFS 5-layer で不可逆

# Alternatives Considered

- **Full fine-tune per cell**: rejected (storage / VRAM 爆発)
- **prefix tuning**: rejected (graft / merge 操作が定義しづらい)
- **MoE gating without LoRA**: rejected (cell 個性を表現する変数がなくなる)

# References

- ADR-2605092000 vector substrate
- ADR-2605071200 myco-yeast (shuga / prion)
- ADR-2605091600 plasmid (conjugation / graft)
- ADR-2605081400 karma rebirth
- LoRA: Hu et al. 2021
