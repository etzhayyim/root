---
id: adr-2606011500-kami-engine-reusable-vs-repo-specific-separation-plan
title: "ADR-2606011500: kami-engine reusable-vs-repo-specific separation plan (submodule prerequisite)"
status: accepted
doc_type: adr
topic: kami-engine-layer-separation
authoritative: true
last_verified: 2026-06-01
priority: 5.0
axis: architecture
weight: 0.5
priority_note: "Classifies the kami-engine workspace + e7m-sim scenes into three layers — TS/Svelte UI SDK (kami-engine-sdk), reusable Rust robotics engine (control/sensor/physics, incl. kami-autodrive), and etzhayyim repo-specific apps+scenes — and lays out the staged separation that is the prerequisite for managing the reusable layer(s) as git submodules. KEY FINDING: code coupling is minimal (the generic engine crates compile-time-include ONLY generic fixtures cartpole/double_pendulum/arm3; the lone kami-genesis↔hikari reference is a doc comment, not an include); the real work is relocating repo-specific apps + scenes out of the reusable engine and deciding where the generic fixtures (shared by Rust + magatama Python) live. Robotics control (LQR/IK/controllers/Jacobian/trajectory in kami-genesis) + sensor sim (kami-sensor-sim) are the Rust reusable layer, NOT the TS kami-engine-sdk."
authoritative_for:
  - kami-engine reusable-vs-repo-specific layer classification
  - staged submodule-separation plan (kami-engine-sdk + reusable robotics engine)
depends_on:
  - adr-2606010600-kami-autodrive-gnc-autonomy-layer
  - adr-2606011040-session-close-kami-autodrive-gnc-and-ci-hygiene
related:
  - adr-2605211845-etzhayyim-org-cleanup-completion-and-kami-engine-sdk-standalone
  - adr-2605312355-session-close-kotoba-datom-first-class-and-charter-rider-d1
supersedes: []
superseded_by: []
---

# ADR-2606011500: kami-engine reusable-vs-repo-specific separation plan

**Status**: proposed
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

Goal: manage the reusable engine as git **submodules** (not subrepo / not
inlined monorepo source), so the common pieces can be versioned and reused
independently while etzhayyim-specific content stays in the monorepo.

An impact investigation of `40-engine/kami-engine` (93 `kami-*` dirs) and
`70-tools/e7m-sim/scenes` (1.6 MB, 66 files) established:

- **Code coupling is minimal.** Generic engine crates (kami-genesis,
  kami-shugyo, kami-articulated, kami-cartpole-wasm) compile-time `include_str!`
  ONLY generic fixtures (cartpole / double_pendulum / arm3). The single
  kami-genesis↔`hikari-r1-solar-tracker-2km` reference is a **doc comment**, not
  an include — no layering violation. kami-engine is its own self-contained Cargo
  workspace (no root monorepo workspace).
- **The TS SDK ≠ the robotics engine.** `kami-engine-sdk` is a pure TS/Svelte UI
  SDK (81 svelte/ts files, no Rust). The **robotics control** (LQR / IK /
  controllers / Jacobian / trajectory in `kami-genesis`) and **sensor sim**
  (`kami-sensor-sim`), articulation (`kami-articulated`), planning
  (`kami-pathfind`), vehicle dynamics (`kami-vehicle`), and autonomy
  (`kami-autodrive`) are **Rust crates**, NOT in kami-engine-sdk. `giemon`
  (kami-app-giemon / -giemon-factory) consumes them via path deps to
  kami-genesis + kami-articulated.
- **Scenes split cleanly** into generic fixtures vs repo-specific; the scenes
  dir is a *shared hub* consumed by kami-engine (Rust, compile-time), magatama
  (Python nv_compat, runtime), and 70-tools tooling (assemble-usd / mapillary /
  sbom) + referenced by ~19 docs.

# Decision

Adopt a **three-layer model** and separate along it:

