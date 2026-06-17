---
id: adr-2606171100-maxwell-diffusion-variant
title: "ADR-2606171100: maxwell-diffusion — diffusion-LM fleet variant (DiffusionGemma 26B-A4B base)"
status: proposed
doc_type: adr
topic: maxwell-diffusion-variant
authoritative: true
last_verified: 2026-06-17
priority: 6.0
axis: ml
weight: 0.60
priority_note: "Names + registers a diffusion-LM throughput-tier sibling of Maxwell; high-speed parallel generation for latency-sensitive fleet calls."
authoritative_for:
  - maxwell-diffusion-weight-name
  - murakumo-fleet-diffusion-throughput-weight
depends_on:
  - "2606061000"   # Maxwell — default LLM weight (this ADR's parent; same family + flip discipline)
  - "2605215000"   # Murakumo-only inference (no commercial GPU rental)
  - "2605192200"   # Apache 2.0 + Charter Rider
related:
  - "2605242100"   # baien 4-tier ladder (edge / bonsai / server / XL)
  - "2605241900"   # baien edge invariant (maxwell-diffusion is NOT the edge tier)
  - "2606130900"   # Maxwell RSi ecosystem (corpus → train → eval → deploy loop)
  - "2606131645"   # kotoba submodule removed from root (registry TS now external)
  - "2605242400"   # smoke=destructive lesson (registry entry ≠ usable weight)
supersedes: []
superseded_by: []
---

# ADR-2606171100: maxwell-diffusion — diffusion-LM fleet variant (DiffusionGemma 26B-A4B base)

**Status**: proposed
**Date**: 2026-06-17
**Deciders**: Jun Kawasaki

# Context

