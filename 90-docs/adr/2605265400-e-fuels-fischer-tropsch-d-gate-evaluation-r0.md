---
id: adr-2605265400-e-fuels-fischer-tropsch-d-gate-evaluation-r0
title: "e-Fuels Fischer-Tropsch full product slate (diesel + naphtha + waxes + lubricants) — D1..D5 evaluation R0 (sub-ADR of 2605263500; sibling of methanol/DME 2605264700 + SAF 2605265200 §2 e-Jet-FT)"
status: proposed-pending-council-ratification
doc_type: adr
topic: e-fuels-fischer-tropsch-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 6.7
axis: constitutional
weight: 0.67
priority_note: "Sub-ADR of ADR-2605263500. ADR-2605264700 covers methanol+DME from green H₂+DAC CO₂. ADR-2605265200 §2 covers e-Jet via FT. This ADR completes the FT product slate: diesel-range C12-C20 + naphtha C5-C11 + heavy paraffinic wax C20+ + group-V lubricant base oil. All pathways share the same upstream (reverse water-gas-shift → syngas → FT) but post-FT hydrocracking + isomerization tunes product distribution. Verdict: full FT slate CONDITIONALLY PERMITTED ≤500 kg/yr aggregate of all non-jet products through R3; commercial off-take of any product PROHIBITED."
authoritative_for:
  - "FT product-slate D1..D5 across diesel / naphtha / wax / lubricant"
  - "Anderson-Schulz-Flory distribution + downstream upgrading shared infrastructure with SAF e-Jet pathway"
  - "Religious-corp-internal cross-actor product routing (diesel → wadachi/sarutahiko backup; naphtha → algae solvent; wax → mitsuho crop protection; lubricant → kuni-umi robotics)"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605263600-hydrogen-economy-d-gate-evaluation-r0
  - adr-2605264600-direct-air-capture-d-gate-evaluation-r0
  - adr-2605264700-methanol-dme-synfuel-d-gate-evaluation-r0
  - adr-2605265200-saf-sustainable-aviation-fuel-d-gate-evaluation-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605265300-cellulosic-ethanol-d-gate-evaluation-r0
supersedes: []
superseded_by: []
---

# ADR-2605265400: e-Fuels FT full product slate — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade

# Context

Fischer-Tropsch produces a range of hydrocarbons following Anderson-Schulz-Flory (ASF) distribution; the average chain length is tuned via catalyst + reactor conditions:

| Product cut | Chain length | Religious-corp use |
|---|---|---|
| LPG | C3-C4 | Limited (DME from 2605264700 §2 covers most C2-class roles) |
| Naphtha | C5-C11 | Chemistry-feedstock solvent; algal-lipid extraction (alternative to hexane per ADR-2605264800) |
| Jet kerosene | C8-C16 | ADR-2605265200 §2 (SAF e-Jet-FT) |
| Diesel | C12-C20 | wadachi/sarutahiko/suki R3+ backup fuel (alternative to DME from 2605264700) |
| Heavy paraffinic wax | C20-C40 | mitsuho crop-protection waxes (organic apple coating, anti-desiccation) |
| Lubricant base oil (Group V isomerized) | C30-C50 | kuni-umi robotics + tatekata machinery + igata mold-release |

# Decision

## §1 FT full product slate from green H₂ + DAC CO₂ — CONDITIONALLY PERMITTED

≤500 kg/yr aggregate religious-corp non-jet FT product through R3 (ADR-2605265200 §2 e-Jet ≤300 kg/yr counted separately).

| Gate | Assessment |
|---|---|
| **D1..D5** | All ✓ (parallel to methanol ADR-2605264700 §1 and SAF ADR-2605265200 §2 reasoning) |

**Conditions**:

1. **Stoichiometry chain-of-custody MANDATORY**: every product batch carries `eFuelFtBatchAttestation` Lexicon citing source `hydrogenProductionAttestation` + `dacCaptureRecord` CIDs with mass-balance ≥95%
2. **Co-product routing**: ASF distribution gives unavoidable co-products; routing matrix:
   - Diesel cut (C12-C20) → wadachi/sarutahiko/suki R3+ ICE backup (cross-actor consumer ADR required per actor)
   - Jet cut (C8-C16) → ADR-2605265200 §2 e-Jet pathway (not counted in this ADR cap)
   - Naphtha (C5-C11) → algal-lipid extraction solvent (cross-actor ADR-2605264800 §1 alternative to hexane) OR future religious-corp olefin chemistry
   - Wax (C20-C40) → mitsuho apple/citrus coating (food-grade attestation Council Lv6+ ≥3); cross-actor with manabi science-education programs (paraffin wax for chemistry / candle-making heritage skills)
   - Lubricant (C30-C50, isomerized via dewaxing + hydroisom) → kuni-umi robotics + tatekata heavy machinery + igata mold-release agent
