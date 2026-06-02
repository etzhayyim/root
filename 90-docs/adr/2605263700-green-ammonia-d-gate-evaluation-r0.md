---
id: adr-2605263700-green-ammonia-d-gate-evaluation-r0
title: "Green ammonia — D1..D5 evaluation + Haber-Bosch from green H₂ conditional permit R0 (sub-ADR of 2605263500; sibling of 2605263600)"
status: proposed-pending-council-ratification
doc_type: adr
topic: green-ammonia-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 8.2
axis: constitutional
weight: 0.82
priority_note: "Sub-ADR of ADR-2605263500 §1.5 Open Questions item 6 (ammonia ADR slot). Sibling of ADR-2605263600 (hydrogen). Closes the cross-actor §4 hook between green H₂ and mitsuho fertilizer-N self-sufficiency. Verdict: green NH₃ via Haber-Bosch from green H₂ + atmospheric N₂ PERMITTED with conditions; grey NH₃ (from grey H₂) and ammonium nitrate (explosive precursor) ABSOLUTELY PROHIBITED on independent grounds. Ratification cascades from ADR-2605263500."
authoritative_for:
  - "Ammonia synthesis pathway D1..D5 evaluation"
  - "Green NH₃ conditional permit (≤200 kg/day religious-corp aggregate R3; storage ≤500 kg per LANDS parcel R3; agricultural-use only)"
  - "Ammonium nitrate absolute prohibition (D4 dual-use proliferation: ANFO precedent — Oklahoma City 1995, Beirut 2020 — incompatible with §1.12 Transparent Force open-source posture)"
  - "Cross-actor mitsuho fertilizer-N pathway (anhydrous + UAN ≤32% urea-ammonium-nitrate-solution carve-out for liquid fertilizer)"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605263600-hydrogen-economy-d-gate-evaluation-r0
  - adr-2605261015
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605192315-etzhayyim-transparent-force-rd
supersedes: []
superseded_by: []
---

# ADR-2605263700: Green ammonia — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade from ADR-2605263500
**Constitutional weight**: sub-evaluation under D1..D5 framework

# Context

ADR-2605263600 §4 flags green NH₃ as the religious-corp-compliant nitrogen-fertilizer pathway. mitsuho R0 (ADR-2605261015) §G6 prohibits synthetic pesticides but does NOT prohibit synthetic nitrogen fertilizer per se — biological N fixation (legume rotation + cyanobacteria) is preferred, with synthetic-N as a hedged fallback for soils with insufficient legume rotation capacity.

Global NH₃ production is ~95% grey (SMR-derived H₂ + Haber-Bosch with natural gas feedstock); ~150 Mt/yr; ~1.4% of global CO₂ emissions. Religious-corp constitutional posture inherits ADR-2605263500 + 2605263600 prohibitions on grey/blue/black/pink H₂; therefore religious-corp NH₃ MUST be green or DEFER.

# Decision

## §1 Green NH₃ via Haber-Bosch from green H₂ — CONDITIONALLY PERMITTED

| Gate | Assessment |
|---|---|
| **D1** | ✓ if H₂ feedstock is green per ADR-2605263600 §1 + N₂ from atmospheric distillation (PSA or cryogenic ASU; both religious-corp-deployable open-hardware) |
| **D2** | ✓ no long-lived waste; trace NOₓ from synthesis is short-half-life; ammonia inventory is non-radiological |
| **D3** | ✓ no carbon in synthesis loop; embodied CO₂ from construction offset by hikari renewable per §2.2 of 2605263500 |
| **D4** | ⚠ marginal — NH₃ itself is non-weaponizable, but ammonium nitrate (NH₄NO₃) downstream is dual-use as explosive precursor (ANFO); §3 below structurally excludes AN production |
| **D5** | ✓ Haber-Bosch reactor + ASU + heat-recovery loop open-hardware mandatory |

**Verdict**: PERMITTED under the following operational conditions:

1. **H₂ feedstock provenance**: every kg NH₃ produced consumes 0.176 kg H₂ stoichiometrically; H₂ MUST be green per ADR-2605263600 §1 with `hydrogenProductionAttestation` chain-of-custody preserved
2. **N₂ source**: atmospheric distillation only (PSA / cryogenic ASU); NO N₂ purchased from industrial gas vendors (D1 — air is the ambient flux)
3. **Reactor open-hardware**: Haber-Bosch reactor design + iron-based catalyst formulation (Mittasch-type Fe-based; Ru promoter open-publication if used) + control firmware Apache 2.0 + Charter Rider per D5
4. **Synthesis pressure / temperature**: industrial Haber-Bosch operates at 150-300 bar / 400-500°C; religious-corp R0-R2 limited to ≤150 bar / ≤450°C (proportionate safety; R3+ Council Lv6+ ≥3 per facility for higher pressures)
5. **Use restriction**: agricultural fertilizer-N for mitsuho cross-actor consumption + energy-carrier R&D (anhydrous NH₃ as zero-carbon fuel + as H₂ carrier 17.6% H by mass + 121 kg H₂/m³ liquid NH₃ density — denser than LH₂ but with toxicity burden). **NOT for commercial sale.** Surplus may transfer to other religious-corp actors only.
6. **Storage limits R0-R3**:
   - Per LANDS.md parcel: ≤500 kg NH₃ stored at any time (anhydrous in pressurized tank @ ≤17 bar at ambient temperature, or aqueous as ammonium hydroxide ≤25% solution)
   - Religious-corp aggregate: ≤2,000 kg NH₃ stored total
