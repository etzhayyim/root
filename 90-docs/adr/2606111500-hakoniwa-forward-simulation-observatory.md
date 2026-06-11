---
id: adr-2606111500-hakoniwa-forward-simulation-observatory
title: "ADR-2606111500: hakoniwa 箱庭 — forward-simulation observatory (synthetic-persona swarm; the charter-clean inversion of a MiroFish-class prediction engine)"
status: accepted
doc_type: adr
topic: hakoniwa-forward-simulation-observatory
authoritative: true
last_verified: 2026-06-11
priority: 6.0
axis: actor
weight: 0.6
priority_note: "Answers 「666ghj/MiroFish のような群体知能で未来予測する actor は etzhayyim にあるか?」 — there was no agent-based social-simulation forecaster; entity-as-actor mirrors are static and mitooshi only SCORES. hakoniwa is the missing generative layer: it runs a CONTAINED box of FICTIONAL latent personas to produce a DISTRIBUTION that mitooshi scores. Charter-clean by construction under ADR-2606111400 (synthetic-persona carve-in): no-PII synthetic agents (G1) + distribution-only (G2) + non-steering (G3) + transparent/reciprocal (G4). ZERO Tier-0 amendments."
authoritative_for:
  - "hakoniwa actor scope (agent-based forward simulation over a synthetic-persona box → outcome distribution; design + deterministic engine)"
  - "the synthetic-persona invariant (:persona/synthetic true; no PII; real persons unrepresentable, enforced at load)"
  - "the distribution-only simulation-output invariant (:forecast/point-asserted structurally false; feeds mitooshi proper-scoring)"
depends_on:
  - 2606111400
  - 2606051800
  - 2606042330
  - 2606091200
  - 2605242600
  - 2605241900
  - 2605215000
  - 2605312345
  - 2605231525
  - 2605181100
related:
  - 2606071600
  - 2606061500
  - 2605263200
  - 2605262130
supersedes: []
superseded_by: []
---

# ADR-2606111500: hakoniwa 箱庭 — forward-simulation observatory (synthetic-persona swarm)

**Status**: accepted
**Date**: 2026-06-11
**Deciders**: Jun Kawasaki

# Context

The question: *「`666ghj/MiroFish` のような群体知能 (swarm-intelligence) で未来予測する actor は
etzhayyim にあるか?」* MiroFish builds a "parallel digital world" of thousands of LLM personas
extracted from real-world information, runs them forward, and reports how an event or public
opinion will unfold (Python + Vue, Zep Cloud memory, OpenAI-compatible API, AGPL-3.0).

**The honest pre-state (verified by full-roster survey):** there is **no equivalent**. The
roster has three *adjacent* pieces that do not compose into one:

- **entity-as-actor** (ADR-2606042330) — ~29k keyless mirror-actors of real public entities,
  but a **static** observational mirror; it does not simulate anything forward.
- **mitooshi 見通し** (ADR-2606051800) — a probabilistic forecasting observatory with a
  leak-free fact→error→weight→learn proper-scoring loop, but **no generative simulation
  engine**; it *scores* forecasts, it does not *produce* them from an agent model.
- **Shibuya digital-twin** (kami-genesis) — multi-agent **physical** simulation, not a social /
  opinion forward model.

The naive way to close the gap — model real people to predict (and implicitly steer) opinion —
is exactly the surveillance-capitalism shape the Charter rejects. The corrected reading
(ADR-2606111400) is that the obstacle is **real-person modelling**, not simulation as such:
a box of **fictional latent personas** that map to no natural person is **not surveillance at
all**. ADR-2606111400 ratified that distinction and authorized this actor.

# Decision

