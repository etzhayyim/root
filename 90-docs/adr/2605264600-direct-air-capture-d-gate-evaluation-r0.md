---
id: adr-2605264600-direct-air-capture-d-gate-evaluation-r0
title: "Direct air capture (DAC) of atmospheric CO₂ — D1..D5 evaluation R0 (sub-ADR of 2605263500; closed-loop synfuel feedstock enabler)"
status: proposed-pending-council-ratification
doc_type: adr
topic: direct-air-capture-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 7.5
axis: constitutional
weight: 0.75
priority_note: "Sub-ADR of ADR-2605263500. Closed-loop atmospheric CO₂ capture for: (a) §2.2 microbial-hydrocarbon photobioreactor feedstock, (b) future methanol/DME synfuel feedstock (cross-actor wadachi/sarutahiko diesel-substitute), (c) co-product from §2.3 of 2605264500 geothermal-deep gas capture. Verdict: small-scale DAC ≤1 t CO₂/day CONDITIONALLY PERMITTED with religious-corp open-sorbent + open-hardware. Carbon-offset commercial sale ABSOLUTELY PROHIBITED (hikari N8 + Charter §2(b) financialization-of-atmosphere ban inherits)."
authoritative_for:
  - "DAC sorbent technology D1..D5 evaluation (solid amine / liquid hydroxide / mineralization)"
  - "Captured-CO₂ utilization scope (synfuel + agricultural + microbial-feedstock + mineralization)"
  - "Carbon-offset commercial sale absolute prohibition (no atmospheric financialization)"
  - "CCS commercial-vendor + state-licensed geological-sequestration prohibition (D1 + D2 multi-gen)"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605261100
  - adr-2605263800-biomethane-d-gate-evaluation-r0
  - adr-2605264500-geothermal-deep-egs-d-gate-evaluation-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605263600-hydrogen-economy-d-gate-evaluation-r0
supersedes: []
superseded_by: []
---

# ADR-2605264600: Direct air capture (DAC) — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade

# Context

ADR-2605263500 §2.2 (microbial hydrocarbon) permits atmospheric-CO₂-only feedstock and EXPLICITLY excludes fossil-flue-gas CO₂ recycling. ADR-2605263800 (biomethane) captures upgrading-stripped CO₂ for downstream use including microbial photobioreactor or greenhouse fertilization. Future methanol/DME synfuel ADRs (not yet drafted) require captured CO₂ + green H₂ as feedstock.

The common requirement across these use cases: **religious-corp-owned source of atmospheric CO₂** that is NOT commercial fossil-CCS (which fails D1 + D2 per ADR-2605263600 §2 blue-H₂ analysis) and NOT atmospheric-carbon-offset commercial market (which fails Charter §2(b) financialization).

Direct air capture (DAC) technology classes:

| Class | Sorbent / mechanism | TRL | Energy intensity | Religious-corp fit |
|---|---|---|---|---|
| **Solid-amine swing (S-DAC)** | Amine-functionalized porous solid; temperature-swing OR vacuum-swing | 7-8 (Climeworks Orca 2021, Mammoth 2024) | ~2-3 GJ/t CO₂ thermal | ✓ §1 |
| **Liquid hydroxide (L-DAC)** | KOH/NaOH absorption + Ca(OH)₂ regeneration cycle | 7 (Carbon Engineering pilot) | ~5-9 GJ/t CO₂ + electricity | ⚠ §2 |
| **Mineralization** | CO₂ + Mg/Ca silicate → carbonate (in situ basalt OR ex situ olivine) | 6-7 | Modest energy + abundant rock | ✓ §3 |
| **Electrochemical** | pH-swing or redox-active sorbent | 4-5 | High electricity intensity | DEFERRED §4 |
| **Geological CCS** (post-capture sequestration in saline aquifer / depleted reservoir) | Underground injection | 8-9 commercial | n/a | PROHIBITED §5 |

# Decision

## §1 Solid-amine swing DAC (S-DAC) — CONDITIONALLY PERMITTED

≤1 t CO₂/day capture per facility; ≤3 facilities religious-corp aggregate through R3 (= ≤3 t CO₂/day = ~1100 t CO₂/yr aggregate cap).

| Gate | Assessment |
|---|---|
| **D1** | ✓ if sorbent religious-corp-synthesized OR open-formula commodity; air = ambient flux; contactor + regeneration hardware religious-corp-owned open-hardware |
| **D2** | ✓ Spent sorbent (amine-on-silica typical) end-of-life is non-hazardous; thermal regeneration is the standard cycle (no liquid waste stream) |
| **D3** | ✓ DAC is by definition net-atmospheric-CO₂-reducing per pass; closed-loop when captured CO₂ is utilized in same-cycle synthesis (vs sequestered) |
| **D4** | ✓ No fissile |
| **D5** | ✓ Sorbent formulation MUST be open-publication; contactor + control firmware Apache 2.0 + Rider |

