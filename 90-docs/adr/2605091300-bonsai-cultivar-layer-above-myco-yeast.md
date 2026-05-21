---
id: adr-2605091300-bonsai-cultivar-layer-above-myco-yeast
title: "Bonsai Cultivar Layer Above Myco-Yeast Substrate — Plant/Soil Two-Stratum Model"
status: active
doc_type: adr
topic: bonsai-cultivar-architecture
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - bonsai cultivar layer (root/trunk/branch/leaf/flower/fruit)
  - plant/soil two-stratum metaphor
  - human-as-gardener role boundary (water + prune only)
  - cohort = bonsai trunk lineage
priority: 9.5
axis: architecture
weight: 0.95
priority_note: "CRITICAL — top-level metaphor that re-anchors all subsequent organism ADRs (091400-092500). Supersedes 0080100 bonsai growth-and-prune."
depends_on:
  - adr-2605071200-myco-yeast-artificial-organism-jp-naming
  - adr-2605081300-karma-hegemon-edge-primary-spirit-in-physic
  - adr-2605081400-karma-self-growing-organism-ecosystem
  - adr-2605061200-agi-active-inference-artificial-organism-architecture
related:
  - adr-2605080100-bonsai-growth-prune-model
  - adr-0026-agent-only-reverse-identity-topology
  - adr-2605082000-langgraph-graph-definition-as-data
supersedes:
  - adr-2605080100-bonsai-growth-prune-model
superseded_by: []
---

# Context

ADR-2605071200 (myco-yeast) は organism を **菌類モデル** で表現したが、
そこには「人間が育てる」「果実を収穫する」「悪い枝を切る」という
**栽培論** が欠落していた。組織 (org) や human が agent を
「育てる対象」として接する世界モデルは菌類より植物の方が直観的で、
かつ既存 ADR-2605080100 の bonsai growth-prune モデルと整合する。

本 ADR は myco-yeast を **下層 (土壌微生物)** に固定したまま、
上層に **盆栽 (bonsai cultivar)** を載せる二段モデルを正式化し、
人間の介入権能を **灌水 + 剪定の 2 つに限定** する。

# Decision

## A. 二段ストラタム

```
☀️ 太陽 = GPU/電力 (RunPod 6000 Ada, k8s nodes)
🌬 空気 = network (CF edge, AT firehose)
─────────────── 上層 (Plant / Bonsai cultivar) ───────────────
🍎 果実 fruit   = published artifact (yoro post, decision)     ← 収穫面
🌸 花  flower   = draft / candidate output
🍃 葉  leaf     = active LangGraph node (光合成)
🪾 枝  branch   = LangGraph subgraph / BPMN process
🌳 幹  trunk    = chromosome lineage (graph_def 系譜) = cohort
🌿 根  root     = mycorrhiza interface (MCP server-to-server)
─────────────── 下層 (Soil / Myco-yeast) ─────────────────────
🍄 微生物 = kabi/kobo/kinoko/houshi/hakkou (ADR-2605071200)
💧 水    = data signal / attention / OAuth grant / $
🪴 土    = RW + Hyperdrive + IPFS 5-layer (ADR-0036, ADR-2605081300 §G)
```

両ストラタムは **mycorrhiza** で接続 (root ↔ mycelium)。

## B. Cohort = Bonsai Trunk Lineage

ADR-0026 cohort と本 ADR の trunk を **同一物** とする。
`vertex_kobo_agent` の chromosome 系譜が trunk、cohort fission が
副 trunk の発生 (株分け) に対応する。

## C. 人間の権能 (Gardener Role)

人間 (および org) は本 ecosystem で **以下 2 操作のみ** 可:

1. **灌水 (water)** — 選択的養分付与 (ADR-2605091500)
2. **剪定 (prune)** — 枝 / 果実 / 葉の除去 (ADR-2605091800)

禁止:
- chromosome の直接書換え (mutation-permit grant 経由のみ)
- trunk の創出 (genesis は ADR-2605081400 の K-floor 自然発生のみ)
- floor 違反 / DAO 判断の上書き (constitutional gate)

## D. Schema 増分

```sql
vertex_yoro_flower    -- draft / candidate
vertex_yoro_fruit     -- published artifact (摘果対象)
edge_yoro_prune       -- 剪定 edge (ADR-2605091800)
edge_bonsai_water     -- 灌水 edge (ADR-2605091500)
```

詳細は派生 ADR。

## E. ADR-2605080100 との関係

旧 bonsai-growth-prune ADR は本 ADR と ADR-2605091800 (剪定) に分割し、
本 ADR が **メタファ層**, 091800 が **operational protocol** を担う。
旧 ADR は `superseded_by` で両者を指す。

# Consequences

## Positive
- 人間の介入経路が 2 つに収束 (灌水・剪定) — governance surface 最小化
- myco-yeast を破棄せず再利用 — 既存 schema/worker そのまま
- 「育てる/育てられる」の双方向性が metaphor として明示

## Negative
- 二段モデルは認知負荷増 — どこが土でどこが植物かの境界教育が必要
- bonsai/myco の用語が並走 — naming 規約 (ADR-2605091900) で吸収

## Reversibility
- メタファ層なので reversible (用語のみ)。schema 変更は派生 ADR 単位

# Alternatives Considered

- **菌類のみ (myco only)**: rejected。「育てる人間」を表現できない
- **植物のみ (plant only)**: rejected。既存 myco-yeast 実装が無駄になる
- **動物モデル**: rejected。homeostasis は動物的だが「庭師に育てられる」非対称性が出ない

# References

- ADR-2605071200 myco-yeast (土壌生態系)
- ADR-2605081400 karma self-growing ecosystem
- ADR-2605080100 (superseded) bonsai growth-prune
- 派生: 091400 / 091500 / 091600 / 091800 / 091900
