---
id: adr-2606051600-noroshi-photonic-electronic-convergence-comms-chip-isac
title: "ADR-2606051600: noroshi (烽) — Photonics-Electronics Convergence (光電融合) Comms Chip + ISAC Sim + Photonic Packaging Robotics"
status: proposed
doc_type: adr
topic: noroshi-photonic-convergence
authoritative: true
last_verified: 2026-06-05
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "first photonic / optical-communication actor; closes the 光電融合 + ISAC gap left by the all-electronic silicon line"
authoritative_for:
  - noroshi
  - photonic-electronic-convergence
  - isac-jcas-sim
depends_on:
  - 2605242500
  - 2605312345
  - 2605215000
  - 2605231525
  - 2606032130
related:
  - 2605242515
  - 2605242530
  - 2605261300
  - 2606012600
  - 2606033600
  - 2605261800
  - 2606010600
  - 2606042330
  - 2605192100
supersedes: []
superseded_by: []
---

# ADR-2606051600: noroshi (烽) — Photonics-Electronics Convergence (光電融合) Comms Chip + ISAC Sim + Photonic Packaging Robotics

**Status**: proposed
**Date**: 2026-06-05
**Deciders**: Jun Kawasaki

# Context

The question put to the substrate was: *「光電融合の通信チップの actor, robotics, ISAC sim の設計はできているか?」*
A repo-wide search returned **no**:

- **No optical / photonic communication chip.** The silicon line (`silicon` ADR-2605242500,
  `iwakura` ADR-2605242515, `fuigo` ADR-2605242530) is **all-electronic, all-digital** ternary ASIC +
  fab. Its packaging cell covers wire-bond / flip-chip / CoWoS and *alignment-camera* optics, not
  **photonic** interconnect. There is zero coverage of silicon photonics, co-packaged optics (CPO),
  optical transceivers, photonic ICs (PIC), or the 光電融合 (photonics-electronics convergence) idea
  (the IOWN shape).
- **No ISAC.** Nothing covers Integrated Sensing And Communication (a.k.a. JCAS, joint
  communication-and-sensing): one waveform that both carries data and senses range/velocity.
- **No photonic-packaging robotics.** The robotics actors (sanae/kiyome/hataori/giemon, the silicon
  fab cells) are decoupled from any optical assembly; fibre↔grating active alignment — the dominant
  cost and labour of photonic packaging — is unrepresented.

The closest existing actors are siblings, not the thing: `tsutae` (RF handheld comms, electronic
modem), `watatsuna` (the submarine-cable *medium* KG), `silicon`/`iwakura`/`fuigo` (electronic fab +
digital ASIC). The 光電融合 layer that sits **between** an electronic compute die and an optical fibre
— and the sensing function that the same photonic/RF front-end can do for free — was simply missing.

This is also a **dual-use** domain that the Charter constrains tightly. Optical power and ISAC sensing
are one design decision away from directed-energy weapons, laser dazzlers, and fire-control /
targeting radar; photonic EDA is dominated by proprietary tools (Cadence/Synopsys/Lumerical/Ansys)
and NDA foundry PDKs; and packaging robotics displaces human technicians. Any design here must be
**civilian by construction**, **clean-room open-EDA**, **no-server-key**, **outward-gated**, and
**displacement-dividend coupled** — or it does not belong in this repo.

# Decision

Introduce **`noroshi` (烽)** — a Tier-B actor for **photonics-electronics convergence (光電融合)
communication chips**, with the **ISAC** simulation and the **photonic packaging robotics** as two of
its three faces. 烽 (狼煙, beacon-fire) is the original optical telecom — a watchtower **senses** a
distant fire and **relays** a coded message — one emission, two functions, which is precisely ISAC.

It does **all three** asked-for pieces as one actor with three faces, each backed by a deterministic,
offline, unit-tested `methods/` core:

1. **chip face — 光電融合 comms-chip design + optical link budget.**
   `methods/link_budget.py` computes the end-to-end power budget of a silicon-photonic / CPO link
   (laser → modulator → grating coupler → waveguide/fibre → photodetector vs receiver sensitivity →
   margin) plus the **energy-per-bit** figure of merit that justifies CPO. On the reference designs a
   co-packaged 2 km/100G link closes at **+10.05 dB** and costs **3.141 pJ/bit vs 12.441 pJ/bit** for
   a front-panel pluggable — **3.96× lower energy/bit**, the number that makes CPO worth building.

