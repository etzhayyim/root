---
id: adr-2605264700-methanol-dme-synfuel-d-gate-evaluation-r0
title: "Methanol (CH₃OH) + Dimethyl ether (CH₃OCH₃ / DME) synfuel from green H₂ + DAC CO₂ — D1..D5 evaluation R0 (sub-ADR of 2605263500; first end-to-end closed-loop liquid synfuel)"
status: proposed-pending-council-ratification
doc_type: adr
topic: methanol-dme-synfuel-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 7.4
axis: constitutional
weight: 0.74
priority_note: "Sub-ADR of ADR-2605263500. First end-to-end closed-loop liquid synfuel pathway in the religious-corp energy substrate: green H₂ (2605263600) + DAC CO₂ (2605264600) → methanol via Cu/ZnO/Al₂O₃ catalyst → dehydrate to DME via γ-Al₂O₃ catalyst. Both can power wadachi/sarutahiko/futawa R3+ engines as diesel-substitute (DME especially clean-burning). Verdict: methanol + DME synthesis CONDITIONALLY PERMITTED ≤500 kg/day religious-corp aggregate R3; methanol-from-syngas via biomethane SMR PROHIBITED (D3 inherits — biomethane is already-released atmospheric CO₂; converting to syngas adds embodied-energy without net carbon benefit vs direct H₂+CO₂ route); methanol-from-fossil-syngas ABSOLUTELY PROHIBITED."
authoritative_for:
  - "Methanol + DME synthesis route D1..D5 evaluation (green H₂+CO₂ ✓ / biomethane-syngas ✗ / fossil-syngas ✗)"
  - "Synfuel conditional permit ≤500 kg/day religious-corp aggregate R3"
  - "Cross-actor liquid-fuel pathway for transport actors (wadachi/sarutahiko/futawa/suki R3+) — separate ratification per consumer ADR"
  - "Stoichiometry chain-of-custody attestation (green H₂ Lexicon CID + DAC CO₂ Lexicon CID → methanol/DME batch CID)"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605263600-hydrogen-economy-d-gate-evaluation-r0
  - adr-2605264600-direct-air-capture-d-gate-evaluation-r0
  - adr-2605263800-biomethane-d-gate-evaluation-r0
  - adr-2605242000-roso-pattern-frontier-distill
  - adr-2605252500-sarutahiko-heavy-truck-manufacturing-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605263700-green-ammonia-d-gate-evaluation-r0
supersedes: []
superseded_by: []
---

# ADR-2605264700: Methanol + DME synfuel — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade

# Context

Three independently-ratified-pending ADRs unlock the methanol/DME synfuel pathway:

| Feedstock | Source ADR | Lexicon attestation |
|---|---|---|
| Green H₂ | 2605263600 §1 | `hydrogenProductionAttestation` |
| Atmospheric CO₂ | 2605264600 §1-3 (DAC) | `dacCaptureRecord` |
| (alt) Biomethane CO₂ | 2605263800 §1 upgrading PSA tail-gas | `biomethaneProductionAttestation` |

Methanol (CH₃OH) and DME (CH₃OCH₃) synthesis from H₂+CO₂:
- Methanol: `CO₂ + 3 H₂ → CH₃OH + H₂O` (ΔH = -49 kJ/mol at 250°C, 50-100 bar over Cu/ZnO/Al₂O₃)
- DME (one-step from methanol or direct from syngas): `2 CH₃OH → CH₃OCH₃ + H₂O` (γ-Al₂O₃, 250-300°C)

Stoichiometry per kg methanol: 0.19 kg H₂ + 1.37 kg CO₂. Per kg DME: 0.26 kg H₂ + 1.91 kg CO₂.

