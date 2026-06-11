# e7m-sim scene — `suki-r1-tokachi-2km-pasture/`

**Status**: W4 cross-actor first additional scene (sibling of
`wadachi-r1-shibuya-1km`). Scene YAML committed; world-data layer
CIDs are placeholders until operator pins real SRTM + Overture +
Sentinel-2 CIDs via `e7m-dataset pull` for this bbox.

## Binding

- **Robot class ADR**: ADR-2605261500 — suki (farm tractor manufacturing, ≤200 hp Wave 1).
- **Operator class**: mitsuho (food / agriculture, ADR-2605261015).
- **World-data ADR**: ADR-2605262500 — robotics-sim world-data ingestion + kami-usd pipeline.
- **Substrate ADR**: ADR-2605261600 — e7m-sim 5-stack reference + G5 ≥0.75 quality gate.
- **Compat ADR**: ADR-2605261800 — kami-engine nv-compat (kami-usd / kami-genesis / kami-pbrt).

## Scope

Hokkaido Tokachi pasture area, EPSG:4326 bbox
`[143.18, 42.91, 143.20, 42.93]` (~2km×2km).

| Layer | Source | Tier | W phase |
|---|---|---|---|
| Terrain (30m DEM) | SRTM `n42e143` | A | W1 |
| Raster overlay (RGB + NDVI optional) | Sentinel-2 L2A | A | W1 |
| Vector roads (farm tracks) | Overture transportation JP | A | W1 |
| Vector landuse (fields) | Overture base/land_use JP | A | W2 (new layer kind) |

This scene exercises a **non-urban** outdoor bbox to stress test the
assembler against Shibuya's urban-density assumptions. Suki's R1 sim
will run vehicle dynamics in this scene to validate that the pipeline
generalizes to agricultural settings.

## Constitutional non-goals (R0-R3, immutable)

- NVIDIA Omniverse / Isaac Sim runtime / OptiX / RTX Renderer /
  Replicator / DriveSim / Nucleus = NEVER (ADR-2605261600 N3 +
  ADR-2605261800 §2(b)).
- NVIDIA PhysX backing = NEVER. All physics through `kami-genesis`.
- Mega-tractor (≥400 hp) sim variant = N3 post-R3 + Council Lv6+
  (ADR-2605261500 non-goals).
