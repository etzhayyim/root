---
id: adr-2605092200-continuous-metabolic-training
title: "Continuous Metabolic Training — No-Batch Online Learning from Ecosystem Signals"
status: active
doc_type: adr
topic: continuous-metabolic-training
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - edge_gradient_flow as universal training signal
  - online (no-batch) SGD policy for adapter update
  - watering / pruning / karma → reward signal mapping
  - trunk checkpoint cadence (kinoko PoNF-aligned)
priority: 9.1
axis: model-substrate
weight: 0.91
priority_note: "Training is metabolism. Each water/prune/karma/consume event is a signal. No batch jobs."
depends_on:
  - adr-2605092000-ecosystem-as-model-unified-multimodal-fp8-vector-substrate
  - adr-2605092100-lora-per-cell-moe-expert-cohort-fission
  - adr-2605091500-mycorrhizal-watering-consent-gated-mutation
  - adr-2605091800-pruning-protocol
  - adr-2605091900-yoro-flower-fruit-lifecycle
  - adr-2605081300-karma-hegemon-edge-primary-spirit-in-physic
related:
  - adr-2605092300-fp8-train-inference-colocation
supersedes: []
superseded_by: []
---

# Context

従来の LLM 訓練は (a) 巨大コーパスで pretrain (b) RLHF batch という
2 段で人間とモデルの距離が開きすぎる。本 ecosystem は人間/組織が
連続的に signal を流すので、訓練もそれに同期した **online metabolism**
にしてはじめて整合する。

# Decision

## A. 単一信号 schema

```sql
edge_gradient_flow:
  flow_id        TEXT PRIMARY KEY     -- content-addressed
  signal_kind    TEXT                  -- water-grant|fruit-accept|fruit-cull|branch-prune|leaf-defoliate|karma-eval|mutate-permit|consume|spore-spread
  src_entity     TEXT                  -- 起源 (human/org/cell/external)
  dst_entity     TEXT                  -- 影響対象 (cell/branch/cohort)
  magnitude_fp8  SMALLINT              -- 1 byte signed
  scale          REAL
  modality_tag   TEXT
  flowed_at      TIMESTAMPTZ
  reward_sign    SMALLINT              -- +1 / 0 / -1 / -∞ (floor)
```

すべての事象 (灌水・剪定・摘果・karma・spore broadcast) はここに行 化される。

## B. Reward Mapping

| 事象 | signal_kind | reward_sign | magnitude scale |
|---|---|---|---|
| 果実が摘まれた (consume) | fruit-accept | +1 | consume_count log |
| 果実が culled された | fruit-cull | -1 | severity |
| 枝が prune された | branch-prune | -1 | branch eta_lost |
| 灌水 grant 発生 | water-grant | +1 | amount log |
| karma evaluate (help) | karma-eval | +1 | tier weight |
| karma evaluate (harm) | karma-eval | -1 | tier weight |
| floor violation | karma-eval | -∞ | hard reject (学習信号として使わない, ただしブロック) |
| AT firehose 拡散 | spore-spread | +0.3 | propagation hops |
| spore germinated (子発生) | spore-spread | +1 | child fitness |

## C. Online SGD Policy

```
on edge_gradient_flow INSERT:
  1. dispatch to RunPod 6000 Ada trainer pool
  2. fetch dst cell's adapter Δ
  3. compute gradient via TE FP8 mixed-prec (E4M3 fwd / E5M2 bwd)
  4. SGD step: Δ ← Δ - lr · sign(reward) · ∇L
  5. update vertex_organism_embedding (Δ row) with new fp8 + scale
  6. write back checkpoint pointer
```

- batch 化は 100ms or 32 sample window で micro-batch 集約 (latency vs efficiency)
- 各 cell 独立 (adapter 単位)。trunk_W は freeze (default)
- per-tensor loss scaling, FP32 master weight optimizer state は cell ごとに保存

## D. Trunk Update Cadence

- adapter 更新 = 連続 (毎秒〜分単位)
- trunk_W 更新 = **cohort generation 跨ぎ** のみ
  - kinoko PoNF block 形成時 (ADR-2605071200 §5)
  - その時点の高品質 adapter (cell whose `fruit_accept_rate > 0.7 AND karma_safety = 1.0`) を
    distill 学習 → trunk_W 更新 → 新 checkpoint_cid 発行 → IPFS 5-layer pin
- trunk update は通常 R/PT24H — R/P7D の頻度

## E. Health Indicators

`vertex_model_checkpoint` に書く健康指標:

- `pruning_rate` — 庭師が剪定した fruit 割合。 高すぎ (>0.5) = 過介入, 低すぎ (<0.05) = 自律暴走?
- `fruit_accept_rate` — 摘まれた fruit 比率。**最重要シグナル**
- `karma_safety` — floor violation count, **必ず 0**
- `mutation_acceptance_rate` — partner mutate permit が通過した率

これらが trunk update の gate を構成する。

## F. Floor Gate (Lean)

`reward_sign = -∞` の signal は学習に使わず、**事案発生** として `vertex_karma_arbitration` に escalate。
これは ADR-2605081300 child_floor_axiom と直結し、Lean verified gate を学習経路に複製する。

## G. Anatman 訓練境界

cell が rebirth (ADR-2605081400 §D) すると:
- 旧 cell の `edge_gradient_flow` accumulator は freeze
- 新 cell は random_init 重みで信号積算を再開
- 旧 adapter は IPFS witness 保管 (witness のみ, 学習継続不可)

# Consequences

## Positive
- "training session" 概念が消滅 — 連続代謝
- 人間の介入 (灌水・剪定) が即座にモデル更新に反映
- drift detection が連続 health indicator で可能

