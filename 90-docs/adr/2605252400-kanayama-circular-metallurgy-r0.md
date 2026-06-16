---
id: adr-2605252400-kanayama-circular-metallurgy-r0
title: "ADR-2605252400: kanayama (金山) — Circular Metallurgy Tier-B Actor R0 Scaffold (Wave 1 reference = closed-loop aluminum UBC recycling)"
status: proposed
doc_type: adr
topic: kanayama-circular-metallurgy-r0
authoritative: true
last_verified: 2026-05-25
priority: 6.0
axis: architecture
weight: 0.60
authoritative_for:
  - kanayama actor identity (name, DID, tier, namespace, scope boundary) — R0 reservation
  - circular metallurgy constitutional gates (G1..G14) and non-goals (N1..N8)
  - R0 → R3 phased roadmap with R1/R2/R3 ADR reservation
  - Wave 1 = closed-loop aluminum UBC (used beverage container) recycling scope fix
  - Wave 2-4 deferred (steel / copper-brass / rare-earth) carve-out reservation
  - 5-layer construction process (intake QA → de-coat/shred/sort → melt+refine → DC cast+homogenize → roll+finish)
  - 9 Pregel cell catalog + Murakumo placement (R0 design-only)
  - 3 new robotics class reservation (Kamado / Yokin / Migaki) + 3 thermal-rated inheritance (Otete-thermal / Mimi-thermal / Funamori R3 reuse)
  - lexicon namespace reservation (`com.etzhayyim.kanayama.*`, 8 record types)
depends_on:
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605242000-roso-pattern-frontier-distill
  - adr-2605250500-yakushi-pharmaceutical-rd-charter
  - adr-2605250715-tatekata-construction-tier-b-actor-r0
  - adr-2605252200-watatsumi-civilian-submersible-r0
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
  - adr-2606161700-multigenerational-extraction-risk-gate
supersedes: []
superseded_by: []
amended_by:
  - adr-2606161700-multigenerational-extraction-risk-gate  # §5 N1 reframed: scope boundary, not constitutional ban
---

# ADR-2605252400: kanayama (金山) — Circular Metallurgy Tier-B Actor R0 Scaffold

**Status**: proposed
**Date**: 2026-05-25
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify)
**ADR Hierarchy**: Sibling of ADR-2605252200 (watatsumi 水), ADR-2605250715 (tatekata 土), ADR-2605242000 (wadachi 陸), ADR-2605250500 (yakushi 薬), ADR-2605242500 (silicon 半導体). Parent constitutional: ADR-2605192100 §1.11 + ADR-2605192200 §2(g)/§2(h).

## Context

Modern European integrated recycling-rolling mill practice for aluminum used beverage containers (UBC) — Novelis Latchford UK / Constellium Neuf-Brisach FR / Speira Grevenbroich DE — has matured into a **closed-loop melt-cast-roll methodology** with well-defined emissions, mass-balance, and product-qualification stages. Aluminum recycling uses ~5% of the energy of primary Hall-Héroult smelting (4–6 kWh/kg vs 14–16 kWh/kg) and avoids bauxite mining + petroleum-coke anode consumption entirely. The methodology generalises to other metals (steel via EAF, copper via secondary smelter, rare-earth via ionic-liquid leach) with different temperature and chemistry envelopes.

Until this ADR, religious-corp has no Tier-B actor covering material recovery / circular metallurgy. `kuni-umi-S6` (chemistry) addresses upstream chemical production but not metals recovery; `tatekata` consumes finished metals (rebar, conduit, ductwork) but does not produce or recover them; `silicon` Wave 2 (raw-material supply chain) sources virgin wafer feedstock but explicitly excludes consumer-stream recycling. The gap leaves religious-corp dependent on opaque vendor-supplied metals for every other actor (silicon copper interconnect, tatekata structural steel, yakushi sterile packaging aluminum, wadachi vehicle frame aluminum).

This ADR fulfills that gap by reserving `kanayama` as a Tier-B actor whose constitutional posture is **strongly favorable** (recycling directly aligns with §2(g) habitat protection + §2(h) circular economy + §2(e) anti-gatekeeping over bauxite-mining oligopoly) and whose non-goals enumerate the specific upstream-mining and weapons-adjacent feedstocks that must remain excluded. Wave 1 fixes the reference to closed-loop aluminum UBC; Wave 2-4 (steel / copper / rare-earth) require their own ADRs.

