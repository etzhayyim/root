---
id: adr-2605265500-concentrated-pv-d-gate-evaluation-r0
title: "Concentrated photovoltaic (CPV) with III-V multijunction cells — D1..D5 evaluation R0 (sub-ADR of 2605263500; complements 2605264300 thermal CSP on the high-efficiency-PV axis)"
status: proposed-pending-council-ratification
doc_type: adr
topic: concentrated-pv-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 6.6
axis: constitutional
weight: 0.66
priority_note: "Sub-ADR of ADR-2605263500. Extends hikari R0 §2.1 PV (single-junction Si) into the high-efficiency-concentrated PV regime: III-V multijunction cells (InGaP/InGaAs/Ge) under 500-2000× sunlight concentration via Fresnel-lens or mirror optics. Verdict: III-V CPV with religious-corp-owned cell manufacturing PROHIBITED through R3 (MOCVD III-V epitaxy is commercial-vendor-IP-dense + supply-chain dependency); III-V CPV with open-publication cell + religious-corp assembly DEFERRED to R4+ with Council Lv6+ ≥3 per facility; Si-CPV (≤100× concentration, leveraging hikari R0 §2.1 Si cell baseline) CONDITIONALLY PERMITTED ≤200 kW per facility R3; ZERO-cobalt-permanent-magnet tracker mandatory (G8 inheritance from hikari R0). Land-use intensity is the binding constraint — CPV concentrates → footprint shrinks but requires direct-normal-irradiance (DNI) sites only."
authoritative_for:
  - "CPV technology classification (Si-CPV vs III-V multijunction) under D1..D5"
  - "III-V cell manufacturing prohibition (vendor-IP density + supply-chain depth incompatible with D1+D5)"
  - "DNI site qualification gate (direct-normal-irradiance ≥1800 kWh/m²/yr minimum for economic viability)"
  - "Tracker accuracy + Council attestation per facility"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605261100
  - adr-2605264300-csp-solar-thermal-d-gate-evaluation-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192245-etzhayyim-global-land-sovereignty
related:
  - adr-2605265000-district-heating-cooling-d-gate-evaluation-r0
supersedes: []
superseded_by: []
---

# ADR-2605265500: Concentrated PV — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade

# Context

hikari R0 §2.1 permits single-junction crystalline-Si PV. ADR-2605264300 covers thermal CSP. The third axis — high-efficiency concentrated PV — sits between: same direct-normal-irradiance physics as CSP but converts sunlight to electricity via PV cell rather than heat-engine.

| Class | Concentration | Cell technology | Lab record η | Religious-corp fit |
|---|---|---|---|---|
| Si-CPV (LCPV) | 10-100× | Crystalline Si (hikari R0 §2.1 reuse) | ~28% (1-junction) | ✓ §1 ≤200 kW/facility R3 |
| III-V CPV (HCPV) | 500-2000× | III-V multijunction (InGaP/InGaAs/Ge) | 46.7% (4-junction 2014) | ✗ §2 (III-V vendor lock) |
| Quantum-dot CPV | 100-500× | QD-absorber + III-V | R&D | DEFERRED |

# Decision

## §1 Si-CPV (low-to-medium concentration ≤100×) — CONDITIONALLY PERMITTED

≤200 kW electrical per facility through R3; ≤5 facilities religious-corp aggregate.

| Gate | Assessment |
|---|---|
| **D1** | ✓ Si cells per hikari R0 §2.1 already permitted; concentrator optics (Fresnel lens or mirror dish) + tracker + thermal management open-hardware |
| **D2** | ✓ No long-lived waste; same Si-cell EOL as hikari G7 (≥90% recyclable) |
| **D3** | ✓ No carbon |
| **D4** | ✓ No fissile |
| **D5** | ✓ Optics + tracker + cooling firmware Apache 2.0 + Rider |

**Conditions**:

1. ≤200 kW electrical per facility; ≤5 facilities = ≤1 MW religious-corp aggregate through R3
2. **Si cell sourcing per hikari R0 §G2** (no Uyghur-XUAR polysilicon; per-lot supply audit Council Lv6+ ≥3)
3. **Concentrator optics open-hardware**: Fresnel lens (PMMA/SOG) OR parabolic mirror; design + manufacturing per D5
4. **Tracker accuracy**: ≤0.1° pointing error for ≤100× concentration; Council Lv6+ ≥3 per facility calibration attestation
5. **NO NdFeB rare-earth magnets in tracker motors** per hikari R0 G8 (open-coil electrical excitation or stepper motors only — possible 5-15% efficiency penalty on motor side accepted)
6. **Active cooling**: heated absorber requires cooling loop; preferred = heat-recovery cogeneration delivering ≤80°C process heat into ADR-2605265000 district network (cross-actor synergy with §5 of 2605264300)
7. **DNI site qualification gate**: facility location MUST have direct-normal-irradiance ≥1800 kWh/m²/yr (CPV economic minimum; lower DNI makes flat-plate Si win); LANDS-attested with 1-yr DNI measurement campaign before commissioning
8. Same lifecycle (≥90% EOL recyclability per hikari G7), public maintenance schedule per hikari G12, no commercial utility resale per hikari G13
9. Annual `silenCpvReview` Council Lv6+ ≥3

