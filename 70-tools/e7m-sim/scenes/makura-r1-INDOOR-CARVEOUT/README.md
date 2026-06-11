# scene path reserved — `makura-r1-INDOOR-CARVEOUT/`

**Status**: NO scene.yaml. Constitutional carve-out per ADR-2605262500
W4 — makura (foam pillow, ADR-2605261115) is an INDOOR-only Tier-B
actor and does NOT have an outdoor geospatial scene.

## Rationale

ADR-2605262500's world-data ingestion pipeline (SRTM / Sentinel-2 /
Overture / MS-Buildings / OpenUSD / Mapillary / Objaverse-XL NC) is
optimized for **outdoor** robotics-sim consumers. makura's R1 task
(foam-pour density characterization + PU shred-fill mixing) operates
entirely inside a factory-floor envelope where:

- Terrain layer is irrelevant (floor is flat concrete).
- Raster overlay is irrelevant (no aerial imagery contributes).
- Vector roads / buildings are irrelevant (single building interior).
- Tier-C street imagery is irrelevant (no outdoor scene at all).

The factory-floor scene is the responsibility of a separate
**ADR-TBD** ("e7m-sim indoor scene primitives") covering floor /
walls / ceiling / lighting / safety-zone primitives, which is OUT OF
SCOPE for ADR-2605262500.

## Why land this README

To prevent accidental "we forgot makura" audit findings: this empty
scene directory IS the audit artifact saying makura R1 outdoor scene
is intentionally not produced under ADR-2605262500.

## What W4 covers for makura instead

W4 cross-actor count for ADR-2605262500:

| Tier-B actor | W4 scene | Status |
|---|---|---|
| wadachi | shibuya-1km | shipped |
| suki | tokachi-2km-pasture | shipped |
| sarutahiko | tomei-5km | shipped |
| igata-outdoor | foundry-yard-50m | shipped |
| futawa | mountain-3km | shipped |
| tatekata | construction-site-100m | shipped |
| hodoki | elv-yard-200m | shipped |
| tsutae | shibuya-crossing-200m | shipped |
| **makura** | **INDOOR carve-out** | **N/A — needs separate indoor ADR** |
| **watatsumi** | submersible — bathymetry sub-ADR | deferred per ADR-2605262500 §6 |

W4 = 8/10 actors covered. makura + watatsumi are explicit
out-of-scope carve-outs, not gaps.
