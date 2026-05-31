---
id: adr-2606010030-giemon-factory-r0-kami-engine-kotoba-4d-bim
title: "ADR-2606010030: giemon factory R0 — whole-plant layout + 建材 + 4D 建築手順, designed in kami-engine + kotoba Datomic"
status: accepted
doc_type: adr
topic: giemon-factory-kami-engine-kotoba-4d-bim
authoritative: true
last_verified: 2026-05-31
priority: 5.0
axis: architecture
weight: 0.4
priority_note: "Founder asked to design + build the giemon FACTORY itself — its layout, hardware, building materials (建材) and construction procedure (建築手順) — entirely in kami-engine and kotoba Datomic, nothing outside that stack. This composes three shipped precedents: kami-app-giemon (the products: arm6 + kabitori on kami-genesis), kami-app-shibuya (constructing an environment: baked scene → AABB obstacles → multi-agent physics), and the kabitori part-ledger→SBOM→kotoba EAVT pilot (Datomic EDN → kg.ingest_batch). New modeling = a 4D BIM construction sequence expressed as kotoba datoms and replayed in kami-engine. All Rust claims verified by direct cargo test + wasm build; the EDN→kotoba pipeline verified by running kotoba_gen.py."
authoritative_for:
  - giemon robot manufacturing plant R0 layout (factory.scene.json — walls/columns/beams/zones/machines/conveyors/cells/AGVs)
  - 建材 + 設備 ledger (building.edn — Datomic-style EDN, 27 parts, groups A-F) → CycloneDX SBOM + kotoba kg/claim/part/* datoms
  - 建築手順 / 4D 施工シーケンス (construction.edn — 13 steps, depends-on/consumes/reveals) → kotoba kg/claim/step/* datoms + construction.order.json
  - kami-app-giemon-factory two-entry viewer (completed plant w/ live arm6 cells + AGVs; 4D construction playback)
  - honest scope boundary: rigid-body + AABB contact + scheduling only; no FEM/CFD/structural/MEP solver
depends_on:
  - adr-2605311800-kami-genesis-3d-spatial-articulation-and-contact-solver
  - adr-2605311900-shibuya-street-digital-twin-osm-citymesh-fullphysics-sim
  - adr-2605312300-giemon-kabitori-mold-removal-probe-sim
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262130-kotoba-storage-substrate-unification
related:
  - adr-2605261600-robotics-simulation-substrate-r0
  - adr-2605261200-igata-hpdc-megacasting-tier-b
supersedes: []
superseded_by: []
---

# ADR-2606010030: giemon factory R0 — whole-plant layout + 建材 + 4D 建築手順 in kami-engine + kotoba Datomic

**Status**: accepted

## Context

The giemon robot **line** already exists and is validated on the kami-engine
clean-room stack: the 6-DOF arm (`giemon_arm6.urdf`) and the kabitori
mold-removal probe run on the `kami-genesis` Featherstone (RNEA + CRBA + LDLᵀ) +
rigid-contact solver (ADR-2605311800, 2605312300). Separately, `kami-app-shibuya`
showed how to **construct an environment** — a baked `scene.json` whose buildings
become `Obstacle::Aabb` collision volumes and whose roads become the drivable
ground, populated by full-physics floating-base agents (ADR-2605311900). And the
kabitori **part-ledger → CycloneDX SBOM → kotoba EAVT pilot** showed how to author
a Datomic-style EDN ledger and ingest it as first-class datoms into the kotoba
Datom log (`parts.edn` → `sbom_gen.py` → `kg.ingest_batch`; ADR-2605312300,
2605312345).

The founder asked for the next object: **the factory itself** — its layout, its
hardware, its building materials (建材), and its construction procedure (建築手順)
— designed end-to-end in kami-engine and kotoba, with nothing outside that stack.

This ADR composes the three precedents into one artifact: a plant that
manufactures the giemon line, whose **building** (建材 + 4D 施工手順) and
**production hardware** (machines + arm6 work-cells + AGVs) are both modeled in
kami-engine, and whose entire bill-of-materials **and construction sequence** live
as kotoba datoms. The genuinely new modeling layer is the **4D BIM construction
sequence** (3-D geometry + schedule) expressed as datoms and replayed in the
engine.

## Decision

Build **`giemon-factory-r0`** as a three-layer model, all inside kami-engine +
kotoba:

### 1. Building shell (建材) — kami-genesis geometry + obstacles
An 80 m × 50 m single-bay light-assembly plant: perimeter walls + an inspection
partition (`Obstacle::Aabb`, z = 0..h), an 8-column structural grid, 3 roof
trusses, an epoxy-zoned floor (受入→機械加工→組立→検査→出荷). Authored by hand in
`70-tools/e7m-sim/scenes/giemon-factory-r0/factory.scene.json` (shibuya-`Scene`
lineage, extended with `columns`/`beams`/`zones`/`machines`/`conveyors`/`cells`/
`agvs`) — no OSM step; the plant is designed, not surveyed.

### 2. Production hardware (設備) — CAD geometry + articulations
CNC mills, a lathe, a CMM, assembly benches, a conveyor spine, pallet racks, a
packing station, **4 giemon arm6 work-cells** (the product redeployed into its own
line, fixed-base `Articulation3d` running a PD work-cycle), and **2 four-DOF AGV
carts** (the shibuya floating-base agent path) that drive the floor and collide
with walls / columns / machines.

### 3. Construction procedure (建築手順) — 4D sequence as datoms
`construction.edn` — 13 ordered steps, each a datom-ready map with
`:step/depends-on` (predecessor refs), `:step/consumes` (建材 part refs),
`:step/duration-d`, and `:step/reveals` (render-element ids). `kotoba_gen.py` bakes
`construction.order.json`; the viewer's `run_giemon_factory_build_v1` reveals each
step's geometry in `:seq` order (site-prep → foundation → steel → roof → cladding
→ floor → MEP → machines → conveyor → robots → commissioning), so one literally
watches the plant be built per the stored 手順.

### Datom schema (kotoba EAVT, ADR-2605312345)
`building.edn` (27 parts) → one `GiemonFactoryPart` entity each
(`kg/claim/part/{group,procurement,manufacturer,product,mpn,purl,qty,massKg,
material,simFeature,sourcing,…}`). `construction.edn` (13 steps) → one
`GiemonFactoryStep` entity each (`kg/claim/step/{seq,name,trade,zone,durationD}`)
with `step/dependsOn` and `step/consumes` emitted as **entity-ref** claims so the
critical path is recoverable by VAET reverse lookup. `kotoba_gen.py` cross-checks:
`:seq` contiguous 1..N, depends-on acyclic + resolvable, every `:consumes` a real
building part, every `:reveals` a real render element in `factory.scene.json`.

## Pipeline

```
building.edn + construction.edn        (Datomic EDN — SSoT)
        │  python3 kotoba_gen.py  (+ cross-checks)
        ▼
factory.cdx.json   kotoba_ingest.json   construction.order.json
 (CycloneDX SBOM)  (kg.ingest_batch:     (4D order → kami-app-giemon-factory
                    27 parts + 13 steps)  run_giemon_factory_build_v1)
```

## Components

| Artifact | Path |
|---|---|
| Scene descriptor (e7m-sim) | `70-tools/e7m-sim/scenes/giemon-factory-r0/scene.yaml` |
| Runtime scene (hand-authored) | `…/giemon-factory-r0/factory.scene.json` |
| 建材 + 設備 ledger (SSoT) | `…/giemon-factory-r0/building.edn` |
| 建築手順 4D sequence (SSoT) | `…/giemon-factory-r0/construction.edn` |
| Generator + cross-checks | `…/giemon-factory-r0/kotoba_gen.py` |
| Generated SBOM / ingest / order | `…/giemon-factory-r0/{factory.cdx.json,kotoba_ingest.json,construction.order.json}` |
| Engine crate | `40-engine/kami-engine/kami-app-giemon-factory/` (`scene.rs` + `lib.rs`) |
| WASM viewer | `60-apps/ai-gftd-project-isekai/appview/ai-gftd-wasm-isekai-is3k41w0/svelte/static/giemon-factory.htm` |

## Charter / gates

- `physics_backend: kami-genesis` · `render_backend: kami-pbrt` ·
  `inference_substrate: murakumo-only` (no commercial GPU; this R0 trains nothing).
- `charter_rider_scan: required`; `max_tier: A`; `replication_min: 2`.
- `:sourcing :representative` — every manufacturer/MPN/purl in `building.edn` is a
  defensible R0 **design example**, NOT a procurement or 建築確認申請 (building-permit)
  decision. Confirm before buying or building.

## Non-goals (honest scope)

- **No mega-press / ≥7500 t HPDC clamping** — that is N1 constitutional (post-R3 +
  Council Lv6+, ADR-2605261200). This plant is light-assembly + bench machines.
- **No FEM / structural analysis** — columns/beams/trusses are rigid AABB geometry
  + a 建材 ledger, not a solved structure.
- **No MEP / HVAC / electrical CFD or load-flow** — MEP (group E) is a 建材 line
  item + a schedule step only, not simulated.
- **No agent–agent collision** — AGVs collide vs the static building only
  (shibuya iter-1 boundary). Tabletop arm cells cannot reach the factory walls, so
  obstacle-collision is exercised by the AGV carts, not the arms.

## Update v2 (2026-05-31) — full MEP + 外構 + 原材料

Extended from the initial shell+equipment R0 to a complete plant at the founder's
request ("もっと電気・水道・ガス・配線・照明・外部動線なども含めて全て設計, 実装配線,
sbom に。また原材料や市販品、建材なども"):

- **Routed MEP utilities** (not just line items): `factory.scene.json` now carries
  `service_nodes` (引込/受電キュービクル+変圧器/受水槽+ポンプ/ガス整圧器/通信引込),
  `utilities` (12 colour-coded **routed networks** — electrical busway + underground
  feeder + branch drops, compressed-air ring, data backbone, water supply, hot
  water, drainage, storm, gas, fire-main), and `fixtures` (24 high-bay luminaires +
  誘導灯/非常灯). The crate renders each network as conduit/pipe ribbons along its
  polyline (underground runs traced at the surface for visibility; design depth kept
  in the EDN/SBOM).
- **External circulation (外構/外部動線)**: `site_pavements` (access road, truck
  apron, car-park, service drive, walkway), `site_greens`, `site_structures`
  (perimeter mesh fence + electric slide gate), `site_posts` (6 外灯 poles + 5
  bollards + sign); `site_bbox_m` 124 m × 88 m.
- **BOM groups G-L** added to `building.edn`: G-electrical, H-water, I-gas,
  J-fire-safety, K-site/外構, **L-raw-materials** (生コン/アスコン/砕石/エポキシ/
  シーリング/鉄骨塗装), with `length-m` / `area-m2` / `spec` / `rating` / `unit`
  fields. **27 → 72 parts** (57 cots / 15 custom-fab).
- **Construction sequence 13 → 23 steps** with utilities woven in (引込 →
  地中埋設配管 → 基礎 → 鉄骨 → 屋根 → 外装 → 電気配線 → 圧空/データ → 照明 →
  床 → 衛生 → 消防 → 機械 → コンベア → ロボット → 外構舗装 → 外部動線 →
  外灯/フェンス → 植栽 → 通電/通水/通ガス試運転).

## Update v3 (2026-05-31) — engineering passes + IFC + procurement depth

Pushed from "representative boxes" toward "computed + checked design" at the
founder's request (clash detection / sizing / code-checks / IFC + 原材料・調達もと・
企業名・機器名). **Honest scope**: simplified engineering models with documented
assumptions — a real step up, but NOT a licensed engineer's stamped 構造/設備計算書,
確認申請, or 消防同意. New tools in the scene dir, all orchestrated by `kotoba_gen.py`:

- **`engineering.py`** — (1) **clash detection**: utility routes vs structure
  (柱/梁/壁) hard interference + utility-vs-utility proximity (<0.30 m
  coordination); (2) **sizing**: electrical (load schedule → demand → feeder
  current → %voltage-drop), water (fixture units → flow → Ø), drainage
  (run × min-slope → fall); (3) **code checks**: 建ぺい率/容積率/避難距離/消火栓
  カバー/駐車. Emits `engineering.json`, `clashes.json`, and `clash/* sizing/*
  code/*` kotoba datoms. **Found 12 clashes + 2 real defects** (drainage fall NG,
  single-hydrant coverage NG) — i.e. it does its job.
- **`ifc_export.py`** — scene → `factory.ifc` (IFC4 STEP, 956 entities / 70
  elements: IfcColumn/Beam/Wall/Slab/BuildingElementProxy/FlowSegment +
  IfcExtrudedAreaSolid geometry + spatial hierarchy + Pset 企業名/機器名/調達もと).
  Openable in BlenderBIM / IfcOpenShell; structurally valid (0 dangling refs).
- **`procurement.py`** — manufacturer(企業名) → 調達もと(商社/代理店) / 原産国 /
  リードタイム / channel, joined onto every part at generation time (representative).
  CycloneDX `publisher`=manufacturer, `supplier`=調達もと; raw materials (L) deepened
  with composition (生コン配合 / ミルシート級 / F10T). **72 → 74 parts**.
- **Rust**: `run_giemon_factory_v1` loads `clashes.json` and renders red (hard) /
  orange (coordination) clash markers; `giemonFactoryClashCount` JS hook.

## Update v4 (2026-05-31) — the factory built BY robotics (tatekata)

At the founder's request — "robotics でこの建築までも全て robotics で … 単に表示する
のではなくて、素材の調達・搬入・組み立てなど **すべての工程を robotics 手順に**" — the
construction itself is now modeled as an executable **robot task graph**, not just
a geometry reveal. Binds to the `tatekata` 建方 actor (ADR-2605250715).

- **`robots.edn`** — 施工ロボット registry (7: 自動建機 / 配筋 / コンクリ3Dプリンタ /
  鉄骨ボルト溶接 / パネル設置 / MEP / 内装AGV), each with reach / footprint / cycle /
  `:robot/process` (deposition | thermal-weld | none) / **honest maturity**
  (field-trial | partial | human-collab — none is turnkey autonomous). Every
  `construction.edn` step gets `:step/robot`; `kg/claim/robot/*` datoms.
- **`process_gen.py`** — expands each step into an **ordered robot operation
  sequence** covering the whole flow: **procure (調達 → 調達もと) → deliver (搬入,
  自律トラック) → stage (搬送・仮置き, AGV) → build (建方/据付/敷設/打設) →
  fasten (締結/溶接/養生) → inspect (検査 scan-to-BIM)**. **125 ops over 23 steps**,
  each with robot + materials (→ building.edn part + 調達もと) + logistics from→to +
  material process; `kg/claim/op/*` datoms (the executable task graph).
- **Buildability** (in `engineering.py`) — per step: robot reach vs work-zone
  (relocation setups), cycle-time vs schedule (robots needed), footprint —
  `build/*` datoms. All 23 schedule-feasible (with N setups reported).
- **Material-process solvers** (`kami-app-tatekata`, app-layer stand-ins, same
  honest posture as kabitori `MoldField` — NO granular/MPM/thermal-FEM):
  `deposit_field.rs` (concrete deposition/levelling height grid → printer steps)
  + `weld_field.rs` (moving heat-source fusion → bolter steps).
- **`kami-app-tatekata`** crate (path-deps `kami-app-giemon-factory`) — viewer
  `run_tatekata_v1`: each step's assigned robot performs its op sequence on
  kami-genesis; HUD shows the live op. `tatekata.htm` viewer.

### v5 (2026-05-31) — the construction PROCESS itself is physics-driven

At the founder's request ("シミュレーションも、ものを動かすのも、工事プロセスまでも
物理シミュレーションに基づいて"), the tatekata construction is governed by real
kami-genesis rigid-body physics, not scripted reveal:
- **`Agv::step_toward`** (new) — the delivery **cart** physically DRIVES 受入 →
  work-zone during 搬入/搬送 (clamped position-PD sized to overcome ground
  friction μN, floating-base + obstacle contact).
- **`Agv::step_free`** (new) — a material **payload** is DROPPED from height and
  FALLS + SETTLES under gravity + contact; its **settling fraction drives the
  build pace** (geometry reveal is gated by the physics, not a clock). Concrete
  steps feed the settle into `DepositField`, steel steps into `WeldField`.
- Validated by `cargo test`: `payload_free_falls_and_settles`,
  `cart_drives_toward_target`. Honest: rigid-body cart/payload/robot physics is
  real; material-process (concrete flow / weld pool) remains an app-layer field.

## Verification (all run 2026-05-31)

- `python3 kotoba_gen.py` (orchestrates process + buildability + engineering +
  IFC) → 74 parts / 23 steps / 7 robots / **125 robot ops** / 12 clashes / 3
  sizing / 5 code / 23 buildability → `kotoba_ingest.json` **272 entities**;
  `process.json` (125 ops), `robots.json`, `engineering.json`, `clashes.json`,
  `factory.ifc` (956), `factory.cdx.json` (74). All cross-checks (incl. op→step/
  material + step→robot resolution) pass.
- `cargo test -p kami-app-giemon-factory -p kami-app-tatekata` → **10 + 8 passed**
  (deposit/weld field math, process plan ordering, robot assignment). Both wasm
  bundles rebuilt (`tatekata` 636K, `giemon-factory` 508K).

### v3 figures (superseded)

- `python3 kotoba_gen.py` (orchestrates engineering + IFC) → `building parts=74
  cots=59 custom-fab=15`, `clashes=12 (hard=4 coord=8)`, `sizing={電気:OK 給水:OK
  排水:NG}`, `code_NG=[屋内消火栓 包含半径]`; wrote `kotoba_ingest.json` (**117
  entities** = 74 parts + 23 steps + 12 clash + 3 sizing + 5 code), `engineering.json`,
  `clashes.json`, `factory.ifc` (956 STEP entities / 0 dangling refs), `factory.cdx.json`
  (74). `cargo test -p kami-app-giemon-factory` → **9 passed** (+ clashes_load).
  `wasm-pack` viewer bundle rebuilt.

### v2 figures (superseded by v3 counts above)

- `python3 kotoba_gen.py` → `building parts=72 cots=57 custom-fab=15
  groups=[A-foundation..L-raw-materials]`, `construction steps=23
  nominal_programme_days=179`; wrote `factory.cdx.json` (72 components),
  `kotoba_ingest.json` (95 entities = 72 parts + 23 steps), `construction.order.json`
  (23 steps). All cross-checks (seq contiguity, DAG acyclicity, consumes/reveals
  resolution — now incl. `service_nodes`/`utilities`/`fixtures`/`site_*`) pass.
- `cargo test -p kami-app-giemon-factory` → **8 passed** (scene load, MEP+site
  present, obstacle counts, 4D order contiguity + reveal-id resolution, arm6 =
  6-DOF/7-body, arm cell settles finite, AGV = 4-DOF + blocked-by-obstacle,
  static_boxes coverage).
- `cargo build -p kami-app-giemon-factory --target wasm32-unknown-unknown`
  (rustup stable) → **Finished**, clean (the two `run_*` entries compile).
- Pre-existing env note: the default `cargo` on this host is Homebrew rust (no
  wasm32 std); wasm builds go through the rustup stable toolchain (as the repo's
  `wasm-pack` flow already does).

## Consequences

- The factory is now a first-class kotoba citizen: building materials and the
  construction programme are queryable datoms (critical path via VAET), and the
  same SSoT renders + animates in the engine. Adding/removing an element is a
  scene-json + EDN edit (regenerate, rebuild) — no bespoke code.
- Establishes the **4D-BIM-as-datoms** pattern reusable by the other Tier-B actor
  plants (igata foundry, tatekata construction site, etc.): scene.json layout +
  building.edn 建材 + construction.edn 手順 + a thin `kami-app-*-factory` crate.

## Future work

- Replace the AABB structural proxy with `kami-bim`/`kami-cae` solved frames
  (FEM) for a structural-adequacy gate.
- Drive the arm6 cells from a real assembly task graph (pick/place of giemon
  sub-assemblies on the conveyor) instead of a PD sweep.
- Ingest `kotoba_ingest.json` into a live `kotoba serve` in CI and assert the
  documented queries (parts/steps counts, machines-per-zone, critical path) as a
  regression gate, mirroring the kabitori pilot.
