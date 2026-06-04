---
id: adr-2605252200-watatsumi-civilian-submersible-r0
title: "ADR-2605252200: watatsumi (綿津見) — Civilian Submersible Manufacturing Tier-B Actor R0 Scaffold"
status: proposed
doc_type: adr
topic: watatsumi-civilian-submersible-r0
authoritative: true
last_verified: 2026-05-25
priority: 6.0
axis: architecture
weight: 0.60
authoritative_for:
  - watatsumi actor identity (name, DID, tier, namespace, scope boundary) — R0 reservation
  - civilian submersible manufacturing constitutional gates (G1..G14) and non-goals (N1..N12)
  - R0 → R3 phased roadmap with R1/R2/R3 ADR reservation
  - 5-layer modular ring-section construction process (耐圧殻リング → セクション → NDT → 統合 → 結合+試験+公試)
  - 9 Pregel cell catalog + Murakumo placement (R0 design-only)
  - 4 new robotics class reservation (Sango / Tako / Hibiki / Ama) + 3 marinized inheritance (Otete-marine / Mimi-marine / Funamori reuse)
  - lexicon namespace reservation (`com.etzhayyim.watatsumi.*`, 8 record types)
depends_on:
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605242000-roso-pattern-frontier-distill
  - adr-2605250500-yakushi-pharmaceutical-rd-charter
  - adr-2605250715-tatekata-construction-tier-b-actor-r0
  - adr-2605242500-baien-ternary-silicon-and-tsukuru-fab-charter
  - adr-2605242745-silicon-wave-2-funamori-marine-bulk-cargo
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192315-etzhayyim-transparent-force-rd
  - adr-2605192400-etzhayyim-eros-gore-council-judging
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
  - adr-2605214000-etzhayyim-murakumo-mesh-no-vke-and-lexicon-port-rules
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - 2605191524-ameno-multi-tab-swarm-broadcast
related:
  - wellbecoming-karma-lean-proofs
  - wellbecoming-karma-lean-proofs
  - wellbecoming-karma-lean-proofs
  - wellbecoming-karma-lean-proofs
  - wellbecoming-karma-lean-proofs
supersedes: []
superseded_by: []
---

# ADR-2605252200: watatsumi (綿津見) — Civilian Submersible Manufacturing Tier-B Actor R0 Scaffold

**Status**: proposed
**Date**: 2026-05-25
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify)
**ADR Hierarchy**: Sibling of ADR-2605242000 (wadachi), ADR-2605250500 (yakushi), ADR-2605250715 (tatekata). Parent constitutional: ADR-2605192100 §1.12 (Transparent Force) + ADR-2605192200 §2(a) (no weapons).

## Context

Modern European shipyard practice for large submerged pressure vessels (TKMS / Naval Group / Saab Kockums / Fincantieri / Navantia) has matured into a **modular ring-section construction methodology** with well-defined NDT, integration, and class-certification stages. That methodology — pressure-hull rolling, ring-frame welding, multi-pass section joining, 100% radiographic + ultrasonic inspection, pressure-vessel certification — is **technologically neutral**: it underpins both military combat submarines (Charter Rider §2(a) prohibited) and civilian deep-sea research / subsea infrastructure / aquaculture / observation craft (constitutionally allowed and arguably constitutional **carriers** for §2(e) anti-gatekeeping and §1.13 wellbecoming when applied to research/infrastructure missions).

Until this ADR, religious-corp has no Tier-B actor covering submerged pressure-vessel manufacturing. `kuni-umi.Funamori` (ADR-2605242745) is **surface-only** with explicit `§2(a) no naval weapons` and IMO MASS Degree 3 cap; it does not address pressure-hull metallurgy, deep-water NDT, or submersible-class certification. Without a dedicated actor:

1. Civilian deep-sea research capability (e.g., Shinkai 6500-equivalent, hydrothermal-vent observation) has no design surface inside religious-corp.
2. Subsea cable inspection / fiber laying / offshore wind anchor verification (kotoba-datomic physical substrate concerns) has no first-party manufacturing path — every project would depend on opaque defence-adjacent vendors.
3. Constitutional gates against military/weapons submersibles must be **declared before** capability lands, mirroring the wadachi (autonomous mobility) and yakushi (pharmaceutical) R0 patterns — gate-after-the-fact loses meaning.

