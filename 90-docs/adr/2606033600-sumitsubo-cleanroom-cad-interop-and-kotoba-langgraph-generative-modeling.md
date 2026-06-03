---
id: adr-2606033600-sumitsubo-cleanroom-cad-interop-and-kotoba-langgraph-generative-modeling
title: "ADR-2606033600: sumitsubo 墨壺 — cleanroom CAD interop (Vectorworks / Autodesk / AutoCAD) for modeling + export, and kotoba Pregel-LangGraph generative / modeling assistance"
status: proposed
doc_type: adr
topic: sumitsubo-cleanroom-cad-interop
authoritative: true
last_verified: 2026-06-03
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "NOTE: ADR id 2606033600 is shared with a parallel-agent tsuzuri ADR (PDF editor); filename + actor name disambiguate, per the CLAUDE.md parallel-race convention. Reconcile in a future id sweep."
authoritative_for:
  - the cleanroom CAD-interop SDK module (geometry kernel + open-format import/export + published-API-shape command adapters) shipped for kami-engine-sdk re-export
  - the cleanroom invariant for CAD vendor interop (no vendor SDK headers / no decompilation / no trademarked code / public specs only)
  - the kotoba Pregel-LangGraph generative + modeling-assistance cells (NL → modeling-op plan → kotoba Datoms)
  - the open-format export fidelity + DWG-proprietary honesty boundary
related:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605231525-etzhayyim-no-server-side-signing-key
  - adr-2606011500-spirit-in-physics-kotoba-datafication
supersedes: []
superseded_by: []
depends_on:
  - ADR-2605262130 (kotoba storage substrate — EAVT canonical state)
  - ADR-2605215000 (Murakumo-only inference — generative cells call LiteLLM 127.0.0.1:4000)
  - ADR-2605192200 (Charter Rider v2.0 — Apache-2.0 + Rider on the SDK module)
---

# ADR-2606033600: sumitsubo 墨壺 — cleanroom CAD interop + kotoba-LangGraph generative modeling

**Status**: proposed
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

> **Parallel-agent id note**: a concurrently-running session created a different ADR that
> also took id `2606033600` (tsuzuri, an in-browser PDF editor) by checking out a feature
> branch mid-session. Per the repo's documented convention (root CLAUDE.md: "filename +
> actor name disambiguate" for parallel-agent id races, as already exists for 2605263400 /
> 2605263500), this ADR keeps id 2606033600 with the distinct `sumitsubo-…` filename. A
> future id-reconciliation sweep may renumber one of them.

# Context

kami-engine already ships `kami-app-cad` and `kami-app-bim` (Rust→WASM viewers) and the
TS `kami-engine-sdk` exposes an `IndustrialSoftwareDomain` that *names* `cad`/`cae`/`cam`/`plm`
as integration targets — but there is **no actual interoperability layer**: nothing reads or
writes the data formats that real-world drafting/BIM lives in (DXF, IFC, glTF, OBJ, STEP), and
nothing lets a script written against the **published** shapes of Vectorworks (VectorScript /
Marionette) or Autodesk AutoCAD (ObjectARX / AutoCAD .NET / AutoLISP) drive the kami kernel.

The founder asked for kami-engine-sdk to support **Vectorworks, Autodesk and AutoCAD** via
**cleanroom design**, covering **modeling** and **export**, and additionally for **kotoba
Pregel-LangGraph** to support **generative + modeling assistance**.

Two hard constraints frame this:

1. **Cleanroom**. Autodesk and Vectorworks SDKs ship under proprietary licenses; AutoCAD's
   native **DWG** format is undocumented/proprietary. We may NOT copy vendor SDK headers,
   decompile their binaries, vendor their sample code, or use their trademarks as if endorsed.
   We MAY implement against **publicly published** material: the openly documented **DXF**
   reference, the **IFC** (ISO 16739) / **STEP** (ISO 10303) / **glTF** (Khronos) / **OBJ**
   open specifications, and the **published method *shapes*** of the vendor scripting APIs
   (names/arity as documented for interoperability — an idea, not their code).

