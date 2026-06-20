---
id: adr-2606201000-maxwell-diffusion-drafter-assisted-decode
title: "ADR-2606201000: maxwell-diffusion drafter-assisted decode — AR draft warm-starts the block-diffusion canvas"
status: proposed
doc_type: adr
topic: maxwell-diffusion-drafter-assisted-decode
authoritative: true
last_verified: 2026-06-20
priority: 6.0
axis: ml
weight: 0.60
priority_note: "Adds a speculative-style AR drafter to maxwell-diffusion: the AR weight's answer seeds the diffusion canvas (warm-start) instead of uniform-random init. Measured: quality 80→100%, decoder forward passes −17% (E4B drafter) / −27% (12b drafter), no regressions. Realizes the '12b-class pre-inference, diffusion finishes' direction."
authoritative_for:
  - maxwell-diffusion-drafter-assisted-decode
  - maxwell-diffusion-warm-start-canvas
depends_on:
  - "2606171100"   # maxwell-diffusion variant (DiffusionGemma 26B-A4B base; this ADR's parent)
  - "2606061000"   # Maxwell — default AR LLM weight (the drafter source)
  - "2605215000"   # Murakumo-only inference (drafter = fleet, target = gad; no commercial GPU/API)
related:
  - "2606130900"   # Maxwell RSi ecosystem (eval leg; e7m micro bench reused here)
  - "2606171800"   # weight-family-generalization-physics (diffusion = annealed denoising operator)
  - "2606142200"   # Research Tracks B (speculative decode) + C (MatFormer drafter) on the AR side
supersedes: []
superseded_by: []
---

# ADR-2606201000: maxwell-diffusion drafter-assisted decode — AR draft warm-starts the block-diffusion canvas

**Status**: proposed
**Date**: 2026-06-20
**Deciders**: Jun Kawasaki

# Context

**maxwell-diffusion** (ADR-2606171100) is the block-diffusion throughput sibling of Maxwell
(`google/diffusiongemma-26B-A4B-it`, MoE 25.2B/3.8B active). Its sampler generates a canvas
by **iterative denoising from a uniform-RANDOM initial canvas** — the entropy-bound sampler
in `transformers/models/diffusion_gemma/generation_diffusion_gemma.py`:

```python
# ~line 985
current_canvas = model_kwargs.pop(
    "decoder_input_ids", sampler.initialize_canvas(batch_size=batch_size, device=device))
```

So `decoder_input_ids`, if supplied, **replaces the random starting canvas** — a documented
"set the starting canvas" hook. This is the natural insertion point for a speculative-style
**drafter**: a cheap AR model proposes the answer, and we hand that proposal to the denoiser
as its starting point. A draft near the target sits at low effective diffusion-time *t*, so
the sampler's adaptive stopping should converge in fewer decoder forward passes; a draft far
from the target makes the sampler thrash (low acceptance → repeated renoise) — the same
acceptance-rate dependence as AR speculative decoding (ADR-2606142200 Track B).

This is the concrete form of the long-standing "**diffusion で 12b 級の事前推論**" idea: let a
strong AR weight do the *pre-inference* (the look-ahead), and let the cheap parallel diffusion
pass *finish/verify* it.

# Decision

Add **drafter-assisted decode (warm-start)** as an inference-time option for maxwell-diffusion:

1. A cheap AR drafter generates the answer **text** for the prompt.
2. The text is re-tokenized into the diffusion model's (gemma) vocab — cross-tokenizer safe.
3. **Partial warm-start**: the draft ids seed the canvas *prefix*; the tail stays uniform-random
   (so short answers are not penalised by a forced full 256-token content canvas).
4. The seeded canvas is passed as `decoder_input_ids` to `generate()`. No training, no model change.

Harness: `70-tools/scripts/maxwell/draft_init_bench.py` (two-phase: draft → free drafter → bench,
to avoid 52GB-target + drafter co-residency). Quality uses the **same e7m micro PROMPTS/scorers**
that produced the 80% diffusion base bench (ADR-2606171100), so it is apples-to-apples.

Murakumo-only (ADR-2605215000): drafter = fleet (E4B as local HF on gad; 12b via naphtali Ollama
`gemma4:12b-it-qat`), target = gad diffusion. No commercial GPU / external API.

## Measured results (gad EVO-X2, CPU bf16, 15-prompt e7m micro)

| drafter | quality base→warm | decoder forward passes | drafter cost |
|---|---|---|---|
| SmolLM2-135M (2-prompt smoke) | preserved | — | **wall ×5 SLOWER** (too-far draft → thrash) |
| **gemma-4-E4B** (AR Maxwell base) | 12/15 → **15/15** (80→100%) | 52 → 43 (**−17%**) | ~0.3–5 s/prompt |
| **gemma4:12b-it-qat** (fleet Ollama) | 13/15 → **15/15** (86.7→100%) | 56 → 41 (**−27%**) | ~1–4 s/prompt |

