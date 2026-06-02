---
id: adr-2605263600-hydrogen-economy-d-gate-evaluation-r0
title: "Hydrogen economy — D1..D5 evaluation + green-H₂ conditional permit R0 (sub-ADR of 2605263500)"
status: proposed-pending-council-ratification
doc_type: adr
topic: hydrogen-economy-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 8.4
axis: constitutional
weight: 0.84
priority_note: "Sub-ADR of ADR-2605263500 §1.5 Open Questions item 5 (hydrogen-economy ADR slot deferred). Applies the D1..D5 5-gate framework to hydrogen production/storage/use. Verdict: green hydrogen (electrolysis from hikari renewable surplus + atmospheric / mineral-water source) PERMITTED with conditions; blue/grey/black hydrogen ABSOLUTELY PROHIBITED (D1 + D3 + Charter Rider §2(d)); turquoise (methane pyrolysis) CONDITIONALLY PROHIBITED pending closed-loop carbon attestation. Ratification cascades from ADR-2605263500 ratification (same Council Lv7+ unanimity threshold via D-gate framework constitutional locking)."
authoritative_for:
  - "Hydrogen production color classification D1..D5 evaluation"
  - "Green-H₂ conditional permit (≤500 kg/day religious-corp aggregate R3; storage ≤200 kg per LANDS parcel R3; high-pressure ≤350 bar R3 / ≤700 bar R4+ Council Lv6+ ≥3)"
  - "Hydrogen NOT-categorically-prohibited carve-out from prior ADR-2605202000 SMR/水素 deferral"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605261100
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605202000-etzhayyim-energy-substrate
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
supersedes: []
superseded_by: []
---

# ADR-2605263600: Hydrogen economy — D1..D5 evaluation + green-H₂ conditional permit R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade from ADR-2605263500 ratification
**Constitutional weight**: sub-evaluation under ADR-2605263500 D1..D5 framework; permits/prohibits derived from D-gate application, not new constitutional invariants

# Context

ADR-2605263500 §1.5 Open Questions item 5 explicitly defers hydrogen evaluation to its own ADR under the D1..D5 framework. ADR-2605202000 also deferred hydrogen ("future ADR `etzhayyim-energy-hydrogen`"). This ADR closes both deferrals at R0 scope.

Hydrogen is industrially classified by carbon-source color:

| Color | Production | D1 (dependency) | D2 (waste) | D3 (closed-loop C) | D4 (proliferation) | D5 (open-hw) |
|---|---|---|---|---|---|---|
| **Green** | Electrolysis from renewable electricity + water | ✓ if water sourced ambient + electrolyzer religious-corp-owned | ✓ no waste | ✓ no carbon | ✓ no fissile | ✓ if firmware open-source |
| **Grey** | Steam methane reforming (natural gas, CO₂ vented) | ✗ commercial fossil dependency | ✗ atmospheric CO₂ addition | ✗ geological fossil C | ✓ | depends |
| **Blue** | SMR + CCS (CO₂ sequestered) | ✗ commercial fossil dependency | ⚠ CO₂ sequestration site multi-gen liability | ⚠ leakage risk | ✓ | depends |
| **Black/Brown** | Coal gasification | ✗ commercial fossil dependency | ✗ atmospheric CO₂ + heavy-metal slag | ✗ geological fossil C | ✓ | depends |
| **Pink** | Electrolysis from nuclear (fission) electricity | ✗ via fission (ADR-2605263500 §2.4 D1+D2+D4) | ✗ fission HLW | ✓ | ✗ enrichment cascade | depends |
| **Turquoise** | Methane pyrolysis (CH₄ → H₂ + solid C) | ✗ commercial methane dependency unless religious-corp-grown biomethane | ⚠ solid carbon disposal | conditional on methane source | ✓ | depends |
| **White** | Naturally-occurring underground H₂ (rare) | ⚠ extraction industry development | ✓ | ✓ geological non-carbon | ✓ | depends |

# Decision

## §1 Green hydrogen — CONDITIONALLY PERMITTED

Green H₂ produced via PEM/AEM/alkaline electrolyzers powered by hikari renewable surplus (solar + small wind + geothermal-micro per hikari R0 §2.1) PERMITTED under D1..D5 with the following operational conditions:

