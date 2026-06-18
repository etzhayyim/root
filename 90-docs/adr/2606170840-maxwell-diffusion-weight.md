---
id: adr-2606170840-maxwell-diffusion-weight
title: "ADR-2606170840: Maxwell-Diffusion — diffusion-LM sibling weight (diffusiongemma-26B-A4B-it fine-tune)"
status: proposed
doc_type: adr
topic: maxwell-diffusion-weight
authoritative: true
last_verified: 2026-06-17
priority: 6.5
axis: ml
weight: 0.65
priority_note: "Names + registers the Maxwell-lineage diffusion-LM trunk; high reuse for parallel/structured/infill workloads."
authoritative_for:
  - diffusion-llm-weight-name
  - murakumo-fleet-diffusion-instruct-weight
depends_on:
  - "2606061000"   # Maxwell — default LLM weight (parent lineage)
  - "2605215000"   # Murakumo-only inference (no commercial GPU rental)
  - "2605250400"   # gemma-coder-distill recipe (corpus + gate reused; objective adapted)
  - "2605242100"   # baien 4-tier ladder (server/fleet tier, not edge)
  - "2605241900"   # baien edge invariant (Maxwell-Diffusion is NOT the edge tier)
related:
  - "2605092350"   # baien (edge BitNet trunk — distinct-trunk sibling precedent)
  - "2606062100"   # Apache 2.0 + Charter Rider v3.1 (3-Tier) — license
  - "2605262200"   # Charter Rider §2(i)(2) train-only GPU-rental carve-out (gated)
  - "2605242400"   # smoke=destructive lesson (min-informative training tier)
  - "2605250005"   # kotoba-llm WebGPU inference (future diffusion-decode path)
supersedes: []
superseded_by: []
---

# ADR-2606170840: Maxwell-Diffusion — diffusion-LM sibling weight (diffusiongemma-26B-A4B-it fine-tune)

**Status**: proposed
**Date**: 2026-06-17
**Deciders**: Jun Kawasaki

# Context

ADR-2606061000 named **Maxwell** (`maxwell-1`) — the religious-corp default
instruct weight, a Charter-aligned fine-tune of **Gemma 4 E4B**, an
**autoregressive** trunk served Murakumo-only on the fleet tier. Every actor's
`heartbeat / shinka / react / general / social / structured / json` call resolves
through it.

Autoregressive left-to-right decoding is not the only generation paradigm. A
**discrete text-diffusion LM** decodes in parallel by iteratively denoising a
fully-masked sequence — which is structurally better at:

- **constrained / structured output** (JSON, EDN datoms, lexicon-shaped records)
  where the whole shape is denoised jointly rather than committed left-to-right;
- **infilling / fill-in-the-middle** (patching a method body, completing a
  template clause) where both prefix and suffix condition every step;
- **controllable / self-correcting generation** (a denoising step can revise an
  earlier token an AR model has already locked in).

