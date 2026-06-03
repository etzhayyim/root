---
id: adr-2606035500-session-close-sumitsubo-cleanroom-cad-interop
title: "ADR-2606035500: Session close — sumitsubo 墨壺 cleanroom CAD interop + kotoba-LangGraph generative modeling (R0)"
status: active
doc_type: adr
topic: session-close-sumitsubo-cleanroom-cad-interop
authoritative: false
last_verified: 2026-06-03
authoritative_for: []
related:
  - adr-2606033600-sumitsubo-cleanroom-cad-interop-and-kotoba-langgraph-generative-modeling
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606033600 (sumitsubo cleanroom CAD interop — authoritative design)
---

# ADR-2606035500: Session close — sumitsubo 墨壺 cleanroom CAD interop (R0)

**Status**: active (documentation-only session record)
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

# Context

Documentation-only closure for the 2026-06-03 session answering
*「kami engine sdk で Vectorworks/Autodesk/AutoCAD の api を cleanroom 設計で対応して、modeling, export などに対応して。また kotoba pregel langgraph での生成、modeling 支援にも対応して」*.

Authoritative design = **ADR-2606033600** (`sumitsubo-cleanroom-cad-interop-…`).

# Decision (what shipped)

New Tier-B actor **`20-actors/sumitsubo/` 墨壺** (the carpenter's ink-line marking
instrument), bundling two co-designed surfaces over one canonical drawing model with an
identical `ModelOp` vocabulary ("one model, two runtimes"):

1. **SDK module `@etzhayyim/sumitsubo-cad`** (`sdk/`, TypeScript, **zero runtime deps**,
   kami-engine-sdk re-export target):
   - geometry kernel + neutral `ModelOp` vocabulary (line/polyline/rect/circle/arc/box/extrude/move/scale)
   - exporters **dxf/svg/obj/gltf (full)** · **ifc/step (honest IFC4-tessellation / AP242-pointset subset)** · **dwg (proprietary → DXF fallback + `DWG_PROPRIETARY` advisory, never native, G5/N1)**
   - dxf importer (round-trips the exporter)
   - **published-API-shape adapters** `VectorScript` (Vectorworks) + `AcadDatabase`/`BlockTableRecord`/`command()` (AutoCAD ObjectARX/.NET/AutoLISP) — translate only the documented call shapes onto the kernel
   - kotoba EAVT bridge `drawingToDatoms` → `:dwg.*` canonical state
   - **`tsc` strict clean + 15 vitest green**
2. **kotoba Pregel-LangGraph cells** (`py/agent.py` + `cells/`): `model` (generative
   NL→Murakumo→validated ModelOp plan→Datoms) · `draft` (2D drafting assist) · `interop`
   (vendor-script→neutral ops, py mirror of the TS adapters) · `export` · `catalog`.
   Murakumo-only (G3), kotoba-EAVT-native (G2), **py tests green** offline.

Plus `manifest.edn`, 4 lexicons `com.etzhayyim.sumitsubo.*`, `kotoba/schema.edn` (`:dwg.*`)
+ seed + deploy, README, CLAUDE.md, Charter-Rider NOTICE. **Cleanroom invariant (G1/N1)**:
no vendor SDK headers / decompilation / vendored sample / trademark code — only public
format specs (DXF/IFC/STEP/glTF/OBJ) + published API shapes. 10 gates total.

**Landed** on branch `feat/sumitsubo-cad`. Registered in **root CLAUDE.md table + adr/README +
deps.toml `[[adrs]]`**.

# Consequences / honest limits (R0)

- Exporters are real but subset (DXF R12 / IFC4 tessellation / STEP point-set); no
  ACIS/Parasolid B-rep parity (N2); DWG fallback-only (N1).
- The kami WASM-kernel binding is by op-list (the cells emit ops; wiring into the live
  `kami-app-cad` WASM is a follow-up). Adapters cover common published call shapes, not the
  full vendor API surface. No hosted CAD cloud (N3); no live IPC sync with a running
  Vectorworks/AutoCAD instance (N4).
- **kami-engine-sdk re-export wiring deferred**: the kami-engine submodule is not checked out
  in this clone (build artifacts only, no `.git`), so the actual `export * from
  '@etzhayyim/sumitsubo-cad'` lands upstream in a follow-up. The op-list is engine-neutral, so
  a Rust binding can be added later without changing the model.

# Incident note — concurrent-session working-tree race + ADR-id collisions

This session ran amid heavy concurrent activity on a shared working tree:

- A concurrent session **checked out branch `feat/tsuzuri-adr-toml`** mid-build, **wiping this
  session's then-untracked files** (~25 recreated) and creating a **different ADR reusing id
  `2606033600`** (tsuzuri, an in-browser PDF editor).
- The first commit's branch also **transiently accumulated unrelated concurrent commits**
  (manako/ooyake) that were not on `origin/main`; the work was therefore **rebuilt on a clean
  branch off `origin/main`** (`feat/sumitsubo-cad`) carrying only sumitsubo, to keep the PR
  focused and avoid bypassing other sessions' review.
- This session-close ADR was **renumbered 2606035000 → 2606035500** after discovering another
  session had taken `2606035000` (a PR #865 review close) on `origin/main`.

Per the repo's documented parallel-agent id-race convention (root CLAUDE.md: *"filename +
actor name disambiguate"*, as already exists for 2605263400 / 2605263500), the sumitsubo
**design** ADR keeps id 2606033600 with a distinct filename. A future id-reconciliation sweep
may renumber the 2606033600 pair.

# References

- ADR-2606033600 — authoritative sumitsubo design
- `20-actors/sumitsubo/` — actor (sdk + py + cells + lex + kotoba schema)
- ADR-2605262130 (kotoba substrate) · ADR-2605215000 (Murakumo-only) · ADR-2605231525 (no server key) · ADR-2605192200 (Charter Rider) · ADR-2606011500 (kami-engine submodule topology)