This ADR fulfills that gap by reserving `watatsumi` as a Tier-B actor, declaring 14 constitutional gates and 12 non-goals (the +2 over the wadachi/tatekata pattern reflect submersible-specific risks: nuclear propulsion and acoustic-stealth coatings), and landing a 9-cell Pregel scaffold whose `solve()` methods raise `RuntimeError` until R1 activation.

The user-prompted source reference for this design is the manufacturing methodology survey in the YouTube video "Inside One of Europe's Most Advanced Shipyards Building Giant Submarines From Scratch" (LfiVZxNbgZM, 2026). The methodology is adopted; the military application is rejected per §2(a).

## Decision

### 1. Actor identity

| Field | Value |
|---|---|
| Actor name | `watatsumi` |
| Japanese | 綿津見 / わだつみ (Shinto sea kami; counter-form of Funamori 船守 surface→submerged) |
| Display name | `綿津見 (watatsumi)` |
| Tier (ADR-2605192415 §B) | **B** — per-domain leader, sibling of `kuni-umi` / `wadachi` / `tatekata` / `yakushi` / `silicon` |
| Path-based DID | `did:web:etzhayyim.com:watatsumi` |
| Per-craft DID pattern (reserved) | `did:web:etzhayyim.com:watatsumi:craft:<serial>` |
| Per-mission DID pattern (reserved) | `did:web:etzhayyim.com:watatsumi:mission:<missionCode>` |
| Repo location | `20-actors/watatsumi/` |
| Lexicon namespace | `com.etzhayyim.watatsumi.*` |
| License | Apache 2.0 + Charter Compliance Rider v2.0 |

### 2. Scope (R0)

**In scope (civilian only):**

- Research submersibles (manned ≤3 crew, unmanned ROV/AUV; design depth ≤6500 m)
- Subsea infrastructure inspection + cable laying support (design depth ≤2000 m)
- Aquaculture infrastructure + benthic observation networks (design depth ≤200 m)

**Explicitly deferred to R3+:**

- Tourist submersibles (≤50 m acrylic-hull): wellbecoming §1.13 review required. Council Lv6+ supermajority.

**Constitutional non-goals (R0–R3, immutable; amendment requires Council Lv6+ supermajority + new ADR):** see §4 below.

### 3. 5-Layer Modular Ring-Section Construction Process

Adopted from modern European shipyard practice; civilianised by metallurgical, propulsion, and acoustic-emission constraints.

| Layer | Stage | Key technology | Civilian-only constraints |
|---|---|---|---|
| **L1** | 耐圧殻リング製造 (pressure hull ring fabrication) | HSLA-80 steel plate rolling OR Ti-6Al-4V ELI titanium (Shinkai 6500 grade) ring-frame welding (TIG / SAW); roundness < 0.5% Ø | No HY-100 or higher (military-grade steel) without per-project Council attestation; no proprietary alloy formulations |
| **L2** | セクション組立 (section assembly) | 10–15 m section stacking; internal frame + bulkhead installation; hull penetrators (hatches, sensor heads, snorkel) | No torpedo tubes, missile silos, mine-laying bays, or weapon mounts (N1) |
| **L3** | 溶接全 NDT (full weld inspection) | 100% RT/UT/PT to ASME BPVC §VIII Div 3 or equivalent; in-process witness via Sango/Tako AUV swarm | All inspection records IPFS-pinned + DNV/ABS/NK/BV audit log on kotoba-datomic (G2) |
| **L4** | システム統合 (system integration) | Propulsion (LFP battery / H2 / NH3 / methanol fuel-cell only); pressure-compensated electrical penetrations; ballast/trim; CO₂ scrubber + O₂ generator; passive sonar; acoustic modem | **No nuclear propulsion** (N2); active sonar ≤180 dB re 1µPa @1m (G8 cetacean protection); no proprietary acoustic stealth coatings (N12) |
| **L5** | セクション結合 + 圧力試験 + 公試 (section joining + pressure test + sea trial) | Final ring-to-ring multi-pass TIG + 100% RT; PWHT; **1.25× design-depth water-pressure test**; dock trial → harbor → deep-water class certification | Class certification under civilian regimes (DNV-RU-UWT / ABS Underwater Vehicles / NK 同等), not naval secret class |

