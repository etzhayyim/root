---
id: adr-2605272000-isekai-omniverse-r1-1-usd-physx-playable
title: "ADR-2605272000: isekai.etzhayyim.com Omniverse / PhysX / OpenUSD R1.1 — playable via kami-engine-sdk + kami-usd USDA mini-parser + kami-genesis World"
status: proposed
doc_type: adr
topic: isekai-omniverse-r1-1
authoritative: true
last_verified: 2026-05-27
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "First R1+ activation of ADR-2605261800 §D10.3 nv-compat facade across a user-playable surface (isekai.etzhayyim.com/omniverse.htm). Promotes kami-usd from path-reservation to R1.1-usda-mini and wires kami-genesis World (PxScene / PxArticulationReducedCoordinate shape) behind a kami-app-isekai WASM entry plus an `<IsekaiCanvas/>` Svelte 5 component shipped from @etzhayyim/kami-engine-sdk."
authoritative_for:
  - isekai.etzhayyim.com Omniverse / PhysX / OpenUSD facade entry
  - kami-usd USDA mini-parser scope and behaviour
  - IsekaiCanvas SDK component contract
depends_on:
  - adr-2605261800-nvidia-omniverse-stack-api-compat
  - adr-2605261600-robotics-simulation-substrate-r0
  - adr-2605262500-robotics-world-data-ingestion-and-usd-pipeline
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605264300-kami-engine-sdk-three-free-cutover
related:
  - adr-0031-kami-vrm-three-free-topology
  - adr-2605211845-etzhayyim-org-cleanup-completion-and-kami-engine-sdk-standalone
supersedes: []
superseded_by: []
---

# ADR-2605272000: isekai.etzhayyim.com Omniverse / PhysX / OpenUSD R1.1 — playable via kami-engine-sdk + kami-usd USDA mini-parser + kami-genesis World

**Status**: proposed
**Date**: 2026-05-27
**Deciders**: Jun Kawasaki

# Context

ADR-2605261800 stood up the kami-engine nv-compat layer in R1.0 path-reservation
form across ten `kami-*` crates, plus the first wasm32 demonstrator
(`kami-cartpole-wasm`, 485KB) proving the Omniverse / Isaac Sim / PhysX / OpenUSD
API facade compiles end-to-end on WebGPU. R1.1 for the e7m-sim sub-charter
landed Cartpole closed-form dynamics in `kami-genesis` plus the URDF parser in
`kami-articulated` and the Python facade in `kotodama.nv_compat.*`.

What remained missing was a **user-playable surface** that exercises the full
facade — OpenUSD scene parsing + PhysX-shaped articulation execution + an SDK
component external apps can embed. Without it, the nv-compat layer reads like
a buildable crate set rather than a working stack from a religious-corp
member's standpoint.

`isekai.etzhayyim.com` is the natural place for this. It already serves the
voxel sandbox (`v2.htm`) and the 11-scene DEC physics harness (`v3-demos.htm`)
via the same `kami-app-isekai` WASM crate. Adding a third entry that loads an
OpenUSD stage and ticks a PhysX-shaped `World` over the same voxel surface
constitutes the smallest non-trivial proof that the facade is real.

Scope question for the user (asked + answered 2026-05-27 in-session):

> R0 = SDK 組込 + USD scene load (Recommended): kami-engine-sdk に
> `<IsekaiCanvas/>` Svelte component を追加。kami-usd で `.usda` シーン読込
> パス、kami-physx は α=0 step-0 verify レベルで配線。実物理は v3 DEC が
> 継続駆動。

R0 selected. R1+ (PhysX-backed rigid bodies, full v3-demos replacement) deferred.

# Decision

We add `isekai.etzhayyim.com/omniverse.htm` as a third entry alongside `v2.htm`
and `v3-demos.htm`, backed by:

## 1. `kami-usd` — promoted from R1.0 path-reservation to R1.1-usda-mini

A ~280-LoC native Rust USDA mini-parser lives in `40-engine/kami-engine/kami-usd/src/lib.rs`.
Recognised prim types: `Xform` / `Cube` / `Sphere` / `Plane` / `Mesh` /
`PhysicsScene` / `Cartpole`. Recognised attribute prefixes: `custom` /
`uniform` / `varying` (skipped). Recognised xform ops: `xformOp:translate` /
`xformOp:rotateXYZ` / `xformOp:scale`. Layer metadata: `upAxis` /
`metersPerUnit`.

Output type `Stage { up_axis, meters_per_unit, prims: Vec<Prim> }` mirrors
`pxr::UsdStage` shape closely enough that swapping the parser body to
`tinyusdz` (R1.2 target) leaves callers untouched (§D10.3 invariant).

Unknown prim types degrade to `PrimKind::Xform` rather than rejecting the
stage — partial parsing is preferred over total failure when shipping to a
public canvas.

Tests (3): `parses_isekai_omniverse_stage` / `empty_stage_round_trips` /
`unknown_prim_degrades_to_xform`. All green.

## 2. `kami-app-isekai::omniverse` — new `runIsekaiOmniverse(canvas_id, usda_src)` WASM entry

