---
id: adr-2606161730-busshi-commodity-materials-observatory-r0
title: "ADR-2606161730: busshi (物資) — world commodity & raw-materials KG-mirror observatory (clj-native R0)"
status: accepted
doc_type: adr
topic: busshi-commodity-materials-observatory
authoritative: true
last_verified: 2026-06-16
priority: 6.0
axis: architecture
weight: 0.60
authoritative_for:
  - busshi actor identity (name, DID, namespace, scope) — clj-native R0
  - commodity & raw-materials observation gates G1..G8 + non-goals N1..N5
  - §2(l) multi-generational (子・孫) × wellbecoming risk axis as the analytical core
  - clj-native method triad (busshi_edn loader + analyze/datoms/coverage) + seed
depends_on:
  - adr-2606161700-multigenerational-extraction-risk-gate
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605192100-etzhayyim-mission-charter
related:
  - adr-2606022000-kabuto-supply-chain-kg
  - adr-2606032000-kanjo-financial-disclosure-kg
  - adr-2606072201-shionome-capital-flow-observatory
  - adr-2605252400-kanayama-circular-metallurgy-r0
  - adr-2606051500-kamado-closed-loop-carbon-refining
supersedes: []
superseded_by: []
---

# ADR-2606161730: busshi (物資) — world commodity & raw-materials KG-mirror observatory

**Status**: accepted (R0 landed, clj-native, tests green)
**Date**: 2026-06-16
**Deciders**: Jun Kawasaki

# Context

The roster mirrors the world's power and value structures (kabuto 兜 supply-chain,
kanjō 勘定 financial disclosure, kasa 嵩 compute capacity, shionome 潮目 capital
flows, rare-earth-coverage rare metals, masago 砂 materials discovery) but had **no
umbrella observatory for the world's commodities & raw materials themselves** — gold
(金), silver (銀), rare metals (レアメタル), and energy (石油/ガス/石炭) as a single
layer keyed on the material, with its supply concentration and multi-generational
risk made into queryable Datoms.

This actor is authored directly under the framing ratified the same day in
**ADR-2606161700**: extraction is **not banned** — it is judged on the
**multi-generational (子・孫) × wellbecoming risk axis**. busshi is the OBSERVATION
side of that axis (sibling of rare-earth-coverage, which now carries the same axis):
it does not mine, extract, or trade. It mirrors where material wealth concentrates
and where its multi-gen footprint is heaviest, and routes that to resilience.

The repo is in a clj-native migration phase (ADR-2606142300 / 2606152300); the user
asked for this layer "datomic, clj". busshi is therefore clj-native from R0: pure
babashka `.cljc` methods + a kotoba EDN seed + clojure.test, matching the
kakaku/meisai/kabuto `*_edn` family.

# Decision

## 1. Actor identity

| Field | Value |
|---|---|
| Name | `busshi` |
| Japanese | 物資 (ぶっし — commodities & materials / matériel); kango-named observatory sibling of kanjō/kakaku/meisai |
| DID | `did:web:etzhayyim.com:busshi` |
| Lexicon namespace | `com.etzhayyim.busshi.*` |
| Repo | `20-actors/busshi/` |
| License | Apache 2.0 + Charter Compliance Rider v3.2 |
| Kind | observation watcher — commodity & raw-materials KG mirror (clj-native) |

## 2. Scope (R0, Wave 1 = all-domains-thin)

One umbrella actor whose seed covers all five commodity classes thinly in a single
pass (depth deferred to later waves):

- **precious-metal** — gold, silver, platinum, palladium
- **base-metal** — copper, aluminium, zinc, nickel, lead, tin
- **rare-metal** — lithium, cobalt, rare-earths (agg.; detail → rare-earth-coverage), gallium, germanium, tungsten, antimony
- **energy** — crude oil, natural gas, coal, uranium
- **ag-soft** — wheat, corn, soybean, coffee, sugar

(25 commodities in the R0 seed; all figures `:representative`.)

## 3. Analytical core — §2(l) multi-gen × wellbecoming risk axis

Per commodity, derive (clj, pure): top-producer-share + named-HHI (concentration,
`:other` residual excluded), chokepoint-risk level, **multigen-risk** (0.40·monopoly
+ 0.30·carbon-intensity + 0.30·irreversibility), and a resilience **route**:

- `:de-monopolization` — monopoly/chokepoint is the dominant driver → route-around (abaki/kabuto/tsumugi)
- `:restoration` — irreversible environmental footprint dominant → circular path (kanayama/kamado/inochi)
- `:resilience` — default: diversify supply + build stock/recovery buffers

Plus per-class aggregates + a coverage gap worklist.

## 4. Constitutional gates (G1–G8)

| Gate | Requirement |
|---|---|
| **G1** | **Observation only — never a trade.** No buy/sell/position/order; `:busshi/trade` is unrepresentable (test-enforced). |
| **G2** | §2(l) multi-gen risk axis: concentration + multi-gen footprint routed to RESILIENCE / de-monopolization / restoration — **NEVER a target-list** (report says so, in words). |
| **G3** | Non-adjudicating: a producer SHARE + a price LEVEL are DISCLOSED facts, never a verdict and **never a forecast** (no `:busshi/signal`, no point-forecast attribute; mitooshi does distributions). |
| **G4** | kotoba Datom-native (EAVT EDN); no SQL/RisingWave/Cypher. Derived datoms flagged `:busshi/derived` + `:busshi/sourcing`. |
| **G5** | Aggregate-first: no precise mine/well coordinates (`:busshi.producer/mine-coordinates` unrepresentable); no person-level data. |
| **G6** | Any narration is Murakumo-only (ADR-2605215000). |
| **G7** | No-server-key; live primary-source ingest is an operator step (R0 seed is `:representative`). |
| **G8** | No paid data terminals (Rider §2(e)) — the Bloomberg/Refinitiv inversion; public-info only. |

## 5. Non-goals (N1–N5)

- **N1** — NOT an extraction/mining actor. Extraction is gated by §2(l) (ADR-2606161700) as its OWN actor; busshi only observes.
- **N2** — NOT a trading desk / no market signal (shionome echo). 取引しない.
- **N3** — NOT a price forecaster (mitooshi 見通し owns distributions; busshi observes levels).
- **N4** — NOT a paid terminal / data-broker (Rider §2(c)+§2(e)).
- **N5** — no person/individual data.

## 6. Clj-native files (R0)

```
20-actors/busshi/
├── CLAUDE.md · README.md · MATURITY.md · manifest.edn · run_tests.sh
├── kotoba/{ontology.busshi.edn, seed.edn}
└── methods/
    ├── busshi_edn.cljc          # loader + classify (clojure.edn, :clj file I/O)
    ├── analyze.cljc             # analyze → render-datoms → coverage → render-report (+ bb CLI)
    ├── test_busshi_edn.cljc     # loader tests
    └── test_analyze.cljc        # analytics + G1/G3/G5 invariant tests
```

Run: `bb --classpath 20-actors 20-actors/busshi/methods/test_analyze.cljc` (9 tests / 55 assertions green; loader 3/9).

# Consequences

**Positive** — closes the commodity/materials observatory gap; first actor authored natively under the ADR-2606161700 risk axis; clj-native + kotoba-Datom from R0; feeds meyasu/mitooshi/kabuto without ever trading or forecasting.

**Negative / deferred** — R0 seed is `:representative` (live primary-source ingest = G7 operator step); rare-earths kept thin (detail in rare-earth-coverage); per-commodity depth (futures curve, stocks, recycling-loop linkage to kanayama) deferred to Wave 2+.

# Alternatives Considered

1. **Per-domain actors** (separate gold/energy/ag actors). Rejected: one umbrella with class subsystems matches rare-earth-coverage's subsystem shape and avoids actor sprawl.
2. **Extend rare-earth-coverage to all commodities.** Rejected: rare-earth-coverage is the rare-metals specialist; busshi is the umbrella, with rare-earth-coverage as a sibling.
3. **Python methods.** Rejected: the user asked for clj + datomic; repo is in clj-native migration.

# References

- ADR-2606161700 — multi-gen extraction risk-gate (the axis busshi observes)
- ADR-2606022000 / 2606032000 / 2606072201 — kabuto / kanjō / shionome observatory siblings
- ADR-2605252400 / 2606051500 — kanayama (recycling) / kamado (energy transition) circular routes
- ADR-2605262130 / 2605312345 — kotoba Datom canonical state
