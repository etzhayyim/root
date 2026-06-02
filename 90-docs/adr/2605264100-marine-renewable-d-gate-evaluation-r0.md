---
id: adr-2605264100-marine-renewable-d-gate-evaluation-r0
title: "Marine renewables (OTEC / wave / tidal-stream / tidal-lagoon / salinity-gradient) — D1..D5 evaluation R0 (sub-ADR of 2605263500; Funamori actor pre-evaluation)"
status: proposed-pending-council-ratification
doc_type: adr
topic: marine-renewable-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 7.9
axis: constitutional
weight: 0.79
priority_note: "Sub-ADR of ADR-2605263500 D1..D5. Covers all marine renewable energy classes that ADR-2605261100 N5 deferred to 'Funamori marine actor scope'. This ADR is constitutional-pre-evaluation only — actual Funamori marine renewable actor R0 charter is separate ADR at Funamori-actor-instantiation time. Verdict: tidal-stream + small wave PERMITTED with conditions; OTEC + salinity-gradient CONDITIONALLY PERMITTED at R&D scale; tidal-lagoon + large-array offshore wind PROHIBITED (D1 commercial-utility scale + biodiversity/displacement)."
authoritative_for:
  - "Marine renewable D1..D5 evaluation across 5 sub-classes"
  - "Tidal-stream / small wave: conditional permit ≤500 kW per device R3"
  - "OTEC + salinity-gradient: R&D conditional permit ≤100 kW R3"
  - "Tidal-lagoon barrage + large-array offshore wind: absolute prohibition (commercial-utility scale + ecosystem displacement)"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605261100
  - adr-2605252200-watatsumi-civilian-submersible-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192330-etzhayyim-extended-land-sovereignty-ocean-river-air-orbit
related:
  - 2605242745-funamori-marine-bulk-cargo-r0.md
supersedes: []
superseded_by: []
---

# ADR-2605264100: Marine renewables — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade from ADR-2605263500
**Constitutional weight**: sub-evaluation under D1..D5; offshore-renewable boundary for Funamori marine actor R0 (separate ADR)

# Context

hikari R0 §N5 deferred "offshore wind" to "Funamori marine actor scope". ADR-2605263500 §1.5 OQ-OTEC is open. This ADR closes both at the constitutional-evaluation level — actual marine renewable equipment R&D ADR happens at Funamori R0+ time.

Marine renewable classes:

| Class | Resource | Maturity | Religious-corp scale | D-gate verdict |
|---|---|---|---|---|
| **Tidal stream** | Predictable diurnal current 0.5-3 m/s | Commercial 2020s | ≤500 kW per device | PERMITTED §1 |
| **Small wave** (point-absorber, OWC < 100 kW) | Surface gravity waves 5-30 kW/m | Pilot 2025-30 | ≤100 kW per device | PERMITTED §2 |
| **OTEC** (ocean thermal energy conversion) | ΔT ≥ 20°C surface-deep | Demo 1 MW | R&D ≤100 kW | CONDITIONAL §3 |
| **Salinity-gradient** (PRO / RED) | River-mouth Δsalinity | Pilot only | R&D ≤50 kW | CONDITIONAL §4 |
| **Tidal-lagoon barrage** | Tidal range ≥ 5 m | Few sites globally | Large-utility scale | PROHIBITED §5 |
| **Large-array offshore wind** | Continental-shelf wind | Mature commercial | >10 MW scale | PROHIBITED §5 |
| **Floating offshore wind** (single turbine ≤5 MW) | Deep-water wind | Pilot | ≤5 MW per turbine | DEFERRED §6 |

# Decision

## §1 Tidal stream — CONDITIONALLY PERMITTED

| Gate | Assessment |
|---|---|
| **D1** | ✓ Tidal flow is ambient flux; device religious-corp-owned open-hardware |
| **D2** | ✓ No long-lived waste; nacelle EOL recyclable per ≥90% gate equivalent to hikari G7 |
| **D3** | ✓ No carbon |
| **D4** | ✓ No fissile |
| **D5** | ✓ Open-hardware turbine + control firmware Apache 2.0 + Rider |