2. **isac face — Integrated Sensing And Communication simulator.**
   `methods/isac_sim.py` implements the OFDM-radar reciprocal-processing model (Sturm & Wiesbeck):
   the transmitter divides its known data symbols out of the echo to get a pure delay-Doppler grid,
   then a 2-D periodogram recovers a target's range + radial velocity. It also gives the
   **communication-vs-sensing power-split (ρ) tradeoff** — more comms power buys data rate at the cost
   of sensing precision (CRLB) — making JCAS a quantified design choice. Sensing is **civilian**: the
   target is an **object** with a range and a velocity, never a person (no `:person` class exists).

3. **packaging face — photonic packaging robotics + laser safety.**
   `methods/active_alignment.py` is the safety-critical coded core (the noroshi analogue of tazuna's
   `teleop_safety`): a Hooke-Jeeves pattern search aligns a fibre to an on-chip grating coupler by
   climbing measured coupling power to the unknown peak (<1 dB in ~50 probes), gated by a **laser-safety
   interlock** — an IEC 60825 class gate (any hazardous class needs an enclosure interlock + safety
   attestation) and a **civilian-use** gate (weaponisation / directed-energy / dazzle / fire-control is
   refused before the laser is ever energised).

**Charter shape (constitutional invariants, immutable R0→R5):**

- **G1 cleanroom-epda / N5** — open-source photonic + digital EDA ONLY (GDSFactory / Meep / KLayout /
  Verilator / yosys / OpenLane + an open PDK), extending the verified `iwakura` RTL→sky130 GDSII flow
  (ADR-2606012800) to photonics; no Cadence/Synopsys/Lumerical/Ansys bundling, no NDA foundry PDK
  in-repo, no decompile/trademark/fork (the `sumitsubo` G1 + `nv-compat` precedent).
- **G3 civilian-force-separation / N1** — optical power + ISAC sensing are civilian-only;
  weaponisation is **structurally unrepresentable** in the schema, lexicons, and
  `active_alignment.PERMITTED_USES` (the `iwakura`/`nusa` `:class` precedent; Mission Charter §1.12).
- **G4 sensing-not-surveillance / N2** — an ISAC `senseEstimate` is an object's range+velocity; there
  is no person/biometric/pattern-of-life field (the `watari` G4 invariant).
- **G5 laser-safety-soft / N3** — the IEC 60825 interlock is best-effort soft-safety, **not** a
  certified safety controller (certified / hard-RT live actuation = R5/Lv7+; `kotoba-os` N2 precedent).
- **G2 displacement-dividend-coupling** — packaging robots displace fibre-alignment technicians, so a
  live fleet requires a funded tenure-weighted cohort (ADR-2606032130).
- **G6 murakumo-only / N6** (ADR-2605215000) · **G7 no-server-key** (ADR-2605231525) · **G8
  outward-gated** (live tapeout / mask set / measurement / laser / actuation = Council Lv6+ + operator;
  Class-3B/4 near humans Lv7+) · **G9 kotoba-EAVT canonical state** (ADR-2605312345, no Kotoba/Datomic) ·
  **G10 sourcing-honesty** (`:representative`; sims are arithmetic/DSP, no measured silicon) · **G11
  sbom-provenance** (a fabricated die carries a CycloneDX SBOM into kotoba at tapeout; the `wasm-sbom`
  / `giemon` part-graph precedent).

**Siblings:** `silicon`/`iwakura`/`fuigo` are the **electronic** (digital ternary) silicon line;
noroshi is the **photonic** (光電融合) sibling. `tsutae` is the RF comms device; noroshi is the optical
comms chip. `watatsuna` is the submarine-cable **medium**; noroshi is the **CPO transceiver chips** at
the cable's ends (they share the resilience picture).

**R0 deliverable (this ADR):** the actor (`20-actors/noroshi/`) with manifest, 5 lexicons
(`com.etzhayyim.noroshi.*`), kotoba EAVT schema + `:representative` seed, a packaging robotics fleet
seed, 6 cells (langgraph→WASM, `.solve()` raises; `active_alignment` coded), the 3 verifiable method
cores (**34 method tests + 14 cell-state-machine tests green**), generated `out/` reports, a shared
ontology (`00-contracts/schemas/photonic-convergence-ontology.kotoba.edn`), and a DID registration in
`infra-actors.ts`. **Zero invariant amendments.**

# Consequences

**Positive.**
- Closes the 光電融合 + ISAC + photonic-robotics gap with one coherent, charter-shaped actor instead of
  three loose pieces; the beacon-fire metaphor makes communication-and-sensing one idea.
- Everything asked for is **verifiable now, before any silicon**: link budget, JCAS recovery, and
  active alignment are pure arithmetic/DSP with 48 green tests and reproducible `out/` reports.