- **Stronger/closer drafter → larger speedup** (12b −27% > E4B −17%), exactly the acceptance-rate
  prediction. The 135M drafter is *too far* from the target and is net-negative.
- **Every quality flip was an empty-output rescue**: the diffusion base occasionally collapses to
  `''` from random init; seeding the drafter's answer (`C` / `7` / `Thank you.`) lets the denoiser
  keep it → correct. No prompt regressed in either run.
- Wall-clock also dropped (E4B −22%, 12b −25%) but the **absolute** wall-clock is noisy across runs
  (gad CPU load moved the *base* between 371 s and 942 s); the stable within-run indicator is
  **decoder forward passes**.

## GPU throughput (Modal A100/H100; base diffusion vs AR 12b)

The CPU numbers above measure the *drafter effect*; they undersell raw throughput (gad has no
working GPU path — gfx1151 ROCm crashes: bnb-4bit HIP GP-fault, and quanto-int4 OOMs at 47.45/48 GB
in the MoE `grouped_mm_experts_forward`). To get real GPU tok/s we ran on Modal NVIDIA GPUs (open-model
research, transparent — Rider v3.3 §2(i) / ADR-2606172359 objective-function compute).

**throughput is measured on long generation** (400-word essay); short answers (1-token MMLU) over a
256-canvas grossly under-report diffusion tok/s, which is why the e7m-micro warm-start tok/s looked
~10. Single-sequence, bf16, tok/s:

| model | type | params | B=1 | batched peak | int4 peak |
|---|---|---|---|---|---|
| maxwell-diffusion | discrete-diffusion | 25.2B / 3.8B-active MoE | **318** (H100) / 137 (A100) | 531 (H100 bf16 B=4) | 555 (H100 B=8) |
| gemma-4-12b | autoregressive | 12B dense | 25 (H100) | 430 (bf16 B=32) | **629 (int4 B=64)** |

- **Single-stream: diffusion ≫ AR** — 318 vs 25 tok/s (**~13×**). Block-diffusion emits a 256-canvas in
  ~17 forward passes (tokens_per_forward ≈ 15–20) vs AR's 1 token / forward. The diffusion win is
  *latency / low-batch*.
- **High-concurrency: AR wins** — gemma-4-12b int4 is 8–15 GB resident → packs B=64 → 629 tok/s aggregate;
  maxwell-diffusion's MoE forward intermediate caps batch at ~8 (B=16 OOM even int4), peaking ~555.
- **int4 effect is asymmetric**: huge for AR (24→8 GB enables big batch: bf16 430 → int4 629), marginal
  for the diffusion MoE (555 vs 531 — limited by the forward *intermediate*, not weight storage; int4
  B=16 still OOMs). At B=1 int4 is slightly *slower* than bf16 (dequant overhead: 12b 20 vs 25 tok/s).
- **~1000 tok/s** (the diffusion-LM marketing figure) needs fp8 + fused-MoE/flash-attn + H200/B200 (bigger
  batch); single-sequence unoptimized on H100 is ~318.
- These are **base (random-init) diffusion** numbers. The drafter warm-start (above) is an additive
  quality/step effect on the *single-stream* path; on long multi-canvas output it only seeds the first
  canvas, so its throughput contribution is smaller than on short answers.

## Generation-quality benchmark (Modal H100; GSM8K + e7m-micro)

**GSM8K** (80 test items, 0-shot CoT, exact-match, `max_new_tokens=512`):

| config | accuracy | time | vs 12b |
|---|---|---|---|
| gemma-4-12b (AR) | 78/80 = **97.5%** | 1552 s | 1× |
| maxwell-diffusion base (random-init) | 79/80 = **98.8%** | 91 s | **~17× faster** |
| maxwell-diffusion warm (12b-integrated) | 78/80 = **97.5%** | 59 s | ~26× (diffusion-stage only) |

- **Quality parity**: all three ≈ 97–99% — the 25.2B/3.8B-active diffusion matches the dense 12b on
  math reasoning, while being **~17× faster** (91 s vs 1552 s). Same quality, fraction of the wall-clock.
- **Warm-start adds no quality here**: base is already at the 98.8% ceiling, so the empty-output rescue
  that lifted e7m-micro (80→100%) does not fire (CoT fills the canvas). Its only effect is a faster
  diffusion stage (59 s); end-to-end it is slower because the 12b draft costs 1552 s. **Warm-start's
  quality value is regime-dependent** — it helps where base whiffs (short structured answers), and is
  neutral where base is already strong (math CoT).
- **Context length is decisive**: at `max_new_tokens=256` the same GSM8K run scored 12b 40% (truncated
  CoT); raising to 512 → 97.5%. All scores here use 512.

