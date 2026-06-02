---
id: adr-2606013400-funadaiku-zero-emission-cargo-shipbuilding-r0
title: "ADR-2606013400: funadaiku 船大工 — zero-emission (wind + solar + hydrogen) autonomous cargo-ship building Tier-B actor (R0)"
status: proposed
doc_type: adr
topic: funadaiku-zero-emission-cargo-shipbuilding
authoritative: true
last_verified: 2026-06-01
priority: 6.5
axis: architecture
weight: 0.65
priority_note: "Surface zero-emission autonomous cargo-ship building actor; sibling of watatsumi (submersible); wind-assist + solar + hydrogen fuel-cell powertrain; reuses kami-autodrive ShipHydro GNC"
authoritative_for:
  - funadaiku actor (zero-emission autonomous cargo shipbuilding)
  - Nagi 凪 class coastal zero-emission cargo carrier reference design
  - com.etzhayyim.funadaiku.* lexicons
  - funadaiku shipyard plant (kami-engine + kotoba EAVT)
depends_on:
  - adr-2605252200-watatsumi-civilian-submersible-r0
  - adr-2606010600-kami-autodrive-gnc-autonomy-layer
  - adr-2606010030-giemon-factory-r0-kami-engine-kotoba-4d-bim
  - adr-2605242000-etzhayyim-wadachi-autonomous-mobility-rd
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2606012600-watatsuna-submarine-cable-knowledge-graph-and-watatsumi-cable-laying-robotics
  - adr-2605252500-sarutahiko-heavy-truck-manufacturing-r0
  - adr-2605250715-tatekata-construction-tier-b-actor-r0
  - adr-2605261100-hikari-energy-tier-b-actor-r0
  - adr-2606012100-okaimono-provisioning-commons-actor
  - adr-2605301020-basic-high-income-doctrine
supersedes: []
superseded_by: []
---

# ADR-2606013400: funadaiku 船大工 — zero-emission autonomous cargo-ship building (R0)

**Status**: proposed
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

The founder asked whether the repo has **designed the cargo-carrying autonomous ship and
the factory that builds it**, and — given a survey of solar / hydrogen / wind-assist marine
propulsion maturity — to **build the cargo shipbuilding on a wind + solar + hydrogen base**.

Audit of the repo found the pieces but no whole:

- **`kami-autodrive`** (ADR-2606010600) has `VehicleClass::Ship` with a real `dynamics::ShipHydro`
  (Fossen 3-DOF surge/sway/yaw, added mass, quadratic damping, rudder) and a full
  perception→planning→control GNC loop — i.e. the **autonomous-navigation brain** exists, but
  as a generic planar-kinematic ship, not a cargo vessel and with no powertrain.
- **`watatsumi 綿津見`** (ADR-2605252200) is a *submersible* manufacturer with a mature 9-cell
  modular ring-section shipyard line (hull fab → assembly → NDT → integration → joining →
  pressure test → sea trial → emissions audit → class certification). It is the closest
  sibling but builds pressure hulls for deep-sea craft, not surface cargo carriers, and its
  G13 already restricts propulsion to **LFP / H₂ / NH₃ / methanol fuel-cell only**.
- **`sarutahiko`** (truck mfg), **`tatekata`** (construction), **`giemon factory`** (ADR-2606010030,
  whole-plant 4D-BIM layout + MEP + SBOM in kami-engine + kotoba) establish the **factory-as-actor**
  pattern.
- **`hikari`** (energy) already produces the components a zero-emission ship needs (LFP storage,
  PV) and lists them in `products.edn`.

No actor builds **surface cargo ships**, and none ties the autonomy brain to a **zero-emission
powertrain**. The user's own propulsion survey is the design brief:

| Tech | Maturity | Best fit | Weakness |
|---|---|---|---|
| Solar PV | medium | small / coastal / inland / hotel-load | low areal power; insufficient as sole main propulsion |
| Hydrogen FC | medium–high | ferries, harbour, short-sea, future cruise | storage volume, bunkering infra, cost, safety |
| Wind-assist (rotor/wing/kite) | high | cargo / tanker / bulker / ferry fuel-saving | wind-dependent; cannot be sole prime mover |

