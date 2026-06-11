---
id: adr-2605265300-cellulosic-ethanol-d-gate-evaluation-r0
title: "Cellulosic ethanol from non-food agricultural waste — D1..D5 evaluation R0 (sub-ADR of 2605263500; closes 2605265200 §4 ATJ-SPK deferral + 2605264800 §4 heterotrophic-sugar gate)"
status: proposed-pending-council-ratification
doc_type: adr
topic: cellulosic-ethanol-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 6.8
axis: constitutional
weight: 0.68
priority_note: "Sub-ADR of ADR-2605263500. Closes two specific deferrals: (a) ADR-2605265200 §4 ATJ-SPK Annex A5 / SIP Annex A3 carve-out for non-food cellulosic sugar; (b) ADR-2605264800 §4 heterotrophic-algae sugar feedstock R4+ re-evaluation. Verdict: cellulosic ethanol from religious-corp-internal mitsuho crop residue + hodoki organic ELV cellulosic streams CONDITIONALLY PERMITTED ≤200 t/yr religious-corp aggregate R3; commercial corn-stover off-take + commercial enzyme-supply contract PROHIBITED; engineered yeast/E.coli with closed-genome IP (Codexis / Novozymes proprietary) PROHIBITED."
authoritative_for:
  - "Cellulosic ethanol pathway D1..D5 evaluation (pretreatment + enzymatic hydrolysis + fermentation)"
  - "Cross-actor crop-residue feedstock cap from mitsuho R2+ (10-30% of residue, leave majority for soil organic matter)"
  - "Closed-genome cellulase enzyme PROHIBITION (D5 inheritance — open-publication enzymes only)"
  - "Lignin byproduct routing (combustion-CHP cross-actor to hikari OR biochar to mitsuho soil amendment)"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605265200-saf-sustainable-aviation-fuel-d-gate-evaluation-r0
  - adr-2605264800-algal-biofuel-d-gate-evaluation-r0
  - adr-2605264700-methanol-dme-synfuel-d-gate-evaluation-r0
  - adr-2605261015
  - adr-2605261215-hodoki-elv-disassembly-tier-b-actor-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605263800-biomethane-d-gate-evaluation-r0
supersedes: []
superseded_by: []
---

# ADR-2605265300: Cellulosic ethanol from non-food agricultural waste — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade

# Context

Two specific deferrals from upstream ADRs require resolution:

| Deferral | Source | Resolution path |
|---|---|---|
| ATJ-SPK from non-food agricultural waste cellulosic ethanol | ADR-2605265200 §4 | This ADR provides the upstream ethanol; ATJ-SPK is separate downstream sibling future ADR |
| SIP from non-food sugar fermentation | ADR-2605265200 §4 | Same upstream sugar source; SIP downstream future ADR |
| Heterotrophic-algae sugar feedstock | ADR-2605264800 §4 (R4+ re-evaluation if sugar verifiably non-food) | This ADR is one valid sugar source path |

Cellulosic ethanol = pretreatment (steam explosion / dilute acid / alkali) of lignocellulose → enzymatic hydrolysis (cellulase + xylanase + β-glucosidase) → C5 + C6 sugar slurry → fermentation (S. cerevisiae for C6 alone OR engineered yeast for C5+C6 co-fermentation) → ethanol + CO₂ + lignin residue.

Feedstock candidates (religious-corp-internal):

| Source | Cellulose content | Annual availability (R3 estimate) | Religious-corp actor |
|---|---|---|---|
| Wheat straw / rice straw | 30-40% | ~500-2000 t (mitsuho R2+ if grain) | mitsuho |
| Corn stover | 30-40% | n/a (no corn — N4 food-displacement) | n/a |
| Bagasse (sugarcane residue) | 30-50% | n/a (no sugarcane — N4 displacement; sweetener crops) | n/a |
| Switchgrass / miscanthus (dedicated energy crops) | 30-40% | EXCLUDED — dedicated energy crops fail N4 (displace food cropland) | n/a |
| Hardwood/softwood residue (cross-actor tatekata + hodoki cellulosic ELV interior trim/wood) | 40-50% | ~50-200 t (cross-actor) | tatekata + hodoki |
| Bamboo (fast-growing, non-food, can grow on marginal land) | 40-50% | ~100-500 t (cross-actor mitsuho dedicated bamboo grove R3+ on non-food parcel) | mitsuho |

# Decision

## §1 Cellulosic ethanol from non-food agricultural + forestry waste — CONDITIONALLY PERMITTED

≤200 t/yr religious-corp aggregate cellulosic ethanol through R3.

| Gate | Assessment |
|---|---|
| **D1** | ✓ Feedstock 100% religious-corp-internal waste streams (mitsuho crop residue / tatekata + hodoki cellulosic / future bamboo) |
| **D2** | ✓ Spent fermentation broth + lignin residue short-cycle; lignin biochar disposition multi-gen carbon-positive |
| **D3** | ✓ Closed-loop carbon (atmospheric CO₂ → plant cellulose → ethanol → combustion → atmosphere; net ≈ 0) |
| **D4** | ✓ No fissile |
| **D5** | ✓ Pretreatment + hydrolysis + fermentation reactor open-hardware; **enzymes open-publication only** per §1.4 |

