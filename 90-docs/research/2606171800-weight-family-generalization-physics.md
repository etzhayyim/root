---
id: research-2606171800-weight-family-generalization-physics
title: "The Physics of Generalization in the etzhayyim Weight Family: three traversal operators on the grokking energy landscape (oka-sheaf / maxwell-diffusion / baien-BitNet)"
status: active
doc_type: explanation
topic: weight-family-generalization-physics
authoritative: false
last_verified: 2026-06-17
authoritative_for: []
related:
  - "2606171100"   # maxwell-diffusion variant
  - "2606061000"   # Maxwell default LLM weight
  - "2606130900"   # Maxwell RSi ecosystem
  - "2605250700"   # Oka × MMSheaf (sheaf diffusion)
  - "2605092350"   # baien BitNet edge
  - "weight-family-viz"   # figure index
---

# The Physics of Generalization in the etzhayyim Weight Family

**Three traversal operators on the grokking energy landscape — oka-sheaf, maxwell-diffusion, baien-BitNet.**

*Research note · etzhayyim / Murakumo · 2026-06-17 · status: working draft (measured + computed results; oka is R0, no deployed weights).*

## Abstract

We frame etzhayyim's three server/edge weight families as **three distinct ways of
traversing the same energy landscape of generalization** — the landscape made famous by
*grokking* (the delayed memorization→generalization phase transition). **baien** (BitNet
1.58-bit) performs **quantized greedy descent** on a discrete ternary lattice; **maxwell-diffusion**
(block-diffusion LM, DiffusionGemma-26B-A4B base) performs **stochastic annealed denoising**
whose temperature crosses energy barriers; **oka** (MMSheaf cellular-sheaf diffusion) performs
**lateral field relaxation** that minimises a *sheaf Dirichlet energy* toward a globally
consistent (harmonic) section. We make this concrete with **real computation**: (i) a genuinely
solved cellular-sheaf-diffusion instance (real sheaf Laplacian `L_F=δᵀδ`, harmonic subspace of
dimension 6, exponential energy decay); and (ii) the **real loss landscape and weight tensors**
of the trained `maxwell-1` checkpoint (Gemma 4 E4B + M1-r2 LoRA) — filter-normalised loss surface,
gradient norm `‖∇L‖=6.57`, LoRA ΔW concentrated in deep-layer MLP, and a causal attention pattern
with the canonical token-0 sink. We close by identifying the **RSi self-evolution loop** with the
"continued-training" drive that triggers the grokking transition, and we are explicit about what is
measured, what is config-grounded, and what is conceptual.

---

## 1. Introduction

The default religious-corp inference weight is **Maxwell** (a Charter-aligned fine-tune of Gemma 4
E4B; ADR-2606061000), with siblings **baien** (edge BitNet 1.58-bit; ADR-2605092350), **oka**
(server FP8 + cellular-sheaf-diffusion multimodal fusion; ADR-2605250700), and the diffusion variant
**maxwell-diffusion** (ADR-2606171100). These are usually described by *tier* (edge / server /
throughput). This note proposes a second, unifying description by *dynamics*: each is a different
**operator that moves a state down an energy landscape**, and the landscape is the one that governs
generalization.

The motivating picture is **grokking**: a network can reach perfect training accuracy yet generalize
poorly, then — under *continued* training — undergo a sharp **phase transition** to generalization.
Physics readings of grokking describe an **energy landscape** with a *wide, shallow, high-entropy
memorization basin* and a *narrow, deep, circuit-efficient generalization well*, separated by a
barrier the generalizing solution is slow to cross [1,2,3]. Our claim: **oka, maxwell-diffusion, and
baien are three different ways of crossing that landscape**, and the **RSi loop** (ADR-2606130900)
is the continued-training drive.

## 2. The energy landscape of generalization

Let `θ` be parameters and `L(θ)` a task loss. The grokking picture treats `L` as an energy with two
relevant features: a broad basin (memorization, high state-space volume / entropy) and a narrow deep
well (generalization, low entropy, *circuit-efficient*). The transition is a barrier crossing under
continued optimization. We will use a single scalar diagnostic throughout — a **Dirichlet-type
energy** whose minimisation defines "agreement" — and instantiate it three ways.

## 3. Three traversal operators

### 3.1 baien — quantized greedy descent (BitNet 1.58-bit)

baien constrains weights to ternary `{-1,0,+1}`. Training uses a straight-through estimator: gradients
are computed in full precision but the *state* snaps to the ternary lattice. The traversal is therefore
a **discrete, axis-quantised, greedy descent** — a staircase that halts at the *nearest* lattice
minimum. Its strength is the **destination**: the ternary network is the maximally compressed,
low-entropy *efficient circuit* — precisely the narrow generalizing solution grokking converges to. Its
weakness is locality: pure greedy quantised descent is easily trapped in the memorization basin.

### 3.2 maxwell-diffusion — stochastic annealed denoising (block diffusion)

