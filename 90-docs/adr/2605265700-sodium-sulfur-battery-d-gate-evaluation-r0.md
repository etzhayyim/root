---
id: adr-2605265700-sodium-sulfur-battery-d-gate-evaluation-r0
title: "Sodium-sulfur (NaS) molten-salt battery — D1..D5 evaluation R0 (sub-ADR of 2605263500; alternative chemistry per hikari R0 G3)"
status: proposed-pending-council-ratification
doc_type: adr
topic: sodium-sulfur-battery-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 6.4
axis: constitutional
weight: 0.64
priority_note: "Sub-ADR of ADR-2605263500. Extends hikari R0 §G3 battery chemistry (LFP / NMC restricted / sodium-ion preferred) with NaS as a fourth permitted chemistry for stationary long-duration storage. Verdict: NaS battery CONDITIONALLY PERMITTED ≤500 kWh per facility R3 with mandatory thermal-runaway containment + sodium-handling safety + open-formula ceramic electrolyte (β″-Al₂O₃); commercial NGK NaS proprietary modules PROHIBITED; ≤350°C operating temperature ceiling per R3; ≥10-yr cycle-life attestation per facility commissioning."
authoritative_for:
  - "NaS chemistry D1..D5 evaluation"
  - "Open-formula β″-alumina ceramic electrolyte requirement"
  - "Commercial NaS module (NGK Insulators primary global supplier) prohibition"
  - "Operating-temperature ceiling + thermal-runaway containment framework"
  - "Cross-actor with hikari mechanical-storage portfolio (ADR-2605264200 §6)"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605261100
  - adr-2605264200-mechanical-energy-storage-d-gate-evaluation-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605263800-biomethane-d-gate-evaluation-r0
supersedes: []
superseded_by: []
---

# ADR-2605265700: NaS molten-salt battery — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade

# Context

hikari R0 §G3 lists 3 permitted battery chemistries: LFP (LiFePO₄), NMC restricted-cobalt, sodium-ion. The list explicitly excluded lead-acid stationary R2+ on D2 multi-gen + safety grounds. NaS (sodium-sulfur) is a fourth chemistry with distinctive properties:

| Chemistry | Energy density (Wh/kg) | Cycle life | Operating temp | Capex (2026) |
|---|---|---|---|---|
| LFP (hikari G3) | 90-160 | 3000-7000 | 0-60°C ambient | $100-200/kWh |
| NMC restricted | 150-260 | 1000-3000 | 0-60°C ambient | $80-150/kWh |
| Na-ion (hikari G3) | 70-160 | 2000-5000 | -20 to 60°C | $80-130/kWh |
| Lead-acid (PROHIBITED) | 30-50 | 200-1500 | ambient | $50-80/kWh |
| **NaS molten** | **150-240** | **4500+** | **300-350°C** | **$200-350/kWh** |

NaS advantages: long cycle life, energy density 2-4× lead-acid, abundant sodium + sulfur, no rare elements. Disadvantages: 300-350°C operating temperature requires heated containment + insulation; molten-sodium handling has fire risk; commercial market dominated by NGK Insulators (Japan) which is proprietary IP.

# Decision

## §1 NaS battery for stationary long-duration storage — CONDITIONALLY PERMITTED

≤500 kWh per facility through R3; ≤5 facilities = ≤2.5 MWh religious-corp aggregate.

| Gate | Assessment |
|---|---|
| **D1** | ✓ Sodium + sulfur are commodity abundant materials; β″-Al₂O₃ ceramic electrolyte is open-publication chemistry (post-1967 declassified Ford Motor invention); cell + module + BMS open-hardware |
| **D2** | ✓ Spent NaS cells recyclable (Na recovered; S recovered as elemental); ceramic safely disposed; long cycle life (≥4500 cycles) means low replacement frequency over multi-gen horizon |
| **D3** | ✓ No carbon in operation; heated operation uses religious-corp electricity per ADR-2605215000 (NOT commercial grid) |
| **D4** | ✓ No fissile |
| **D5** | ✓ Cell + module + BMS + thermal-management firmware Apache 2.0 + Rider; β″-Al₂O₃ ceramic formulation open-publication (avoid NGK proprietary process; literature variants from MIT / Argonne / DLR sufficient) |

**Conditions**:

1. **Open-formula β″-Al₂O₃ ceramic electrolyte MANDATORY per D5**: religious-corp produces ceramic in-house using open-publication recipes (Na₂O·11Al₂O₃ stoichiometry + Li₂O or MgO stabilizer); **NGK Insulators proprietary NAS modules PROHIBITED**
2. **Operating temperature**: 300-350°C ceiling through R3 (higher temp = better ionic conductivity but more thermal stress + insulation burden); R4+ Council Lv6+ ≥3 per facility for higher temp
3. **Thermal-runaway containment MANDATORY**: per-cell molten-Na + molten-S separation by β″-Al₂O₃ ceramic; if ceramic fractures → Na + S exothermic reaction → cell-level shutdown via fusible link + module-level isolation valve + facility-level fire-suppression (open-hardware design per D5)
4. **Sodium fire safety**: per OSHA + NFPA equivalent open-publication safety frameworks for molten-Na handling; mandatory dry-powder Class D extinguisher (NO water — water + Na = H₂ + NaOH + heat); commissioning + annual Council Lv6+ ≥3 attestation
5. **Insulation**: vacuum-jacketed OR vermiculite-fill insulation MUST keep external surface ≤60°C during operation (safety for personnel); insulation open-hardware
6. **Cycle-life attestation**: per facility commissioning MUST demonstrate ≥4500 cycle capability via per-batch sampling test (destructive sampling of representative cells); annual capacity-fade monitoring
7. **Use case**: stationary long-duration storage (hours-to-days) complementing hikari §2.1 LFP/Na-ion (which serve sub-hour-to-day). NaS fits the multi-day-bridging gap between battery and pumped-hydro/H₂ in ADR-2605264200 §6 storage-tech-selection matrix
8. ≤500 kWh per facility through R3; aggregate ≤2.5 MWh
9. **EOL recyclability ≥90%** per hikari G7 analog; Na recovery via cooling + filtering; S recovery via cooling + crystallization; β″-Al₂O₃ ceramic ground + recycled into new electrolyte
10. **Public maintenance + commissioning schedule on IPFS** per hikari G12
11. Annual `silenNasReview` Council Lv6+ ≥3

