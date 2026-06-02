---
id: adr-2605264800-algal-biofuel-d-gate-evaluation-r0
title: "Algal biofuel — D1..D5 evaluation R0 (extends 2605263500 §2.2 microbial-hydrocarbon to algal lipid pathway; cross-actor mitsuho aquaculture)"
status: proposed-pending-council-ratification
doc_type: adr
topic: algal-biofuel-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 7.3
axis: constitutional
weight: 0.73
priority_note: "Sub-ADR of ADR-2605263500. Extends §2.2 microbial-hydrocarbon (cyanobacteria-direct-to-alkane) to algal-lipid biofuel pathway (microalgae → lipid → transesterification or hydroprocessing → diesel/jet drop-in). Verdict: photoautotrophic microalgae open-pond OR enclosed PBR CONDITIONALLY PERMITTED ≤10 t-DW/yr biomass through R3; HVO (hydroprocessed vegetable oils)-route biodiesel CONDITIONALLY PERMITTED via green H₂ from ADR-2605263600; transesterification FAME (fatty-acid methyl ester) via §2 methanol from ADR-2605264700 CONDITIONALLY PERMITTED. Heterotrophic algae fed sugar feedstock from food crops PROHIBITED (N4 inheritance). Open-pond invasive-species risk requires containment per Council Lv6+ ≥3."
authoritative_for:
  - "Algal biofuel pathway D1..D5 evaluation (photoautotrophic open-pond / PBR / heterotrophic)"
  - "Lipid-route biodiesel (FAME via methanol transesterification + HVO via H₂ hydroprocessing)"
  - "Algal-feedstock cross-actor with mitsuho aquaculture R2+ (algal protein co-product as fish/livestock feed)"
  - "Heterotrophic-sugar-fed algae absolute prohibition (food-crop-displacement N4 inheritance)"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605263600-hydrogen-economy-d-gate-evaluation-r0
  - adr-2605264600-direct-air-capture-d-gate-evaluation-r0
  - adr-2605264700-methanol-dme-synfuel-d-gate-evaluation-r0
  - adr-2605261015
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605263800-biomethane-d-gate-evaluation-r0
supersedes: []
superseded_by: []
---

# ADR-2605264800: Algal biofuel — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade

# Context

ADR-2605263500 §2.2 permits cyanobacteria + engineered photosynthetic organisms producing hydrocarbon DIRECTLY (acyl-ACP-decarbonylase → alkane). The algal-lipid pathway is structurally adjacent but distinct:

- Microalgae (Chlorella, Nannochloropsis, Botryococcus, Scenedesmus, Schizochytrium) accumulate intracellular triacylglycerol (TAG) lipid at 20-50% of dry weight under nutrient-starvation conditions
- Lipid extraction (hexane, supercritical CO₂, or wet-extraction) yields algal oil
- Algal oil → biodiesel via:
  - **FAME route**: transesterification with methanol (ADR-2605264700 §1) + KOH catalyst → fatty acid methyl esters
  - **HVO route**: hydroprocessing with green H₂ (ADR-2605263600 §1) + NiMo/Al₂O₃ catalyst → straight-chain alkanes (drop-in diesel + jet)
- Co-products: protein (cross-actor mitsuho R2+ aquaculture / livestock feed) + carbohydrate (biomethane feedstock §1.1 of ADR-2605263800)

# Decision

## §1 Photoautotrophic microalgae cultivation — CONDITIONALLY PERMITTED

| Cultivation system | Productivity (g/m²/d) | CO₂ utilization | D-gate notes |
|---|---|---|---|
| **Open raceway pond** | 10-25 | atmospheric or DAC §2 | ✓ §1 with strict containment |
| **Enclosed flat-panel PBR** | 20-50 | DAC dedicated | ✓ §1 higher capex, lower contamination |
| **Tubular PBR** | 30-60 | DAC dedicated | ✓ §1 highest capex |

| Gate | Assessment |
|---|---|
| **D1** | ✓ Religious-corp owned strain + cultivation + downstream; CO₂ from DAC (ADR-2605264600) or biomethane upgrading (ADR-2605263800); nutrient-N from green NH₃ (ADR-2605263700) or compost (mitsuho cross-actor) |
| **D2** | ✓ Biomass + spent media short-cycle biological (compostable / digester feed) |
| **D3** | ✓ Closed-loop carbon via DAC or biomethane CO₂; net atmospheric Δ ≈ 0 |
| **D4** | ✓ No fissile |
| **D5** | ✓ Strain open-genome OpenMTA; cultivation system + harvest + extraction open-hardware Apache 2.0 + Rider |

