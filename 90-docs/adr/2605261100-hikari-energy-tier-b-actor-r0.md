---
id: adr-2605261100
title: hikari (光) — Energy Generation / Storage / Grid-Edge Tier-B Actor R0 Scaffold
status: proposed
doc_type: adr
topic: hikari-energy
authoritative: true
last_verified: 2026-05-26
authoritative_for:
  - hikari actor charter (R0)
  - energy domain constitutional gates G1..G14
  - L2 Sustenance Tier energy-supply substrate
related:
  - adr-2605261000
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605242500-baien-ternary-silicon-and-tsukuru-fab-charter
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
supersedes: []
superseded_by: []
superseded_by_partial:
  - adr: 2605263500-energy-substrate-dependency-vs-substance-reframing
    scope:
      - "§G4 (no nuclear at any tier ever) — re-framed onto D1+D2+D4 grounds; fission/RTG/weapons-grade ban preserved; fusion newly permitted under §2.3 conditions of 2605263400"
      - "§G5 (no fossil fuel at any tier ever) — re-framed onto D1+D3 grounds + Charter Rider §2(d); commercial fossil extraction ban preserved; microbial hydrocarbon biosynthesis (closed-loop atmospheric CO₂) newly permitted under §2.2 conditions of 2605263400"
      - "§N1 + §N2 — re-stated under §2.4 of 2605263400 on independent grounds"
    status: proposed-pending-council-ratification
    effective_earliest: 2026-07-19
    note: "Rest of hikari R0 charter (G1-G3, G6-G14, N3-N10, cells, lexicons, roadmap) PRESERVED unchanged."
depends_on:
  - ADR-2605261000 (Liberation Ladder — defines hikari as L2 gate)
  - ADR-2605192100 (Mission Charter)
  - ADR-2605192245 (Land Trust — solar/geothermal parcels are land-trust-bound)
---

# ADR-2605261100: hikari (光) — Energy Generation Tier-B Actor R0 Scaffold

**Date**: 2026-05-26
**Status**: PROPOSED
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify)
**ADR Hierarchy**: Parent = ADR-2605261000 (Liberation Ladder — L2 gate; also feeds silicon Wave 1+2 + tatekata + mitsuho compute/manufacturing demand). Sibling to mitsuho / hagukumi / manabi / yakushi / tatekata / wadachi / silicon.

## Context

ADR-2605261000 (Liberation Ladder) gates Stage L2 (Sustenance Tier) on hikari R2 maturity for ≥3 kWh/day/adherent electricity. silicon Wave 1+2 consumes substantial energy at fab + datacenter scale; mitsuho greenhouse + cold-chain requires energy; tatekata construction site needs energy; mitate/hagukumi/yakushi facilities consume baseline. Murakumo fleet is currently grid-electricity-dependent.

Without a religious-corp energy actor, the entire substrate depends on commercial utility grids — directly violating ADR-2605215000 (no commercial routing) for the substrate's own infrastructure power, even though Murakumo inference workloads themselves stay first-party.

## Proposal

