---
id: adr-2605101001-baien-mx-multimodal-expansion-from-rw
renumbered_from: "2605101000"
title: "Baien-MX: trunk-surgery multimodal expansion from Kotoba/Datomic-native modalities"
status: proposed
doc_type: adr
topic: edge-multimodal-model-1bit
authoritative: true
last_verified: 2026-05-10
authoritative_for:
  - Baien-MX architecture (per-modality 1.58-bit branches + new cross-modal layers)
  - Training data sourced exclusively from existing Kotoba/Datomic vertex/views
  - Per-modality weight separation in vertex_training_checkpoint
depends_on:
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
  - adr-2605070700-rw-native-model-training-weight-lineage
  - adr-2604262359-kotoba-multimodal-vector-search-topology
related:
  - 30-graph/graph-schema/migrations/20260508000000_vertex_training_lineage.ts
  - 30-graph/graph-schema/migrations/20260427001000_vector_embedding_project_tables.ts
  - 30-graph/graph-schema/migrations/20260502120000_v_training_text.ts
  - 30-graph/graph-schema/migrations/20260508230000_vertex_3d_blob_catalog.ts
  - doc-baien-multimodal-reasoning-roadmap
supersedes: []
superseded_by: []
---

# Goal

Extend Baien from a text-only 1.58-bit trunk into a **proper
multimodal model** by **adding new layers and per-modality weight
branches**, all trained on **modalities that already live in
Kotoba/Datomic**. No external dataset ingest, no new pretraining budget.

This supersedes the conservative LLaVA-style "freeze SigLIP, train
projector only" path described in
`multimodal-reasoning-roadmap.md` Move 1, because the user has
explicitly authorized:

- adding new layers to the trunk,
- using separate weights per modality,
- using the weights and corpora already in RW.

LLaVA-style grafts remain a fallback if the surgery path
under-delivers, but they are no longer the primary recipe.

# Scope

In scope:

- Baien-MX architecture: per-modality 1.58-bit input branches +
  shared BitNet trunk + at least one new 1.58-bit cross-modal
  fusion block inserted mid-trunk.
- Modality coverage = the four modalities natively available in
  Kotoba/Datomic today: text, knowledge triples, multimodal vector
  embeddings (768d and 4096d FP8), and 3D blob latents.
- Per-modality weight separation in `vertex_training_checkpoint`
  (one row per modality projector + one row per shared block).
- Training kind `baien-mx-train` reusing the same H100 NVL pod and
  `runpod_handler` dispatch as Oka.

Out of scope:

- Adding new modalities not yet in RW (image bytes, audio bytes,
  video). Those keep the LLaVA-style graft path from
  ADR 2605092350.
- Re-pretraining the BitNet trunk. We graft, we don't retrain the
  4T tokens.
- Frontier reasoning. Reasoning escalation goes to Oka per
  ADR 2605091400, unchanged.

# Executive Summary

