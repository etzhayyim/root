---
id: adr-2605252600-yamabiko-high-speed-rail-manufacturing-r0
title: "ADR-2605252600: yamabiko (山彦) — High-Speed Rail Manufacturing Tier-B Actor R0 Scaffold (Wave 1 reference = civilian Shinkansen-class trainset)"
status: proposed
doc_type: adr
topic: yamabiko-high-speed-rail-manufacturing-r0
authoritative: true
last_verified: 2026-05-25
priority: 6.0
axis: architecture
weight: 0.60
authoritative_for:
  - yamabiko actor identity (name, DID, tier, namespace, scope boundary) — R0 reservation
  - high-speed rail manufacturing constitutional gates (G1..G14) and non-goals (N1..N12)
  - R0 → R3 phased roadmap with R1/R2/R3 ADR reservation
  - Wave 1 = civilian Shinkansen-class trainset (~250-320 km/h, 8-16 cars) reference fix
  - Wave 2-3 deferred (conventional + LRT/tram) carve-out reservation
  - 5-layer trainset assembly process (carbody → bogie → interior → traction → final + dynamic test + homologation)
  - 9 Pregel cell catalog + Murakumo placement (R0 design-only)
  - 4 new robotics class reservation (Tsugite / Wadasa / Toritsuke / Pantagora) + 3 inherited (Otete-heavy / Mimi-precision / Akari)
  - lexicon namespace reservation (`com.etzhayyim.yamabiko.*`, 9 record types)
depends_on:
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605242000-roso-pattern-frontier-distill
  - adr-2605252200-watatsumi-civilian-submersible-r0
  - adr-2605252400-kanayama-circular-metallurgy-r0
  - adr-2605252500-sarutahiko-heavy-truck-manufacturing-r0
  - adr-2605250715-tatekata-construction-tier-b-actor-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192315-etzhayyim-transparent-force-rd
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
  - adr-2605214000-etzhayyim-murakumo-mesh-no-vke-and-lexicon-port-rules
  - 2605191524-ameno-multi-tab-swarm-broadcast
related:
  - wellbecoming-karma-lean-proofs
  - wellbecoming-karma-lean-proofs
  - wellbecoming-karma-lean-proofs
supersedes: []
superseded_by: []
---

# ADR-2605252600: yamabiko (山彦) — High-Speed Rail Manufacturing Tier-B Actor R0 Scaffold

**Status**: proposed
**Date**: 2026-05-25
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify)
**ADR Hierarchy**: Sibling of ADR-2605252500 (sarutahiko 道, public-road trucks), ADR-2605252200 (watatsumi 水), ADR-2605252400 (kanayama 金), ADR-2605250715 (tatekata 土), ADR-2605242000 (wadachi 公道自律).

## Context

Modern high-speed-rail trainset manufacturing — Hitachi A-Train (Kasado / Newton Aycliffe) / Kawasaki efSET / Talgo Avril / Siemens Velaro / Alstom Avelia — has matured into **friction-stir-welded extruded-aluminum carbody + bogie modular + multi-system integration** assembly. The methodology generalises across conventional rail (EMU/DMU/BEMU), light rail (LRT), and high-speed (≥250 km/h Shinkansen / TGV / ICE class) with shared bogie + traction + signalling primitives.

Until this ADR, religious-corp has:
- `sarutahiko` (ADR-2605252500) covering public-road trucks (heavy commercial vehicle manufacturing)
- `wadachi` (ADR-2605242000) covering public-road autonomous operation
- but **no Tier-B actor covering rail (track-bound) vehicle manufacturing**

Rail vehicles are methodologically distinct from road vehicles:
- bogies + wheel sets + pantograph + ATP/ATO are domain-specific
- the witness invariant for FSW carbody seams + bogie torquing differs from sarutahiko marriage
- the homologation regime (EN 50126/8/9 RAMS / 日本鉄道事業法 / FRA Tier I-III) is rail-specific
- the operating model (track-bound, GoA 1-4 ATO, signal-controlled) is fundamentally different from SAE J3016 Levels

