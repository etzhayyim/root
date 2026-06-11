# e7m-sim scene — `igata-r1-foundry-yard-50m/`

**Status**: W4 cross-actor. Foundry yard outdoor scenario for igata R1
benchtop HPDC commissioning (ADR-2605261215).

## Binding

- **Robot class ADR**: ADR-2605261215 — igata R1 (benchtop ≤500 ton HPDC commissioning).
- **Parent**: ADR-2605261200 igata R0 (HPDC megacasting Tier-B).
- **World-data ADR**: ADR-2605262500.
- **Substrate ADR**: ADR-2605261600.

## Scope

A small foundry yard, EPSG:4326 bbox `[136.880, 35.180, 136.881, 35.181]`
(~50m × 50m — typical industrial yard scale).

| Layer | Source | Tier | Notes |
|---|---|---|---|
| Terrain (30m DEM) | SRTM `n35e136` | A | Flat industrial site |
| Raster overlay (RGB) | Sentinel-2 L2A `T53SQA` | A | Aichi area |
| Vector roads | Overture transportation JP | A | Yard access road |
| Vector buildings | Overture buildings JP | A | Workshop / warehouse |

Exercises the assembler at **small bbox** scale (50m vs the
1km-2km-5km scenes already shipped). Validates the projection
approximation holds at sub-100m resolution.

## Constitutional non-goals

- Mega-casting press ≥7500 ton clamping force = N1 post-R3 + Council Lv6+ (ADR-2605261200).
- Same NVIDIA Omniverse / PhysX exclusions.
