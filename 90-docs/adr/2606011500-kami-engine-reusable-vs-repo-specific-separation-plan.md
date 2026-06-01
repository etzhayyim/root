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
  - adr-2605211845-gftd-org-cleanup-completion-and-kami-engine-sdk-standalone
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
| **L2 — Reusable Rust robotics engine** | kami-core, kami-render, kami-genesis (physics + **control**), kami-articulated, kami-sensor-sim (**sensors**), kami-autodrive (autonomy), kami-pathfind, kami-vehicle, kami-physics-*, kami-terrain, kami-atmosphere, … + generic fixtures (cartpole / double_pendulum / arm3 / giemon_arm6 / _schema) | git **submodule** (after L3 + fixtures separated) |
| **L3 — etzhayyim repo-specific** | kami-app-{shibuya, giemon, giemon-factory, tatekata, …} + repo-specific scenes (shibuya, *-r1-*, giemon-factory-r0, giemon_kabitori/otete, kusawake, …) | stays in monorepo (app layer) |

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
2. **Generic-fixtures home.** cartpole/double_pendulum/arm3/giemon_arm6/_schema
   are shared by L2 (Rust compile-time) and magatama (Python runtime). Decide:
   (a) vendor into L2 engine (drift risk), (b) move into L2 as SoT + update
   magatama/tooling, or (c) a small shared `e7m-fixtures` submodule both consume.
   This unblocks L2 self-containment.
3. **L3 extraction.** Move repo-specific kami-app-* crates + their scenes out of
   the reusable engine workspace into the monorepo app layer; they keep
   path/submodule deps on L2. Update the ~24 repo-specific include paths.
4. **L2: kami-engine → submodule.** Once L3 + fixtures are separated, extract
   the reusable engine (history via `git subtree split`), new remote
   `etzhayyim/kami-engine`, add Charter Rider + NOTICE per repo convention,
   wire external dependents (`20-actors/magatama/hosts/magatama-kami-host`,
   `60-apps/ai-gftd-project-watashi/native/watashi-host`).
5. Update deps.toml + ADRs at each stage.

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