### 4. Constitutional Gates (G1–G14, IMMUTABLE R0–R3)

| Gate | Requirement | Rationale |
|---|---|---|
| **G1** | Pressure hull CAD + FEA + firmware **open-source** (Apache 2.0 + Charter Rider) | §2(b) anti-secrecy; constitutional Transparent Force |
| **G2** | Class certification audit log on **kotoba-datomic** (DNV/ABS/NK/BV equivalent), all stages | §1.12.B Transparent Force visibility |
| **G3** | Every weld pass and every test step has **IPFS-pinned photo + video** evidence | ADR-2605241500 dataset substrate echo |
| **G4** | Every critical weld signed by **witness quorum ≥2 distinct robots** (Ed25519, DID-bound) | ADR-2605191524 swarm broadcast |
| **G5** | All permits, class reports, owner's manuals **JP + EN bilingual minimum** | §2(e) anti-gatekeeping |
| **G6** | All CAD + firmware artifacts pass **Charter Rider §2(a-h) scan** before release | §2 enforcement |
| **G7** | Autonomous submerged operation limited to **maritime SAE J3016 Level ≤4 equivalent**; Level 5 = constitutional non-goal | wadachi G7 echo |
| **G8** | Active sonar **≤180 dB re 1µPa @1 m** (NMFS Level A harassment threshold); no airgun above 180 dB | §1.13 wellbecoming applied to cetacean/marine life |
| **G9** | CAD only from **vendor-free tools** (FreeCAD, OpenSCAD, Open CASCADE, first-party); CATIA / NX / Solid Edge prohibited | §2(b) anti-proprietary lock-in |
| **G10** | Inference paths use **Murakumo no-VKE mesh only** per ADR-2605214000 / ADR-2605215000 | Religious-corp inference SSoT |
| **G11** | Hot-work zones, pressure-test bays, and dive operations are **SBT-gated personnel** + 1 SBT = 1 vote council review for non-SBT visitors | §1.12 transparent; safety + governance |
| **G12** | **KPI caps**: max civilian depth 6500 m, max manned crew 3, max submerged duration 72 h. Council Lv6+ to amend | Self-imposed scope discipline |
| **G13** | Propulsion fuels: **LFP battery / H₂ / NH₃ / methanol fuel-cell only**. Nuclear propulsion is constitutional N2 | §2(g) clean substrate echo + non-eschatological |
| **G14** | MARPOL Annex I–VI + BWMC + IMO biofouling guidelines compliance; consistent with ADR-2605242745 Funamori | §2(g) marine pollution prevention |

### 5. Non-Goals (N1–N12, IMMUTABLE R0–R3)

| # | Non-Goal | Constitutional anchor |
|---|---|---|
| **N1** | **Naval weapons** (torpedoes, missiles, mines, depth charges, anti-submarine munitions, any kinetic weapon mount or stowage) | §2(a) explicit |
| **N2** | **Nuclear propulsion** (reactor-driven submersibles of any size or yield) | §2(g) + §1.15 non-eschatological |
| **N3** | Military stealth / covert / camouflaged submersibles; anechoic-tile R&D for weapon evasion | §2(a) + §2(d) covert |
| **N4** | Bottom-mounted weapon platforms or hibernating arsenal submersibles | §2(a) |
| **N5** | Sovereignty-violating EEZ/territorial-waters incursion (except via the Transparent Force §1.12.B authorisation workflow with full on-chain log) | §1.11 land sovereignty + §1.12.B |
| **N6** | Deep-sea mining (polymetallic nodule, hydrothermal sulfide, cobalt-crust extraction) — irreversible habitat destruction | §2(g) habitat |
| **N7** | Salvage of unexploded ordnance / wartime munitions | §2(a) war-contamination transfer |
| **N8** | Submarine cable cutting, sabotage, or interdiction capability | §2(d) infrastructure attack |
| **N9** | Human depth-record / vanity dive priority missions | §1.13 wellbecoming |
| **N10** | Mariana / hadal-zone (≤-10,000 m) R&D as priority — exceeds G12 energy + safety envelope | G12 |
| **N11** | Closed-loop life support beyond 72 h without independent Council review (sleep/atmosphere/psychological harm) | §1.13 wellbecoming |
| **N12** | Proprietary acoustic-stealth coating R&D | §2(a) + §2(b) |