**Conditions**:

1. Per-facility ≤1 t CO₂/day through R3; religious-corp aggregate ≤3 t CO₂/day
2. **Sorbent open-formula**: amine chemistry (typical PEI / TEPA / diamine-on-silica) MUST be open-publication; NO commercial sorbent (Climeworks proprietary / Carbon Engineering proprietary / Heirloom proprietary) — religious-corp synthesizes from open-publication recipes OR procures commodity open-formula sorbent
3. Regeneration heat source: must be religious-corp renewable (hikari §2.1 solar-thermal collector per ADR-2605264300 OR geothermal medium-depth per ADR-2605264500 §1 OR biomethane CHP waste-heat per ADR-2605263800 §1.7(a)); NO commercial fossil natural-gas regeneration (D3 closed-loop)
4. **Captured CO₂ utilization restriction** (this is the KEY constraint): captured CO₂ MUST flow to one of:
   - §2.2 microbial-hydrocarbon photobioreactor feedstock (ADR-2605263500)
   - Future methanol/DME synfuel reactor (TBD ADR)
   - Greenhouse fertilization (mitsuho R2+; agronomically beneficial at 800-1500 ppm)
   - Beverage / food-grade CO₂ for religious-corp internal use only
   - Mineralization §3 of this ADR
   - **NO commercial sale**; **NO geological sequestration** §5; **NO carbon-offset registry credit** §6
5. Open-hardware contactor + blower + control firmware Apache 2.0 + Rider per D5
6. Air-quality + acoustic public-comment period at commissioning (blower noise + airflow ≥10,000 m³/h per t-CO₂/day capacity)
7. Annual `silenDacReview` Council Lv6+ ≥3: mass-balance audit (atmospheric in → captured out → downstream utilization)

## §2 Liquid hydroxide DAC (L-DAC) — CONDITIONALLY PERMITTED with stricter conditions

Higher energy intensity + caustic chemical handling burden. Permitted under §1 conditions PLUS:

1. ≤500 kg CO₂/day per facility (half of §1 scale due to caustic handling complexity)
2. KOH/NaOH inventory ≤1 t aggregate; Ca(OH)₂ regeneration loop MUST be closed (no commercial caustic procurement after initial stock)
3. Pellet-regeneration calciner heat source: same restrictions as §1.3 (renewable only)
4. Council Lv6+ ≥4/7 per facility commissioning (higher than §1 due to chemical-handling risk)

## §3 Mineralization (ex situ olivine / serpentine OR in situ basalt) — CONDITIONALLY PERMITTED

CO₂ + Mg₂SiO₄ (forsterite) → MgCO₃ + SiO₂ is thermodynamically downhill (-89 kJ/mol) but kinetically slow. Religious-corp ex-situ pathway = grind olivine + react with captured CO₂ in pressurized aqueous slurry; in-situ pathway = inject CO₂-saturated water into basalt formation (CarbFix Iceland precedent).

**Conditions**:

1. Ex-situ scope only through R3 (in-situ injection has aquifer + induced-seismicity overlap with ADR-2605264500 §2 EGS regulatory regime — defer to R4+ per-site)
2. Olivine sourcing: mineral-resource Charter §2(g) audit (no Uyghur-mined / conflict-zone material); preferred = ex-mine-tailings reuse (cross-actor with future kanayama metallurgy ADR ADR-2605252400 olivine-bearing tailings)
3. Carbonate product disposition: aggregate / construction-fill use (cross-actor tatekata / igata) OR religious-corp landscape soil amendment; NO commercial mineral sale (Charter §2(b) financialization-adjacent)
4. ≤10 t CO₂/day per facility through R3 (mineralization is highest-scale of three permitted classes)

## §4 Electrochemical DAC — DEFERRED to R3+

Electrochemical pH-swing (Verdox-style) or redox-active sorbents are R&D-frontier (TRL 4-5 as of 2026). DEFERRED to R3+ per-program ADR.

## §5 Geological CCS (saline aquifer / depleted reservoir / coal seam) — PROHIBITED

| Failing gate |
|---|
| **D1** — geological injection requires state mineral-rights licensing + commercial CCS-vendor (Aker Carbon Capture, Equinor, etc.) ecosystem dependency |
| **D2** — multi-gen leak / migration / induced-seismicity stewardship 1000+ yr (NETL guidance); fails D2 ≤100 yr bound except Council Lv7+ per increment which is operationally infeasible at CCS scale |
| ADR-2605264500 §3 (CAES-underground parallel) | Same geological-formation-dependency D1 violation |

PROHIBITED on triple-independent grounds.

## §6 Carbon-offset commercial market sale — ABSOLUTELY PROHIBITED