This ADR fills that gap by reserving `yamabiko` as a Tier-B actor. Constitutional posture is **strongly favorable for civilian rail** (rail is structurally democratic transit — §2(e) anti-gatekeeping aligned, §2(g) efficient land use, §1.13 wellbecoming positive vs car-centric mobility), but with **heavy §2(a) carve-out** against armored / military rail (armored trains, missile-on-rail TEL, military supply trains) and **N4 diesel locomotive sunset** at R2 gate paralleling sarutahiko G7 fossil sunset.

The user-prompted source reference is YouTube video `KFSPENlRdFU` ("Inside Giant Factory Building Super Modern High-Speed Trains From Scratch"). Methodology adopted; military-rail / mass-surveillance / vanity-project applications rejected per §2(a) + §2(d).

## Decision

### 1. Actor identity

| Field | Value |
|---|---|
| Actor name | `yamabiko` |
| Japanese | 山彦 / やまびこ (Shinto 山の精霊 mountain echo deity / こだま伝承; JR 東日本 E2/E5 系新幹線愛称 — religious-corp 山岳信仰 and rail-愛称 traditions both align) |
| Display name | `山彦 (yamabiko)` |
| Tier (ADR-2605192415 §B) | **B** — per-domain leader, sibling of sarutahiko / wadachi / watatsumi / kanayama / tatekata / yakushi / silicon / kuni-umi |
| Path-based DID | `did:web:etzhayyim.com:yamabiko` |
| Per-trainset DID pattern (reserved) | `did:web:etzhayyim.com:yamabiko:trainset:<serial>` |
| Per-car DID pattern (reserved) | `did:web:etzhayyim.com:yamabiko:car:<serial>` |
| Repo location | `20-actors/yamabiko/` |
| Lexicon namespace | `com.etzhayyim.yamabiko.*` |
| License | Apache 2.0 + Charter Compliance Rider v2.0 |

### 2. Scope (R0)

**Wave 1 reference (R0–R3 in scope)**: Civilian Shinkansen-class high-speed trainset (~250-320 km/h, 8-16 cars). Hitachi A-Train / Kawasaki efSET / Talgo Avril / Siemens Velaro / Alstom Avelia class. End-to-end: carbody → bogie → interior → traction + electrical → final assembly → dynamic test → homologation.

**Wave 2-3 deferred (Council Lv6+ activation)**:
- Wave 2: Conventional rail (EMU / DMU / BEMU, ~120 km/h commuter + intercity)
- Wave 3: Light rail / tram (LRT, ≤80 km/h, low-floor, urban)

**Constitutional non-goals (R0–R3, immutable):** see §5 below.

### 3. 5-Layer Assembly Process

| Layer | Stage | Wave 1 key technology |
|---|---|---|
| **L1** | Aluminum / composite carbody fabrication | Friction Stir Welding (FSW) Hitachi A-Train double-skin extrusion; Al alloys 6N01 / A6005C; FSW seam + spot weld |
| **L2** | Bogie assembly | Cast steel bogie frame (igata Wave 2 source R3+) + air spring + tread brake + axle + wheel set + traction motor (PMSM / IM) |
| **L3** | Interior + HVAC + PIS | Al-honeycomb floor + fire-retardant seating + wheelchair-accessible toilets + vacuum waste + HEPA AC + multilingual passenger information system |
| **L4** | Traction electrical + pantograph + signalling + ATO | 25 kV AC / 1500 V DC pantograph + traction inverter + Automatic Train Protection (ATP) + GoA 2/3 Automatic Train Operation + IP67 cable harness |
| **L5** | Final assembly + dynamic test + homologation | Bogie + carbody marriage + cab + livery + static test + dynamic test on ≥100 km test track + EN 50126/50128/50129 (RAMS) / 日本鉄道事業法 / FRA Tier I-III certification |

### 4. Constitutional Gates (G1–G14, IMMUTABLE R0–R3)

