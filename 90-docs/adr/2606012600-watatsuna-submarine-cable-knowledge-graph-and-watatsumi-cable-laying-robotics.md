---
id: adr-2606012600-watatsuna-submarine-cable-knowledge-graph-and-watatsumi-cable-laying-robotics
title: "ADR-2606012600: watatsuna 綿津綱 — world submarine-cable network knowledge graph (kotoba EAVT) + watatsumi 綿津見 cable-laying robotics extension"
status: proposed
doc_type: adr
topic: watatsuna-submarine-cable-knowledge-graph
authoritative: true
last_verified: 2026-06-01
priority: 6.5
axis: architecture
weight: 0.65
priority_note: "World submarine-cable network as a kotoba knowledge graph; resilience-not-interdiction; pairs the KG with watatsumi's lay/repair robotics"
authoritative_for:
  - watatsuna actor (world submarine-cable network knowledge graph)
  - submarine-cable-ontology kotoba schema
  - com.etzhayyim.cable.* kotoba-native lexicons (supersede legacy etzhayyim telecom/telecomInfra/cableRepairFleet)
  - watatsumi cable-laying robotics fleet
depends_on:
  - adr-2606011800-tsumugi-spirit-intel-power-graph
  - adr-2606011000-engi-organism-ontology-and-musubi-knowledge-graph
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605252200-watatsumi-civilian-submersible-r0
  - adr-2605241500-dataset-cid-substrate
  - adr-2605241800-etzhayyim-agenturi-five-layer
related:
  - adr-2606011500-spirit-in-physics-kotoba-datafication
  - adr-2605301600-danjo-public-accountability
  - adr-2605302300-kanae-fiscal-flow-visualization
  - adr-2605301400-tadori-onchain-tracing
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
supersedes: []
superseded_by: []
---

# ADR-2606012600: watatsuna 綿津綱 — world submarine-cable network knowledge graph + watatsumi cable-laying robotics

**Status**: proposed
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

The founder asked whether a **submarine-cable database** could be (a) designed as a
kotoba server/actor and (b) displayed as an actor on `etzhayyim.com`, and — if etzhayyim
needs it — to also design the **敷設 (cable-laying) robotics**.

Audit of the repo found only **legacy `etzhayyim`-namespaced lexicons** scattered across
`telecom`, `telecomInfra`, and `cableRepairFleet` (record schemas authored against the
deprecated RisingWave vertex model), **no** dedicated actor, **no** kotoba EAVT dataset,
and **no** ADR. The closest actor, **watatsumi 綿津見** (民生 submersible, ADR-2605252200),
already scopes "subsea infrastructure inspection + cable laying support (≤2000 m)" and
lists "submarine cable cutting / sabotage" as constitutional non-goal **N8**.

The world submarine-cable network is high-stakes public infrastructure: ~99% of
intercontinental data crosses it, and capacity concentrates onto a handful of maritime
chokepoints (Luzon Strait, Malacca/Singapore, Suez/Red Sea, Gibraltar). A knowledge graph
of it is squarely in the lineage of etzhayyim's **observation actors** — `tsumugi` (産霊
power graph), `danjo` (accountability), `kanae` (fiscal flows), `tadori` (on-chain tracing).

The acute constitutional risk: a "where are the cables and where do they break" graph is
one framing away from a **target-list**. The design must be **resilience-not-interdiction**
by construction, consistent with watatsumi **N8** and Charter Rider **§2(d)** (infrastructure
attack prohibited).

# Decision

Create **two paired, same-root deliverables**:

## 1. watatsuna 綿津綱 — the knowledge-graph actor (new Tier-B, R0 design-only)

`20-actors/watatsuna/` — the *observation* face. Datafies the planet's submarine cable
network into the **kotoba Datom log** and surfaces chokepoint / single-point-of-failure
concentration, **routed to redundancy + faster repair**.