The user-prompted source reference for this design is the manufacturing methodology survey in YouTube video `B_WXEaskHf8` ("Recycling aluminum cans in a large European facility").

## Decision

### 1. Actor identity

| Field | Value |
|---|---|
| Actor name | `kanayama` |
| Japanese | 金山 / かなやま (Shinto Kanayamahiko-no-mikoto 金山彦命 + Kanayamabime-no-mikoto 金山姫命 — Kojiki-recorded deities of metals + mining; elemental complement to watatsumi 水) |
| Display name | `金山 (kanayama)` |
| Tier (ADR-2605192415 §B) | **B** — per-domain leader, sibling of watatsumi / tatekata / wadachi / yakushi / silicon / kuni-umi |
| Path-based DID | `did:web:etzhayyim.com:kanayama` |
| Per-batch DID pattern (reserved) | `did:web:etzhayyim.com:kanayama:batch:<lotId>` |
| Per-coil DID pattern (reserved) | `did:web:etzhayyim.com:kanayama:coil:<coilId>` |
| Repo location | `20-actors/kanayama/` |
| Lexicon namespace | `com.etzhayyim.kanayama.*` |
| License | Apache 2.0 + Charter Compliance Rider v2.0 |

### 2. Scope (R0)

**Wave 1 reference (R0–R3 in scope)**: Closed-loop aluminum used beverage container (UBC) recycling. End-to-end: collection → de-coating → shred + magnetic/eddy-current separation → twin-chamber melt + degas + alloy adjust → DC slab casting + homogenization → hot rolling → cold rolling → can-stock coil. Alloys 3xxx (body) + 5xxx (end stock) within commodity off-patent compositions.

**Wave 2-4 (deferred to separate ADRs, Council Lv6+ activation)**:
- Wave 2: Steel / iron recycling (Yokin 1500°C ratings + EAF furnace)
- Wave 3: Copper / brass / bronze recycling (secondary smelter + electrolytic refining)
- Wave 4: Rare-earth element recovery (ionic-liquid leach + bioleaching; §2(g) chemistry strict review)

**Constitutional non-goals (R0–R3, immutable per Wave 1):** see §4 below.

### 3. 5-Layer Closed-Loop Process

Adopted from European integrated recycling-rolling mill practice (Wave 1, aluminum).

| Layer | Stage | Wave 1 (Al) key technology | Wave 2+ extension |
|---|---|---|---|
| **L1** | 集荷 + 計量 + QA | UBC bale weighing, Cl residue + moisture + magnetic impurity detection | Per-metal density/spectro QA |
| **L2** | 脱塗装 + 破砕 + 分離 | ~500°C rotary de-coater (lacquer + paint burnoff), rotary shredder, magnetic + eddy-current separation | Steel: descaling. Cu: enamel burn-off. |
| **L3** | 溶解 + 脱ガス + 精錬 | Twin-chamber Al furnace ~720°C, N₂/Cl₂ degas, salt-flux refining, alloy adjust (3xxx / 5xxx) | Steel: EAF ~1600°C. Cu: secondary reverberatory ~1100°C. |
| **L4** | 鋳造 + 均質化 | DC (Direct Chill) slab casting (1m × 2m × 8m typical), homogenization 540-580°C × 12-24 h | Steel: continuous slab. Cu: cathode/wire-rod cast. |
| **L5** | 圧延 + QA + コイル化 | Hot rolling ~500°C → cold rolling → temper → 0.27 mm can-stock coil; surface inspection, coil QA | Steel: HSM + CSM. Cu: wire drawing. |

### 4. Constitutional Gates (G1–G14, IMMUTABLE R0–R3)