- Extends, rather than re-invents, the proven open-EDA flow (`iwakura` RTL→GDSII) and the safety
  patterns (`tazuna` coded safety cell, `kotoba-os` soft-safety, `watari` sensing-not-surveillance).
- Dual-use risk is contained **structurally**, not by policy text: weaponisation and person-sensing are
  unrepresentable in the data model.

**Negative / honest limits (G10/N4).**
- **No silicon, no foundry, no measured device.** The link budget is a dB ledger over
  `:representative` device parameters; the sims are not characterisation data. Live tapeout / mask set
  / measurement is R3+ and Council Lv6+ + operator gated (G8), and must ship a CycloneDX SBOM (G11).
- **ISAC sim is a model, not a radar.** It is OFDM-radar reciprocal processing on a synthetic echo with
  honest aliasing beyond R_max / the Doppler interval; no live emission (G8). The default waveform's
  velocity resolution is coarse (few symbols) — a parameter choice, not a measured limit.
- **Active alignment is simulated.** A Gaussian coupling model + Hooke-Jeeves search; no robot, no live
  laser. A live fleet is G7 no-server-key + G8 outward-gated + G2 dividend-coupled.
- **EPDA bindings are nominal.** The cells name GDSFactory/Meep/KLayout/OpenLane as the open-EDA
  targets; the live tool wiring (as with `sumitsubo`'s kami-kernel binding) is a follow-up.

# Alternatives Considered

1. **Extend `silicon` instead of a new actor.** Rejected: `silicon` is constitutionally the
   *electronic* fab + digital ASIC actor; folding photonics + ISAC + a distinct safety surface into it
   would blur its mandate and its force-class model. A photonic sibling that *shares* the fab/packaging
   lineage but owns its own civilian-force-separation + laser-safety invariants is cleaner.
2. **Three separate actors (chip / isac / robotics).** Rejected: the beacon-fire (烽) insight is that
   communication and sensing are **one** emission, and packaging is what makes the chip real; splitting
   them loses the coupling and triples the manifest/ADR overhead for no gain.
3. **A kami-engine Rust ISAC sim crate.** Deferred: a full kami-engine crate (like kami-autodrive) is
   heavier and lives in the submodule; a stdlib Python JCAS core is self-contained, deterministic, and
   immediately unit-testable here. A kami-engine render/sim integration is a natural R1+ follow-up.
4. **Proprietary photonic EDA (Lumerical/Ansys) for fidelity.** Rejected outright — Charter Rider §2 +
   G1/N5. Open photonic EDA (Meep/MPB, GDSFactory, KLayout) is the only admissible path, as open
   digital EDA was for `iwakura`.

# R1 — Integrations (2026-06-05 follow-up)

Three composition bridges were added, each turning a noroshi face into a wired integration with an
existing actor/engine. All are deterministic + offline-tested (method suite now **50 tests**;
**64 total** with the cell state-machine). They extend, not amend, every R0 invariant.

- **(c) optical-network resilience — noroshi × watatsuna** (`methods/cable_endpoint.py`). noroshi's CPO
  chips sit at the **ends** of watatsuna's submarine-cable **medium**, so each in-service cable's design
  capacity becomes a concrete count of CPO transceiver lanes at each landing station. Aggregating that
  demand behind watatsuna's chokepoint tags reproduces watatsuna's own capacity ranking
  (**luzon-strait → suez-red-sea → malacca → gibraltar**), now expressed as the *transceiver fleet* that
  must be built and **diversified** there. Inherits watatsuna's framing verbatim: resilience (redundant
  endpoints + diverse routes + faster repair), **never a target-list** (watatsumi N8 + Charter Rider
  §2(d)). A full offline join over the present watatsuna seed.
