---
id: adr-2605264301-csp-solar-thermal-d-gate-evaluation-r0
renumbered_from: "2605264300"
title: "Concentrated solar power (CSP) + solar-thermal process heat — D1..D5 evaluation R0 (sub-ADR of 2605263500; closes original 6-gap energy coverage list at 6/6)"
status: proposed-pending-council-ratification
doc_type: adr
topic: csp-solar-thermal-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 7.7
axis: constitutional
weight: 0.77
priority_note: "Sub-ADR of ADR-2605263500 D1..D5. Closes the last of the 6 originally identified energy-coverage gaps (cumulative: hydrogen ✓ ammonia ✓ biomethane ✓ marine ✓ mechanical-storage ✓ CSP ✓ → 6/6). CSP is the thermal-route counterpart to hikari R0 §2.1 PV-electrical solar; complements thermal-storage already permitted under hikari §2.1. Verdict: CSP small parabolic-trough + Stirling-dish CONDITIONALLY PERMITTED ≤500 kW thermal; CSP tower (heliostat-field central-receiver) DEFERRED to R2+ scaling; solar-process-heat (≤200°C) CONDITIONALLY PERMITTED for direct-use in mitsuho greenhouse + yakushi WFI + tatekata MEP."
authoritative_for:
  - "CSP D1..D5 evaluation across 3 sub-classes (parabolic-trough / Stirling-dish / tower)"
  - "Solar process heat ≤200°C direct-use conditional permit"
  - "Thermal-storage extension (molten salt small ≤10 m³; phase-change ≤5 m³) referenced from hikari §2.1"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605261100
  - adr-2605261015
  - adr-2605250500-yakushi-pharmaceutical-rd-charter
  - adr-2605250715-tatekata-construction-tier-b-actor-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605263800-biomethane-d-gate-evaluation-r0
supersedes: []
superseded_by: []
---

# ADR-2605264301: CSP + solar-thermal process heat — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade from ADR-2605263500
**Constitutional weight**: sub-evaluation under D1..D5; closes 6/6 original gap list

# Context

hikari R0 §2.1 covers **PV** (photovoltaic-electrical) solar but not **thermal** solar. CSP and solar-process-heat are constitutionally distinct: they convert sunlight to heat directly (no PV cell) and either (a) drive a thermodynamic cycle for electricity (CSP) or (b) deliver heat directly to a thermal load (process-heat). Multiple cross-actor heat consumers exist:

| Heat consumer | Temperature need | Religious-corp actor |
|---|---|---|
| Greenhouse heating + soil-warming | 30-80°C | mitsuho R2+ |
| Domestic hot water + space heating | 40-80°C | hagukumi + iyashi + facilities |
| Water for Injection (WFI) sterilization | 121°C+ (autoclave) | yakushi R2+ |
| Building radiant heating | 30-50°C | tatekata R2+ |
| Concrete curing (mass casting) | 40-80°C | igata + tatekata |
| Industrial steam (≤200°C) | 100-200°C | various (small process-heat) |
| Steam-Rankine electricity | 400-565°C (CSP tower) | hikari R2+ if CSP tower active |
| Biomass drying + char | 200-400°C | hodoki + biomethane R2+ |

# Decision

## §1 Parabolic-trough CSP — CONDITIONALLY PERMITTED

≤500 kW thermal per facility through R3.

| Gate | Assessment |
|---|---|
| **D1** | ✓ Sunlight = ambient; mirrors + receiver tubes religious-corp-owned open-hardware |
| **D2** | ✓ No long-lived waste; mirror EOL recyclable per hikari G7 |
| **D3** | ✓ No carbon |
| **D4** | ✓ No fissile |
| **D5** | ✓ Tracking control firmware + receiver design Apache 2.0 + Rider |

**Conditions**:

