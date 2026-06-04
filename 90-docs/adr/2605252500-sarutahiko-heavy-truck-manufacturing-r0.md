---
id: adr-2605252500-sarutahiko-heavy-truck-manufacturing-r0
title: "ADR-2605252500: sarutahiko (猿田彦) — Heavy Truck Manufacturing Tier-B Actor R0 Scaffold (Wave 1 reference = civilian Class-8 cargo truck)"
status: proposed
doc_type: adr
topic: sarutahiko-heavy-truck-manufacturing-r0
authoritative: true
last_verified: 2026-05-25
priority: 6.0
axis: architecture
weight: 0.60
authoritative_for:
  - sarutahiko actor identity (name, DID, tier, namespace, scope boundary) — R0 reservation
  - heavy truck manufacturing constitutional gates (G1..G14) and non-goals (N1..N12)
  - R0 → R3 phased roadmap with R1/R2/R3 ADR reservation
  - Wave 1 = civilian Class-8 cargo truck (~26-40t GVWR) reference fix
  - Wave 2-3 deferred (mid/light commercial / specialty civilian vehicles) carve-out reservation
  - 5-layer assembly process (frame → powertrain → cab → marriage → paint+electrical+QA)
  - 9 Pregel cell catalog + Murakumo placement (R0 design-only)
  - 4 new robotics class reservation (Kasane / Tsutsumi / Akari / Norimichi) + 3 inherited (Otete-heavy / Mimi-precision / Migaki)
  - lexicon namespace reservation (`com.etzhayyim.sarutahiko.*`, 9 record types)
  - manufacturing-side counterpart positioning to wadachi (operator-side autonomous mobility)
depends_on:
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605242000-roso-pattern-frontier-distill
  - adr-2605250500-yakushi-pharmaceutical-rd-charter
  - adr-2605250715-tatekata-construction-tier-b-actor-r0
  - adr-2605252200-watatsumi-civilian-submersible-r0
  - adr-2605252400-kanayama-circular-metallurgy-r0
  - adr-2605242500-baien-ternary-silicon-and-tsukuru-fab-charter
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192315-etzhayyim-transparent-force-rd
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
  - adr-2605214000-etzhayyim-murakumo-mesh-no-vke-and-lexicon-port-rules
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - 2605191524-ameno-multi-tab-swarm-broadcast
related:
  - wellbecoming-karma-lean-proofs
  - wellbecoming-karma-lean-proofs
  - wellbecoming-karma-lean-proofs
  - wellbecoming-karma-lean-proofs
supersedes: []
superseded_by: []
---

# ADR-2605252500: sarutahiko (猿田彦) — Heavy Truck Manufacturing Tier-B Actor R0 Scaffold

**Status**: proposed
**Date**: 2026-05-25
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify)
**ADR Hierarchy**: Sibling of ADR-2605252200 (watatsumi 水), ADR-2605252400 (kanayama 金), ADR-2605250715 (tatekata 土), ADR-2605242000 (wadachi 陸 operator-side), ADR-2605250500 (yakushi 薬), ADR-2605242500 (silicon 半導体). Parent constitutional: ADR-2605192100 §1.12 (Transparent Force) + ADR-2605192200 §2(a)/§2(g)/§2(h).

## Context

Modern large-scale heavy-truck assembly plant practice — Ford Otosan F-MAX / Mercedes-Benz Türk Aksaray / MAN Türkiye Ankara / BMC İzmir / DAF Eindhoven / Iveco Suzzara — has matured into a **modular line architecture** with well-defined sub-line + main-line + paint + QA stages. The methodology generalises across heavy / medium / light commercial vehicles (Class 8 down to Class 3) and is **technologically neutral**: it underpins both civilian cargo logistics (Charter Rider pro-clearance per §2(g) infrastructure + §2(e) anti-gatekeeping over OEM duopoly) and military / mining / weapons-platform applications (Charter Rider §2(a) and §2(g) explicit prohibitions).

