---
id: adr-2606172200-shinka-loop-c-architecture-evolution
title: "ADR-2606172200: Shinka Loop C — architecture evolution (NAS-via-Co-scientist on Murakumo)"
status: proposed
doc_type: adr
topic: shinka-architecture-evolution
authoritative: true
priority: 6.5
axis: ml
weight: 0.65
priority_note: "Adds the third Shinka loop — evolving the model ARCHITECTURE itself (not just capability+weight), under the strongest leash; high reuse across the weight family."
authoritative_for:
  - shinka-loop-c-architecture-evolution
  - architecture-search-governance
last_verified: 2026-06-17
depends_on:
  - "2606142200"   # Shinka self-evolution engine (Loop A capability + Loop B weight) — parent
  - "2606130900"   # Maxwell RSi ecosystem (Loop B train→eval→deploy reused for finalists)
  - "2606111400"   # revocable CACAO leash (member-signed capability) — the promotion gate
  - "2605215000"   # Murakumo-only inference/compute
  - "2605192200"   # Apache 2.0 + Charter Rider (§2 scan on generated arch code)
related:
  - "2606061000"   # Maxwell (AR E4B) — search-space member
  - "2606171100"   # maxwell-diffusion — search-space member
  - "2605250700"   # oka MMSheaf (sheaf diffusion) — search-space member
  - "2605092350"   # baien BitNet 1.58 — search-space member
  - "research-2606171800-weight-family-generalization-physics"   # fitness tooling (real loss-landscape / sharpness)
supersedes: []
superseded_by: []
---

# ADR-2606172200: Shinka Loop C — architecture evolution (NAS-via-Co-scientist on Murakumo)

**Status**: proposed
**Date**: 2026-06-17
**Deciders**: Jun Kawasaki

# Context

Shinka (ADR-2606142200) defines two evolution loops: **Loop A** evolves *capability*
(Co-scientist cells over artifacts/code/hypotheses) and **Loop B** evolves *the weight*
(Robin/RSi: corpus → SFT → eval → deploy). Neither evolves the **model architecture
itself** — layer topology, attention/MoE configuration, or the choice among the weight
family (AR `maxwell-1` / `maxwell-diffusion` / `oka`-sheaf / `baien`-BitNet). Those
siblings exist as **ADR-decided** options, not an evolvable search space.

The Google **AI co-scientist** that Shinka mirrors also does *not* search architectures —
it evolves research *hypotheses* via a multi-agent generate/reflect/rank/evolve tournament.
So faithfully mirroring co-scientist (Loop A) yields *strategy* evolution, never NAS.

Two recent results make architecture evolution tractable to *govern* now:

1. The **weight-family-as-traversal-operators** framing (research note 2606171800):
   architecture is precisely *how* a model traverses the generalization energy landscape
   (oka = terrain / sheaf relaxation, maxwell-diffusion = annealed dynamics, baien =
   compressed destination). Choosing/recombining it is an optimization the same tournament
   machinery can drive.
2. A **real fitness signal** now exists: the measured loss-landscape + sharpness tooling
   (`loss_landscape.py`, Hessian/basin-width) + microbench + tok/s — built on real weights.

This ADR adds **Loop C — architecture evolution** as a third loop, reusing Loop A's
Pregel cells and Loop B's training, under the *strongest* leash (architecture
self-modification is the deepest form of self-modification).

# Decision

## D1 — Loop C exists, reusing the Co-scientist cells over architecture candidates

A third loop runs the same Pregel cells as Loop A, but the population is **architecture
genotypes** instead of hypotheses:

| Co-scientist / Shinka cell | Loop-C function |
|---|---|
| Generation → `propose` | emit candidate architecture genotypes (mutations / novel specs) |
| Reflection → `critic` | feasibility + Charter Rider §2 scan + cost estimate; reject infeasible |
| Ranking → `tournament` | Elo over candidates by the tiered fitness (D3) |
| Proximity → `cluster` | dedup near-identical genotypes; maintain diversity |
| Evolution → `recombine` | crossover/merge top-Elo genotypes (incl. model-merge recipes) |
| Meta-review → `synthesize` | write an ADR + PR **draft**; never auto-merge (D5) |

## D2 — Search space (the genotype, an EDN spec → a `:db/add` datom)

- **(a) family** — `{:ar :diffusion :sheaf :bitnet}` (the existing siblings) or hybrids.
- **(b) config genes** — depth, width, `num_heads`/`num_kv_heads` (GQA), MoE `num_experts`/
  `top_k`, attention variant (full/sliding/window), RoPE/context, and family-specific genes
  (oka: stalk dim `d`, sheaf-graph topology, restriction-map family; diffusion: canvas length,
  denoise steps; bitnet: quantization schedule).
- **(c) merge recipes** — MatFormer elastic slice (E2B↔E4B), LoRA composition, layer
  recombination / evolutionary model-merge (Sakana-style). This is the **cheapest sub-mode**
  (no full pretrain) and the first to exercise.