**e7m-micro warm-start on GPU** (H100, 15 prompts): base 12/15 @ 9.27 tok/s (49 forwards) →
warm 15/15 @ 36.35 tok/s (37 forwards) = quality 80→100%, **forward passes −24.5%** (the tok/s gain is
inflated by base's empty-output cases; forward-passes + quality are the robust read).

## Code-implementation quality (etzhayyim Python→Clojure; clj-kondo gate)

The project's *actual* task is Python→Clojure refactoring scored by **clj-kondo** (the RSi quality gate).
30 real corpus prompts ("Convert this Python method to Clojure following kotoba Datom log idioms"),
H100, `max_new_tokens=512`, scored by clj-kondo error-clean (0 errors):

| config | clj-kondo clean | avg errors |
|---|---|---|
| GOLD (verified corpus answers) | 27/30 = **90%** | 0.1 |
| gemma-4-12b (AR) | 11/30 = **37%** | 3.93 |
| maxwell-diffusion base (random-init) | 3/30 = **10%** | 3.8 |
| maxwell-diffusion warm (12b-integrated) | 3/30 = **10%** | 3.63 |

**Reversal vs GSM8K**: on syntactically-rigid code the AR 12b *beats* the diffusion model (37% vs 10%),
and **warm-start does NOT help** — seeding the 12b's better draft into the canvas and re-denoising
*corrupts* it back to base level (10%). Mechanism: diffusion rewrites the whole canvas in parallel, which
breaks long-range syntactic constraints (paren/S-expr nesting) that AR preserves left-to-right; math CoT
(natural text + a final number) is error-tolerant, so diffusion held there, but Clojure is not.
**Implication for Maxwell**: for the real clj/Datomic implementation target, autoregressive (12b/Maxwell-AR)
is the right tier — diffusion's speed does not convert to code quality, and drafter warm-start cannot
rescue it. (Both are *base* models; the RSi loop fine-tunes the AR weight on Clojure. GOLD = curated +
verified corpus, not raw generation.)

# Consequences

## Positive

- A drop-in, **training-free** quality+speed win for maxwell-diffusion (80→100% on e7m micro,
  −17/−27% forward passes) using only the `decoder_input_ids` hook.
- Unifies the family: the AR Maxwell weight (or the fleet 12b) becomes the *drafter* for its
  diffusion sibling — one weight, two roles (cf. MatFormer E2B drafter, ADR-2606142200 Track C).
- Directly realises the "12b pre-inference → diffusion finishes" direction.

## Negative / honest limits

- The quality gain is **draft-assisted**: the drafter's knowledge surfaces and the diffusion model
  verifies/keeps it (e.g. MC answers seeded as `C`). It is not the diffusion model's standalone
  quality. Safe side: zero regressions observed.
- **Not a uniform speedup**: trivial prompts the base already solves in ~2 forward passes can get
  *slower* when the draft adds tokens to denoise (e.g. reason_batball 2→6 in the E4B run). Needs
  confidence-gated warm/random selection.
- CPU-only numbers; GPU residency remains walled (ADR-2606171100 / BNB-ROCM-BUILD.md). The D4
  corruption schedule is still recipe-unvalidated vs Google.
- A too-weak drafter is **net-negative** (135M ×5 slower). The drafter must be close to the target.

# Alternatives Considered

- **Block-level (across-block) speculative decode** — drafter proposes the next block, diffusion
  verifies in one forward, accept longest prefix (reuse `speculative.py` α/γ math). More formal,
  but the per-token diffusion conditional isn't cheaply exact, so acceptance is approximate.
  Warm-start (within-block) is exact w.r.t. the diffusion distribution and needed no new accept rule.
- **diffusion-as-drafter for an AR target** (SSD-style) — the inverse direction; not our goal here
  (we want the diffusion model's parallel output, accelerated/improved).
- **Self-drafting** (the diffusion model's own E2B-equivalent) — deferred; needs a nested submodel.

# Next steps

1. **Confidence gating** — pick warm vs random per prompt by draft confidence, to kill the
   trivial-prompt slowdown.
2. **Train-time self-conditioning** (D4 extension) — fine-tune maxwell-diffusion to *expect* a warm
   start, raising acceptance further.
3. **GPU** — re-measure once 4-bit residency unlocks (the wall-clock story is CPU-bound today).

# References

- `70-tools/scripts/maxwell/draft_init_bench.py` — two-phase draft/bench harness (this ADR)
- gad: `~/maxwell/specdiff_e4b.jsonl`, `~/maxwell/specdiff_12b.jsonl`, `~/maxwell/drafts_{e4b,12b}.jsonl`
- `transformers/models/diffusion_gemma/generation_diffusion_gemma.py` — `decoder_input_ids` canvas hook (~985)
- ADR-2606171100 (maxwell-diffusion variant), ADR-2606061000 (Maxwell AR weight)
- ADR-2606142200 (Research Tracks B speculative + C MatFormer drafter)
- ADR-2605215000 (Murakumo-only inference)