| Gate | Requirement |
|---|---|
| **G1** | Control firmware (ATP / ATO / traction) + carbody CAD + bogie CAD **open-source** (Apache 2.0 + Charter Rider) |
| **G2** | Per-trainset manufacturing log **kotoba-datomic anchor** + open trainset registry |
| **G3** | Per-trainset **IPFS-pinned photo + video** (FSW seam / dynamic test / homologation) |
| **G4** | Every critical FSW + bogie marriage signed by witness quorum ≥2 robots (Ed25519, DID-bound) |
| **G5** | Operator manual + passenger PIS **JP + EN + local-language trilingual minimum** |
| **G6** | All CAD + firmware pass **Charter Rider §2(a-h) scan** |
| **G7** | **Propulsion**: full electrification (overhead 25 kV AC / 1500 V DC / third-rail) as default. **R0/R1 transition**: BEMU + H₂ fuel-cell hybrid acceptable. **Diesel locomotive = §2(g) prohibited at R2+ gate.** Conventional rail Wave 2 BEMU migration mandated. |
| **G8** | Wayside noise ≤ ISO 3095 + 日本騒音規制法 + vibration ≤60 dB at trackside boundary + EMC IEC 62236 |
| **G9** | CAD only from **vendor-free tools** (FreeCAD / OpenSCAD / Open CASCADE) |
| **G10** | Inference paths via **Murakumo no-VKE mesh only** |
| **G11** | High-voltage (1.5 kV / 25 kV) + bogie installation + paint booth = **SBT-gated personnel** + 1 SBT = 1 vote council review for non-SBT visitors |
| **G12** | **KPI caps**: Wave 1 commercial max speed ≤320 km/h / trainset length ≤450 m / **autonomous operation ≤ GoA 3** (driverless GoA 4 = constitutional non-goal Wave 1; deferrable R3 + Council Lv6+) |
| **G13** | Per-trainset **DID** (`did:web:etzhayyim.com:yamabiko:trainset:<serial>`) + per-trainset key |
| **G14** | **EoL recyclability ≥90% by mass** (closes back to kanayama Wave 1 Al + Wave 2 steel + Wave 3 Cu + interior plastic stream) + scrapping yard §2(h) waste tracking |

### 5. Non-Goals (N1–N12, IMMUTABLE R0–R3)

| # | Non-Goal | Constitutional anchor |
|---|---|---|
| **N1** | **Military trains** (armored trains, missile-on-rail TEL, military supply trains, troop transport) | §2(a) weapons platform |
| **N2** | **Border guard / police transport / riot control rail** | §2(d) state-violence amplifier |
| **N3** | **Nuclear / chemical / biological material transport** (NBC) | §2(a) + radiological boundary |
| **N4** | **R2+ diesel locomotive** (R0/R1 transition only; R2+ full electrification + H₂/NH₃ hybrid mandatory) | §2(g) + G7 |
| **N5** | **Proprietary signalling + ATP/ATO firmware NDA** | §2(b) anti-secrecy |
| **N6** | **Third-party advertising train wraps** (route maps + safety information permitted) | §2(c) anti-advertising |
| **N7** | **Fully autonomous unmanned operation** (GoA 4) Wave 1; deferrable R3 + Council Lv6+ | wellbecoming + safety |
| **N8** | **Mass-surveillance trains** (face recognition PIS / passenger behavior tracking) | §2(d) §2(h) wellbecoming |
| **N9** | **Passenger surveillance UX** (biometric monitoring with data sale) | §2(d) §2(h) |
| **N10** | **Luxury first-class / premium-only trains** (structural democratic-access destruction) | §2(e) anti-gatekeeping |
| **N11** | **National prestige vanity projects** (operational ROI-blind politically-driven specs) | §2(b) §2(d) |
| **N12** | **Proprietary coupling / bogie / gauge** breaking interoperability | §2(b) §2(e) |

### 6. Pregel Cell Catalog (9 cells, R0 = import-time RuntimeError)

