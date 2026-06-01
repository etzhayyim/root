# kami-apps — etzhayyim repo-specific (L3) robotics-actor apps

These are the **etzhayyim-specific** robotics digital-twin / actor apps, extracted
from the reusable `kami-engine` workspace per **ADR-2606011500 stage 3** so that
the eventual `kami-engine` git-submodule (stage 4) stays purely reusable.

| Crate | Purpose | Page |
|---|---|---|
| `kami-app-shibuya` | Shibuya street digital-twin physics sim | `shibuya.htm` |
| `kami-app-giemon` | Giemon robot kit viewer + kabitori/otete | `giemon.htm` |
| `kami-app-giemon-factory` | The factory that manufactures the giemon line (4D BIM) | `giemon-factory.htm` |
| `kami-app-tatekata` | 建方 — the factory built BY construction robotics (physics-driven) | `tatekata.htm` |

## Relationship to kami-engine

This is a **separate Cargo workspace** (`40-engine/kami-apps/`), a sibling of
`40-engine/kami-engine/`. Each crate path-depends on the **L2** engine crates
under `../kami-engine/` (kami-app, kami-pipelines, kami-render, kami-genesis,
kami-articulated) and `include_str!`s:

- generic robot fixtures from `../../kami-engine/fixtures/` (e.g. `giemon_arm6`)
- repo-specific (L3) scenes from `../../../../70-tools/e7m-sim/scenes/`

Reference games (`kami-app-isekai`, `-quarry-walk`, `-car-sim`) and the
`*.etzhayyim.com` product apps (`-bim`, `-cad`, `-live`, `-maps3d`,
`-amenominaka`, `-animeka-timeline`) intentionally **remain** in the
`kami-engine` workspace (they are engine showcases / not in scope for stage 3).

## Build

```sh
cargo test --workspace                         # native rlib + tests
wasm-pack build kami-app-shibuya --target web --release   # (run from this dir)
```

The deployed WASM bundles live in `60-apps/.../svelte/static/<app>/` and the
`.htm` pages load them from there — independent of this crate-source location.
