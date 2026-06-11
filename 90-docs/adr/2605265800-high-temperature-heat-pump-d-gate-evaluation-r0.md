---
id: adr-2605265800-high-temperature-heat-pump-d-gate-evaluation-r0
title: "High-temperature heat pump (HTHP, ≤200°C delivery) — D1..D5 evaluation R0 (sub-ADR of 2605263500; industrial process heat efficiency multiplier)"
status: proposed-pending-council-ratification
doc_type: adr
topic: high-temperature-heat-pump-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 6.3
axis: constitutional
weight: 0.63
priority_note: "Sub-ADR of ADR-2605263500. Adds high-temp heat pump (HTHP, sink ≤200°C) for industrial process heat to religious-corp energy substrate as a 3-5× efficiency multiplier over direct electric or combustion heat. Complements thermal-storage in hikari §2.1 + CSP §1 of 2605264300 + district network 2605265000 + waste heat recovery from DAC 2605264600 / CPV 2605265500. Verdict: CO₂ HTHP (natural refrigerant) + open-cycle steam-compression HTHP CONDITIONALLY PERMITTED ≤500 kW thermal per facility R3; HFC/HFO refrigerants ≤GWP 10 PROHIBITED R0-R3 (D3 indirect GHG); ammonia HTHP CONDITIONALLY PERMITTED via cross-actor ADR-2605263700 §1 NH₃ inventory."
authoritative_for:
  - "HTHP refrigerant chemistry D1..D5 evaluation (CO₂ / NH₃ / steam-compression / HFC-HFO)"
  - "Refrigerant cap ≤GWP 10 through R3 (natural refrigerants only)"
  - "Cross-actor waste-heat-source-pairing matrix (DAC regeneration / CPV cell-cooling / biomethane CHP / geothermal flash)"
  - "Industrial-process-heat sink consumer matrix (yakushi WFI / mitsuho greenhouse heating / igata cement curing / tatekata MEP)"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605261100
  - adr-2605263700-green-ammonia-d-gate-evaluation-r0
  - adr-2605264300-csp-solar-thermal-d-gate-evaluation-r0
  - adr-2605264500-geothermal-deep-egs-d-gate-evaluation-r0
  - adr-2605264600-direct-air-capture-d-gate-evaluation-r0
  - adr-2605265000-district-heating-cooling-d-gate-evaluation-r0
  - adr-2605265500-concentrated-pv-d-gate-evaluation-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605265700-sodium-sulfur-battery-d-gate-evaluation-r0
supersedes: []
superseded_by: []
---

# ADR-2605265800: High-temperature heat pump (HTHP) — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade

# Context

Industrial process heat from ambient (or low-grade waste) sources to ≤200°C delivery is currently a constitutional gap. Direct electric resistive heating works but wastes electricity (COP=1). HTHP with natural refrigerants achieves COP 2.5-4.0 in the 100-200°C delivery range, multiplying renewable-electricity → process-heat efficiency.

| Heat sink consumer | Temperature need | Cross-actor ADR |
|---|---|---|
| Yakushi WFI sterilization preheat | 80-100°C | 2605250500 + 2605264300 §5 |
| Mitsuho greenhouse / cold-storage heat-pump heating | 30-50°C | 2605261015 + 2605264300 §5 |
| Tatekata radiant floor / building DHW | 30-60°C | 2605250715 |
| Igata cement-curing thermal blanket | 40-80°C | 2605261200 |
| DAC §1 solid-amine sorbent regeneration | 80-100°C | 2605264600 |
| Biomethane digester (thermophilic) heating | 55°C | 2605263800 |
| **Industrial process steam ≤200°C** (chemistry / food processing) | **100-200°C** | **NEW domain — closes a gap** |

HTHP refrigerant classes:

| Refrigerant | GWP | Sink temp | Religious-corp fit |
|---|---|---|---|
| **CO₂ (R-744)** | 1 (reference) | up to 90°C | ✓ §1 (natural refrigerant) |
| **NH₃ (R-717)** | 0 | up to 110°C | ✓ §1 (cross-actor 2605263700) |
| **Steam (R-718)** | 0 | 100-200°C | ✓ §1 (open-cycle mechanical vapor recompression) |
| **HFC-134a / HFC-32 / etc.** | 1500-3500 | up to 130°C | ✗ §2 (D3 indirect GHG) |
| **HFO-1234yf / HFO-1233zd / etc.** | <10 | up to 150°C | ⚠ §3 (deferred R4+ pending atmospheric stability) |

# Decision

