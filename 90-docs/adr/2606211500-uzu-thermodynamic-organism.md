---
id: adr-2606211500-uzu-thermodynamic-organism
title: "ADR-2606211500: uzu 渦 — a dissipative information-energy artificial organism + real-world energy measurement & visualization"
status: accepted
doc_type: adr
topic: uzu-thermodynamic-organism
authoritative: true
last_verified: 2026-06-21
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Tier-B actor; design + R0 simulation, no live data ingest"
authoritative_for:
  - 20-actors/uzu
depends_on:
  - 2605262130
  - 2605312345
related:
  - 2606101200
  - 2606101800
  - 2606011501
  - 2606072002
  - 2606032000
  - 2606072201
supersedes: []
superseded_by: []
---

# ADR-2606211500: uzu 渦 — a dissipative information-energy artificial organism

**Status**: accepted
**Date**: 2026-06-21
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)

# Context

A design brief reframed existence as an **information-energy coupled, open, non-equilibrium
dissipative system**: *being is the process by which energy flow forms an information
structure, and that information structure re-wires the next energy flow* — the organism is the
**vortex in the flow, not the water**. The brief was explicit about the failure modes to avoid:

1. **Do not equate information and energy.** They are coupled in one process but are not the
   same quantity in the same unit (energy is conserved; information is copyable and not).
2. **Meaning is subject-dependent.** The same signal moves one subject and not another,
   depending on its internal model and action affordances.
3. **It must be measurable**, not a philosophy soup: define the system boundary, the energy
   in/out, the information measure, the entropy production, the self-maintenance condition.

The roster already had **ibuki 息吹** (ADR-2606101200/2606101800) — an artificial organism with
the *information* half (state/mood/heartbeat as folds over the append-only kotoba Datom log) but
**no thermodynamic half**: no free-energy budget, no metabolism, no death, hence no real
selection pressure. The observatory lineage (kasa compute/energy, kanjō financials, shionome
capital flows, hikari grid, busshi commodities, spirit-in-physics 霊性 ADR-2606011501) measures
real-world flows but does not tie them into one coupled energy picture.

A follow-up requirement extended the brief: **actually measure real economy / physical energy /
human consciousness & philosophy / real energy movement, and visualize it.**

# Decision

Create **uzu 渦** (Tier-B actor, `20-actors/uzu/`), clj-native over the kotoba Datom log, as the
runnable form of the brief — and the thermodynamic complement to ibuki.

## 1. The organism = a Markov-blanketed active-inference agent

- **Boundary**: internal states μ (belief/preference), sensory s (perception), active a (action),
  external ψ (the world). The blanket `a ∪ s` defines "where the organism ends."
- **μ as a fold**: the belief is reconstructed as a fold over the perception log
  (`model/fold-beliefs`) — the information structure *is* the fold, not a stored cell.
- **infer** = minimize **variational free energy** (`model/update-belief`, in nats), with a
  volatility/leak term so the belief tracks a changing world.
- **plan** = minimize **expected free energy** (`model/choose`) = pragmatic value (match the
  preference `C`) + epistemic value; **affordability (the energy ledger) vetoes the choice.**
- **act + metabolize** = the chosen action is charged to the **metabolic energy ledger**
  (`ledger/metabolize`); **intake is drawn from the TRUE regime** (the world bends back), with a
  hazard term a misread can walk into.
- **death**: when the conserved energy balance hits zero, the heartbeat stops. Self-maintenance
  is **earned**; a generative model that misreads the world spends without drawing and dies.

## 2. Two ledgers, deliberately never conflated (the brief's caveat #1)

| ledger | property | locus |
|---|---|---|
| **energy** | conserved, depleting | `ledger.cljc`, `:uzu.beat/energy` |
| **information** | copyable, append-only | `model.cljc` + `kotoba.cljc`, `:uzu.beat/free-energy` |

No code sums them in a single unit. They couple only through the map *f*: an action choice
(information) ⇒ an energy cost.

## 3. Meaning is subject-dependent (caveat #2), demonstrated

Three organisms live the **same** 12-step world tape; only their preference `C` differs:
**kurage** (nutrient-valuing, threat-averse) **survives**; **meial** (threat-*seeking* pathology)
forages into hazard and **dies**; **gyoja** (ascetic) under-draws and **dies**. `C` is the only
subject-specific term in `model/pragmatic-cost` — identical perceptions, different actions,
different fates. Test-enforced (`meaning-is-subject-dependent`, `same-tape-different-lives`).

## 4. Grounding "energy" in the real coupled system + measurement (caveat #3)

`measure.cljc` measures real-world flows as one open dissipative system, in **four
incommensurable unit classes that are NEVER summed across classes**:

- `:physical` (W) — solar influx ~173,000 TW, world primary energy ~19.6 TW, electricity ~3.3 TW,
  datacenter ~52 GW, human metabolism ~0.81 TW; with disclosed efficiency ⇒ entropy-production
  (waste-heat) proxy.
