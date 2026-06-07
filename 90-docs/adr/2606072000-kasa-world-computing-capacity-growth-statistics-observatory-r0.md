---
id: adr-2606072000-kasa-world-computing-capacity-growth-statistics-observatory-r0
title: "ADR-2606072000: kasa 嵩 — Worldwide Computing-Capacity Growth Statistics Observatory (Tier-B Actor R0)"
status: proposed
doc_type: adr
topic: kasa-computing-capacity-growth-observatory
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Tier-B observation-layer actor that registers, from PUBLIC information only, the WORLDWIDE annual MAGNITUDE + GROWTH of computing capacity across four founder-named domains — STORAGE (HDD+SSD exabytes shipped), MEMORY (DRAM+NAND revenue + bit-shipment growth), GPU/CPU (discrete-GPU + client-CPU units, datacenter-accelerator revenue), COMPUTE/FLOPS (TOP500 aggregate Rmax, frontier-model training compute) — plus DATACENTER power capacity, into the kotoba Datom log as :compute.obs/*, then computes the annual increase (年間増加量) YoY + CAGR and coverage-honest domain aggregates. The industry-aggregate sibling of kanjō 勘定 (per-company 決算, ADR-2606032000) and the demand-side counterpart of the silicon actors (handotai / iwakura / fuigo). Feeds measured actuals to mitooshi 見通し (ADR-2606051800) but NEVER forecasts itself (G4). NON-ADJUDICATING (G2) + PLANNING-LENS not a targeting list (G9) + NO investment advice. PROHIBITED inputs: paid market-research full reports + subscription terminals (Gartner / IDC-report / Omdia / Bloomberg / S&P / Statista-Pro / Yole) per Charter Rider §2(e) anti-gatekeeping + §2(c) vendor query-tracking — the same bar as kanjō; the free press-release headline is admissible, the paid terminal compilation is not. Vocab compute-capacity-ontology.kotoba.edn (:compute.series/:compute.obs/:compute.source/:compute.growth/:compute.agg). R0 = design + vocab + source-catalogue + :representative/:estimated seed (8 sources / 11 series / 52 obs, 2020–2024) + 3 cells + 23 tests; live full open-dataset parse = G7 Council+operator gated. 12 gates + 8 non-goals."
authoritative_for:
  - computing-capacity-growth-observatory-actor
  - compute-capacity-eavt-vocabulary
  - public-compute-source-admissibility-map
depends_on:
  - 2606032000
  - 2606022000
  - 2606051800
  - 2605263800
  - 2605262130
  - 2605312345
  - 2605215000
related:
  - 2606013800
  - 2606013600
  - 2605242500
supersedes: []
superseded_by: []
---

# ADR-2606072000: kasa 嵩 — Worldwide Computing-Capacity Growth Statistics Observatory (Tier-B Actor R0)

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

The founder asked:
*「年間のコンピューターのストレージサイズ、メモリサイズ、GPU・CPU などのコンピューティング能力の、
全世界での増加量を、統計・公開情報から推測するアクターは設計されているか?」*
("Is there already an actor that estimates, from statistics and public information, the worldwide
annual INCREASE in computing capacity — storage size, memory size, GPU, CPU, …?")

The answer was **no**. A sweep of the 20-actors roster found the closest actors all stop short:

- **kanjō 勘定** (ADR-2606032000) reads ONE listed company's disclosed 決算 (BS/PL/CF line items).
  It is per-company, not industry-wide capacity, and explicitly **does not forecast or aggregate
  hardware volumes**.
- **kabuto 兜** (ADR-2606022000) holds the public-company supply graph — supplier→customer edges +
  concentration metrics — but its only number is a `:representative` market-cap snapshot; it holds
  *relationships*, not *capacity volumes*.
- **handotai 半導体** tracks semiconductor *news / market / products*, not capacity statistics
  (exabytes shipped, FLOPS installed).
- **mitooshi 見通し** (ADR-2606051800) is the *forecaster* — it emits probability distributions over
  public time-series. But it is distribution-only and had **no measured-actuals feeder for the
  compute domain**; nothing in the roster turned public compute-shipment statistics into queryable
  Datoms it could forecast over.
- The **silicon actors** (iwakura / fuigo / tsukuru, ADR-2605242500) are the *supply/fab* side; none
  measures world demand-side capacity.

So the missing piece is a **demand-side, industry-aggregate observatory**: read public
compute-capacity statistics (semiconductor sales, memory revenue, storage exabytes, GPU/CPU units,
FLOPS), normalize them into one EAVT vocabulary, and compute the **annual increase (年間増加量)** —
the very quantity the founder named.

**Why "public information" is the whole game.** The founder's instinct — *統計・公開情報から推測する*
("estimate from statistics and public information") — is exactly right and exactly the constraint.
The FACTS are public: WSTS/SIA put global semiconductor sales in free monthly press releases,
TrendForce publishes DRAM/NAND revenue, TOP500 is a public semiannual list, and Epoch AI publishes
its notable-models training-compute database under **CC-BY**. What is *inadmissible* is the **paid
market-research product**: a Gartner / IDC / Omdia full report or a Bloomberg / S&P terminal — a
gatekept, copyrighted compilation sold for a fee whose vendor would also learn the member's query
posture. Ingesting those fails the same two grounds kanjō already codified — (1) **copyright/
license** (no open license → cannot be redistributed into an Apache-2.0 / IPFS corpus), and (2)
**Charter Rider §2(e) anti-gatekeeping + §2(c) vendor query-tracking**. kasa therefore inherits
kanjō's G1 stance verbatim: **read the press release + the open dataset, never the paid terminal.**

**Why not just extend kanjō or mitooshi.** kanjō's vocabulary is per-company GAAP line items — the
wrong shape for "exabytes of HDD shipped worldwide" or "FLOP of the year's largest model". mitooshi
is a forecaster and must stay one (a measured-actuals ingest would blur its distribution-only
invariant). The clean design is a **new sibling**: kasa measures and records *actuals + historical
growth*; mitooshi *forecasts* over what kasa records. The boundary between them is load-bearing and
becomes kasa's G4.

# Decision

Create **kasa 嵩** (*bulk / volume / amount* — the reckoner of the world's accumulating compute), a
**Tier-B, R0 design-only** observation-layer actor.

## Vocabulary — `00-contracts/schemas/compute-capacity-ontology.kotoba.edn`

A kotoba-native EAVT vocabulary (sibling of kanjō's `corporate-financials-ontology`):

- `:compute.series/*` — the DEFINITION of one measured series: `domain` (`:semiconductor | :dram |
  :nand | :storage | :gpu | :cpu | :flops | :datacenter`) × `metric` (`:revenue | :shipped-capacity
  | :shipped-units | :flops-installed | :flops-training | :power-capacity | …`) × `unit` × `scale` ×
  `geography`. The shape; observations hang off it.
- `:compute.obs/*` — ONE observation (a series × a `year` × a `value`), linked to its public
  `source`, with `method` (required when `:estimated`) and `superseded-by` (revision history).
- `:compute.source/*` — a public source: `publisher` × `access` × `license` × `url` × `doc-cid`.
  The provenance + admissibility anchor.
- `:compute.growth/*` — derived YoY (consecutive years) + full-span CAGR (`:synthesized`, G5). The
  **年間増加量** — a measured rate of change, not a forecast.
- `:compute.agg/*` — domain / geography aggregate (`:synthesized`, coverage-honest). Aggregation is
  confined to one `(domain × metric × unit × scale)` so memory (`:dram`/`:nand`) — a subset of
  `:semiconductor` in a distinct domain key — is structurally never double-counted.

## Cells (`20-actors/kasa/methods/`)

- `cell:kasa.sources` (`sources.py`) — the **G1 admissibility layer**: 9 admissible public
  publishers + 10 prohibited paid terminals; `admissible(publisher, access)` gates every ingest.
  Encodes Charter Rider §2(e)+§2(c). Emits `out/source-catalogue.kotoba.edn`.
- `cell:kasa.ingest` (`ingest.py`) — public rows-JSON → `:compute.series` + `:compute.obs` EAVT,
  G1-gated; merge with seed (`:authoritative` > `:estimated`/`:representative`). Offline default;
  live `--fetch-epoch` (Epoch AI CC-BY) is **G7** Council+operator gated.
- `cell:kasa.analyze` (`analyze.py`, stdlib) — obs → per-series YoY + full-span CAGR → domain
  aggregates → aggregate-first **年間増加量** report (`out/intel-report.md` +
  `out/compute-growth.kotoba.edn`).

## R0 seed (proof-of-model)

`data/seed-compute-capacity.kotoba.edn`: **8 public sources / 11 series / 52 observations**,
2020–2024, spanning all four founder-named domains plus datacenter power. Every value is
`:representative` (public headline, rounded) except the frontier-training-compute + datacenter-power
series, which are `:estimated` (Epoch AI / analyst estimate, each carrying a `:compute.obs/method`).
**Zero `:authoritative` rows** — the exact-dataset-row path is R1, G7-gated.

## Gates (constitutional)

- **G1 Public sources only** — public/redistributable headline figures + open datasets; paid full
  reports + subscription terminals prohibited (Charter Rider §2(e)+§2(c)). Encoded in `sources.py`.
- **G2 Non-adjudicating** — measured quantities + transparent growth; no country/company ranking,
  no "winner", no dominance verdict.
- **G3 Aggregate-first.**
- **G4 No forecasting** — PAST/PRESENT actuals + measured growth only; future projection is mitooshi
  見通し. `:estimated` is a *nowcast* of a knowable present/past quantity (with method), never a
  future forecast.
- **G5 Sourcing honesty** — `:authoritative | :representative | :estimated | :synthesized`; derived
  values never re-ingested; Σ coverage-bounded (read against `:compute.agg/n`), never a market total.
- **G6 Murakumo-only** narration (ADR-2605215000).
- **G7 Outward-gated ingest** — live dataset fetch = `KASA_OPERATOR_GATE` + Council; passive-only.
- **G8 No git-lfs** — source snapshots → DataLad → IPFS (`80-data/compute-capacity`); CID on
  `:compute.source/doc-cid`.
- **G9 Planning-lens, NOT a targeting list** — figures route to compute-commons sizing + labor-
  liberation planning, never to export-control / sanctions / weaponization targeting. Society-scale
  aggregates only; no per-person data.
- **G11 Revision-as-history (非終末論)** — a restatement asserts a NEW obs via `superseded-by`; the
  prior Datom is retained. Read as-of.
- **G12 Coverage-honest aggregates** — aggregation only within one `(domain × metric × unit ×
  scale)`; memory never double-counted into semiconductor; `:petaflops` never summed with raw
  `:flops`.
- **G13 Read-only** — kasa is an observer; it never mutates upstream sources.

## Substrate

State = kotoba Datom log (ADR-2605262130 + 2605312345; IPFS block backend, MST ingress, Base L2
anchor). No SQL / RisingWave. Source CSV/PDF snapshots → DataLad → IPFS (`80-data/compute-capacity`,
G8). Render = in-browser kotoba-wasm node (ADR-2606013600); DID
`did:web:etzhayyim.com:actor:kasa` (ADR-2606013800; INFRA_ACTORS registration pending).

# Consequences

**Positive.**

- Closes a real gap: the religious-corp can now SIZE its own non-rival compute donation
  (`moyai` / compute-node donation, ADR-2606012100) against the world's measured annual compute
  growth — a direct labor-liberation planning input (Charter §1, mission).
- Completes the intel/observation cohort's compute axis: kasa (capacity actuals) → mitooshi
  (forecasts) → kanae/danjo (accountability), with kasa as the measured-actuals feeder mitooshi
  lacked.
- Inherits kanjō's proven sourcing-honesty + anti-gatekeeping model, so the family stays consistent
  (one `:sourcing` discipline, one "read the filing/press-release, never the terminal" stance).
- 23 stdlib tests green; the four-domain growth model + double-count safety are pinned.

**Costs / risks.**

- The R0 seed is `:representative` headline figures — useful for proving the model, NOT a coverage
  claim. MATURITY.md states this plainly; the report's honesty section repeats it.
- Memory-subset-of-semiconductor and FLOPS scale-mixing are genuine double-count traps; mitigated
  structurally (distinct domain keys; aggregation keyed on unit AND scale) and tested.
- The G4 boundary with mitooshi must be policed: kasa must never grow a "projected 2027" column.
  Enforced by the no-future-dated-obs invariant test + the report's explicit no-forecast disclaimer.

**Follow-ups (R1).** Implement the Epoch AI CC-BY CSV parser (first `:authoritative` rows); bridge
WSTS/SIA + TrendForce + TOP500 public series under the G7 gate; populate the `:geography` axis;
wire `com.etzhayyim.kasa.*` publish to kotoba-server and hand `:compute.obs` series to mitooshi.

# Alternatives Considered

1. **Extend kanjō** to hold industry capacity. Rejected — kanjō's per-company GAAP shape is wrong
   for exabytes/FLOPS, and mixing world aggregates into a per-filer vocabulary breaks its coverage
   semantics.
2. **Add a measured-actuals ingest to mitooshi.** Rejected — it would blur mitooshi's
   distribution-only invariant (G1 there). Clean separation: kasa measures, mitooshi forecasts.
3. **Allow paid market-research as a source** (Gartner/IDC/Omdia full reports). Rejected — fails
   license + Charter Rider §2(e)+§2(c), identical to kanjō's 四季報/terminal bar. Free press-release
   headlines + CC-BY datasets are sufficient for the model and are the constitutional ceiling.
4. **A forecasting-capable capacity actor.** Rejected — that is precisely mitooshi's charter-clean
   role (and a naive extrapolator drifts toward speculation). kasa stays measured-actuals-only.

# References

- `20-actors/kasa/` — actor scaffold (manifest, CLAUDE.md, README.md, MATURITY.md, 3 cells, seed, 23 tests)
- `00-contracts/schemas/compute-capacity-ontology.kotoba.edn` — the EAVT vocabulary
- ADR-2606032000 — kanjō 勘定 (per-company financial disclosure; G1 sourcing model inherited)
- ADR-2606022000 — kabuto 兜 (public-company supply graph; shared observation lineage)
- ADR-2606051800 — mitooshi 見通し (the forecaster kasa feeds; the G4 boundary)
- ADR-2605263800 — corporate-disclosure substrate / Tier-A source taxonomy
- ADR-2605242500 — silicon actors (iwakura / fuigo / tsukuru; supply-side counterpart)
- ADR-2605262130 / 2605312345 — kotoba Datom log canonical state
- ADR-2606012100 — compute-node donation / moyai (the planning consumer of kasa's output)
- Public sources: SIA Global Semiconductor Sales · WSTS · TrendForce · IDC · Jon Peddie Research ·
  TOP500 · Epoch AI Notable AI Models (CC-BY) · Our World in Data (CC-BY)
