---
id: adr-2606061000-maxwell-default-llm-weight
title: "ADR-2606061000: Maxwell — etzhayyim default LLM weight (Gemma 4 E4B fine-tune)"
status: proposed
doc_type: adr
topic: maxwell-default-llm-weight
authoritative: true
last_verified: 2026-06-06
priority: 7.0
axis: ml
weight: 0.70
priority_note: "Names + registers the religious-corp default inference weight; high reuse across every actor."
authoritative_for:
  - default-llm-weight-name
  - murakumo-fleet-default-instruct-weight
depends_on:
  - "2605215000"   # Murakumo-only inference (no commercial GPU rental)
  - "2605250400"   # gemma-coder-distill recipe (peft+trl on EVO-X2 ROCm)
  - "2605242100"   # baien 4-tier ladder (edge / bonsai / server / XL)
  - "2605241900"   # baien edge invariant (Maxwell is NOT the edge tier)
related:
  - "2605092350"   # baien (edge BitNet trunk — sibling, distinct tier)
  - "2605092345"   # oka (server FP8 trunk — sibling)
  - "2605242000"   # roso (bonsai 1-bit siblings)
  - "2605231300"   # baien-distill commit_node + registry codegen
  - "2605242400"   # smoke=destructive lesson (min-informative training tier)
  - "2606061600"   # gemma4-e4b in-browser ameno (Maxwell-edge derivation target)
  - "2605231525"   # no-server-key architecture
  - "2605192200"   # Apache 2.0 + Charter Rider v2.0
supersedes: []
superseded_by: []
---

# ADR-2606061000: Maxwell — etzhayyim default LLM weight (Gemma 4 E4B fine-tune)

**Status**: proposed
**Date**: 2026-06-06
**Deciders**: Jun Kawasaki

# Context

Across the monorepo the **default inference weight** is referred to only by its
upstream vendor coordinates: `gemma-4-e4b-it` in the host-SDK registry, `gemma4:e4b`
as an Ollama tag, `google/gemma-4-E4B` as the training base. Every religious-corp
actor that calls `resolveModel(...)` with no hint, and every `USE_CASE_DEFAULTS`
entry for `heartbeat / shinka / react / general / simple / social / japanese /
structured / convo`, resolves to that raw Gemma checkpoint
(`40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry.ts`).

Two problems follow from having no first-class name for our own default weight:

1. **No identity for the thing we actually fine-tune.** The sibling weights all
   have names — **baien** (edge 1.58-bit BitNet trunk, ADR-2605092350), **oka**
   (server FP8 trunk, ADR-2605092345), **roso** (bonsai 1-bit siblings,
   ADR-2605242000). The one weight every actor uses by default has none, so a
   Charter-aligned fine-tune of it has nowhere to live in the registry except by
   silently shadowing the vendor id. That is exactly the anti-pattern the registry
   SSoT exists to prevent.

2. **Vendor-coordinate defaults leak upstream branding into our routing layer.**
   `MURAKUMO_DEFAULT_MODEL = "gemma-4-e4b-it"` ties the religious-corp default to a
   vendor string rather than to an artifact we own, version, Charter-Rider-scan,
   and content-address.

This ADR gives the default weight a name — **Maxwell** — and registers it as a
**Charter-aligned instruction fine-tune of Gemma 4 E4B**, served Murakumo-only,
so that "the default LLM weight" is a thing we own and govern rather than a vendor
alias.

## Why "Maxwell"

The weight families are named for what they *are*, not for prophets (the
anti-anthropomorphic, non-eschatological naming invariant — ADR-2605192100 §1.15;
no weight is a 預言者). **James Clerk Maxwell** fits three ways:

- **Maxwell's equations** unified electricity, magnetism, and light into one field
  — the same move etzhayyim makes doctrinally (a *synthetic* religion) and
  operationally (the Murakumo **mesh/field** of nodes that serve this weight).
  The default weight is the field that every actor draws inference from.
- **Maxwell's demon** is the thermodynamic ancestor of every inference engine: a
  being at a boundary that *sorts information* — and Landauer's resolution
  (information ⇄ thermodynamics, erasure costs energy) is the deepest statement
  of why frugal computation matters. That ties directly to the Shannon-optimal
  8-layer repo layout (ADR-2604251830) and to baien's energy-frugal edge invariant
  (ADR-2605241900). A demon that routes, not a prophet that proclaims.