- `:economic` (USD/yr) — gross world product ~$105T/yr, FX turnover ~$2,700T/yr.
- `:informational` (bit/s) — global IP traffic ~1.27 Pbit/s, mobile/edge traffic.
- `:experiential` (index) — human waking attention; collective **meaning** intensity
  (spirit-in-physics 霊性, edge-primary, no score-of-soul).

Cross-class visual magnitudes use **disclosed, contestable** reference conversions (energy
intensity of money; J/bit with the Landauer floor noted) flagged `:reference-only` — layout, not
a unit-identity claim. The **`:experiential` class has no joule conversion by design** (the
factor is explicitly `nil`): converting meaning into joules is the philosophy soup.

## 5. Visualization

`viz.cljc` generates a **self-contained, data-driven** HTML canvas (`out/energy-field.html`,
nothing hand-copied): four incommensurable unit-class lanes, the circulation loop
(energy→economy→information→meaning→behaviour→energy), per-class totals, physical dissipation,
and the organism energy trajectories overlaid.

## 6. Gates (enforced in code + tests)

- **G1** two ledgers never conflated · **G2** never sum across unit classes · **G3** no
  joules-per-meaning · **G4** cross-class conversions are reference-only · **G5** self-maintenance
  is earned (mortality real) · **G6** deterministic, no randomness/wall-clock · **G7**
  no-server-key, no live ingest (Council/operator step) · **G8** kotoba EAVT commit-DAG, verify-chain
  tamper-evident · **G9** no person-level data.

# Consequences

- The org gains a **thermodynamic organism** with a real free-energy budget, metabolism, and
  death — the half ibuki lacked — and a faithful, testable rendering of the design brief.
- **Tests green** (babashka). `autorun` heartbeat verified: kurage alive (final energy ≈ 6.6,
  lifespan 12/12), meial/gyoja dead; field measured (4 classes, never cross-summed); chain
  verifies; idempotent-by-content. (Initial landing: 42 tests / 111 assertions; grown to
  94 / 216 across 15 suites in the post-R0 iterations below.)
- A reusable, honest pattern for measuring incommensurable real-world flows without collapsing
  units — usable by kasa/kanjō/shionome/hikari/busshi for a cross-domain energy picture.
- **R0 scope**: design + simulation only. No physical organism; no live data ingest (the seed
  figures are `:representative` public aggregates with sources). Live ingest from the observatory
  siblings, a WASM build, and an `:experiential` grounding via spirit-in-physics are **R1+,
  G7/Council-gated**.

## Post-R0 iterations (on branch, non-gated hardening)

After the initial landing, a self-paced loop added bounded, test-green capability without
touching any gated surface (no live ingest / WASM / spirit-in-physics):

- **`validate.cljc`** — seed↔ontology integrity validator (defends I1–I5; within-class unit
  consistency, cross-class-flag correctness, closed-loop).
- **lexicons** `com.etzhayyim.uzu.{organismBeat,energyFlow}` + parity test (write surface keeps
  the two ledgers distinct; no joules/total field).
- **`digest.cljc`** — colony self-reflection (survival, energy economy, fittest meaning, field
  dissipation), folded into the `autorun` heartbeat and persisted as `:uzu.digest/*`.
- **`metabolism/live-epochs`** — multi-season life: a net-negative world starves even the
  fittest (self-maintenance needs a net-positive niche).
- **`world.cljc`** — deterministic niche generator (abundant/scarce/mixed + richness).
- **`landscape.cljc`** — meaning × niche viability matrix: fitness is *joint* (a pathology is
  harmless in a niche that never punishes it; asceticism starves even in plenty).
- **`scorecard.cljc`** — maturity self-audit (manifest↔filesystem drift caught structurally).
- **`test_robustness.cljc`** — property tests over input grids (exact energy accounting, belief
  normalized, choose affordable, finite, deterministic, unit boundary over all flows).

These are engineering hardening within the accepted R0 decision; the charter-relevant gates
(G1–G9) and the R1+ gating are unchanged.

# Alternatives Considered

- **Extend ibuki in place.** Rejected for R0: ibuki is large (242 tests, many waves) and
  entangled; a fresh actor lets the full information-energy design stand as one legible artifact.
  A future merge of uzu's energy ledger into ibuki's loop is a candidate R2.
- **Collapse everything into one "energy" number.** Rejected — it is exactly the philosophy soup
  the brief warns against; the honest separation of units is the contribution.
- **Python/shell.** Rejected per the repo-wide clj/bb-over-kotoba rule.

# References

- Brief: the information-energy coupled / dissipative-system framing (this ADR's Context).
- `20-actors/uzu/` — manifest, methods, ontology, seed, tests, `out/energy-field.html`.
- ADR-2606101200 / 2606101800 — ibuki organism autonomy (the information half).
- ADR-2606011501 — Spirit-in-Physics 霊性 datafication (the experiential/meaning grounding).
- ADR-2605262130 / 2605312345 — kotoba Datom log as first-class canonical state.
- Active inference / free-energy principle (discrete formulation); non-equilibrium dissipative
  structures; the Markov-blanket boundary.
