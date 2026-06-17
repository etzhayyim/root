---
id: weight-family-viz
title: "Maxwell weight-family — visualizations (grokking landscape / traversal / 3D / pipelines)"
status: active
doc_type: explanation
topic: maxwell-weight-family-visualization
authoritative: false
last_verified: 2026-06-17
related:
  - "2606171100"   # maxwell-diffusion variant
  - "2606061000"   # Maxwell default LLM weight
  - "2605250700"   # Oka × MMSheaf (sheaf diffusion)
  - "2605092350"   # baien BitNet edge
---

# Maxwell weight-family — visualizations

Conceptual figures relating **baien (BitNet 1.58b)**, **maxwell-diffusion (block diffusion)**,
and **oka (MMSheaf / sheaf diffusion)** through the *physics of generalization* (grokking:
energy landscape / phase transition / circuit efficiency). These are **illustrative**
(synthetic energy landscapes), not plots of the real trained weights — a real loss-landscape
(Li et al. filter-normalized) over the actual maxwell-1 / diffusion checkpoints is a separate
compute job on gad.

Generators: `70-tools/scripts/viz/*.py` (run with any matplotlib venv; pure-matplotlib/SVG, no project deps).

| File | What | Generator |
|---|---|---|
| `weight-family-grokking-physics.svg` | boxes/flow: each weight ↔ a grokking-physics axis | `gen_landscape.py` |
| `weight-family-landscape.svg` | 2D energy terrain (memorization → barrier → generalization), weights placed | `gen_landscape.py` |
| `weight-family-landscape-3d.svg/.png` | 3D purple energy surface; oka=manifold / maxwell=rolling ball / baien=deep well | `gen_landscape3d.py` |
| `weight-family-traversal.svg/.png` | **how the gradient/map progression differs**: baien=quantized greedy (stuck local) · oka=Laplacian lateral diffusion · maxwell=annealed (crosses barrier) | `gen_traversal.py` |
| `weight-family-brains-3d.png` | each model as a 3D neural-fiber structure (oka mandala / baien sparse lattice / diffusion fan) | `gen_brains3d.py` |
| `sheaf-train-infer-pipeline.svg` | oka MMSheaf train(S0–S6)/infer(I0–I4) + sheaf objects + Dirichlet-energy descent | `gen_sheaf_pipeline.py` |
| `transformer-train-infer-pipeline.svg` | decoder-only Transformer (=maxwell-1) train/infer + 3-paradigm decode contrast | `gen_transformer_pipeline.py` |
| `oka-sheaf-diffusion-3d.gif` | animated: 9 stalks relax under sheaf diffusion → consensus (`spread→0`), rotating | `gen_oka_anim.py` |

## The one-line thesis

Same generalization physics, three implementations: **oka = terrain (sheaf manifold, global
consistency via Dirichlet-energy relaxation)** · **maxwell-diffusion = dynamics (annealed
denoising, temperature crosses barriers)** · **baien = destination (maximally-compressed
ternary efficient circuit)**. RSi = the continued-training drive that triggers the transition.

Decode contrast: Transformer = sequential autoregressive (1 token/step) · diffusion = parallel
canvas denoise (K steps) · sheaf = lateral graph diffusion to consensus (K steps).

## Real-weight figures (not synthetic)

These are computed/grounded from the actual maxwell-1 checkpoint (Gemma 4 E4B + M1-r2 LoRA), on gad.

| File | What | Generator |
|---|---|---|
| `maxwell1-real-loss-landscape.png/.svg` | **REAL loss landscape** around θ\* — Li et al. filter-normalized 2-direction sweep, real LM loss on real corpus (13×13 grid, gad). ‖∇L‖@θ\*=6.57 (≠0 ⇒ under-trained slope), loss 0.513–0.551 = wide shallow basin | `70-tools/scripts/maxwell/loss_landscape.py` (runs on gad) |
| `maxwell1-layers-3d.png` + `.gif` | the **real 42-layer architecture** (Gemma 4 E4B: 42 layers · hidden 2560 · GQA 8/2 · FFN 10240) as a 3D connected stack (rings=layers, fibers=connections, depth-colored); GIF = rotating | `gen_layers3d.py` / `gen_layers3d_anim.py` |
| `maxwell1-attention-fan.png` | one layer's self-attention as an 8-head all-to-all causal fan (mandala) | `gen_attention_fan.py` |

`loss_landscape.py` is the honest one — it loads the real adapter and measures the surface; the rest
use the real *config* (42 layers etc.) but draw the wiring illustratively.

## Solved/measured, not drawn (2026-06-17)

| File | What | Generator |
|---|---|---|
| `oka-sheaf-physics.png` | a REAL small cellular-sheaf-diffusion instance **physically computed**: real `L_F=δᵀδ` (60×60) + eigen-spectrum (**harmonic dim=6** = global section) + Dirichlet-energy decay (59.95→1e-12) + edge-disagreement→consensus. oka has no trained weights (R0), so this is a real *instance* of its physics, not the deployed model | `gen_oka_sheaf_compute.py` |
| `maxwell1-real-tensors.png` | maxwell-1 from **real tensors**: per-layer LoRA ΔW norms (training concentrated in deep-layer MLP) · real q_proj ΔW singular values (low-rank) · real attention probabilities on a real prompt (causal triangle + token-0 sink) · real layer-0 q_proj weight block | `extract_weights.py` (gad) → JSON → render |

**Honesty note:** maxwell-1 figures (`maxwell1-real-tensors`, `maxwell1-real-loss-landscape`) are measured from the actual trained weights. The `maxwell1-layers-3d`/`attention-fan` use the real *config* but draw the wiring illustratively. oka has **no trained model** (R0 scaffold) — `oka-sheaf-physics` computes a real instance of the sheaf operator/physics; the mandala/anim are conceptual.