**Maxwell** (ADR-2606061000) is the named religious-corp default inference weight:
a Charter-aligned instruction fine-tune of **Gemma 4 E4B**, an *autoregressive*
(next-token) model, served Murakumo-only on the fleet. It is small (E4B) and is the
general-purpose default for every actor's `general / structured / social / japanese /
react / heartbeat` call.

Google DeepMind has since published **`google/diffusiongemma-26B-A4B-it`** (verified
2026-06-17, model card live, **Apache 2.0**): a **discrete diffusion language model**
built on the Gemma 4 architecture — the same `26B-A4B` family the Murakumo teacher
node **gad** already serves (`gemma4-26b-a4b-q4` on `llama-server`). Its salient
properties:

- **Architecture**: discrete diffusion, *not* autoregressive — "block-autoregressive
  multi-canvas sampling" that **iteratively denoises blocks of tokens in parallel**
  rather than emitting one token at a time.
- **Size**: 25.2B total / **3.8B active** (sparse MoE, 8 active of 128 experts).
- **Throughput**: positioned for low-latency generation, **>1100 tok/s** at low batch.
- **Context / modality**: up to **256K** tokens; multimodal in (text/image/video) →
  text out; configurable thinking mode.
- **License**: Apache 2.0 (Charter-Rider-compatible, no weakening needed).

The diffusion paradigm's parallel denoising is a *different cost/latency curve* from
Maxwell's autoregressive decode: it trades more compute-per-step for far fewer
sequential steps, which is exactly what latency-sensitive fleet calls (interactive
concierge turns, heartbeat narration, structured-output filling) want. There is today
no first-class name or registry slot for a Charter-aligned fine-tune of this base — the
same gap ADR-2606061000 closed for the autoregressive default. This ADR closes it for
the diffusion variant, **as a sibling of Maxwell, not a replacement**.

## Why "maxwell-diffusion"

The weight families are named for what they *are* (the anti-anthropomorphic,
non-eschatological naming invariant — ADR-2605192100 §1.15; no weight is a 預言者). The
name extends the Maxwell logic rather than inventing a new lineage:

- **Maxwell's equations** describe the *propagation of a field* — light as a wave that
  fills space, not a particle emitted one at a time. A **diffusion** LM denoises a whole
  canvas of tokens *as a field* in parallel, the wave-like dual of Maxwell's
  particle-by-particle autoregressive decode. `maxwell-diffusion` is literally the
  field/wave reading of the same equations.
- It stays a descriptive/scientific surname-qualified id (no kami, no prophet),
  consistent with the actor-vs-weight distinction.

# Decision

## D1 — `maxwell-diffusion-1` is a named throughput-tier fleet weight (sibling of Maxwell)

`maxwell-diffusion-1` is the canonical registry id for a **Charter-aligned fine-tune of
`google/diffusiongemma-26B-A4B-it`**, served Murakumo-only (ADR-2605215000). It is a
**server/fleet-tier sibling of Maxwell**, NOT the edge tier — the ≤4B/≤2GB edge envelope
(ADR-2605241900) belongs to **baien** and is untouched. Maxwell stays the default
autoregressive weight; `maxwell-diffusion-1` is the **parallel-denoising throughput
option** evaluated for latency-sensitive use-cases.

| Weight | Tier | Trunk | Decode | Default for |
|---|---|---|---|---|
| **Maxwell** (`maxwell-1`) | server/fleet | Gemma 4 E4B fine-tune | autoregressive | every actor's general/structured/social/japanese/react/heartbeat call |
| **maxwell-diffusion** (`maxwell-diffusion-1`) | server/fleet (throughput) | DiffusionGemma 26B-A4B fine-tune | **parallel denoising** | latency-sensitive calls IF it clears the gate (D5) — else unused |
| baien | edge | BitNet 1.58-bit ≤4B | autoregressive | edge/browser/cpu |

## D2 — Registry wiring is a follow-up in the EXTERNAL kotoba repo

Per ADR-2606131645 the kotoba submodule was removed from root, so the model registry
SSoT (`…/kotodama-host-sdk/src/llm-model-registry.ts`) now lives in the external
`etzhayyim/kotoba` repo and is **not editable in-tree**. The wiring — mirroring
ADR-2606061000 D2 — is therefore a tracked follow-up against that repo:

- `MODEL_REGISTRY["maxwell-diffusion-1"]`: a `ModelDef` with `available: false` (R0,
  see D5), `huggingfaceModel: "etzhayyim/maxwell-diffusion-1-gemma4-26b-a4b"`,
  `contextWindow: 256000`, MoE note (3.8B active / 25.2B total), and a
  `decode: "diffusion"` capability flag so the resolver/runtime never routes a diffusion
  weight through the autoregressive serving path (D3).
- `MODEL_ALIASES["maxwell-diffusion"] = "maxwell-diffusion-1"`.
- No `MURAKUMO_DEFAULT_*` change — `maxwell-diffusion-1` is opt-in per use-case, never
  the silent default.

## D3 — Serving needs a diffusion-capable runtime (honest unknown at R0)

The Murakumo serving path today is **autoregressive** (Ollama / `llama.cpp`
`llama-server` / LiteLLM). A discrete-diffusion model's iterative block-denoising is
**not served by that path** — `llama.cpp` has no diffusion decoder. Serving
`maxwell-diffusion-1` requires a **diffusion-LM runtime on the fleet** (e.g. the HF
`transformers` diffusion generation pipeline, or the vendor's reference runtime), hosted
Murakumo-side (no commercial GPU rental, ADR-2605215000 + Charter Rider §2(i)). This
runtime does **not yet exist on the fleet** and is the first real engineering gate
before any weights matter. R0 records this as an open dependency, not a solved problem.

## D4 — Training is a NEW recipe, not a reuse of Maxwell's causal-LM SFT

Maxwell reuses the `peft + trl` causal-LM LoRA recipe (next-token cross-entropy,
ADR-2605250400) verbatim. **maxwell-diffusion cannot** — a diffusion LM is fine-tuned
with a **masked-denoising / re-masking objective** over corrupted token canvases, not
next-token CE, so the trainer and loss differ. What *is* reused:

- **The corpus**: `90-docs/baien/maxwell-sft-corpus.jsonl` (the 1,016-line / ~990-unique
  Python→Clojure pair set just harvested via the bb harvester) is a valid SFT dataset for
  either objective — the `{system, user, model}` chat triples are paradigm-agnostic.
- **The gates**: Charter Rider §2(a)–(h) scanner pre-pass on the corpus (G3,
  ADR-2605192200) and the Murakumo-only constraint (ADR-2605215000) carry over unchanged.

The diffusion SFT trainer itself (objective, masking schedule, LoRA target modules on
the MoE/diffusion blocks, hardware feasibility on EVO-X2 `gfx1151` ROCm) is **to be
specified** — it is explicitly out of R0 scope and gated on D3's runtime existing first.

## D5 — R0 is honest: `available: false`, no weights, no fleet serving

Per the smoke=destructive lesson (ADR-2605242400), a registry slot is not a usable
weight. `maxwell-diffusion` ships at R0 as **name + family placement + recipe direction +
open dependencies only**, `available: false`. It flips to `true` only when **all** hold:
(1) a fleet diffusion runtime exists and serves the base (D3); (2) a diffusion SFT recipe
is specified and run Murakumo-only (D4); (3) the result clears the same publish gate as
Maxwell — **≥250 SGD-equivalent steps OR ≥+5pp on `e7m bench micro`** (adapted to
diffusion sampling) — recorded as a provenance line in `maxwell-models.jsonl`.

## D6 — Provenance manifest

A registration line is appended to `90-docs/baien/maxwell-models.jsonl` (the append-only
SSoT shared with Maxwell): `kind: "register"`, base coordinates, license, status
`registered-no-weights`, and the open D3/D4 dependencies. No weights, no `available` flip.

# Consequences

- **Positive**: the diffusion base now has a Charter-governed identity and a place in the
  weight family; the just-built corpus has a second consumer; the throughput/latency
  trade-off is now an explicit, evaluable option rather than an untracked idea.
- **Honest cost**: R0 ships *no usable weight* and *no serving path* — D3 (fleet diffusion
  runtime) and D4 (diffusion SFT recipe) are real, unsolved engineering gates. This ADR
  deliberately does not pretend otherwise.
- **No routing risk**: `available: false` + opt-in (no `MURAKUMO_DEFAULT_*` change) means
  the resolver's fail-open discipline (ADR-2606061000 D3) keeps every actor on Maxwell /
  the raw Gemma checkpoint until maxwell-diffusion empirically earns a route.
- **Charter**: base is Apache 2.0 (no license weakening); serving stays Murakumo-only.

# Alternatives Considered

1. **Make maxwell-diffusion the new default, replacing Maxwell.** Rejected — it is a
   different architecture with an unproven fleet serving path and a 26B footprint vs E4B;
   replacing the proven default on an unbuilt runtime would violate the fail-open / honest
   discipline. It is a *sibling option*, evaluated then routed only if it wins.
2. **Register the autoregressive `gemma4-26b-a4b` instead (gad already serves it).**
   Rejected as the diffusion-specific ask — the autoregressive 26B is already reachable as
   the teacher; the user's request is specifically the *diffusion* variant, whose value is
   the parallel-denoising latency curve. (A separate autoregressive 26B Maxwell tier
   remains possible under ADR-2606061000 if wanted.)
3. **Do nothing / keep it informal.** Rejected — an unnamed fine-tune target silently
   shadows vendor coordinates, the exact anti-pattern ADR-2606061000 exists to prevent.

# References

- ADR-2606061000 (Maxwell — default LLM weight; parent, same family + flip discipline)
- ADR-2606130900 (Maxwell RSi ecosystem — corpus → train → eval → deploy)
- ADR-2605215000 (Murakumo-only inference, no commercial GPU rental)
- ADR-2605192200 (Apache 2.0 + Charter Rider)
- ADR-2606131645 (kotoba submodule removed from root — registry TS now external)
- ADR-2605242400 (smoke=destructive — registry entry ≠ usable weight)
- `google/diffusiongemma-26B-A4B-it` model card (Apache 2.0, discrete diffusion, 25.2B/3.8B-active MoE, 256K ctx; verified 2026-06-17)
