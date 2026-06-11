---
id: adr-2605265200-saf-sustainable-aviation-fuel-d-gate-evaluation-r0
title: "Sustainable aviation fuel (SAF) — D1..D5 evaluation R0 (sub-ADR of 2605263500; closes 14/14 original+expanded energy-coverage gap list at 100%)"
status: proposed-pending-council-ratification
doc_type: adr
topic: saf-sustainable-aviation-fuel-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 6.9
axis: constitutional
weight: 0.69
priority_note: "Sub-ADR of ADR-2605263500. Closes the last item of the 14-list expanded energy-coverage scope (cumulative cascade: 2605263500 framework + 2605263600..2605265100 = 13 sub-ADRs + this = 14). SAF for religious-corp aviation needs (e.g., shidemori long-distance bereavement-care travel, manabi educational delegation, hagukumi pediatric long-distance referral, future open-emergency-medical flight). Verdict: HEFA-SPK (algal-HVO §3 of 2605264800) + e-jet-fuel (Fischer-Tropsch from green H₂ + DAC CO₂, sibling pathway to 2605264700 methanol but FT product slate) CONDITIONALLY PERMITTED ≤500 kg/yr religious-corp aggregate through R3; corn-ethanol-derived ATJ-SPK PROHIBITED (N4 food-crop displacement); FAME biodiesel NOT-applicable as aviation (cold-flow + thermal-stability fail jet-fuel specs); commercial SAF off-take + CORSIA-credit-trading PROHIBITED."
authoritative_for:
  - "SAF pathway D1..D5 evaluation (HEFA-SPK / e-jet via FT / ATJ-SPK)"
  - "Religious-corp aviation fuel sourcing constraint (closed-loop only; NO commercial SAF off-take)"
  - "Aviation activity scope (mission-essential only per Charter §1.13 + §2(g); NO leisure/recreational aviation)"
  - "CORSIA credit trading absolute prohibition (Charter §2(b) financialization + N8 carbon-offset-trading inheritance)"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605263600-hydrogen-economy-d-gate-evaluation-r0
  - adr-2605264600-direct-air-capture-d-gate-evaluation-r0
  - adr-2605264700-methanol-dme-synfuel-d-gate-evaluation-r0
  - adr-2605264800-algal-biofuel-d-gate-evaluation-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605264900-v2g-demand-response-d-gate-evaluation-r0
supersedes: []
superseded_by: []
---

# ADR-2605265200: SAF — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade

# Context

Aviation is uniquely-energy-dense — battery-electric aviation is infeasible at most regimes (energy density of Li-ion 250 Wh/kg vs jet kerosene 12,000 Wh/kg = 48× gap). Religious-corp aviation activities through R5+ are small but mission-essential:

| Use case | Frequency | Aviation alternative? |
|---|---|---|
| shidemori bereavement-care delegation cross-jurisdiction | Few-per-year | None (rail/road for short distance, but >1500 km needs air) |
| manabi educational delegation | Few-per-year | Same |
| hagukumi pediatric long-distance referral (chronic care unavailable locally) | Variable | None for emergency cases |
| Future open-emergency-medical-flight (e.g., disaster response) | Rare | Helicopter/fixed-wing for medevac in disaster zones |
| Cargo for time-critical mizuho water-quality samples / iyashi clinical specimens | Occasional | Rail for non-time-critical |

Religious-corp aviation policy = mission-essential only (Charter §1.13 + §2(g)); leisure/recreational/tourism aviation PROHIBITED (§2(h) Wellbecoming + multi-gen carbon).

ASTM D7566 lists 7 SAF pathways approved for blending with conventional Jet-A1:

| Annex | Pathway | Religious-corp fit |
|---|---|---|
| A1 | Fischer-Tropsch SPK (FT-SPK) from syngas | ✓ §2 if green H₂ + DAC CO₂ feedstock |
| A2 | HEFA-SPK (hydroprocessed esters + fatty acids) | ✓ §1 (algal lipid → HVO per 2605264800 §3) |
| A3 | SIP (synthetic iso-paraffinic from fermentation of sugar) | ⚠ N4 inheritance — only OK if non-food-crop sugar |
| A4 | FT-SPK/A (with aromatics) | Same as A1 |
| A5 | ATJ-SPK (alcohol-to-jet from isobutanol/ethanol) | ✗ if corn-ethanol feedstock (N4) |
| A6 | CHJ (catalytic hydrothermolysis from algae) | ✓ §1 alternative |
| A7 | HC-HEFA from algal triglycerides | ✓ §1 (parallel to A2) |

