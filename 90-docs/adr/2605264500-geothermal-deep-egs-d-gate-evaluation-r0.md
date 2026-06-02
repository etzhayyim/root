---
id: adr-2605264500-geothermal-deep-egs-d-gate-evaluation-r0
title: "Geothermal deep + Enhanced Geothermal Systems (EGS) — D1..D5 evaluation R0 (sub-ADR of 2605263500; extends hikari §2.1 micro ≤500 m / ≤500 kW)"
status: proposed-pending-council-ratification
doc_type: adr
topic: geothermal-deep-egs-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 7.6
axis: constitutional
weight: 0.76
priority_note: "Sub-ADR of ADR-2605263500. Extends hikari R0 §2.1 geothermal-micro (≤500 m bore / ≤500 kW/well) to medium-depth (500-3000 m / ≤2 MW) and EGS (Enhanced Geothermal Systems via hydraulic-fracturing-stimulated reservoirs). Verdict: medium-depth conventional geothermal CONDITIONALLY PERMITTED ≤2 MW/well with hydrogeology + induced-seismicity Council gates; EGS CONDITIONALLY PERMITTED at R&D scale ≤500 kW with hydraulic-stimulation Council Lv7+ unanimity per well + ≤M3.0 induced-seismicity tripwire; ultra-deep ≥3000 m + supercritical geothermal DEFERRED."
authoritative_for:
  - "Geothermal 4-tier depth/temperature classification (micro / medium-depth / deep / supercritical)"
  - "EGS hydraulic-stimulation conditional permit + tripwire framework"
  - "Cross-actor coupling: mizuho R2+ working-fluid water + hikari thermal-storage + CSP §5 heat-network integration"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605261100
  - adr-2605263100-mizuho-water-sanitation-tier-b-actor-r0
  - adr-2605264300-csp-solar-thermal-d-gate-evaluation-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192245-etzhayyim-global-land-sovereignty
related:
  - adr-2605192330-etzhayyim-extended-land-sovereignty-ocean-river-air-orbit
supersedes: []
superseded_by: []
---

# ADR-2605264500: Geothermal deep + EGS — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade

# Context

hikari R0 §2.1 permits geothermal-micro ≤500 kW/well + ≤500 m bore. Tier-medium (500-3000 m, ≤2 MW/well) and EGS (engineered fracture network in dry hot rock) were not addressed and were implicitly excluded by the depth cap. ADR-2605263500 D1..D5 enables principled extension.

| Tier | Depth | Temp | Resource | Religious-corp fit |
|---|---|---|---|---|
| **Micro** (hikari §2.1) | ≤500 m | 30-90°C | Heat-pump + GSHP | ✓ Already permitted |
| **Medium-depth** | 500-3000 m | 90-200°C | Direct binary-cycle | ✓ Conditional §1 |
| **EGS** | 2000-5000 m | 150-300°C | Hot dry rock + hydraulic stimulation | ✓ R&D conditional §2 |
| **Ultra-deep + supercritical** | ≥3000 m | ≥374°C | Supercritical water Rankine | DEFERRED §3 |

# Decision

## §1 Medium-depth conventional geothermal — CONDITIONALLY PERMITTED

≤2 MW thermal per well; ≤4 wells religious-corp aggregate through R3.

| Gate | Assessment |
|---|---|
| **D1** | ✓ Geothermal gradient = ambient subsurface flux; wellbore + heat-exchanger religious-corp-owned |
| **D2** | ⚠ Working fluid (water) circulates; spent brine reinjection mandatory (NO surface discharge per Charter §2(c)) |
| **D3** | ✓ No carbon (some non-condensable gases CH₄/CO₂/H₂S from formation may co-produce — capture + re-inject MANDATORY per §1.6) |
| **D4** | ✓ No fissile (NORM/Naturally Occurring Radioactive Material — Ra-226/228 from formation — flagged §1.5) |
| **D5** | ✓ Wellhead + binary-cycle ORC + pump open-hardware (vendor IP retrofit) |

**Conditions** (analogous to hikari R0 G1-G14 + new geothermal-specific):

