---
id: adr-2606171800-tatara-global-manufacturing-plant-kg
title: "ADR-2606171800: tatara 鑪 — world manufacturing-plant + logistics geographic knowledge graph"
status: proposed
doc_type: adr
topic: tatara-manufacturing-geo
authoritative: true
last_verified: 2026-06-17
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - geographic / facility-scale layer of the supply lineage (where the world's manufacturing physically sits)
  - tatara actor design, ontology, lexicons, gates
  - manufacturing export-dependence ↔ watari/watatsuna chokepoint composition
  - watari first visualization layer (craft-globe) + integrated world-supply globe
depends_on:
  - "2606022000"
  - "2606081800"
  - "2606041827"
  - "2606012600"
  - "2605262130"
  - "2605312345"
  - "2605215000"
  - "2605192200"
related:
  - "2605232345"
  - "2605232500"
supersedes: []
superseded_by: []
---

# ADR-2606171800: tatara 鑪 — world manufacturing-plant + logistics geographic knowledge graph

## Context

The roster modelled the supply world abstractly (kabuto 兜 = org→org supply edges; uchiwake 内訳
= product GTIN→part→material BOM) and the moving world live (watari 渡り = ship/aircraft positions;
watatsuna 綿津綱 = submarine cables). **No actor answered the geographic question:** *where on
Earth does the world's manufacturing physically sit, at what scale (employment / floor area /
production capacity), and which shipping chokepoints does its export depend on?*

A user asked precisely this — "全世界の manufacture の中核、物流企業の位置・場所… 出荷・物流・
労働者数・工場規模・生産能力" — and whether it is designed/implemented/**visualized** on the
actor / Datom / Clojure / kotoba substrate. The honest answer was: the *pieces* existed (kabuto
carried `:company.address/lat/lon`; haraedo carried `:facility/lat/lon`; watari/watatsuna carried
chokepoints) but **no facility-scale geographic manufacturing layer, and no integrated map**.

## Decision

Add **tatara 鑪** (the traditional ironworks furnace — the heart of making, at planet scale): a
Tier-B, kotoba-native, R0 actor that holds the **geographic / facility-scale** layer of the
supply lineage and **composes with watari + watatsuna over shared chokepoint keywords**.

### Ontology (`00-contracts/schemas/manufacturing-plant-ontology.kotoba.edn`)

- `:plant/*` — a manufacturing facility: id, name, **operator** (→ kabuto `org.corp.*`), country,
  **`:lat`/`:lon`** (rounded ~0.01°), `:sector`, `:products`, `:established`, **`:headcount-est`**
  (aggregate employment), **`:floor-area-m2`** (scale), **`:capacity-value` + `:capacity-unit`**
  (production capacity).
- `:hub/*` — a logistics node (seaport / airport / rail / DC) with lat/lon + throughput.
- `:flow/*` — a plant→hub export edge; **`:via`** = chokepoint keyword(s), **the same vocabulary
  as watari `:lane/chokepoint` and watatsuna `:station/chokepoint`** — the join key that composes
  the three maps into one resilience picture.
- derived `:concentration/*` — per-sector country HHI, single-source flag, chokepoint
  export-dependence. Flagged `:concentration/derived`, never re-ingested as fact.

### Engine (cljc, babashka-runnable)

- `methods/analyze.cljc` — classify → per-sector country **HHI** + single-source → **chokepoint
  export-dependence** → country employment/floor rollup → per-sector **capacity** rollup →
  `out/concentration-report.md` + derived datoms.
- `methods/kotoba.cljc` — content-addressed **EAVT commit-DAG** persistence (append-only,
  verify-chain tamper-evident, resume-safe, no external I/O).
- `viz/build_viz.cljc` — emits three self-contained canvas globes from the seeds (every
  coordinate **derived**, none hand-copied):
  - `viz/plant-globe.htm` — world plants by sector + export flows.
  - `viz/world-supply-globe.htm` — **integrated**: plants (tatara) + live craft (watari) +
    chokepoint composition on one globe.
  - `../watari/viz/craft-globe.htm` — **watari's first visualization** (it previously had none).

### Seed

22 real, public, well-known plants (TSMC / Samsung / Intel / Hyundai / Toyota / VW / Tesla / CATL
/ POSCO / Baowu / Foxconn / Boeing / Airbus / HD Hyundai …) across 8 sectors / 9 countries, 6
logistics hubs, 22 export flows — all `:representative`, coordinates rounded to city/campus scale.

## Constitutional gates

- **G2 resilience, not interdiction** — outputs framed toward redundancy / diversification /
  reshoring; never a target-list (Charter Rider §2(a)+§2(d); mirrors kabuto/watatsuna G2).
- **G4 DISCLOSED AGGREGATE facility figures only — the defining gate.** `:plant/headcount-est` is
  a disclosed aggregate SIZE (like market-cap). **No `:worker/*` / `:person/*` attribute exists**;
  an individual worker is structurally unrepresentable (Charter Rider §2(c) reciprocity axis: no
  asymmetric labour surveillance; Wellbecoming §1.13; mirrors sarutahiko/itonami/niyaku).
  **Enforced by construction + by tests** — `test_analyze` and `test_kotoba` both assert no
  worker/person namespace can appear in the records or the persisted datoms.
- **G1 / G5 / G6 / G7 / G8 / G9** — coarse public geography; sourcing honesty; Murakumo-only;
  live ingest Council+operator-gated; no git-lfs; disclosed product classes only (no recipe).

## Consequences

- The supply lineage now has its geographic substrate: kabuto (who → whom) + uchiwake (what) +
  **tatara (where, at what scale)** + watari (live transit) + watatsuna (cable) — composing over
  one chokepoint vocabulary.
- The user's "可視化" request is answered concretely: three runnable globes, including the
  integrated world manufacturing + logistics map, and the visualization watari was missing.
- R0 ships a bounded seed; live disclosure / GLEIF / OSM ingest is the G7 Council+operator step.

## Status

R0 LANDED 2026-06-17 — ontology + seed (22 plants / 6 hubs / 22 flows) + analyze + kotoba
commit-DAG + autonomous autorun heartbeat + 3 globes + **19 tests / 2,162 assertions green**
(`bb 20-actors/tatara/run_tests.sh`).
Council attestation = PR review (founder operational premise, 2026-06-11). Live ingest G7-gated.