The DiffusionGemma base initialises a token *canvas* with **random tokens** and iteratively denoises
it (uniform discrete diffusion, not absorbing-mask; verified in the model's sampler). The reverse
process is a **temperature-annealed stochastic descent**:

```
x_{t+1} = x_t − η ∇E(x_t) + sqrt(2 η T_t) · ξ ,    T_t : high → low
```

High temperature early lets the trajectory **cross the barrier** (exploration); low temperature late
**refines** (exploitation) — the "learning vs exploration" temperature trade-off. This is the operator
that most directly *reaches the global well* by hopping barriers a greedy method cannot. Its SFT
objective (this work, §4.4) is uniform-diffusion canvas-corruption cross-entropy.

### 3.3 oka — sheaf-Laplacian lateral diffusion (MMSheaf)

oka is not a point descending; it is a **field relaxing across a graph**. A cellular sheaf on a graph
`G=(V,E)` assigns a vector space (stalk) `F(v)=ℝ^d` to each node and a **restriction map**
`F_{v⊴e}: F(v)→F(e)` (a `d×d` linear map, *not* a scalar weight) to each incident node–edge pair. With
coboundary `(δx)_e = F_{v⊴e}x_v − F_{u⊴e}x_u`, the **sheaf Laplacian** is `L_F = δᵀδ`, and the **sheaf
Dirichlet energy**

```
E(x) = ½ xᵀ L_F x = ½ Σ_e ‖F_{v⊴e}x_v − F_{u⊴e}x_u‖²
```

measures how far the local (modality) views are from agreeing after transport. Sheaf diffusion
`Ẋ = −L_F X` is the gradient flow that minimises `E`, converging to the **harmonic space** `ker L_F`
— the *globally consistent sections* where all modality stalks agree. Because the transport is a
*matrix* (not a scalar GNN weight), oka can keep modalities distinct while making them consistent;
the harmonic space stays high-dimensional and classes do not collapse (the over-smoothing escape of
Neural Sheaf Diffusion [4]). The 9-modality stalk vocabulary (audio/image/text/3d/tabular/time/geo/
video/doc) is the hub; the restriction maps are the spokes' gluing; the harmonic core is the consensus.

### 3.4 Contrast (decode)

| operator | move | reaches | decode |
|---|---|---|---|
| baien (BitNet) | discrete greedy lattice descent | nearest (local) efficient circuit | autoregressive, 1 token/step |
| maxwell-diffusion | annealed stochastic denoise | global well (crosses barriers) | parallel canvas denoise, K steps |
| oka (sheaf) | lateral Laplacian field relaxation | harmonic consensus (`ker L_F`) | parallel graph diffusion, K steps |

## 4. Real computations

### 4.1 oka sheaf physics — solved, not drawn  (`../baien/oka-sheaf-physics.png`)

We built a genuine cellular-sheaf-diffusion instance: 9 modality stalks + 1 global node, `d=6`, star
+ ring edges, per-node orthogonal restriction maps `O_k` (cycle-consistent → a real global section
exists). Computing `L_F=δᵀδ` (a real `60×60` operator) and integrating `X←X−αL_F X` we **measure**:

- eigen-spectrum with **harmonic dim = 6** (= `d`) — the global-section subspace `ker L_F`;
- **Dirichlet energy** decays `59.95 → 1.7×10⁻¹²` (exponential, slope set by the spectral gap);
- edge-disagreement `‖δX‖ → 0` (consensus).

With *untrained random* maps the harmonic dimension collapses to 0 and the consensus is trivial
(`X→0`); cycle-consistent maps yield the non-trivial `ker L_F` above. This is exactly the role of
training (learn restriction maps that keep the harmonic space high-dimensional). **oka has no deployed
weights** (R0; D3 runtime + D4 SFT open, ADR-2606171100) — this is a real *instance* of oka's
operator/physics, the honest stand-in until trained oka weights exist.

### 4.2 maxwell-1 real loss landscape  (`../baien/maxwell1-real-loss-landscape.png`)

Using the Li et al. **filter-normalised** 2-direction method [5] on the *actual* M1-r2 LoRA adapter,
we evaluate the real LM loss on real corpus batches over a `13×13` grid of
`θ* + α d₁ + β d₂`. Measured: `L(θ*)≈0.28` on the gradient batch, grid loss range **0.513–0.551**
(a *wide, shallow basin* in these two directions), and **`‖∇L‖ at θ* = 6.57`** — far from zero. The
non-zero gradient is an honest signal that the checkpoint (300 steps ≈ 0.59 epoch on 1,016 pairs) is
**under-trained** — still on a slope of a high-volume basin, exactly the memorization-side regime that
continued RSi training would deepen and sharpen.

### 4.3 maxwell-1 real tensors  (`../baien/maxwell1-real-tensors.png`)

From the same adapter we extract real tensors:

- **LoRA ΔW norm per layer**: adaptation **concentrates in the deep-layer MLP** (`down_proj`/`gate_proj`
  rise after ~layer 25); attention projections move little — the fine-tune adjusted feed-forward
  content more than routing.
- **q_proj ΔW singular values**: strongly **low-rank** (1–2 dominant of 16) — the LoRA `r=16` signature.
- **Real attention probabilities** (layer 20, head-mean, real prompt): a clean **causal lower triangle**
  with a bright **token-0 attention sink** — the canonical LLM behaviour, measured.
- **Real layer-0 q_proj weight block** (`2048×2560` → `96²`): zero-mean ± dense projection values.

### 4.4 maxwell-1 architecture and diffusion SFT mechanism

The real config is 42 layers · hidden 2560 · GQA 8/2 heads · FFN 10240 · vocab 262144
(`../baien/maxwell1-layers-3d.png`, `../baien/maxwell1-attention-fan.png` — config-accurate, wiring
illustrative). The diffusion train-leg (`train_diffusion.py`) computes the uniform-diffusion objective
on the real DiffusionGemma forward (canvas logits, no internal loss) and a 3-step CPU smoke shows the
loss/gradient/LoRA-step/save loop executes (loss 1.07→0.04); a 4-bit GPU path is built
(`BNB-ROCM-BUILD.md`) but VRAM-bounded on gfx1151.

## 5. Synthesis

The three weights are **not different goals but different routes to the same generalization minimum**:
**oka = the terrain** (sheaf manifold; global consistency by Dirichlet-energy relaxation), **maxwell-diffusion
= the dynamics** (annealed denoising; temperature crosses barriers), **baien = the destination** (the
maximally-compressed efficient circuit). The **RSi loop** — corpus → train → eval → deploy
(ADR-2606130900) — is the *continued-training drive* that carries a checkpoint across the grokking
barrier; §4.2's wide shallow basin with `‖∇L‖=6.57` is precisely a pre-transition state, and re-running
the loss-landscape probe after further RSi steps would let us *watch* the basin deepen.

## 6. Limitations & honesty

- **oka has no trained model** (R0 scaffold). §4.1 is a real instance of the *operator*, not the deployed
  26B model. The mandala/animation figures are conceptual.
- maxwell-1 figures in §4.2–4.3 are **measured** from real weights; §4.4 layer/attention 3D figures are
  **config-accurate but illustratively wired**.
- The loss landscape (§4.2) is a 2-direction *slice* of a million-dimensional surface (standard, honest).
- The diffusion SFT objective (§3.2/§4.4) is a defensible *uniform-diffusion* loss, **not bit-confirmed**
  against Google's unpublished training recipe.
- The checkpoint is deliberately under-trained; all conclusions are about *where on the landscape it sits*,
  not final quality.

## 7. Future work

1. **Landscape-over-training series** — re-run `loss_landscape.py` across RSi steps to film the basin
   deepening (grokking made visible on real weights).
2. **oka, made real** — close D3 (fleet diffusion/sheaf runtime) + D4 (diffusion/sheaf SFT) so the
   sheaf physics of §4.1 runs on trained weights, not a constructed instance.
3. **diffusion-26B real landscape** — the heavier filter-normalised landscape for maxwell-diffusion.
4. **Hessian sharpness** — measure top eigenvalues at `θ*` to quantify the wide-vs-narrow valley
   (flatness ↔ generalization) directly.

## Reproducibility

| Result | Script | Where |
|---|---|---|
| oka sheaf physics | `70-tools/scripts/viz/gen_oka_sheaf_compute.py` | local (numpy) |
| maxwell-1 loss landscape | `70-tools/scripts/maxwell/loss_landscape.py` | gad (real adapter) |
| maxwell-1 real tensors | `70-tools/scripts/maxwell/extract_weights.py` | gad → JSON → render |
| concept figures | `70-tools/scripts/viz/gen_*.py` | local (matplotlib/SVG) |

Figure index: `90-docs/baien/weight-family-viz.md`. All compute Murakumo-only (ADR-2605215000).

## References

1. *The Physics Secret Behind Neural Nets' Weirdest Phenomenon* (grokking / energy-landscape; YouTube Zn4fApSAtsc, 2026).
2. *Why Turning Up "Temperature" Can Make Neural Nets Smarter [Learning vs Exploration]* (YouTube, 2026).
3. Nanda et al. / DeepMind, circuit-efficiency account of grokking (memorize→generalize, slow generalizing circuit), 2023.
4. Bodnar, Di Giovanni, et al., *Neural Sheaf Diffusion: A Topological Perspective on Heterophily and Oversmoothing in GNNs*, NeurIPS 2022.
5. Li, Xu, Taylor, Studer, Goldstein, *Visualizing the Loss Landscape of Neural Nets* (filter-normalized directions), NeurIPS 2018.
6. ADR-2605250700 (Oka × MMSheaf), ADR-2606171100 (maxwell-diffusion), ADR-2606130900 (Maxwell RSi), ADR-2606061000 (Maxwell), ADR-2605092350 (baien BitNet), ADR-2605215000 (Murakumo-only).