3. **Catalyst**: cobalt-based FT for higher-MW products (diesel + wax + lubricant) — cobalt supply Charter §2(g) audit mandatory (NO DRC-conflict cobalt); iron-based FT for lighter cuts; religious-corp catalyst recycling ≥90% per cycle
4. **Reactor type**: slurry-bubble-column or multi-tubular fixed-bed; both open-design at R&D scale; commercial Sasol / Shell SMDS / BP designs may be referenced for engineering choices but not licensed (open-clean-room implementation per D5)
5. **Hydrocracking + isomerization downstream stages**: NiMo/Al₂O₃ or Pt/zeolite catalysts; same supply-chain + open-formula constraints as ADR-2605264800 §3 HVO route
6. Use restriction: religious-corp-internal only (NO commercial sale of any product cut; transport-fuel blending into commercial diesel pool PROHIBITED — analogous to ADR-2605264700 §1.7)
7. **Operating conditions**: 200-250°C / 20-40 bar (LTFT — low-temperature FT) preferred over HTFT (300-350°C, more cobalt + iron-mix); ≤40 bar through R3
8. **Wax product food-grade attestation gate**: paraffin wax destined for mitsuho food-coating use REQUIRES Council Lv6+ ≥3 per batch food-grade purity + chain-length-spec attestation; non-food-grade wax routes only to non-edible applications
9. Annual `silenEFuelFtReview` Council Lv6+ ≥3: feedstock chain audit + product-cut routing + cross-actor consumer attestation + recycling-rate confirmation

## §2 Cross-actor consumer registry (R3+ activation gate)

Same consumer-ADR pattern as ADR-2605264700 §3:

| Consumer actor | Product cut | Required ADR |
|---|---|---|
| wadachi R3+ light EV (alt-fuel backup) | Diesel C12-C20 OR DME | wadachi diesel/DME consumer ADR (separate) |
| sarutahiko R3+ heavy Class-8 | Diesel C12-C20 OR DME | sarutahiko diesel/DME consumer ADR (separate) |
| suki R3+ farm tractor | Diesel C12-C20 OR DME | suki consumer ADR |
| algal-lipid extraction (ADR-2605264800 §1.7) | Naphtha C5-C11 (hexane substitute) | Direct cross-actor; no separate consumer ADR (chemistry-feedstock) |
| mitsuho R2+ orchard | Wax C20-C40 (food-grade) | mitsuho food-grade-wax consumer ADR |
| kuni-umi robot fleet | Lubricant C30-C50 | kuni-umi lubricant-spec ADR |
| tatekata machinery R2+ | Lubricant + naphtha | tatekata consumer ADR |
| igata mold-release | Wax + lubricant blend | igata consumer ADR |
| manabi science-education programs | Paraffin wax samples + naphtha lab-solvent | manabi cross-actor ADR (educational-use) |

## §3 Anderson-Schulz-Flory α-tuning policy

ASF distribution: weight fraction of product with chain length n ∝ n × α^(n-1) × (1-α)² where α is chain-growth probability. Higher α = more long chains.

| Operating target | α typical | Dominant product |
|---|---|---|
| Diesel-maximizing | 0.85-0.90 | C12-C20 peak |
| Wax-maximizing | 0.92-0.95 | C30+ |
| Naphtha-maximizing | 0.75-0.80 | C5-C11 |

Religious-corp R3+ runs the slate Council-balanced based on aggregate cross-actor demand quarterly. Single-product optimization at the expense of co-product surplus is wasteful (forces flaring or downgrade); production planning is multi-actor Council-mediated.

## §4 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; path-reserved `20-actors/hikari/cells/ft_diesel_wax_lubricant/` import-time RuntimeError | None |
| **R1** | post-Council + ADR-2605264700 R1 methanol+DME baseline + ADR-2605265200 R1 SAF baseline + ≥1 FT-catalysis-engineer on Council | Bench ≤5 kg/yr aggregate non-jet FT product (any α-tune) | 5 kg/yr |
| **R2** | post-R1 + 30-day public + first cross-actor consumer-ADR ratified | ≤50 kg/yr + first downstream upgrading (hydrocracking + isomerization) | 50 kg/yr |
| **R3** | post-R2 + Council Lv6+ ≥3 + multi-cut routing attested | Full §1 cap; ASF α-tuning per quarterly cross-actor demand plan | 500 kg/yr |

## §5 New Lexicons (R1+)

```
com.etzhayyim.hikari.{
  eFuelFtBatchAttestation,             # per-batch FT slate + H2 CID + DAC-CO2 CID + α value + product cut breakdown
  eFuelFtProductCutRouting,            # per-cut: kg + downstream consumer CID + food-grade-attestation (for wax)
  silenEFuelFtReview                   # annual Council Lv6+ ≥3 mass-balance + slate-routing audit
}
```

# Consequences

**Positive**:
- Completes the green-H₂ + DAC-CO₂ → liquid hydrocarbon synfuel matrix (methanol/DME + jet + diesel + naphtha + wax + lubricant covered)
- Co-product routing unlocks cross-actor circular economy (algal-extraction naphtha, mitsuho food-grade wax, kuni-umi robotics lubricant)
- ASF α-tuning policy gives Council strategic lever over religious-corp synfuel mix without single-product over-investment

**Negative**:
- ASF inevitability means single-product targeting always has co-product surplus
- Wax food-grade purity attestation burden (cross-actor mitsuho food chain)
- Cobalt catalyst supply-chain monitoring
- Capex shared with methanol/DME + SAF makes per-product capex hard to attribute (Public Fund shared-cost accounting via toritate cross-actor)

# References

- ADR-2605263500 (parent D1..D5)
- ADR-2605264700 (methanol/DME sibling synfuel — methanol from same upstream feedstock; complementary product distribution)
- ADR-2605265200 §2 (SAF e-Jet-FT — same upstream + downstream jet-cut from same reactor)
- ADR-2605263600 (H₂)
- ADR-2605264600 (DAC CO₂)
- Anderson, R. B. "The Fischer-Tropsch Synthesis" (Academic Press, 1984) — public-domain FT chemistry reference
- de Klerk, A. "Fischer-Tropsch Refining" (Wiley, 2011) — open-publication