The genotype is a structured, content-addressable EDN object; each candidate and its result
is appended to the kotoba Datom log.

## D3 — Tiered fitness (cost gate — do NOT train every candidate)

Architecture search is compute-prohibitive if each candidate is fully trained. Loop C is a
**cascade**; only survivors escalate:

- **T0 zero-cost** — param/FLOP budget, zero-cost NAS proxies (synflow/jacob-cov-like) +
  Charter/feasibility screen. Cheap reject of most of the population.
- **T1 elastic/surrogate** — MatFormer/elastic-submodel eval or a small surrogate, proxy-task
  microbench, **no full train**.
- **T2 short-SFT** — a short LoRA-SFT then: microbench score + **real loss-landscape sharpness**
  (Hessian top-eigenvalue / basin width, research 2606171800 tooling) + tok/s. Flatness↔
  generalization is a measured fitness term, not a guess.
- **T3 full RSi** — only the Elo **finalists** run the full Loop-B train (ADR-2606130900).

Elo accrues across tiers; a candidate that wins cheaply earns the right to expensive eval.

## D4 — Flywheel coupling (Loop C feeds A and B)

A Loop-C **winner** becomes (i) a new **weight target** handed to Loop B (train it), and (ii) a
registered **family sibling** (`available:false` until human-gated). A Loop-A capability gap can
*propose* arch genes (e.g., "structured-output failures → try more KV heads"). Loop-C provenance
(every genotype + fitness) is itself corpus/evidence for the others. The three loops share one
fabric (Murakumo) and one ledger (the Datom log).

## D5 — Invariants (strongest leash — this is the deepest self-modification)

- **I1 — append-only evidence.** Every candidate genotype, every fitness measurement, every
  tournament result is a `:db/add` datom. The architecture-evolution history is immutable evidence.
- **I2 — NO autonomous merge or deploy.** `synthesize` emits a *PR draft + ADR* only. Promoting an
  architecture to a *trainable* target (T3) or a *deployable* sibling requires a member's
  **CACAO-signed capability** (ADR-2606111400) — human-attributed, scoped, expiring. The engine is
  the bearer, never the signer.
- **I3 — Murakumo-only** compute (no commercial GPU; ADR-2605215000).
- **I4 — Charter Rider §2 scan** on any generated architecture *code* before it runs (ADR-2605192200).
- **I5 — fail-open.** A non-promoted candidate never touches the live model registry; the resolver
  keeps serving the current weight (`available:false` default).

## D6 — R0 is honest: schema + harness + cost-gate, NO autonomous architecture change

R0 ships: the genotype schema, the tiered-fitness harness (D3 wired to the real tooling), the
cost gate, and the Pregel-cell wiring reusing Loop A. **No novel architecture is auto-adopted.**
The first exercise is a **tournament over the existing family** (AR vs diffusion vs sheaf vs
BitNet) on the real fitness signals → a *ranked PR draft*, not an invented network. Novel-genotype
search (b)/(c) is a later, leash-gated phase.

# Consequences

- **Positive** — architecture becomes an *evaluable, evolvable, governed* object under the same
  Charter discipline as capability and weight; the real loss-landscape tooling gains a purpose
  (fitness); the weight family becomes a *measured* search space rather than an ADR opinion.
- **Honest cost** — full architecture search is expensive; the **cost gate (D3) is the crux**, and
  the highest near-term value is simply *ranking the existing family*, not inventing topologies.
- **Safety** — the deepest self-modification gets the strongest leash: no-auto-merge + CACAO + the
  immutable datom ledger. The engine can *propose* an architecture; only a consenting human promotes it.

# Alternatives Considered

1. **Keep architecture human/ADR-decided (status quo).** Rejected as a self-evolution gap — but
   retained as the *safe default* that Loop C only relaxes under an explicit member leash (D5).
2. **Full automated NAS from scratch.** Rejected — compute-prohibitive on Murakumo and unsafe to
   auto-deploy; D3's cascade + D6's "rank the family first" is the bounded form.
3. **Evolutionary model-merge only (Sakana-style, no topology search).** Adopted as the *cheapest
   first sub-mode* inside D2(c), not as the whole of Loop C.

# References

- ADR-2606142200 (Shinka self-evolution engine — Loop A capability + Loop B weight; parent)
- ADR-2606130900 (Maxwell RSi ecosystem — Loop B train→eval→deploy)
- ADR-2606111400 (revocable CACAO leash — the promotion gate)
- ADR-2605215000 (Murakumo-only compute) · ADR-2605192200 (Charter Rider §2)
- ADR-2606061000 / 2606171100 / 2605250700 / 2605092350 (the weight-family search-space members)
- research note 2606171800 (weight-family generalization physics — the real fitness tooling)
- AI co-scientist (DeepMind, multi-agent hypothesis evolution) · Sakana Evolutionary Model Merge · AlphaEvolve/ShinkaEvolve · zero-cost NAS proxies (synflow / jacobian-covariance) · Li et al. 2018 (loss-landscape fitness)