1. Per-well ≤2 MW thermal through R3; religious-corp aggregate ≤4 wells / ≤8 MW thermal
2. Depth 500-3000 m only (medium-tier scope; deeper triggers §2 or §3)
3. mizuho R2+ cross-actor: working-fluid water sourcing + waste brine reinjection registered per `waterSupplySourceRegistry` + Charter §2(c)
4. Binary-cycle working fluid: water-steam preferred; if ORC required for low-temp resource (90-130°C), low-GWP HFO (GWP ≤10) only — NO HCFC / HFC ≥GWP 100
5. **NORM (Ra-226/Ra-228) screening MANDATORY**: every well produces NORM in scale + sludge; concentration + disposal plan per Council Lv6+ ≥3 attestation; landfill-class disposal NOT permitted (religious-corp internal monitored containment OR licensed offsite per local regulation)
6. Non-condensable gas capture: H₂S scrubbing MANDATORY (per Charter §2(c) — toxic gas); co-produced CH₄ → ADR-2605263800 biomethane pathway if economic; co-produced CO₂ → re-inject OR feed §2.2 microbial-hydrocarbon photobioreactor
7. **Hydrogeology baseline** Council Lv6+ ≥3 per well: groundwater stratigraphy + aquifer protection + reinjection-zone characterization (60-day public comment per site)
8. **Induced-seismicity monitoring**: passive seismic baseline ≥6 mo pre-drilling + real-time microseismicity during operation; ≥M2.0 → halt + Council review; ≥M3.0 → site abandonment trigger
9. Production yield Ed25519-signed per 15-min (G11 inherits)
10. Public maintenance schedule (G12 inherits)
11. No commercial utility resale (G13 inherits)
12. EOL plug + abandonment plan Council-approved at commissioning (50-yr stewardship per §1.9 multi-gen)
13. Annual `silenGeothermalDeepReview` Council Lv6+ ≥3

## §2 Enhanced Geothermal Systems (EGS) — CONDITIONALLY PERMITTED at R&D scale

≤500 kW thermal per well; ≤1 well religious-corp aggregate through R3.

EGS = hot dry rock at 2000-5000 m depth, hydraulically fractured to create artificial reservoir, water circulated injection-to-production well.

**Additional conditions on top of §1** (EGS-specific risks):

1. **Hydraulic stimulation Council Lv7+ unanimity per well**: hydraulic-fracturing of crystalline basement rock at 4-5 km depth has historical induced-seismicity precedent (Pohang 2017 M5.4, Basel 2006 M3.4, St. Gallen 2013 M3.6); Council Lv7+ unanimity per individual stimulation cycle, not just per facility
2. **Induced-seismicity tripwire**:
   - ≥M2.0 within 10 km of injection well → halt + 30-day technical review
   - ≥M3.0 within 10 km → site abandonment + Council Lv7+ unanimity for any future EGS attempt globally
   - Real-time monitoring with public IPFS-published feed; tripwire is **structural**, not discretionary
3. **No proppant chemistry beyond Council-approved list**: water + minimal-additive (≤0.5% mass total of friction reducer / scale inhibitor / biocide) — NO commercial fracking chemical packages (D1 commercial-vendor dependency + Charter §2(c) covert-substance disclosure)
4. **Closed-loop confirmation**: injected water vs produced water mass-balance ≥90% within 90 days; surface contamination from formation-fluid migration zero-tolerance
5. **No commercial fracking-service-company contract**: drilling + stimulation crews must be religious-corp internal OR open-publication academic partnership (no Schlumberger / Halliburton / Baker Hughes commercial fracking services); preserves §1.6 中間排除
6. **Aquifer separation Council Lv6+ ≥4/7**: stimulation zone MUST be ≥1500 m below any potable / agricultural / mizuho water-source aquifer per `waterSupplySourceRegistry`

## §3 Ultra-deep + supercritical geothermal (≥3000 m / ≥374°C) — DEFERRED to R4+

Supercritical geothermal (Iceland IDDP-1 demo, Krafla 2009 at 4500 m / 450°C) offers ≥10× heat-flux per well but engineering / corrosion / completion risks are R&D-frontier. Materials science for supercritical-water wellbore casings is open research; commercial vendor IP scarce.

