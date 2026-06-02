---
id: adr-2605264200-mechanical-energy-storage-d-gate-evaluation-r0
title: "Mechanical energy storage (pumped-hydro-micro / CAES / flywheel / gravity-block) — D1..D5 evaluation R0 (sub-ADR of 2605263500)"
status: proposed-pending-council-ratification
doc_type: adr
topic: mechanical-energy-storage-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 7.8
axis: constitutional
weight: 0.78
priority_note: "Sub-ADR of ADR-2605263500 D1..D5. Covers mechanical-storage classes complementary to hikari R0 chemical-battery storage (LFP / Na-ion / thermal). Verdict: pumped-hydro-micro ≤500 kW CONDITIONALLY PERMITTED with mizuho water-rights cross-actor + waqf-equivalent water-source inalienability; CAES underground PROHIBITED (geological-formation dependency D1 + multi-gen liability D2); CAES surface-vessel CONDITIONALLY PERMITTED at R&D scale ≤100 kW; flywheel ≤100 kW CONDITIONALLY PERMITTED open-hardware only; gravity-block (Energy Vault-style) CONDITIONALLY PERMITTED ≤500 kW + LANDS parcel + open-hardware."
authoritative_for:
  - "Mechanical-storage D1..D5 evaluation across 4 sub-classes"
  - "Pumped-hydro-micro conditional permit ≤500 kW + ≤100,000 m³ upper-reservoir + waqf-equivalent water inalienability"
  - "CAES underground absolute prohibition (geological formation D1 + multi-gen integrity)"
  - "Flywheel + gravity-block conditional permits R&D scale"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605261100
  - adr-2605263100-mizuho-water-sanitation-tier-b-actor-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605263600-hydrogen-economy-d-gate-evaluation-r0
supersedes: []
superseded_by: []
---

# ADR-2605264200: Mechanical energy storage — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade from ADR-2605263500
**Constitutional weight**: sub-evaluation under D1..D5

# Context

hikari R0 §2.1 covers chemical battery storage (LFP / Na-ion / thermal). Mechanical-storage classes — pumped-hydro / compressed-air / flywheel / gravity-block — are complementary (different power vs energy density vs cycle-life trade-offs) and were not addressed. ADR-2605263500 D1..D5 framework permits decision-making on these.

| Class | Round-trip η | Power scale | Energy scale | Cycle-life | Religious-corp fit |
|---|---|---|---|---|---|
| **Pumped-hydro-micro** | 75-85% | 10 kW - 10 MW | hours-days | 20,000+ | ✓ Conditional §1 |
| **CAES (compressed-air)** underground salt-cavern | 50-60% | 100 MW typical | days | 10,000+ | ✗ §2 |
| **CAES** surface-vessel | 40-55% | 10-100 kW | hours | 10,000+ | ✓ R&D §3 |
| **Flywheel** | 85-95% | 1 kW - 1 MW | minutes-hours | 100,000+ | ✓ Conditional §4 |
| **Gravity-block** (Energy Vault-style stacking crane) | 75-85% | 10 kW - 100 MW | hours-days | 20,000+ | ✓ Conditional §5 |
| **Thermal-mass** | 50-90% | hours - days | thermal only | unlimited | (Already permitted in hikari R0 §2.1) |

# Decision

## §1 Pumped-hydro-micro — CONDITIONALLY PERMITTED

≤500 kW per facility through R3. Upper reservoir ≤100,000 m³.

| Gate | Assessment |
|---|---|
| **D1** | ✓ Water = ambient flux; pump/turbine + penstock religious-corp-owned open-hardware |
| **D2** | ✓ No long-lived waste |
| **D3** | ✓ No carbon |
| **D4** | ✓ No fissile |
| **D5** | ✓ Pump-turbine + control firmware Apache 2.0 + Rider |

**Conditions** (cross-actor mizuho + LANDS):