**Conditions**:

1. **Feedstock chain-of-custody MANDATORY**: every batch carries `cellulosicEthanolFeedstockAttestation` Lexicon citing source actor + waste-stream + dry-matter mass + cellulose %; food-crop-derived feedstock CATEGORICALLY EXCLUDED per N4 inheritance from hikari R0
2. **Feedstock harvest cap from mitsuho crop residue**: religious-corp may extract ≤30% of crop residue from any given parcel; remaining ≥70% MUST stay in field as soil organic matter + erosion control (per IPCC AR6 WG3 + FAO soil-stewardship guidance); annual soil-organic-matter audit Council Lv6+ ≥3 per parcel — extraction reduction mandatory if SOM drops >5% per 5-year period
3. **Pretreatment chemistry**:
   - Steam explosion (preferred — water only, no chemicals)
   - Dilute sulfuric acid (≤2% H₂SO₄, religious-corp recovery ≥90%)
   - Alkali (NaOH or Ca(OH)₂, religious-corp recovery ≥90%)
   - **NO ionic liquid pretreatment with commercial proprietary chemistry** (Charter §2(c) covert substance disclosure + D1)
4. **Enzymes open-publication only per D5**:
   - Cellulase: Trichoderma reesei naturally-secreted (public-domain organism + open-publication strain improvement)
   - Xylanase: Aspergillus niger or Penicillium (public-domain)
   - β-glucosidase: same fungal sources
   - **PROHIBITED**: Codexis CodeXyme / Novozymes Cellic / DuPont Accellerase / DSM PowerCell proprietary enzyme blends (D1 + D5)
   - Religious-corp may produce enzymes via in-house fungal cultivation OR procure from open-formula academic / non-profit suppliers