Why this matters cross-actor:
- DME has cetane number 55-60 (diesel ~50); burns clean (no soot, ≤1% NOₓ vs diesel) → wadachi/sarutahiko diesel-substitute candidate
- Methanol → fuel-cell or methanol-ICE pathway; also feedstock for olefins / acetic acid / formaldehyde in religious-corp internal industrial chemistry
- Stoichiometry closes when religious-corp can deliver green H₂ at the scale of CO₂ availability (DAC §1 ≤3 t/day → ~1 t methanol/day theoretical max; well above this ADR's ≤500 kg/day R3 cap)

# Decision

## §1 Methanol synthesis from green H₂ + DAC CO₂ — CONDITIONALLY PERMITTED

≤500 kg/day religious-corp aggregate methanol production through R3.

| Gate | Assessment |
|---|---|
| **D1** | ✓ Both feedstocks religious-corp-internal per upstream ADRs; reactor + catalyst religious-corp-owned open-hardware |
| **D2** | ✓ No long-lived waste; spent Cu/ZnO/Al₂O₃ catalyst recyclable (Council-attested EOL plan) |
| **D3** | ✓ Closed-loop: CO₂ from atmosphere → methanol → combustion releases same CO₂ back to atmosphere (net ≈ 0 over annual cycle when paired with continuous DAC replenishment) |
| **D4** | ✓ No fissile |
| **D5** | ✓ Reactor + catalyst formulation + process control firmware Apache 2.0 + Rider |

**Conditions**:

1. **Feedstock chain-of-custody MANDATORY**: every batch carries `methanolBatchAttestation` Lexicon citing source `hydrogenProductionAttestation` CIDs + source `dacCaptureRecord` (or `biomethaneProductionAttestation` co-product CO₂) CIDs with mass-balance reconciliation within 5% of stoichiometric requirement
2. **No fossil-syngas pathway ever**: methanol via SMR + syngas from natural gas / coal **ABSOLUTELY PROHIBITED** (D1 commercial fossil + D3 fossil CO₂ + Charter §2(d) — triple-independent ban)
3. **No biomethane-syngas pathway**: methanol via biomethane SMR → syngas → methanol is **PROHIBITED through R3** — biomethane CO₂ is already-released-atmospheric carbon that should reach atmosphere (closed-loop) rather than be re-cycled with embodied-energy cost; biomethane is more efficiently used as direct combustion or turquoise H₂ pyrolysis per ADR-2605263800 §1.7. Re-evaluate at R4+ only if net energy-balance attestation Council Lv7+ shows efficiency win
4. Catalyst: Cu/ZnO/Al₂O₃ (Mittasch-class catalyst chemistry, public-domain since 1923) preferred; alternative Cu/ZrO₂ acceptable; **NO commercial proprietary catalysts** (Topsoe MK-101 / Süd-Chemie / Johnson Matthey specific formulations only acceptable if vendor-IP open-publication negotiated)
5. Reactor type: gas-phase fixed-bed (Lurgi-style) or slurry-phase liquid (Air Products LPMEOH-style); religious-corp R&D scale ≤500 kg/day prefers gas-phase fixed-bed (simpler control). Pressure ≤100 bar through R3
6. **Operating conditions**: 200-280°C, 50-100 bar pressure
7. Use restriction: religious-corp-internal energy substrate + intra-actor chemistry feedstock (NOT for commercial sale). Surplus may flow to other religious-corp actors via SBT↔SBT internal carve-out per ADR-2605192115 §3 only
8. Storage: methanol is liquid at ambient (no high-pressure vessel needed); standard chemical-resistant tank (carbon-steel + epoxy-coated OR HDPE for ≤10,000 L); per LANDS parcel ≤2,000 L storage; aggregate ≤10,000 L
9. **Toxicity safety**: methanol is acutely toxic (lethal dose ~30-100 mL, optic neuropathy at sublethal); per OSHA 1910.1200 + GHS labeling; mandatory PPE + leak detection + spill containment 110% of tank volume; **alcohol-content labeling MANDATORY to prevent ingestion confusion with potable alcohol** (esp. cross-actor with future religious-corp beverage production if any)
10. Annual `silenMethanolReview` Council Lv6+ ≥3: feedstock-CID chain audit + mass-balance + EOL catalyst disposition

## §2 DME synthesis (methanol dehydration) — CONDITIONALLY PERMITTED

≤200 kg/day religious-corp aggregate DME through R3 (more conservative than methanol because of higher fire risk).

**Conditions inherit §1 plus**:

1. Two-step preferred (methanol → dehydration to DME) over one-step direct-syngas
2. Catalyst: γ-Al₂O₃ (public-domain) OR HZSM-5 zeolite (open-publication formulation); proprietary catalysts same constraint as §1.4
3. **Fire safety**: DME has flash point -41°C + wide flammability range 3.4-27% — pressure-vessel storage MANDATORY (≤7 bar at ambient as liquefied gas, analogous to propane handling); per NFPA 58 LP-Gas Code equivalent open-publication framework
4. Use case priority: clean-burning diesel-substitute for wadachi/sarutahiko/suki R3+ (separately Council-ratified at consumer ADR) > stationary CHP > residential heating
5. **No commercial LPG-blend distribution**: DME is sometimes blended into commercial LPG markets at 20% — religious-corp DME is religious-corp-internal only (D1 + Charter §2(b))

## §3 Cross-actor consumer registry

R3+ consumer actors MUST ratify their own consumer-side ADR before drawing methanol/DME supply:

| Consumer actor | Use case | Required ADR (TBD) |
|---|---|---|
| wadachi R3+ | Methanol-ICE or DME-ICE light passenger autonomous vehicles | wadachi methanol/DME consumer ADR |
| sarutahiko R3+ | DME-ICE heavy Class-8 truck (G7 fuel-sunset offset at R2) | sarutahiko DME consumer ADR |
| futawa R3+ | Methanol-ICE motorcycle (G7 ABS-mandatory + ≤250cc 4-stroke; methanol-conversion via flex-fuel) | futawa methanol consumer ADR |
| suki R3+ | DME-ICE farm tractor (G7 fuel-sunset offset) | suki DME consumer ADR |
| stationary CHP (hikari R3+) | DME-fired turbine OR methanol-fueled SOFC for long-duration backup | hikari CHP integration ADR |
| iyashi R2+ | Methanol-fed reformer→H₂→PEM fuel cell for emergency clinical power | iyashi emergency-backup ADR |
| chemistry feedstock (future) | Methanol → formaldehyde / olefins / acetic acid for religious-corp internal industrial chemistry | future chemistry actor ADR |

## §4 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; path-reserved `20-actors/hikari/cells/methanol_dme_synthesis/` import-time RuntimeError | None |
| **R1** | post-Council + ADR-2605263600 H₂ R1 + ADR-2605264600 DAC R1 + ≥1 catalysis-chemist on Council | Bench-scale ≤5 kg/day methanol; no DME yet | 5 kg/day MeOH |
| **R2** | post-R1 + 30-day public + ≥1 yr safe operation + 5%-mass-balance attestation | ≤50 kg/day methanol + first DME dehydration pilot ≤10 kg/day | 50 kg/day MeOH + 10 kg/day DME |
| **R3** | post-R2 + Council Lv6+ ≥3 + first consumer-actor ADR ratified | Full caps §1+§2; consumer-side uptake gated on per-consumer ADR | 500 kg/day MeOH + 200 kg/day DME |

## §5 New Lexicons (R1+)

```
com.etzhayyim.hikari.{
  methanolBatchAttestation,           # per-batch: H2 Lexicon CIDs + CO2 Lexicon CIDs + mass-balance
  dmeBatchAttestation,                # per-batch DME (with parent methanol batch CIDs)
  methanolStorageInventory,           # per-LANDS-parcel + tank-grade + leak-containment
  dmeStorageInventory,                # per-LANDS-parcel + pressure-vessel + NFPA-58-equiv attest
  silenMethanolReview,                # annual Council Lv6+ ≥3 stoichiometry + safety + EOL audit
  silenDmeReview                      # annual Council Lv6+ ≥3
}
```

# Consequences

**Positive**:
- First end-to-end closed-loop liquid synfuel in religious-corp substrate; closes the H₂ → DAC → liquid-fuel chain
- Provides religious-corp-internal diesel-substitute pathway for heavy mobility actors (sarutahiko, suki) that battery-EV cannot yet displace at ≥26 t / agricultural-heavy-load scale
- Methanol as chemistry feedstock unblocks future religious-corp olefin / formaldehyde / acetic-acid industrial chemistry
- DME for emergency backup CHP / fuel-cell with much higher energy density than H₂ (no high-pressure / no LH₂)

**Negative**:
- Stoichiometry: 1 kg methanol needs 0.19 kg H₂ + 1.37 kg CO₂. At ADR-2605263600 R3 H₂ cap (500 kg/day) and ADR-2605264600 R3 DAC cap (3000 kg/day CO₂), max methanol output = 500/0.19 = 2,630 kg/day H₂-limited OR 3000/1.37 = 2,190 kg/day CO₂-limited. This ADR's 500 kg/day cap stays well within both — the upstream caps are the binding R3 constraint
- Capex methanol bench-scale ≤5 kg/day ~$100-300K
- Toxicity culture (methanol) + fire culture (DME) are non-trivial
- Engineering risk: Cu-catalyst poisoning by trace S / Cl / NH₃ in feed streams requires guard beds + analytical chemistry capability
- Round-trip energy efficiency (electricity → H₂ → methanol → combustion → electricity) is poor (~25-35%); pathway only economic for non-electric end-uses (mobility / heat / chemistry)

# Alternatives Considered

- **Direct CO₂ → CO + H₂ via reverse water-gas-shift, then methanol from syngas**: rejected — additional reactor + energy cost vs direct CO₂ hydrogenation; modern Cu/ZnO/Al₂O₃ handles CO₂ directly
- **Fischer-Tropsch hydrocarbons instead of methanol**: deferred — FT product slate (mix of paraffins / olefins / waxes) requires upgrading; methanol is single-product simpler R&D start. Future ADR may add FT for diesel-range hydrocarbons specifically
- **Permit fossil-syngas methanol as transitional**: rejected — Charter §2(d) absolute on new fossil; no transitional carve-out
- **Permit commercial-utility-scale methanol (>500 kg/day)**: rejected — hikari N6 commercial >10 MW analog applies; religious-corp scale stays distributed

# References

- ADR-2605263500 (parent D1..D5)
- ADR-2605263600 (H₂ feedstock)
- ADR-2605264600 (DAC CO₂ feedstock)
- ADR-2605263800 (biomethane upgrading CO₂ alternative feed)
- ADR-2605242000 (wadachi — consumer at R3+)
- ADR-2605252500 (sarutahiko — DME diesel-substitute consumer at R3+)
- IEA Methanol open-publication tech state 2023
- Mittasch H. *Adv. Catalysis* 2 (1950) — Cu/ZnO/Al₂O₃ catalyst public-domain reference
- George Olah, *Beyond Oil and Gas: The Methanol Economy* (2006) — referenced concept-only
- NFPA 58 — LP-Gas Code (referenced for §2.3 DME pressure-vessel framework)
- OSHA 1910.1200 — Hazard Communication Standard (referenced for §1.9)
