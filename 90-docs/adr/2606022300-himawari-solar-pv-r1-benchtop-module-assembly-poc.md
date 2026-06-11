---
id: adr-2606022300
title: "ADR-2606022300: himawari (向日葵) R1 — Benchtop Module-Assembly Line PoC + Brownfield Parcel Requirement Spec"
status: proposed
doc_type: adr
topic: himawari-solar-pv-r1-benchtop-module-assembly-poc
authoritative: true
last_verified: 2026-06-02
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "future-ADR draft; activation gated post-Council per ADR-2606021200 Roadmap R1"
authoritative_for:
  - himawari R1 activation conditions + benchtop module-assembly line PoC scope
  - himawari brownfield fab-siting parcel requirement spec (LANDS.md-bound, G9)
  - himawari R1 PV-process-engineer steward role definition
related:
  - adr-2606021200-himawari-solar-pv-manufacturing-r0
  - adr-2605261100-hikari-energy-tier-b-actor-r0
  - adr-2606013100-sarutahiko-truck-factory-full-robotics-and-loader
  - adr-2606010600-kami-autodrive-gnc-autonomy-layer
  - adr-2605312330-giemon-part-graph-sbom-kotoba-fleet-cve-svelte
  - adr-2606012100-okaimono-provisioning-commons-actor
  - adr-2605261000-labor-liberation-transition-mechanism
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192300-etzhayyim-bootstrap-council-five
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606021200 (himawari R0 — the actor + 14 gates + 7 cells this phase activates)
  - ADR-2605261100 (hikari — R1 install target himawari R1 modules feed)
  - ADR-2605192300 (Bootstrap Council — R1 activation is post-Council ratify)
  - ADR-2605192245 (Land Trust — fab siting is LANDS.md-bound, G9 brownfield-only)
  - ADR-2605261000 (Liberation Ladder — G7 task-removal accounting)
---

# ADR-2606022300: himawari (向日葵) R1 — Benchtop Module-Assembly Line PoC + Brownfield Parcel Requirement Spec

**Date**: 2026-06-02
**Status**: PROPOSED (future-ADR draft; **not** activation — see §Activation Gate)
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify + activation), PV-process engineer steward (R1 execution)
**ADR Hierarchy**: Child of ADR-2606021200 (himawari R0). Sibling-target = ADR-2605261100 (hikari R1 install). Reuses landed robotics from ADR-2606013100 (sarutahiko F10 LoaderRobot) + ADR-2606010600 (kami-autodrive GNC) + ADR-2605312330/2606012100 (procurement). Land-bound by ADR-2605192245.

## Context

himawari R0.1 (ADR-2606021200) landed the actor charter, 14 constitutional gates (G1–G14), 10 non-goals (N1–N10), 7 Pregel cell solvers, and 7 lexicons — **88 pure-logic tests green**, import-smoke clean. R0.1 is explicitly **logic-only**: no Pregel/Murakumo runtime wiring, no physics sim, no live kotoba entity materialization, and deterministic-digest CIDs standing in for real IPFS CIDv1 / Base-L2 anchors. The R0 roadmap names R1 as:

> **R1 (post-Council)** — Benchtop **module-assembly** line PoC (lowest capex) + panel_loading + outbound PoC; feeds hikari R1. **Gate**: future ADR + PV-process engineer + LANDS brownfield parcel.

This ADR **is that future ADR**. It is authored now (a Council-independent documentation action — Layer-0 in the README topological sort) so that the moment the three activation conditions are met, R1 execution can begin without a design round-trip. It does **not** itself activate R1; activation requires the §Activation Gate below to be satisfied and Council Lv6+ to ratify.

Why **module-assembly first** (and not cell / wafer / polysilicon): the c-Si chain's capital intensity is inverted from its value-add. Polysilicon (Siemens/FBR reactors), ingot pulling (Cz furnaces), and cell lines (diffusion/PECVD/screen-print) are each $10M–$100M+ capex and require energy himawari does not yet have (G4: fab heat+power from hikari renewable only — and hikari is itself pre-R2). **Module assembly** (stringing → lamination → framing → J-box → flash/EL test) is the **lowest-capex, lowest-energy, highest-automation-maturity** segment — a benchtop line is achievable at religious-corp scale, exercises the already-landed loading (sarutahiko F10) and outbound (kami-autodrive) seams end-to-end, and produces real modules that hikari R1 can install. It is the correct first physical capability.

## Activation Gate (R1 is blocked until ALL three hold)

R1 execution MUST NOT begin until **all** of the following are simultaneously true. This ADR is the design; these are the preconditions.