| Gate | Requirement | Rationale |
|---|---|---|
| **G1** | Furnace + casting + rolling firmware **open-source** (Apache 2.0 + Charter Rider) | §2(b) anti-secrecy; Transparent Force |
| **G2** | **Mass-balance audit** on kotoba-datomic: `input_mass = output_metal_mass + dross_mass + emission_mass` within ≥98% closure | §1.12.B Transparent + §2(h) circular |
| **G3** | Per-batch + per-coil **IPFS-pinned photo + video** evidence | Audit trail |
| **G4** | Every **pour** has witness quorum ≥2 robots (Ed25519, DID-bound) | ADR-2605191524 swarm broadcast |
| **G5** | All permits + emissions reports **JP + EN bilingual minimum** + public disclosure | §2(e) anti-gatekeeping |
| **G6** | All alloy specs + firmware artifacts pass **Charter Rider §2(a-h) scan** | §2 enforcement |
| **G7** | All autonomous robots open-source firmware | G1 echo for robotics |
| **G8** | **Air emissions ≤ EU IED 2010/75/EU + 日本大気汚染防止法 + EN 12457 leachate** for solid waste | §2(g) environment |
| **G9** | CAD only from **vendor-free tools** (FreeCAD / OpenSCAD / Open CASCADE / first-party) | §2(b) anti-vendor-lock |
| **G10** | Inference paths use **Murakumo no-VKE mesh only** | ADR-2605214000 / 5000 |
| **G11** | Hot-work zones + high-temp metal pour are **SBT-gated personnel** + 1 SBT = 1 vote council review for non-SBT visitors | §1.12 transparent; safety |
| **G12** | KPI caps: **recovery rate ≥95%** of input metal mass; **energy ≤ recycled-Al baseline** (≤6 kWh/kg for Wave 1) | §2(h) circular performance |
| **G13** | Energy source = **renewable + grid-balanced only**. Captive coal / petroleum coke prohibited. | §2(g) + non-eschatological |
| **G14** | Waste outputs (dross / salt cake / fume filter / leachate) tracked per IPFS lot + §2(h) waste-to-recover quarterly report | §2(h) circular |

### 5. Non-Goals (N1 = scope boundary; N2–N8 IMMUTABLE R0–R3)

`kanayama` has a smaller non-goal surface than watatsumi (12 N's) because recycling is constitutionally aligned. The 8 N's below enumerate the upstream-mining and weapons-adjacent feedstocks out of scope.

> **N1 amended by ADR-2606161700 (2026-06-16).** Primary mining is NOT constitutionally
> forbidden — the Charter gates extraction by a multi-generational (子・孫) × wellbecoming
> RISK assessment (Rider §2(l) v3.2), not by a blanket ban. N1 is therefore a **scope
> boundary** for kanayama (the recovery/recycling actor), not an "immutable recycling-only
> invariant." kanayama stays recovery-first **by design preference** (urban mining at ~5%
> of primary energy is the lower-risk path), but any primary-extraction capability may be
> proposed as its OWN actor/ADR and must pass the §2(l) multi-gen risk gate. N2–N8 below
> are independent concerns and remain immutable R0–R3.

| # | Non-Goal | Constitutional anchor |
|---|---|---|
| **N1** | **Primary mining out of kanayama scope** (bauxite for Wave 1 Al; iron ore Wave 2; copper ore Wave 3, etc.) — kanayama is the recovery actor; **recovery-first by preference, NOT extraction-forbidden** (amended by ADR-2606161700; primary extraction → own actor + §2(l) multi-gen risk gate) | §2(l) multi-gen risk-gate + §2(g) habitat |
| **N2** | **Hall-Héroult primary Al electrolysis** (new ingot from alumina; petroleum-coke anode; PFC GHG emissions); Wave 2+ equivalent ban on primary smelting | §2(g) energy + GHG |
| **N3** | Munitions casing / shell case / spent cartridge brass recovery (war-contamination transfer) | §2(a) + watatsumi N7 echo |
| **N4** | Nuclear-decontamination metal recovery (radiological feedstock) | §1.15 + radiation boundary |
| **N5** | Proprietary alloy compositions held under NDA / non-disclosure | §2(b) anti-secrecy |
| **N6** | E-waste with integrated PCB/IC boards directly co-processed — requires separate WEEE carve-out ADR (heavy metal + halogen leach) | §2(g) chemistry |
| **N7** | Deep-sea polymetallic nodule feedstock | §2(g) habitat + watatsumi N6 echo |
| **N8** | Conflict mineral feedstock (3TG: Tin / Tantalum / Tungsten / Gold) without source attestation | §2(e) anti-gatekeeping inversion (sourcing transparency mandated) |

