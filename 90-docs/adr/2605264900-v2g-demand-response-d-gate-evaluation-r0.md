---
id: adr-2605264900-v2g-demand-response-d-gate-evaluation-r0
title: "Vehicle-to-grid (V2G) + demand-response coordination — D1..D5 evaluation R0 (cross-actor wadachi/futawa/sarutahiko/suki + hikari microgrid; without smart-meter PII per hikari N7)"
status: proposed-pending-council-ratification
doc_type: adr
topic: v2g-demand-response-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 7.2
axis: constitutional
weight: 0.72
priority_note: "Sub-ADR of ADR-2605263500. Permits bidirectional EV battery dispatch (V2G) into religious-corp microgrid (hikari §2.1) AND aggregate-only demand-response coordination across facilities (iyashi / hagukumi / manabi / yakushi / mitsuho greenhouse) WITHOUT per-device smart-meter PII (hikari R0 N7 absolute inheritance). Verdict: V2G PERMITTED ≤25 kW per vehicle through R3 + aggregate ≤500 kW religious-corp through R3; demand-response coordination PERMITTED per-facility aggregate ≥1-hour buckets only (NO per-appliance, NO per-member-device); commercial-grid V2G or commercial-DR-program participation ABSOLUTELY PROHIBITED."
authoritative_for:
  - "V2G bidirectional dispatch D1..D5 evaluation; consumer-side ADR coupling per transport actor"
  - "Demand-response coordination protocol (aggregate ≥1-hour buckets; NO per-device PII)"
  - "Commercial-grid V2G + commercial-DR-program participation absolute prohibition (D1 + hikari G13 + N7)"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605261100
  - adr-2605242000-roso-pattern-frontier-distill
  - adr-2605252500-sarutahiko-heavy-truck-manufacturing-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - adr-2605264200-mechanical-energy-storage-d-gate-evaluation-r0
  - adr-2605181100-mst-encrypted-records-signal-keywrap
supersedes: []
superseded_by: []
---

# ADR-2605264900: V2G + demand-response — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade

# Context

EV fleet operating at religious-corp scale (wadachi / futawa / sarutahiko / suki R3+) has aggregate battery capacity comparable to dedicated storage. V2G uses this idle capacity for grid-edge support. Demand-response (DR) coordinates discretionary loads (irrigation pumps, HVAC, water heaters, EV charging itself) to align with renewable generation peaks. Both need careful constitutional treatment because:

- V2G connecting to **commercial** grid would trigger hikari G13 (no commercial utility resale)
- DR via **commercial** aggregator (e.g., AutoGrid / Enel X / Honeywell DR) would trigger D1 commercial-vendor dependency
- Per-device smart-meter DR violates hikari R0 N7 (no smart-meter surveillance)

ADR-2605263500 D1..D5 framework enables principled design.

# Decision

## §1 V2G into religious-corp microgrid — CONDITIONALLY PERMITTED

≤25 kW bidirectional per vehicle through R3; ≤500 kW religious-corp aggregate.

| Gate | Assessment |
|---|---|
| **D1** | ✓ Religious-corp microgrid (hikari §2.1 + ADR-2605264200 mechanical-storage cross-actor); vehicle owned by religious-corp consumer-side actor (wadachi/sarutahiko/futawa/suki) per cross-actor ADR; open-hardware bidirectional charger |
| **D2** | ✓ Battery degradation from V2G cycling is multi-gen-bounded; cycle accounting MANDATORY |
| **D3** | ✓ No carbon (V2G is electrical) |
| **D4** | ✓ No fissile |
| **D5** | ✓ Bidirectional charger + grid-edge controller + coordination protocol Apache 2.0 + Rider |

**Conditions**:

1. **Religious-corp microgrid only** — V2G into commercial utility grid **PROHIBITED** (G13 + N6 large-utility scope). Vehicle's V2G port may only physically connect to religious-corp microgrid-attested charging post per `hikari.installAttestation`
2. **Per-vehicle ≤25 kW bidirectional** through R3 (proportionate to typical light-EV ~7 kW AC L2 → ~22 kW DC fast-charge bracket; higher for sarutahiko fleet R4+ Council Lv6+ ≥3)
3. **Aggregate ≤500 kW religious-corp** through R3 (= 20+ vehicles fleet)
4. **Battery cycle accounting MANDATORY**: each V2G discharge cycle counts toward vehicle's nameplate cycle-life budget; warranty + replacement cost borne by religious-corp Public Fund per `toritate.ledgerEntry` (cross-actor with toritate accounting); SoC swing kept within 30%-80% to minimize degradation impact per vehicle owner agreement
5. **Bidirectional charger open-hardware**: ISO 15118 + IEEE 2030.5 protocol implementation MUST be open-source (most commercial bidirectional chargers — Wallbox Quasar / Fermata FE-15 / etc. — have proprietary firmware; religious-corp uses open-firmware retrofit OR open-design from scratch)
6. **Aggregate dispatch coordination**: discharge events scheduled by hikari microgrid controller based on aggregate generation deficit + storage SoC + cross-actor priority load (iyashi clinical emergency > yakushi WFI > mitsuho cold-chain > daily-living facilities)
7. **No commercial-DR-program participation**: religious-corp fleet does NOT register with commercial DR programs (PJM / CAISO / Open ADR / etc.); D1 commercial-vendor dependency + N7-adjacent per-device telemetry
8. Annual `silenV2gReview` Council Lv6+ ≥3: cycle accounting + battery-degradation impact + per-vehicle owner-fairness audit

## §2 Demand-response coordination — CONDITIONALLY PERMITTED with strict privacy

Coordinated dispatch of discretionary loads across religious-corp facilities to align with renewable generation peaks + storage SoC.

| Gate | Assessment |
|---|---|
| **D1** | ✓ Religious-corp internal coordination only |
| **D5** | ✓ Coordination protocol Apache 2.0 + Rider |
| hikari R0 **N7** | **⚠ binding** — no smart-meter per-device PII |

**Conditions** (N7 inheritance is the binding constraint):