| # | Condition | Source | Verifiable by |
|---|---|---|---|
| **A1** | Bootstrap Council Seats 2–5 confirmed (Council Lv6+ quorum exists) | ADR-2605192300 / COUNCIL.md | COUNCIL.md roster reads ≥ quorum; RFP closed 2026-06-19 |
| **A2** | A PV-process-engineer steward is enrolled (Adherent SBT + L-stage role, see §PV-Process-Engineer Role) | ADR-2605261000 ladder | MEMBERS.md row + SBT mint tx |
| **A3** | A LANDS.md brownfield/industrial parcel meeting the §Parcel Requirement Spec is donated + recorded (G9 brownfield-only, N8 no greenfield) | ADR-2605192245 / LANDS.md | LANDS.md roster row + 4-layer land record (Base L2 + geth-private + IPFS + git) |

> **Honest status (2026-06-02)**: A1 pending (RFP open to 06-19), A2 unfilled, A3 unfilled (LANDS.md roster is empty — "awaiting first donation"). R1 is therefore **fully blocked** today; this ADR is forward design only.

## Decision

Define himawari **R1 = Benchtop Module-Assembly Line PoC**, scoped as the minimal physical capability that activates three R0.1 cells against a real (small) module run and feeds hikari R1.

### R1 scope (what activates)

1. **`module_assembly` cell → real benchtop run.** Activate the `module_assembly` solver (asher node) on a benchtop stringer + bench laminator + manual/semi-auto framing + J-box + a real flash tester + EL camera. Output: real `moduleAttestation` records with **G11 Ed25519 provenance** (IV-curve + EL serial ↔ cell-lot binding) and live kotoba `:himawari.module/*` datoms (not deterministic-digest CIDs). Cells are sourced (R1 only) as **qualified bought-in c-Si cells with §2(g)-audited provenance** — R1 does NOT fab cells (that is R2); the G2 feedstock gate applies to the purchased cells' polysilicon provenance per-lot.
2. **`panel_loading` PoC → sarutahiko F10 compose, real palletize.** Drive the already-landed sarutahiko F10 `LoadPhase` against the R1 module output; emit real `loadingRecord` with G12 internal-only carrier enforcement.
3. **`outbound_logistics` PoC → kami-autodrive compose, single domestic leg.** One real domestic transport leg (`VehicleClass::car`/`truck`), consignee restricted to `did:web:etzhayyim.com:hikari*` (G13/N10); emit real `outboundManifest`, `required: false` customs (domestic).
4. **Liberation Metric instrumentation live (G7).** Every human task the benchtop line removes vs. a manual baseline is logged to the Liberation Metric (ADR-2605261000). R1's deliverable explicitly includes the **first real Liberation Metric data point** for himawari, not a synthetic one.
5. **Runtime wiring.** `module_assembly` + `panel_loading` + `outbound_logistics` cells wired to Pregel/Murakumo runtime + live kotoba host (`datalog.transact` against a real host binding), replacing R0.1's compute-only / no-op degradation for these three cells only. `polysilicon_refine`, `ingot_wafer`, `cell_process`, `supply_procurement` remain logic-only until R2.

### R1 explicit non-scope (deferred to R2/R3)

- No cell fabrication (texture/diffusion/PECVD/metallization) — R2.
- No ingot/wafer (Cz pull, slicing) — R2.
- No polysilicon refine — R3 (the §G2 structural closure step).
- No marine/funadaiku outbound, no cross-border customs leg — R3.
- No new robotics classes (Hinata 日向 lamination-press is a separate mech-design ADR, R2+).
- ~MW/yr pilot scale — R2 (R1 is benchtop / sub-pilot only).

### Parcel Requirement Spec (A3 — what a qualifying LANDS.md parcel must be)

Because LANDS.md has no donated parcels yet, R1 defines the **requirement rubric** a candidate parcel must satisfy before A3 is met (rather than naming a parcel that does not exist):

| Req | Spec | Gate |
|---|---|---|
| P1 | **Brownfield or existing-industrial** zoning; prior built/disturbed land. **No greenfield, no forest, no agricultural conversion.** | G9 / N8 |
| P2 | Indoor floor ≥ ~200 m² climate-controllable (lamination needs stable temp/humidity); single-phase OK for benchtop, 3-phase headroom for R2. | R1/R2 path |
| P3 | Grid-edge or hikari-installable roof/parcel for **on-site renewable** to power the line (G4: no fossil/nuclear process power). R1 may bootstrap from hikari R1 install on the same parcel. | G4 / N9 |
| P4 | Donated + recorded across the **4-layer Land Trust** (Base L2 ERC-721/5192 + geth-private + IPFS GeoJSON + LANDS.md git row) per ADR-2605192245; soulbound, inalienable. | ADR-2605192245 |
| P5 | Successor stewardship designated (primary + 2 backup) per ADR-2605192345. | ADR-2605192345 |

