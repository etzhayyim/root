---
id: adr-2605232500-baien-mx-move1-image-graft-self-training
title: "Baien multimodal Move 1 — image graft self-training kickoff on EVO-X2 ROCm"
status: proposed
doc_type: adr
topic: baien-multimodal
authoritative: true
last_verified: 2026-05-23
authoritative_for:
  - baien Move 1 image graft architecture (frozen image encoder + 1.58-bit projector + frozen baien trunk)
  - Move 1 → 2 → 3 gating criteria
  - EVO-X2 ROCm training contract for Move 1
  - data source decision (baien-graft pipeline + Pixal3D over external HF VLM datasets)
  - chat-template extension for image tokens
depends_on:
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
  - adr-2605101000-baien-mx-multimodal-expansion-from-rw
  - adr-2605202115-baien-graft-3d-augmented-dataset
  - adr-2605202345-evo-x2-gpu-pod-fleet-integration
  - adr-2605231300-baien-distill-react-loop
  - adr-2605231600-baien-context-extension
related:
  - 70-tools/baien-mx-train/                (skeleton — new with this ADR)
  - 70-tools/baien-graft-pipeline/          (data generation)
  - 70-tools/etzhayyim-cli/bench.go         (`e7m bench mx-train` subcommand)
  - 40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry.ts (Move 1 graft registration target)
supersedes: []
superseded_by: []
---

# Goal

Bring baien from **text-only inference** today (per the verified
upstream Microsoft `bitnet-b1.58-2B-4T-bf16` checkpoint) to **vision
+ text inference** by self-training a **single trainable layer** (a
1.58-bit projector) on data the etzhayyim fleet can already produce
(baien-graft / Pixal3D, per ADR-2605202115).

This ADR pins the **kickoff configuration** for the first
self-trained multimodal baien variant. Subsequent moves (Move 2:
cross-modal fusion block; Move 3: per-modality branches) are gated
on Move 1 demonstrating that the bootstrap path works.

# Relationship to prior multimodal ADRs

| Prior ADR | What it covers | What this ADR adds |
|---|---|---|
| ADR-2605101000 (baien-MX) | full surgical multimodal architecture: per-modality 1.58-bit branches + cross-modal fusion block. Supersedes "freeze SigLIP, train projector only" path. | Re-introduces the frozen-encoder + projector path **explicitly as Move 1 bootstrap**. ADR-2605101000 stays authoritative for Move 2/3 (the "supersedes" applies to that path being the *end state*, not to whether we ever run a Move 1 bootstrap). |
| ADR-2605202115 (baien-graft) | image → 3D → 4-view → caption training data pipeline. Move 1 image graft is the explicit target. | Consumes the data; specifies the training stack on top of it. |
| ADR-2605202345 (EVO-X2) | Hardware: Ryzen AI Max+ 395, Radeon 8060S, 128 GB unified, ROCm 7.2 in ComfyUI's python_embeded. | Uses EVO-X2 as the **execution host** for Move 1 self-training. The original ADR-2605101000 said "H100 NVL pod" — this ADR pins EVO-X2 instead, removing the H100 dependency. |
| ADR-2605231300 (baien-distill) | LangGraph SFT loop for text-only baien | Move 1 reuses the `commit_node` two-phase ship pattern (JSONL manifest → TS codegen) to register the multimodal variant in `MODEL_REGISTRY`. |

# Decision

Implement the **LLaVA-style Move 1** with three concrete pins:

1. **Image encoder = `google/siglip-base-patch16-224`** (frozen).
   86 M parameters, output `(B, 196, 768)`. Apache-2.0. Already in
   the `transformers` ecosystem.
   *Why SigLIP over DINOv3 (which EVO-X2 already has via Pixal3D)*:
   SigLIP is contrastively-aligned text-image, which makes the
   projector's job easier than starting from a self-supervised-only
   embedding. DINOv3 can be swapped in as `image_encoder: dinov3` in
   the trainer config without architectural changes.