Until this ADR, religious-corp has `wadachi` (ADR-2605242000) covering **operator-side** autonomous mobility (route planning, motion control, obstacle avoidance, telemetry — software + light hardware integration) but **no Tier-B actor covering vehicle manufacturing itself**. The gap leaves religious-corp dependent on opaque vendor-supplied trucks for every downstream actor (tatekata material delivery, kanayama UBC + scrap logistics, yakushi cold-chain shipment, mitsuho food distribution, kuni-umi site logistics). Without a manufacturing-side actor:

1. Vehicle ECU + powertrain firmware remains a closed proprietary stack (§2(b) violation in every supply contract).
2. Vehicle EoL recyclability cannot be guaranteed at design time, breaking kanayama Wave 2 (steel) + Wave 3 (copper) feedstock closure.
3. Fossil-fuel powertrain commitments are made by external OEMs without §2(g) sunset gates.
4. The methodology must be **civilianised** before capability lands, mirroring the watatsumi (submersibles) and kanayama (recycling) precedents — gate-after-the-fact loses meaning.

This ADR fulfills that gap by reserving `sarutahiko` as a Tier-B actor whose **constitutional posture is mixed-favorable**: §2(g) infrastructure-enablement positive for civilian cargo, but §2(a) heavy carve-out required against military / mining / weapons-platform applications (12 non-goals, matching watatsumi's submersible-specific count rather than kanayama's recycling-aligned 8).

The user-prompted source reference for this design is the manufacturing methodology survey in YouTube video `8XmI2MnAgWQ` ("How Turkey Produces Powerful Trucks Inside Massive Factory") — methodology adopted, military / mining / weapons-platform applications rejected per §2(a) + §2(g).

## Decision

### 1. Actor identity

| Field | Value |
|---|---|
| Actor name | `sarutahiko` |
| Japanese | 猿田彦 / さるたひこ (Shinto kami of roads, crossroads, paths; 道祖神 / dosojin lineage; the kami who guides Ninigi-no-Mikoto in the 天孫降臨 descent — directly applicable to vehicles guiding humans on roads) |
| Display name | `猿田彦 (sarutahiko)` |
| Tier (ADR-2605192415 §B) | **B** — per-domain leader, sibling of watatsumi / kanayama / tatekata / wadachi / yakushi / silicon / kuni-umi |
| Path-based DID | `did:web:etzhayyim.com:sarutahiko` |
| Per-vehicle DID pattern (reserved) | `did:web:etzhayyim.com:sarutahiko:vehicle:<vin>` |
| Per-line-station DID pattern (reserved) | `did:web:etzhayyim.com:sarutahiko:line:<plantCode>:<stationCode>` |
| Repo location | `20-actors/sarutahiko/` |
| Lexicon namespace | `com.etzhayyim.sarutahiko.*` |
| License | Apache 2.0 + Charter Compliance Rider v2.0 |

### 2. Positioning vs wadachi

`sarutahiko` is the **manufacturing-side counterpart** of `wadachi` (operator-side autonomous mobility, ADR-2605242000). The two share the SAE J3016 Level ≤4 ceiling (wadachi G7 echoed as sarutahiko G12), but their phase models, witness invariants, and lexicon namespaces are domain-distinct:

| Concern | wadachi (轍) | sarutahiko (猿田彦) |
|---|---|---|
| Domain | Operator (route + motion + safety + telemetry) | Manufacturer (frame + powertrain + cab + assembly + paint + QA) |
| Witness invariant | Robot route signing | Robot weld/marriage/paint witness |
| Output | `missionCompleteRecord` per trip | `vehicleManufactureRecord` per VIN |
| Cells | 5 (route/motion/obstacle/safety/telemetry) | 9 (frame/powertrain/cab/marriage/paint/electrical/road-test/emissions/VIN) |

A vehicle produced by sarutahiko is **operated** under wadachi's constitutional gates; a vehicle operated under wadachi is **manufactured** under sarutahiko's. The actors are siblings, not nested.

### 3. Scope (R0)