### 6. Pregel Cell Catalog (9 cells, R0 = import-time RuntimeError)

| Cell | Stage | Murakumo node | Input | Output |
|---|---|---|---|---|
| `hull_ring_fabrication` | L1 | naphtali | `materialLot`, `ringSpec` | `pressureHullAttestation` |
| `section_assembly` | L2 | zebulun | `pressureHullAttestation` ×N | `sectionAssemblyAttestation` |
| `weld_inspection` | L3 | joseph | `sectionAssemblyAttestation` | `weldInspectionRecord` |
| `system_integration` | L4 | simeon | `weldInspectionRecord` | `systemIntegrationAttestation` |
| `section_joining` | L5a | dan | `systemIntegrationAttestation` | `sectionJoiningAttestation` |
| `pressure_test` | L5b | dan | `sectionJoiningAttestation` | `pressureTestRecord` |
| `sea_trial` | L5c | levi | `pressureTestRecord` | `seaTrialRecord` |
| `marine_emissions_audit` | cross-cutting | levi | telemetry stream | continuous MARPOL/BWMC compliance record |
| `class_certification_binder` | terminal | judah | all prior records | `classCertificationRecord` (kotoba-datomic-anchored audit binder) |

R0 contract: each cell module imports cleanly; instantiating its class succeeds; calling `.solve()` raises `RuntimeError("watatsumi R0 scaffold: activate via Council ADR post-ratification")`.

### 7. Lexicons (8 record types under `com.etzhayyim.watatsumi.*`, R0 stubs)

```
pressureHullAttestation        # L1 — material lot / roundness / RT/UT
sectionAssemblyAttestation     # L2 — ring stacking + bulkhead
weldInspectionRecord           # L3 — 100% NDT pass log
systemIntegrationAttestation   # L4 — propulsion + life support + sensors
sectionJoiningAttestation      # L5a — final ring-to-ring
pressureTestRecord             # L5b — 1.25× design depth
seaTrialRecord                 # L5c — dock / harbor / deep-water trial
silenSubmersibleReview         # Council 5-of-7 Safe attestation, all new craft classes
```

Schema details deferred to R1 ADR; R0 ships stub JSON with `id` + `defs.main.type=record` only.

### 8. Robotics Classes (R0 design-only reservation)

| Class | Role | Phase | Inheritance |
|---|---|---|---|
| **Sango (珊瑚)** | Benthic inspection AUV swarm — outer-hull weld witness + biofouling | R1+ | new |
| **Tako (蛸)** | Hull-clinging interior NDT walker (8-leg suction) | R2+ | new |
| **Hibiki (響)** | Fixed sonar / acoustic metrology station | R1+ | new |
| **Ama (海女)** | ADS-equivalent humanoid subsea welder | R2+ | Hitogata marinization |
| Otete-marine | Subsea-rated manipulator | R1+ | kuni-umi Otete marinization |
| Mimi-marine | Subsea pressure-compensated metrology | R1+ | kuni-umi Mimi marinization |
| Funamori | Surface support / R3 mother-ship | reuse | ADR-2605242745 |

### 9. Murakumo placement (R0 design-only)

`naphtali` (L1 fabrication), `zebulun` (L2 assembly + L5a joining), `joseph` (L3 NDT), `simeon` (L4 integration), `dan` (L5a/L5b pressure), `levi` (L5c sea trial + emissions audit), `judah` (class certification binder). All 10-node fleet reused; no new node required for R0.

### 10. 4-Phase Roadmap

| Phase | Scope | Trigger ADR |
|---|---|---|
| **R0** (this ADR) | Scaffold only; 9 cells import-time RuntimeError; lexicon stubs; manifest + actor README/CLAUDE.md | 2605252200 |
| **R1** | Benchtop pressure vessel ≤500 mm Ø, ≤30 m water pool test; ROV ≤1 m design; Sango + Hibiki + Otete-marine PoC | 2605252215 (reserved) |
| **R2** | Pilot ROV ≤2 m; harbor trials ≤200 m depth; tatekata-shared yard pilot facility; Tako + Ama PoC | 2605252230 (reserved) |
| **R3** | Research submersible ≤6500 m or infrastructure ROV ≤2000 m; full DNV / ABS class certification; Funamori mother-ship integration | 2605252245 (reserved) |