New module `kami-app-isekai/src/omniverse.rs` (~310 LoC). Three wasm-bindgen
exports:

- `runIsekaiOmniverse(canvas_id: string, usda_src: string) -> Promise<void>` —
  parses the USDA (empty string falls back to `DEFAULT_ISEKAI_USDA`), builds a
  `kami_genesis::World` with gravity sourced from the `PhysicsScene` prim,
  spawns one `kami_genesis::Articulation` per `def Cartpole` prim using the
  bundled URDF, runs the existing isekai voxel sandbox + sky + terrain
  pipelines, and visualises each cartpole as a pair of `AtlasVisAdapter`
  sprites (cart = `FLAME_MEDIUM`, pole tip = bobbing `SPARKLE_STAR`).
- `isekaiOmniverseBanner() -> string` — returns the constitutional facade
  declaration (`kami-usd@<phase> (omni.usd compat) + kami-genesis@<phase>
  (PhysX 5 / isaacsim.core.api compat) — ADR-2605261800`) for HUD display.
- `isekaiOmniverseDefaultUsda() -> string` — returns the bundled
  `DEFAULT_ISEKAI_USDA` so the JS side can prepopulate an editor textarea.

`World::step()` is called per frame (PhysX `PxScene::simulate` shape). At R0
no force input is wired — `Articulation::set_cart_force(0.0)` is implied; the
demonstration is that the physics loop executes and cart / pole positions are
read back into the visual layer. R1 will bind A / D keys to ±10 N driveTarget
calls.

WASM artifact size: 372 KB → 494 KB (+122 KB for `kami-usd` + `kami-genesis` +
`kami-articulated`). Headroom against `ADR-2605241900` baien edge invariant
remains comfortable (this is an app crate, not a baien trunk).

Tests (2): `default_usda_parses_with_one_cartpole` /
`build_world_reads_gravity_from_stage`. All green.

## 3. `<IsekaiCanvas/>` Svelte 5 component in `@etzhayyim/kami-engine-sdk`

New component at `40-engine/kami-engine/kami-engine-sdk/src/lib/components/IsekaiCanvas.svelte`.
Mirrors the `<VrmCanvas/>` topology:

- Props: `wasmBase` (default `/v2`) / `usda` (default empty → use bundled
  default) / `class` / `style` / `bgColor` / `loading` snippet / `error`
  snippet / `onready` callback.
- Dynamically imports `${wasmBase}/kami_app_isekai.js`, awaits `default()`,
  calls `isekaiOmniverseBanner()` for the HUD overlay, then drives
  `runIsekaiOmniverse(canvasId, effectiveUsda)`.
- Built-in retry button on init failure; loading overlay with progress %.
- Exported from `src/lib/components/index.ts` and re-exported from
  `src/lib/index.ts` alongside `VrmCanvas` / `ExpressionPanel` / etc.
- `npm run build` (svelte-package) produces `dist/components/IsekaiCanvas.svelte`
  + `.svelte.d.ts`. The pre-existing svelte-check warnings in Genko / WebVR
  are unchanged and not introduced by this component.

## 4. `omniverse.htm` static page deployed to the existing isekai worker

`60-apps/etzhayyim-project-isekai/appview/etzhayyim-wasm-isekai-is3k41w0/svelte/static/omniverse.htm`
(~5.1 KB). Editable USDA `<textarea>` + Reload button (sessionStorage
round-trip) + Default button + HUD pulling from
`window.__kami_hud_isekai`. The same SvelteKit static pipeline that publishes
`v2.htm` / `v3-demos.htm` publishes `omniverse.htm`. WASM artifacts are
re-published to `svelte/static/v2/`.

The wrangler worker name + routes (`kotodama-is3k41w0`,
`is3k41w0.etzhayyim.com/*` / `isekcom.etzhayyim.ai/*`) are unchanged. No new
Cloudflare resources, no DNS change.

# Consequences

## Positive

1. **First R1+ activation of the §D10.3 facade across a user-playable URL.**
   Constitutional invariants (`kami-*` namespace only, no direct `pxr.*` /
   `omni.*` / `isaacsim.*` imports) hold end-to-end from Rust → wasm → JS →
   DOM. The HUD banner makes the facade declaration legible to anyone who
   opens the page.

2. **kami-engine-sdk gains a robotics-style canvas embed.** Any other Svelte
   app in the monorepo (or external consumer of `@etzhayyim/kami-engine-sdk`)
   can now drop `<IsekaiCanvas usda={…} />` next to `<VrmCanvas/>` /
   `<PartPicker/>` without learning the kami-app-isekai WASM surface.

3. **Parser swap path preserved.** The mini-parser is deliberately under
   ~300 LoC. Replacing it with a `tinyusdz` binding at R1.2 will not touch
   `Stage` / `Prim` / `PrimKind` callers, satisfying §D10.3.

4. **Charter Rider compatibility unchanged.** No new third-party deps. No
   commercial GPU / cloud rental introduced. Inference remains Murakumo-only
   per ADR-2605215000 (this is a client-side render path; no inference is
   invoked at runtime).

