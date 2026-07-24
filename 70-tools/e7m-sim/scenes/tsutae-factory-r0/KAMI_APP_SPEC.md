# kami-app-tsutae-factory — crate spec (the last parity gap)

**Status:** NOT YET BUILT — blocked on kami-engine submodule source.

This documents the Rust `kami-app-tsutae-factory` crate that completes parity with
`kami-app-sarutahiko-factory` (ADR-2606013100) / `kami-app-giemon-factory`
(ADR-2606010030). Everything else in tsutae's parity uplift is done (cells +
manifest + lex + py + kotoba + the full `tsutae-factory-r0` scene + toolchain);
this crate is the only remaining piece.

## Why it isn't in this commit

The crate belongs in the **kami-engine submodule** (`40-engine/kami-engine`, per
ADR-2606011500 §4 — robotics/sim apps are maintained upstream). In the current
checkout that submodule contains only built `pkg/` artifacts (compiled `.wasm` +
`.js` + `.htm`); it has **no Rust workspace source** (0 `Cargo.toml`, 0 `.rs`), and
`git submodule update --init` cannot repopulate it (directory non-empty). So the
crate cannot be authored or compiled here without first restoring the kami-engine
source. A standalone, no-build viewer (`tsutae-factory.htm`, see `viz_gen.py`) ships
the user-facing visualization in the meantime.

## What to build (mirror kami-app-sarutahiko-factory)

Crate location (upstream): `kami-engine/kami-app-tsutae-factory/`

```
kami-app-tsutae-factory/
├── Cargo.toml          # wasm-bindgen + kami-genesis + kami-engine-sdk deps
├── src/lib.rs          # 3 #[wasm_bindgen] entry points (below)
└── pkg/tsutae-factory.htm   # thin loader (import init, run_*; calls into wasm)
```

### WASM entry points (already referenced by the scene/toolchain)

| Entry | Drives | Reads |
|---|---|---|
| `run_tsutae_factory_v1(canvas)` | live cleanroom render | `factory.scene.json` |
| `run_tsutae_factory_build_v1(canvas)` | 4D construction replay | `construction.order.json` (15 steps) |
| `run_tsutae_factory_produce_v1(canvas)` | device flows the line | `production.order.json` (12 stations) |

`production_gen.py` / `kotoba_gen.py` already emit these JSON orders, and
`production.edn` / `construction.edn` already name the `run_tsutae_factory_*_v1`
entries — so the data contract is fixed and stable.

### Physics mapping (kami-genesis)

- **Walls / machines / columns** → `Obstacle::Aabb` (static collision).
- **Component AGV** (`agv_1`) → `Agv::step_toward` (clamped-PD, friction) shuttling
  trays between SMT and assembly — same model as the sarutahiko part-AGVs.
- **Line robot cells** (`cell_smt_1` Tedama / `cell_chassis_1` Otete /
  `cell_display_1` Hitogata / `cell_qc_1` Mimi) → `giemon_arm6` URDF arms
  (reduced-coordinate solver) working the device at each station.
- **Device on the conveyor** → a small rigid body advancing along `conv_main`,
  dwelling `cycle_s` per station; at `display` it is laminated, at `attest` its
  DID is minted, at `eol` it is dismantled (reverse).
- No mega-press / no heavy lift (anti-mass-production G12) — small light-load bay.

### Regression test (mirror sarutahiko's)

`tests/tsutae_line_makes_a_handheld_end_to_end.rs`:
assert a device advances through all 12 stations and the final station emits a
device record with a `did:web:etzhayyim.com:tsutae:device:<serial>` + ≥2 robot
signers (G4). (The pure state-machine equivalent already passes today in
`orgs/etzhayyim/com-etzhayyim-tsutae/cells/test_state_machines.py` — 8/8.)

### Honest scope

R0 design + physics sim only; no real cleanroom, no 電波法/技適 cert, no real
robots. R3 community-scale (≤10,000/yr) is Council + LANDS.md gated.