## §2 Commercial NGK NAS modules + other commercial NaS — PROHIBITED

| Failing |
|---|
| D1 — NGK Insulators is the primary global NaS commercial vendor (effectively monopoly); ~50 GWh deployed globally as of 2026 |
| D5 — NGK module IP is closed; cell-level formulation + assembly process is trade-secret |
| Charter §1.6 中間排除 |

PROHIBITED on triple-independent grounds.

## §3 Cross-actor storage-portfolio integration

Religious-corp R2+ storage portfolio per ADR-2605264200 §6:

| Time scale | Primary | Secondary | Tertiary |
|---|---|---|---|
| Sub-minute | Flywheel | LFP | NaS (overkill) |
| Minutes-to-hour | LFP | Na-ion | NaS (overkill) |
| Hours-to-day | LFP + Na-ion | Pumped-hydro-micro | **NaS §1 (fit-zone)** |
| Multi-day to weekly | Pumped-hydro-micro | **NaS §1 (fit-zone)** | H₂ / biomethane |
| Seasonal (months) | H₂ + biomethane + NH₃ | (NaS economically infeasible at this duration) | n/a |

NaS optimal niche: 6-24 hour discharge at constant power, e.g., overnight bridging for daytime-solar / 8-hr-shift industrial process / 1-2-day low-renewable bridging at hikari R2-R3 scale.

## §4 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; path-reserved `20-actors/hikari/cells/storage_nas/` import-time RuntimeError | None |
| **R1** | post-Council + hikari R2 microgrid + ≥1 electrochemist + ≥1 ceramic-engineer on Council + open-formula β″-Al₂O₃ in-house | Bench ≤5 kWh single-module pilot at ≤350°C; ceramic + cell + module open-hardware fabrication; ≥1000 cycle in-lab demonstration | 5 kWh |
| **R2** | post-R1 + 30-day public + Council Lv6+ ≥3 thermal-runaway containment attestation + 1-yr safe operation + ≥3000 cycle demonstration | ≤50 kWh per facility + first cross-actor multi-day-bridging deployment | 50 kWh (1 facility) |
| **R3** | post-R2 + Council Lv6+ ≥3 + 1-yr safe operation + ≥4500 cycle attestation + EOL plan | Full §1 cap | 500 kWh (5 facilities) |

## §5 New Lexicons (R1+)

```
com.etzhayyim.hikari.{
  nasModuleAttestation,                 # cell + module design CID + β″-Al₂O₃ formula + operating temp ceiling
  nasThermalRunawayContainmentSpec,     # fusible link + isolation valve + fire-suppression design CID
  nasCycleLifeAttestation,              # destructive sampling test result + cycle-count demonstration
  nasFireSafetyAttestation,             # OSHA/NFPA-equivalent + Class D extinguisher + commissioning Council Lv6+ ≥3
  silenNasReview                        # annual Council Lv6+ ≥3
}
```

# Consequences

**Positive**:
- Adds fourth chemistry to hikari battery portfolio for multi-day-bridging niche (LFP / Na-ion best at hours; H₂ best at months; NaS fills 6-24 hr gap)
- Open-formula β″-Al₂O₃ ceramic R&D contributes to global open-publication electrolyte commons
- Long cycle life (≥4500) gives 12-20-yr operational life — matches hikari G7 ≥30-yr panel lifetime ballpark
- Cross-actor with industrial process heat (300-350°C operating temperature could integrate with CSP §4 of ADR-2605264300 thermal cascade)

**Negative**:
- 300-350°C operating temperature is fire risk; thermal-runaway containment is non-trivial engineering
- Capex ~$200-350/kWh higher than LFP ~$100-200/kWh (religious-corp accepts for niche-fit)
- β″-Al₂O₃ ceramic in-house production capability requires multi-year ceramic-engineering capability build (kuni-umi cross-actor potential)
- Molten-sodium spill response training required
- NaS R&D path moves slowly globally; religious-corp open contribution will be slow

# Alternatives Considered

- **Skip NaS entirely (LFP + Na-ion + H₂ + pumped-hydro adequate)**: considered — but 6-24 hr discharge niche is genuinely underserved by other chemistries; NaS fits cleanly
- **Permit commercial NGK modules at small scale**: rejected per §2 D1+D5 vendor lock
- **Defer to R4+ until ceramic in-house mature**: considered — but R0 charter establishes the constitutional framework; R1+ benchtop work develops the ceramic capability

# References

- ADR-2605263500 (parent D1..D5)
- ADR-2605261100 (hikari R0 §G3 battery chemistry sibling)
- ADR-2605264200 (mechanical-storage portfolio cross-actor)
- Ford Motor Co NaS battery 1967 declassified (referenced for open-publication β″-Al₂O₃ baseline)
- Argonne National Lab NaS open-publication research (referenced)
- MIT NaS chemistry references (Cu(II)/Na cells variants, open-publication)
- NGK Insulators NAS commercial deployment data (referenced for §2 prohibition basis + niche-fit verification)
- OSHA 29 CFR 1910 + NFPA 484 — combustible-metal handling reference for §1.4