Introduce **hakoniwa 箱庭** ("a contained miniature garden / sandtray world"), a **Tier-B
forward-simulation observatory** — the **charter-clean inversion** of a MiroFish-class engine —
that runs a **contained box of FICTIONAL latent personas** forward and reads out a
**DISTRIBUTION over possible futures**, routed to **resilience & preparedness**. It is the
**generative front-end that feeds mitooshi 見通し**: hakoniwa produces the distributions,
mitooshi scores them leak-free.

## The inversion (point by point)

| MiroFish-class engine | hakoniwa 箱庭 | gate |
|---|---|---|
| models **real people** to predict opinion | **fictional latent personas** only; no PII; real persons unrepresentable | **G1** |
| asserts a **prediction** (a point) | asserts a **distribution** (quantiles + histogram); 非終末論 structural | **G2** |
| implicitly **steers** (persuasion / targeting) | routed to **resilience**; trade/target/manipulate/campaign unrepresentable | **G3** |
| proprietary / opaque "parallel world" | **transparent** box, plaintext-public on kotoba (相互監視) | **G4** |
| OpenAI-compatible API + Zep Cloud memory | **Murakumo-only** inference + kotoba Datom log world-state | **G5/state** |

## Architecture (the MiroFish 5-stage workflow, charter-fitted)

1. **World build** (`methods/world.py`) — load a scenario EDN into a box of `:persona` /
   `:entity` / `:signal` / `:outcome` nodes + `:influences` / `:exposed-to` / `:holds-stance` /
   `:measures` 縁. `assert_synthetic` **refuses at load** any persona not marked
   `:persona/synthetic true` or carrying a PII-class field (G1, mechanical).
2. **Persona ensemble** (`methods/simulate.py` topology) — synthetic cohort archetypes with
   susceptibility λ, anchor stance, and a fictional cohort label. (MiroFish's persona
   generation, but fictional-by-construction.)
3. **Forward simulation** (`methods/simulate.py`) — **Friedkin-Johnsen opinion dynamics**
   `x_i(t+1) = λ_i·Σ_j w_ij·x_j(t) + (1−λ_i)·a_i` over the box, with signals injecting anchor
   pushes at their activation step. **K replicas** with **deterministic seeded jitter**
   (`sha256`, no `Math.random`) make the run an **ensemble**, not a single trajectory.
4. **Distribution readout** (`methods/distribution.py`) — the ensemble of town-wide statistics
   → quantiles + histogram → a **mitooshi-shaped `:forecast/kind :distribution` record**
   (`:forecast/point-asserted false`, `:forecast/use :preparedness`). (MiroFish's ReportAgent,
   but distribution-only.)