2. **Substrate**. Per ADR-2605262130 + 2605312345, drawing state is **kotoba Datoms** (EAVT),
   not SQL; per ADR-2605215000, any LLM in the generative path is **Murakumo-only**
   (LiteLLM `127.0.0.1:4000`); per ADR-2605231525, the actor holds **no server signing key**.

The kami-engine submodule that hosts the TS SDK is maintained upstream
(`github.com/etzhayyim/kami-engine`, ADR-2606011500 §4) and is not checked out in the
monorepo working clone. To keep this work tracked, testable, and convention-aligned, the
deliverable is a **new Tier-B actor `sumitsubo` 墨壺** (the carpenter's ink-line marking
instrument — the traditional drafting tool) that bundles: (a) a zero-dependency TypeScript
**cleanroom CAD-interop module** designed for `kami-engine-sdk` to re-export, and (b) the
**kotoba Pregel-LangGraph** generative / modeling-assistance cells. kami-engine-sdk picks
this up via a documented re-export point (`export * from '@etzhayyim/sumitsubo-cad'`), exactly
as it already re-exports its other headless builders.

# Decision

Create `20-actors/sumitsubo/` with two co-designed surfaces over one canonical drawing model.

## 1. Cleanroom CAD-interop SDK module (`sdk/`, TypeScript, zero-dep)

A canonical, unit-aware **drawing model** (`Drawing` = layers + entities; model units = mm,
f64) and a small **modeling kernel** (primitives, transforms, profile→extrusion meshing, light
prismatic CSG) — engine-agnostic, so it can drive the kami WASM kernel OR stand alone.

- **Exporters** (write): `dxf` (R12 ASCII — the openly published DXF group-code format),
  `svg`, `obj` (Wavefront), `gltf` (glTF 2.0 JSON), `ifc` (IFC4 STEP-physical-file subset),
  `step` (AP242 minimal point-set). **`dwg`**: NOT written natively (proprietary); the DWG
  exporter emits a DXF payload + an honest `DWG_PROPRIETARY` advisory directing the caller to
  an external ODA/LibreDWG round-trip. (Cleanroom invariant **N1**.)
- **Importers** (read): `dxf` subset (LINE / LWPOLYLINE / POLYLINE / CIRCLE / ARC / POINT, layers).
- **Published-API-shape adapters**: `VectorScript` (a Vectorworks-shaped façade —
  `Rect`/`Line`/`Poly`/`Extrude`/`Move`/`Layer`/… mirroring the *documented* call shapes) and
  `AcadDatabase`/`BlockTableRecord` + `command()` (an ObjectARX/.NET + AutoLISP-shaped façade).
  Each adapter is a thin translator emitting kernel ops; **no vendor code, only the public call
  shapes** (N1).
- **kotoba bridge**: `drawingToDatoms(d)` serializes a drawing to EAVT Datoms under the
  `:dwg.*` namespace (G2), the canonical state home; `datomsToTxEdn` renders the tx.

The module is **zero-runtime-dependency** and tested with `vitest` (15 tests).

## 2. kotoba Pregel-LangGraph cells (`py/`, `cells/`)

Five cells over one kotoba EAVT graph (mirrors the okaimono/watatsuna actor pattern):

- `model` (langgraph) — **generative**: NL prompt → Murakumo LLM → a validated **modeling-op
  plan** (a sequence of kernel ops, schema-checked) → drawing Datoms. The op plan is the
  bridge to the TS kernel: identical op vocabulary on both sides.
- `draft` (langgraph) — **2D drafting assistance**: suggests dimensions, constraints, and
  layer organization over an op set.
- `interop` (langgraph) — translates a Vectorworks/AutoCAD-shaped script into the neutral
  kernel op list (the python mirror of the TS adapters).
- `export` (datalog/kotoba) — resolves a target format + emits an export record (honoring the
  DWG-proprietary boundary).
- `catalog` (datalog/kotoba) — the drawing / entity / layer registry.

LLM is **Murakumo-only** via `KotobaLLM` (G3); all state is **kotoba Datoms** (G6/G2). An
offline deterministic planner keeps the generative cell useful + testable without a live model.

## 3. Gates (G1–G10)