**Conditions** (extends ADR-2605263500 §2.2 framework to algal lipid):

1. ≤10 t-DW (dry weight) biomass / yr religious-corp aggregate through R3 (~3-5 t lipid via 30-50% TAG)
2. **Strain restriction**: photoautotrophic only — Chlorella, Nannochloropsis, Botryococcus, Scenedesmus, Tetraselmis, Synechocystis (cyanobacterial lipid). **Heterotrophic algae fed sugar feedstock (Schizochytrium / Crypthecodinium on glucose / glycerol) PROHIBITED through R3** unless sugar is religious-corp-internal waste stream (mitsuho cellulosic residue post-AD, NOT food crops per N4)
3. **Open-pond containment**: open raceway permitted only with:
   - Local-native species OR mono-culture of well-characterized non-invasive strain (Council Lv6+ ≥3 per site)
   - Physical barrier (≥1 m berm + ≥0.5 m freeboard + bird-netting) against escape
   - Routine genetic-marker testing for cross-contamination
   - Geographic exclusion: NO sites within 5 km of legally-protected wetlands / waterways / mizuho aquifer recharge zones
4. **Enclosed PBR preferred** for engineered strains (per ADR-2605263500 §2.2.5 BSL-1/2 inheritance + double-kill-switch where strain is engineered)
5. **Nutrient sourcing**: N from green NH₃ (R3+ ADR-2605263700) OR compost-derived; P from religious-corp-internal recovery (struvite from mizuho biosolids OR rock-phosphate religious-corp-mined under Charter §2(g)); NO commercial fertilizer-N (D1) NOR phosphate-mining contract
6. CO₂ source: DAC capture (ADR-2605264600) preferred for enclosed PBR; atmospheric CO₂ for open-pond OK at low productivity
7. Harvest: gravity sedimentation + centrifuge OR flocculation (chitosan or chitin from cross-actor future seafood-waste actor); open-hardware harvest equipment
8. Annual `silenAlgalCultivationReview` Council Lv6+ ≥3

## §2 Algal lipid → biodiesel (FAME route via methanol) — CONDITIONALLY PERMITTED

Algal oil + methanol → FAME biodiesel + glycerol byproduct.

**Conditions**:
1. Methanol feedstock MUST be from ADR-2605264700 §1 (closed-loop green methanol); NO commercial methanol procurement
2. KOH catalyst religious-corp recovery (catalyst regeneration ≥80% per cycle)
3. Glycerol byproduct routing: (a) future polyols/propanol industrial chemistry feedstock, (b) biomethane co-substrate (ADR-2605263800 digester), (c) animal feed (cross-actor mitsuho livestock) — NOT commercial sale
4. ≤2 t/yr FAME religious-corp aggregate through R3
5. ASTM D6751 OR EN 14214 equivalent open-publication quality spec (per-batch attestation)

## §3 Algal lipid → HVO drop-in diesel/jet (hydroprocessing route) — CONDITIONALLY PERMITTED

Algal oil + green H₂ + NiMo/Al₂O₃ catalyst → straight-chain alkanes (drop-in diesel + jet-fuel-range).

**Conditions**:
1. H₂ feedstock MUST be from ADR-2605263600 §1 (closed-loop green H₂); NO commercial H₂
2. ≤1 t/yr HVO religious-corp aggregate through R3 (smaller cap due to operating pressure + temperature complexity)
3. Operating ≤80 bar / ≤350°C (proportionate safety scale; R4+ Council Lv6+ ≥3 per facility for higher)
4. NiMo/Al₂O₃ catalyst open-formula; cobalt-promoted variant DEFERRED (cobalt supply-chain Charter §2(g) concern)
5. **Drop-in diesel quality**: per ASTM D975 / EN 590 equivalent; jet variant per ASTM D7566 / Annex A2 (HEFA-SPK) — both open-publication specs
6. Consumer-side ADR required per actor (wadachi / sarutahiko / suki for diesel; future aviation actor for jet)

## §4 Heterotrophic algae fed sugar — PROHIBITED through R3

| Failing |
|---|
| ADR-2605261100 N4 (food-crop biofuel ban) — heterotrophic algae require glucose/glycerol typically from corn/sugarcane food crops |
| D1 if commercial-sugar procurement (vendor dependency on food-industry sugar suppliers) |
| Charter §2(g) supply-chain ethics |

PROHIBITED through R3. R4+ re-evaluation only if sugar source is verifiably religious-corp-internal non-food agricultural waste (cellulosic residue post-pretreatment OR mitsuho food-scrap fermentation byproduct).