Each subsequent R-phase requires its own ADR, Council Lv6+ vote, and (R3) 60-day public review.

## Consequences

**Positive:**
- Civilian submersible manufacturing has a constitutionally-bounded design surface inside religious-corp before capability lands.
- Charter Rider §2(a) weapons exclusion is declared structurally (12 non-goals, not just guidelines), preventing scope creep into combat applications.
- Subsea cable inspection + offshore wind anchor verification path opens for kotoba-datomic physical-substrate concerns (paired with Funamori for surface).
- Manufacturing methodology adopted from mature European shipyard practice is **civilianised** rather than reinvented — engineering risk minimized, constitutional risk explicitly enumerated.

**Negative / risks:**
- Submersible manufacturing is capital-intensive; R3 community-scale will require land-trust dry-dock allocation (LANDS.md amendment) + multi-year capital cycle. Capital path not addressed here — deferred to R2 ADR.
- Dual-use methodology means defence-sector actors could fork the open-source CAD; Apache 2.0 + Charter Rider mitigates the licence dimension but cannot prevent technical reuse. Acceptable per §2(b) anti-secrecy: secrecy is not a defence the religious-corp adopts.
- Class certification under civilian regimes (DNV-RU-UWT etc.) requires Council Lv6+ engagement of certified marine surveyors as SMEs — surveyor onboarding gate added to R1 trigger.

**Open questions (deferred to R1):**
- Specific HSLA grade vs Ti-6Al-4V ELI choice per craft class
- Acoustic-emission monitoring system (passive AE during pressure test) sensor placement
- AUV swarm tether vs untethered comms protocol on kotoba-datomic
- Member-vs-employee status for crewed dives (overlap with §1.12 + MEMBERS.md)

## Alternatives Considered

1. **Defer entirely until R1 demand emerges.** Rejected: matches `wadachi` deferral risk — capability would land bottom-up against deployment pressure. Charter-Rider §2(a) compliance must be visible before manufacturing begins.
2. **Carve as `kuni-umi-S7` sub-phase under existing Tier-B.** Rejected: pressure-hull metallurgy, class-certification regimes, and acoustic-emission protocols are domain-distinct from kuni-umi planetary-infra phases (S1–S6). Independent Tier-B status matches tatekata/yakushi/wadachi precedents.
3. **Adopt military submarine methodology directly without civilianisation.** Rejected absolutely: §2(a) constitutional invariant. The methodology is adopted; the application is rejected. Non-goals N1, N3, N4, N7, N8, N12 enumerate this.
4. **Use unmanned (ROV/AUV) only and prohibit manned submersibles.** Considered, rejected for R0: manned research submersibles (Shinkai-class) are scientifically and culturally significant for marine biology / hydrothermal vent observation; G12 caps (≤3 crew, ≤72 h) are sufficient discipline.

## References

- ADR-2605192100 §1.12 — Transparent Religious Force
- ADR-2605192200 §2(a) — Charter Rider weapons prohibition (constitutional anchor)
- ADR-2605192315 — Transparent Religious Force open-source R&D registry
- ADR-2605242000 — wadachi (轍) autonomous mobility R0 (pattern source)
- ADR-2605250500 — yakushi (薬師) pharmaceutical R0 (pattern source)
- ADR-2605250715 — tatekata (建方) construction R0 (pattern source)
- ADR-2605242745 — Silicon Wave 2 Funamori (船守) marine bulk cargo (sibling, surface domain)
- ADR-2605214000 — Murakumo no-VKE mesh + lexicon port rules
- ADR-2605215000 — etzhayyim inference Murakumo-only (no RunPod)
- ADR-2605191524 — Transparent Force swarm broadcast + witness quorum
- DNV-RU-UWT (civilian underwater technology), ABS Underwater Vehicles, NK class rules — external civilian class references
- YouTube `LfiVZxNbgZM` — "Inside One of Europe's Most Advanced Shipyards Building Giant Submarines From Scratch" (methodology survey source; military application rejected per §2(a))