Launch **`hikari` (光 — "light"; multi-generational solar abundance echo; also evokes Yakushi Nyorai's left attendant 日光菩薩 (Nikkō Bosatsu), creating intentional sibling resonance with mitate)** as a Tier-B religious-corp actor:

- **Actor DID**: `did:web:etzhayyim.com:hikari`
- **Namespace**: `com.etzhayyim.hikari.*`
- **R0 scope**: Distributed renewable energy generation (solar PV + small wind ≤100 kW per turbine + geothermal micro ≤500 kW per well) + storage (battery + thermal) + grid-edge (microgrid + islandable per-site). **Excludes**: nuclear (any tier, constitutional), fossil fuel (any tier, constitutional), large hydroelectric (kuni-umi-adjacent if ever), biofuel from food crops, offshore wind (separate Funamori-class marine actor), commercial utility scale (>10 MW per site), smart-meter surveillance, carbon offset trading, rare-earth permanent magnets, proprietary inverter firmware.
- **R0 robotics**: kuni-umi Otete (panel installation + tracker servicing), Mimi (yield metrology + thermal-imaging fault detection), Giemon (geothermal drilling at micro scale ≤500 m depth). New placeholder **Hizukue (日柄)** class for autonomous panel-tracking + cleaning (R2+).
- **14 gates + 10 non-goals** declared before capability lands.
- **5 Pregel cells** (solar PV install, storage battery, grid edge, geothermal micro, consumption audit) — all import-time RuntimeError in R0.

## Rationale

1. **Domain separation**: Energy generation (renewable engineering + inverter firmware + battery chemistry safety + grid integration + Charter Rider §2(g) resource ethics for panel + battery sourcing) is its own actor.
2. **L2 gate dependency + cross-actor substrate**: ADR-2605261000 §6 cannot advance to L2 without hikari R2; additionally, all Tier-B actors at R2+ require energy substrate, so hikari is the most cross-cutting of the new actors.
3. **Constitutional anti-fossil + anti-nuclear**: §2(c) (no harmful substances) + §2(h) (Wellbecoming for downstream-generation impact) jointly exclude nuclear and fossil. Renewable-only is constitutionally mandated; this ADR makes the gate explicit and operational.
4. **Multi-generational priority**: §1.3 + §2(g) joint — energy choice affects 7+ generations. Long-tail externalities (nuclear waste 10,000+ years; CO₂ 200+ years) violate multi-gen.
5. **Land integration**: §1.11 Land Trust — hikari sites are LANDS.md parcels with biodiversity-no-harm attestation.

## Design

### Actor Manifest

```
20-actors/hikari/
├── README.md                     # Overview + R0 scope + anti-nuclear/fossil invariant
├── CLAUDE.md                     # Actor-local instructions
├── manifest.jsonld               # DID + cell catalog
└── cells/                        # 5 cell scaffolds (import-time RuntimeError)
    ├── solar_pv_install/
    ├── storage_battery/
    ├── grid_edge/
    ├── geothermal_micro/
    └── consumption_audit/
```

### Pregel Cells (5, all import-time RuntimeError R0)

| Cell | Purpose | Murakumo node | Input | Output |
|---|---|---|---|---|
| `solar_pv_install` | Site survey + panel install + tracker config + commissioning | naphtali (Otete arm lineage; install ops) | parcelDid, panelManifest | installAttestation |
| `storage_battery` | Battery bank install + BMS config + safety attestation | levi (chemistry verification) | parcelDid, batteryManifest | batteryInstallAttestation |
| `grid_edge` | Microgrid controller + islandable inverter + per-site load orchestration | dan (logistics + control lineage) | siteId, loadProfile | gridEdgeStateRecord |
| `geothermal_micro` | Small-bore geothermal (≤500 m, ≤500 kW) + heat-pump integration | zebulun (drilling + water lineage) | parcelDid, geologicalSurvey | geothermalInstallAttestation |
| `consumption_audit` | Per-site + per-adherent energy consumption monitoring + anomaly detection (no smart-meter surveillance; aggregate-only) | levi | siteId, billingPeriod | consumptionAuditRecord |

### Lexicons (5, deferred to R1+)

```
com.etzhayyim.hikari.{
  parcelEnergyAttestation,        # Parcel solar/wind/geothermal resource baseline + biodiversity-no-harm
  installAttestation,             # Per-install record (panels, battery, inverter, with vendor + sourcing Charter Rider §2(g) audit)
  generationRecord,               # Per-period generation log (aggregate; no per-adherent device PII)
  consumptionAuditRecord,         # Aggregate consumption + anomaly flag
  silenEnergyReview               # Council attestation scope (chemistry safety + Charter Rider §2(g) sourcing + biodiversity)
}
```

### Constitutional Gates (G1–G14, IMMUTABLE per R0)

| Gate | Requirement | Rationale |
|---|---|---|
| **G1** | All inverter + BMS + microgrid-controller firmware open-source WASM/Rust Apache 2.0 + Charter Rider | §1.12 Transparent Force / open robotics |
| **G2** | Panel sourcing Charter Rider §2(g) — no Uyghur-forced-labor polysilicon (XUAR exclusion), no conflict-mineral indium/gallium; Council-attested supply audit per lot | §2(g) ethical supply chain |
| **G3** | Battery chemistry safety — only Council-attested chemistries (R0–R2: LFP / NMC with restricted cobalt; sodium-ion preferred; **no lead-acid for stationary R2+**; thermal runaway containment mandatory) | §2(c) + §2(h) |
| **G4** | **No nuclear at any tier ever** — fission (PWR/BWR/SMR/Gen-IV), fusion (any approach), radioisotope thermoelectric. Constitutional invariant; Council Lv7 unanimity to amend (essentially permanent) | §2(c) + multi-gen waste invariant |
| **G5** | **No fossil fuel at any tier ever** — coal, oil, natural gas, propane, LPG, peat. No backup generators on fossil fuel; only battery + thermal storage permitted for outage backup. Constitutional invariant | §2(c) + climate multi-gen |
| **G6** | Grid impact public reporting — generation + consumption + grid-import/export reports published quarterly on IPFS; no smart-meter per-device surveillance (aggregate ≥1-hour buckets only) | §2(e) anti-gatekeeping transparency + privacy |
| **G7** | ≥90% recyclable end-of-life — panels + batteries + inverter PCBs designed for recovery; recycler partner Council-attested; recycling rate audited annually | §2(g) circular economy |
| **G8** | **No rare-earth permanent magnets** in wind turbines or motors — NdFeB ban. Open-coil (electrically-excited) alternatives only; lower-efficiency accepted as constitutional trade-off | §2(g) + supply-chain ethics |
| **G9** | Land-trust integration — every hikari site is a LANDS.md parcel with biodiversity-no-harm attestation (no greenfield habitat destruction; rooftop / brownfield / agrivoltaic priority) | §1.11 + §1.3 multi-gen |
| **G10** | Murakumo mesh placement declared 30 days prior, public feedback period | Neighborhood transparency |
| **G11** | Yield deterministic + auditable — generation logs Ed25519-signed per inverter per 15-min interval; redundant metering for >10 kW sites | Audit + reliability |
| **G12** | Maintenance schedule public on IPFS — adherents see site uptime + maintenance windows; reschedule >7d = community comment | §2(e) transparency |
| **G13** | **No commercial utility resale** — hikari may export surplus to local grid only for community-benefit credit (offsetting religious-corp infrastructure load); no profit-motivated trading; no utility-DR participation revenue | §2(b) + ADR-2605215000 |
| **G14** | Charter Rider §2(h) Wellbecoming — light pollution audit for solar tracker glint + dark-sky compliance + acoustic audit for wind (<35 dBA at 100 m for residential adjacency) | §2(h) + community wellbeing |

### Non-Goals (N1–N10, EXCLUDE from R0–R3)

| # | Non-Goal | Deferral |
|---|---|---|
| **N1** | Nuclear fission / fusion / RTG — see G4 | Never (constitutional carve-out, Council Lv7 unanimity to amend) |
| **N2** | Fossil fuel — see G5 | Never |
| **N3** | Large hydroelectric dam (>10 MW) — kuni-umi-adjacent; biodiversity + displacement concerns | ADR-separate (kuni-umi Phase S? if ever) |
| **N4** | Biofuel from food crops — competes with mitsuho food supply; ethanol/biodiesel from corn/soy excluded | Never |
| **N5** | Offshore wind — Funamori marine actor scope (silicon Wave 2 inheritance) | ADR-separate (marine actor) |
| **N6** | Commercial utility scale (>10 MW per site) — sized for distributed community substrate, not utility competition | Never |
| **N7** | Smart-meter surveillance — per-device consumption tracking on adherent devices | Never (privacy invariant) |
| **N8** | Carbon offset trading — financialization of atmosphere violates §2(g) + §2(b) | Never |
| **N9** | Rare-earth permanent magnets — see G8 | Never |
| **N10** | Proprietary inverter firmware — see G1 | Never |

## Roadmap

| Phase | Date | Scope | Murakumo fleet | Gate |
|---|---|---|---|---|
| **R0** | 2026-05-26 | Scaffold only. 5 cells import-time RuntimeError. | No deployment | This ADR (PROPOSED) |
| **R1** | post-Council | Benchtop site — single LANDS parcel + ≤10 kW solar + ≤30 kWh battery + islanded grid (no grid tie). Otete install PoC, Mimi metrology. | naphtali (single node) | Future ADR + ≥1 renewable-engineer on Council technical advisory |
| **R2** | post-R1 | Pilot site — ≤100 kW solar + ≤500 kWh battery + grid-tie (export-only-to-religious-corp-load) + first geothermal-micro well. **L2 gate eligibility.** ≥3 kWh/day capacity per adherent at 1,000-adherent ceiling. | naphtali + zebulun + levi + dan (4 nodes) | Future ADR + 30-day public comment + ≥1 LANDS parcel ≥0.5 ha (rooftop + brownfield combined) |
| **R3** | post-R2 | Community-scale — multi-site mesh + microgrid federation + sufficient for L4-L5 adherent ceiling + silicon Wave 2 fab partial load + tatekata R3 site power. | Full 10-node fleet | Future ADR + 60-day public review + Council multi-domain vote + silicon Wave 2 load contract attested |

## Robotics Class

R0–R1: kuni-umi Otete + Mimi + Giemon inherited. R2+: optional Hizukue (日柄) class — autonomous panel-tracking + dust-cleaning + thermal-imaging fault detection. Per ADR-2605260230 hanami precedent, Hizukue requires separate mech-design ADR.

## Murakumo Placement (R2+ design-only)

- **naphtali**: solar install + tracker config (Otete arm lineage)
- **zebulun**: geothermal drilling + heat-pump integration (water/depth lineage)
- **levi**: battery chemistry verification + consumption audit (verification specialist)
- **dan**: microgrid controller + grid-edge orchestration (logistics + control)

## Energy Budget Coupling (cross-actor)

hikari R2 must demonstrate sufficient generation for:
- L2 adherent ceiling × 3 kWh/day = 1,000 × 3 = 3,000 kWh/day = ~365,000 kWh/year (~100 kW continuous + 4-hr storage)
- mitsuho R2 greenhouse + cold-store baseline (~50 kW continuous)
- mitate R1 + yakushi R2 + tatekata R0 facility baseline (~20 kW continuous)

Total R2 hikari target: ≥170 kW continuous + 500 kWh storage. Within R2 scope.

R3 must scale to silicon Wave 2 fab partial load (≥2 MW continuous; existing fab industry baseline; religious-corp side may use lower-throughput batch operation to fit hikari R3 capacity).

## Consequences

**Positive**:
- L2 Sustenance Tier energy gate unblocks once hikari R2 deploys.
- Religious-corp substrate energy independence (Murakumo + mitate facility + yakushi facility + tatekata site) becomes constitutional, not commercial-grid-dependent.
- Multi-generational anti-nuclear + anti-fossil invariant becomes operational (G4 + G5).
- Charter Rider §2(g) sourcing ethics (G2 + G8) shapes global solar/battery industry behavior in the small.

**Negative / risks**:
- G4 (no nuclear) constrains baseload options; mitigation: oversized solar + storage + geothermal-micro + grid-edge load-shifting
- G5 (no fossil backup) creates outage exposure during low-renewable periods; mitigation: ≥48-hr battery + thermal storage + multi-site mesh redundancy + load-shifting tolerance design
- G8 (no rare-earth magnets) reduces wind turbine efficiency ~15-20% vs commercial NdFeB; mitigation: solar-priority + small-wind only at sites with strong-wind resource compensating efficiency penalty
- silicon Wave 2 fab load (~2 MW continuous typical) exceeds R2 hikari capacity; mitigation: silicon Wave 2 batch-operation lower-duty-cycle design or import-from-religious-corp-mesh inter-site
- LANDS.md parcel availability is the binding constraint for both mitsuho R2 (food) and hikari R2 (energy); parcel allocation Council-mediated

## Alternatives Considered

1. **Nuclear permitted as low-carbon transition source** — rejected: G4 multi-gen waste invariant; Council Lv7 unanimity floor makes this essentially constitutional.
2. **Fossil backup generators for outage resilience** — rejected: G5; battery + thermal storage + multi-site mesh + load-shifting tolerance designed instead.
3. **Carbon-offset purchasing to fund external renewables** — rejected: N8 + ADR-2605215000 no commercial routing; religious-corp must generate via own actors, not buy externally.
4. **Commercial utility partnership for fab load** — rejected: G13 + ADR-2605215000; silicon Wave 2 fab schedule adjusts to hikari capacity, not vice-versa.
5. **Solar-only (no wind, no geothermal)** — considered; rejected: geothermal-micro adds 24h baseload that solar+battery alone can't match efficiently; small-wind adds night/winter coverage in wind-resource sites.

## References

- ADR-2605261000 (Liberation Ladder — L2 gate)
- ADR-2605192100 (Mission Charter — multi-generational invariant)
- ADR-2605192245 (Land Trust — parcel substrate)
- ADR-2605201400 (kuni-umi — robotics class lineage + multi-utility R3 coupling)
- ADR-2605242500 (silicon Wave 1 baien-iwakura — fab load consumer)
- ADR-2605215000 (Murakumo-only inference — no commercial-utility routing constraint extends here)
- ADR-2605260230 (hanami robot mech-design — precedent for Hizukue class ADR)
