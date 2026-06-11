# e7m-sim scene — `wadachi-r1-shibuya-1km/`

**Status**: W1 path reservation. Scene YAML committed; world-data layer
CIDs are placeholder until W1 fetchers (`sentinel2.py` / `srtm.py` /
`overture.py`) land and emit real `datasetPin` records.

## Binding

- **Robot class ADR**: ADR-2605242000 — wadachi (autonomous mobility R&D, SAE Level 4 ceiling).
- **World-data ADR**: ADR-2605262500 — robotics-sim world-data ingestion + kami-usd pipeline (this scene is the first testbed per §9).
- **Substrate ADR**: ADR-2605261600 — e7m-sim 5-stack reference + G5 ≥0.75 quality gate.
- **Compat ADR**: ADR-2605261800 — kami-engine nv-compat (kami-usd / kami-genesis / kami-pbrt backends).
- **Inference ADR**: ADR-2605215000 — Murakumo-only (no commercial GPU rental).

## Scope

Tokyo 23-ku Shibuya 1km×1km outdoor scene, EPSG:4326 bbox
`[139.69, 35.65, 139.71, 35.67]`.

| Layer | Source | Tier | W phase |
|---|---|---|---|
| Terrain (30m DEM) | SRTM `n35e139` | A | W1 |
| Raster overlay (RGB) | Sentinel-2 L2A `T54SUE` B432 | A | W1 |
| Vector roads | Overture transportation JP | A | W1 |
| Vector buildings | Overture buildings JP | A | W1 |
| Tier-C props (cars) | Objaverse-XL NC subset | C | W3 (`-nc-` variant sibling dir) |

W3 variant: `wadachi-r1-shibuya-1km-nc/` — same world layers + Tier-C
prop instances. Derived sim recordings from the `-nc-` variant carry
`-nc-` infix and route through judah LiteLLM + SBT-gate only (G4 + G5).

## W1 → W2 gate (per ADR-2605262500 + ADR-2605261600)

W2 PoC must satisfy:

1. `assemble-usd-scene.py` ingests this `scene.yaml`, resolves all 4
   Tier-A `datasetPin_at` placeholders to real CIDs, and emits a
   deterministic `.usd` file (G6).
2. The `.usd` loads in `e7m-sim` via `kami-rt` + `kami-usd` + `kami-genesis`
   without runtime errors.
3. Isaac Sim reference scene is generated **once** on a one-time-use
   isolated trial machine never connected to religious-corp infra
   (ADR-2605261600 G5).
4. PSNR/SSIM/Chamfer/IoU min ≥ 0.75 across 32 viewpoints on a 200m
   road segment (G11).
5. `simulationRunAttestation` lexicon emitted on each sim run (G6 of
   ADR-2605261600).

## Constitutional non-goals (R0-R3, immutable)

- NVIDIA Omniverse / Isaac Sim runtime / OptiX / RTX Renderer /
  Replicator / DriveSim / Nucleus = NEVER (ADR-2605261600 N3 +
  ADR-2605261800 §2(b)).
- NVIDIA PhysX backing = NEVER. All physics through `kami-genesis`
  (Genesis Apache-2.0). PhysX nv-compat facade is API-only.
- Commercial GPU rental for sim runs = NEVER (ADR-2605215000 +
  ADR-2605262500 N10).
- Cesium ion / Google Earth / Mapillary commercial tier = NEVER
  (ADR-2605262500 N1 + N2 + N5).
