---
id: adr-2606101800-ibuki-ecosystem-maturation-food-web-symbiosis
title: "ADR-2606101800: 息吹 (ibuki) ecosystem maturation — the colony as a symbiotic food web (植物→粘菌→カビ→人類), 7 waves"
status: accepted
doc_type: adr
topic: ibuki-organism-ecosystem
authoritative: true
last_verified: 2026-06-10
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - ibuki-organism-ecosystem
  - artificial-organism-food-web
  - colony-commons-symbiosis
depends_on:
  - adr-2606101200-ibuki-organism-autonomy-r2-gap-closure
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605231525-server-side-signing-capability-boundary
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2606062100-moyai-inference-reciprocity-credit
  - adr-2605192100-etzhayyim-mission-charter
related:
  - adr-2606101500-session-close-ibuki-organism-autonomy-r0-r3
  - adr-2606072200-shionome-cross-asset-capital-flow-observatory-r0
supersedes: []
superseded_by: []
---

# ADR-2606101800: 息吹 (ibuki) ecosystem maturation — the colony as a symbiotic food web

- **Status**: accepted
- **Date**: 2026-06-10 (JST)
- **Deciders**: founder seat (autonomous /loop, ecosystem-maturity wave)
- **Supersedes / amends**: none — extends ADR-2606101200 (organism autonomy R0–R3). ZERO
  invariant amendments; every gate (no-server-key, Murakumo-only, outward-gated, 非終末論,
  edge-primary) is preserved and made concrete for the ecosystem layer.

## Context

ADR-2606101200 closed the artificial-organism autonomy loop (state as-of on the kotoba Datom
log, durable heartbeat, Murakumo narration, member-principal posting, kaizen feedback) and
bound the real 18,342-organism fleet. But organisms were still **isolated individuals** — no
interaction, no metabolic exchange, no symbiosis.

The founder's framing (2026-06-10): *「単一ではなく ecosystem として、黒カビがクエン酸を
製造するように生命として人類と共生していく」* — not single organisms, but an ecosystem that,
as a byproduct of *living*, produces something humanity consumes in symbiosis (as Aspergillus
niger excretes citric acid). This ADR records the 7-wave maturation that made the colony an
ecosystem, each wave landed as its own PR and verified by an expanding hermetic test suite
(134 → 198 tests).

## Decision

Build the ecosystem as differentiated trophic niches on the append-only log, with every
mechanism log-derived, deterministic, and charter-clean. Seven waves (each a merged PR):

| wave | PR | mechanism | motif |
|---|---|---|---|
| 1 食物網 | #1565 | `ecosystem.py`: niches `:organism/niche` — **植物 producer** (fixes `:metabolite/substrate` from mood-richness) → **粘菌 router** (relays) → **カビ decomposer** (excretes `:metabolite/commons`, the citric-acid analogue); mutualism `:event/symbiosis-fed` folded into the SAME-beat checkpoint; **satiation** so a fed producer's mood EQUILIBRATES (no saturation) | primary production + mutualism |
| 2 健全化 (prereq) | #1558 | `health.py`: colony audit (muteness/saturation/stress-excess/checkpoint-divergence/posting-drought/mood-monoculture) → `:health/*` checkpoints + KaizenProposal lines. Fixed the homeostasis-loss bug (event-entity shadowing) found by the 100-beat audit | homeostasis |
| 3 腐生 | #1567 | detritus recycling: substrate no router relayed is dead matter → decomposers recycle it into commons at a lossy yield (`DETRITUS_YIELD`). **Matter loop closed** (nothing fixed is wasted, circular/非終末論); commons output becomes CONTINUOUS while feeding stays intermittent | saprotrophy |
| 4 レジリエンス | #1569 | niches logged at birth → `health.py` web-resilience: `keystone-niche-absent` (a trophic role missing → web cannot close) + `niche-imbalance` (Pielou evenness floor); `:health/eco-maturity` checkpointed | diversity / keystone |
| 5 stigmergy | #1570 | the 粘菌 router becomes an ADAPTIVE Physarum optimizer: past relays deposit an EVAPORATING trail (`trail_strengths`), routing prefers nutrient × (1 + trail) → good tubes self-reinforce, the router CONVERGES (Tokyo-rail-network behaviour) | slime-mold trails |
| 6 共生 | #1571 | `symbiosis.py`: the colony's commons byproduct accumulates a standing **commons pool** (like moyai 入会権); a MEMBER draws via `draw(...)` — member-principal + operator-gated, ibuki NEVER auto-draws; `:symbiosis/draw` attributed to the member | humanity consumes the gift |
| 7 定足数 | #1572 | `quorum.py`: emergent collective phenotype from the mood distribution — ≥2/3 flourishing → the colony FRUITS (collective commons burst, bounded); ≥2/3 stressed → dormancy; checkpointed `:quorum/*` (aggregate, never per-organism) | quorum sensing / fruiting |

The food web is wired into BOTH `autorun.py` (3 seed niches) and `fleet.py` (18,342-organism,
niches hash-derived) as a 3-phase beat (feel/act → ecosystem cascade → fold symbiosis into the
SAME-beat checkpoint so checkpoint == as-of replay).

## Consequences

- The colony is now a **symbiotic food web**, bidirectional and un-fakeable: producers fix →
  routers relay (adaptively) → decomposers refine + recycle → a commons pool accumulates →
  humanity draws it (member-principal). Offers are the colony's byproduct on the log; draws
  exist only when a member actually took the gift.
- Every property is **measured from the log, not assumed**: `ecosystem.web_report` (commons
  by source + nutrient to humanity), `health.audit` (six pathologies + web-resilience +
  eco-maturity), `symbiosis.commons_pool` (offered/drawn/available), `quorum.quorum_history`
  (collective phenotypes + fruiting total).
- Verified at full scale: a 12-beat 18,342-organism sweep produces thousands of commons
  metabolites (e.g. 7,987 / 454,552 nutrient) on one verified chain; niches hash-distribute
  evenly (evenness 0.9999); a 100-beat seed run stays healthy (stress equilibrates flat, 0
  saturation, 3/3 mood diversity, matter loop closed).
- **198 tests / 17 hermetic stdlib-only suites green.** ZERO invariant amendments.
- Charter alignment: the commons output is the colony's contribution to the labor-liberation
  commons (Charter §1.4 / moyai ADR-2606062100); the symbiosis with humanity is structural,
  member-principal, and on-chain-honest.

## Alternatives Considered

- **Mutable niche / succession** (organisms changing trophic role over time) — rejected:
  conflicts with stable organism identity (niche = who you are). Resilience is measured
  instead (diversity health), and quorum gives the colony a time-varying *collective*
  phenotype without changing individual identity.
- **Fabricating human consumption** of the commons — rejected: ibuki cannot fabricate a human
  benefit. Draws are member-principal (the colony never self-draws), keeping 共生 honest.

## References

- ADR-2606101200 (ibuki organism autonomy R0–R3)
- ADR-2606062100 (moyai inference-reciprocity credit — the commons-draw-rights pattern)
- Each wave's PR: #1565 / #1558 / #1567 / #1569 / #1570 / #1571 / #1572