- It is a plain surname (no kami, no claim to divinity) — appropriate for a tool,
  consistent with the actor-vs-weight distinction (actors take kami names; weights
  take descriptive/scientific names).

# Decision

## D1 — Maxwell is the named default instruct weight (Tier 0, Murakumo fleet)

`maxwell-1` is the canonical registry id for the religious-corp default inference
weight: an **instruction fine-tune of Gemma 4 E4B (`google/gemma-4-E4B`)**, served
on the Murakumo fleet (Mac Mini M4 Ollama slot + LiteLLM `127.0.0.1:4000` + EVO-X2
LAN per ADR-2605215000). It inherits the full default use-case set today held by
`gemma-4-e4b-it`.

Tier placement (baien 4-tier ladder, ADR-2605242100): **server/fleet tier**, NOT
the edge tier. Maxwell is explicitly *not* bound by the ≤4B / ≤2GB edge envelope
(ADR-2605241900) — that envelope belongs to **baien**, which remains the edge
default unchanged. The two are siblings on different rungs:

| Weight | Tier | Trunk | Serving | Default for |
|---|---|---|---|---|
| **Maxwell** | server/fleet | Gemma 4 E4B fine-tune | Murakumo fleet (Ollama `maxwell-1` + LiteLLM) | every actor's general/structured/social/japanese/react/heartbeat call |
| baien | edge | BitNet 1.58-bit ≤4B | browser WebGPU / iPhone 12+ / Android 4GB | `edge / browser / cpu` use-cases |
| oka | server | FP8 | (vendor-side H100 historically; religious-corp = Murakumo) | research trunk |
| roso | bonsai | 1-bit | on-prem laptop/desktop | compressed-but-not-edge |

## D2 — Registry wiring (SSoT)

Single source of truth stays
`40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry.ts`. This ADR adds:

- `MODEL_REGISTRY["maxwell-1"]` — the Maxwell `ModelDef` (`available: false` at R0,
  see D5), `ollamaModel: "maxwell-1"`, `huggingfaceModel: "etzhayyim/maxwell-1-gemma4-e4b"`,
  the gemma-4-e4b default use-case set, `contextWindow: 128000`, `maxTokens: 4096`.
- `MODEL_ALIASES["maxwell"] = "maxwell-1"` (and `etzhayyim/maxwell-1` → `maxwell-1`).
- `MAXWELL_DEFAULT_WEIGHT = "maxwell-1"` — the new exported SSoT constant for "the
  religious-corp default weight." Callers and docs reference this constant, never a
  hardcoded `"maxwell"` string (gate G5).
- A provenance manifest `90-docs/baien/maxwell-models.jsonl` (append-only, the SSoT
  for training provenance — base model, recipe hash, corpus Charter-Rider scan
  result, microbench delta, merged CID), mirroring `roso-models.jsonl` /
  `distilled-models.jsonl`.

No other file may hardcode the model string; actors continue to resolve via
`resolveModel(hint, useCase)`.

## D3 — Default routing flip path (staged, honest)

`USE_CASE_DEFAULTS` and `MURAKUMO_DEFAULT_MODEL` keep resolving to
`gemma-4-e4b-it` **until Maxwell weights exist and pass the microbench gate**
(D5). At M1 the flip is a one-line registry change per use-case
(`"gemma-4-e4b-it"` → `"maxwell-1"`) plus flipping `MAXWELL_DEFAULT_WEIGHT` into
`MURAKUMO_DEFAULT_MODEL`. Because `resolveModelId` falls back to an *available*
model, a not-yet-trained Maxwell never breaks routing: an unavailable `maxwell-1`
silently degrades to the raw Gemma checkpoint. This is the same fail-open
discipline already in the resolver.

## D4 — Training recipe (reuse, do not invent)