## §1 Natural-refrigerant HTHP — CONDITIONALLY PERMITTED

≤500 kW thermal per facility through R3; ≤5 facilities = ≤2.5 MW aggregate.

| Gate | Assessment |
|---|---|
| **D1** | ✓ Religious-corp-owned compressor + heat exchanger + refrigerant inventory; ambient or waste heat is ambient flux |
| **D2** | ✓ Natural refrigerants short-cycle environmental impact; equipment EOL recyclable per analog of hikari G7 |
| **D3** | ✓ CO₂ refrigerant GWP=1 reference; NH₃ GWP=0; steam GWP=0; electricity input from religious-corp renewable per ADR-2605215000 |
| **D4** | ✓ No fissile |
| **D5** | ✓ Compressor + control firmware Apache 2.0 + Rider; refrigerant cycle design open-hardware |

**Conditions per refrigerant**:

1. **CO₂ (R-744) HTHP** — transcritical Brayton or trans-CO₂ cycle; sink temperature ≤90°C through R3; pressure ≤120 bar; suitable for DAC regeneration / DHW / mitsuho greenhouse heating / building HVAC heat-pump-heating
2. **NH₃ (R-717) HTHP** — sink temperature ≤110°C through R3; ≤200 kg NH₃ refrigerant inventory per facility (well below ADR-2605263700 §1.6 storage cap); cross-actor: NH₃ refrigerant produced via ADR-2605263700 §1 green NH₃ pathway; toxic-gas safety per 2605263700 §1.9 (OSHA 1910.111 + ASME B31.3); facility location ≥50 m from residential adjacency
3. **Steam (R-718) HTHP open-cycle MVR (mechanical vapor recompression)** — sink temperature ≤200°C; primary use case for industrial process steam (chemistry / food processing / sterilization); ≤500 kW thermal; open-cycle (compresses ambient steam to higher pressure)

**Cross-conditions all natural-refrigerant variants**:

4. **Compressor open-hardware**: screw / scroll / centrifugal / reciprocating; design + control firmware Apache 2.0 + Rider per D5; commercial vendor IP retrofit if needed
5. **Heat-source pairing matrix** (HTHP needs a heat source from which to "pump"; the pairing matters for COP):
   - **Best**: waste heat from DAC §1 regeneration / CPV cell-cooling / biomethane CHP / geothermal flash (40-90°C feed → ~3-4× COP)
   - **Good**: ambient air (winter -10°C → 50°C lift = ~2.5× COP)
   - **Acceptable**: ground / water-source heat exchanger
6. **Electrical input MUST be religious-corp renewable** per ADR-2605215000 / hikari §2.1
7. **COP attestation MANDATORY**: per facility commissioning + annual cycle; published on IPFS (transparency analog of hikari G6 grid-impact reporting)
8. **No vapor-compression in food-grade applications WITHOUT ammonia-detection + auto-shutoff** (toxicity safety — NH₃ above 25 ppm in food space triggers automatic shutdown)
9. ≤500 kW thermal per facility; aggregate ≤2.5 MW
10. Annual `silenHthpReview` Council Lv6+ ≥3

## §2 HFC-refrigerant HTHP — PROHIBITED

| Refrigerant | Failing gate |
|---|---|
| HFC-134a | D3 (GWP-1430 indirect-GHG; persistent atmospheric) |
| HFC-32 | D3 (GWP-675) |
| HFC-410A / HFC-407C / etc. | D3 (GWP-1700-2100) |
| R-22 (HCFC, Montreal Protocol phased out) | D3 (GWP-1810) + D2 (ozone-depletion legacy) |
| R-12 (CFC, Montreal Protocol banned) | D3 + D2 |

ABSOLUTELY PROHIBITED on D3 grounds.

## §3 HFO-refrigerant HTHP — DEFERRED to R4+

HFOs (1234yf, 1233zd, etc.) have GWP <10 which technically passes §1.D3 ceiling. However, atmospheric stability + TFA (trifluoroacetic acid) hydrolysis byproduct emerging concern (persistent + bioaccumulative). DEFERRED to R4+ pending peer-reviewed environmental impact resolution.

## §4 Heat-pump pairing with §2.2 microbial-hydrocarbon biosynthesis combustion

Religious-corp closed-loop microbial hydrocarbon (ADR-2605263500 §2.2) provides ≤10 t/yr alkanes through R3. Combustion of these alkanes in stationary CHP recovers thermal energy; HTHP can extract additional heat from flue gas via gas-phase heat exchanger (sub-condensing economizer) before atmospheric venting. This adds 5-10% energy recovery to the closed-loop microbial pathway — cross-actor synergy.