The empirically honest conclusion (matching real 2024–2025 deployments — hybrid solar inland
freighters, 50 hydrogen vessels built/converted as of Nov 2024 e.g. *Sea Change* / *まほろば*,
and Wind-Assisted Propulsion retrofits on tankers/bulkers/Ro-Ro) is that **no single source is
a complete prime mover**. The design must be a **hybrid: wind-assist + solar + hydrogen
fuel-cell + LFP battery + electric pod drive**, sized to route/speed/bunkering, with the
decarbonization claim evaluated **well-to-wake** (green H₂ chain-of-custody), not tank-to-wake.

# Decision

Create **`funadaiku 船大工`** (shipwright) — a **Tier-B actor that designs and builds
zero-emission autonomous cargo ships**. It is the **surface counterpart of `watatsumi`**
(綿津見 submersible ↔ 船大工 surface cargo), reuses watatsumi's proven modular-block shipyard
methodology and the `kami-autodrive` ShipHydro GNC, and adds the **wind + solar + hydrogen
powertrain** as its defining, constitutional subsystem.

## Reference vessel — Nagi 凪 class

A **coastal / short-sea zero-emission autonomous cargo carrier** (honest, achievable scale;
NOT a 200,000 DWT ocean VLCC at R0):

- **Hull**: ~3,000 DWT general cargo, LOA ≈ 90 m, beam ≈ 15 m, design speed ≈ 10 kn (service),
  steel hull (recyclable, hodoki/kanayama EOL route).
- **Wind-assist (primary fuel-saver)**: 2 × 24 m rotor sails (Flettner) OR rigid wing sails,
  route-and-weather-optimised; contributes thrust, never the sole prime mover.
- **Solar deck**: ~800 m² PV on weather deck + hatch covers ≈ 160 kWp (hikari `solar-pv-400w`);
  serves hotel/auxiliary load and battery top-up, not high-speed main propulsion.
- **Hydrogen fuel cell (electrical prime mover)**: PEM FC genset ≈ 2 × 1.2 MW; compressed
  (350 bar) or liquid H₂ store; **green-H₂ chain-of-custody mandatory** (G14).
- **Battery buffer**: LFP ≈ 2 MWh (hikari `storage`) for peak-shaving, harbour
  zero-emission manoeuvring, and wind/solar smoothing.
- **Drive**: 2 × 1.5 MW electric azimuth pods.
- **Autonomy**: IMO MASS **Degree 3 (remote-controlled, no crew)** baseline; Degree 4
  (fully autonomous) Council-gated. GNC = `kami-autodrive` ShipHydro + COLREG layer.

**There is no fossil main or auxiliary engine.** That is the constitutional point (G13/N5).

## Shipyard — funadaiku yard

The plant that builds the Nagi class, modelled in **kami-engine + kotoba EAVT** exactly like
`giemon factory` (ADR-2606010030): building dock, panel line, curved/flat block shops, grand-block
erection area, outfitting quay, paint shed, H₂-safe powertrain integration bay (ATEX-zoned), plus
routed MEP (power / compressed air / cooling water / **H₂ + N₂ purge** / fire). Construction is
the **modular block / grand-block** method inherited from watatsumi, scaled to a surface hull.

## 9 Pregel cells (L1→L5 + cross + terminal)

Mirrors watatsumi's proven line, re-targeted to a surface cargo hull and a zero-emission powertrain:

1. `steel_block_fabrication` (L1) — panel line + curved/flat block + sub-assembly
2. `grand_block_assembly` (L2) — grand-block erection + block joining on the building dock
3. `weld_ndt_inspection` (L3) — 100% NDT (RT/UT/PT) on hull seams
4. `powertrain_integration` (L4) — **wind-assist rig + solar array + H₂ fuel cell + LFP battery
   + electric pod + autonomous GNC** (the zero-emission heart)