**Conditions** (12 gates analogous to hikari R0 G1-G14 adapted to marine):

1. Per-device ≤500 kW rated through R3 (≤5 devices per LANDS-extended marine parcel per ADR-2605192330; ≤10 devices religious-corp aggregate through R3)
2. NO rare-earth permanent magnet (G8 of hikari R0 inherits — open-coil electrically-excited generator OR direct-drive low-speed synchronous OK)
3. Open-hardware turbine + control firmware Apache 2.0 + Rider per D5
4. LANDS-extended marine parcel per ADR-2605192330 (river/ocean/air/orbit sovereignty); parcel attestation required before installation
5. Marine-biodiversity impact assessment Council Lv6+ ≥3 per site (mammal-strike + fish-passage + benthic-scour; small-device-fleet pattern mitigates large-utility-scale impacts that drove hikari R0 N3 large-hydro ban)
6. Anti-fouling: NO copper-based / tin-based / biocidal coatings (Charter Rider §2(c)); silicone-fouling-release coating only
7. Yield Ed25519-signed per 15-min interval (analogous to hikari G11)
8. Maintenance window public on IPFS (analogous to hikari G12)
9. NO commercial utility resale (analogous to hikari G13)
10. Decommissioning + EOL plan Council-approved at commissioning
11. No state-military partnership (D4 + §1.12)
12. Annual `silenMarineRenewableReview` Council Lv6+ ≥3

## §2 Small wave — CONDITIONALLY PERMITTED

Same gate framework as §1, scaled to ≤100 kW per device, ≤3 devices per parcel through R3, ≤10 devices religious-corp aggregate. Point-absorber or oscillating-water-column (OWC) types preferred (open-hardware designs exist); overtopping types DEFERRED (require larger civil structure, biodiversity assessment more complex).

## §3 OTEC — CONDITIONALLY PERMITTED (R&D scale only)

| Gate | Assessment |
|---|---|
| **D1** | ✓ Ocean thermal gradient is ambient flux; closed-cycle (Rankine with ammonia or HFC working fluid) — note ammonia OK per ADR-2605263700 internal use |
| **D2** | ⚠ Cold-water pipe (CWP) reaches ~1000 m depth; long-term deep-ocean ecosystem disturbance via deep-water nutrient upwelling at outfall — Council Lv6+ ≥3 per-site marine-biology impact assessment |
| **D3** | ✓ No carbon |
| **D4** | ✓ Working fluid carve-out: HFC refrigerants are GWP-positive (D3 indirect) — open-cycle OTEC or NH₃ Rankine preferred; HFC PROHIBITED for working fluid |
| **D5** | ✓ Open-hardware turbo-generator + CWP + heat-exchanger Apache 2.0 + Rider |

**Conditions**:
- R&D scale only through R3: ≤100 kW per site, ≤1 site religious-corp aggregate
- Working fluid MUST be NH₃ (per ADR-2605263700 §1 if religious-corp synthesized) OR open-cycle (no working fluid, direct seawater flash-evaporation)
- Cold-water pipe ≤1000 m depth, ≤2 m diameter through R3 (limits ecological disturbance scale)
- Site selection tropical / sub-tropical LANDS-extended parcel only (ΔT ≥ 20°C requirement)
- Deep-water nutrient upwelling outfall design Council-approved (must not over-fertilize surface ecosystem)

R4+ scale (≥1 MW) requires Council Lv7+ unanimity per facility.

## §4 Salinity-gradient — CONDITIONALLY PERMITTED (R&D scale only)

PRO (pressure-retarded osmosis) and RED (reverse electrodialysis). River-mouth deployment with mixed-water discharge back to estuary.