1. Per-facility ≤500 kW; religious-corp aggregate ≤5 MW through R3
2. Upper reservoir ≤100,000 m³; head ≤200 m (micro-scale, NOT large-hydro per hikari R0 N3)
3. mizuho R2+ cross-actor consultation REQUIRED — pumped-hydro is water-stewardship; mizuho `waterSupplySourceRegistry` must register upper + lower reservoir as land-trust water rights waqf-equivalent inalienable per ADR-2605192245 (water trading prohibited)
4. Closed-loop reservoir preferred (no river withdrawal); river-fed only if mizuho G11 waqf-attestation + biodiversity Council Lv6+ ≥3
5. NO concrete dam ≥10 m height (would trigger hikari R0 N3 large-hydro ban scope); earth-fill + geomembrane lined preferred for upper reservoir
6. Pump-turbine open-hardware (most commercial PAT - pump-as-turbine - designs are vendor IP; require open-firmware retrofit before commissioning OR design-license negotiation)
7. Public maintenance schedule on IPFS
8. Annual `silenPumpedHydroReview` Council Lv6+ ≥3

## §2 CAES underground (salt-cavern / aquifer / depleted-reservoir) — PROHIBITED

| Gate | Failing |
|---|---|
| **D1** | ✗ Geological formation dependency — salt cavern / aquifer / depleted gas reservoir are commercial-scale industry geology + state-licensed mineral rights |
| **D2** | ✗ Multi-gen leak / integrity monitoring liability 100+ yr stewardship |
| hikari R0 N6 | ✗ Commercial utility scale (100+ MW typical) |

PROHIBITED on triple-independent grounds.

## §3 CAES surface-vessel — CONDITIONALLY PERMITTED (R&D scale)

Above-ground steel pressure vessel (≤200 bar) compressed-air storage. R&D scale only.

**Conditions**:
- ≤100 kW per facility, ≤1 facility religious-corp aggregate through R3
- Pressure ≤200 bar through R3; ≤300 bar R4+ Council Lv6+ ≥3
- Adiabatic CAES (heat-of-compression stored separately for re-injection on expansion) MANDATORY — diabatic CAES requires fossil-fuel reheat which fails D3
- Compressor + expander open-hardware; commercial vendor IP integration only if open-firmware retrofit feasible
- Safety per ASME BPVC Section VIII pressure-vessel framework equivalent

## §4 Flywheel — CONDITIONALLY PERMITTED

≤100 kW per device, ≤500 kW religious-corp aggregate through R3.

**Conditions**:
- Rotor material: steel laminate OR carbon-fiber composite; composite-burst containment housing MANDATORY (catastrophic-failure mode)
- Magnetic bearings preferred (no lubrication contamination), but NO NdFeB (hikari R0 G8 inherits); electromagnetic-bearing (active-control) acceptable
- Open-hardware bearing controller + motor-generator + housing design Apache 2.0 + Rider
- Vacuum housing (windage-loss reduction); vacuum pump open-hardware
- Use case: short-duration power-quality smoothing (minutes-hours) complementing chemical-battery long-duration; NOT competitive with LFP for >2-hr storage

## §5 Gravity-block stacking — CONDITIONALLY PERMITTED

Energy Vault-style crane stacking concrete / earth blocks for potential-energy storage. ≤500 kW per facility, ≤2 MW aggregate through R3.

**Conditions**:
- Crane + lift motor + control software Apache 2.0 + Rider
- Block material: low-embodied-CO₂ (earth-cement composite preferred OVER Portland cement; ADR-2605261200 igata fab can co-locate gravity-block factory using reject batch material)
- LANDS parcel siting Council Lv6+ ≥3 (visual + acoustic + footprint impact)
- Open-hardware control firmware (Energy Vault commercial system is closed-IP; pure open-source clone or third-party open-design required)
- Ground-bearing capacity geotechnical attestation per parcel