| Gate | Name | Rule |
|---|---|---|
| **G1** | **cleanroom-invariant** | No vendor SDK headers, no decompilation, no vendored sample/trademark code. Only public format specs (DXF/IFC/STEP/glTF/OBJ) + published API *shapes*. Vendor names nominative (interop), never endorsement. |
| **G2** | kotoba-EAVT-native | Drawings/entities/layers/export state are kotoba Datoms (`:dwg.*`); no RW/SQL/Lance canonical (ADR-2605262130/2605312345). |
| **G3** | murakumo-only | Generative/assist LLM via KotobaLLM `127.0.0.1:4000`; no external LLM (ADR-2605215000). |
| **G4** | open-format-fidelity-honesty | Export fidelity is reported (`full|subset|fallback`); lossy/subset exports + skipped entities flagged; no claim of full vendor parity. |
| **G5** | dwg-proprietary-honesty | DWG never claimed native; `DWG_PROPRIETARY` advisory + DXF fallback (N1). |
| **G6** | no-server-key | No platform signing key; export/publish artifacts content-addressed, member/operator-signed (ADR-2605231525). |
| **G7** | sourcing-honesty | Generated geometry marked `:representative` unless dimensioned from authoritative input. |
| **G8** | charter-rider | Apache-2.0 + Charter Rider v2.0 on the SDK module (ADR-2605192200). |
| **G9** | outward-gated | Live ingestion of third-party drawing corpora / external CAD-cloud calls = Council + operator gated. |
| **G10** | wellbecoming-tool | A drafting *instrument* for makers (labor-liberation, multi-gen design durability), never an engagement/lock-in surface. |

## 4. Non-goals (N1–N6)

- **N1** native DWG write, or any reliance on vendor SDK/decompilation/trademark (cleanroom).
- **N2** full geometric-kernel parity with ACIS/Parasolid (kami kernel is mesh-first + light prismatic CSG; exact B-rep solid modeling is out of R0).
- **N3** a hosted CAD cloud / Autodesk-Forge-equivalent service.
- **N4** bidirectional live sync with a running Vectorworks/AutoCAD instance (adapters are script-shape translators, not IPC bridges).
- **N5** GIS/PLM/MES integration (those `IndustrialSoftwareDomain` members stay separate).
- **N6** claiming certified IFC/STEP conformance (R0 emits valid-but-subset files).

# Consequences

- kami-engine-sdk gains real CAD data-exchange (DXF/IFC/glTF/OBJ/STEP) + Vectorworks/AutoCAD
  script-shape drivers, all behind a clean re-export, with the cleanroom posture documented.
- Generative modeling becomes a kotoba-native, Murakumo-only LangGraph flow whose op
  vocabulary is shared verbatim with the TS kernel — one model, two runtimes.
- **Honest R0**: exporters are real but subset (DXF R12 / IFC4 tessellation subset / STEP
  point-set); DWG is fallback-only; the kami WASM kernel binding is by op-list (the cells emit
  ops; wiring the ops into the live `kami-app-cad` WASM is a follow-up); adapters cover the
  most common published call shapes, not the full vendor API surface.

# Alternatives Considered

- **Author into the kami-engine submodule directly** — rejected: the submodule is not checked
  out in the monorepo clone (no `.git`, build artifacts only), so source would be untracked
  and untestable. The new-actor home is writable + tested; the SDK re-exports it.
- **Rust→WASM crate in kami-apps** — rejected for R0: path-depends on the absent kami-engine
  crates (won't compile here) and loses TS SDK ergonomics. The op-list is engine-neutral, so a
  Rust binding can be added later without changing the model.
- **Open formats only / API-shapes only** — rejected: the founder chose formats **and**
  API-shape adapters for the broadest interop.

# References

- `20-actors/sumitsubo/` — actor (sdk + py + cells + lex + kotoba schema)
- DXF reference (openly published group-code format); IFC ISO 16739; STEP ISO 10303-242; glTF 2.0 (Khronos); Wavefront OBJ
- ADR-2605262130 (kotoba substrate) · ADR-2605215000 (Murakumo-only) · ADR-2605231525 (no server key) · ADR-2605192200 (Charter Rider)