Google's `google/diffusiongemma-26B-A4B-it`
(<https://huggingface.co/google/diffusiongemma-26B-A4B-it>) is an
instruction-tuned **diffusion** Gemma: a **Mixture-of-Experts trunk, 26B total
parameters / ~4B active** per step. The active-parameter budget (≈4B) is the same
fleet-tier class as Maxwell's Gemma 4 E4B (≈4B effective), so it slots onto the
**same Murakumo server/fleet rung** — it is **not** an edge weight (the full 26B
weight set is far over the ≤2GB edge envelope, ADR-2605241900).

The registry SSoT
(`crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry.ts`, in the
`40-engine/kotoba` submodule) has no first-class name for a diffusion trunk, and
the naming invariant (ADR-2606061000 §"Why Maxwell") says weights take
descriptive/scientific names. This ADR gives the diffusion trunk a name —
**Maxwell-Diffusion** — and registers it as a **Charter-aligned instruction
fine-tune of `diffusiongemma-26B-A4B-it`**, served Murakumo-only, as a
**sibling weight in the Maxwell lineage** (not a replacement for `maxwell-1`).

## Why "Maxwell-Diffusion"

It keeps the **Maxwell** family name (the field every actor draws inference from —
ADR-2606061000) and qualifies it by architecture, the way `gemma-4-e4b` vs
`gemma-4-e2b` qualify by size. The qualifier is doubly apt and stays
non-anthropomorphic / non-eschatological (ADR-2605192100 §1.15):

- **Diffusion is literally Maxwell's physics.** The Maxwell-Boltzmann
  distribution and Maxwell's demon are statements *about diffusion and the
  thermodynamics of sorting information*. A weight that generates by reversing a
  noising (diffusion) process is the most on-the-nose possible reading of the
  family name: a demon that *denoises*, not a prophet that proclaims.
- It is an architecture qualifier, not a kami and not a claim to divinity —
  consistent with the actor-vs-weight distinction (actors take kami names;
  weights take descriptive names).

# Decision

## D1 — Maxwell-Diffusion is a named sibling weight (Tier 0, Murakumo fleet, diffusion trunk)

`maxwell-diffusion-1` is the canonical registry id for a **Charter-aligned
instruction fine-tune of `google/diffusiongemma-26B-A4B-it`**, served on the
Murakumo fleet (LiteLLM `127.0.0.1:4000` + EVO-X2 LAN per ADR-2605215000).

Tier placement (baien 4-tier ladder, ADR-2605242100): **server/fleet tier**, NOT
the edge tier. The ≈4B active-parameter step is fleet-class, but the full 26B MoE
weight set is far over the ≤2GB edge envelope (ADR-2605241900) — **baien remains
the edge default, unchanged**. Maxwell and Maxwell-Diffusion are siblings on the
same fleet rung, differing in *decoding paradigm*:

| Weight | Tier | Trunk | Decoding | Best for |
|---|---|---|---|---|
| **Maxwell** (`maxwell-1`) | server/fleet | Gemma 4 E4B fine-tune | autoregressive | every actor's general/social/japanese/react/heartbeat call (the default) |
| **Maxwell-Diffusion** (`maxwell-diffusion-1`) | server/fleet | diffusiongemma-26B-A4B-it fine-tune | discrete diffusion (parallel denoise) | constrained-structured / JSON / EDN-datom / infill / self-correcting generation |
| baien | edge | BitNet 1.58-bit ≤4B | autoregressive | `edge / browser / cpu` |

`maxwell-1` **stays the default weight.** Maxwell-Diffusion is an *additional*
trunk an actor opts into via `resolveModel(hint="maxwell-diffusion", useCase)` for
workloads where parallel denoising wins; it does not take over any
`USE_CASE_DEFAULTS` entry (D3).

## D2 — Registry wiring (SSoT, kotoba submodule)

Single source of truth is
`40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry.ts`
(tracked by the **`etzhayyim/kotoba` submodule**, so the registry edit lands as
its **own PR in that repo**, paired with this ADR in `etzhayyim/root`). It adds:

- `MODEL_REGISTRY["maxwell-diffusion-1"]` — the `ModelDef` (`available: false` at
  R0, see D5), `huggingfaceModel: "etzhayyim/maxwell-diffusion-1-diffusiongemma-26b-a4b"`,
  `cfModel: "huggingface:etzhayyim/maxwell-diffusion-1-diffusiongemma-26b-a4b"`,
  `contextWindow: 128000`, `maxTokens: 4096`,
  `useCases: ["structured", "json", "extraction"]`.
  **No `ollamaModel` field** — stock Ollama's autoregressive runtime cannot serve a
  diffusion decoder; serving is via the LiteLLM gateway to a diffusion-capable
  backend on EVO-X2 (and, later, the kotoba-llm WebGPU diffusion-decode path,
  ADR-2605250005). Recording a fake `gemma4:*` Ollama tag would be dishonest.
- `MODEL_ALIASES["maxwell-diffusion"] = "maxwell-diffusion-1"` (and
  `etzhayyim/maxwell-diffusion-1-diffusiongemma-26b-a4b` → `maxwell-diffusion-1`).
- `MAXWELL_DIFFUSION_WEIGHT = "maxwell-diffusion-1"` — the exported SSoT constant
  for "the religious-corp diffusion trunk." Callers and docs reference this
  constant, never a hardcoded string (gate G5), mirroring `MAXWELL_DEFAULT_WEIGHT`.
- A provenance manifest `90-docs/baien/maxwell-diffusion-models.jsonl` (append-only,
  the SSoT for diffusion-trunk training provenance — base model, recipe hash,
  corpus Charter-Rider scan, microbench delta, merged CID), mirroring
  `maxwell-models.jsonl`.

## D3 — No default flips at R0 (additive only)

Maxwell-Diffusion adds a *new* resolvable id; it changes **no**
`USE_CASE_DEFAULTS` entry and does **not** touch `MURAKUMO_DEFAULT_MODEL` or
`MAXWELL_DEFAULT_WEIGHT`. Because `resolveModelId` falls open to an *available*
model, an `available: false` `maxwell-diffusion-1` never breaks routing: an actor
that asks for it before weights exist silently degrades to `gemma-4-e4b-it`. Any
future flip of a specific use-case (e.g. `json`/`structured`) to
`maxwell-diffusion-1` is a separate, explicit one-line registry change gated on the
M1 evidence (D5) — not assumed here.

## D4 — Training recipe (corpus reused; objective adapted — do NOT claim verbatim reuse)

Maxwell-Diffusion reuses the **corpus and the gate**, but **not** the loss, of the
gemma-coder-distill recipe (ADR-2605250400) — because the training objective is
fundamentally different:

- **Reused verbatim**: the etzhayyim-aligned SFT corpus
  (`90-docs/baien/maxwell-sft-corpus.jsonl`, the same ChatML
  `system/user/model` pairs), the **Charter Rider §2(a)–(h) scanner pre-pass**
  (`charter_rider.scan`, ADR-2605192200, gate G3 — no step runs on
  unscanned text), and the **EVO-X2 ROCm** religious-corp training substrate
  (no RunPod / no commercial GPU rental, ADR-2605215000 + Charter Rider §2(i)).
- **Adapted (the honest difference)**: a diffusion LM is trained with a
  **masked/denoising objective over the discrete token field**, not next-token
  cross-entropy. The LoRA adapter attaches to the diffusiongemma MoE
  attention/expert projections, and the loss is the diffusion denoising loss
  (random mask schedule → predict the clean tokens), **not** the AR CE in
  ADR-2605250400. Claiming "reuses gemma-coder-distill verbatim" (as Maxwell does,
  legitimately, because Maxwell *is* autoregressive) would be false here. The
  diffusion-adapted recipe is specified as a **new recipe spec** (`maxwell-diffusion`
  recipe), corpus- and gate-compatible with Maxwell but with its own objective.

Merged adapter → HF `etzhayyim/maxwell-diffusion-1-diffusiongemma-26b-a4b` → a
LiteLLM diffusion-backend slot → a provenance line in
`maxwell-diffusion-models.jsonl`.

## D5 — R0 is honest: `available: false` until empirically trained

Per the smoke=destructive lesson (ADR-2605242400), a registry entry is not a
usable weight. Maxwell-Diffusion ships at R0 as **name + registry slot + recipe
spec + provenance scaffold only**, `available: false`. It flips to `true` only when
a real diffusion fine-tune clears the publish gate — **≥250 optimizer steps OR a
measurable win on a diffusion-appropriate microbench** (constrained-decode /
infill exact-match, since `e7m bench micro`'s AR-decode harness does not directly
fit a diffusion decoder — the bench adaptation is itself an M1 deliverable),
recorded in `maxwell-diffusion-models.jsonl`. Until then this ADR is design-only.

## D6 — Lineage (named, each its own ADR)

- **MD0** (this ADR, R0): naming + registry scaffold + recipe spec + provenance.
- **MD1**: first diffusion fine-tune on EVO-X2 (or the gated train-only GPU-rental
  carve-out, ADR-2605262200, if 26B-A4B exceeds EVO-X2); diffusion microbench gate;
  flip `available`. Wire the LiteLLM diffusion backend.
- **MD2**: constrained-decode integration — feed lexicon/EDN-datom output schemas
  to the denoiser as a hard mask so structured generation is guaranteed-shaped.
- **MD3+**: kotoba-llm WebGPU diffusion-decode path (ADR-2605250005) for an
  in-fleet, no-external-runtime decoder.

# Consequences

**Positive**

- The diffusion paradigm gets an owned, versioned, Charter-scannable identity in
  the SSoT registry, named consistently with `maxwell-1` / baien.
- A parallel-denoise trunk targeted at the exact workloads (structured / JSON /
  EDN-datom / infill) the autoregressive default is weakest at — additive, never
  destabilising the default route (D3).

**Negative / honest limits**

- **Gemma licence inheritance (must verify before publish).** A fine-tune of
  `diffusiongemma` inherits Google's **Gemma Terms of Use** on the *weights* (the
  training code/recipe/registry stay Apache 2.0 + Charter Rider v3.1). MD1 must
  confirm Gemma-Terms compatibility with IPFS/HF distribution before flipping
  `available: true`. Flagged open item, identical to Maxwell ADR-2606061000.