- **Vocabulary**: `00-contracts/schemas/submarine-cable-ontology.kotoba.edn` —
  `:cable/*` systems · `:station/*` landing stations (with `:chokepoint` tags) ·
  first-class edges `:cable.link/*` (cable⇄station) and `:cable.seg/*` (station⇄station,
  with `:traverses` chokepoints) · `:cable.fault/*` observed bulletins (as-of history).
- **Seed**: `data/seed-cable-graph.kotoba.edn` — 14 real public systems (JUPITER, FASTER,
  PLCN, MAREA, Dunant, Grace Hopper, 2Africa, SEA-ME-WE 3/4, ADC, SJC, Equiano, Bifrost,
  APCN-2), 22 landing stations, 43 links, 11 chokepoint segments, 2 public fault bulletins.
  Every node/edge carries `:sourcing` (`:representative` throughout the seed).
- **Analyzer**: `methods/analyze.py` (stdlib only) → aggregate-first `out/intel-report.md`
  + `out/cable-criticality.kotoba.edn`. First run: top chokepoints **Malacca 490 Tbps ·
  Luzon Strait 455 · Gibraltar 324 · Suez/Red Sea 250 · South China Sea 191** — the
  industry-recognized vulnerable straits surface exactly as intended.
- **Display**: registered in `INFRA_ACTORS` (`50-infra/etzhayyim-did-web/src/registry/
  infra-actors.ts`) → resolvable as `did:web:etzhayyim.com:actor:watatsuna` at
  `https://etzhayyim.com/actor/watatsuna/did.json`. **This answers the founder's
  display question: yes.**

### watatsuna gates (G1–G9)

1. **G1 public-only** — public-record infrastructure only; classified/military routes,
   precise armoring depth, live repair-vessel position beyond public AIS = out of scope.
2. **G2 resilience-not-interdiction** — chokepoint ranking routed to redundancy + repair;
   never a target-list (watatsumi N8 + Charter Rider §2(d)).
3. **G3 aggregate-first + claimed-first** output.
4. **G4 no intent adjudication** — fault `:kind` mirrors only the public bulletin's own
   classification; sabotage is a state matter, never asserted by watatsuna.
5. **G5 sourcing honesty** — `:authoritative | :representative | :synthesized` on every node/edge.
6. **G6 Murakumo-only** narration (ADR-2605215000).
7. **G7 outward-gated** — live planet-scale ingest (TeleGeography feed / cable-ship AIS) = Council + operator.
8. **G8 no git-lfs** — large geo assets DataLad → IPFS (`80-data/submarine-cable`), per ADR-2605241500.
9. **G9 no PII** — infrastructure graph only; incidental personal data → encrypted envelope, excluded by default.

## 2. kotoba-native lexicons — migrate the legacy `etzhayyim` cable lexicons (founder ask "c")

New `com.etzhayyim.cable.*` namespace asserting into the kotoba Datom log
(`txCid` + `datomCount`, ADR-2605312345), with `:sourcing` on every record:
`registerCableSystem` · `registerLandingStation` · `registerSegment` · `flagCableFault`.

Full inventory + legacy→kotoba mapping is the SoT in
`00-contracts/lexicons/com/etzhayyim/cable/MIGRATION-NOTES.md`. Notably,
`cableRepairFleet.flagSubseaCableTamper` is **RETIRED, not ported** — a "tamper flag"
presumes intent adjudication (violates G4) and reads as interdiction-adjacent. Repair-fleet
lexicons (`registerRepairVessel`, `logRepairMission`) move to **watatsumi** (operational).
Per repo-root CLAUDE.md §Do-Not, the legacy `etzhayyim-` removal executes as one atomic cutover
wave; R0 leaves them in place behind this inventory.

## 3. watatsumi 綿津見 — cable-laying robotics extension (敷設)

The *operational* face, paired same-root with watatsuna. New fleet in
`watatsumi/data/cable-laying-fleet.kotoba.edn` + manifest `cableLayingFleet` + CLAUDE/README:

| Robot | Glyph | Role | Phase |
|---|---|---|---|
| Tsuna-suki | 綱鋤 | Towed sea plough / burial trencher (≤3 m, ≤2000 m) | R1+ |
| Horinuki | 掘抜 | Jet-trenching burial / PLIB ROV | R2+ |
| Tsugite | 接手 | Splice / repeater-housing manipulation ROV (inherits Otete-marine) | R2+ |
| Tedori | 手繰 | Grapnel cable-recovery ROV — **REPAIR-ONLY** | R2+ |
| Kikimimi | 聞耳 | DAS passive cable-health monitor → feeds watatsuna `flagCableFault` | R1+ |

**N8 invariant (CRITICAL)**: every unit acts ONLY to lay / bury / splice / repair / monitor.
Cutting / interdiction / sabotage is hard-prohibited (watatsumi N8 + Charter Rider §2(d)).
**Tedori** carries grapnel cut-and-hold for recovering a *faulted* cable for re-splice, only
under a logged **G4 witness-quorum (≥2 robots)** repair work-order; never against a healthy
cable. Fleet missions are planned **off watatsuna's resilience output** — lay diverse routes
where `redundancy-gap`, pre-stage repair where `chokepoint-load` is high. watatsuna knows; watatsumi acts.

# Consequences

**Positive**
- A kotoba-native, content-addressed, on-chain-anchorable submarine-cable knowledge graph that
  is queryable (kotoba-kqe arrangements) and resolvable as a first-class etzhayyim actor.
- The legacy `etzhayyim` cable lexicons get a clean kotoba-native successor + an explicit retirement
  decision for the interdiction-adjacent `flagSubseaCableTamper`.
- A clear division of labor: watatsuna (KG, observation) ↔ watatsumi (robotics, operation),
  same `綿津` root, both N8-bound.

**Negative / risk**
- Dual-use sensitivity is real. Mitigated structurally: G1 public-only, G2 resilience framing,
  G4 no intent adjudication, and the explicit retirement of the tamper-flag lexicon.
- R0 ships a bounded `:representative` seed only; live ingest is G7-gated, so coverage is
  illustrative, not operational, until Council approval.

**Honest limitations (R0)**
- Seed is a bounded illustrative sample, not exhaustive; coordinates rounded to landing town;
  capacities are public design figures; chokepoint dependency charted only for seeded segments.
- watatsumi robotics are **design-only** — no hardware; maturity flags conservative.
- No live TeleGeography/ITU/AIS feed; no WASM resilience viz yet (R1, kanae-style).

# Alternatives Considered

1. **Fold into tsumugi** — rejected; tsumugi is power-entity 縁 (organisms), cable network is
   physical infrastructure with distinct vocab and a distinct dual-use risk profile.
2. **Reuse the legacy `etzhayyim` lexicons as-is** — rejected; they assume RisingWave vertices
   (substrate-boundary violation) and include the intent-adjudicating tamper flag.
3. **Put the KG inside watatsumi** — rejected; watatsumi is a manufacturing/operational actor.
   Observation vs operation is the same split as danjo(watch)↔toritsugi(act); pairing two
   same-root actors keeps each single-purpose. (Chosen per founder direction.)
4. **No robotics** — rejected; founder asked for 敷設 robotics where needed, and watatsumi is
   the natural, N8-bound home.

# References

- `20-actors/watatsuna/` — actor (manifest, README, CLAUDE, data, methods, out)
- `00-contracts/schemas/submarine-cable-ontology.kotoba.edn` — vocabulary
- `00-contracts/lexicons/com/etzhayyim/cable/` — kotoba-native lexicons + MIGRATION-NOTES.md
- `20-actors/watatsumi/data/cable-laying-fleet.kotoba.edn` — cable-laying robotics fleet
- `50-infra/etzhayyim-did-web/src/registry/infra-actors.ts` — `INFRA_ACTORS.watatsuna`
- ADR-2605252200 (watatsumi R0, N8) · ADR-2606011800 (tsumugi, observation-actor pattern) ·
  ADR-2605262130 + 2605312345 (kotoba substrate) · ADR-2605215000 (Murakumo-only) ·
  ADR-2605192200 (Charter Rider §2(d))