1. Per-facility ≤500 kW thermal through R3; religious-corp aggregate ≤2 MW thermal
2. Heat-transfer fluid (HTF) restriction: synthetic oil (Therminol VP-1 equivalent — biphenyl/diphenyl-oxide eutectic OK) OR pressurized water OR molten-salt (60% NaNO₃ / 40% KNO₃ "solar salt"); NO molten-sodium / NO molten-lead-bismuth (D2 + D4 nuclear-adjacent material risk)
3. Working fluid for downstream Rankine (if electricity gen) MUST be water-steam, NOT organic-Rankine-cycle (ORC) refrigerant (D3 indirect GHG); R&D ORC at R4+ only with HFO refrigerants ≤GWP 10 + Council Lv6+ ≥3
4. Mirror open-hardware: silvered-glass parabolic reflector is mature commodity; tracking mechanism + receiver design open-hardware per D5
5. Land-trust integration per hikari G9 — rooftop or brownfield priority; greenfield only with biodiversity-no-harm Council Lv6+ ≥3
6. Glare + heat-island public-comment period (analogous to hikari G14 light-pollution audit + acoustic)
7. Annual `silenCSPReview` Council Lv6+ ≥3

## §2 Stirling-dish CSP — CONDITIONALLY PERMITTED

≤25 kW electrical per dish (typical Stirling-dish unit size). ≤10 dishes religious-corp aggregate through R3.

**Conditions**:
- Stirling engine working fluid: helium OR hydrogen OR air (helium preferred for engine longevity; hydrogen acceptable only if green per ADR-2605263600 §1)
- Dish-tracking + Stirling control firmware Apache 2.0 + Rider
- NO rare-earth magnets in Stirling-driven alternator (G8 inherits)
- All other conditions per §1.1-§1.7

## §3 CSP tower (heliostat-field central-receiver) — DEFERRED to R2+

Heliostat-field central-receiver CSP (large solar tower) has:
- Per-facility scale ≥10 MW typically (would trigger hikari R0 N6 commercial >10 MW)
- Vendor-IP-dense heliostat tracking (BrightSource, Heliogen, etc.)
- Bird-strike concern (concentrated flux corridor)

Council Lv6+ ≥3 per-facility ADR required at R2+ if open-design heliostat field at ≤5 MW scale ever proposed; current R0 verdict = DEFERRED.

## §4 Solar process heat (≤200°C direct-use) — CONDITIONALLY PERMITTED

Direct flat-plate or evacuated-tube collector heat delivered to process-heat consumer with NO electricity generation step (efficiency 50-70% thermal vs PV+resistive 18-25% — material advantage where heat is the load).

| Gate | Assessment |
|---|---|
| **D1..D5** | All ✓ analogous to §1 |

**Conditions**:

1. Collector type: flat-plate (≤80°C) OR evacuated-tube (≤180°C); concentrating only at §1/§2 framework
2. Storage: thermal-mass (water tank ≤10 m³ OR phase-change material PCM ≤5 m³ OR rock-bed ≤20 m³); thermal storage already permitted under hikari §2.1
3. Cross-actor heat-customer attestation: each process-heat installation MUST have downstream-consumer Lexicon entry (mitsuho greenhouse / yakushi WFI / hagukumi facility / tatekata radiant / igata curing / biomethane digester heating)
4. Per-facility ≤500 kW thermal; religious-corp aggregate ≤5 MW thermal
5. Open-hardware collector + control firmware Apache 2.0 + Rider per D5

## §5 Cross-actor heat integration matrix

R3 multi-actor heat-distribution architecture:

```
solar process-heat (§4)
    ↓ via insulated piping
hikari thermal storage (water/PCM/rock-bed)
    ↓
    ├─→ mitsuho greenhouse (30-80°C)
    ├─→ hagukumi facility heating + DHW (40-80°C)
    ├─→ iyashi facility heating + DHW (40-80°C)
    ├─→ yakushi WFI preheating (80-100°C; 121°C final boost from biomethane-fired autoclave OR electric)
    ├─→ tatekata radiant floor (30-50°C)
    ├─→ igata mass-concrete curing (40-80°C; replaces electric-mat or steam-blanket)
    └─→ biomethane digester heating (mesophilic 35°C OR thermophilic 55°C)
```

R2+ heat-network attestation per cross-actor pairing.

