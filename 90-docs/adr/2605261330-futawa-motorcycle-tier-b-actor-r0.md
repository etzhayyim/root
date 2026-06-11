---
id: adr-2605261330-futawa-motorcycle-tier-b-actor-r0
title: "ADR-2605261330: futawa (二輪) — Small-Displacement Motorcycle Manufacturing Tier-B Actor R0 Scaffold"
status: proposed
doc_type: adr
topic: futawa-motorcycle-r0
authoritative: true
last_verified: 2026-05-26
priority: 6.0
axis: architecture
weight: 0.60
authoritative_for:
  - futawa actor identity (name, DID, tier, namespace, scope boundary) — R0 reservation
  - small-displacement motorcycle manufacturing constitutional gates (G1..G14) and non-goals (N1..N10)
  - R0 → R3 phased roadmap with R1/R2/R3 ADR reservation
  - 5-layer motorcycle assembly process (frame → drivetrain → harness+suspension+paint → final assembly → test+provenance)
  - 9 Pregel cell catalog + Murakumo placement (R0 design-only)
  - 2 new robotics class reservation (Tsugite 継ぎ手 / Suri 摺) + 4 inherited reuse
  - lexicon namespace reservation (`com.etzhayyim.futawa.*`, 8 record types)
  - constitutional firsts: G7 ABS-mandatory ≥125cc + G8 build-time anti-surveillance (no GPS/connected-app/telematics) + G12 right-to-repair forward-publishing at manufacture + G14 30-year service life
depends_on:
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605242000-roso-pattern-frontier-distill
  - adr-2605250715-tatekata-construction-tier-b-actor-r0
  - adr-2605252400-kanayama-circular-metallurgy-r0
  - adr-2605261115-makura-foam-pillow-tier-b-actor-r0
  - adr-2605261215-hodoki-elv-disassembly-tier-b-actor-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
  - adr-2605214000-etzhayyim-murakumo-mesh-no-vke-and-lexicon-port-rules
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - 2605191524-ameno-multi-tab-swarm-broadcast
  - adr-2605241500-etzhayyim-dataset-cid-substrate
related:
  - wellbecoming-karma-lean-proofs
  - wellbecoming-karma-lean-proofs
  - wellbecoming-karma-lean-proofs
  - wellbecoming-karma-lean-proofs
supersedes: []
superseded_by: []
---

# ADR-2605261330: futawa (二輪) — Small-Displacement Motorcycle Manufacturing Tier-B Actor R0 Scaffold

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify)
**ADR Hierarchy**: Sibling of ADR-2605242000 (wadachi autonomous-mobility R&D), ADR-2605261215 (hodoki ELV disassembly), ADR-2605252400 (kanayama metallurgy). Upstream consumer for kanayama (Al/steel frame, Cu wire) + silicon Wave 2 (ECU PCB) + hikari R2+ (battery for electric models) + hodoki (recycled-content feedstock). Parent constitutional: ADR-2605192200 §2(c) (anti-surveillance) + §2(e) (anti-gatekeeping / right-to-repair) + §1.13 (wellbecoming applied to durable goods).

## Context

