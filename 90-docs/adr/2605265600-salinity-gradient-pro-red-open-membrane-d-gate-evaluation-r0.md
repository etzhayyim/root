---
id: adr-2605265600-salinity-gradient-pro-red-open-membrane-d-gate-evaluation-r0
title: "Salinity-gradient PRO/RED with open-design membrane — D1..D5 evaluation R0 (sub-ADR of 2605263500; closes 2605264100 §4 membrane-IP gap)"
status: proposed-pending-council-ratification
doc_type: adr
topic: salinity-gradient-pro-red-open-membrane-d-gate-evaluation
authoritative: true
last_verified: 2026-06-16
priority: 6.5
axis: constitutional
weight: 0.65
priority_note: "Sub-ADR of ADR-2605263500. Closes the specific deferral in ADR-2605264100 §4 (salinity-gradient marine renewable membrane-IP gap). Verdict: PRO (pressure-retarded osmosis) and RED (reverse electrodialysis) CONDITIONALLY PERMITTED at R&D scale only with religious-corp-developed OR open-publication-licensed membranes; commercial proprietary membranes (Toray / Hydranautics / GE Power / Statkraft IP) PROHIBITED; closed-loop river-mouth deployment with estuarine impact Council Lv6+ ≥3 per site. Caps as per parent ADR-2605264100 §4 ≤50 kW per site, ≤1 site through R3."
authoritative_for:
  - "Salinity-gradient membrane open-design R&D pathway"
  - "Commercial PRO/RED membrane absolute prohibition (D1 + D5)"
  - "Cross-actor mizuho river-mouth site qualification + estuarine ecosystem attestation"
  - "PRO vs RED selection criteria for religious-corp R&D"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605264100-marine-renewable-d-gate-evaluation-r0
  - adr-2605263100-mizuho-water-sanitation-tier-b-actor-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192330-etzhayyim-extended-land-sovereignty-ocean-river-air-orbit
related:
  - adr-2605265000-district-heating-cooling-d-gate-evaluation-r0
supersedes: []
superseded_by: []
---

# ADR-2605265600: Salinity-gradient PRO/RED — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade

# Context

ADR-2605264100 §4 (salinity-gradient marine renewable) deferred membrane-IP gap: "Membrane chemistry MUST be open-source (most commercial PRO/RED membranes are vendor-IP-encumbered — membrane R&D required)". This ADR resolves the deferral.

| Technology | Working principle | Membrane chemistry | Lab-scale power density |
|---|---|---|---|
| **PRO (pressure-retarded osmosis)** | Fresh water osmotic pull across semi-permeable membrane lifts brine pressure, drives turbine | Thin-film composite polyamide (TFC) on polysulfone support — adapted from RO membranes | 1-3 W/m² (2026) |
| **RED (reverse electrodialysis)** | Salinity-driven ion flux across alternating cation- and anion-exchange membranes generates current | Sulfonated polystyrene-divinylbenzene cation-exchange + quaternary ammonium anion-exchange | 0.5-2 W/m² (2026) |
| Variants | Hybrid PRO-RED stacks; CapMix capacitor; reverse-flow nanofiltration | R&D-frontier | <1 W/m² |

Power density gap vs cost: PRO/RED needs ~5 W/m² to be cost-competitive with other renewables. Commercial focus has been on incremental polyamide / ion-exchange membrane improvements with IP density rising; open-publication progress is slower (Stanford, Wetsus academic consortia).

# Decision

## §1 PRO/RED with religious-corp-developed OR open-publication membranes — CONDITIONALLY PERMITTED at R&D scale

≤50 kW per site, ≤1 site religious-corp aggregate through R3 (inherits ADR-2605264100 §4 cap).

| Gate | Assessment |
|---|---|
| **D1** | ✓ Religious-corp R&D-owned membrane synthesis + stack assembly + balance-of-plant; river-mouth water = ambient flux |
| **D2** | ✓ Membrane EOL = polymer-recyclable / biodegradable composite preferred (avoid PFAS membrane chemistries per Charter §2(c)) |
| **D3** | ✓ No carbon |
| **D4** | ✓ No fissile |
| **D5** | ✓ Membrane formulation + stack design + control firmware Apache 2.0 + Rider per D5 |

**Conditions**:

1. **Membrane open-publication MANDATORY per D5**: membrane chemistry (polymer + crosslinker + casting solvent + post-treatment) MUST be published with OpenMTA-equivalent license OR religious-corp-developed in-house. **PROHIBITED commercial membranes**: Toray Industries TFC PRO membranes / Hydranautics RED stacks / GE Power Sepa / Statkraft proprietary IP. Academic open-publication acceptable references: Stanford Polyak group OPRO membranes, Wetsus RED stack open-design (per published procedure).
2. **No PFAS-containing membranes per Charter §2(c)**: perfluorinated chemistry membranes (Nafion-class for RED) are persistent-pollutant concern; alternative sulfonated-polystyrene-divinylbenzene or sulfonated-polyetheretherketone (SPEEK) open-formula preferred
3. **Mizuho R2+ cross-actor**: river-mouth deployment site MUST be `mizuho.waterSupplySourceRegistry` attested + Council Lv6+ ≥3 estuarine ecosystem baseline (per ADR-2605264100 §4.3)
4. **Salinity-gradient resource**: salinity difference ≥30 g/L (fresh vs sea) required for economic viability; brackish-water sites (≤15 g/L diff) DEFERRED to R4+
5. **Pretreatment burden**: river water + seawater both require pretreatment (UF/MF) to prevent membrane fouling — open-hardware pretreatment unit Apache 2.0 + Rider
6. **Power-density quality gate R3**: religious-corp R&D MUST demonstrate ≥1 W/m² power density before R3 scale-up; below threshold = re-design or DEFER (not economically meaningful)
7. **PRO vs RED selection R1**: site-specific (PRO better for high-Δsalinity ≥35 g/L deep estuaries; RED better for intermediate-Δsalinity + lower fouling tolerance); Council Lv6+ ≥3 per site
8. **Bidirectional discharge**: mixed-effluent discharged BACK to estuary at salinity intermediate between fresh/sea (cf. PRO/RED is a SALINITY-MIXING process — net effect on estuary is small zone of mixing immediately downstream of stack)
9. ≤50 kW/site, ≤1 site through R3 (parent §4 cap)
10. Annual `silenSalinityGradientReview` Council Lv6+ ≥3