5. **Fermentation organism**:
   - C6-only: S. cerevisiae (baker's yeast, public-domain)
   - C5+C6 co-fermentation: engineered S. cerevisiae OR engineered Zymomonas mobilis with **open-genome OpenMTA license** (mirrors ADR-2605263500 §2.2.4 microbial strain disclosure)
   - **PROHIBITED**: closed-IP engineered organisms (DuPont Bio-PDO yeast / DSM Phytopharma / etc.)
6. **Lignin residue routing**:
   - Combustion-CHP at hikari R2+ thermal/electrical co-generation (highest-value disposition; ~50% of biomass energy content)
   - Biochar production via slow pyrolysis → mitsuho R2+ soil amendment (carbon-negative cross-actor with §3 of ADR-2605264600 mineralization sibling axis)
   - Direct field-application as mulch (chemistry-screen Council Lv6+ ≥3 per batch)
7. **CO₂ byproduct utilization** (fermentation releases ~0.96 kg CO₂ per kg ethanol):
   - Photobioreactor §2.2 of ADR-2605263500 feedstock OR
   - DAC concentration (ADR-2605264600 §1 alternative when DAC capacity insufficient) OR
   - mitsuho greenhouse fertilization
   - Atmospheric venting acceptable (carbon-cycle-neutral; fermentation CO₂ originated from atmospheric photosynthesis ≤1 yr ago)
8. **Use restriction**: religious-corp-internal energy substrate
   - Direct combustion in stationary engines (hikari R2+ CHP backup)
   - Feedstock for ATJ-SPK aviation fuel pathway (Annex A5 — future SAF sub-ADR enabled by this ADR)
   - Feedstock for SIP aviation fuel pathway (Annex A3 — future SAF sub-ADR)
   - Sugar source for heterotrophic algal lipid pathway (closes ADR-2605264800 §4 R4+ deferral with this ADR as the "verifiably-internal-non-food" sugar source)
   - **NO commercial sale** (D1 + Charter §2(b))
   - **NO transport-fuel blending into commercial gasoline pool** (D1)
9. ≤200 t/yr religious-corp aggregate through R3; aggregate-cap derivation: typical 0.3 L ethanol per kg dry biomass × 30% extraction × 2 kt residue available R3 = ~180 t ethanol — within cap
10. **Annual `silenCellulosicEthanolReview`** Council Lv6+ ≥3: feedstock chain audit + soil-organic-matter parcel audit + enzyme open-publication attestation + downstream use disposition

## §2 Commercial cellulosic ethanol off-take — PROHIBITED

| Failing |
|---|
| D1 — commercial cellulosic ethanol industry (POET / DuPont / Granbio / Iogen) commercial off-take = vendor + supply-chain dependency |
| Charter §1.6 中間排除 |

PROHIBITED on dual-independent grounds.

## §3 Dedicated energy-crop cellulosic — PROHIBITED

| Failing |
|---|
| hikari R0 N4 (food-crop biofuel ban) — even non-food energy crops like switchgrass / miscanthus displace cropland that could feed people OR support biodiversity |
| Charter §1.3 multi-gen + §2(g) supply ethics |

Mitsuho-permitted exception: **bamboo grove on marginal land where soil/climate is unsuited for food** can be religious-corp cellulosic feedstock at R3+ Council Lv6+ ≥3 per parcel (separate ADR if pursued).

## §4 Cross-actor mesh

| Actor | Role | Direction |
|---|---|---|
| **mitsuho** R2+ | Crop residue feedstock (≤30% extraction) + bamboo grove R3+ + soil-organic-matter audit | → feedstock |
| **tatekata** R2+ | Construction wood-residue cellulosic feedstock | → feedstock |
| **hodoki** R2+ | ELV cellulosic interior trim (carpet / textile / wood) feedstock | → feedstock |
| **hikari** R2+ | CHP combustion of lignin residue + receives ethanol for thermal storage/backup | ←→ |
| **mitsuho** R2+ greenhouse | Receives fermentation CO₂ for crop fertilization | ← |
| **iyashi/yakushi** R2+ | Pharma-grade ethanol downstream possibility (separate Council Lv6+ ≥3 attestation) | ← (limited) |
| **chigiri** R1+ | Procedural attestation + cross-juris harmonization | (verification) |
| **toritate** R1+ | Public Fund accounting for feedstock-cost-sharing with cross-actor | (audit) |
| **Future SAF Annex A5 ATJ-SPK** | Ethanol → jet fuel pathway | → downstream |
| **Future SAF Annex A3 SIP** | Sugar → SIP pathway (intermediate ethanol skipped) | → downstream |
| **ADR-2605264800 §4** heterotrophic algae | Sugar feedstock for algal lipid pathway | → downstream |

## §5 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; path-reserved `20-actors/hikari/cells/cellulosic_ethanol_pretreat_hydrolysis_ferment/` import-time RuntimeError | None |
| **R1** | post-Council + mitsuho R2 crop-residue attested + ≥1 fermentation-engineer + ≥1 biomass-pretreat-engineer on Council | Bench ≤500 kg/yr ethanol from single-feedstock pilot (likely rice straw) | 500 kg/yr |
| **R2** | post-R1 + 30-day public + soil-organic-matter baseline + ≥1 yr safe operation | ≤20 t/yr ethanol + first lignin-CHP attestation | 20 t/yr |
| **R3** | post-R2 + Council Lv6+ ≥3 + cross-actor downstream consumer attested | Full §1 cap; downstream SAF / algal / pharma-grade unlocks per separate consumer-side ADR | 200 t/yr |

## §6 New Lexicons (R1+)

```
com.etzhayyim.hikari.{
  cellulosicEthanolFeedstockAttestation,  # source actor + waste-stream CID + DM mass + cellulose % + soil-extract %
  cellulosicEthanolBatchAttestation,      # per-batch ethanol + pretreatment + enzyme open-publication CID + fermentation organism CID
  ligninResidueRoutingRecord,             # per-batch lignin disposition (CHP / biochar / mulch)
  soilOrganicMatterAuditRecord,           # per-parcel annual SOM audit (cross-actor mitsuho)
  silenCellulosicEthanolReview            # annual Council Lv6+ ≥3 full chain audit
}
```

# Consequences

**Positive**:
- Closes 2 specific deferrals from upstream ADRs (2605265200 §4 + 2605264800 §4)
- Cellulosic ethanol from agricultural waste = highest-value disposition for crop residue (better than open-field burning OR direct combustion)
- Cross-actor circular economy: mitsuho residue → ethanol → lignin → mitsuho soil amendment; fermentation CO₂ → mitsuho greenhouse; downstream sugar → algal feed
- Unlocks ATJ-SPK + SIP aviation fuel pathways for religious-corp aviation (cross-actor with 2605265200 SAF)

**Negative**:
- Cellulosic ethanol economics historically poor vs corn ethanol (which is N4-PROHIBITED for religious-corp); but religious-corp economics framework already excludes commercial-margin pressure
- Pretreatment + enzyme cost remain substantial — open-publication enzyme production at religious-corp scale is non-trivial fungal cultivation
- Soil-organic-matter monitoring burden (long-term studies needed; 5-year reduction trigger)
- Lignin disposition has multiple-path optimization complexity (CHP / biochar / mulch / future biochemistry feedstock)

# References

- ADR-2605263500 (parent D1..D5)
- ADR-2605265200 (SAF — closes §4 deferral)
- ADR-2605264800 (algal-biofuel — closes §4 R4+ heterotrophic sugar deferral)
- ADR-2605261015 (mitsuho — crop-residue feedstock + soil-stewardship cross-actor)
- ADR-2605261215 (hodoki — ELV cellulosic feedstock)
- ADR-2605264600 (DAC — sibling carbon pathway via lignin biochar)
- IPCC AR6 WG3 — bioenergy carbon-accounting reference
- FAO Soil-Stewardship Guidelines — referenced for §1.2 extraction-cap derivation
- NREL "Process Design and Economics for Biochemical Conversion of Lignocellulosic Biomass to Ethanol" 2011 — open-publication tech baseline
