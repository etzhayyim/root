# sarutahiko-factory-r0 — 猿田彦 Class-8 truck assembly plant (R0 design)

The **full-robotics factory that builds the sarutahiko (猿田彦) Class-8 cargo
truck** of [ADR-2605252500](../../../../90-docs/adr/2605252500-sarutahiko-heavy-truck-manufacturing-r0.md),
designed end-to-end in kami-engine + kotoba. It **reuses the giemon-factory 4D-BIM
pattern** ([ADR-2606010030](../../../../90-docs/adr/2606010030-giemon-factory-r0-kami-engine-kotoba-4d-bim.md))
— same EDN SSoT → SBOM → kotoba ingest → 4D order → engineering passes → IFC
toolchain — applied to a 180 m × 90 m heavy steel portal-frame truck plant, and
adds the truck-line production robots including the **積込ロボット (loading robot)**.

Governing ADR: [ADR-2606013100](../../../../90-docs/adr/2606013100-sarutahiko-truck-factory-full-robotics-and-loader.md).

## SSoT files (hand-authored)

| File | What |
|---|---|
| `factory.scene.json` | plant layout: walls / 12 columns / 4×90m-span beams / 7 zones (受入→L1 フレーム→L2 パワートレイン→L3 キャブ→塗装→L4 GA結合→L5 EOL) / truck-line machines / EMS conveyor / 8 arm6 cells / 2 part-AGVs / **2 loaders** / full MEP (受電/給排水/ガス/圧空/通信/消火) / 外構 + 出荷ヤード + 2 carriers + 2 finished trucks |
| `building.edn` | 77-part 建材 + 設備 BOM, groups A-L. Group F = truck-line equipment: F1 frame jig · F2 1600t servo press · F3 BIW weld jig · F4 waterborne paint booth · F5 EMS conveyor · F7 Class-8 dyno · F8 arm6 cells · F9 AGV · **F10 積込ロボット** · F11 marriage gantry · F12 EOL CMM |
| `construction.edn` | 25-step 4D 建築手順, each step → a 施工ロボット (robots.edn). Heavy 90 m span uses `robot:crane` |
| `robots.edn` | 8 **construction** robots (tatekata 建方 fleet that BUILDS the plant). The **production** robots that manufacture trucks live in `factory.scene.json` + building.edn group F, NOT here |
| `production.edn` | the **manufacturing line**: 8 ordered stations a truck body flows through — 受入 → L1 フレーム溶接 → L3 キャブBIW → 塗装 → L4 結合 → L5 EOL検査 → ステージング → 積込/出荷. Each station → arm6 cell + cycle takt. **PRODUCTION layer, distinct from `construction.edn` (which builds the plant)** |

## Generated

`python3 kotoba_gen.py` (plant): `factory.cdx.json` (CycloneDX SBOM, 77 components)
· `kotoba_ingest.json` (286 EAVT entities: part/* + step/* + robot/* + op/* +
clash/sizing/code/build/*) · `construction.order.json` (25-step 4D order) ·
`process.json` (137 robot ops: 調達→搬入→搬送→建方→締結→検査) · `engineering.json` +
`clashes.json` (6 clashes; electrical OK via 325sq×N parallel feeders, water OK,
**drainage NG / 避難距離 NG / 消火栓半径 NG** — honest large-plant findings) ·
`robots.json` · `factory.ifc` (IFC4, 1112 STEP entities, BlenderBIM-openable).

`python3 production_gen.py` (line): `production.order.json` (8 stations) +
`production_ingest.json` (35 EAVT entities: station/* + mfgop/* — 27 manufacturing
ops 供給→搬送→加工→検査→搬出).

## kami-engine viewer

Crate `kami-app-sarutahiko-factory` (**4 WASM entries** over this scene):

- `run_sarutahiko_factory_v1` — completed plant, live arm6 cells + AGVs + clash markers
- `run_sarutahiko_factory_build_v1` — 4D 建築手順 playback (reveal in `:seq` order)
- `run_sarutahiko_factory_produce_v1` — **生産ライン**: one truck body flows through
  the 8 stations on kami-genesis physics (`step_toward`), arm6 cells working,
  **recoloured bare-steel → painted at the paint station**, then handed to the
  loader and shipped — a truck made end-to-end through the 5-layer process
- `run_sarutahiko_factory_load_v1` — **積込ロボット showcase**: a straddle loader
  drives across the 出荷ヤード (clamped position-PD over ground friction),
  straddles a finished truck, carries it, and **lowers it onto a carrier deck
  where it settles with real kami-genesis sphere-on-AABB contact**

Browser viewer: `60-apps/…/svelte/static/sarutahiko-factory.htm` (`?mode=live|build|produce|load`).
Build: `wasm-pack build kami-app-sarutahiko-factory --target web --release` →
copy `pkg/*` into `…/static/sarutahiko-factory/`.

Native tests (`cargo test -p kami-app-sarutahiko-factory`): **14 green**, incl.
`production_line_makes_a_truck_end_to_end` (paint → load → ship, settled on
carrier) and `loader_picks_and_places_truck_on_carrier` (full pick → carry →
settle cycle).

## HONEST scope (R0)

- Design + data-model + physics-simulation only. **No real plant, no procurement,
  no 確認申請 / 消防同意 / 受電契約.** All `:representative` figures.
- Heavy-truck manufacturing is capital-intensive (ADR-2605252500 §Consequences):
  R3 community-scale ≥100 veh/month is **Council Lv6+ + LANDS.md plant-site gated**.
- The sarutahiko cells (`orgs/etzhayyim/com-etzhayyim-sarutahiko/cells/`) remain R0 scaffold
  (`.solve()` raises `RuntimeError`) — this scene is the **plant-design layer**,
  it does not activate manufacturing capability.
- Engineering passes are simplified models (loads / fixture-units / code limits
  embedded) — they flag problems, they do not certify; not a licensed engineer's
  stamped 構造/設備計算書.
- Loader transport is real physics; the lift/lower is a controlled hydraulic
  motion (a real loader does not free-drop a 9 t truck). 3-D arm + carrier-polygon
  collision + live ingest are deferred.
- N1/N2/N4 etc. (military / weapons / mining-haul trucks) remain constitutional
  non-goals — this plant produces the **civilian Class-8 cargo truck only**.