## §2 Commercial proprietary membranes — PROHIBITED

| Membrane vendor | Failing gate |
|---|---|
| Toray Industries TFC PRO | D1 (vendor + Charter §1.6) + D5 (closed IP) |
| Hydranautics RED stack | Same |
| GE Power Sepa | Same |
| Statkraft PRO proprietary | Same |
| Nafion (DuPont) and other PFAS chemistries | D5 + Charter §2(c) substance-pollutant |

ABSOLUTELY PROHIBITED.

## §3 Hybrid / R&D-frontier variants — DEFERRED

CapMix (capacitor mixing), reverse-flow nanofiltration, dialytic battery — R&D scale only; DEFERRED to R4+ separate per-tech ADRs.

## §4 Cross-actor mesh

| Actor | Role |
|---|---|
| **mizuho** R2+ | River-mouth site qualification + waterSupplySourceRegistry attestation + pretreatment cross-actor |
| **hikari** R2+ | Electrical output integration into microgrid + ADR-2605264200 §3 mechanical-storage potential pairing for diurnal smoothing |
| **chigiri** R1+ | Estuarine ecosystem regulatory cross-jurisdictional |

## §5 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; **LANDED 2026-06-16** as runnable methods — `20-actors/funamori/` actor instantiated as the full kuni-umi 3-layer infra-robotics pattern: `methods/salinity_gradient.cljc` (PRO/RED **physics** + §1 gates as throwing `ex-info` assertions) + `methods/stack_robotics.cljc` (**kinematics** — boustrophedon anti-fouling coverage sweep per §5 + EOL membrane-module swap, over the shared kuni-umi substrate of ADR-2606091800; dry-run/no-server-key) + `methods/plant.cljc` (**plant+control** — M2-tidal generation → battery-buffered grid-tie smoothing → hikari microgrid handoff per §4; peak-power ≤50 kW reuses the §1.9 cap); **53 cljc tests / 224 assertions green** via babashka; `kotoba/{schema,seed}.edn` (`:funamori.{salinity,robotics,plant}.*` EAVT), 4 kotoba-native cell specs (`cells/*.edn` — site_qualification/membrane_attestation/power_characterization/stack_service, `.solve()` R1), 3 lexicons (§6), `manifest.edn` (15 gates). Physics validated vs the Table (PRO 2.1 W/m², RED ~1.2 W/m², seawater π≈29 bar). Design only — no hardware. | None |
| **R1** | post-Council + ≥1 membrane-chemist on Council + Funamori R0 + mizuho R2 river-mouth attested LANDS-marine parcel | Bench ≤1 kW PRO OR ≤500 W RED single-stack pilot; open-membrane R&D + power-density characterization | 1 kW |
| **R2** | post-R1 + 30-day public + power-density ≥1 W/m² demonstrated | ≤10 kW + ecosystem-impact baseline; PRO vs RED selection per §1.7 | 10 kW |
| **R3** | post-R2 + Council Lv6+ ≥3 + 1-yr safe operation + Δsalinity site cert | Full §1 cap | 50 kW (1 site) |

## §6 New Lexicons (R1+)

```
com.etzhayyim.funamori.{
  salinityGradientMembraneAttestation,   # technology (PRO/RED/hybrid) + membrane formula CID (open-publication) + power density characterization
  salinityGradientSiteAttestation,       # mizuho river-mouth + Δsalinity baseline + estuarine ecosystem
  silenSalinityGradientReview            # annual Council Lv6+ ≥3
}
```

# Consequences

**Positive**:
- Closes ADR-2605264100 §4 deferral with explicit open-membrane R&D framework
- Adds salinity-gradient as a third marine renewable axis (alongside tidal-stream + wave-small)
- Open-publication membrane R&D contributes to global open-science / non-IP renewable energy commons

**Negative**:
- Power-density floor 1 W/m² is below commercial-economic threshold (~5 W/m²); religious-corp accepts non-competitive cost for constitutional-substrate reasons
- Membrane R&D is a multi-decade chemistry program at small religious-corp scale; progress likely slow
- Mizuho cross-actor estuarine ecosystem assessment burden
- Pretreatment fouling control adds OpEx complexity

# References

- ADR-2605263500 (parent D1..D5)
- ADR-2605264100 §4 (parent marine renewable — closes the deferral here)
- ADR-2605263100 (mizuho cross-actor)
- ADR-2605264200 §3 (mechanical-storage cross-actor for diurnal smoothing)
- ADR-2605192330 (extended LANDS for river-mouth marine parcels)
- Pattle, R. E. "Production of electric power by mixing fresh and salt water" *Nature* 174 (1954) — original PRO/RED concept reference
- Loeb, S. + Sourirajan, S. asymmetric membrane (1962) — TFC-PRO ancestor reference
- Wetsus Centre Excellence — Netherlands open-publication PRO/RED research reference
- Stanford Polyak group — Open Polymeric Reverse Osmosis (OPRO) membrane reference