**Wave 1 reference (R0–R3 in scope)**: Civilian Class-8 cargo truck (~26-40 t GVWR, 6×2 / 6×4 drive). End-to-end: chassis frame fabrication → powertrain assembly → cab body forming + welding → final marriage → paint + interior + electrical → quality + road test → VIN attestation. Wave 1 powertrain accepts R0/R1 transition fuels (B100 biodiesel + diesel hybrid); R2+ requires LFP battery + H₂ / NH₃ / methanol fuel-cell only (G7).

**Wave 2-3 (deferred to separate ADRs, Council Lv6+ activation)**:
- Wave 2: Mid + light commercial (Class 3-7, ~3.5-7.5 t GVWR)
- Wave 3: Civilian specialty vehicles (fire engine + ambulance + cold-chain refrigerated logistics — §1.13 wellbecoming positive)

**Constitutional non-goals (R0–R3, immutable per Wave 1):** see §5 below.

### 4. 5-Layer Assembly Process

Adopted from large-scale heavy-truck plant practice (Turkey OEM class).

| Layer | Stage | Wave 1 (Class-8 cargo) key technology |
|---|---|---|
| **L1** | Frame fabrication | HSLA-590 / HSLA-780 high-strength low-alloy steel longitudinal rails + cross-members; robotic MIG / MAG welding; ladder-frame straightness < 1 mm/m |
| **L2** | Powertrain assembly (sub-line) | Engine (R0/R1: B100 biodiesel + diesel hybrid; R2+: LFP / H₂ / NH₃ / methanol fuel-cell) + transmission + drive axles + brake integration |
| **L3** | Cab body forming + welding | Steel sheet (sourced from kanayama Wave 2 steel coil when available; Wave 1 R0–R2 external commodity-steel acceptable) → hot stamping → robotic spot welding → leak test |
| **L4** | Final marriage | Chassis lowering + cab drop + powertrain mount + electrical harness connection; ≥2 robot witness on critical fastener torque |
| **L5** | Paint + interior + electrical + QA + road test + VIN attestation | KTL primer + base coat + clear coat (water-based, VOC < 100 g/L); interior trim; ECU flash (open-source firmware per G1); roller dynamometer + 50 km public-road test; VIN kotoba-datomic anchor |

### 5. Constitutional Gates (G1–G14, IMMUTABLE R0–R3)

| Gate | Requirement | Rationale |
|---|---|---|
| **G1** | ECU + all electrical firmware **open-source** (Apache 2.0 + Charter Rider) | §2(b) anti-secrecy; Transparent Force |
| **G2** | Per-VIN manufacturing log **kotoba-datomic anchor** + open VIN registry | §1.12.B Transparent + open accountability |
| **G3** | Per-VIN **IPFS-pinned photo + video** (frame welding, paint, road test) | Audit trail |
| **G4** | Every critical weld + final marriage signed by witness quorum ≥2 robots (Ed25519, DID-bound) | ADR-2605191524 swarm broadcast |
| **G5** | Operator manual + service manual **JP + EN bilingual minimum** + open-source | §2(e) anti-gatekeeping |
| **G6** | All CAD + firmware pass **Charter Rider §2(a-h) scan** | §2 enforcement |
| **G7** | **R0/R1 transition: B100 biodiesel + diesel hybrid acceptable. R2+ only: LFP battery / H₂ / NH₃ / methanol fuel-cell.** Pure-fossil powertrain phased out at R2 gate. | §2(g) fossil sunset |
| **G8** | Emissions ≤ **Euro 7 + 日本 ポスト新長期 + Bharat Stage VI** (R0-R1); R2+ zero tailpipe emission | §2(g) air quality |
| **G9** | CAD only from **vendor-free tools** (FreeCAD / OpenSCAD / Open CASCADE) | §2(b) anti-proprietary lock-in |
| **G10** | Inference paths via **Murakumo no-VKE mesh only** | ADR-2605214000 / ADR-2605215000 |
| **G11** | Paint booth + welding zone + hot work = **SBT-gated personnel** + 1 SBT = 1 vote council review for non-SBT visitors | §1.12 transparent; safety |
| **G12** | **KPI caps**: Wave 1 GVWR ≤40 t / max speed ≤90 km/h civilian / range ≥800 km / **autonomous operation ≤ SAE J3016 Level 4** (Level 5 = constitutional non-goal, wadachi G7 echo) | Self-imposed scope discipline |
| **G13** | Per-VIN **DID** (`did:web:etzhayyim.com:sarutahiko:vehicle:<vin>`) + per-vehicle key | §1.12.B traceability |
| **G14** | **EoL recyclability ≥90% by mass** (Wave 1 Al body + Wave 2 steel frame + Wave 3 copper interconnect close back to kanayama) + interior §2(h) waste tracking | §2(h) circular |