## §6 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; path-reserved `20-actors/hikari/cells/solar_thermal_*/` for parabolic_trough + stirling_dish + flat_plate_process_heat | None |
| **R1** | post-Council ratification of 2605263500 + this ADR + ≥1 thermal-engineer on Council | First flat-plate process-heat ≤50 kW pilot serving mitsuho greenhouse OR hagukumi DHW | 1 facility |
| **R2** | post-R1 + 30-day public + cross-actor heat-customer attestation | ≤500 kW process-heat aggregate + first parabolic-trough ≤100 kW thermal pilot (R&D scale) OR first Stirling-dish ≤25 kW unit | 3 facilities |
| **R3** | post-R2 + ≥1 yr safe operation + heat-network attestation | Full caps per §1-§4; CSP-tower deferral re-evaluation if open-design heliostat ≤5 MW proposed | per-class caps |

## §7 New Lexicons (R1+)

```
com.etzhayyim.hikari.{
  cspFacilityAttestation,                   # type + capacity + HTF + open-hardware-CIDs
  solarProcessHeatFacilityAttestation,      # collector type + downstream-consumer-CIDs
  thermalStorageInventory,                  # storage medium + capacity + state-of-charge
  heatNetworkAttestation,                   # cross-actor pairing + insulation + meter
  silenCSPReview                            # annual Council Lv6+ ≥3 all sub-classes
}
```

# Consequences

**Positive**:
- Closes 6/6 of original ADR-2605263500-identified energy-coverage gaps; thermal-route solar complements PV
- Higher conversion efficiency where heat is the load (50-70% vs 18-25% via PV→resistive)
- Cross-actor heat integration unlocks mitsuho greenhouse year-round operation + yakushi WFI without grid electricity + tatekata radiant heating + igata cement curing
- Thermal storage already permitted under hikari §2.1; this ADR provides the heat SOURCE that storage can hold

**Negative**:
- Capex ~$200-500/m² collector area + $50-150/kWh thermal storage; ≤50 kW R1 ~$50-100K capex
- Direct-use heat requires customer proximity (insulated piping >100 m loses efficiency)
- Glare hazard for parabolic-trough requires public-comment period
- Stirling engine maintenance (helium seal replacement every 5-10 yr) is non-trivial

# Coverage status (closes 6-gap original list at 6/6 = 100%)

| Gap | ADR | Verdict |
|---|---|---|
| Hydrogen | 2605263600 | ✓ closed |
| Ammonia | 2605263700 | ✓ closed |
| Biomethane | 2605263800 | ✓ closed |
| Marine (OTEC/wave/tidal) | 2605264100 | ✓ closed |
| Mechanical storage | 2605264200 | ✓ closed |
| **CSP + solar process heat** | **2605264300 (this)** | **✓ closed — 6/6** |

**Next expansion candidates** (new gap-list for iteration 5+):

| Candidate | Constitutional axis | Notes |
|---|---|---|
| Geothermal deep ≥500 m + EGS | Extends hikari §2.1 micro-only | Multi-gen-induced-seismicity concern |
| Methanol/DME as energy carrier | Green-H₂ + captured CO₂ synfuel | DME diesel-substitute for wadachi R3+ |
| District heating/cooling networks | Cross-actor heat distribution | Sibling to §5 of this ADR |
| Algal biofuel | Extends 2605263500 §2.2 microbial-hydrocarbon to algal lipid pathway | Cross-actor with mitsuho aquaculture |
| Vehicle-to-grid (V2G) | Cross-actor wadachi + futawa + sarutahiko | Bidirectional battery dispatch |
| Demand-response coordination | Cross-actor scheduling | Without smart-meter PII (hikari N7) |

# References

- ADR-2605263500 (parent D1..D5)
- ADR-2605261100 (hikari R0 §2.1 PV sibling)
- ADR-2605261015 (mitsuho — heat customer)
- ADR-2605250500 (yakushi — WFI heat)
- ADR-2605250715 (tatekata — radiant + curing heat)
- IEA SolarPACES technology brief — CSP open-publication reference
- NREL Concentrating Solar Power Projects database — global open-data
