# e7m-sim scene — `futawa-r1-mountain-3km/`

**Status**: W4 cross-actor (sibling of wadachi / suki / sarutahiko / igata).
Small-displacement motorcycle on a winding mountain road.

## Binding

- **Robot class ADR**: ADR-2605261330 — futawa (motorcycle, ≤250cc / ≤200kg Wave 1).
- **World-data ADR**: ADR-2605262500.
- **Substrate ADR**: ADR-2605261600.

## Scope

Mountain road in Tochigi-Nikko area, EPSG:4326 bbox
`[139.59, 36.74, 139.62, 36.755]` (~2.7km × 1.7km — elevated terrain
exercises the flat-grid terrain placeholder's biggest weakness, which
W2.1 will fix with real SRTM triangulation).

| Layer | Source | Tier |
|---|---|---|
| Terrain (30m DEM) | SRTM `n36e139` | A |
| Raster overlay (RGB) | Sentinel-2 L2A `T54SVE` | A |
| Vector roads | Overture transportation JP | A |