2. **Projector = 2-layer BitLinear** (1.58-bit ternary, matching the
   baien trunk's W1.58A8 quantization):
   ```
   nn.Sequential(
       BitLinear(768, 2560),       # SigLIP-out → baien hidden_size
       nn.GELU(),
       BitLinear(2560, 2560),
       Reshape(B, 196 → 16, 2560)  # downsample to 16 image tokens
   )
   ```
   ~8.5 M ternary params ≈ **1.6 MB on disk**, shippable to edge.

3. **baien trunk = frozen `microsoft/bitnet-b1.58-2B-4T-bf16`** with
   chat template extended to admit a special `<image>` token whose
   embedding is replaced at runtime by the projector output.

Total trainable parameters per Move 1 iter: **~8.5 M** (= ratio
≈ 0.4% of the 2 B trunk). LoRA-equivalent compute footprint.

# Architecture (Move 1)

```
   PIL image (any res)
        │
        ▼
  ┌────────────────────────────────────────────┐
  │ SigLIP-base-patch16-224  (FROZEN, Apache-2)│
  │ output: (B, 196, 768)                      │
  └──────────────┬─────────────────────────────┘
                 │
                 ▼
  ┌────────────────────────────────────────────┐
  │ 1.58-bit Projector  (TRAINABLE, 8.5 M ter) │
  │ BitLinear 768→2560 → GELU → BitLinear      │
  │ → 2560→2560 → reshape to (B, 16, 2560)     │
  └──────────────┬─────────────────────────────┘
                 │  (16 "image tokens", ready for trunk)
                 ▼
text prompt ─────┼───► chat-template formatter substitutes
                 │       <image> placeholder with the 16 tokens
                 ▼
  ┌────────────────────────────────────────────┐
  │ baien trunk (FROZEN, BitNet b1.58 2B-4T)  │
  │ 30 layers, 20 heads (GQA 5 KV), head 128   │
  │ ctx 4096 (4 of which are image tokens     │
  │ on Move 1; longer ctx via ADR-2605231600)  │
  └──────────────┬─────────────────────────────┘
                 │
                 ▼
              response text
```

Move 2 adds a 1.58-bit cross-modal fusion block at trunk layer L/2.
Move 3 unfreezes per-modality input branches. Both gated below.

# Data source

**Reuse the baien-graft pipeline** (`70-tools/baien-graft-pipeline/`):

| Stage | Output | Per-sample wall (EVO-X2 ROCm) |
|---|---|---|
| ComfyUI Hunyuan3D-2 *or* TencentARC Pixal3D-T | `.glb` mesh (+ for Pixal3D: 8 frames × 6 render modes + SLAT) | 66 s / 120 s |
| moderngl 4-view render (Mac) — skipped if Pixal3D used | 4 PNG per sample | ~1 s |
| Florence-2 caption (Mac MPS) | multi-view caption + main-object noun | ~10 s |
| sample.json assembly | `(image, mesh_cid, 4 renders, captions)` | ~0.1 s |

**Each baien-graft sample yields 4 Move 1 training rows** (one per
view), so 1 k baien-graft samples → ~4 k training rows. The Pixal3D
backend gives 8 × 6 = 48 view variants per sample (drop to 4-8 for
SFT, keep the rest for Move 2 contrastive eval).

**No external HF VLM dataset is wired in Move 1** (LAION / CC3M /
COCO captions are all CC-BY or unknown — Charter Rider §2 review
gate would block them by default). baien-graft data is first-party
and the licensing chain is clean (`Apache-2.0` Florence-2 +
Hunyuan-Community / Tencent-license generator, declared in
`sample.json`).

# Numerical analysis

## Trainable parameter budget

```
BitLinear(768, 2560) = 768 × 2560 ternary weights = 1,966,080 params
+ activations 8-bit                                  (free per ADR-2605092350)
BitLinear(2560, 2560) = 2560 × 2560 ternary        = 6,553,600 params
biases (bf16)                                       =     5,120 params
─────────────────────────────────────────────────────────
total trainable                                     ≈ 8,524,800 params
on-disk size (i2_s packed)                          ≈ 1.6 MB
```

That's **0.42 % of the 2 B trunk** — strictly LoRA-sized in
deployment footprint.

## Training-time budget

```
forward pass per image       ≈ baien trunk pass + SigLIP pass
                              = 30 layers × bf16 matmul (frozen) + SigLIP86M
                              ≈ 0.6 s on EVO-X2 ROCm gfx1151 (bf16)
backward pass per image      ≈ only projector grads + activations stored
                              = ~30 % of forward cost
                              ≈ 0.2 s
gradient_accumulation 4      → effective batch 4
total per step               ≈ 4 × (0.6 + 0.2) = 3.2 s
```

| Phase | Examples | Epochs | Steps (per_dev_batch=1, grad_accum=4) | Wall (3.2 s/step) |
|---|---|---|---|---|
| **A smoke** | 100 | 1 | 25 | **80 s** |
| **B bootstrap** | 1 000 | 3 | 750 | **~40 min** |
| **C scale** | 10 000 | 3 | 7 500 | **~6.7 h** |
| D (later) | 50 000 | 3 | 37 500 | ~33 h |

All times are baien-trunk-frozen, projector-only updates. Even Phase
D is overnight-feasible on EVO-X2. Phase A serves as the wiring
smoke; Phase B is the first quality checkpoint.

## Data generation budget (baien-graft, parallel with training)

Per ADR-2605202115 Phase 2 measurement: **~81 s / sample** end-to-end
on EVO-X2 (Hunyuan3D-2). To feed Phase B (1 000 samples) we need
~22.5 h of `bgp-submit` runtime; for Phase C (10 000 samples) ~9
days at 1× concurrency. **Solution**: kick off data-gen ASAP and
batch-train as data accumulates (the projector trainer accepts
incremental row additions per epoch).

## EVO-X2 RAM footprint at peak (Move 1 training)

```
SigLIP-base (frozen, bf16)         ≈   170 MB
baien trunk (frozen, bf16)         ≈ 5 200 MB
projector (trainable, bf16 master + ternary copy)
                                   ≈    35 MB
activations (batch=1, ctx 256+16)  ≈   400 MB
optimizer (AdamW, projector only)
                                   ≈    70 MB
─────────────────────────────────────
total RAM (peak)                   ≈ 5 900 MB
```

Fits trivially in EVO-X2's 96 GB system RAM + 32 GB iGPU VRAM. Even
running Move 1 training **alongside** an `e7m bench core4` ROCm job
(also ~6 GB) leaves ~84 GB free.

# Chat template extension

baien tokenizer is LLaMA-3 (vocab 128,256). The plan:

1. Add a single new special token `<image>` with id 128256
   (= existing vocab_size) via `tokenizer.add_special_tokens({"additional_special_tokens": ["<image>"]})`.
2. **Resize trunk `embed_tokens` and `lm_head`** to admit the new id.
   Since `tie_word_embeddings=true` in baien's config, one resize
   covers both. The new row is **randomly initialized** but its
   embedding is **never used** at inference — at runtime the
   projector output is substituted for that position by a
   forward-hook (`baien_mx.runtime.image_token_injector`).
3. Chat template becomes:
   ```
   <|user|>
   <image>
   {text}
   <|assistant|>
   ```
   where the `<image>` token at trainer time is expanded to the 16
   projector tokens by the data collator.
4. Loss is computed only on the assistant turn, with cross-entropy
   masked to ignore the 16 image positions.

# Training-stack pin

| Layer | Pin | Why |
|---|---|---|
| python | EVO-X2 ComfyUI `python_embeded` (3.12) | ROCm 7.2 / gfx1151 already verified (`scripts/probe_rocm.py`, ADR-2605231300 §5) |
| torch | 2.9.1+rocm7.2.1 | shipped with ComfyUI venv; HIP 7.2 verified |
| transformers | ≥ 5.8 (whichever ComfyUI venv has; current 5.8.0) | BitNet model_type supported |
| peft | 0.19+ | for hooking the projector as a "PEFT adapter" optionally, though Move 1 uses plain nn.Module |
| trl | 1.4+ | SFTTrainer with `data_collator=Move1ImageCollator` |
| image encoder | `google/siglip-base-patch16-224` (Apache-2.0) | as decided in §Decision |
| precision | bf16 throughout (frozen weights + projector master) | matches baien bf16 master and SigLIP's native dtype |
| optimizer | AdamW, lr=5e-4, cosine warmup 50 steps | conservative; only 8.5 M trainable so LR can be 10× higher than full-model fine-tune |
| max ctx (training) | 256 text + 16 image = **272 tokens** | well within baien's 4 k window, no Stage 1 rope_extend needed |

# Eval

Move 1 success is measured by **two scorers**:

1. **`visual_microbench.py`** (new) — 15 verifiable image prompts
   (analogous to `microbench.py`): 5 "what is in this image" (single
   noun) + 5 "what color is X" + 5 "yes/no spatial reasoning". Each
   has a rule-based scorer. Target: ≥ 60 % pass-rate (random ≈ 20 %
   for noun, 50 % for yes/no, 25 % for color).
2. **Text microbench regression check** — re-run the existing
   `microbench.py` 15 prompt suite on the Move 1 model with no image.
   Target: pass-rate Δ ≥ -3 pp (we must not break text capability by
   adding the image path).

Move 1 → Move 2 gate:
- ≥ 60 % visual_microbench pass-rate, AND
- ≤ -3 pp text microbench regression, AND
- training loss curve plateaus rather than diverges, AND
- per-image inference latency ≤ 4× the text-only baien latency
  (rough proxy for "edge deployable").

# Storage and registration

Follow the two-phase pattern from ADR-2605231300 §commit_node:

1. Trainer writes `vertex_training_checkpoint.json` row with
   `kind = "baien-mx-move1-projector"` (per ADR-2605070700) per iter.
2. On commit, append a line to
   `90-docs/baien/multimodal-models.jsonl` recording:
   `model_id, base_model, image_encoder, projector_path, training_data_hash, eval_scores, ts`.
3. Reviewer runs the codegen
   `70-tools/scripts/llm-registry/gen-multimodal-entries.mjs` (new,
   sibling of `gen-distilled-entries.mjs`) which emits a TS module
   `llm-model-registry-multimodal.ts` for inclusion in
   `MODEL_REGISTRY` after explicit flip of `available: true`.

# CLI surface

```bash
# train Move 1 (uses ComfyUI python_embeded ROCm by default)
e7m bench mx-train --phase A          # 100-sample smoke, ~80 s
e7m bench mx-train --phase B          # 1k bootstrap, ~40 min
e7m bench mx-train --phase C          # 10k production, ~6-7 h

# eval an existing checkpoint
e7m bench mx-eval --adapter baien-distill-out/mx-move1-iter-XX/projector

# ad-hoc inference (extends e7m baien prompt with --image)
e7m baien prompt --text "What is in this image?" \
                 --image path/to/cat.jpg --rocm
```

The trainer entry script lives in `70-tools/baien-mx-train/`; the
`e7m bench mx-train` subcommand wraps it via SSH dispatch (same
pattern as `e7m bench distill`).

# Move 2 / 3 outlook

If Move 1 lands (per gate above), the next ADRs follow:

| Move | What | Trainable params | Expected wall |
|---|---|---|---|
| 2 | Add 1.58-bit cross-modal fusion block at trunk layer 15 | +12 M | 1-2 days (full Move 2 retrain) |
| 3 | Unfreeze input branches + add audio + 3D blob branches per ADR-2605101000 | +30 M | 1-2 weeks (full Move 3) |
| 4 | Full per-modality LoRA on first 4 trunk layers | +20 M | additive |

# Risks

| Risk | Mitigation |
|---|---|
| BitNet trunk's ternary representation may not absorb the projector signal cleanly | Phase A smoke surfaces this in 80 s; if loss diverges, fall back to bf16 trunk and re-quantize to ternary only at deployment (Microsoft's `bitnet-b1.58-2B-4T-bf16` is the master) |
| SigLIP visual features may not be the best basis for ternary downstream | Swap to DINOv3 (already on EVO-X2 via Pixal3D) without architecture change |
| Data-gen wall (~22.5 h for Phase B) blocks training | Run baien-graft in parallel with Phase A smoke; pre-stage Phase B data overnight; Pixal3D's 48 views/sample reduces baien-graft runs needed by 12× for the same row count |
| Chat-template / `<image>` token semantics not honored by frozen trunk | Tested empirically in Phase A; fall back to interleaved-token strategy (concat image tokens at start of sequence with no special token) if the marker hurts |
| **License pollution** — published Move 1 weights inherit SigLIP (Apache-2.0) + Florence-2 (Apache-2.0) + Hunyuan-Community OR Tencent-Pixal3D-T (per-card) | Charter Rider §2 review per data-gen backend; Apache-2.0 stack is clean; Tencent variants need per-publish review |

