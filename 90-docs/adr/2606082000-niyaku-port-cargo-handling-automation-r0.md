---
id: adr-2606082000-niyaku-port-cargo-handling-automation-r0
title: "ADR-2606082000: niyaku 荷役 — automated port cargo handling (ship↔shore loading/unloading) Tier-B actor (R0)"
status: proposed
doc_type: adr
topic: niyaku-port-cargo-handling-automation
authoritative: true
last_verified: 2026-06-08
priority: 6.5
axis: architecture
weight: 0.65
priority_note: "Port-side loading/unloading automation; operator counterpart of funadaiku (builds the ships); anti-sway crane control verified through clean-room isaacsim.core.api Cartpole; closes the cargo-handling roster gap"
authoritative_for:
  - niyaku actor (automated port cargo handling — ship↔shore container loading/unloading)
  - anti-sway STS/gantry crane control mapped to the Cartpole topology
  - com.etzhayyim.niyaku.* lexicons
depends_on:
  - adr-2606013400-funadaiku-zero-emission-cargo-shipbuilding-r0
  - adr-2605261800-nvidia-omniverse-compat-kami-engine
  - adr-2606010600-kami-autodrive-gnc-autonomy-layer
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2606062100-charter-priority-over-specifics-3tier
related:
  - adr-2606012600-watatsuna-submarine-cable-knowledge-graph-and-watatsumi-cable-laying-robotics
  - adr-2606041827-watari-live-ship-aircraft-position-knowledge-graph
  - adr-2605252500-sarutahiko-heavy-truck-manufacturing-r0
supersedes: []
superseded_by: []
---

# ADR-2606082000: niyaku 荷役 — automated port cargo handling (R0)

**Status**: proposed
**Date**: 2026-06-08
**Deciders**: Jun Kawasaki

# Context

The roster had a zero-emission cargo-ship **builder** (funadaiku 船大工,
ADR-2606013400), a port **registry** (`port`, 35+ terminals/berths), and a live
vessel-**position** mirror (watari 渡り). It had **no actor that automates the
loading and unloading of those ships** — the port-side robotics gap was explicit
(surfaced 2026-06-08).

The defining technical problem of container handling is **anti-sway**: a
ship-to-shore (STS) crane lifts a 20–40 t container on cables and traverses it
30–65 m between hull and quay; the suspended load is a pendulum and cannot be
landed on a stack tier until residual sway settles to a few centimetres.
Dynamically this is the **cart + hanging load** system — the *same topology* the
kami-engine clean-room mirror ships as Isaac Sim's **Cartpole** (prismatic
trolley + revolute load, ADR-2605261800). That mapping makes a verifiable,
NVIDIA-free crane simulation possible today.

# Decision

Introduce **niyaku 荷役** as a Tier-B actor (`did:web:etzhayyim.com:niyaku`),
the operator-side counterpart of funadaiku.

**Scope (R0):**

1. **Three runnable, pure-stdlib / pywasm-ready methods** (`20-actors/niyaku/methods/`):
   - `crane_dynamics.py` — RK4 hanging-pendulum-on-trolley model, state-feedback
     anti-sway controller, ZV input-shaper, per-box cycle-time → moves/hour.
   - `stow_plan.py` — bay/row/tier slotting under weight-on-top + port-rotation
     (no-rehandle) + reefer-row + IMDG hazmat segregation; discharge sequencing.
   - `isaac_sway_sim.py` — drives the clean-room `isaacsim.core.api`
     (`kotodama.nv_compat`) Cartpole with the load at the stable hanging
     equilibrium (θ=π); anti-sway state feedback lands the box quiet
     (residual < 0.01 rad) where a naive position push diverges. Emits kotoba
     EAVT datoms. Skips gracefully when the kotoba submodule is absent.
2. **Nine Pregel cells** (`berth_allocation` → `stowage_planning` →
   `spreader_engagement` → `sts_hoist_cycle` → `trolley_traverse` →
   `yard_transfer` → `lashing_twistlock` → `manifest_attestation`, with
   `emissions_audit` cross-cutting). R0 scaffold: `.solve()` raises until R1.
3. Manifest, `lex/moveAttestation.edn`, reference `data/terminal.edn`.

**14 constitutional gates** (manifest): G1 open-source control · **G2 clean-room
sim only — no NVIDIA Isaac binary/header/library** · G3 ≥2-robot witness per lift
· G4 anti-sway safety envelope · G5 Murakumo-only · G6 kotoba-EAVT-native · G7
tithe non-fiat · **G8 zero-emission electric cranes** (regenerative lowering
credited) · G9 IMDG/weight/rotation stow feasibility · **G10 no
weapons/military-materiel cargo** (Charter Rider §2(a)) · G11 moves/hour KPI, not
a worker-pace ranking · G12 no-server-key (methods move no real crane) · G13
consent-bound (compute-only) · **G14 no worker biometric/pace surveillance**.

**R1 activation** (live actuation, real crane/AGV) is reserved to a future
Council-gated ADR-2606082015.

# Consequences

- The cargo-logistics chain is now end-to-end in the repo: funadaiku **builds**,
  niyaku **loads/unloads**, watari/watatsuna **position/route**, port
  **registers**.
- 27 tests green at R0 (24 methods incl. 6 clean-room Isaac, 3 cell-state-machine).
- The Cartpole↔crane mapping gives a real, runnable "to Isaac Sim" deliverable
  without any NVIDIA dependency (G2).
- R0 is compute-only; nothing actuates real equipment (G12/G13).

# Alternatives Considered

- **Fold handling into funadaiku.** Rejected — building a ship and operating a
  terminal are distinct domains with distinct gates (builder witness vs lift
  witness, MARPOL vs IMDG); siblings, not nested (same rationale as
  sarutahiko ⟂ wadachi).
- **Full Featherstone n-link crane in kami-genesis.** Deferred — the Cartpole
  topology already captures the dominant anti-sway dynamics and is the supported
  clean-room surface today; richer multi-body sim is an R1.5 kami-genesis item.
- **Vendor terminal-OS adapter (e.g. TOS) compat.** Deferred to a later compat
  actor; R0 is the physics + planning core, not a vendor integration.

# References

- `20-actors/niyaku/` — actor (manifest, 9 cells, 3 methods, lex, data)
- ADR-2606013400 — funadaiku (the ship builder this actor serves)
- ADR-2605261800 — NVIDIA Omniverse compat (clean-room `isaacsim.core.api`)
- ADR-2606010600 — kami-autodrive GNC autonomy
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/nv_compat/isaacsim/` — Isaac mirror