**Conditions**:
- R&D scale only through R3: ≤50 kW per site, ≤1 site
- Membrane chemistry MUST be open-source (most commercial PRO/RED membranes are vendor-IP-encumbered — membrane R&D required)
- Estuarine ecosystem assessment Council Lv6+ ≥3 (salinity stratification disturbance + fish migration)
- mizuho R2+ cross-actor (river-water sourcing) consultation

## §5 Tidal-lagoon barrage + Large-array offshore wind — PROHIBITED

| Class | Failing gates |
|---|---|
| **Tidal-lagoon barrage** (e.g., Swansea-style multi-km wall) | D1 (commercial-utility scale typical >100 MW + state-licensing dependency) + D2 (sediment-flow + species-migration multi-gen impact ≥ 100 yr) + hikari R0 N3 large-hydro equivalent ban + N6 commercial >10 MW |
| **Large-array offshore wind** (≥10 turbines, total capacity >50 MW) | D1 (commercial-utility scale) + hikari R0 N5 (Funamori scope) + N6 (>10 MW) + commercial-vendor-IP nacelle/blade gateway + state licensing dependency |

Both PROHIBITED on triple-independent grounds.

## §6 Floating offshore wind (single turbine ≤5 MW) — DEFERRED

Single-turbine floating offshore wind at ≤5 MW per device is in a gap between hikari R0 G8 (no NdFeB — most commercial floating offshore uses direct-drive PMSG with massive NdFeB) and the marine-scope-expansion. Open-coil floating turbines are R&D scale only as of 2026. DEFERRED to ADR at Funamori R0 + 1 year (first review after Funamori instantiation).

## §7 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; path-reserved `20-actors/funamori/cells/marine_renewable_*/` for tidal_stream + wave_small + otec_pilot + salinity_gradient | None |
| **R1** | post-Council ratification of 2605263500 + this ADR + Funamori R0 + ≥1 marine-engineer on Council + LANDS-marine-parcel attested | First tidal-stream device ≤100 kW pilot OR first small-wave device ≤30 kW pilot | 1 device |
| **R2** | post-R1 + 30-day public + ≥1 year safe operation | ≤500 kW tidal OR ≤100 kW wave; first OTEC ≤50 kW R&D pilot if tropical LANDS parcel available | 5 devices aggregate |
| **R3** | post-R2 + Council Lv6+ ≥3 ecological impact pass | ≤10 devices aggregate; full sub-class deployment within caps | 10 devices |

## §8 New Lexicons (R1+)

```
com.etzhayyim.funamori.{
  marineParcelAttestation,             # LANDS-marine-parcel + bathymetry + biodiversity baseline
  marineDeviceInstallAttestation,      # per-device: type + capacity + open-hardware-CID
  marineYieldRecord,                   # 15-min intervals Ed25519-signed
  marineBiodiversityMonitoring,        # Council Lv6+ ≥3 site reports per quarter
  silenMarineRenewableReview           # annual Council Lv6+ ≥3 across all classes
}
```

# Consequences

**Positive**:
- Closes hikari R0 N5 deferral
- Tropical / coastal LANDS parcels (river estuaries, coastal land trust) gain energy substrate option
- OTEC + salinity-gradient open-hardware R&D advances open-publication state of the art

**Negative**:
- Marine deployment requires Funamori actor stand-up (separate ADR + R0 charter pending)
- Biodiversity impact assessment burden higher than terrestrial renewables
- Salt-water corrosion + biofouling + storm survival = engineering complexity / opex
- Marine licensing variance across jurisdictions

# References

- ADR-2605263500 (parent D1..D5)
- ADR-2605261100 (hikari R0 N5 + G8 inheritance)
- ADR-2605192330 (extended land sovereignty — ocean/river parcels)
- ADR-2605242745 (Funamori marine bulk cargo)
- IEC TS 62600 series — Marine energy technology standards (referenced for §1.5 biodiversity)
- IPCC SROCC 2019 — Ocean and Cryosphere report (OTEC nutrient-upwelling reference for §3)