5. **All 77 native unit tests pass** across `kami-usd` (3 new) /
   `kami-app-isekai` (2 new) / `kami-genesis` (71 unchanged) /
   `kami-articulated`.

## Negative

1. **R0 cartpole is visually weak.** Rendered as two atlas sprites rather
   than articulated URDF link geometry. A casual viewer sees a flame + sparkle
   bobbing instead of a recognisable "cart with pole". R1 will replace this
   with a proper articulated-body mesh via `kami-articulated` link geometry
   (~half-day).

2. **Force input deferred.** `World::step()` ticks but no force is applied,
   so the pole simply falls under gravity and the cart stays put. From a
   "playable" standpoint this is closer to "watchable". R1 keyboard binding
   restores interactivity.

3. **The USDA mini-parser is intentionally narrow.** It will reject anything
   non-trivial from a real Hydra exporter (variantSets, references, payloads,
   composition arcs). For the omniverse.htm demo this is fine; for any wider
   adoption R1.2 must bring in `tinyusdz`.

4. **Wasm grew 122 KB.** Acceptable for this app crate; signals we should
   begin tracking per-entry WASM-size budgets if we add more facade surfaces.

5. **No new CI gate yet.** A wasm-build smoke + an `npm run build` smoke on
   `kami-engine-sdk` should be added so the cross-crate dependency chain
   (kami-usd → kami-genesis → kami-articulated → kami-app-isekai → omniverse
   module → JS exports → IsekaiCanvas component dynamic import) stays green.
   Captured as a follow-up.

## Constitutional / Charter Compliance

- §G7 of ADR-2605262500 (no direct NVIDIA APIs) — satisfied. Static grep of
  the new code: zero `omni.*`, `pxr.*`, `isaacsim.*`, `physx.*` imports.
- §D10.3 of ADR-2605261800 (facade-swap invariant) — satisfied. Parser body
  changes do not propagate to callers.
- §G11 of ADR-2605262500 (quality gate >=0.75 vs Isaac Sim) — not yet
  measured at this layer; deferred to R2 cartpole pose-validation step.
- ADR-2605215000 (Murakumo-only inference) — no inference path invoked.

# Alternatives Considered

1. **R1 in this same commit** (real articulated body mesh + force input).
   Rejected — overshoots the user-confirmed R0 scope. Will land as a
   follow-up ADR.

2. **R2 (full `v3-demos.htm` replacement)**. Rejected — would tear out the
   DEC physics layer and replace it with `kami-physx` + `kami-replicator`.
   Regression risk to existing scenes 0-11 is too high for a single commit.

3. **Brand-new entry under a new domain or worker** (e.g.,
   `omniverse.etzhayyim.com`). Rejected — user picked "現 engine worker
   (kami-web/) を継続". Existing SvelteKit static pipeline + isekai worker
   suffices; no new Cloudflare resource is justified.

4. **JS-only USDA parser**. Rejected on §D10.3 grounds — `kami-usd` is the
   canonical OpenUSD impl in the religious-corp namespace. JS-only parsing
   would create a parallel impl with no facade-swap path.

# Procedural Path

This ADR is `proposed`. Wave-by-wave promotion to `accepted` requires a
Council Lv6+ ≥3 attestation per ADR-2605261800 §D10.2 once the omniverse.htm
build is deployed and observed live.

- P0 (today, this commit): ADR + code + WASM build + SDK build + deps.toml
  registration + adr/README.md index entry. **`proposed`**.
- P1 (post-Council ratify of ADR-2605261800 §D10): no additional Council
  attestation required — this ADR is an R1.1 activation of an existing R1.0
  reservation, not a new constitutional claim.
- P2 (R1 follow-up ADR): proper URDF-mesh visual layer + keyboard force
  binding + `windowedRenderQualityAttestation` Lexicon emit per
  ADR-2605262500 §G11.
- P3 (R1.2 follow-up ADR): `tinyusdz` swap-in behind unchanged `kami-usd`
  API surface.

# References

- ADR-2605261800 (NVIDIA Omniverse stack API-compat layer)
- ADR-2605261600 (e7m-sim robotics simulation substrate R0)
- ADR-2605262500 (Robotics-sim world-data ingestion + kami-usd pipeline)
- ADR-2605215000 (etzhayyim inference Murakumo-only)
- ADR-2605192200 (Charter Compliance Rider v2.0)
- ADR-2605264300 (kami-engine-sdk three-free cutover)
- ADR-0031 (kami-vrm three-free topology — IsekaiCanvas mirrors VrmCanvas)
- `40-engine/kami-engine/kami-usd/src/lib.rs`
- `40-engine/kami-engine/kami-app-isekai/src/omniverse.rs`
- `40-engine/kami-engine/kami-engine-sdk/src/lib/components/IsekaiCanvas.svelte`
- `60-apps/etzhayyim-project-isekai/appview/etzhayyim-wasm-isekai-is3k41w0/svelte/static/omniverse.htm`