1. **Aggregate-only**: telemetry per facility per ≥1-hour bucket only; NO per-appliance / NO per-member-device telemetry; NO per-individual usage attribution at any time-resolution
2. **Dispatchable loads scoped to non-personal**:
   - mitsuho irrigation pumps (can shift 30-90 min)
   - hikari water-heater preheat (cross-actor with mizuho)
   - EV charging (scheduling of when to charge, NOT discharge — that's §1 V2G)
   - mitsuho greenhouse supplemental lighting (1-2 hour shift)
   - tatekata cement-curing temperature ramp (slow thermal mass, hours)
   - DAC §1 regeneration heat dispatch (ADR-2605264600 cross-actor)
   - **EXCLUDED**: residential HVAC of any individual member home (privacy + paternalism — members control their own home loads, not religious-corp infrastructure layer)
3. **Coordination protocol**: Murakumo-only inference for dispatch optimization per ADR-2605215000; NO commercial DR-aggregator / NO Google Nest DR / NO Amazon Sidewalk / NO ConnectedHome
4. **Encrypted transport**: even aggregate telemetry SHOULD use `com.etzhayyim.encrypted.*` envelope (ADR-2605181100) for facility-level data above L4 Care tier (iyashi facility electrical load could leak operational metadata if intercepted)
5. **Coordination logs publicly attestable**: aggregate dispatch decisions logged via `dispatchCoordinationRecord` Lexicon on IPFS (operator transparency)

## §3 Charging-only (unidirectional, no V2G discharge) — UNRESTRICTED within hikari §2.1

For clarity: unidirectional charging from hikari microgrid to religious-corp EVs is NOT V2G and is already covered by hikari R0 §2.1 (just a load). No separate ADR needed.

## §4 Cross-actor consumer ADR registry (R3+ activation gate)

V2G permitted under §1 only if consumer-side ADR exists for vehicle type:

| Vehicle actor | Required ADR |
|---|---|
| wadachi R3+ light passenger | wadachi V2G consumer ADR (TBD) |
| sarutahiko R3+ heavy Class-8 | sarutahiko V2G consumer ADR (TBD) — high capacity per vehicle (~50-100 kWh battery) |
| futawa R3+ motorcycle | futawa V2G consumer ADR (TBD; small but numerous fleet) |
| suki R3+ farm tractor | suki V2G consumer ADR (TBD; large battery, mostly-parked-at-night profile ideal for V2G) |

## §5 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; path-reserved `20-actors/hikari/cells/v2g_dispatch/` + `demand_response_coordination/` import-time RuntimeError | None |
| **R1** | post-Council + first consumer-actor R3 ADR ratify + hikari R2 microgrid + bidirectional charger open-design completed | First V2G ≤10 kW bidirectional pilot at single hikari R2 facility with single vehicle | 1 vehicle |
| **R2** | post-R1 + 30-day public + cross-actor consumer attestation + 6-mo cycle-accounting data | ≤25 kW per vehicle + ≤200 kW aggregate + first §2 DR coordination protocol pilot at ≤3 facilities | 8 vehicles + 3 facilities DR |
| **R3** | post-R2 + Council Lv6+ ≥3 + ≥1 yr safe operation | Full §1+§2 caps; encryption envelope enforcement at L4 facilities | per-class caps |

## §6 New Lexicons (R1+)

```
com.etzhayyim.hikari.{
  v2gFacilityAttestation,                # bidirectional charging post + open-firmware CID + nameplate kW
  v2gDispatchRecord,                     # per-event: vehicle DID + cycle delta + SoC range + energy in/out
  v2gCycleAccounting,                    # per-vehicle quarterly cycle-life budget consumption
  drFacilityRegistry,                    # facility ID + dispatchable load classes + ≥1-hr aggregation window
  drDispatchCoordinationRecord,          # per-event: facility aggregate load shift kWh + decision rationale
  silenV2gReview,                        # annual Council Lv6+ ≥3 cycle accounting + owner-fairness audit
  silenDemandResponseReview              # annual Council Lv6+ ≥3 N7 PII-free attestation
}
```

# Consequences

**Positive**:
- Idle EV fleet battery capacity (typical 20-100 kWh × ~20 vehicles = 400-2000 kWh) deeply complements hikari §2.1 stationary storage
- DR coordination unlocks 10-30% generation-load matching improvement without new storage capex
- Privacy-preserving design via N7 inheritance + ADR-2605181100 envelope = differentiated from commercial DR programs that monetize device telemetry

**Negative**:
- Battery degradation from V2G cycling reduces vehicle lifetime; cycle accounting + 30-80% SoC swing mitigates but not eliminates
- Bidirectional charger capex ~$2,000-5,000 per unit incremental over unidirectional (~$1,000); ROI dependent on cycle-life economics
- Coordination protocol complexity vs simple time-of-use scheduling — Murakumo-only inference adds compute cost
- Owner-fairness governance for V2G battery degradation cost-sharing requires toritate Public Fund accounting (cross-actor)

# Alternatives Considered

- **Permit commercial-grid V2G**: rejected (G13 + N6 + D1)
- **Permit commercial DR-program participation for revenue**: rejected (D1 + Charter §2(b) financialization)
- **Per-appliance smart-meter DR**: rejected (N7 absolute)
- **Skip V2G in favor of dedicated stationary battery only**: considered — but idle EV capacity is genuinely underutilized; cross-actor cycle-life cost-sharing makes economics work

# References

- ADR-2605263500 (parent D1..D5)
- ADR-2605261100 (hikari R0 — G13 + N6 + N7 inheritance)
- ADR-2605264200 (mechanical-storage sibling; V2G is electrochemical-storage cross-actor)
- ADR-2605181100 (encrypted-record envelope for §2.4 facility telemetry)
- ADR-2605215000 (Murakumo-only inference extended to DR coordination)
- ISO 15118 — Vehicle-to-grid communication interface (referenced)
- IEEE 2030.5 — Smart Energy Profile (referenced)
- OpenADR Alliance — referenced (and explicitly NOT used per §1.7 D1)