| Layer | Change | Weight separation | Storage |
|---|---|---|---|
| Text input | unchanged (trunk's tokenizer + Embedding) | shared with trunk | existing |
| Triple input (`v_training_triple`) | NEW 2-layer 1.58-bit projector → 16 tokens × D | per-modality | `vertex_training_checkpoint kind=baien-mx-projector-triple` |
| Vector-embedding input (`vertex_vector_embedding_768` / `_4096_fp8`) | NEW 1-layer BitNet linear(768→D) and (4096→D) → 8 / 16 tokens × D | per-modality (one ckpt per source dim) | same |
| 3D blob input (`vertex_3d_blob`) | NEW 2-layer 1.58-bit projector → 32 tokens × D | per-modality | same |
| BitNet 2B trunk middle | **frozen for v0** | shared | unchanged Baien text-only B2 ref |
| Cross-modal fusion block at layer L/2 | **NEW 1.58-bit attention block, allows non-text tokens to attend to text and vice versa with a fresh QKV** | shared | `vertex_training_checkpoint kind=baien-mx-fusion` |
| LM head | unchanged | shared with trunk | existing |
| Optional v1: per-modality LoRA on first 4 trunk layers | LoRA rank ≤ 16 per modality, merged at serve time | per-modality | `kind=baien-mx-trunk-lora-{modality}` |

All new blocks are themselves BitNet 1.58-bit (QAT-trained on the
H100 master, re-quantized to i2_s for serving). The model stays a
"1.58-bit edge" model — we are *adding* 1.58-bit capacity, not
mixing fp16 grafts.

# Decision

## 1. Architecture

```
                     ┌─ text ids ──────────────┐ (frozen trunk embed)
                     │
RW row → multimodal  ├─ triple (s,p,o) ────────┤ NEW projector (1.58-bit)
training-sample      │                          │   per-modality weights
materialized view    ├─ vector_768 ────────────┤ NEW projector (1.58-bit)
                     │                          │
                     ├─ vector_4096_fp8 ───────┤ NEW projector (1.58-bit)
                     │                          │
                     └─ 3d_blob latent ────────┘ NEW projector (1.58-bit)

                                ↓ concat with modality-boundary token
                                ↓
   Layers 0 .. L/2-1   = frozen BitNet b1.58 2B trunk
   Layer  L/2          = NEW cross-modal attention block (shared, 1.58-bit)
   Layers L/2+1 .. L-1 = frozen BitNet b1.58 2B trunk
                                ↓
                         frozen LM head → next-token loss on text portion only
```

Hidden dim D, layer count L are inherited from the BitNet 2B trunk.

The cross-modal attention block is the **single shared learnable
mid-trunk addition** for v0. It exists because freezing the trunk
entirely with only input-side projectors gives the trunk no chance
to integrate non-text information beyond the first attention pass.
One inserted block at L/2 is the minimum architectural change that
buys cross-modal mixing without re-training the trunk.

## 2. Per-modality weight separation

Each non-text modality has its own input projector with its own
weights, saved as a separate row in `vertex_training_checkpoint`:

| Checkpoint kind | Stored | Approx size |
|---|---|---|
| `baien-mx-projector-triple` | 2-layer BitNet 1.58-bit + small embedding tables for entity/predicate vocabulary | ~5 MB i2_s |
| `baien-mx-projector-vec768` | 1-layer BitNet linear(768→D) | ~1 MB i2_s |
| `baien-mx-projector-vec4096fp8` | 1-layer BitNet linear(4096→D), input is dequant from FP8 | ~5 MB i2_s |
| `baien-mx-projector-3dblob` | 2-layer BitNet 1.58-bit | ~3 MB i2_s |
| `baien-mx-fusion` | one BitNet attention block at trunk hidden dim | ~10 MB i2_s |
| (v1) `baien-mx-trunk-lora-{modality}` | rank ≤ 16 LoRA over first 4 trunk layers, per-modality | ~2 MB i2_s |

All projector blobs share the same B2 prefix
`b2://etzhayyim-models/baien-mx/{ver}/`. Total Baien-MX cold-start
artifact size = trunk i2_s (1.2 GiB) + ~25 MB of projector blobs.

The serving side selects which projectors to load based on which
modalities are present in the input — single-modality inference
loads only the needed projector + the trunk + the fusion block.

## 3. Training data — RW-native multimodal sample view

Define a new Kotoba/Datomic materialized view
`v_training_multimodal_sample` that joins:

```sql
v_training_multimodal_sample(
    sample_id              text PRIMARY KEY,
    text                   text NOT NULL,                    -- always present
    triple_subject         text,                             -- optional
    triple_predicate       text,
    triple_object          text,
    vec768                 float[],                          -- optional (vector_embedding_768)
    vec4096_fp8            bytea,                            -- optional (vector_embedding_4096_fp8)
    threed_blob_id         text,                             -- optional (vertex_3d_blob)
    sensitivity_ord        smallint,
    created_at             timestamptz
)
```

Source rows:

- `v_training_text` (4,800+ Baien-visible text samples) — text col.
- `v_training_triple` — triple cols, joined to text by
  `subject = text.actor_did` or by topic match.
- `vertex_vector_embedding_768` and `_4096_fp8` — joined by the
  source vertex id.
- `vertex_3d_blob` — joined by the same vertex id when present.

For text-only rows, the optional cols are NULL — the training step
just doesn't activate the corresponding projector branch. The loss
is masked accordingly (no projector → no gradient through it).

This **enables fully-mixed batches**: in one mini-batch we can have
"text-only", "text+triple", "text+vec768", "text+3d", and any union
of those. This is the single most valuable property — it lets us
train all four projectors plus the fusion block on the data we
already have, no new ingest, no new dataset snapshot.

## 4. Training kind + lineage

Add a new training kind `baien-mx-train` to the runpod_handler
dispatch. Payload extends the existing `baien-multimodal-graft`
shape with a `modalities` list field:

```json
{
  "kind": "baien-mx-train",
  "baseModel": "microsoft/bitnet-b1.58-2B-4T-bf16",
  "datasetSnapshotId": "<v_training_multimodal_sample snapshot>",
  "modalities": ["text", "triple", "vec768", "vec4096fp8", "3dblob"],
  "trunkFrozen": true,
  "fusionLayerIndex": "L/2",
  "loraOverFirst4Layers": false,
  "hyperparams": {...}
}
```

The handler runs the same `_run_finetune` skeleton, but with a
**per-modality optimizer-param-group** so each projector gets its
own learning rate and is saved as a separate
`vertex_training_checkpoint` row. The shared fusion block + the
optional trunk LoRA each become their own checkpoint rows too.

## 5. Quantization-aware training (QAT)

All NEW blocks (projectors + fusion + optional LoRA) are BitNet
1.58-bit modules trained with **QAT from initialization**. We do
NOT train fp16 and quantize post-hoc — that path costs us the
1.58-bit advantage. Implementation: vendor the BitLinear / ternary
QAT module from `microsoft/BitNet`'s training scripts, register it
under `kotodama.modules.bitnet_qat`, and use it for every new
parameter introduced by Baien-MX.

# Comparison to the LLaVA-graft path

|  | LLaVA-style graft (ADR 2605092350) | Baien-MX (this ADR) |
|---|---|---|
| Trunk modification | none | 1 new attention block at L/2 |
| Encoder | external (SigLIP, Whisper) — fp16 | none — RW already has the latents |
| New parameters | projector only, ~3 MB | projectors + fusion ≈ 25 MB |
| Modalities | image, audio, env (encoder-driven) | text, triple, vec768, vec4096fp8, 3dblob (RW-driven) |
| Data dependency | external paired-data ingest | reuse existing RW corpus |
| Training cost | 6–10 H100 hr per modality | 1 run trains all four projectors + fusion ≈ 10–14 H100 hr |
| Edge-friendliness | encoder is fp16 → still need server CPU for it | all branches 1.58-bit → fully edge-portable |

The two paths are complementary, not exclusive. Baien-MX covers the
RW-native modalities; LLaVA-style grafts cover the raw-bytes
modalities (image, audio) when we want them later.

# Rationale

- **Why insert a new block instead of only stacking projectors at
  the front?** Front-only projectors mean the trunk's first
  attention layer is the single point where text and non-text
  tokens can interact, and the trunk's QKV was never trained to
  expect non-text tokens. One fresh attention block at L/2 gives
  the model a *trained-from-scratch* opportunity to mix modalities
  without disturbing the rest of the frozen weights. This is the
  minimum useful architectural change.
- **Why per-modality weights instead of a shared projector?** We
  want the option to ship Baien-MX in several profiles: edge
  text-only loads zero projectors, edge text+triple loads the
  triple projector + the fusion block (~15 MB extra), edge full
  loads everything (~25 MB extra). Shared weights would force
  always-load-all.
- **Why all-1.58-bit new layers?** Mixing fp16 layers into a
  1.58-bit edge model gives them up the latency win. We have a QAT
  recipe upstream — use it.
- **Why frozen trunk for v0?** Two reasons. First, training is much
  cheaper. Second, we keep one source-of-truth trunk shared between
  Baien text-only and Baien-MX, so one upstream patch (e.g. the
  arm64 i2_s decode fix when it lands) covers both.

# Exceptions

- **No v0 modality crosses sensitivity_ord = 0.** Baien-MX trains
  only on `sensitivity_ord = 0` rows (PII Tier 3 + Cohort-First,
  CRITICAL rule). Higher-sensitivity rows go to Oka.
- **No new tokens added to the tokenizer in v0.** Modality-boundary
  signaling is done by reserving 4 unused token IDs from the
  BitNet base vocabulary (`<extra_id_*>` slots). v1 may extend.
- **No multi-image / multi-3d-blob in one sample for v0.** One
  optional instance per modality per sample.

# Status

Design only. Implementation steps land in subsequent commits, in
this order:

1. **Migration** — `30-graph/graph-schema/migrations/<ts>_v_training_multimodal_sample.ts`
   defines the materialized view and a snapshot helper.
2. **BitNet QAT module** — vendor / wrap the ternary BitLinear and
   put it under `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/modules/bitnet_qat.py`
   with explicit unit tests on shape and quant correctness.
3. **Architecture** — `kotodama/modules/baien_mx.py` builds:
   `BaienMXProjectorTriple`, `BaienMXProjectorVec768`,
   `BaienMXProjectorVec4096FP8`, `BaienMXProjector3dBlob`,
   `BaienMXFusionBlock`, and a top-level `BaienMXModel(trunk_path,
   modalities)` that wires them together with the frozen trunk.
4. **Lexicon + handler** — extend
   `runBaienMultimodalGraft` to accept `modalities` (multi-value)
   and add a new `kind="baien-mx-train"` branch in
   `runpod_handler`. Per-modality optimizer-param-group + per-block
   `vertex_training_checkpoint` writes.
5. **Smoke** — extend `baien-bitnet-lora-smoke.py` (or add a sibling
   `baien-mx-smoke.py`) with a CPU smoke that materializes 32 mixed
   rows from the new MV and runs 5 optimizer steps to verify all
   projector branches receive gradient.
6. **H100 sprint** — actual training run on the H100 NVL pod when
   provisioned. Eval gates: (a) text-only loss does not regress vs
   plain Baien, (b) text+triple grounded-QA accuracy beats RAG-only
   baseline by ≥ 5 pts, (c) post-i2_s-quant accuracy drops ≤ 5 pts
   vs the bf16 master.

# References

- ADR 2605092350 (Baien design + bisect log)
- ADR 2605092345 (Oka — sibling FP8 trunk, shares the H100 pod)
- ADR 2605070700 (training lineage SSoT)
- ADR 2604262359 (Kotoba/Datomic multimodal vector substrate)
- `90-docs/baien/multimodal-reasoning-roadmap.md` (the path
  superseded for RW-native modalities, retained for raw-bytes
  modalities)