1. **Electricity sourcing attestation**: every kg H₂ produced carries `com.etzhayyim.hikari.hydrogenProductionAttestation` Lexicon entry certifying electricity source = hikari surplus (NOT grid import; NOT fossil-grid mix). Real-time hikari-export contemporaneous (≤15 min temporal-coincidence per IEC 62325-451-8 hourly-matching upgraded to ≤15 min for religious-corp tighter standard).
2. **Water source**: ambient rainwater / mineral water / desalinated seawater (mizuho R2+ cross-actor consultation). NO commercial municipal water supply contract (D1).
3. **Electrolyzer open-hardware**: stack design + control firmware + balance-of-plant Apache 2.0 + Charter Rider per D5. PEM stacks from commercial vendors permitted only if vendor IP terms allow religious-corp publication of integration interfaces.
4. **Use restriction**: religious-corp-internal energy substrate (long-duration storage + heat for industrial process + transport-fuel-cell pilot in wadachi R3+ if approved separately + fertilizer feedstock via ammonia ADR — see §3 below). NOT for commercial sale. Surplus may transfer to other religious-corp actors only.
5. **Storage limits R0-R3**:
   - Per LANDS.md parcel: ≤200 kg H₂ stored at any time
   - Religious-corp aggregate: ≤500 kg H₂ stored total
   - Pressure: ≤350 bar through R3 (Type-III/IV composite cylinders); ≤700 bar permitted only at R4+ with Council Lv6+ ≥3 per-facility (proportionate to safety burden of high-pressure containment).
6. **Liquid hydrogen (LH₂) prohibited through R4**: cryogenic-storage energy penalty ~30% + boil-off losses + open-cryo-hardware scarcity. Re-evaluate R5+.
7. **Underground storage prohibited**: salt-cavern / aquifer / depleted-reservoir H₂ storage is commercial-utility scale (hikari N6 ≤10 MW per site equivalent — also conflicts with §1.11 Land Trust waqf-equivalent constraint).
8. **Safety attestation**: H₂ handling per OSHA 1910.103 + NFPA 2 equivalent open-publication safety frameworks (jurisdictionally-adapted but content-equivalent); Council Lv6+ ≥3 attestation per facility commissioning.
9. **Annual review**: `silenHydrogenReview` Council Lv6+ ≥3 attestation: (a) all production attested to hikari-renewable electricity ≤15-min temporal coincidence, (b) zero commercial-grid imports for H₂ production, (c) leak rate ≤2% production-to-end-use mass-balance (climate-impact mitigation per recent atmospheric-H₂-as-indirect-GHG findings, IPCC AR6 WG1 Ch.6).

## §2 Grey/Black/Blue/Pink — PROHIBITED

Confirmed prohibition on independent grounds:

| Color | Failing gates |
|---|---|
| Grey (SMR from natural gas) | D1 (commercial fossil) + D3 (atmospheric CO₂) + Charter Rider §2(d) (new fossil extraction) — **triple-independent** |
| Black (coal gasification) | D1 + D3 + §2(d) + heavy-metal slag D2 — **quadruple-independent** |
| Blue (SMR + CCS) | D1 + multi-gen CCS site liability D2 + leakage-risk D3 — triple-independent. Note: CCS sequestration sites carry 1,000+ yr stewardship burden (NETL guidance) which exceeds D2 ≤100 yr default and would require Council Lv7+ per increment, making blue H₂ infeasible at religious-corp scale. |
| Pink (electrolysis from fission electricity) | Inherits all D1+D2+D4 from ADR-2605263500 §2.4 fission prohibition |

## §3 Turquoise / White — DEFERRED CONDITIONAL

- **Turquoise** (methane pyrolysis, CH₄ → H₂ + solid C): PERMITTED only if methane source is religious-corp closed-loop biomethane from agricultural waste anaerobic digestion (cross-actor with future biomethane ADR; mitsuho + hodoki feedstock). Solid carbon co-product MUST be sequestered as soil amendment (biochar pathway) for net-negative carbon. Re-evaluate at R2+ if biomethane infrastructure exists.
- **White** (natural underground H₂): PERMITTED only at small-extraction-prospector scale (≤100 kg/day per site; passive seepage capture or low-impact drilling ≤500 m to match hikari geothermal-micro depth limit per G9 land-trust integration). NOT large-scale H₂ field development (would trigger commercial-extraction-industry dependency D1). Re-evaluate at R3+ if religious-corp-owned LANDS parcel exhibits H₂ seepage.

## §4 Cross-actor ammonia hook

Green H₂ + atmospheric N₂ → green NH₃ (Haber-Bosch with green H₂) is the religious-corp-compliant pathway for nitrogen fertilizer (cross-actor with mitsuho per ADR-2605261015 G6 "no synthetic pesticides" — N fertilizer is separate from pesticide, and biological nitrogen fixation is preferred under mitsuho doctrine but green NH₃ remains a hedged fallback for soils without sufficient legume rotation). **Green ammonia evaluation deferred to its own ADR** (`etzhayyim-energy-ammonia-d-gate-evaluation`); this ADR §4 only flags the cross-reference.

## §5 Roadmap