DEFERRED to R4+ per-program ADR; current R0 verdict = future evaluation only.

## §4 Cross-actor heat integration

Medium-depth geothermal R2+ output flows into ADR-2605264300 §5 heat-network architecture:

```
geothermal medium-depth well (90-200°C heat)
    ↓ wellhead heat exchanger
hikari thermal storage (water tank / molten salt)
    ↓
    ├─→ mitsuho greenhouse heating
    ├─→ hagukumi / iyashi DHW + space heating
    ├─→ yakushi WFI preheat (paired with biomethane autoclave final-boost)
    ├─→ tatekata radiant floor
    └─→ biomethane digester thermophilic 55°C heating
```

## §5 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; path-reserved `20-actors/hikari/cells/geothermal_medium_depth/` + `geothermal_egs_rd/` | None |
| **R1** | post-Council + ≥1 hydrogeologist + ≥1 seismologist on Council + LANDS parcel + 6-mo passive-seismic baseline | First medium-depth ≤1 MW well at 1000-2000 m depth | 1 well |
| **R2** | post-R1 + 30-day public + cross-actor mizuho + iyashi heat-network attestation | ≤2 MW/well + heat-customer attestation + first EGS R&D evaluation site survey | 2 wells |
| **R3** | post-R2 + Council Lv6+ ≥3 + ≥2 yr safe operation | Full caps §1; first EGS ≤500 kW R&D well IF Council Lv7+ unanimity per stimulation + aquifer-separation attested | 4 wells + 1 EGS |

## §6 New Lexicons (R1+)

```
com.etzhayyim.hikari.{
  geothermalWellAttestation,                # depth + temp + capacity + open-hardware + hydrogeology baseline
  geothermalProductionRecord,               # 15-min interval thermal output Ed25519-signed
  geothermalNormDispositionRecord,          # NORM concentration + containment plan + audit
  egsStimulationAttestation,                # per-stimulation cycle Council Lv7+ unanimity record
  inducedSeismicityFeed,                    # real-time microseismicity IPFS feed
  silenGeothermalDeepReview                 # annual Council Lv6+ ≥3 across all geothermal tiers
}
```

# Consequences

**Positive**:
- Extends hikari §2.1 micro-only into useful baseload range (medium-depth 24/7 thermal at ≤2 MW/well)
- Opens religious-corp geothermal-rich LANDS parcel (Iceland / Japan / Indonesia / Philippines / Kenya / New Zealand) energy utilization
- EGS R&D path keeps religious-corp at open-research frontier vs commercial-only

**Negative**:
- Drilling capex ~$3-7M per medium-depth well; EGS ~$15-30M; non-trivial vs solar PV
- Induced-seismicity risk especially EGS — tripwire structural but reputational risk
- NORM disposal stewardship is multi-gen burden (Ra-226 half-life 1600 yr)
- Wellbore corrosion + scale (CaCO₃ / SiO₂) requires ongoing chemistry management
- mizuho cross-actor brine-handling adds complexity

# Alternatives Considered

- **Permit ultra-deep / supercritical at R0**: rejected — materials science immature; defer R4+
- **Reject EGS due to induced seismicity**: considered — tripwire framework + Council Lv7+ unanimity per stimulation provides proportional rigor; outright rejection forecloses open-research path
- **Use commercial fracking-service contract**: rejected per §2.5 D1 dependency

# References

- ADR-2605263500 (parent D1..D5)
- ADR-2605261100 (hikari R0 §2.1 micro sibling)
- ADR-2605264300 (CSP + heat-network cross-actor integration §5)
- ADR-2605263100 (mizuho — working-fluid water)
- IEA Geothermal Heat & Power 2023 tech brief — open-publication reference
- ISO 19101 + ISO 14001 — geothermal facility EMS reference
- Pohang 2017 (Korea) M5.4 EGS-induced earthquake — §2.2 tripwire precedent
- Basel 2006 (Switzerland) M3.4 EGS-induced earthquake — §2.2 tripwire precedent