5. `outfitting` (L5a) — cargo systems, hatch covers, coatings, accommodation, autonomy sensor suite
6. `launch_commissioning` (L5b) — float-out + inclining test + dock trial
7. `sea_trial` (L5c) — speed / endurance / autonomy (MASS) / COLREG trial
8. `decarbonization_audit` (cross-cutting) — MARPOL Annex VI + EEXI + CII + IMO GHG
   **well-to-wake** zero-emission verification incl. green-H₂ chain-of-custody
9. `class_certification_binder` (terminal) — class society (DNV / ABS / NK / BV equivalent) +
   IMO MASS autonomous-ship code audit binder, kotoba-anchored

# Constitutional Gates (G1–G14, immutable R0–R3; Council Lv6+ to amend)

- **G1** Hull CAD + FEA + GNC firmware open-source (Apache 2.0 + Charter Rider).
- **G2** Every class-certification stage anchored on kotoba (DNV/ABS/NK/BV equivalent).
- **G3** Every weld pass + test step IPFS-pinned photo + video (ADR-2605241500).
- **G4** Witness quorum ≥2 distinct robots per critical weld (Ed25519, DID-bound; ADR-2605191524).
- **G5** JP + EN bilingual minimum for all class reports / permits / owner's manuals.
- **G6** Charter Rider §2(a–h) scan on every CAD + firmware artifact.
- **G7** Autonomy ≤ IMO MASS **Degree 3** baseline (SAE-equiv L4 ceiling, mirrors wadachi);
  Degree 4 fully-unmanned is Council-gated (N10).
- **G8** Navigation/obstacle sonar ≤180 dB re 1µPa @1m (NMFS cetacean Level A).
- **G9** CAD only from vendor-free tools (FreeCAD / OpenSCAD / Open CASCADE / first-party).
- **G10** Inference paths use Murakumo no-VKE mesh only (ADR-2605214000 / ADR-2605215000).
- **G11** Hot-work / launch / sea-trial / H₂ bunkering ops are SBT-gated personnel.
- **G12** KPI caps (R0–R3): ≤5,000 DWT, ≤14 kn service speed, MASS ≤ Degree 3. Council Lv6+ to amend.
- **G13 (defining)** **Zero-emission propulsion ONLY**: wind-assist + solar + H₂ / NH₃ / methanol
  fuel-cell + LFP battery + electric drive. **No fossil main or auxiliary engine; no HFO / MGO /
  LNG-as-fuel.** Constitutional — this is the whole purpose of the actor.
- **G14** MARPOL Annex VI + EEXI + CII + IMO GHG strategy, evaluated **well-to-wake**; H₂ / NH₃ /
  methanol must carry a **green (renewable) production chain-of-custody attestation** — a ship
  burning hydrogen made from fossil power is not zero-emission (the lifecycle-optimisation point).

# Non-Goals (N1–N12, constitutional, immutable R0–R3)

- **N1** Naval / armed vessels — gun mounts, missile/torpedo stowage, military sealift as a design driver. §2(a).
- **N2** Nuclear propulsion. §2(g) + §1.15.
- **N3** Military stealth / covert / grey-hull / low-observable vessels. §2(a) + §2(d).
- **N4** Warship hull forms or naval-auxiliary primary design.
- **N5** Fossil-fuel main or auxiliary propulsion (HFO / MGO / diesel / LNG-as-fuel). Reinforces G13.
- **N6** Flag-of-convenience / tax-avoidance registration engineering.
- **N7** IUU-fishing support, ocean dumping, at-sea waste incineration.
- **N8** Beaching-yard ship-breaking (Alang/Chittagong-style). EOL routes hodoki + kanayama green recycling.
- **N9** Ballast-water invasive-species transfer (BWMC violation by design).
- **N10** MASS Degree 4 fully-unmanned autonomy without independent Council review. Caps G7.
- **N11** Dark-fleet / sanctions-evasion operation (AIS spoofing, STS transfer concealment). §2(d).
- **N12** Speed-record / vanity priority over voyage-energy efficiency. §1.13 wellbecoming.

# Roadmap