5. **Replay / interaction** — the whole box + step log is on the kotoba Datom log
   (`methods/datom_emit.py`), queryable and transparent. (MiroFish's "chat with the simulated
   world", but plaintext-public and read-only.)

The **R0 engine is deterministic** (no LLM in the path) so the invariants are testable. The
**LLM-persona variant** (G5, gated) swaps the scalar update for a Murakumo-routed persona step
with the swarm on baien-edge (ADR-2605242600 / 2605241900); the interface and gates are
identical.

## Hard gates

- **G1 — FICTIONAL latent personas only, NEVER a real-person model.** `:persona/synthetic
  true`; no PII / no real-person profile / no re-identifiable trait; real already-public
  entities appear only as their existing public mirror (ADR-2606042330). Enforced at load.
- **G2 — DISTRIBUTION-ONLY** (inherits mitooshi G1). Output is a distribution; no
  `:forecast/point` field exists; `:forecast/point-asserted` structurally false. 非終末論.
- **G3 — NON-STEERING** (inherits mitooshi G2). Resilience-only use enum; trade / wager /
  position / target / manipulate / campaign unrepresentable (a breach raises).
- **G4 — TRANSPARENT & RECIPROCAL** (ADR-2606082400 + 2606111400). Whole box plaintext-public;
  open-source + on-chain + 1 SBT = 1 vote.
- **G5 — Murakumo-only inference** (ADR-2605215000); swarm on baien-edge.
- **G6 — sourcing honesty.** Personas `:synthetic`; real facts `:authoritative |
  :representative`; a box is illustrative, never an exhaustive real-population model.
- **G7 — leak-free as-of** (inherits mitooshi G5). `:forecast/as-of`; no future leakage;
  mitooshi scores it leak-free.
- **G8 — outward-gated & no-server-key** (ADR-2605231525). R0 = engine + seed + tests; live
  large-swarm runs, real-entity ingest, and any social emission are Council + operator-DID
  gated; no platform-held key signs an artifact.

# Consequences

- **Positive**: closes the agent-based-forecasting gap with a single coherent inversion; gives
  mitooshi the generative engine it lacked; reuses the rasen/inochi pure-stdlib pywasm method
  pattern (deterministic, 13 tests green, network-free); the synthetic-persona discipline is a
  *mechanical* load-time gate, not just a doctrine. Resilience-aligned (sonae / kazaori).
- **Negative / risks**: the "model real people" hazard is permanent — it is held off by the G1
  load assertion and the ADR-2606111400 hard line (real-person modelling is explicitly outside
  the carve-in and, with PII, routes through ADR-2605181100 envelopes; it must never be bolted
  onto hakoniwa). Calibration of a synthetic box to a real population is **not** claimed — the
  output is a distribution over a *modelled* box, scored by mitooshi against realised outcomes;
  skill is earned, never asserted.
- **Status**: 🟡 R0 — design + deterministic engine + 13 tests. LLM-persona swarm + live runs
  gated (G8).

# Alternatives Considered

- **Extend mitooshi with a simulation cell instead of a new actor.** Rejected: mitooshi's
  invariant is *non-generative scoring*; bolting a generative agent engine onto it would blur a
  clean boundary. Two actors with a typed `:forecast/kind :distribution` handoff is cleaner.
- **Model real public figures' stated positions as the personas.** Rejected: that is real-person
  modelling — outside the ADR-2606111400 carve-in. Public *entities* may be mirrored (G1), but
  the *agents* in the box are fictional archetypes.
- **Emit a single expected-value prediction (point).** Rejected: violates G2 / 非終末論. The box
  is uncertain by construction; the honest output is its distribution.
- **Vendor the MiroFish code (AGPL-3.0).** Rejected for R0: clean-room is simpler than AGPL
  isolation (cf. manako weight-isolation), and MiroFish's real-person extraction + cloud-memory
  + OpenAI-API path is exactly what the gates forbid; only the *shape* (5-stage agent forecast)
  is reused.

# References

- ADR-2606111400 (synthetic-persona / forward-simulation charter carve-in — the authorizing basis)
- ADR-2606051800 (mitooshi 見通し — distribution-only + non-speculative + leak-free proper-scoring; hakoniwa feeds it)
- ADR-2606042330 (entity-as-actor — already-public entity mirrors) · ADR-2606091200 (sonae 備え — resilience consumer) · ADR-2605263200 (kazaori 風折 — disaster response)
- ADR-2606071600 (sukashi — synthesized fictional entities) · ADR-2606061500 (tsumugi — latent influence nodes)
- ADR-2605242600 / 2605241900 (baien-edge swarm) · ADR-2605215000 (Murakumo-only) · ADR-2605312345 (Datom canonical state) · ADR-2605231525 (no-server-key) · ADR-2605181100 (PII envelope)
- `20-actors/hakoniwa/` (actor: CLAUDE.md · manifest.jsonld · deps.toml · data/seed-scenario.kotoba.edn · methods/{world,simulate,distribution,datom_emit}.py · tests/{test_simulate,test_distribution}.py · wasm/README.md · out/*) + `00-contracts/schemas/hakoniwa-scenario-ontology.kotoba.edn`
- upstream shape reference: `github.com/666ghj/MiroFish` (swarm-intelligence prediction engine; AGPL-3.0)