## §2 III-V multijunction CPV (high concentration ≥500×) — PROHIBITED through R3

| Gate | Failing assessment |
|---|---|
| **D1** | ✗ III-V cells (InGaP/InGaAs/Ge) require MOCVD epitaxy that has 3 commercial vendors globally (Azur Space / Solar Junction-now-Microlink / Spectrolab-now-Boeing) — all vendor-IP-encumbered; supply-chain depth incompatible with §1.6 中間排除 |
| **D5** | ✗ III-V wafer + epitaxy process designs are commercial-IP; open-publication academic designs exist for individual junctions but full 3J/4J cell stack-up is vendor-proprietary |
| Indirect | Ge substrate sourcing (Ge from coal-fly-ash or zinc-mining byproduct) has Charter §2(g) supply audit complexity |

**Verdict**: PROHIBITED through R3. R4+ re-evaluation if:
- Religious-corp-owned open-publication III-V cell manufacturing capability emerges (multi-decade R&D commitment); OR
- Open-source III-V wafer + epitaxy IP becomes available (currently no such commons exists)

R4+ evaluation also constrained by: trade-export controls on III-V semiconductor (US ITAR/EAR partial); religious-corp jurisdictional risk attestation required per §2.3.8 of ADR-2605263500 §2.3 (analog of fusion-jurisdiction gate).

## §3 Quantum-dot CPV — DEFERRED to R4+

R&D-frontier; no open-publication mature designs. Re-evaluate R4+ if open-formula QD absorbers mature.

## §4 Cross-actor heat-recovery cogeneration

Si-CPV active cooling produces 50-80°C waste heat (the cells dissipate the unutilized 70% of incident concentrated solar). This heat is high-value cross-actor:

```
Si-CPV concentrator (200 kW electrical + 470 kW thermal at η=30%, dissipated)
    ↓ active cooling loop
ADR-2605265000 §1 4GDH/5GDH district network 50-80°C inlet
    ↓
    ├─→ mitsuho greenhouse
    ├─→ hagukumi/iyashi DHW
    ├─→ tatekata radiant floor
    └─→ biomethane (2605263800) digester mesophilic 35°C heating
```

Per-facility cogeneration attestation Council Lv6+ ≥3 (cross-actor with hikari R2+ district network).

## §5 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; path-reserved `20-actors/hikari/cells/cpv_si_lcpv/` import-time RuntimeError | None |
| **R1** | post-Council + hikari R2 Si baseline + ≥1 optical-engineer on Council + ≥1-yr DNI baseline | First ≤10 kW Si-CPV at 10× concentration pilot on DNI ≥2000 LANDS parcel | 10 kW |
| **R2** | post-R1 + 30-day public + tracker accuracy attestation + cross-actor district-heat consumer attestation | ≤100 kW per facility + heat-recovery cogeneration commissioned | 200 kW (1 facility) |
| **R3** | post-R2 + Council Lv6+ ≥3 + 1-yr safe operation + DNI verification + EOL plan | Full §1 cap; III-V evaluation re-opens at R4+ if open IP emerges | 1 MW (5 facilities) |

## §6 New Lexicons (R1+)

```
com.etzhayyim.hikari.{
  cpvFacilityAttestation,           # concentration ratio + tracker design CID + cooling-loop CID + DNI site cert
  cpvDniSiteCertification,          # ≥1-yr DNI measurement campaign data
  cpvHeatRecoveryAttestation,       # cogeneration heat delivery to district network
  silenCpvReview                    # annual Council Lv6+ ≥3
}
```

# Consequences

**Positive**:
- Extends hikari §2.1 PV into the concentrated regime with higher land-use efficiency
- Cross-actor heat-recovery cogeneration unlocks district-network use of CPV waste heat (otherwise dumped)
- DNI site qualification + tracker accuracy attestation framework reusable for future III-V case R4+

**Negative**:
- ≤200 kW/facility R3 is much smaller than commercial CPV plants (commercial typical 10+ MW), but consistent with hikari R0 N6 distributed-scale invariant
- DNI ≥1800 kWh/m²/yr requirement excludes most of Europe, Japan, and much of US east-of-Mississippi
- Tracker accuracy + maintenance burden vs flat-plate Si — Si-CPV adds complexity for ~10-15% efficiency gain over flat-plate at moderate concentration
- Heat-recovery integration requires district network at R2+ availability

# Alternatives Considered

- **Permit III-V at R0**: rejected per §2 D1+D5 vendor-IP density
- **Skip CPV entirely (Si flat-plate is sufficient)**: considered — but DNI-rich sites + cogeneration cross-actor make CPV worth exploring as second-mode of PV deployment
- **Permit thermal-only (skip electrical generation)**: that's ADR-2605264300 CSP, already covered

# References

- ADR-2605263500 (parent D1..D5)
- ADR-2605261100 (hikari R0 — flat-plate Si sibling + G8 NdFeB ban inheritance)
- ADR-2605264300 (thermal CSP — sibling solar-concentrating axis)
- ADR-2605265000 (district heating — cross-actor heat-recovery consumer)
- NREL CPV technology open-publication briefing
- Soitec / SolFocus CPV deployment history (referenced for III-V vendor-IP density assessment)
- AltaDevices GaAs cell (referenced for III-V vendor concentration)