7. **Toxic-gas safety**: NH₃ is toxic (TLV-TWA 25 ppm; STEL 35 ppm) + flammable (LFL 15-28%) + corrosive; per OSHA 1910.111 + ASME B31.3 equivalent open-publication safety frameworks; Council Lv6+ ≥3 attestation per facility commissioning; mandatory respirator + leak-detection at every storage point
8. **Annual review**: `silenAmmoniaReview` Council Lv6+ ≥3 attestation: (a) all H₂ feedstock traced to green-H₂ Lexicon entries, (b) zero ammonium nitrate production, (c) leak rate ≤1% (NH₃ as indirect GHG via N₂O secondary chemistry per IPCC AR6 WG3 Ch.7)

## §2 Grey / Blue / Pink NH₃ — PROHIBITED

Inherits H₂-color prohibition from ADR-2605263600 §2. Triple-independent grounds.

## §3 Ammonium nitrate (NH₄NO₃) — ABSOLUTELY PROHIBITED

| Gate | Assessment |
|---|---|
| **D4** | ✗ — AN is dual-use explosive precursor; ANFO (94% AN + 6% fuel oil) is the most common industrial explosive globally; weaponized in Oklahoma City 1995 (3,200 kg AN) + Beirut 2020 (~2,750 t AN deflagration); religious-corp production of AN at any scale is incompatible with §1.12 Transparent Religious Force open-source posture (open-publication of AN production protocols = proliferation-equivalent knowledge transfer to non-state actors) |
| §1.12 | ✗ — same |

**Verdict**: ABSOLUTELY PROHIBITED (Council Lv7+ unanimity to amend; D4 + §1.12 double-independent ground; effectively permanent).

**Fertilizer alternative**: religious-corp fertilizer-N stays as **anhydrous NH₃** (direct soil injection per knife-coulter applicator) OR **aqueous ammonia** (≤25% NH₄OH solution) OR **urea** (CO(NH₂)₂, synthesized from NH₃ + CO₂; biuret limit ≤1.5% per agronomy standard) OR **UAN ≤32%** (urea-ammonium-nitrate solution; the ammonium-nitrate fraction of UAN ≤32% is in dilute aqueous solution — explicitly **carve-out from §3 prohibition only when**: (a) solution concentration ≤32%, (b) shipped as liquid (not crystallized), (c) per-batch ≤500 L, (d) annual Council Lv6+ ≥3 attestation that no crystallization-and-concentration pathway exists in religious-corp inventory).

## §4 Cross-actor mitsuho integration

mitsuho R2+ uses green NH₃ as the **fallback nitrogen source** when biological N fixation is insufficient. Priority order per Council Lv6+ ≥3 review:

1. **Primary**: biological N fixation (legume rotation: soybean / clover / vetch; *Azolla*-rice symbiosis; *Frankia*-actinorhizal nitrogen-fixing trees; free-living cyanobacteria in paddy systems)
2. **Secondary**: animal manure (mitsuho R2+ livestock integration; ≤25 N kg/ha/yr cap to prevent runoff)
3. **Tertiary**: compost-derived N (mitsuho compost cell from mitsuho + hodoki + kazaori organic waste streams)
4. **Hedged fallback**: green NH₃ from this ADR (anhydrous knife-coulter or aqueous; ≤50 N kg/ha/yr cap; NOT default)

`mitsuho.silenMitsuhoReview` annual audit MUST report per-parcel N-source ratio with green NH₃ ≤25% of total N applied (else trigger biological-fixation expansion plan).

## §5 Roadmap