| Phase | Date / Trigger | Scope | Cap |
|---|---|---|---|
| **R0** | this commit | This ADR + path-reserved `20-actors/hikari/cells/green_hydrogen_electrolyzer/` (import-time RuntimeError) | None |
| **R1** | post-Council ratification of both this ADR and parent 2605263500 | Single ≤5 kg/day PEM electrolyzer benchtop on LANDS parcel + ≤20 kg storage @ 200 bar + open-hardware control firmware | 5 kg/day |
| **R2** | post-R1 + ≥1 energy-engineer on Council technical advisory + ≤1 yr operation no incidents | ≤50 kg/day + ≤100 kg storage @ 350 bar + first fuel-cell-vehicle (FCV) pilot if wadachi R3+ approves separately | 50 kg/day |
| **R3** | post-R2 + 30-day public + cross-actor mitsuho ammonia consultation | ≤500 kg/day religious-corp aggregate + ≤200 kg/parcel + ammonia ADR ratification (green NH₃ for fertilizer) | 500 kg/day |
| **R4+** | post-R3 + Council Lv6+ ≥3 per facility | ≤700 bar storage permitted per-facility Council approval | per Council |

## §6 New Lexicons

```
com.etzhayyim.hikari.{
  hydrogenProductionAttestation,    # per-kg: electricity source CID + temporal-coincidence proof ≤15min + water source
  hydrogenStorageInventory,         # per-LANDS-parcel: kg current + pressure + cylinder cert
  hydrogenSafetyAttestation,        # per-facility commissioning: OSHA/NFPA-equivalent compliance
  silenHydrogenReview               # annual Council Lv6+ ≥3 mass-balance + leak-rate audit
}
```

# Consequences

**Positive**:
- Long-duration energy storage option (electrolyze hikari surplus → H₂ → fuel cell back to electricity; round-trip ~35–45% but bridges multi-day low-renewable gaps that battery cannot)
- Green NH₃ pathway opens for nitrogen-fertilizer self-sufficiency cross-actor with mitsuho (currently fertilizer is grey-H₂-derived 95%+ globally — substantial constitutional gap)
- Transport-fuel pathway for heavy duty (wadachi R3+ FCV pilot if approved) where battery weight is prohibitive at sarutahiko ~26-40 t scale

**Negative**:
- Electrolyzer capex ~$2,000-5,000/kW installed (commercial 2026); ≤5 kg/day R1 ~$50-100K capex
- Round-trip efficiency 35–45% (vs battery 85–95%) — only use case justified is long-duration / heavy-mobility, not short-cycle storage
- Atmospheric H₂ leakage is itself indirect GHG (GWP100 ~11 per IPCC AR6); §1.9 ≤2% leak-rate gate is tight
- Safety burden: H₂ flame is invisible + wide flammability range 4-75% in air + small molecule leaks through micro-cracks; safety culture investment required

# Alternatives Considered

- **Defer hydrogen indefinitely** (per ADR-2605202000 prior posture): rejected — D1..D5 framework cleanly evaluates green H₂ as PERMITTED; deferring leaves long-duration backup and fertilizer-N self-sufficiency unresolved
- **Permit all hydrogen colors at small scale**: rejected — grey/black/blue/pink fail multiple D-gates independently; relaxation would require Council Lv7+ unanimity per color cascade (impractical)
- **Permit grey H₂ as transitional bridge**: rejected — Charter Rider §2(d) absolute on new fossil extraction; no "transitional" carve-out historically (chigiri / iyashi / mizuho all reject transitional commercial vendor compromises)

# Open Questions

1. **Electrolyzer technology selection R1**: PEM (Nafion membrane, fast response, Pt catalyst rare-earth concern) vs AEM (alkaline-exchange, Ni catalyst, lower TRL) vs alkaline (oldest, robust, slow response). To be decided at R1 ADR.
2. **Hydrogen storage cylinder open-hardware**: Type III (Al liner + CFRP) and Type IV (HDPE liner + CFRP) cylinders are vendor-IP-dense industry. Open-design needed.
3. **Leak detection open-hardware**: H₂ sensors (electrochemical, catalytic, MEMS thermal-conductivity, optical) — selection + open-firmware spec at R2.
4. **Ammonia ADR sibling**: when proposed?  Green NH₃ depends on green H₂; ADR sequence is H₂ R1 then NH₃ R0.

# References

- ADR-2605263500 (parent D1..D5 framework)
- ADR-2605261100 (hikari R0 renewable electricity source)
- ADR-2605202000 (energy substrate predecessor, hydrogen deferral now closed by this ADR)
- ADR-2605192200 (Charter Rider §2(d) new fossil extraction ban)
- IEC 62325-451-8 — Energy attribute certificate temporal-matching standard
- IPCC AR6 WG1 Ch.6 §6.4 — atmospheric hydrogen as indirect GHG
- NETL CCS site stewardship guidance — referenced for §2 blue H₂ multi-gen CCS liability
- OSHA 1910.103 — H₂ handling reference (open-publication safety framework)
- NFPA 2 — Hydrogen Technologies Code reference