## §5 Algal protein co-product cross-actor

Per kg lipid, ~1.5-2 kg defatted algal biomass (40-60% protein) remains. Cross-actor utilization:

| Consumer | Use | Path |
|---|---|---|
| mitsuho R2+ aquaculture (fish meal substitute) | Sustainable fish-feed protein | Direct feed pelletization |
| mitsuho R2+ livestock (cattle, poultry feed) | Protein supplement | Direct feed |
| Human food (cyanobacteria spirulina/chlorella as nutraceutical) | Sustainable protein, requires food-grade strain + GRAS attestation | Council Lv6+ ≥3 per strain + jurisdiction |
| Biomethane digester | AD feedstock if no higher-value use | ADR-2605263800 §1.1 |

## §6 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; path-reserved `20-actors/hikari/cells/algal_lipid_cultivation/` import-time RuntimeError | None |
| **R1** | post-Council + microbial §2.2 R1 OR DAC R1 + ≥1 phycologist/algal-biotech on Council | Bench ≤100 m² open-pond OR ≤2 m² PBR; ≤100 kg-DW/yr biomass; lipid characterization only (no fuel production) | 100 kg-DW/yr |
| **R2** | post-R1 + 30-day public + cross-actor mitsuho aquaculture protein-feed pilot | ≤1000 m² open-pond OR ≤20 m² PBR; ≤1 t-DW/yr biomass; FAME or HVO ≤100 kg/yr; mitsuho protein co-product attestation | 1 t-DW/yr |
| **R3** | post-R2 + Council Lv6+ ≥3 + 1-yr safe operation + first transport-consumer ADR ratified | Full caps §1-3; first wadachi/sarutahiko HVO consumer-side ADR | 10 t-DW/yr |

## §7 New Lexicons (R1+)

```
com.etzhayyim.hikari.{
  algalCultivationFacilityAttestation,    # strain + system type + containment + CO2 source
  algalBiomassHarvestRecord,              # per-batch DW + lipid % + protein %
  algalLipidExtractionRecord,             # per-batch lipid kg + extraction method
  fameBatchAttestation,                   # FAME biodiesel batch + algal-oil CID + methanol CID + glycerol disposition
  hvoBatchAttestation,                    # HVO drop-in batch + algal-oil CID + green-H2 CID + catalyst
  algalProteinFeedAttestation,            # cross-actor mitsuho feed manifest + safety
  silenAlgalCultivationReview             # annual Council Lv6+ ≥3
  silenAlgalFuelReview                    # annual Council Lv6+ ≥3 for FAME + HVO
}
```

# Consequences

**Positive**:
- Extends §2.2 cyanobacteria-direct-to-alkane to broader algal-lipid pathway (more strain options + higher productivity in some configurations)
- Cross-actor protein co-product = mitsuho aquaculture sustainable fish-feed substitute (currently global fish-feed depends on wild-caught forage fish — major sustainability gap)
- HVO drop-in diesel/jet is the only constitutionally-permissible aviation-fuel pathway (battery-electric aviation infeasible at most regimes)
- Cross-cuts hikari → hydrogen → methanol → algal cultivation → biodiesel → transport actors

**Negative**:
- Capex ~$50-200/m² open-pond, ~$300-1000/m² PBR; ≤100 m² R1 ~$5-100K
- Open-pond contamination + harvest energy historically poor economics vs petroleum
- Hexane extraction is solvent burden; supercritical CO₂ extraction is open-hardware-immature
- Invasive-species risk requires structural containment + monitoring
- Engineered-strain biocontainment burden (per ADR-2605263500 §2.2.5)

# Alternatives Considered

- **Permit heterotrophic algae at R0**: rejected per §4 N4 inheritance
- **Skip algal-biofuel as not-yet-economic**: considered — but cross-actor protein-feed value + drop-in HVO uniqueness justify R&D path
- **Use algal biomass directly for biomethane only (skip lipid)**: simpler but forgoes drop-in fuel pathway

# References

- ADR-2605263500 §2.2 (parent microbial-hydrocarbon framework)
- ADR-2605263600 (H₂ for HVO §3)
- ADR-2605264600 (DAC CO₂ for enclosed PBR feedstock)
- ADR-2605264700 (methanol for FAME §2)
- ADR-2605261015 (mitsuho aquaculture cross-actor)
- ASTM D6751 / EN 14214 — biodiesel quality standards (referenced)
- ASTM D7566 Annex A2 — HEFA-SPK aviation drop-in (referenced)
- IEA Bioenergy TCP Task 34 — Direct Thermochemical Liquefaction (referenced)