| Cell | Stage | Murakumo node | Input | Output |
|---|---|---|---|---|
| `carbody_fabrication` | L1 | naphtali | `aluminumExtrusionLot`, `carbodySpec` | `carbodyAttestation` |
| `bogie_assembly` | L2 | joseph | `wheelSetLot`, `motorLot`, `brakeLot` | `bogieAttestation` |
| `interior_hvac` | L3 | zebulun | seating + HVAC + PIS components | `interiorAttestation` |
| `traction_electrical` | L4 | levi | pantograph + ECU + ATP/ATO firmware | `tractionElectricalAttestation` |
| `final_assembly` | L5a | simeon | carbody + bogie + interior + electrical | `finalAssemblyAttestation` |
| `dynamic_test` | L5b | dan | ≥100 km test track | `dynamicTestRecord` |
| `homologation_binder` | L5c | judah | EN 50126/8/9 + 鉄道事業法 + FRA | `homologationRecord` |
| `emissions_acoustic_audit` | cross-cutting | levi | continuous wayside telemetry | `acousticEmissionsAuditRecord` |
| `silenRailReview` | governance | judah | Council 5-of-7 Safe | review record |

R0 contract: each cell module imports cleanly; instantiating its class succeeds; calling `.solve()` raises `RuntimeError("yamabiko R0 scaffold: activate via Council ADR-2605252615 post-ratification")`.

### 7. Lexicons (9 record types under `com.etzhayyim.yamabiko.*`, R0 stubs)

```
carbodyAttestation              # L1 FSW Al extrusion carbody
bogieAttestation                # L2 wheelSet + motor + brake
interiorAttestation             # L3 seating + HVAC + PIS
tractionElectricalAttestation   # L4 pantograph + ECU + ATP/ATO firmware (G1 open-source mandate)
finalAssemblyAttestation        # L5a marriage + livery + ≥2 robot witness
dynamicTestRecord               # L5b ≥100 km test track
acousticEmissionsAuditRecord    # cross-cutting ISO 3095 / 騒音規制法 / IEC 62236
homologationRecord              # L5c EN 50126/8/9 / 鉄道事業法 / FRA
silenRailReview                 # Council 5-of-7 Safe — new Wave / new trainset / new jurisdiction
```

### 8. Robotics Classes (R0 design-only reservation)

| Class | Role | Phase |
|---|---|---|
| **Tsugite (継手)** | Friction-Stir-Welding manipulator (Al 6N01 / A6005C carbody seams) | R1+ |
| **Wadasa (輪佐)** | Wheel set + bogie installation manipulator (≥2 t payload) | R1+ |
| **Toritsuke (取付)** | Interior + seating + HVAC fitting | R2+ |
| **Pantagora (パンタゴラ)** | Pantograph + high-voltage harness routing (R0 name placeholder) | R2+ |
| Otete-heavy | sarutahiko derivative reuse | R1+ |
| Mimi-precision | sarutahiko derivative reuse | R1+ |
| Akari | sarutahiko ECU/electrical reuse | R2+ |

### 9. Murakumo Placement (R0 design-only)

7-node fleet reuse: naphtali (L1 carbody) / zebulun (L3 interior) / joseph (L2 bogie) / simeon (L5a marriage) / dan (L5b dynamic test) / levi (L4 traction + cross emissions) / judah (L5c homologation + governance). No new node required.

### 10. 4-Phase Roadmap

| Phase | Scope | Trigger ADR |
|---|---|---|
| **R0** (this ADR) | Scaffold only; 9 cells RuntimeError; 9 lexicon stubs | 2605252600 |
| **R1** | Benchtop 1-car mockup + manual assembly + rail engineering SME + civil engineer SME | 2605252615 (reserved) |
| **R2** | Pilot 1 trainset (3-4 car EMU) ≤120 km/h commuter class + 30-day public comment | 2605252630 (reserved) |
| **R3** | Community-scale 8-16 car ≥1 trainset/month Shinkansen-class ≤320 km/h + 60-day public review + LANDS.md depot + test track (≥10 km) allocation | 2605252645 (reserved) |