# Decision

## §1 HEFA-SPK (Annex A2 + A7) — CONDITIONALLY PERMITTED

Algal-lipid HVO drop-in per ADR-2605264800 §3, hydroprocessed to jet-range alkanes.

| Gate | Assessment |
|---|---|
| **D1** | ✓ algal feedstock per ADR-2605264800 §1; H₂ per ADR-2605263600 §1; both religious-corp closed-loop |
| **D2** | ✓ no long-lived waste |
| **D3** | ✓ closed-loop carbon (atmospheric CO₂ → algae → lipid → fuel → combustion → atmosphere) |
| **D4** | ✓ no fissile |
| **D5** | ✓ NiMo/Al₂O₃ catalyst + reactor open-formula per ADR-2605264800 §3.4 |

**Conditions**:
1. Feedstock chain-of-custody MANDATORY per ADR-2605264800 §3.5 (ASTM D7566 Annex A2 / Annex A7 batch attestation)
2. ≤200 kg/yr religious-corp aggregate HEFA-SAF through R3 (within ADR-2605264800 §3 ≤1 t/yr HVO cap)
3. **Blending limit ASTM D7566**: 50% SAF blended with conventional Jet-A1 max per current spec; **religious-corp aviation MUST use 100% SAF where possible**, accepting smaller aircraft + shorter range OR requiring Council Lv6+ ≥3 per-flight attestation if 100% SAF cert unavailable
4. Use restriction: religious-corp mission-essential aviation only per §3 below

## §2 e-Jet-Fuel via Fischer-Tropsch (Annex A1) — CONDITIONALLY PERMITTED

Green H₂ (ADR-2605263600 §1) + DAC CO₂ (ADR-2605264600 §1-3) → reverse water-gas-shift → syngas → Fischer-Tropsch wax → hydrocracking → jet-range alkanes.

| Gate | Assessment |
|---|---|
| **D1..D5** | All ✓ (parallel to methanol ADR-2605264700 §1 reasoning; just different downstream product slate) |

**Conditions**:
1. Stoichiometry chain-of-custody MANDATORY (per kg jet fuel ≈ 0.45 kg H₂ + 3.15 kg CO₂)
2. ≤300 kg/yr religious-corp aggregate e-Jet through R3
3. FT reactor: cobalt-based (commercial) preferred over iron-based for jet-range selectivity; cobalt catalyst Charter §2(g) supply-chain audit MANDATORY (DRC-cobalt-conflict ✗); religious-corp recycle ≥90% per cycle
4. FT reactor open-design; Lurgi-type slurry reactor preferred at R&D scale
5. Hydrocracking step uses green H₂ from §1 same source as feedstock — internally consistent
6. Use restriction: same §3 below

## §3 Aviation activity scope (Charter §1.13 + §2(g) bound)

| Activity | Religious-corp posture |
|---|---|
| **Mission-essential**: shidemori bereavement-care cross-jurisdiction / manabi delegation / hagukumi long-distance pediatric referral / iyashi emergency medical / mizuho water-sample logistics / disaster-response medevac | ✓ PERMITTED per Council Lv6+ ≥3 per program |
| **Leisure / recreational / tourism** | ✗ ABSOLUTELY PROHIBITED (Wellbecoming §2(h) multi-gen carbon footprint) |
| **Cargo-utility** (e.g., supply chain for remote Lands parcels) | Council Lv6+ ≥3 per program; rail / sea / road preferred wherever feasible |
| **Charter / executive jet** | ✗ ABSOLUTELY PROHIBITED (Charter §1.3 anti-individualism + §2(b) financialization) |
| **Drone aviation < 25 kg** | Out of this ADR scope (separate cargo / surveillance drone ADR; per ADR-2605261100 G6 anti-surveillance + ADR-2605263200 kazaori §3 NO surveillance drone) |

## §4 PROHIBITED + DEFERRED pathways