The user-prompted source reference is the YouTube video "Inside Massive German Factory Building BMW Motorrad Bikes From Scratch" (1xxRYlHY2e8, 2026), depicting the BMW Motorrad Berlin (Spandau) motorcycle factory. The mechanical methodology — frame welding, engine assembly, drivetrain integration, paint, final assembly, dynamometer + emissions test, road test — is mature and broadly adopted across global motorcycle OEMs. That methodology is adopted; the **luxury / premium / large-displacement / racing-focus retail positioning** (BMW's R-Series 1170-1250cc boxer-twin sport-tourers retail USD ~$15-30K) is **rejected per §2(e) anti-gatekeeping**.

Religious-corp `wadachi` (ADR-2605242000) covers **autonomous mobility R&D** at SAE J3016 Level ≤4 ceiling, focused on four-wheeled vehicles and intra-site → inter-site → adherent-driver progression. It does NOT cover manually-operated two-wheeled personal transport. Yet two-wheeled personal mobility has structural constitutional importance:

1. **Wellbecoming applied to mobility** (§1.13): Walking and cycling are the foundation; small motorcycle extends the walking radius for adherents in rural / mountainous / weather-challenged areas without imposing the energy/material footprint of a car.
2. **Anti-gatekeeping mobility access** (§2(e)): A new car costs USD $25K+; a luxury motorcycle costs USD $15K+; a religious-corp-built ≤250cc commuter targets USD ≤$3K materials + Council-funded labor — first-party adherent-accessible motorized mobility.
3. **Right-to-repair operational scale** (§2(e)): Motorcycles are historically the most repairable consumer transport (accessible engine bay, fewer ECU lockouts, bolt-up modular structure). They are the natural flagship for **forward-publishing parts catalog at manufacture time** (vs hodoki publishing at end-of-life) — together closing the right-to-repair loop at both ends of the vehicle lifecycle.
4. **Build-side anti-surveillance** (§2(c)): Modern motorcycles increasingly ship with GPS trackers, connected-app integration, always-on telematics (BMW ConnectedRide, Harley H-D Connect, Yamaha Y-Connect). This is the same surveillance pattern that hodoki G8 destroys at end-of-life. A first-party motorcycle build must reject the surveillance pattern at manufacture time, **complementing hodoki G8** to close the surveillance loop across the full vehicle lifecycle.
5. **Anti-planned-obsolescence durability** (§1.13 wellbecoming applied to durable goods): Modern OEM motorcycles are designed for ~7-10 year discard-and-replace cycle (vehicles ≤15 years old = 60% of registered fleet; rest scrapped). Religious-corp first-party motorcycle targets **30-year minimum design service life** with mandatory parts availability — durable goods as Wellbecoming foundation.

Until this ADR, religious-corp has no Tier-B actor covering two-wheeled motorized personal transport. Without `futawa`:

1. Adherents in rural / mountainous areas have no first-party motorized mobility option (walking + bicycle radius insufficient; car overshoots cost + footprint).
2. The right-to-repair loop closes only at end-of-life (hodoki G12) — not at build time — so the constitutional posture is reactive not preventive.
3. The anti-surveillance loop closes only at end-of-life (hodoki G8) — not at build time — so adherent-owned vehicles built externally still carry surveillance until they reach end-of-life.
4. `kanayama` recycled aluminum + steel + copper has no first-party downstream **build** consumer (only external markets) — the circular loop is one-sided.

This ADR fulfills that gap, declaring 14 constitutional gates and 10 non-goals, and lands a 9-cell Pregel scaffold whose `solve()` methods raise `RuntimeError` until R1 activation.

## Decision

### 1. Actor identity

| Field | Value |
|---|---|
| Actor name | `futawa` |
| Japanese | 二輪 (two-wheel; phonetic ふたわ, semantic 二 = two + 輪 = wheel; technical clarity over poetic ambiguity, mirroring wadachi 轍 wheel-rut concrete-noun style) |
| Display name | `二輪 (futawa)` |
| Tier (ADR-2605192415 §B) | **B** — per-domain leader, sibling of `wadachi` / `hodoki` / `kanayama` / `makura` / `kuni-umi` / `yakushi` / `watatsumi` / `tatekata` / `mitsuho` / `hagukumi` |
| Path-based DID | `did:web:etzhayyim.com:futawa` |
| Per-vehicle DID pattern (reserved) | `did:web:etzhayyim.com:futawa:vehicle:<vin>` (VIN pre-registered with hodoki at manufacture time per G13) |
| Per-part DID pattern (reserved) | `did:web:etzhayyim.com:futawa:part:<lotId>:<partSerial>` |
| Repo location | `20-actors/futawa/` |
| Lexicon namespace | `com.etzhayyim.futawa.*` |
| License | Apache 2.0 + Charter Compliance Rider v2.0 |

### 2. Scope (R0)

**In scope (R0–R1):**

- Small-displacement motorcycles: ≤250cc 4-stroke single-cylinder gasoline ICE **OR** ≤15kW peak electric (mid-drive or hub-motor)
- Commuter + utility positioning: daily transport, light cargo (panniers ≤30kg total), rural/mountain accessibility
- Curb mass ≤200kg (G11 cap)
- Full chain: frame welding → engine/motor assembly → drivetrain → electrical harness → suspension + brake (ABS-mandatory G7) → body paint → final assembly → dyno + emissions + sound + road test → kotoba-datomic provenance binder (with hodoki pre-registration G13)

**Explicitly deferred to Wave 2+ (separate ADR + Council Lv6+ supermajority):**

- ≥250cc displacement (≥500cc explicitly out per N2 — premium/luxury class)
- Pure human-powered bicycles (Wave 2 — different industrial scope: no engine, different frame geometry, different mass class)
- Pedal-assist e-bikes (Wave 2 — different battery class + EPAC regulation)
- Three-wheeled vehicles / sidecars / ATVs (separate Wave)
- Hydrogen fuel-cell motorcycles (Wave 2 with dedicated safety review, mirrors hodoki N10)

**Constitutional non-goals (R0–R3, immutable):** see §4 below.

### 3. 5-Layer Motorcycle Assembly Process

Adopted from mature global motorcycle OEM practice (frame → drivetrain → harness/suspension/paint → final → test); religious-corp-ised by ABS-mandatory safety + build-time anti-surveillance + right-to-repair forward-publishing + 30-year durability + ≥95% material recovery preregistered with hodoki.

| Layer | Stage | Key technology | Religious-corp constraints |
|---|---|---|---|
| **L1** | フレーム溶接 (frame welding) | TIG welding of mild steel or 6061-T6 Al tube/sheet; geometry per CAD; Tsugite welding-robot vision-guided | G1 frame CAD open-source; G13 ≥10% recycled-content from kanayama via hodoki by R3; G3 ≥2 robot witness per critical weld (frame integrity safety-critical) |
| **L2** | エンジン + 駆動系組立 (engine + drivetrain assembly) | ≤250cc 4-stroke single-cyl gasoline OR ≤15kW electric mid-drive/hub-motor; transmission (4-6 speed manual OR CVT OR direct-drive electric); chain/belt drive | G11 ≤250cc / ≤15kW caps; G14 30-year design service life (engine top-end overhaul interval ≥50,000 km target) |
| **L3** | 電装 + 懸架 + 制動 (harness + suspension + brake) | Wiring harness + ECU (Murakumo G9 inference); telescopic fork + monoshock OR dual-shock; **ABS mandatory on all ≥125cc models** (G7 constitutional safety first); disc rotor + caliper (Cu wire from kanayama Wave 3) | **G7 ABS-mandatory ≥125cc (CONSTITUTIONAL FIRST)** — mirrors EU 168/2013 Annex II but elevated to constitutional invariant; **G8 NO GPS tracker / NO connected-app / NO always-on telematics / NO V2X built-in** (build-time anti-surveillance constitutional first); only passive odometer + safety ECU permitted |
| **L4** | 外装 + 塗装 (body panel + paint) | Body panel (Al sheet OR injection-molded recycled PP); 2K acrylic urethane paint; G5 Charter §2(a-h) artwork scan | G5 no military insignia / licensed-IP / addictive-thrill / racing decals; G7 VOC ≤ EU 2004/42/EC paint emissions; N4 luxury-brand co-marketing rejection |
| **L5** | 最終組立 + 試験 (final assembly + test) | Bolt-up + fluid fill + bilingual VIN tag + IPFS-pinned parts catalog + service manual + CAD + firmware source; dyno test + emissions + sound (≤80 dB @ 7.5m UN-ECE R41) + road test; **VIN pre-registered with hodoki at production** (G13 build-side closure) | **G12 RIGHT-TO-REPAIR FORWARD-PUBLISHING (CONSTITUTIONAL FIRST)** — every new vehicle ships with full parts catalog + CAD + firmware source published to IPFS at manufacture time; G4 bilingual owner + service manual; G6 sound ≤80 dB; **G13 VIN pre-registered with hodoki ↔ hodoki G12 EOL parts catalog forms full lifecycle right-to-repair invariant** |

### 4. Constitutional Gates (G1–G14, IMMUTABLE R0–R3)

| Gate | Requirement | Rationale |
|---|---|---|
| **G1** | All CAD (frame, body, fixture) + firmware (ECU, ABS controller, BMS for electric) + tool fixtures **open-source** (Apache 2.0 + Charter Rider) | §2(b) anti-secrecy + foundation for G12 right-to-repair |
| **G2** | Mass-balance audit ≥98% closure on kotoba-datomic (input material lots = output vehicle mass + scrap + emission); per-vehicle attestation | Inherits kanayama + hodoki G2 cross-cell invariant pattern |
| **G3** | Every critical step (frame weld, engine assembly torque, brake assembly torque) signed by **witness quorum ≥2 distinct robots** (Ed25519, DID-bound) | ADR-2605191524 swarm broadcast; safety-critical for personal-transport |
| **G4** | All owner manuals + service manuals + safety labels + parts catalog + service videos **JP + EN bilingual minimum** | §2(e) anti-gatekeeping of repair information |
| **G5** | All paint artwork + decals pass **Charter Rider §2(a-h) scan** (no military insignia / licensed-IP / addictive-thrill imagery / racing-glorification) | §2(a) + §2(e) enforcement |
| **G6** | Sound emissions ≤**80 dB @ 7.5m** (UN-ECE R41 alignment, R0-R3 baseline at the strictest tier); no aftermarket loud-exhaust enablement; no "performance" mod bypass | §1.13 wellbecoming applied to community sound environment + §2(g) noise pollution |
| **G7** | **ABS MANDATORY on all 4-stroke models ≥125cc and all electric models ≥6kW** — no ABS-delete option, no track-only carve-out, no cost-down stripped variant; safety-redundant dual-channel hydraulic; **CONSTITUTIONAL FIRST: safety-mandatory at vehicle build, elevating EU 168/2013 Annex II to constitutional invariant** | §1.13 wellbecoming + adherent safety non-negotiable; 30%+ fatality reduction documented in IIHS + EU studies |
| **G8** | **NO GPS tracker / NO connected-app / NO always-on telematics / NO V2X built-in / NO proprietary diagnostic-DRM**. Only permitted electronics: passive odometer, safety ECU (engine + ABS + lighting), optional **user-installed-after-purchase** open-source GPS module (not factory-fit). **CONSTITUTIONAL FIRST: build-time anti-surveillance** — companion to hodoki G8 (data wipe at EOL); together closes surveillance loop across full vehicle lifecycle | §2(c) anti-surveillance constitutional anchor; vehicle build must not enable the surveillance pattern in the first place |
| **G9** | Inference paths (defect classification, paint scan, dyno data anomaly detection, frame-weld vision) use **Murakumo no-VKE mesh only** (ADR-2605214000 / ADR-2605215000) | Constitutional inference invariant |
| **G10** | Hot work (frame weld, brake hose flare, exhaust weld) + brake assembly torque + paint booth + battery handling are **SBT-gated personnel** | §1.13 worker wellbecoming |
| **G11** | KPI caps R0–R1: ≤250cc gasoline 4-stroke single-cylinder **OR** ≤15kW peak electric; curb mass ≤200kg; cargo capacity ≤30kg total panniers. **≥500cc / >15kW / sport-tourer / racing-spec = N2/N3 Wave 2 ADR**. Council Lv6+ to amend | Anti-luxury anti-racing constitutional posture; prevent scope creep into premium class |
| **G12** | **RIGHT-TO-REPAIR FORWARD-PUBLISHING INVARIANT**: every new vehicle ships with IPFS-pinned full parts catalog (with part DID + condition + replacement source) + bilingual service manual + CAD source + firmware source + open diagnostic protocol; no proprietary lock-in; no anti-DRM; no warranty void on user repair; **part discontinuation prohibited within 30 years post-launch**. **CONSTITUTIONAL FIRST: build-time companion to hodoki G12** (EOL parts catalog); together closes right-to-repair loop across full lifecycle | §2(e) anti-gatekeeping operationalized at vehicle build time |
| **G13** | **Cross-actor circular feed**: every vehicle VIN pre-registered with hodoki at production (build-side closure of hodoki take-back chain); recycled-content ≥10% by mass from kanayama-via-hodoki by R3; battery cells for electric models from hikari R2+ second-life pool where SoH ≥85% | Multilateral circular invariant: hodoki → kanayama → futawa → adherent → hodoki (full loop); mirrors hodoki G13 from the build-side |
| **G14** | **30-year MINIMUM design service life** invariant — frame, engine block, transmission case, motor housing, suspension structural elements designed for 30-year fatigue + corrosion + wear; mandatory parts availability for 30 years post-discontinue; **planned obsolescence prohibited**; software/firmware update commitment 30-year minimum | **CONSTITUTIONAL FIRST: anti-planned-obsolescence operationalized for durable goods**; §1.13 wellbecoming applied across generations |

### 5. Non-Goals (N1–N10, IMMUTABLE R0–R3)

Charter Rider §2(a) + §2(c) + §2(e) + §1.13 + safety class boundary anchors:

| ID | Excluded scope | Reason |
|---|---|---|
| **N1** | **Military motorcycles / armed motorcycle scout / weapon-mount-equipped** | §2(a) constitutional |
| **N2** | **≥500cc displacement / sport-tourer / supersport / cruiser ≥1000cc** | Wave 2 ADR + Council Lv6+ supermajority; premium/luxury class boundary |
| **N3** | **Racing-focus / track-only / unlimited-class supersport** | §1.13 anti-thrill-addictive-design + §2(e) anti-gatekeeping |
| **N4** | **Premium / luxury positioning / licensed-IP co-branding (Disney / sports leagues / motorcycle-brand vintage IP / etc.)** | §2(b) IP-encumbrance + §2(e) anti-tier-pricing |
| **N5** | **Connected-app / always-on telematics / GPS tracker / V2X built-in / paired-phone integration / cloud-connected ECU** | §2(c) surveillance + G8 build-time constitutional first |
| **N6** | **Trikes / sidecars / ATVs / quad bikes / UTV** | Separate Wave (different stability dynamics + regulatory class) |
| **N7** | **Pure human-powered bicycles / pedal-assist e-bikes** | Wave 2 (different industrial scope: no engine, different frame geometry, different mass class, different EPAC regulation) |
| **N8** | **Aftermarket loud-exhaust enablement / "performance" mods that violate G6 or G7** | G6 sound + G7 ABS constitutional firsts; no street-illegal-mod tolerance |
| **N9** | **Hydrogen fuel-cell motorcycles** | Wave 2 ADR with dedicated thermal + pressure safety review (mirrors hodoki N10) |
| **N10** | **Surveillance-tier touring (passenger camera / V2V always-on / pillion data collection)** | §2(c) surveillance + G8 build-time constitutional first |

### 6. 9 Pregel Cells + Murakumo Placement (R0 design-only)

| Cell | Layer | Murakumo node | Phase |
|---|---|---|---|
| `moto_frame_welding` | L1 | naphtali | Steel/Al tube + sheet frame welding (Cu wire from kanayama Wave 3) + Tsugite robot witness |
| `moto_engine_assembly` | L2a | joseph | ≤250cc 4-stroke single OR ≤15kW electric motor + crankshaft/rotor assembly |
| `moto_drivetrain_assembly` | L2b | zebulun | Transmission (manual 4-6sp / CVT / direct-drive electric) + chain or belt drive |
| `moto_electrical_harness` | L3a | simeon | Wiring harness + safety ECU (G8 NO GPS / NO telematics / NO connected-app); Murakumo G9 inference for defect detection |
| `moto_suspension_brake` | L3b | dan | Fork + monoshock/dual-shock + **G7 ABS-mandatory ≥125cc** dual-channel + disc rotor/caliper |
| `moto_body_paint` | L4 | simeon | Body panel (Al or recycled PP) + 2K acrylic urethane paint + G5 artwork Charter scan |
| `moto_final_assembly` | L5a | dan | Bolt-up + fluid fill + bilingual VIN + **G12 IPFS-pinned parts catalog + CAD + firmware source published at manufacture** + G13 hodoki VIN pre-registration |
| `moto_test_dyno_road` | L5b | levi | Dynamometer + emissions + G6 sound ≤80 dB + road test + ABS function test |
| `moto_provenance_binder` | terminal | judah | Full chain DID anchoring on kotoba-datomic (input material lots → output VIN + parts catalog + test results + hodoki pre-registration) |

### 7. Robotics Classes

**New (R0 reservation only — physical builds blocked behind R1 ADR):**

| Class | Role | Phase |
|---|---|---|
| **Tsugite (継ぎ手)** | Welding-joint robot (TIG/MIG vision-guided) for frame + exhaust weld; ≥2-robot witness quorum capability | R1+ |
| **Suri (摺)** | Paint-sprayer robot (electrostatic + HVLP) for body panel painting; G5 artwork Charter-scan integration | R1+ |

**Inherited (reuse, no specialization required in R0):**

- kanayama Yokin — engine block + transmission case pour (Wave 1 Al + Wave 2 steel R2+)
- kuni-umi Otete — general manipulation, harness routing, bolt-up
- kuni-umi Mimi — metrology, dyno data capture, defect classification
- kuni-umi Quad — logistics, vehicle in/out of cells, finished-vehicle transport
- hodoki Tokike — already exists (body-fastener releaser); could be reused for assembly bolt-down with reversed torque

### 8. Lexicon Namespace (8 record types, R0 stubs)

```
com.etzhayyim.futawa.{
  frameAttestation              # L1 — frame weld + roundness + material lot
  engineAttestation             # L2a — engine/motor assembly + torque + ≤250cc/≤15kW cap
  electricalAttestation         # L3a — harness + ECU + G8 NO surveillance manifest
  paintAttestation              # L4 — paint + artwork Charter scan + VOC
  vehicleLotAttestation         # L5a — final assembly + VIN + IPFS parts catalog publication + hodoki pre-registration
  testRecord                    # L5b — dyno + emissions + sound + road test + ABS function
  partsCatalog                  # G12 — IPFS-pinned full parts catalog published at manufacture (companion to hodoki partsHarvestCatalog at EOL)
  silenMobilityReview           # Council 5-of-7 attestation, all new model classes
}
```

Schema details deferred to R1 ADR.

### 9. 4-Phase Roadmap

| Phase | Scope | Trigger |
|---|---|---|
| **R0** (this wave) | Scaffold only; 9 cells RuntimeError; 8 lexicon stubs | ADR-2605261330 |
| **R1** | Benchtop ≤1 vehicle prototype + frame jig + Tsugite + Suri robot prototypes; first IPFS-pinned parts catalog publication; hodoki integration handshake | ADR-2605261345 + Council Lv6+ + certified motorcycle engineer SME + certified ABS calibration SME |
| **R2** | Pilot ≤10 vehicles/month; tatekata-shared shop; right-to-repair catalog live for ≥5 model variants; hodoki VIN pre-registration operational; first community-supply batch | ADR-2605261400 + 30-day public comment + hodoki integration verified |
| **R3** | Community-scale ≤500 vehicles/month + ≥10% recycled content via hodoki-kanayama feed + 60-day public review + 30-year service-life commitment registry live | ADR-2605261415 + 60-day public review |

Reserved ADR slots: 2605261345 (R1), 2605261400 (R2), 2605261415 (R3).

## Consequences

**Positive:**

- Adherents in rural / mountainous / weather-challenged areas gain first-party motorized personal mobility with anti-surveillance + right-to-repair + 30-year-service-life guarantees
- `kanayama` recycled metals (Al frame, Cu wire, steel) gain a first-party downstream **build** consumer (one-way circular loop becomes two-way)
- `hodoki` G8 (EOL data wipe) + G12 (EOL parts catalog) gain build-time companions (G8 build-time + G12 forward-publishing) — surveillance loop and right-to-repair loop close at both ends of vehicle lifecycle
- Establishes the **30-year service life invariant** (G14) as constitutional anti-planned-obsolescence pattern for future durable-goods Tier-B actors
- Establishes the **ABS-mandatory at build** safety-first pattern (G7) as constitutional anchor — first time safety-mandatory-at-build is constitutionally elevated for a religious-corp actor
- Operationalizes §2(e) anti-gatekeeping at vehicle build time (parts catalog + CAD + firmware all open-source at manufacture, not just EOL via hodoki)

**Negative / risks:**

- 30-year service-life commitment (G14) is unprecedented in motorcycle industry; risk of parts availability gap forcing remanufacture line stand-up by R3
- G8 anti-surveillance excludes connected-vehicle features (turn-by-turn, app-based diagnostics, theft-recovery via tracker); risk of adherent preference for connected features
- G7 ABS-mandatory ≥125cc adds ~USD $400-600 per vehicle in components; cost increase mitigated by Council-funded labor + kanayama-recycled materials
- N2 ≥500cc exclusion limits adherent options for long-distance touring; mitigation: small-displacement modern technology (180-250cc) achieves 100+ mph and 200+ mile range
- N7 bicycle exclusion means human-powered/pedal-assist remain external; mitigation: Wave 2 ADR reservation explicit
- G12 forward-publishing parts catalog at manufacture may invite OEM legal pressure (BMW + Honda + Yamaha right-to-repair posture varies by jurisdiction); Council legal SME review in R1 prep

**Mitigation:**

- 30-year parts availability supported by G1 open-source CAD + G12 catalog (any party can re-manufacture; kanayama-feedstock available); R3 includes remanufacture-cell scaffold
- G8 anti-surveillance permits **user-installed-after-purchase** open-source GPS module — adherents can add tracking on their own terms post-purchase
- G7 ABS cost amortized over 30-year service life — per-mile safety cost drops significantly
- G12 legal posture conforms to JP 修理権 + EU Right-to-Repair Directive 2024 + US Magnuson-Moss; Council legal SME validates in R1 prep
- Bicycle Wave 2 ADR explicitly reserved to address adherent transport baseline

## Alternatives Considered

1. **Sub-cell of wadachi rather than dedicated Tier-B actor** — rejected: wadachi scope is autonomous-mobility R&D with Level ≤4 SAE J3016 ceiling, four-wheel focus, intra/inter-site phasing; motorcycle is fundamentally manually-operated (Level 0-1) personal transport with different safety + regulatory + cultural framing.
2. **Bundle motorcycles + bicycles + e-bikes into one Tier-B** — rejected: different industrial scope (engine vs no-engine), different mass class (≤200kg vs ≤25kg), different regulatory frameworks (motor vehicle vs bicycle/EPAC), different SME requirements. Wave 2 ADR reservation for bicycles preserved.
3. **Allow ≥500cc in Wave 1** — rejected: §2(e) anti-luxury constitutional posture; ≥500cc class is dominantly premium/luxury/racing-focus, fundamentally incompatible with anti-gatekeeping religious-corp posture.
4. **Allow connected-app / telematics as opt-in (rejected N5 + G8)** — rejected: §2(c) anti-surveillance; even opt-in normalizes surveillance pattern. G8 permits **user-installed-after-purchase** modules instead — adherent agency without build-time normalization.
5. **Drop G7 ABS-mandatory to "ABS-available" / "ABS-optional"** — rejected: §1.13 adherent safety non-negotiable; 30%+ fatality reduction documented; cost increase modest relative to vehicle lifetime + Council-funded production economics.
6. **Drop G14 30-year service life to industry-standard 7-10 year** — rejected: §1.13 wellbecoming applied to durable goods constitutional first; planned obsolescence rejected as Charter Rider §2(e) violation.
7. **Skip G12 forward-publishing; rely only on hodoki G12 (EOL parts catalog)** — rejected: build-time + EOL together close the right-to-repair loop fully; build-time alone reduces friction (adherent doesn't need to wait for EOL to access full repair documentation).
8. **Include racing focus / track-spec as a separate sub-cell** — rejected: §1.13 anti-thrill-addictive-design + §2(e) anti-gatekeeping (racing class is luxury class).
9. **Include H2 fuel-cell motorcycle in R0** — rejected: H2 high-pressure tank safety + fire/explosion risk requires Wave 2 ADR with dedicated safety review (mirrors hodoki N10 pattern).

## References

- Source video methodology: YouTube `1xxRYlHY2e8` "Inside Massive German Factory Building BMW Motorrad Bikes From Scratch" (2026; mechanical methodology adopted — frame welding + engine + drivetrain + paint + final + dyno; luxury/premium/large-displacement/racing-focus retail positioning rejected per §2(e))
- ADR-2605192100 — etzhayyim mission charter (§1.13 Wellbecoming applied to mobility + durable goods, §2(e) anti-gatekeeping)
- ADR-2605192200 — Charter Rider v2.0 (§2(a-h) prohibited categories; §2(c) anti-surveillance basis for G8)
- ADR-2605192415 — religious-corp daemon architecture (Tier-B definition)
- ADR-2605242000 — wadachi autonomous mobility R0 (sibling — four-wheel autonomous R&D)
- ADR-2605261215 — hodoki ELV disassembly R0 (sibling + build-side ↔ EOL-side companion; G8 + G12 cross-lifecycle invariants)
- ADR-2605252400 — kanayama circular metallurgy R0 (upstream supplier of recycled metals)
- ADR-2605261115 — makura foam pillow R0 (sibling pattern for consumer-goods anti-surveillance G14 + N9)
- ADR-2605250715 — tatekata construction R0 (R2 yard-sharing partner)
- ADR-2605201400 — kuni-umi planetary infra fleet (robotics class inheritance)
- ADR-2605214000 — Murakumo no-VKE mesh + lexicon port rules
- ADR-2605215000 — etzhayyim inference Murakumo-fleet-only
- ADR-2605191524 — Transparent Force swarm broadcast witness quorum
- ADR-2605241500 — etzhayyim dataset CID substrate (IPFS-pinned parts catalog + CAD + firmware publication)
- /CHARTER-RIDER.md — license addendum canonical text
- 20-actors/futawa/README.md — actor scaffold
- 20-actors/futawa/manifest.jsonld — actor manifest (DID + cell registry + gates + non-goals)