### 6. Non-Goals (N1–N12, IMMUTABLE R0–R3)

`sarutahiko` carries 12 non-goals — matching watatsumi's count rather than kanayama's smaller 8. The reason is heavy-truck domain dual-use exposure is closer to submersibles (high §2(a) + §2(d) + §2(g) risk surface) than to aluminum recycling (positively-aligned by design).

| # | Non-Goal | Constitutional anchor |
|---|---|---|
| **N1** | **Military trucks** (4×4 / 6×6 troop carriers, MRAP, armored vehicles, mil-spec 6×6, military reconnaissance vehicles) | §2(a) weapons platform |
| **N2** | **Weapons + ammunition transport** (ammunition trucks, missile / torpedo transporter, ICBM TEL, mil-spec field artillery prime mover) | §2(a) |
| **N3** | **Riot control / water-cannon / armored police vehicles** | §2(d) state-violence amplifier |
| **N4** | **Mining haul trucks** (rigid frame haul trucks for coal / iron ore / bauxite / oil-sand extraction) | §2(g) habitat + kanayama N1 echo |
| **N5** | **Fossil fuel tankers** (gasoline / diesel / LNG bulk transport). Bio-fuel + water + food tankers remain in scope. | §2(g) fossil diffusion |
| **N6** | **Military surveillance vehicles** (ELINT, SIGINT, military lidar swarm carriers) | §2(d) covert |
| **N7** | **Fully autonomous unmanned military platforms** | §2(a) + N1 echo |
| **N8** | **Proprietary ECU under NDA / non-disclosure** | §2(b) anti-secrecy |
| **N9** | **Driver-suppression UX** (biometric driver monitoring with data sale, driver behavior conditioning beyond safety-critical alerts) | §2(d) §2(h) wellbecoming |
| **N10** | **Pure-fossil-only powertrain at R2+** (R0/R1 transition window only; LFP / H₂ / NH₃ / methanol fuel-cell mandatory from R2) | §2(g) + G7 |
| **N11** | **Mobile billboard / LED advertising trucks** | §2(c) anti-advertising |
| **N12** | **For-profit MaaS rental fleets**. Non-profit member delivery + community logistics remain in scope. | §2(b) anti-rent-extraction |

### 7. Pregel Cell Catalog (9 cells, R0 = import-time RuntimeError)

| Cell | Stage | Murakumo node | Input | Output |
|---|---|---|---|---|
| `frame_fabrication` | L1 | naphtali | `steelLot`, `frameSpec` | `frameAttestation` |
| `powertrain_assembly` | L2 | joseph | `engineLot`, `transmissionLot`, `axleLot` | `powertrainAttestation` |
| `cab_body_forming` | L3 | zebulun | kanayama coil + steel sheet | `cabBodyAttestation` |
| `final_marriage` | L4 | simeon | frame + cab + powertrain attestations | `marriageAttestation` |
| `paint_finishing` | L5a | simeon | `marriageAttestation` | `paintAttestation` |
| `electrical_integration` | L5b | levi | `paintAttestation` + harness + ECU | `electricalAttestation` |
| `quality_road_test` | L5c | levi | `electricalAttestation` + dyno + 50 km road | `roadTestRecord` |
| `emissions_audit` | cross-cutting | levi | continuous telemetry | `emissionsAuditRecord` |
| `vin_attestation_binder` | terminal | judah | all prior + VIN | `vehicleManufactureRecord` (kotoba-datomic anchor) |

