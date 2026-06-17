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