## §5 Cross-actor heat-network integration

HTHP delivers heat to ADR-2605265000 district network OR to specific cross-actor consumers per §1 matrix. Per-facility consumer ADR required:

```
HTHP (≤500 kW thermal, ≤200°C delivery)
    ↓
   ADR-2605265000 §1 4GDH/5GDH district inlet (50-80°C)
    ↓
    ├─→ mitsuho greenhouse heating + cold-storage refrigeration
    ├─→ tatekata radiant floor + DHW
    ├─→ yakushi WFI preheat (+ biomethane autoclave for final 121°C boost)
    ├─→ iyashi/hagukumi DHW
    ├─→ igata cement-curing thermal mass
    ├─→ DAC §1 sorbent regeneration heat
    ├─→ biomethane digester thermophilic heating
    └─→ industrial process steam ≤200°C (open-cycle MVR variant per §1.3)
```

## §6 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; path-reserved `20-actors/hikari/cells/hthp_co2/` + `hthp_nh3/` + `hthp_mvr_steam/` import-time RuntimeError | None |
| **R1** | post-Council + ≥1 refrigeration-engineer on Council + first heat-customer cross-actor attestation | First CO₂ HTHP ≤50 kW pilot for DAC R1 sorbent regeneration OR mitsuho greenhouse heating | 50 kW |
| **R2** | post-R1 + 30-day public + COP attestation + 1-yr safe operation | ≤200 kW per facility + first NH₃ HTHP (post-ADR-2605263700 R2 NH₃ supply) OR first steam-MVR for yakushi WFI | 200 kW per facility |
| **R3** | post-R2 + Council Lv6+ ≥3 + full COP attestation + cross-actor consumer attestations | Full §1 caps; HFO §3 re-evaluation if atmospheric studies resolve | 2.5 MW aggregate |

## §7 New Lexicons (R1+)

```
com.etzhayyim.hikari.{
  hthpFacilityAttestation,             # refrigerant class + sink temp + capacity + compressor design CID
  hthpRefrigerantInventory,            # per-facility refrigerant kg + class + leak-monitor
  hthpCopAttestation,                  # commissioning + annual: COP at design + actual operating points + heat source/sink
  silenHthpReview                      # annual Council Lv6+ ≥3 refrigerant chain + COP + safety audit
}
```

# Consequences

**Positive**:
- 3-5× efficiency multiplier vs direct electric resistive heat for ≤200°C industrial process applications
- Natural-refrigerant-only constraint preempts the HFC phase-down regulatory churn that has dominated commercial HVAC IP for 30+ years
- Cross-actor heat-network synergy: HTHP pairs naturally with waste-heat sources (DAC / CPV / biomethane / geothermal) and process-heat sinks (yakushi / mitsuho / igata / DAC regeneration loop)
- Steam-MVR variant unlocks industrial process steam ≤200°C without combustion (a non-trivial decarbonization step for religious-corp chemistry / food)

**Negative**:
- CO₂ HTHP requires high-pressure (≤120 bar) components — engineering complexity
- NH₃ HTHP toxicity burden — facility siting + leak-detection requirements
- Steam-MVR initial capex high (industrial-grade compressors for steam are expensive)
- COP degrades at high-temperature-lift (winter ambient → 200°C sink may drop COP to <2; pairing strategy matters)

# Alternatives Considered

- **Permit HFCs as transitional**: rejected per §2 D3 ban
- **Defer all HTHP until R4+ when HFO atmospheric stability resolved**: considered — but natural refrigerants are mature now; HFO is the third option not the only path
- **Direct electric resistive heat only (no HTHP)**: status quo — wastes 60-75% of renewable electricity at the heat conversion step; constitutionally permitted but operationally suboptimal

# References

- ADR-2605263500 (parent D1..D5)
- ADR-2605265000 (district network heat-distribution cross-actor)
- ADR-2605263700 (NH₃ refrigerant cross-actor)
- ADR-2605264300 §5 (heat-network architecture predecessor)
- ADR-2605264500 (geothermal flash heat-source cross-actor)
- ADR-2605264600 §1 (DAC regeneration heat-source/sink cross-actor)
- ADR-2605265500 (CPV cell-cooling heat-source cross-actor)
- IEA HTHP Task 1-7 (HPT-AN58) — open-publication HTHP tech state reference
- ASHRAE Standard 34 — refrigerant safety classification reference
- IPCC AR6 WG1 — GWP values for §2 prohibition basis