- **(a) ISAC sensor in the GNC loop — noroshi × kami-autodrive** (`methods/kami_isac_bridge.py` +
  `wit/kami-isac.wit`). The ISAC estimator is driven from a kami-autodrive-style moving-object scenario
  to produce per-object range/velocity **tracks** — the `IsacSensor` plant kami-autodrive's perception
  stage (ADR-2606010600) polls each frame for collision-avoidance. The WIT contract encodes the civilian
  shape structurally (object-estimate has no person/identity field; no fire-control op; G3/G4/N1/N2).
  HONEST (G10): the `40-engine/kami-engine` submodule is unpopulated in this checkout, so this is the
  data bridge + interface contract, not a compiled crate (the sumitsubo "op-list now, live binding
  follow-up" pattern). The waveform's coarse velocity bin (Δv≈279 m/s, a 16-symbol frame) is reported
  honestly (N4) — fine automotive velocity needs many more OFDM symbols (a kami-autodrive-side config).
- **(b) PIC layout → budget loop — noroshi × open-EDA** (`methods/pic_layout.py`). A silicon-photonic
  transmitter PIC is emitted as a neutral, GDSFactory-shaped **ModelOp plan** (the sumitsubo CAD
  pattern); the plan's on-chip waveguide length feeds back into `link_budget.py`, closing the
  layout→margin loop. A real GDS is written **only** if the open-source `gdsfactory` is importable, and
  that write is outward-gated (G8); never a proprietary EDA tool, never an NDA foundry PDK (G1/N5). In
  this checkout gdsfactory is absent, so the GDS write is honestly gated and the verifiable artifact is
  the deterministic plan.

Live kami-engine crate wiring, a live gdsfactory GDS write, and a live watatsuna feed remain G8
outward-gated.

# Session close — R0+R1 maturity wave (2026-06-06)

R0+R1 were hardened over a 16-iteration self-paced session: **48 → 203 tests green** (189 methods + 14
cell state-machine), zero invariant amendments, every iteration ending green. The growth was both
**functional** and **verificational**.

Functional maturity added (each verifiable, deterministic, stdlib-only):
- **chip** — BER → receiver-sensitivity physics (Q-factor bisection + thermal-noise model) for **PIN and
  APD** (McIntyre excess-noise F(M), ~6.8 dB gain at M=10, honestly bounded to the thermal-limited
  regime); GDSFactory-shaped **transmitter AND receiver** PIC ModelOp layout feeding the end-to-end budget.
- **isac** — **multi-target** CLEAN extraction, seeded **CA-CFAR** detection-in-noise, and a **Pd-vs-SNR**
  detector operating curve (surfaced in the generated isac report), beyond the original single-target sim.
- **packaging** — **two-stage** acquisition (exhaustive raster OR early-stop expanding-square **spiral**)
  → Hooke-Jeeves refine, robust to a far / narrow-lobe start where a bare gradient method stalls.
- **bridges** — the watatsuna join gained the authoritative `:cable.seg/traverses` physical-crossing view
  (alongside station-tag); the kami-autodrive bridge gained one-shot multi-target `sense_frame`.

Verification systems locked in (8): the verifiable cores; the 3 composition bridges; a **structural
charter-invariant** suite (civilian-only / object-not-person / no-server-key / open-EDA over the parsed
lex+schema+ontology); an **SSoT-consistency** suite (manifest↔files, ontology≡schema, seeds↔schema, and
**seed-VALUE enum/const** enforcement so a forbidden value cannot enter the data); a **lexicon/cell
well-formedness** suite (required⊆properties, every prop typed, cell-gates↔manifest referential integrity,
LLM-cells Murakumo-only); and a **governance/honest-framing** suite (gates/non-goals↔CLAUDE.md doc parity,
no-forbidden-substrate/inference-import, report honesty markers). Plus a hardening pass closing
degenerate-input / route-length / missing-seed / explicit-`0.0`-step gaps. The actor has reached the
maturity ceiling for a design-only R0; further maturity requires the G8-gated physical legs.

# References

- ADR-2605242500 (silicon — electronic fab orchestration + RTL) — sibling, contrast (electronic)
- ADR-2605242515 / 2605242530 (iwakura / fuigo — ternary ASIC; RTL→sky130 GDSII open-EDA flow) — the
  open-EDA precedent extended to photonics
- ADR-2605261300 (tsutae — RF handheld comms device) — RF comms sibling
- ADR-2606012600 (watatsuna — submarine-cable KG) — the optical medium; noroshi = the CPO chips at its ends
- ADR-2606033600 (sumitsubo — clean-room CAD interop) — the G1 clean-room / published-API-shape precedent
- ADR-2606036000 (wasm-actor SBOM) / 2605312330 (giemon part-graph) — the CycloneDX→kotoba SBOM precedent (G11)
- ADR-2605261800 (nv-compat) — vendor-names-in-docstrings clean-room pattern
- ADR-2606010600 (kami-autodrive) — the sensing/GNC sim precedent; ISAC sensing composes with it
- ADR-2606032130 (Displacement Dividend) — G2 coupling for the packaging-robotics fleet
- ADR-2606042330 (entity-as-actor) — `/search` resolvable-actor registration pattern
- ADR-2605215000 (Murakumo-only inference) — G6 · ADR-2605231525 (no-server-key) — G7 ·
  ADR-2605312345 (kotoba Datom first-class canonical state) — G9
- ADR-2605192100 (Mission Charter §1.12 force-separation) — G3/N1 constitutional anchor