## §6 Storage technology selection guidance (cross-actor coordination)

The four mechanical-storage classes + chemical battery (hikari R0 §2.1) have different fit profiles. Religious-corp R2+ storage portfolio selection should be Council-mediated based on parcel + load profile:

| Use case | Recommended primary | Secondary |
|---|---|---|
| Sub-minute power-quality smoothing | Flywheel §4 | LFP battery |
| Minutes-to-hour load shifting | LFP battery (hikari §2.1) | Flywheel §4 |
| Hours-to-day diurnal cycling | LFP battery (hikari §2.1) + Na-ion | Pumped-hydro-micro §1 |
| Multi-day to weekly (low-renewable bridging) | Pumped-hydro-micro §1 + thermal | H₂ (ADR-2605263600) |
| Seasonal (months) | H₂ (ADR-2605263600 §1) + biomethane (ADR-2605263800) + NH₃ (ADR-2605263700) | (gravity-block sized to weeks-only is theoretically possible but capex-prohibitive) |
| Power-quality + capex-low | Gravity-block §5 (cement/earth blocks low embodied CO₂) | Pumped-hydro §1 |

## §7 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; path-reserved `20-actors/hikari/cells/storage_mechanical_*/` for pumped_hydro_micro + caes_surface + flywheel + gravity_block | None |
| **R1** | post-Council + mizuho R1 (for pumped-hydro) + ≥1 mechanical-engineer on Council | First flywheel ≤30 kW OR first gravity-block ≤50 kW pilot | 1 device |
| **R2** | post-R1 + 30-day public | First pumped-hydro-micro ≤100 kW + closed-loop reservoir OR CAES-surface ≤30 kW R&D | 3 devices |
| **R3** | post-R2 + Council Lv6+ ≥3 cross-actor mizuho ratify | Full caps per §1-5 | per-class caps |

## §8 New Lexicons (R1+)

```
com.etzhayyim.hikari.{
  pumpedHydroFacilityAttestation,         # reservoir CIDs + waqf attestation + biodiversity baseline
  caesSurfaceFacilityAttestation,         # pressure-vessel design + ASME-equivalent compliance
  flywheelDeviceAttestation,              # rotor design + burst-containment + bearing type
  gravityBlockFacilityAttestation,        # block material + crane CAD + geotechnical
  mechanicalStorageDispatchRecord,        # per-cycle: energy-in / energy-out / round-trip-η / SOC
  silenMechanicalStorageReview            # annual Council Lv6+ ≥3 per-class compliance
}
com.etzhayyim.mizuho.{
  pumpedHydroReservoirWaqfAttestation     # cross-actor: water-source registered + inalienable
}
```

# Consequences

**Positive**:
- Closes the last identified storage gap from ADR-2605263500 (chemical batteries alone capped useful storage at hour-to-day scale)
- Pumped-hydro-micro provides religious-corp multi-day-scale storage option without H₂ safety burden
- Cross-actor mizuho integration deepens water-as-energy-substrate doctrine
- Gravity-block uses igata cement-fab reject materials → cross-actor manufacturing-residual valorization

**Negative**:
- Pumped-hydro requires mizuho R2+ infrastructure + LANDS parcel with sufficient head
- CAES underground prohibited — large-scale long-duration option closed
- Flywheel composite-rotor burst is severe failure mode requiring engineering rigor
- Gravity-block visual + footprint impact may face community-objection during 30-day public period

# References

- ADR-2605263500 (parent D1..D5)
- ADR-2605261100 (hikari R0 §2.1 chemical-battery sibling)
- ADR-2605263100 (mizuho — pumped-hydro cross-actor water-rights)
- ADR-2605192245 (Land Trust waqf-equivalent extension to water sources for §1.3)
- ASME BPVC Section VIII — pressure vessel reference for §3
- IEEE 1547 — interconnection standards for §1.6 + §3 grid-tie