R0 contract: each cell module imports cleanly; instantiating its class succeeds; calling `.solve()` raises `RuntimeError("sarutahiko R0 scaffold: activate via Council ADR-2605252515 post-ratification")`.

### 8. Lexicons (9 record types under `com.etzhayyim.sarutahiko.*`, R0 stubs)

```
frameAttestation              # L1 chassis frame + steel lot + straightness
powertrainAttestation         # L2 engine + transmission + axle + G7 fuel check
cabBodyAttestation            # L3 cab forming + spot weld + leak test
marriageAttestation           # L4 final assembly + ≥2 robot witness
paintAttestation              # L5a paint + VOC + KTL film
electricalAttestation         # L5b harness + ECU firmware CID + diagnostics
roadTestRecord                # L5c roller dyno + public-road test
emissionsAuditRecord          # cross-cutting Euro 7 / 大気汚染防止法 / Bharat VI
silenVehicleReview            # Council 5-of-7 Safe attestation for new Wave / new type / G7 fuel transition
```

Plus terminal `vehicleManufactureRecord` aggregates all the above and anchors to kotoba-datomic via `vin_attestation_binder`. R0 ships stub JSON; schema details deferred to R1 ADR.

### 9. Robotics Classes (R0 design-only reservation)

| Class | Role | Phase | Inheritance |
|---|---|---|---|
| **Kasane (重ね)** | Frame + chassis lay-up MIG/MAG welding manipulator (HSLA-590/780 thick plate, multi-pass) | R1+ | new |
| **Tsutsumi (包み)** | Cab body paint booth robot (water-based KTL + base + clear, VOC <100 g/L) | R2+ | new |
| **Akari (灯り)** | Electrical harness routing + ECU flash + diagnostics binding | R1+ | new |
| **Norimichi (乗道)** | Public-road test driver (SAE Level 3 driver-in-seat, wadachi inheritance) | R2+ | new (wadachi marinization analog) |
| Otete-heavy | kuni-umi Otete heavy-payload variant (≥200 kg) | R1+ | kuni-umi marinization |
| Mimi-precision | kuni-umi Mimi μm-level alignment for marriage station | R1+ | kuni-umi marinization |
| Migaki | Rolled-coil + body-panel surface inspector | R2+ | kanayama reuse |

### 10. Murakumo Placement (R0 design-only)

7-node fleet reuse: naphtali (L1 frame) / zebulun (L3 cab) / joseph (L2 powertrain) / simeon (L4 marriage + L5a paint) / dan (heavy assembly support) / levi (L5b/L5c electrical + road test + emissions) / judah (terminal VIN binder). No new node required.

### 11. 4-Phase Roadmap

| Phase | Scope | Trigger ADR |
|---|---|---|
| **R0** (this ADR) | Scaffold only; 9 cells RuntimeError; 9 lexicon stubs; manifest + actor README/CLAUDE.md | 2605252500 |
| **R1** | Benchtop 1-vehicle prototype (≤2 t cargo van size) + manual assembly + B100 biodiesel + Council Lv6+ + automotive engineering SME onboarded | 2605252515 (reserved) |
| **R2** | Pilot ≤10 vehicles/month Class 3-5 cargo truck (~7.5 t) + LFP battery hybrid + 30-day public comment + first Kasane/Tsutsumi/Akari deployment | 2605252530 (reserved) |
| **R3** | Community-scale Class-8 (~26-40 t) ≥100 vehicles/month + H₂ fuel-cell + LANDS.md plant-site allocation + 60-day public review + R2-mandated zero-tailpipe gate active | 2605252545 (reserved) |

Each subsequent R-phase requires its own ADR + Council Lv6+ vote.

## Consequences

**Positive:**
- Religious-corp gains a constitutionally-bounded design surface for vehicle manufacturing before capability lands.
- §2(a) weapons exclusion declared structurally (12 non-goals, not guidelines) — prevents scope creep into military / mining / weapons-platform applications.
- §2(g) fossil sunset declared at R2 gate — prevents pure-fossil capital lock-in.
- Cross-actor supply loop closes: kanayama Wave 1 (Al coil) + Wave 2 (steel frame) + Wave 3 (Cu interconnect) → sarutahiko vehicle manufacture → wadachi vehicle operation → sarutahiko EoL recycling back to kanayama.
- ECU open-source mandate (G1 + N8) breaks proprietary firmware lock-in across the entire downstream actor fleet.