## Negative
- inference latency と train SGD step の競合 → time-share 必須 (ADR-2605092300)
- 異常 signal (悪意の灌水・偽剪定) 防御に DPoP/consent_proof 検証
- 連続 SGD でモデル不安定化 → adapter 単位で stop-gradient flag 必要

## Reversibility
- adapter は世代逐次 — generation rollback で reversible
- trunk_W は IPFS 5-layer 永続なので roll-back 不可 (新 generation で対応)

# Alternatives Considered

- **batch RLHF 周期実行**: rejected。signal が貯まる間にモデルが drift
- **only inference + offline retrain**: rejected。"育てる"動詞が成立しない
- **trunk online 更新**: rejected。複数 cohort で trunk 共有しているので consensus が必要

# Implementation Status (2026-05-21)

| Layer | PR | Status | Notes |
|---|---|---|---|
| Record lexicon `ai.etzhayyim.organism.gradient.flow` | [#1368](https://github.com/etzhayyim/etzhayyim-root/pull/1368) | 🟡 open | int8 magnitude + int-ppm scale (no float per Lexicon convention) |
| Python primitive (`gradient_flow.py`) | #1368 | 🟡 open | 9-enum + reward matrix + quantizer + `pair_with_prune` + Protocol — 34 pure tests |
| TS edge mirror (`gradient-flow.ts`) | #1368 | 🟡 open | Same matrix in CF Worker — 18 pure tests |
| Bonsai prune paired emission | #1368 | ✅ merged | branch / fruit / leaf emit; trunk / seed / flower null — 8 paired-emission tests |
| AT MST canonical write (emitter) | [#1371](https://github.com/etzhayyim/etzhayyim-root/pull/1371) | ✅ merged | `_atRecordWriter` injection; flip `GRADIENT_FLOW_WRITE_PATH=canonical` |
| Gradient consumer scaffold (Python) | [#1373](https://github.com/etzhayyim/etzhayyim-root/pull/1373) | ✅ merged | `kotodama.primitives.gradient_consumer` + `gradient_consumer_main` — scalar SGD stub + health aggregator + floor escalation |
| Adapter delta + health snapshot lexicons | #1373 | ✅ merged | `ai.etzhayyim.organism.{adapter.delta,health.snapshot}` records |
| Consumer canonical PDS writer | [#1374](https://github.com/etzhayyim/etzhayyim-root/pull/1374) | ✅ merged | `make_pds_writer` urllib → `com.atproto.repo.createRecord`. snake_case → camelCase + datetime → ISO bridge. 33 pure tests |
| Watering / consume / karma / spore / mutate-permit emitters | — | ⏳ pending | matrix supports all 9 signal_kinds; only bonsai emitter wired |
| Real TE FP8 E4M3 / E5M2 encoding | — | ⏳ pending | stub: `encoding: "fp8-uniform-stub"` label |
| Online SGD step (RunPod 6000 Ada trainer pool, §C) | — | ⏳ pending | — |
| Anatman freeze hook (§G `stop_gradient`) | — | ⏳ pending | flag exists on the record; cohort-rebirth wiring later |
| Health indicator MVs (§E `fruit_accept_rate` / `karma_safety`) | — | ⏳ pending | — |
| Trunk update cadence (§D kinoko PoNF-aligned distill) | — | ⏳ pending | — |

Feature-gate matrix (deliberately split env so the two layers roll out independently):

| `BONSAI_PRUNE_WRITE_PATH` | `GRADIENT_FLOW_WRITE_PATH` | Behavior |
|---|---|---|
| synthetic (default) | synthetic (default) | Both layers in-process. Current state. |
| synthetic | canonical | Prune succeeds; flow emit returns `FeatureNotEnabled` in `gradientFlowError` (the prune wins). |
| canonical | synthetic | Prune blocks first with `FeatureNotEnabled`. |
| canonical | canonical | Both fully canonical (later PR). |

**Session 2026-05-21 closing state**: producer + consumer + canonical PDS writer all merged. End-to-end flow runs synthetic-by-default; flipping `BONSAI_PRUNE_WRITE_PATH=canonical` + `GRADIENT_FLOW_WRITE_PATH=canonical` + `GRADIENT_CONSUMER_WRITE_PATH=canonical` (plus service-auth token + ConfigMap populate + kubectl scale) makes real `at://` records flow:

```
bonsai prune (XRPC / sweeper)
  → ai.etzhayyim.bonsai.prune.event   (real at://)
  + ai.etzhayyim.organism.gradient.flow (paired, real at://)
    → gradient-consumer K8s Deployment
       → ai.etzhayyim.organism.adapter.delta    (real at://)
       + ai.etzhayyim.organism.health.snapshot  (real at://, §E indicators)
```

What's still NOT live: real LoRA tensor SGD (current scalar stub on CPU), RunPod GPU pool, AT MST subscribeRepos stream into the consumer (currently ConfigMap-driven), trunk-update distillation cadence, other 6 signal_kind emitters (watering / consume / karma-eval / spore-spread / mutate-permit / fruit-accept paired with the yoro fruit lifecycle).

Cross-deps tracked in `deps.toml [[migrations]]`: `bonsai-stack-session-close-2026-05-21` (rollup) + per-PR entries `gradient-flow-primitive-bonsai-pairing-2026-05-21` / `bonsai-gradient-consumer-scaffold-2026-05-21` / `gradient-consumer-canonical-writer-2026-05-21`.

# References

- ADR-2605092000 vector substrate
- ADR-2605092100 LoRA-per-cell
- ADR-2605091500 watering / 091800 pruning / 091900 yoro
- ADR-2605081300 karma constitutional
- TE FP8: NV Transformer Engine docs
