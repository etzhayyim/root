---
id: adr-2606211200-energy-order-protocol
title: "ADR-2606211200: Energy Order Protocol — Proof-of-Useful-Flow actor suite (澪/撓/燠/樋/委)"
status: proposed
doc_type: adr
topic: energy-order-protocol
authoritative: true
last_verified: 2026-06-21
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/mio
  - energy-order-protocol-suite
depends_on: []
related:
  - 2606071500
  - 2605261100
  - 2606051800
  - 2606072201
  - 2606111400
  - 2605262130
  - 2605312345
  - 2606172359
supersedes: []
superseded_by: []
---

# ADR-2606211200: Energy Order Protocol — Proof-of-Useful-Flow actor suite (澪/撓/燠/樋/委)

**Status**: proposed
**Date**: 2026-06-21
**Deciders**: Jun Kawasaki

# Context

Bitcoin's lasting lesson is not "information became energy" but the reverse: it used
**physical cost (electricity + compute + network + difficulty adjustment) to fix ORDER
into information space** — an unforgeable ledger, digital scarcity, time-ordering,
economic coordination, and waste heat. Proof of Work made *consumed* energy the basis of
scarcity.

The generalizable principle: **routing an unorganized physical flow through an information
protocol with verification + incentives produces new scarcity, trust, order, and markets.**
Applied forward, the next engine inverts the direction — **use information to put
verifiable order onto physical energy-flow itself**: `Hashrate → Flowrate`,
`Proof of Work → Proof of Useful Flow`.

The roster already has the *body* and adjacent observatories — `hikari 光` (energy
gen/storage/grid), `mitooshi 見通し` (forecast distributions), `kasa 嵩` (compute-capacity
growth), `shionome 潮目` (capital flows), `funamori 舫` (salinity-gradient power) — but no
actor that **orders, verifies, and accounts energy-flow** as the unit of value. The hardest
part is **verification** (additionality / baseline / double-counting / leakage): the swamp
that sank voluntary carbon credits. An Energy-Order engine that cannot verify rots on
contact.

# Decision

Introduce the **Energy Order Protocol** — a five-actor suite that decomposes the engine
pipeline `information-investment → prediction → controllability → flow-ordering →
verifiable value → reinvestment`. All five are **OBSERVATION / COORDINATION / VERIFICATION
only**; actuation stays with `hikari` under Council gate (no-server-key, like
GPU/inference, force, and land).

| actor | glyph | theory | asset class | role |
|---|---|---|---|---|
| **澪 mio** | 澪 (ordered channel) | Proof of Useful Flow / Entropy-Reduction Ledger / §9 verification | verification | **backbone** — verify flow-improvement claims, account the org "Flowrate" |
| **撓 tawami** | 撓 (flexure) | Proof of Flexibility | flexibility | "right to bend future flows" KG (DER/EV/battery/HVAC/datacenter shiftability) |
| **燠 okibi** | 燠 (residual heat) | Thermal Matching Market | coordination | waste-heat source ↔ heat-demand local matching observatory |
| **樋 toi** | 樋 (conduit) | Compute as Thermal Routing | coordination | route deferrable compute to surplus-renewable × heat-demand × cooling-efficiency sinks |
| **委 yudane** | 委 (entrust) | Human Intention Energy Engine | meaning-translation | consented member intention → aggregate energy variables (most charter-sensitive) |

**The pivot, fixed in code (mio G1):** the basis of reward is **ORDERED flow, never
CONSUMED energy**. There is no `:consumed-reward` attribute and never may be one;
`useful-flow-score` is 0 unless a claim is `:verified`; only `:verified` routes to
`:reward`. This is the whole difference from PoW.

**Verification is the defining gate (mio G2).** A flow-improvement claim reaches
`:verified` (and may earn) only with all five §9 facts AND
`verification-confidence ≥ threshold`:

- `:baseline-method` — the counterfactual the delta is measured against
- `:additionality ≥ 0.3` — it would not have happened anyway
- `:measurement-source` — a *trusted* measurement (`:self-report` weight 0.3 alone cannot verify)
- `:double-count-key` unique — the same saving is not counted twice
- `:leakage ≤ 0.5` — not offset by increased emissions elsewhere

where `verification-confidence = measurement-weight × additionality × (1 − leakage)` and
`useful-flow-score = order-delta-kWh × confidence`. The verified-flow total is the org's
**Flowrate** — the hashrate analogue.

**Suite topology.** `撓/燠/樋/委` (and `hikari`) submit claims; `澪 mio` is the shared
verification + accounting SSoT; verified outcomes route to `:reward` (advisory →
1 SBT=1 vote + TitheRouter) and to `hikari` for actuation under Council gate. `mitooshi`
feeds forecast distributions; `kanae` renders; `kasa`/Murakumo `fleet.toml` ground `樋`.

**委 yudane is gated three ways** because it alone touches human data: an `ibuki`-style
revocable CACAO leash (consent), `mimamori`-style degeneration-series unrepresentability
(no denunciation / no score / symmetric visibility), and Rider §2(c) reciprocity. Its
claims are content-free aggregates — `:mio.person/*` is structurally absent. It is
implemented last; a safe 4-actor R0 (澪/撓/燠/樋) is acceptable if consent design is not yet
settled.

## Status (this ADR)

- **澪 mio — R0 LANDED (2026-06-21).** `20-actors/mio/` clj-native: manifest + ontology +
  15-claim seed (6 flow classes, mixed provenance) + `mio_edn`/`analyze`/`kotoba`/`autorun`
  methods + content-addressed append-only verification ledger (verify-chain tamper-evident,
  idempotent-by-content heartbeat). **24 tests / 174 assertions green** (babashka). Seed
  result: 15 claims → 9 verified, Flowrate 37313.778 kWh-equiv, 1 double-count rejected,
  1 leakage rejected, 4 insufficient-evidence. G1 backbone proven (no `:consumed-reward`;
  score 0 unless verified).
- **撓 tawami — R0 LANDED (2026-06-21).** `20-actors/tawami/` clj-native (flexibility
  leg): manifest + ontology + 12-asset seed (6 resource classes) + `tawami_edn`/`analyze`/
  `kotoba`/`autorun` + flexibility commit-DAG ledger. **20 tests / 134 assertions green**.
  Seed result: 12 assets → total flex-value 5472.6 kWh-equiv (fast-flex 3582.75 across 6).
  flex-value = energy-capacity × availability × responsiveness × time-shift weight; each
  asset tiered + assigned a best-use mio flow-class. G1 proven (no `:tawami/dispatch`;
  map-not-dispatch). R1 seam = emit a 澪 mio flow-improvement claim when a flexibility is used.
- **燠 okibi — R0 LANDED (2026-06-21).** `20-actors/okibi/` clj-native (waste-heat leg):
  manifest + ontology (source + sink kinds) + seed (4 sources / 6 sinks) + `okibi_edn`/
  `analyze`/`kotoba`/`autorun` + thermal-matching commit-DAG ledger. **21 tests / 92
  assertions green**. Matching gated by the temperature cascade (source ≥ sink-req +
  approach) AND distance (≤ 5 km); greedy allocation by quality. Seed result: 4 matches,
  1138.5 kW matched, 409.0 kW surplus, 238.4 kW unmet (absorption-f by cascade, spaceheat-e
  by distance). G2 proven (infeasible pairs never match; cooling-load is not a heat sink).