## Consequences

**Positive:**
- Religious-corp gains a constitutionally-bounded design surface for rail vehicle manufacturing before capability lands.
- Sibling-pattern parity with sarutahiko (road) — together they cover the two civilian land-mobility manufacturing domains (track-bound + road-bound).
- §2(e) democratic-transit alignment: rail vehicles serve the §1.13 wellbecoming non-car-centric mobility goal more naturally than any other transport mode.
- ECU + ATP/ATO open-source mandate (G1 + N5) breaks proprietary signalling lock-in (CBTC / ETCS / Digital ATC), enabling cross-vendor interoperability per N12 anti-fragmentation.

**Negative / risks:**
- Rail manufacturing is capital-intensive (single trainset typically USD 30-50M); R3 community-scale ≥1 trainset/month requires LANDS.md amendment for depot + test track + multi-year capital cycle. Capital path deferred to R2 ADR.
- Track-side infrastructure (overhead line, signalling, civil works) is out of scope for yamabiko — partial dependency on tatekata (track-bed construction) + hikari (overhead line + substation) cross-actor coordination.
- Wave 1 BEMU + H₂ powertrain transition depends on hikari (renewable energy) cross-coverage; coordination gate declared in R2 ADR.
- N4 diesel locomotive sunset at R2+ is irreversible — religious-corp will never produce R2+ diesel locomotives; conventional rail Wave 2 must be BEMU-only.

**Open questions (deferred to R1):**
- Specific R1 mockup car size (multiple-unit head car vs trailing car)
- BEMU battery chemistry baseline (LFP vs sodium-ion vs solid-state)
- ATP signalling baseline (CBTC vs ETCS Level 2 vs Digital ATC) — must be open-source per G1
- Trainset-level vs car-level DID granularity for G13

## Alternatives Considered

1. **Carve as sarutahiko-Wave-4 rail subdomain**. Rejected: bogie + ATP + homologation regime are methodologically distinct from road. Independent Tier-B is correct.
2. **Defer until first downstream-actor demand**. Rejected: same gate-after-the-fact failure mode as watatsumi precedent.
3. **Single integrated mobility actor covering road + rail**. Rejected: phase models, witness invariants, and lexicons distinct.
4. **Adopt mass-transit-as-state-amplifier methodology directly**. Rejected: §2(d) state-violence amplifier risk. Wave 1 explicitly excludes border / police / riot control rail (N2).

## References

- ADR-2605192100 §1.12 — Transparent Religious Force
- ADR-2605192200 §2(a), §2(d), §2(g), §2(e), §1.13 — Charter Rider anchors
- ADR-2605242000 — wadachi (轍) autonomous mobility R0 (operator-side counterpart concept)
- ADR-2605252500 — sarutahiko (猿田彦) heavy truck manufacturing R0 (sibling pattern)
- ADR-2605252200 — watatsumi (綿津見) civilian submersible R0 (pattern source, §2(a) carve-out)
- ADR-2605252400 — kanayama (金山) circular metallurgy R0 (downstream Al/steel supply + EoL loop)
- ADR-2605250715 — tatekata (建方) construction R0 (track-bed cross-actor)
- EN 50126 / EN 50128 / EN 50129 — RAMS (G6 + L5c anchor)
- 日本鉄道事業法 — Japan Railway Business Act (homologation anchor)
- FRA Tier I-III — US Federal Railroad Administration (homologation anchor)
- ISO 3095 — Acoustics — Railway applications — Measurement of noise emitted by railbound vehicles (G8 anchor)
- IEC 62236 — Railway applications — Electromagnetic compatibility (G8 anchor)
- IEC 62290 — Railway applications — Urban guided transport management and command/control systems — GoA taxonomy (G12 anchor)
- YouTube `KFSPENlRdFU` — "Inside Giant Factory Building Super Modern High-Speed Trains From Scratch" (Wave 1 methodology source)