- **Serving is not stock-Ollama.** A diffusion decoder needs a diffusion-capable
  backend (LiteLLM-fronted on EVO-X2, later kotoba-llm WebGPU). The Murakumo
  invariant holds (no commercial GPU rental), but the per-node Ollama
  `gemma3:4b`/`gemma4:e4b` slots **cannot** serve this weight — hence no
  `ollamaModel` field. This is a real serving-substrate gap MD1 must close.
- **26B-A4B may exceed EVO-X2 for training.** If so, MD1 is blocked on the gated
  train-only GPU-rental carve-out (ADR-2605262200) — a governance step, not a
  free one.
- No weights exist yet — R0 is design-only; all empirical claims deferred to MD1.

# Alternatives Considered

- **Fold the diffusion trunk into `maxwell-1`.** Rejected: `maxwell-1` is the
  autoregressive Gemma 4 E4B default; a diffusion MoE is a different trunk and a
  different decoding paradigm. Collapsing them would make the default weight
  ambiguous and break the one-trunk-per-id SSoT discipline.
- **Flip `json`/`structured` defaults to it immediately.** Rejected: violates the
  smoke=destructive honesty rule — no trained diffusion weights exist (D5), and
  the diffusion microbench isn't built yet.
- **Give it a non-Maxwell name.** Rejected: it shares Maxwell's fleet tier, its
  corpus, its gate, and its Murakumo-only serving discipline — it is a Maxwell
  lineage member, and "Diffusion" is the natural architecture qualifier (and,
  literally, Maxwell's own physics).
- **Claim verbatim reuse of the gemma-coder-distill recipe.** Rejected as
  dishonest: the diffusion denoising objective is not AR cross-entropy (D4).

# References

- `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry.ts` — SSoT registry (kotoba submodule)
- `90-docs/baien/maxwell-diffusion-models.jsonl` — Maxwell-Diffusion provenance manifest (this ADR)
- `90-docs/baien/maxwell-sft-corpus.jsonl` — shared SFT corpus (reused)
- `70-tools/scripts/maxwell/gate_candidates.py` — clj-kondo + Charter Rider gate (reused)
- <https://huggingface.co/google/diffusiongemma-26B-A4B-it> — base model
- ADR-2606061000 — Maxwell default LLM weight (parent lineage)
- ADR-2605215000 — Murakumo-only inference (no commercial GPU rental)
- ADR-2605250400 — gemma-coder-distill recipe (corpus + gate reused; objective adapted)
- ADR-2605242100 — baien 4-tier ladder; ADR-2605241900 — edge invariant
- ADR-2605262200 — Charter Rider §2(i)(2) train-only GPU-rental carve-out (gated)
- ADR-2605242400 — smoke=destructive / minimum-informative training tier
- ADR-2606062100 — Apache 2.0 + Charter Rider v3.1 (3-Tier)
- ADR-2605250005 — kotoba-llm WebGPU inference (future diffusion-decode path)
</content>
</invoke>