**Negative / risks:**
- Heavy-truck manufacturing is highly capital-intensive; R3 community-scale ≥100 vehicles/month requires LANDS.md amendment for plant-site allocation + multi-year capital cycle. Capital path deferred to R2 ADR.
- B100 biodiesel feedstock dependency in R0/R1 transition window creates upstream-actor exposure (mitsuho-side oil seed cultivation? — defer to R1 ADR).
- H₂ / NH₃ refueling infrastructure in R2+ depends on hikari (energy actor) cross-coverage; coordination gate to be declared in R2 ADR.
- N4 mining-haul-truck exclusion is irreversible — religious-corp will never produce mining haul trucks; if downstream construction actors (tatekata) require bulk earth movement, alternative methodology (conveyor / on-site mobile crusher / rail) must be used.

**Open questions (deferred to R1):**
- Specific R1 prototype chassis size (van vs pickup vs flat-bed)
- B100 biodiesel SME source + Charter Rider §2(g) supply chain audit
- Frame fabrication welding parameters (root pass, fill pass, cap pass for HSLA-780)
- Driver-monitoring UX design that meets G14 safety-critical alerts without N9 driver-suppression
- ECU open-source baseline (Autoware vs custom)

## Alternatives Considered

1. **Carve under wadachi as wadachi-S5 manufacturing sub-phase**. Rejected: wadachi (operator) and manufacturing (sarutahiko) have domain-distinct witness invariants, lexicons, and phase models. Sibling actors are correct architecture.
2. **Defer until first downstream-actor (e.g. tatekata material delivery) demands a religious-corp-manufactured truck**. Rejected: defers gating to capability landing, which is the failure mode flagged for watatsumi and kanayama.
3. **Restrict Wave 1 to light commercial only (≤3.5 t pickup / van)**. Considered, rejected: Class-8 cargo truck is the methodological reference in the video source; light commercial generalises trivially to Wave 2 once Wave 1 frame + powertrain methodology is bedded in.
4. **Combine sarutahiko + wadachi into a single "land mobility" actor**. Rejected: same reasoning as #1. Witness + phase distinct.
5. **Adopt military truck methodology directly without civilianisation**. Rejected absolutely: §2(a) constitutional invariant. The methodology is adopted; the application is rejected. Non-goals N1, N2, N3, N6, N7 enumerate this.

## References

- ADR-2605192100 §1.12 — Transparent Religious Force
- ADR-2605192200 §2(a), §2(g), §2(h) — Charter Rider weapons / environment / circular anchors
- ADR-2605192315 — Transparent Religious Force open-source R&D registry
- ADR-2605242000 — wadachi (轍) autonomous mobility R0 (operator-side counterpart)
- ADR-2605252200 — watatsumi (綿津見) civilian submersible R0 (pattern source, §2(a) carve-out)
- ADR-2605252400 — kanayama (金山) circular metallurgy R0 (downstream Al/steel/Cu supply)
- ADR-2605250715 — tatekata (建方) construction R0 (pattern source)
- ADR-2605250500 — yakushi (薬師) pharmaceutical R0 (pattern source)
- ADR-2605214000 — Murakumo no-VKE mesh + lexicon port rules
- ADR-2605215000 — etzhayyim inference Murakumo-only (no RunPod)
- ADR-2605191524 — Transparent Force swarm broadcast + witness quorum
- EU Regulation (EU) 2024/1257 — Euro 7 (G8 anchor)
- 日本 ポスト新長期排出ガス規制 — Post New Long Term emission standards (G8 anchor)
- Bharat Stage VI — Indian heavy vehicle emission standards (G8 anchor)
- SAE J3016 — autonomous driving level taxonomy (G12 ceiling)
- YouTube `8XmI2MnAgWQ` — "How Turkey Produces Powerful Trucks Inside Massive Factory" (Wave 1 methodology source)