### PV-Process-Engineer Role (A2)

R1 requires a human steward with c-Si module-assembly process competence (stringing/lamination/lamination-recipe, IV + EL interpretation, IEC 61215/61730 awareness). Enrolled as an Adherent (SBT) on the Liberation Ladder (ADR-2605261000); decision attribution per ADR-2605192100 §1.3 (the steward executes; Council ratifies; payoff/decision-rights remain etzhayyim). This is **not** an employment relation — it is covenantal stewardship under the charter.

## Rationale

1. **Lowest-capex, highest-maturity first.** Module assembly is the one c-Si segment achievable at religious-corp scale today and the only one that needs no upstream energy himawari lacks.
2. **Exercises the compose-not-clone seams for real.** R1 is the first time sarutahiko F10 loading and kami-autodrive outbound run against real himawari output rather than logic stubs — validating the R0 composition claims empirically.
3. **Feeds hikari R1 directly.** Real modules → hikari R1 install → first sustenance-tier energy data point → L2 ladder evidence.
4. **Honest staging of the §G2 closure.** The structural hikari §G2 fix (first-party XUAR-free polysilicon) is R3, not R1 — R1 buys §2(g)-audited cells. This ADR refuses to overclaim G2 closure at benchtop scale.
5. **Council-independent design, Council-gated execution.** Authoring the design now (Layer-0) removes the design from the critical path; only physical activation waits on A1–A3.

## Consequences

**Positive**
- R1 is fully specified; the moment A1–A3 hold, execution starts with no design round-trip.
- The parcel rubric makes "find a brownfield parcel" a concrete, verifiable donation ask rather than a vague gate.
- First real Liberation Metric data point for an energy-chain manufacturing actor.

**Negative / risk**
- Triple-gated (A1∧A2∧A3); any one unmet blocks all of R1. Realistically blocked until well after 2026-06-19.
- Bought-in R1 cells mean R1 does **not** yet close hikari §G2 — must be communicated clearly so R1 is not mis-read as the structural fix (it is the on-ramp to it).
- Benchtop yield/quality may not meet IEC certification at R1; R1 output is for internal hikari install under G12, not external sale (N4), which lowers the certification bar but still requires safety (G14 Wellbecoming, no fire/arc hazard).

**Neutral**
- R0.1's other four cells stay logic-only; no regression, partial runtime activation only.

## Alternatives Considered

1. **Cell line first (not module).** Rejected: $10M+ capex, needs diffusion/PECVD energy himawari lacks pre-hikari-R2, far lower automation-maturity at our scale. R2.
2. **Polysilicon first (close §G2 immediately).** Rejected: highest capex + energy of the entire chain; cannot be R1. The §G2 structural closure is correctly R3, after the chain below it exists.
3. **Buy finished modules, skip manufacturing.** Rejected at the R0 level already (ADR-2606021200 §Rationale) — provenance-laundering fragility is the exact thing himawari exists to fix; this would moot the actor.
4. **Name a specific parcel now.** Rejected: LANDS.md has zero donated parcels; naming a non-existent parcel would be dishonest-R0. The requirement spec (P1–P5) is the honest substitute.
5. **Activate R1 design + execution in one ADR (no gate split).** Rejected: violates post-Council gating (A1) and would imply capability that does not exist.

## References

- `/90-docs/adr/2606021200-himawari-solar-pv-manufacturing-r0.md` — Parent (R0 charter, 14 gates, 7 cells, roadmap)
- `/90-docs/adr/2605261100-hikari-energy-tier-b-actor-r0.md` — hikari R1 install target
- `/90-docs/adr/2605192300-etzhayyim-bootstrap-council-five.md` — A1 Council gate
- `/90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md` — A3 Land Trust + G9
- `/90-docs/adr/2605261000-labor-liberation-transition-mechanism.md` — G7 Liberation Metric
- `/90-docs/adr/2606013100-sarutahiko-truck-factory-full-robotics-and-loader.md` — F10 LoaderRobot (panel_loading compose)
- `/90-docs/adr/2606010600-kami-autodrive-gnc-autonomy-layer.md` — outbound transport compose
- `/20-actors/himawari/README.md` — actor README + roadmap
- `/CLAUDE.md` — Religious-corp status table