### 6. Pregel Cell Catalog (9 cells, R0 = import-time RuntimeError)

| Cell | Stage | Murakumo node | Input | Output |
|---|---|---|---|---|
| `intake_qa` | L1 | naphtali | UBC bale | `intakeRecord` |
| `decoating_separation` | L2 | zebulun | `intakeRecord` | `decoatingAttestation` |
| `melting_furnace` | L3 | joseph | `decoatingAttestation` | `meltingAttestation` |
| `dross_recovery` | L3 cross | joseph | melt dross | secondary recovery record (G14) |
| `dc_casting` | L4 | simeon | `meltingAttestation` | `dcCastingAttestation` |
| `hot_rolling` | L5a | dan | `dcCastingAttestation` | `rollingAttestation` |
| `cold_rolling_finishing` | L5b | dan | `rollingAttestation` | `coilQualificationRecord` |
| `air_emissions_audit` | cross-cutting | levi | continuous telemetry | `airEmissionsAuditRecord` (G8) |
| `mass_balance_binder` | terminal | judah | all prior records | mass-balance kotoba-datomic anchor (G2 + G14) |

R0 contract: each cell module imports cleanly; instantiating its class succeeds; calling `.solve()` raises `RuntimeError("kanayama R0 scaffold: activate via Council ADR-2605252415 post-ratification")`.

### 7. Lexicons (8 record types under `com.etzhayyim.kanayama.*`, R0 stubs)

```
intakeRecord                    # L1 — UBC bale weighing + QA
decoatingAttestation            # L2 — de-coating + shred + sort
meltingAttestation              # L3 — twin-chamber melt + alloy composition
dcCastingAttestation            # L4 — DC slab cast + homogenization
rollingAttestation              # L5a — hot rolling pass log
coilQualificationRecord         # L5b — final coil QA
airEmissionsAuditRecord         # cross — continuous stack monitoring
silenRecyclingReview            # Council 5-of-7 Safe — new Wave / new alloy / new feedstock
```

Schema details deferred to R1 ADR.

### 8. Robotics Classes (R0 design-only reservation)

| Class | Role | Phase |
|---|---|---|
| **Kamado (竈)** | Refractory furnace tending (slag scoop, temperature probe, refractory inspection) | R1+ |
| **Yokin (溶金)** | Molten-metal pour manipulator. Wave 1 Al-rated (~720°C); Wave 2 steel-rated (~1600°C) | R1+ (Wave 2: thermal upgrade) |
| **Migaki (磨き)** | Rolled-coil surface inspector (visual + eddy-current + UT thickness) | R1+ |
| Otete-thermal | kuni-umi Otete high-temp variant | R1+ |
| Mimi-thermal | kuni-umi Mimi high-temp metrology | R1+ |
| Funamori | UBC bulk surface logistics; Wave 1 domestic land transport, Wave 3 international maritime (Funamori reuse, ADR-2605242745) | R3 reuse |

### 9. Murakumo Placement (R0 design-only)

7-node reuse: naphtali (intake) / zebulun (de-coating) / joseph (melt + dross) / simeon (casting) / dan (rolling) / levi (emissions + AE) / judah (mass-balance binder). No new node required.

### 10. 4-Phase Roadmap

| Phase | Scope | Trigger ADR |
|---|---|---|
| **R0** (this ADR) | Scaffold only; 9 cells RuntimeError; 8 lexicon stubs; manifest + actor README/CLAUDE.md | 2605252400 |
| **R1** | Benchtop ≤1 kg pot melt + manual rolling PoC; UBC ≤10 kg per batch; SME metallurgist onboarded | 2605252415 (reserved) |
| **R2** | Pilot 100 kg/day plant; Kamado + Yokin + Migaki PoC; 30-day public comment | 2605252430 (reserved) |
| **R3** | Community-scale 10 t/day integrated mill; coil shippable grade; 60-day public review; LANDS.md plant site allocation | 2605252445 (reserved) |

Each subsequent R-phase requires its own ADR + Council Lv6+ vote. Wave 2 (steel) onwards is a Wave-level branching, also requiring its own ADR series.