| Phase | Date / Trigger | Scope | Cap |
|---|---|---|---|
| **R0** | this commit | This ADR + path-reserved `20-actors/hikari/cells/haber_bosch_ammonia/` import-time RuntimeError | None |
| **R1** | post-Council ratification of 2605263500 + 2605263600 + this ADR + mitsuho R1 nitrogen-deficit attested | Bench-scale ≤2 kg/day Haber-Bosch reactor + ≤50 kg storage at ≤150 bar | 2 kg/day |
| **R2** | post-R1 + ≥1 ammonia-process-engineer on Council + 1-year safe operation | ≤20 kg/day + ≤200 kg storage + first mitsuho field-application pilot | 20 kg/day |
| **R3** | post-R2 + 30-day public + cross-actor mitsuho ratify | ≤200 kg/day religious-corp aggregate + ≤500 kg/parcel + UAN ≤32% carve-out activated under §3 conditions | 200 kg/day |

## §6 New Lexicons

```
com.etzhayyim.hikari.{
  ammoniaProductionAttestation,    # per-kg: h2_attestation_cid + n2_source + reactor_facility + leak_check
  ammoniaStorageInventory,         # per-LANDS-parcel: kg current + form (anhydrous/aqueous) + pressure
  ammoniaSafetyAttestation,        # per-facility commissioning: OSHA 1910.111 / ASME B31.3 equivalent
  silenAmmoniaReview               # annual Council Lv6+ ≥3: H2 chain-of-custody + zero-AN attestation + leak rate
}
com.etzhayyim.mitsuho.{
  nitrogenSourceLedger             # per-parcel-per-season: biological / manure / compost / green-NH3 kg-N breakdown
}
```

# Consequences

**Positive**:
- Closes religious-corp nitrogen-fertilizer self-sufficiency loop (currently 95% global N fertilizer is grey-H₂-Haber-Bosch — substantial constitutional dependency gap)
- Provides energy-carrier R&D pathway (NH₃ as zero-carbon fuel; 121 kg-H/m³ density vs 71 kg-H/m³ for LH₂; storable at modest pressures)
- Cross-actor coupling hikari + mitsuho deepens substrate integration

**Negative**:
- Haber-Bosch synthesis is energy-intensive (~30-35 GJ/t NH₃; ~10 MWh/t); religious-corp green NH₃ at 200 kg/day R3 cap = ~6 MWh/day for synthesis alone (~6× hikari R2 capacity of ~170 kW × 24 h = 4.08 MWh/day; therefore R3 NH₃ requires hikari R3 multi-site mesh capacity)
- Toxicity burden: NH₃ leak at high concentration is lethal; safety culture investment substantial
- Pressure burden: 150 bar containment requires industrial-grade vessels + open-hardware design gap (most reactor designs are vendor IP)
- Cross-jurisdictional regulatory burden: NH₃ storage > 4500 kg triggers EPA Risk Management Plan in US (RMP §112(r)); similar thresholds in other jurisdictions — §1.6 of 2,000 kg aggregate cap stays well below

# Alternatives Considered

- **Defer ammonia indefinitely**: rejected — mitsuho R2+ fertilizer-N is operationally pressing; green NH₃ is the only constitutionally-permissible synthetic-N pathway
- **Allow ammonium nitrate at small scale**: rejected — D4 + §1.12 double-independent ban; even small-scale AN protocols become proliferation knowledge once open-source-published per §1.12
- **Use synthetic urea exclusively**: considered — urea is non-explosive, less toxic, and globally the largest N fertilizer (~55% of N market); urea is permitted under this ADR §3 alternative list. But urea synthesis still requires NH₃ feedstock; this ADR is upstream
- **Permit fossil-derived NH₃ as transitional**: rejected — Charter Rider §2(d) absolute

# Open Questions

1. **Reactor catalyst R1**: Mittasch-type Fe-based (mature, public-domain) vs Ru-promoted (higher activity, scarce-metal supply chain concern). To be decided at R1 ADR.
2. **ASU technology R1**: pressure-swing adsorption (PSA, lower capex, suitable for <1 t/day) vs cryogenic distillation (lower opex per t, suitable for ≥10 t/day). PSA likely for R1-R2; cryogenic at R3+.
3. **Cross-actor wadachi/sarutahiko NH₃-fuel pilot**: NH₃ as zero-carbon fuel for heavy mobility (NH₃ ICE or NH₃-PEM cracking). To be decided at wadachi R3+ separately.

# References

- ADR-2605263500 (parent D1..D5 framework)
- ADR-2605263600 (hydrogen sibling — H₂ feedstock)
- ADR-2605261015 (mitsuho R0 — fertilizer consumer)
- ADR-2605192315 (Transparent Force — §1.12 ground for §3 AN prohibition)
- IPCC AR6 WG3 Ch.7 — NH₃ atmospheric chemistry
- OSHA 1910.111 — Storage and handling of anhydrous ammonia
- ASME B31.3 — Process Piping Code (NH₃ applicable section)
- EPA RMP §112(r) — Risk Management Plan threshold for NH₃ (4500 kg / 10,000 lb)
- Oklahoma City bombing 1995 + Beirut explosion 2020 — referenced as AN-weaponization precedent for §3