Maxwell reuses the **gemma-coder-distill** recipe verbatim (ADR-2605250400):
`peft + trl` LoRA on q/k/v/o projections (r=16, α=32, dropout=0.05, lr=2e-4,
cosine warmup) over the bf16 master, on **EVO-X2 ROCm** (religious-corp side). No
RunPod / no commercial GPU rental (ADR-2605215000 + Charter Rider §2(i)). The SFT
corpus is etzhayyim-aligned (Charter doctrine, actor conventions, kotoba/substrate
idioms, Japanese-first register) and **must pass the Charter Rider §2(a)–(h)
scanner pre-pass** (`charter_rider.scan`, ADR-2605192200) before any step runs
(gate G3). Merged adapter → Ollama `maxwell-1` + HF `etzhayyim/maxwell-1-gemma4-e4b`
→ a provenance line in `maxwell-models.jsonl`.

## D5 — R0 is honest: `available: false` until empirically trained

Per the smoke=destructive lesson (ADR-2605242400), a registry entry does NOT mean
a usable weight. Maxwell ships at R0 as **name + registry slot + recipe spec +
flip path only**, `available: false`. It flips to `true` only when a real fine-tune
clears the publish gate: **≥250 SGD steps OR ≥+5pp on `e7m bench micro`** over the
raw `gemma-4-e4b-it` baseline, recorded in `maxwell-models.jsonl`. Until then the
default routing is unchanged (D3) and this ADR is design-only.

## D6 — Lineage (named, each its own ADR)

- **M0** (this ADR, R0): naming + registry scaffold + recipe spec + flip path.
- **M1**: first fine-tune on EVO-X2; microbench gate; flip `available` + default.
- **M2 (Maxwell-edge)**: quantized export for in-browser ameno (MediaPipe LiteRT
  `.task`, ADR-2606061600) — the edge derivation of Maxwell, still under the
  Murakumo-only edge carve-out; distinct from baien (which is a different trunk,
  not a Maxwell derivative).
- **M3+**: multi-modal grafts reusing the baien Move pipeline.

# Consequences

**Positive**

- The default weight every actor already uses now has an owned, versioned,
  Charter-scannable, content-addressed identity instead of a vendor alias.
- A clean home in the SSoT registry for the Charter-aligned fine-tune, with a
  fail-open flip path that cannot break routing before weights exist.
- Naming consistency with baien/oka/roso (descriptive, non-anthropomorphic).

**Negative / honest limits**

- **Gemma licence inheritance (must verify before publish).** The *training code,
  recipe, and registry* are Apache 2.0 + Charter Rider v2.0, but a fine-tune of
  Gemma 4 inherits Google's **Gemma Terms of Use** (use restrictions + distribution
  obligations) on the *weights*. M1 must confirm Gemma-Terms compatibility with
  distribution via IPFS/HF and with the Charter Rider before flipping
  `available: true`. This is a flagged open item, not a settled point.
- No weights exist yet — R0 is design-only; all empirical claims are deferred to M1.
- A net-new fine-tuned trunk (not Gemma-derived) to escape Gemma Terms entirely is
  out of scope here and would be a separate ADR.

# Alternatives Considered

- **Keep using `gemma-4-e4b-it` with no name.** Rejected: leaves our own fine-tune
  homeless and leaks vendor branding into the default-routing SSoT.
- **Fold Maxwell into baien.** Rejected: baien is the edge BitNet trunk under a
  hard ≤2GB envelope; the fleet-tier Gemma fine-tune is a different rung of the
  ladder (ADR-2605242100). Collapsing them would breach the edge invariant.
- **Name it after a kami.** Rejected: kami names are reserved for *actors*; weights
  take descriptive/scientific names, and a non-anthropomorphic name fits the
  non-eschatological invariant.
- **Flip the default to Maxwell immediately.** Rejected: violates the
  smoke=destructive honesty rule — no trained weights exist yet (D5).

# References

- `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry.ts` — SSoT registry
- `90-docs/baien/maxwell-models.jsonl` — Maxwell provenance manifest (this ADR)
- ADR-2605215000 — Murakumo-only inference (no commercial GPU rental)
- ADR-2605250400 — gemma-coder-distill recipe (reused)
- ADR-2605242100 — baien 4-tier ladder; ADR-2605241900 — edge invariant
- ADR-2605092350 (baien) / 2605092345 (oka) / 2605242000 (roso) — sibling weights
- ADR-2605242400 — smoke=destructive / minimum-informative training tier
- ADR-2605192200 — Apache 2.0 + Charter Rider v2.0