- **樋 toi — R0 LANDED (2026-06-21).** `20-actors/toi/` clj-native (compute leg):
  manifest + ontology (job + site kinds) + seed (6 jobs / 5 sites) + `toi_edn`/`analyze`/
  `kotoba`/`autorun` + routing commit-DAG ledger. **21 tests / 98 assertions green**.
  Routes deferrable compute by site-score (carbon / surplus-renewable / cooling /
  heat-sink / transparency); Murakumo default-preferred (G2). Seed result: 5 routed,
  1422 kgCO2 avoided, 1900 kWh waste heat reusable (→ okibi), commercial GPU unused
  (score 0.055), pinned job stays in-place. G1 proven (no `:toi/dispatch`; map-not-job-kill).
- **委 yudane — R0 LANDED (2026-06-21).** `20-actors/yudane/` clj-native (intention leg):
  manifest + ontology (offer kind; negative space = the surveillance degeneration series)
  + seed (8 offers: 4 consent + 4 refusal) + `yudane_edn`/`analyze`/`kotoba`/`autorun` +
  content-free intention commit-DAG ledger. **21 tests / 96 assertions green**. Consented,
  aggregate cohort intention → flex offer, gated by a member-signed revocable capability +
  k-anonymity floor + reciprocity. Seed result: 4 consented (12800 kWh aggregate flex),
  4 refused (one per gate: k-anon / no-cap / expired / non-reciprocal). G1/G2 proven
  (consent-bound + content-free; no per-person field; the degeneration series
  五人組→隣組→Stasi→social-credit is unrepresentable).

## Suite complete (5/5, 2026-06-21)

All five Energy Order Protocol actors are R0 LANDED + green: **澪 mio** (verification
backbone, 24/174) · **撓 tawami** (flexibility, 20/134) · **燠 okibi** (waste-heat, 21/92)
· **樋 toi** (compute-routing, 21/98) · **委 yudane** (intention, 21/96). Total **107 tests
/ 594 assertions green** (babashka). The energy-flow-ordering loop is closed: 撓/燠/樋/委
observe and submit; 澪 mio verifies + accounts the org Flowrate; hikari actuates under
Council gate. R1 across the suite = the claim-emitter seam (each leg → a 澪 mio
flow-improvement claim) + live operator-gated ingest + fleet registration.

# Consequences

- The org gains a single, auditable definition of "useful energy work done" that is
  scarcity-bearing without being a market signal — a resilience/reward map, never a trade.
- Verification rigor is structural, not aspirational: unverifiable claims cannot earn, so
  the carbon-credit failure mode is closed by construction (and by test).
- New surface to defend: `委 yudane`'s consent membrane. Mitigated by the three-way gate
  and by shipping it last.
- mio is now a dependency hub for four future actors + `hikari`; its ontology/ledger format
  is an interface contract (versioned in `ontology.mio.edn`).

# Alternatives Considered

- **Reuse PoW directly (mine for order).** Rejected — PoW's scarcity is from *consumption*,
  the exact thing this suite must not reward (G1).
- **A single mega-actor.** Rejected — flexibility / waste-heat / compute-routing / intention
  have different data, gates, and risk (intention is human-data-sensitive); they decompose
  cleanly into mirrors over one verification backbone (the inochi-mirror : sanae-body shape).
- **Let mitooshi own it.** Rejected — mitooshi owns forecast *distributions*; mio owns
  *realized verified flow*. Distinct roles; mio consumes mitooshi.
- **Defer verification to R1.** Rejected — verification is the value; without it the ledger
  is theater. It is the R0 core.

# References

- This ADR's backbone: `20-actors/mio/` (README + CLAUDE + MATURITY)
- ADR-2605261100 (`hikari` energy body) · ADR-2606051800 (`mitooshi` forecasting) ·
  ADR-2606072201 (`shionome` capital-flow observatory, the pattern echoed)
- ADR-2606111400 (`ibuki` synthetic-persona / revocable-leash consent pattern, for 委)
- ADR-2605262130 + ADR-2605312345 (kotoba Datom log = first-class canonical state)
- ADR-2606172359 (Rider v3.5 objective-function; Murakumo default-preferred)
