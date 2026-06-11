---
id: adr-2606014000-session-close-funadaiku-zero-emission-cargo-shipbuilding
title: "ADR-2606014000: Session close — funadaiku 船大工 zero-emission cargo shipbuilding (R0 + kami-engine operational voyage sim)"
status: active
doc_type: adr
topic: session-close-funadaiku-zero-emission-cargo-shipbuilding
authoritative: false
last_verified: 2026-06-01
priority: 6.0
axis: architecture
weight: 0.6
priority_note: "Documentation-only session-close for the funadaiku zero-emission autonomous cargo-shipbuilding actor + its kami-engine autonomous voyage simulation"
authoritative_for: []
depends_on:
  - adr-2606013400-funadaiku-zero-emission-cargo-shipbuilding-r0
  - adr-2606010600-kami-autodrive-gnc-autonomy-layer
  - adr-2605252200-watatsumi-civilian-submersible-r0
related:
  - adr-2605242000-etzhayyim-wadachi-autonomous-mobility-rd
  - adr-2606010030-giemon-factory-r0-kami-engine-kotoba-4d-bim
  - adr-2605261100-hikari-energy-tier-b-actor-r0
supersedes: []
superseded_by: []
---

# ADR-2606014000: Session close — funadaiku 船大工 zero-emission cargo shipbuilding

**Status**: active (documentation-only record)
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

Documentation-only session-close record for the 2026-06-01 session that answered
*「貨物運搬用の自動運転船舶の設計と製造工場は設計されているか」* and the follow-up
*「風力・太陽光・水素ベースで貨物造船を」*.

Audit found the pieces but no whole: `kami-autodrive` had `VehicleClass::Ship` +
`ShipHydro` (the autonomy brain, ADR-2606010600) but no cargo vessel or powertrain;
`watatsumi 綿津見` had a mature 9-cell modular-block shipyard but builds submersibles;
`hikari` makes the PV + LFP. None tied an autonomous cargo hull to a zero-emission
powertrain. Authoritative design = **ADR-2606013400**.

# What shipped (per ADR-2606013400)

**R0 — new Tier-B actor `20-actors/funadaiku/`** (船大工, shipwright; surface counterpart
of watatsumi):

- `manifest.jsonld` (DID `did:web:etzhayyim.com:funadaiku`, 9 cells, 14 gates G1–G14,
  12 non-goals N1–N12, R0→R3 roadmap), `CLAUDE.md`, `README.md`.
- **9 Pregel cells** (`steel_block_fabrication` → `grand_block_assembly` →
  `weld_ndt_inspection` → **`powertrain_integration`** → `outfitting` →
  `launch_commissioning` → `sea_trial` + `decarbonization_audit` cross-cut +
  `class_certification_binder` terminal) — import-clean, `RuntimeError` on `.solve()`.
- **9 lexicons** `com.etzhayyim.funadaiku.*` (integer-typed, religious-corp gate clean).
- **Nagi 凪 class** reference design `data/vessel.edn` (wind-assist + solar + PEM H₂
  fuel cell + LFP + electric pods; **no fossil engine**, G13/N5) + `data/shipyard.edn`
  (building dock / panel line / block shops / ATEX-zoned H₂ powertrain bay + routed MEP,
  giemon-factory pattern) + `data/building.edn` SBOM + `data/fleet.kotoba.edn` yard
  robotics + `products.edn` (okaimono Ring-1 catalog).
- **Analytic budget** `methods/voyage_energy.py` (stdlib Admiralty-law) → 200 nm coastal
  leg: **wind 16.0% / solar 1.9% / hydrogen 82.1% / fossil 0.0%**, green-H₂ ≈ 1,039 kg,
  battery 170 min harbour zero-emission.

**Operational simulation (kami-engine)** — the Nagi sails autonomously:

- `40-engine/kami-engine/kami-autodrive/examples/nagi_voyage.rs` drives the `Autopilot`
  + `ShipHydro` GNC through a multi-waypoint coastal course while a reduced-order
  zero-emission powertrain gates available thrust each step and books the energy split.
  No fossil source: when the green budget can't meet commanded thrust the throttle is
  power-limited (slower), never fuel-topped. Captured run: autonomous arrival,
  **hydrogen 84.4% / solar 8.9% / wind-assist 6.6% / fossil 0.0%**
  (`20-actors/funadaiku/out/nagi-voyage-sim.txt`).
- `kami-autodrive/tests/nagi_zero_emission_voyage.rs` — 2 regression tests green; full
  kami-autodrive suite green; all examples build.

# Verification

- Python: `py_compile` clean (9 cells + sim); state-machine transitions exercised; manifest
  + 9 lexicons valid JSON; EDN round-trips; `voyage_energy.py` runs and emits `out/` report.
- Rust: `cargo test -p kami-autodrive` green (incl. 2 new tests), `cargo build --examples` clean,
  `nagi_voyage` example runs to autonomous arrival with fossil = 0.
- lefthook pre-commit green (religious-corp lexicon gate after number→integer fix,
  substrate-boundary, docs registry + graph freshness, e7m-verify).
- Registered in root CLAUDE.md status table + `90-docs/adr/README.md` + `deps.toml`.

# Honest boundary

R0 = design + data-model + simulation ONLY — no steel cut, no hull, no FC stack. The voyage
budget is a reduced-order analytic model (not CFD/sea-keeping); in the kami-engine demo
`ShipHydro` is a small-vessel surrogate (8 m/s, ~2 t) at perception-grid scale — energy
*shares* are scale-invariant, kWh figures are demo-scale. Nagi is coastal scale; ocean VLCC
is out of R0–R3 (G12). Robotics fleet is design-only. All values `:representative`. Live yard /
H₂ bunkering / sea-trial is Council + operator gated (G11/G12).

# Delivery

Committed on `feat/funadaiku-zero-emission-cargo-shipbuilding` (2 commits: R0 `2887a6789`
+ operational sim `29af5fe13`) → **PR #681** (base `main`). A concurrent agent's
`feat/sarutahiko-truck-factory` branch transiently carried a stray copy of the sim commit;
the canonical copy was moved cleanly onto the funadaiku branch via an isolated git worktree
(no force-push), and PR #681 verified to contain both commits + all three sim files.

Authoritative design = **ADR-2606013400**.

# References

- `/90-docs/adr/2606013400-funadaiku-zero-emission-cargo-shipbuilding-r0.md` — master ADR
- `/20-actors/funadaiku/` — actor (manifest, cells, data, methods, products, out)
- `/40-engine/kami-engine/kami-autodrive/examples/nagi_voyage.rs` — operational voyage sim
- `/40-engine/kami-engine/kami-autodrive/tests/nagi_zero_emission_voyage.rs` — regression tests