| Pathway | Verdict | Reason |
|---|---|---|
| ATJ-SPK from corn-ethanol (Annex A5) | ABSOLUTELY PROHIBITED | N4 inheritance (food-crop displacement) |
| ATJ-SPK from non-food agricultural waste cellulosic ethanol | DEFERRED | Acceptable in principle (N4 carve-out for non-food feedstock); pending cellulosic-ethanol ADR (separate) |
| SIP from non-food sugar fermentation | DEFERRED | Same as cellulosic ATJ-SPK |
| FAME biodiesel for aviation | NOT APPLICABLE | Cold-flow cloud-point + thermal-stability fail jet-fuel specs |
| FT-SPK/A with aromatics (Annex A4) | DEFERRED | More complex than A1; aromatics give better seal-swell for older engines, less needed for newer engines |
| Commercial SAF off-take (Neste / World Energy / LanzaJet / Gevo) | ABSOLUTELY PROHIBITED | D1 commercial-vendor + Charter §1.6 中間排除 |
| CORSIA / EU-ETS SAF credit trading | ABSOLUTELY PROHIBITED | Charter §2(b) financialization-of-atmosphere + hikari N8 carbon-offset-trading inheritance |

## §5 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; path-reserved `20-actors/hikari/cells/saf_hefa/` + `saf_e_jet_ft/` import-time RuntimeError | None |
| **R1** | post-Council + ADR-2605264800 R3 HVO + ADR-2605263600 R3 H₂ + ADR-2605264600 R3 DAC + first mission-essential aviation Council Lv6+ ≥3 attested | Bench ≤10 kg HEFA-SAF; no e-Jet yet | 10 kg/yr |
| **R2** | post-R1 + 30-day public + first §3.1 mission-essential flight log | ≤50 kg HEFA + first FT bench ≤10 kg | 50 kg/yr HEFA + 10 kg/yr FT |
| **R3** | post-R2 + Council Lv6+ ≥3 + ≥1 yr safe operation | Full §1+§2 caps; 100% SAF cert per-aircraft Council attestation chain | 200 HEFA + 300 FT kg/yr |

## §6 New Lexicons (R1+)

```
com.etzhayyim.hikari.{
  hefaSafBatchAttestation,                # ASTM D7566 A2/A7 per-batch + algal-feedstock CID + H2 CID
  eJetFtBatchAttestation,                 # ASTM D7566 A1 per-batch + H2 CID + DAC-CO2 CID + FT-catalyst lot
  missionEssentialFlightAttestation,      # per-flight Council Lv6+ ≥3 mission-essential justification record
  silenSafReview                          # annual Council Lv6+ ≥3 stoichiometry + flight-mission audit
}
```

# Consequences

**Positive**:
- Closes 14/14 of original+expanded energy-coverage scope (100%)
- Provides the only constitutionally-permissible aviation-fuel pathway (battery-electric infeasible at jet regime)
- Cross-actor binding shidemori / manabi / hagukumi / iyashi / mizuho mission-essential activities to closed-loop fuel chain
- Stoichiometry chain-of-custody discipline matches methanol/DME precedent

**Negative**:
- ≤500 kg/yr aggregate severely limits aviation scale — only mission-essential, not routine transport
- Capex algal R&D + DAC + H₂ + FT = $1-5M cumulative for R3 operation
- Aviation engine certification for 100% SAF (vs 50% blend) requires aircraft-specific compatibility attestation; older aircraft may need elastomer seal upgrades for aromatic-free SAF
- Religious-corp internal carbon attribution of mission-essential flight should be transparent (per-flight CO₂ figure published) per N7-adjacent privacy: aggregate by activity-class, not per-traveler

# References

- ADR-2605263500 (parent D1..D5)
- ADR-2605263600 (H₂)
- ADR-2605264600 (DAC CO₂)
- ADR-2605264700 (methanol/DME sibling synfuel)
- ADR-2605264800 (algal-biofuel parent for HEFA-SPK)
- ASTM D7566 (Standard Specification for Aviation Turbine Fuel Containing Synthesized Hydrocarbons; Annexes A1-A7)
- ICAO CORSIA SAF reference (referenced for §4 explicit non-participation)
- IATA Net-Zero CO₂ Roadmap 2050 (referenced for context, not adopted)