# Open issues (not blocking)

- The chat-template `<image>` token id collides with vocab_size + 1
  if multiple special tokens are added later. Tokens table ADR
  reserved for batch-wide special-token planning.
- We do not implement **image-to-image** (image in / image out) in
  Move 1-3. Add Move 5+ ADR if/when the use case shows up.
- bitnet.cpp / WebGPU runtime support for image input is unverified;
  the projector is small enough to inline as a WebGPU shader but
  this is runtime-team work, not in scope here.

# Acceptance criteria (`proposed → accepted`)

1. `70-tools/baien-mx-train/` exists with `state.py`, `projector.py`,
   `train.py`, `eval.py`, and an `__main__.py` CLI entry.
2. `e7m bench mx-train --phase A --dry-run` walks the trainer setup
   without an actual SigLIP load (skeleton verification).
3. Phase A smoke (100 samples, 1 epoch) completes ≤ 5 min on EVO-X2
   ROCm and writes a `vertex_training_checkpoint.json` row.
4. ADR amendment when Move 1 → Move 2 gate is hit (or when Move 1
   plateaus and we decide to skip Move 1 and try Move 2-first).

# References

- ADR-2605092350 baien design (BitNet trunk + LoRA-on-bf16 recipe)
- ADR-2605101000 baien-MX (surgical multimodal — Move 2/3 target)
- ADR-2605202115 baien-graft (data pipeline + Pixal3D)
- ADR-2605202345 EVO-X2 (training host)
- ADR-2605231300 baien-distill (commit_node two-phase ship pattern)
- ADR-2605070700 vertex_training_checkpoint (lineage)
- Microsoft `bitnet-b1.58-2B-4T-bf16` model card and `config.json`
- SigLIP: https://huggingface.co/google/siglip-base-patch16-224
