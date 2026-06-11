# e7m-sim scene — `sarutahiko-r1-tomei-5km/`

**Status**: W4 cross-actor (sibling of `wadachi-r1-shibuya-1km`,
`suki-r1-tokachi-2km-pasture`). Heavy-truck highway scenario along the
Tomei expressway in Shizuoka.

## Binding

- **Robot class ADR**: ADR-2605252500 — sarutahiko (Class-8 heavy truck manufacturing, ~26-40 t GVWR Wave 1).
- **Sibling actor**: wadachi (operator-side autonomous mobility, ADR-2605242000) — sarutahiko is the manufacturing-side counterpart.
- **World-data ADR**: ADR-2605262500.
- **Substrate ADR**: ADR-2605261600 e7m-sim + G5 ≥0.75.
- **Compat ADR**: ADR-2605261800 kami-engine nv-compat.

## Scope

Tomei expressway (東名高速道路) corridor in Shizuoka, EPSG:4326 bbox
`[138.40, 35.10, 138.45, 35.11]` (~5km×1km strip — long-stretch highway
geometry, not square urban density).

| Layer | Source | Tier | Notes |
|---|---|---|---|
| Terrain (30m DEM) | SRTM `n35e138` | A | Coastal plain + slight elevation |
| Raster overlay (RGB) | Sentinel-2 L2A `T54SUE` | A | (re-uses Shibuya-area tile) |
| Vector roads | Overture transportation JP | A | Multi-lane expressway with shoulders |

This scene stress-tests the assembler on a **non-square bbox** (5:1
aspect ratio). The vector_roads ribbon emitter currently produces a
single horizontal strip; the wide aspect ratio makes that placeholder
geometry meaningfully different from Shibuya / Tokachi square bboxes.

## Constitutional non-goals

- Offensive truck modifications (armor / blast plate / military
  payload) = NEVER per ADR-2605252500 N4 (ADR-2605192100 §1.12
  Transparent Force only).
- Same NVIDIA Omniverse / PhysX exclusions as other e7m-sim scenes.