| Layer | Contents | Management target |
|---|---|---|
| **L1 — UI SDK** | `kami-engine-sdk` (TS/Svelte: genko, trackpad, gsplat, document, manufacturing, webvr) | git **submodule** ✅ (PR #655 — `etzhayyim/kami-engine-sdk@ccb315c`, SoT inverted) |
| **L2 — Reusable Rust robotics engine** | kami-core, kami-render, kami-genesis (physics + **control**), kami-articulated, kami-sensor-sim (**sensors**), kami-autodrive (autonomy), kami-pathfind, kami-vehicle, kami-physics-*, kami-terrain, kami-atmosphere, … + generic fixtures now in-workspace `kami-engine/fixtures/` ✅ (cartpole / double_pendulum / arm3 / giemon_arm6) | git **submodule** ✅ (PR stage 4 — `etzhayyim/kami-engine@a58df69c`; kami-engine-sdk nested inside) |
| **L3 — etzhayyim repo-specific** | robotics-actor apps `kami-app-{shibuya, giemon, giemon-factory, tatekata}` extracted ✅ to `40-engine/kami-apps/` (stage 3); repo-specific scenes (shibuya, *-r1-*, giemon-factory-r0, giemon_kabitori/otete, kusawake, …) in `70-tools/e7m-sim/scenes/` | stays in monorepo (app layer) |

Robotics control + sensor are **L2**, distinct from the **L1** TS SDK.

## Staged migration (each stage = its own PR; ordered by risk)

1. **L1: kami-engine-sdk subrepo → submodule. ✅ DONE (PR #655, 2026-06-01).**
   Lowest risk; remote exists; precedent = kotoba (ADR-2605312355). The mirror
   `etzhayyim/kami-engine-sdk` was first advanced to the current monorepo source
   (conflict-free: it was a single `Initial mirror` snapshot, the monorepo a
   strict superset) at `ccb315c`; then the monorepo's 94 vendored files +
   `.gitrepo` were replaced by a `.gitmodules` gitlink pinned there. **SoT
   inversion**: this supersedes ADR-2605211845's "monorepo SoT + read-only
   mirror" *for kami-engine-sdk* — the standalone repo is now the source of
   truth. Submodule content verified byte-identical to the prior subrepo (93
   files, 0 mismatches). CI jobs that read the sdk path (SDK-build,
   monorepo-health) gained a targeted `git submodule update --init` step
   (not `submodules: recursive`, which would choke on the local-only
   `90-docs/baien/datasets` DataLad superdataset).
2. **Generic-fixtures home. ✅ DONE (option b, 2026-06-01).** cartpole/
   double_pendulum/arm3/giemon_arm6 were shared by L2 (Rust compile-time) and
   magatama (Python runtime) via an out-of-workspace `../../../../70-tools/`
   escape — the concrete blocker for stage 4. **Owner picked option (b)**: the
   4 generic fixtures were `git mv`'d into `40-engine/kami-engine/fixtures/` as
   the single SoT (history preserved). All 15 compile-time `include_str!` (across
   kami-genesis, kami-shugyo, kami-cartpole-wasm, kami-app-giemon{,-factory}) +
   the one runtime CWD-relative CSV read in `kami-genesis/tests/g5_scorecard.rs`
   now resolve in-workspace (`../../fixtures/` / `../fixtures/`); magatama's
   resolvers gained a shared `_fixture.load_fixture` helper that probes
   `kami-engine/fixtures/` first with the legacy `70-tools/e7m-sim/scenes/` path
   as fallback. `_schema` + the ~16 repo-specific (L3) scenes stay in
   `70-tools/e7m-sim/scenes/`. **L2 is now self-contained** (zero out-of-workspace
   fixture escapes), unblocking stage 4. Verified: every touched crate builds +
   tests green (kami-genesis 94 / kami-shugyo / kami-cartpole-wasm / kami-app-giemon
   4 / kami-app-giemon-factory; g5_scorecard 3); magatama resolver finds all 4.
   Pre-existing workspace failures (kami-map/kami-web wgpu API drift; kami-game
   island_gen) are unrelated, stash-confirmed on origin/main.
3. **L3 extraction. ✅ DONE (4 robotics-actor apps, 2026-06-01).** Owner scoped
   this to the 4 robotics-actor apps (`kami-app-{shibuya, giemon, giemon-factory,
   tatekata}`) — the ADR-named L3 set that consumes L3 scenes; the 3 reference
   games (isekai / quarry-walk / car-sim) and the 6 `*.etzhayyim.com` product
   apps stay with the engine (a follow-on may reclassify the product apps). The
   4 crates were `git mv`'d out of the kami-engine Cargo workspace into a new
   sibling workspace `40-engine/kami-apps/` (OUTSIDE the future submodule root
   `40-engine/kami-engine/`). Path-deps rewired `../kami-X` → `../../kami-engine/kami-X`
   (the tatekata→giemon-factory inter-app dep stays relative); the `giemon_arm6`
   fixture includes deepened `../../fixtures/` → `../../../kami-engine/fixtures/`;
   L3 scene includes (`70-tools/e7m-sim/scenes/`) unchanged (same path depth).
   **Deploy unaffected**: the `.htm` pages load wasm from committed
   `60-apps/.../static/<app>/` bundles (independent of crate-source location);
   only the `wasm-pack build` path moves. Verified: kami-apps workspace builds +
   **39 tests green**; the kami-engine workspace still builds (minus the 3
   pre-existing-broken crates kami-map/kami-web/kami-character — broken on
   origin/main regardless, stash-confirmed). The ~9 other kami-app-* (reference
   games + product apps) were intentionally NOT moved.
4. **L2: kami-engine → submodule. ✅ DONE (2026-06-01).** Extracted the reusable
   engine via `git subtree split -P 40-engine/kami-engine` (105-commit history)
   to the new public remote **`etzhayyim/kami-engine`** (`a58df69c`), then
   replaced the monorepo's 567-file tracked tree with a `.gitmodules` gitlink.
   **Nested submodule**: kami-engine-sdk (the L1 TS SDK) now lives as a submodule
   INSIDE kami-engine (its `.gitmodules` moved from the monorepo root into the
   kami-engine repo; pinned at `ccb315c`) — clones need
   `git submodule update --init --recursive 40-engine/kami-engine`. Added
   LICENSE + CHARTER-RIDER.md + README to the kami-engine repo per convention
   (NOTICE already present). **External dependents unaffected by path**: the
   `../../../../40-engine/kami-engine/kami-X` path-deps in
   `magatama-kami-host` + `watashi-host` (×2) resolve unchanged once the
   submodule is checked out. CI: the 3 workflows that read kami-engine internals
   (kami-engine-sdk build, monorepo-health, deps-toml-paths) switched their
   stage-1/2 targeted sdk-init to `--init --recursive 40-engine/kami-engine`.
   Verified: no data loss (567 original files all present); the `kami-apps`
   workspace builds green through the submodule path-deps.
5. Update deps.toml + ADRs at each stage.

## Post-stage-4 status (2026-06-01)

All 4 staged migrations landed (PRs #655 / #662 / #663 / #666). Follow-on work:

- **Engine native-build fix** (`etzhayyim/kami-engine@0419c43`, monorepo gitlink
  bump PR #672): the 3 crates that failed `cargo build --workspace` on native —
  kami-character (`glam` 0.29 vs workspace 0.33), kami-map / kami-web (ungated
  wasm-only wgpu code) — fixed; added a `.gitignore` to the engine repo (the
  subtree split hadn't carried the monorepo's root one).
- **CI baseline reds** (PR #680): deps-toml-paths "non-strict tracker" step no
  longer aborts under `bash -e` on pre-existing kotoba metadata drift;
  monorepo-health rollup re-baselined 25 → 7 (legitimate resolution).

- **Stage-3 follow-on — app-crate homes: ✅ RESOLVED (split model, 2026-06-01).**
  Concurrent parallel engine PRs (#1 physics sync · #2 carry robotics apps INTO
  the engine · #3 sarutahiko-factory · #4 funadaiku) revealed the canonical
  split: **robotics/sim apps are maintained IN the `etzhayyim/kami-engine`
  submodule; `*.etzhayyim.com` product apps live in monorepo `kami-apps/`.**
  - Engine repo: the 5 product apps (`bim/cad/live/maps3d/animeka-timeline`)
    were removed (`kami-engine@0155c1c`, kept — owner built PR #4 on top of it);
    robotics apps (giemon/giemon-factory/shibuya/tatekata/sarutahiko/funadaiku)
    + domain libs (kami-bim/kami-cad/kami-live/…) + `amenominaka` app-shell stay.
  - Monorepo `kami-apps/`: now holds **only the 5 product apps**; the stage-3
    robotics duplicates were **dropped** (they were stale — `kami-app-giemon`'s
    `Collider`-match never tracked the engine's `Collider::Box` variant, i.e.
    abandoned in favour of the engine copies). Gitlink bumped `2c54ff5 → 8e60f9a`.
  This removes the robotics-app duplication; each app crate now has exactly one
  home. (A brief mis-step — an erroneous revert of `0155c1c` (`de15ac4`) — was
  force-undone before reconciliation; engine main restored to `8e60f9a`.)

# Consequences

- Reusable robotics engine (L2) and UI SDK (L1) become independently versioned
  submodules; etzhayyim-specific apps/scenes (L3) stay in the monorepo.
- Honest scope: stages 2–4 have real cross-consumer blast radius (Rust + magatama
  Python + 70-tools tooling + docs all reference the scene hub) and require new
  remotes (`etzhayyim/kami-engine`) — multi-PR, partially irreversible. Stage 1
  is independently shippable now.
- `main` is currently CI-green and untouched; all separation work proceeds in
  isolated worktrees, staged.

# Alternatives Considered

- Inline everything (status quo) — rejected: blocks independent reuse/versioning.
- Move the whole scene hub into kami-engine — rejected as the default: breaks
  magatama + e7m-sim tooling + docs (kept as option 2b, owner decision).
- Treat kami-engine-sdk as the robotics SDK — rejected: it is a TS/Svelte UI SDK
  with no Rust; robotics control/sensor are separate Rust crates (L2).

# References

- ADR-2606010600 (kami-autodrive — L2 autonomy), ADR-2606011040 (session close)
- ADR-2605211845 (kami-engine-sdk standalone mirror), ADR-2605312355 (kotoba subrepo→submodule precedent)
- `40-engine/kami-engine/` (workspace), `70-tools/e7m-sim/scenes/` (shared hub)