| Failing |
|---|
| hikari R0 N8 ("Carbon offset trading — financialization of atmosphere violates §2(g) + §2(b)") |
| Charter §2(b) — financialization of public-goods atmosphere |
| Verra / Gold Standard / ACR registry participation = commercial-vendor dependency D1 |
| Voluntary-carbon-market secondary trading = financial-derivative-of-atmosphere |

Religious-corp DAC captured CO₂ is for religious-corp-internal closed-loop use **only**. No issuance / sale / trading of carbon credits, voluntary-market certificates, removal-tonne attestations to third parties. **Council Lv7+ unanimity to amend** (essentially permanent).

## §7 Cross-actor utilization matrix

```
DAC captured CO₂ (§1-3)
    ↓
    ├─→ §2.2 microbial-hydrocarbon photobioreactor (closed-loop alkane synthesis)
    ├─→ future methanol/DME synfuel reactor (green H₂ + CO₂ → CH₃OH or DME)
    ├─→ mitsuho R2+ greenhouse CO₂ enrichment 800-1500 ppm
    ├─→ food-grade CO₂ for facility use (carbonation / inertization)
    ├─→ §3 mineralization (permanent storage as carbonate)
    ↑
    co-product CO₂ feeds from:
    ├─→ ADR-2605263800 biomethane upgrading PSA tail-gas
    └─→ ADR-2605264500 §1.6 geothermal-deep co-produced non-condensable gas
```

## §8 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; path-reserved `20-actors/hikari/cells/dac_*/` for solid_amine + liquid_hydroxide + mineralization | None |
| **R1** | post-Council + ≥1 sorbent-chemist on Council + microbial-hydrocarbon R1 OR mitsuho greenhouse R2 demand-attested | Solid-amine bench ≤10 kg CO₂/day pilot serving §2.2 microbial reactor OR mitsuho greenhouse | 1 facility |
| **R2** | post-R1 + 30-day public + cross-actor utilization attestation | ≤1 t CO₂/day per facility + first mineralization ≤5 t CO₂/day pilot if cross-actor kanayama olivine tailings available | 3 facilities |
| **R3** | post-R2 + Council Lv6+ ≥3 + ≥1 yr safe operation | Full caps §1-3; methanol/DME synfuel feedstock activated if synfuel ADR ratified separately | per-class caps |

## §9 New Lexicons (R1+)

```
com.etzhayyim.hikari.{
  dacFacilityAttestation,                  # technology + capacity + sorbent open-formula CID + regen heat source
  dacCaptureRecord,                        # per-batch: t CO₂ captured + sorbent cycle + heat consumed
  dacUtilizationManifest,                  # downstream-CID per kg utilized (microbial / mitsuho / synfuel / mineral)
  dacMineralizationProductRecord,          # per-batch carbonate product + downstream consumer
  silenDacReview                           # annual Council Lv6+ ≥3 mass-balance + utilization audit
}
```

# Consequences

**Positive**:
- Closes the closed-loop-carbon enabler for §2.2 microbial-hydrocarbon at scale beyond what biomethane CO₂ upgrading can provide
- Opens methanol/DME synfuel pathway for cross-actor wadachi/sarutahiko diesel-substitute (future ADR)
- Mineralization provides permanent religious-corp-owned negative-emissions option without geological-formation dependency
- Cross-actor with mitsuho greenhouse + kanayama tailings + tatekata aggregate = circular material economy

**Negative**:
- DAC energy intensity 2-9 GJ/t CO₂ is substantial — at religious-corp 3 t/day aggregate ≈ 6-27 MWh/day for regeneration heat alone
- Sorbent capex ~$200-500/t-CO₂/yr capacity; ≤10 kg/day R1 pilot ~$50-150K capex
- Caustic handling burden (L-DAC) requires dedicated safety culture
- Olivine mining (if not tailings-reuse) is environmental impact — mitigated by §3.2 ex-mine-tailings preference

# Alternatives Considered

- **Permit commercial CCS partnership**: rejected per §5 D1+D2+ADR-2605264500 §3 parallel
- **Permit voluntary carbon-credit sale**: rejected per §6 N8 + Charter §2(b)
- **DAC as only closed-loop-carbon source (deprecate biomethane CO₂)**: rejected — biomethane already captures concentrated CO₂ for free as upgrading by-product; DAC is the marginal-source closing what biomethane cannot supply

# References

- ADR-2605263500 (parent D1..D5 + §2.2 microbial-hydrocarbon downstream consumer)
- ADR-2605263600 (hydrogen — feedstock for future methanol/DME)
- ADR-2605263800 (biomethane — CO₂ co-product upstream feed)
- ADR-2605264500 (geothermal-deep — CO₂ co-product upstream feed §1.6)
- IEA DAC Outlook 2023 — open-publication tech state
- CarbFix Iceland — §3 in-situ basalt mineralization precedent (referenced as deferral basis, not adopted at R0)
- NETL CCS multi-gen stewardship guidance — §5 prohibition basis
- Verra / Gold Standard registry documentation — §6 commercial-offset-market prohibition reference