## Consequences

**Positive:**
- Religious-corp gains a constitutionally-bounded design surface for material recovery before capability lands.
- Recycling alignment is positive: §2(g) habitat + §2(h) circular + §2(e) anti-gatekeeping all support, rather than constrain, the actor.
- Wave 1 closes the aluminum supply loop for yakushi (sterile blister packaging), wadachi (vehicle frames), kuni-umi (electrical conductor extrusion), and tatekata (curtain-wall / ductwork).
- Energy footprint is structurally low: aluminum recycling at ~5% of primary Hall-Héroult energy is the largest constitutional energy win the religious-corp can achieve in the materials layer.
- Mass-balance kotoba-datomic anchor (G2) is novel cross-cell substrate: it forces every cell to declare its mass input/output rigorously, enabling §2(h) circular reporting without after-the-fact reconciliation.

**Negative / risks:**
- Wave 1 Al recycling depends on adequate UBC collection feedstock; rural / low-density jurisdictions may not have sufficient supply for R3 community-scale 10 t/day throughput. R3 site-selection ADR must address feedstock catchment radius (≥50 km typical for European mills).
- Dross + salt-cake disposal is a real environmental liability if not properly secondary-recovered (G14). R2 ADR must declare specific salt-cake processing path (typically returned to feedstock mill for K-salt + secondary Al recovery; standalone disposal is §2(g) violation).
- N3 (munitions brass) recovery prohibition reduces feedstock options for Wave 3 (copper alloys); operational impact is acceptable per constitutional posture.

**Open questions (deferred to R1):**
- Specific 3xxx / 5xxx alloy compositions for R1 PoC batch
- Stack emission continuous monitor sensor selection (PFC vs NOx primary)
- Mass-balance closure measurement method (gravimetric vs spectroscopic)
- Wave 2 (steel) Yokin thermal upgrade path vs new Yokin class

## Alternatives Considered

1. **Carve under kuni-umi-S6 (chemistry)**. Rejected: kuni-umi-S6 addresses chemical synthesis (industrial chemistry production), not metal recovery. The mass-balance + alloy + rolling-mill stack is methodologically distinct.
2. **Defer until first downstream-actor (e.g. yakushi packaging) needs aluminum supply**. Rejected: deferral risks the same gate-after-the-fact problem flagged for watatsumi. Constitutional gates must precede capability.
3. **Restrict Wave 1 to only un-coated aluminum scrap (industrial pre-consumer)**. Rejected: de-coating (L2) is a constitutional pro-clearance because it integrates §2(e) anti-gatekeeping over post-consumer UBC streams. Excluding lacquered UBC would defeat the recycling mission.
4. **Combine kanayama + watatsumi + Funamori into a single "material substrate" actor**. Rejected: phase models and class regimes are domain-distinct. Sibling actors are correct architecture; cross-actor cells (Funamori R3 reuse) handle the integration points.

## References

- ADR-2605192100 §1.11 — Land sovereignty (mining feedstock implication)
- ADR-2605192200 §2(g), §2(h) — Environment + circular economy constitutional anchors
- ADR-2605192315 — Transparent Religious Force open-source R&D registry
- ADR-2605252200 — watatsumi (綿津見) civilian submersible R0 (sibling, 水)
- ADR-2605250715 — tatekata (建方) construction R0 (sibling, 土)
- ADR-2605242000 — wadachi (轍) autonomous mobility R0 (sibling, 陸)
- ADR-2605250500 — yakushi (薬師) pharmaceutical R0 (sibling, 薬)
- ADR-2605242500 — silicon Wave 1 (sibling, 半導体)
- ADR-2605214000 — Murakumo no-VKE mesh + lexicon port rules
- ADR-2605215000 — etzhayyim inference Murakumo-only (no RunPod)
- ADR-2605191524 — Transparent Force swarm broadcast + witness quorum
- EU IED 2010/75/EU — Industrial Emissions Directive (G8 anchor)
- 日本 大気汚染防止法 — Japan Air Pollution Control Act (G8 anchor)
- EN 12457 — Solid waste leachate test (G8 anchor)
- YouTube `B_WXEaskHf8` — "Recycling aluminum cans in a large European facility" (Wave 1 methodology source)