| Phase | Date | Scope | Gate |
|---|---|---|---|
| **R0** | 2026-06-01 | Scaffold + reference design. No physical fabrication. 9 cells import-clean, RuntimeError on `.solve()`. 9 lexicon stubs. Nagi-class `vessel.edn` + `shipyard.edn` + `building.edn` + voyage energy-budget sim. | ADR-2606013400 (this, proposed) |
| **R1** | post-Council | Scale-model hull + powertrain HIL bench (rotor-sail rig + PV string + FC stack + LFP), pool/tank GNC. Naval-architect + marine-FC SME onboarded. | reserved ADR-2606013415 |
| **R2** | post-R1 | Pilot harbour-craft / inland zero-emission cargo, MASS Degree 2 supervised. tatekata-shared yard pilot. | reserved ADR-2606013430 |
| **R3** | post-R2 | Nagi-class coastal cargo, full class + MASS Degree 3 certification, green-H₂ bunkering partner. 60-day public review. | reserved ADR-2606013445 (multi-actor Council vote: funadaiku + hikari + watatsumi) |

# Consequences

**Positive**: closes the "cargo ship + shipyard" gap with the autonomy brain (kami-autodrive)
and the energy components (hikari) already in-repo; the powertrain is constitutionally
zero-emission; the vessel and the yard are both first-class kotoba EAVT data; delivers a
producing actor for okaimono (zero-emission freight as an internal service) and a concrete
Labor-Liberation / Basic-High-Income-in-kind logistics capability.

**Operational simulation (landed)**: beyond the analytic budget, the Nagi class sails
autonomously in kami-engine — `40-engine/kami-engine/kami-autodrive/examples/nagi_voyage.rs`
drives the `Autopilot` + `ShipHydro` GNC through a multi-waypoint coastal course while a
reduced-order zero-emission powertrain (wind-assist + solar + H₂ FC + LFP) gates the available
propulsion power each step and books the energy split. No fossil source exists; when the green
budget can't meet commanded thrust the throttle is power-limited (slower), never fuel-topped.
Captured run: autonomous arrival, **hydrogen 84.4% / solar 8.9% / wind-assist 6.6% / fossil
0.0%** (`20-actors/funadaiku/out/nagi-voyage-sim.txt`). Regression test
`kami-autodrive/tests/nagi_zero_emission_voyage.rs` (2 tests) green; full kami-autodrive suite green.

**Honest R0 limits**: design + data-model + simulation ONLY — no steel cut, no hull, no FC
stack. In the kami-engine demo `ShipHydro` is a small-vessel surrogate (8 m/s, ~2 t) at
perception-grid scale — the energy shares are scale-invariant, the kWh figures are demo-scale. The voyage energy budget is a reduced-order analytic model (areal solar yield, rotor-sail
thrust coefficient curve, FC efficiency, drag-power), not CFD/sea-keeping. `kami-autodrive`
ShipHydro provides 3-DOF planar GNC, not 6-DOF sea-keeping — full marine CFD is deferred. The
Nagi class is coastal/short-sea scale; ocean VLCC scale is explicitly out of R0–R3 (G12).
Robotics fleet is design-only. All numbers are `:representative`. Live yard / bunkering / sea
trial is Council + operator gated (G11/G12).

# References

- `/20-actors/funadaiku/manifest.jsonld` — DID + cell registry + gates + non-goals
- `/20-actors/funadaiku/data/vessel.edn` — Nagi-class reference design (kotoba EAVT)
- `/20-actors/funadaiku/data/shipyard.edn` — yard plant
- `/20-actors/funadaiku/methods/voyage_energy.py` — wind/solar/hydrogen energy-budget sim
- `/90-docs/adr/2605252200-watatsumi-civilian-submersible-r0.md` — submersible sibling (block-shipyard methodology, G13)
- `/90-docs/adr/2606010600-kami-autodrive-gnc-autonomy-layer.md` — ShipHydro GNC
- `/90-docs/adr/2606010030-giemon-factory-r0-kami-engine-kotoba-4d-bim.md` — factory-as-actor pattern
- `/CHARTER-RIDER.md` — license addendum (§2(a) weapons, §2(d) infrastructure attack non-goals)
