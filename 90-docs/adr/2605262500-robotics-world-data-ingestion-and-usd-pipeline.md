---
id: adr-2605262500-robotics-world-data-ingestion-and-usd-pipeline
title: "ADR-2605262500: Robotics-sim world-data ingestion (Sentinel-2 raster + SRTM/3DEP DEM + Overture/OSM/MS Buildings vector + OpenUSD samples + Mapillary street imagery Tier C + Objaverse-XL NC 3D asset Tier C) via e7m-dataset → kami-usd conversion → e7m-sim — sibling of ADR-2605262400 on the geospatial-3D axis, wadachi R1 outdoor scene as first testbed"
status: proposed
doc_type: adr
topic: robotics-sim-world-data-ingestion
authoritative: true
last_verified: 2026-05-26
priority: 6.0
axis: architecture
weight: 0.55
priority_note: "Single SoT for how every R1+ outdoor sim consumer (wadachi / suki / watatsumi / sarutahiko / futawa / tatekata / hodoki / makura / igata-outdoor / tsutae sim layers per ADR-2605261600 binding list) loads world geospatial data into kami-engine USD scenes. Two-path split: (A) SIM SCENE ASSEMBLY = scene-recipe.toml → assemble-usd-scene.py → tinyusdz (kami-usd) → e7m-sim load via kami-rt + kami-genesis (PhysX nv-compat facade ONLY, NVIDIA PhysX N1..N9 NEVER per ADR-2605261800 §2(b)); (B) BAIEN TRAIN CORPUS reuses ADR-2605262400 §4 cold path verbatim (no duplication). Tier-A sources (Sentinel-2 Copernicus free / SRTM public-domain / 3DEP public-domain / OSM ODbL / Overture CDLA-Permissive / MS Buildings ODbL / OpenUSD Apache-2.0) produce publishable artifacts. Tier-C sources (Mapillary CC-BY-SA street imagery / Objaverse-XL NC subset) admitted under G13 fleet-internal carve-out per user 2026-05-26 内部利用前提 decision — derived sim recordings (rosbag/video) MUST carry `-nc-` infix, MUST NOT publish, fleet-internal via judah LiteLLM + SBT-gate only (same pattern as ADR-2605262100 R1.4 + ADR-2605262400 §1). PII filter precedes Charter Rider §2 scan; Mapillary face/license-plate/child blur verification at fetch time is MANDATORY (extension to ADR-2605262400 §6 PII filter scope). Inference path UNCHANGED per ADR-2605215000 (Murakumo fleet only); no commercial GPU rental for sim runs or for any sim-derived artifact unless ADR-2605262200 train-rental amendment ratifies. 12 gates G1..G12, 10 non-goals N1..N10, 4-wave delivery W0..W4. First testbed = wadachi R1 outdoor scene Tokyo 23-ku Shibuya 1km×1km."
authoritative_for:
  - robotics-sim world-data ingestion policy for every R1+ outdoor sim consumer
  - separation of sim scene assembly (hot path) vs baien train corpus reuse (cold path delegated to ADR-2605262400)
  - Tier-A vs Tier-C license ladder for sim-consumed geospatial/3D datasets (sibling of ADR-2605262400 ladder)
  - G13 fleet-internal carve-out applied to NC-licensed sim source data (Mapillary, Objaverse-XL NC)
  - SceneRecipe TOML schema for assemble-usd-scene.py
  - new fetcher set in 70-tools/e7m-dataset/src/e7m_dataset/fetchers/ (sentinel2, srtm, usgs_3dep, overture, ms_buildings, openusd_samples, mapillary, hf_3d_nc)
  - new subdataset taxonomy under 90-docs/baien/datasets/geo/{sentinel2,srtm,usgs-3dep,overture,ms-buildings,openusd,mapillary,hf-3d-nc}/
  - kami-usd conversion pipeline contract (kami-engine R1.0 binding for outdoor sim scenes)
  - extension of PII filter scope to face/license-plate/child blur (Mapillary-specific)
  - first wadachi R1 outdoor sim testbed scene (Tokyo 23-ku Shibuya 1km×1km)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605215100-etzhayyim-maps-sentinel-mlx-murakumo-fleet
  - adr-2605241500-etzhayyim-dataset-cid-substrate
  - adr-2605242000-roso-pattern-frontier-distill
  - adr-2605261600-robotics-simulation-substrate-r0
  - adr-2605261800-nvidia-omniverse-stack-api-compat
  - adr-2605262100-baien-moemoekyun-r1-phase0-coding-train
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262400-public-data-organism-ipfs-ingestion
related:
  - adr-2605200300-defense-isr-sensor-fusion
  - adr-2605262200-charter-rider-2i-baien-train-rental-carveout
  - adr-2605262300-baien-moemoekyun-r2-runpod-b200-train-architecture
  - adr-2605261500-suki-farm-tractor-tier-b-actor-r0
  - adr-2605252200-watatsumi-civilian-submersible-r0
  - adr-2605252500-sarutahiko-heavy-truck-manufacturing-r0
  - adr-2605261330-futawa-motorcycle-tier-b-actor-r0
  - adr-2605250715-tatekata-construction-tier-b-actor-r0
  - adr-2605261215-hodoki-elv-disassembly-tier-b-actor-r0
  - adr-2605261115-makura-foam-pillow-tier-b-actor-r0
  - adr-2605261115-igata-megacasting-tier-b-actor-r0
  - adr-2605261300-tsutae-handheld-communication-tier-b-actor-r0
supersedes: []
superseded_by: []
---

# ADR-2605262500: Robotics-sim world-data ingestion + kami-usd conversion pipeline

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

The robotics-sim substrate (ADR-2605261600, `e7m-sim`) plus the
Omniverse-API-compat layer (ADR-2605261800, `kami-engine` /
`kami-usd` / `kami-genesis`) define **what** runs the simulation, but
not **what world data** populates the simulated outdoor scenes consumed
by wadachi (autonomous mobility, ADR-2605242000) and the other R1+ outdoor
sim consumers (suki / watatsumi / sarutahiko / futawa / tatekata /
hodoki / makura / igata-outdoor / tsutae).

What already exists, and what this ADR builds on rather than reinventing:

- `e7m-dataset` (ADR-2605241500) — DataLad + git-annex `directory` +
  IPFS pinner + `com.etzhayyim.substrate.datasetPin` Lexicon as the
  receipt. Four existing fetchers: HF / GeoNames / OSM Geofabrik /
  Wikidata SPARQL.
- `maps_sentinel_murakumo` M1 T0 (ADR-2605215100) — Sentinel-2
  preprocessing prototype at fleet scale; this ADR ports that proven
  pipeline into the `e7m-dataset` fetcher contract.
- `e7m-sim` R0 charter (ADR-2605261600) — OSS USD+Hydra+MuJoCo MJX +
  Embree + BlenderProc 5-stack reference, with quantitative quality
  gate ≥ 0.75 vs Isaac Sim ground truth (PSNR/SSIM/Chamfer/IoU), Murakumo
  capacity caps, and **N1..N9 absolute exclusion** of Omniverse / Isaac
  Sim / Isaac Lab / OptiX / RTX Renderer / Replicator / DriveSim /
  Omniverse Cloud / Nucleus.
- `kami-engine` R1.0 (ADR-2605261800) — 13 KAMI-native Rust crates +
  Python `nv_compat` facade. `kami-usd` (tinyusdz-based) is the USD
  emitter; `kami-genesis` (Genesis Apache-2.0 5-solver) is the physics
  primary; **PhysX N1..N9 NEVER**, only the API-compat facade.
- ADR-2605262400 (sibling, today same session) — ships netreg/DNS/BGP/
  web-graph organism perception + training corpus with Tier A/B/C +
  G13 carve-out + PII filter + Charter Rider §2 scan. The framework
  itself (Tier ladder, G13 invariant, PII filter precedence, passive-
  only network discipline) is reused verbatim by this ADR — only the
  source set, the cold-path consumer, and the gates that depend on
  consumer-specific invariants differ.

What is **missing** until this ADR lands:

1. No fetcher in `e7m-dataset` for the geospatial raster + 3D vector +
   street-level imagery sources that outdoor robotics sim needs.
2. No declarative recipe format for "this sim scene needs these CIDs at
   these layers".
3. No pipeline binding from `datasetPin` CIDs into `kami-usd` USD
   stages that `e7m-sim` can load.
4. No PII filter extension for street-level imagery (face / license
   plate / child blur) — ADR-2605262400 §6 covers RFC-5321 email,
   E.164 phone, postal addresses, WHOIS blocks, but not vision PII.
5. No first wadachi R1 outdoor sim testbed scene committed to a
   recipe TOML.

The user's explicit answers in session 2026-05-26 (this exchange):

- **非営利 → NC sources OK**. CC-BY-NC datasets are admissible because
  the religious-corp is non-profit; the share-alike concern (Mapillary
  CC-BY-SA) is handled by **never publishing derived artifacts**.
- **内部利用前提**. Tier-C-derived sim recordings (rosbag / video /
  trained policy weights) are fleet-internal only, G13 backstop
  applies (same precedent as ADR-2605262100 R1.4 and ADR-2605262400
  Wave 3).
- **First testbed = wadachi R1 outdoor scene**, not suki / watatsumi.
  Watatsumi (submersible) needs a bathymetry dataset axis instead
  (GEBCO / Copernicus Marine) which is deferred to a separate sub-ADR.

Constraint surface (in addition to everything ADR-2605262400 already
constrains):

- **e7m-sim G5 (ADR-2605261600)** — reference scene generation MUST
  occur once on a one-time-use isolated trial machine never connected
  to religious-corp infra. This means the Isaac Sim ground-truth
  reference for the wadachi Shibuya scene is generated offline and the
  resulting metrics CSV is the only artifact imported back; no
  Omniverse/Isaac binaries ever reach religious-corp infra.
- **kami-engine §2(b) (ADR-2605261800)** — PhysX / OptiX / RTX
  Renderer / Replicator are N1..N9 NEVER. All physics goes through
  `kami-genesis`. All rendering goes through `kami-pbrt` (Mitsuba 3
  upstream-PR-only 90-day window per ADR-2605261800 §D11) with Embree
  CPU fallback.
- **ADR-2605215000 §2(i)** — Sim run inference (e.g. perception model
  inside the sim'd autonomous vehicle) routes through Murakumo only.
  Train rental for sim-trained policies is gated on ADR-2605262200
  ratification (~2026-07-19 earliest).
- **Charter Rider §2(c) surveillance avoidance** — Mapillary street
  imagery contains pedestrian faces, license plates, and children.
  The face/plate/child blur step is a hard PII gate, not a "best
  effort" — fail-closed if blur model output is missing or below
  threshold.

# Decision

Adopt a sibling pipeline to ADR-2605262400 on the geospatial-3D axis,
with explicit reuse of the ADR-2605262400 framework (Tier A/B/C ladder,
G13 backstop, Charter Rider §2 scan, PII filter precedence) and an
additive scene-assembly cold path that emits USD for `e7m-sim`.

## §1. Two-path architecture (sim scene assembly vs train corpus reuse)

```
public archive (Sentinel-2 / SRTM / 3DEP / Overture / OSM / MS Buildings /
                 OpenUSD samples / Mapillary / Objaverse-XL NC subset)
        │
        ▼
e7m-dataset add / pull <source>
        │  (PII filter incl. face/plate/child blur for Mapillary;
        │   Charter Rider §2 scan; license tag attached)
        ▼
DataLad subdataset under 90-docs/baien/datasets/geo/<source>/<rev>/
        │
        ▼
git-annex `directory` special remote on local volume
        │
        ▼
e7m-dataset publish-ipfs <subdataset>
        │
        ▼
IPFS Kubo (replicationMin: 2)
        │
        ▼
com.etzhayyim.substrate.datasetPin record on PDS (receipt)
        │
        ├─────────────► (A) SIM SCENE ASSEMBLY (hot path, THIS ADR)
        │                scene-recipe.toml (per-sim-scene)
        │                → assemble-usd-scene.py
        │                   (resolve datasetPin → CID → fetch via Kubo HTTP)
        │                → tinyusdz emit USD stage (kami-usd)
        │                → e7m-sim load (kami-rt + kami-genesis solver)
        │                → wadachi R1 sim run
        │                → rosbag/video output
        │                  (PostSink BLOCKS tier-C-tagged sim outputs
        │                   on public paths — G13 backstop, same as
        │                   ADR-2605262400 §5 R9 rule)
        │
        └─────────────► (B) BAIEN TRAIN CORPUS (cold path)
                         REUSES ADR-2605262400 §4 corpus-recipe.toml
                         verbatim. No duplication. The same fetchers
                         feeding (A) can also feed (B) by reference.
```

The boundary between (A) and (B) is identical to ADR-2605262400's
boundary, just with a different cold-path consumer. The hot path here
ends in a USD stage loaded by `e7m-sim`; in ADR-2605262400 it ended in
an `Observation` consumed by joucho cadence. Both share `e7m-dataset` +
`datasetPin` upstream.

## §2. Data-source ladder (license × tier × scene-role)

| Source | Coverage | License | Tier | Fetcher | Bucket | Sim role |
|---|---|---|---|---|---|---|
| Sentinel-2 L2A | global 10m raster | Free, attrib (Copernicus) | A | new `sentinel2.py` (ports ADR-2605215100 M1 T0) | `geo/sentinel2/` | terrain texture, semantic seg input |
| SRTM 1-arc | global 30m DEM | public-domain (NASA) | A | new `srtm.py` (OpenTopography mirror) | `geo/srtm/` | terrain elevation (global) |
| USGS 3DEP | US 1m DEM | public-domain | A | new `usgs_3dep.py` | `geo/usgs-3dep/` | terrain elevation (US high-res) |
| OSM Geofabrik PBF | global vector | ODbL 1.0 | A | exists (`osm.py`, shared with ADR-2605262400) | `geo/osm/` (shared) | road / building / POI vector |
| Overture Maps | global vector unified | CDLA-Permissive 2.0 | A | new `overture.py` | `geo/overture/` | primary road + building source |
| MS Global Building Footprints | global buildings | ODbL 1.0 | A | new `ms_buildings.py` | `geo/ms-buildings/` | building polygon fallback |
| OpenUSD samples (Pixar) | reference 3D | Apache 2.0 | A | new `openusd_samples.py` | `geo/openusd/` | reference scenes + materials |
| Mapillary street imagery | global street-level | CC-BY-SA 4.0 | **C** (SA propagates; internal use only via G13) | new `mapillary.py` | `geo/mapillary/` | street imagery synth / texture (W3+) |
| Objaverse-XL NC subset | object 3D | mixed CC-BY-NC | **C** | new `hf_3d_nc.py` | `geo/hf-3d-nc/` | sim prop library (cars, pedestrians, signs) |

Notes:

- **Mapillary CC-BY-SA tier classification**. Strictly the license is
  share-alike not non-commercial, so it could be Tier B in
  ADR-2605262400's ladder. However, sim recordings derived from
  Mapillary frames (which `e7m-sim` would render directly as texture
  or as inputs to a learned synth model) inherit the SA obligation,
  which would force the religious-corp to publish those recordings
  under CC-BY-SA — incompatible with Apache 2.0 + Charter Rider for
  redistribution. Per user 2026-05-26 内部利用前提 decision, **Mapillary
  is treated as Tier C in this ADR**: ingest allowed for fleet-
  internal training and sim use, but derived artifacts MUST NOT
  publish. The G13 backstop covers both NC and SA-with-no-redistribute
  cases identically.
- **OSM ODbL** is also share-alike-flavored ("share-alike" for derived
  databases). The sim consumption pattern (rasterize road centerlines
  into a USD ribbon, no database redistribution) is well within
  ODbL's "Produced Work" exception. ADR-2605262400 already treats
  OSM as Tier A on the same reasoning. Preserved.
- **GeoLite2 CC-BY-SA** is admitted as Tier A by ADR-2605262400 §2
  because it's network metadata (IP→geo) that does not flow into sim
  recordings. Not used by this ADR's hot path.

Tier D (commercial high-res satellite e.g. Maxar, commercial city 3D
e.g. Vexcel, commercial sim asset libraries e.g. NVIDIA SimReady) is
**out of scope** and remains prohibited per CHARTER-RIDER §2 + the
ADR-2605261800 §2(b) Omniverse exclusion.

## §3. SceneRecipe abstraction (YAML, extending existing `scenes/<name>/scene.yaml`)

**Convention amendment (2026-05-26, post-landing)**: this ADR initially
specified TOML files under `70-tools/e7m-sim/recipes/`, but the existing
e7m-sim pattern established by ADR-2605261800 R1.1 (cartpole) is
`70-tools/e7m-sim/scenes/<name>/scene.yaml` (YAML). Honoring the existing
convention, the SceneRecipe lives as a new `world:` section inside the
existing `scene.yaml` schema. The schema file path is
`70-tools/e7m-sim/scenes/_schema/scene.schema.json` (JSON Schema, valid
across cartpole / kusawake / wadachi-r1-shibuya-1km and future scenes).

Example scene (`70-tools/e7m-sim/scenes/wadachi-r1-shibuya-1km/scene.yaml`):

```yaml
# wadachi R1 outdoor sim scene — Tokyo 23-ku Shibuya 1km×1km (ADR-2605262500 W1)

adr: ADR-2605262500
phase: W1
sim_consumer: wadachi-r1

# §3 SceneRecipe — world data composition from datasetPin CIDs
world:
  crs: "EPSG:4326"
  bbox: [139.69, 35.65, 139.71, 35.67]   # Shibuya 1km×1km
  output_subdataset: "sim-scenes/wadachi/r1/shibuya-1km/261015/"

  layers:
    - kind: terrain
      source_subdataset: "geo/srtm/n35e139"
      datasetPin_at: "at://did:web:dataset-pinner.etzhayyim.com/com.etzhayyim.substrate.datasetPin/<rkey>"
      tier: A
      shader: "kami-pbrt:Soil_Grass"

    - kind: raster_overlay
      source_subdataset: "geo/sentinel2/T54SUE/261001"
      datasetPin_at: "at://...<rkey>"
      tier: A
      band_mix: "RGB-B432"

    - kind: vector_buildings
      source_subdataset: "geo/overture/buildings/2604-release/jp"
      datasetPin_at: "at://...<rkey>"
      tier: A
      extrude_attr: "height"
      default_height_m: 8.0

    - kind: vector_roads
      source_subdataset: "geo/overture/transportation/2604-release/jp"
      datasetPin_at: "at://...<rkey>"
      tier: A
      material: "kami-pbrt:Asphalt"

  props:
    - kind: object_3d_instances
      source_subdataset: "geo/hf-3d-nc/passenger-car-set-vol2"
      datasetPin_at: "at://...<rkey>"
      tier: C   # G13: derived sim outputs from this scene MUST -nc- + fleet-internal
      count: 50
      placement_strategy: "road_lane_center_jitter"

# existing scene.yaml schema sections (per cartpole / kusawake convention)
scene:
  num_envs: 8
  dt: 0.01
  gravity: [0.0, 0.0, -9.81]

robot:
  urdf: ./wadachi-vehicle-r1.urdf
  base_link: chassis
  spawn:
    pos: [0.0, 0.0, 0.5]
    rot: [1.0, 0.0, 0.0, 0.0]

quality_gate:
  reference_baseline: "isaac_sim_shibuya_1km_v1"
  metrics:
    psnr_min_db: 25.0
    ssim_min: 0.85
    chamfer_max_m: 0.05
    iou_min_at_0p1m_voxel: 0.75
  combined_target: 0.75   # G11 — ADR-2605261600 G5 inheritance
```

Scene YAMLs live in git → audit trail (G10). The `world:` section is
new (this ADR); `scene:` / `robot:` / `quality_gate:` follow the
ADR-2605261800 R1.1 cartpole convention.

## §4. kami-usd conversion pipeline

New tool: `70-tools/e7m-sim/scripts/assemble-usd-scene.py`.

Behavior:

1. Parse `scenes/<name>/scene.yaml`, validate against `scenes/_schema/scene.schema.json`. Reads the `world:` section per §3.
2. Resolve every `datasetPin_at` → IPFS CID via PDS lookup.
3. **Tier ceiling check**: `max(layer.tier, prop.tier)`. If any == "C",
   verify `target_scene` and `output_subdataset` carry `-nc-` infix or
   abort fail-closed. Same convention as ADR-2605262400 §4 step 3.
4. **Defense-in-depth rescan**: Charter Rider §2 + PII filter (incl.
   face/plate/child blur verification for Mapillary layers) per
   resolved shard. The same shards passed the gates at ingest, but the
   scene is the final boundary before sim execution.
5. Per layer:
   - `terrain`: SRTM/3DEP raster → triangulated mesh via
     `e7m_dataset.geo.dem_to_mesh()` → `UsdGeom.Mesh` with displacement
     map.
   - `raster_overlay`: Sentinel-2 bands → reprojected geotiff →
     `UsdShade.Material` with texture sampler bound to terrain mesh
     UVs.
   - `vector_buildings`: GeoJSON polygons → extrude by
     `extrude_attr` (or `default_height_m`) → `UsdGeom.Mesh` instances
     under a `UsdGeom.Scope` named `/Buildings`.
   - `vector_roads`: LineString → ribbon mesh (Overture lane-width
     attr or default 3.5m per lane) → `UsdGeom.Mesh` instances.
   - `object_3d_instances`: glTF/USD from Objaverse-XL → preprocess to
     tinyusdz-readable USD → `UsdGeom.PointInstancer` with
     `placement_strategy`-derived transforms.
6. Emit `.usd` via `kami-usd` (tinyusdz bindings).
7. DataLad save → annex copy → `e7m-dataset publish-ipfs` → datasetPin
   emit. The scene is itself a pinned IPFS artifact.
8. `e7m-sim` loads via `kami-rt` and uses `kami-genesis` for any
   physics interaction (vehicle dynamics, contact). PhysX nv-compat
   facade is API-only; backing impl is Genesis.

Determinism (G6): given a fixed set of input CIDs and a fixed
recipe, the output USD MUST be byte-identical (modulo a documented
ordering tolerance for `UsdGeom.PointInstancer` transforms with a
declared seed). Verified by `tests/test_assemble_deterministic.py`
in W1.

## §5. PII filter extension (Mapillary vision PII)

ADR-2605262400 §6 covers structured PII (email / phone / address /
WHOIS). This ADR extends the PII filter scope to **vision PII**
specifically for the Mapillary fetcher:

- **Face blur**: per-frame face detection (OSS, e.g. CenterFace ONNX
  or `yolov8-face` Apache-2.0); detected boxes filled with Gaussian
  blur σ ≥ 15 px or solid fill.
- **License plate blur**: per-frame plate detection + blur σ ≥ 20 px.
- **Child detection / scene rejection**: heuristic age estimate < 18
  triggers full-frame rejection (drop the frame entirely, do not
  attempt to blur — fail-closed for child-presence).
- **Verification at fetch time**: the `mapillary.py` fetcher runs the
  blur model and writes both original and redacted frames into the
  subdataset, but **only the redacted view is exposed to sensors /
  scene assembly**. Original frames stay in annex behind a Council-
  attestation-gated unlock. (Pattern parallel to ADR-2605262400 §6
  "redacted in place; original preserved in annex".)
- **Blur model itself**: runs on Murakumo fleet only
  (ADR-2605215000); no commercial GPU rental for the preprocessing
  pass.

If the blur model output is missing for any frame, the fetcher
**fails closed** — the entire chunk is rejected and no datasetPin
record is emitted.

## §6. Wave delivery plan

| Wave | Scope | Estimate |
|---|---|---|
| **W0 (this ADR)** | proposed-status ADR + deps.toml [[adrs]] entry + 90-docs/adr/README.md index row + CLAUDE.md Status row | half-day |
| **W1 (Tier-A foundations)** | `sentinel2.py` (ports ADR-2605215100 M1 T0) + `srtm.py` + `overture.py` fetchers; SceneRecipe schema + assemble-usd-scene.py PoC binding 3 layers (terrain + raster_overlay + vector_roads); first wadachi Shibuya scene as Tier A only (no Tier-C props yet); determinism test | 3-5 days |
| **W2 (Tier-A extensions + eval)** | `usgs_3dep.py` + `ms_buildings.py` + `openusd_samples.py` fetchers; full layer set (terrain + raster_overlay + vector_buildings + vector_roads); reference scene generated on isolated trial machine per e7m-sim G5; PSNR/SSIM/Chamfer/IoU eval vs Isaac Sim ref; iterate until ≥ 0.75 | 5-7 days |
| **W3 (Tier-C NC carve-out)** | `mapillary.py` fetcher + face/plate/child blur preprocessing; `hf_3d_nc.py` for Objaverse-XL NC subset; G13 enforcement verify (R9-equivalent leak test on PostSink for sim recordings); `-nc-` artifact naming gate | 5-7 days |
| **W4 (cross-actor extension)** | suki (farm), igata-outdoor (foundry yard), sarutahiko (highway), futawa (motorcycle), tatekata (construction site), hodoki (ELV yard), makura (factory floor — indoor), tsutae (urban street level — overlap with wadachi) sim layer integration; per-actor sub-recipes | per-actor individual |

Watatsumi (submersible) needs **bathymetry sources** (GEBCO / Copernicus
Marine / NOAA bathymetry) which are **out of scope for this ADR** and
deferred to a separate sub-ADR (`adr-watatsumi-bathymetry-ingestion`,
proposed-pending).

## §7. Gates (12)

- **G1**: Every subdataset ingested under this ADR runs Charter Rider §2
  scan at `e7m-dataset add` time. Same gate pattern as ADR-2605262400
  §9 G1.
- **G2**: PII filter runs **before** Charter Rider §2 scan. For
  Mapillary, the filter includes face/plate/child blur per §5. Fail-
  closed if blur model output is missing or below threshold.
- **G3**: Every subdataset honors `replicationMin: 2`
  (ADR-2605241500 §D6 + ADR-2605262400 §9 G3).
- **G4**: Tier C source materials produce Tier C derived sim outputs.
  Sim recordings (rosbag / video / trained-policy weights) downstream
  of a Tier-C-tagged scene MUST carry `-nc-` infix in artifact name
  and `internal_only=True` flag on PostSink Observations.
- **G5**: NC-derived sim outputs MUST NOT publish to public endpoints.
  Routed through judah LiteLLM + SBT-gate only. Same gate pattern as
  ADR-2605262100 G13 + ADR-2605262400 §9 G6.
- **G6**: `assemble-usd-scene.py` MUST be deterministic given fixed
  input CIDs + fixed recipe (modulo declared PointInstancer seed).
  Verified by unit test in W1.
- **G7**: All physics simulation MUST go through `kami-genesis`
  (Apache-2.0 Genesis solver). The `nv_compat.physx` facade is
  API-compatibility ONLY; backing impl is `kami-genesis`. Direct use
  of NVIDIA PhysX (any version) is **N1..N9 NEVER** per
  ADR-2605261800 §2(b). Enforced by lint hook on import statements
  (`70-tools/scripts/lint/no-nvidia-physx-import.mjs`, W1).
- **G8**: All rendering MUST go through `kami-pbrt` (Mitsuba 3
  upstream-PR-only 90-day window) or its Embree CPU fallback. NVIDIA
  OptiX / RTX Renderer / Replicator are **N1..N9 NEVER**.
- **G9**: Sim run inference (perception models inside the sim'd
  vehicle, decision models in the autonomy stack under test) flows
  through Murakumo fleet (ADR-2605215000). Train rental for sim-
  derived policies is gated on ADR-2605262200 ratification.
- **G10**: `scenes/<name>/scene.yaml` files (with `world:` section per
  §3) live under `70-tools/e7m-sim/scenes/` and are committed to git.
  The YAML IS the audit trail for which CIDs went into which scene.
- **G11**: Quantitative quality target ≥ 0.75 vs Isaac Sim reference
  scene (PSNR/SSIM/Chamfer/IoU min) per e7m-sim ADR-2605261600 G5.
  Reference scene generation runs once on a one-time-use isolated
  trial machine; only the metrics CSV is imported back. Threshold
  breach blocks production sim use of that scene until W2 iteration
  brings it above 0.75.
- **G12**: Murakumo capacity caps per e7m-sim ADR-2605261600 G12 (R1
  ≤1 / R2 ≤4 / R3 ≤16 GPU-hr-eq/actor/day). The blur preprocessing
  pass (§5) counts against this budget.

## §8. Non-goals (10)

- **N1**: NOT Google Earth Studio / Google Maps SDK / Google Maps API.
  Out of scope (commercial + §2(c) surveillance ecosystem proximity).
- **N2**: NOT Cesium ion premium / commercial tier. (The Apache-2.0
  CesiumJS client itself is not ingested by this ADR; tile hosting is
  IPFS via `e7m-dataset`.)
- **N3**: NOT NVIDIA Omniverse Nucleus / Omniverse Cloud / SimReady
  asset library / Replicator / DriveSim. **N1..N9 NEVER per
  ADR-2605261800 §2(b)**.
- **N4**: NOT NVIDIA PhysX (any version). All physics via
  `kami-genesis`. (PhysX nv-compat facade is API-only per
  ADR-2605261800 §D11.)
- **N5**: NOT commercial high-res satellite (Maxar / Planet Labs paid
  tier / Vexcel UltraCam). Sentinel-2 free tier + SRTM/3DEP public-
  domain DEM are sufficient for Wave 1-2; commercial sources are
  charter §2 + paywall-warn issues.
- **N6**: NOT real-time satellite feed. Batch ingestion only,
  consistent with ADR-2605215100 M1 T0 cadence.
- **N7**: NOT a planetary-scale tileset hosting service. We pin only
  the regions covered by active scene recipes. Global pins are
  acceptable only for SRTM 30m and IANA-style small metadata.
- **N8**: NOT a live street-view imagery capture pipeline. We are
  passive consumers of Mapillary's public dump only; no contribution
  back, no organism-driven capture.
- **N9**: NOT a replacement for `maps_sentinel_murakumo M1`
  (ADR-2605215100). That pipeline remains the authoritative raster
  fusion path; this ADR is the bridge to USD + e7m-sim consumption.
- **N10**: NOT a commercial GPU rental enabler for sim runs or for
  any sim-derived artifact. Inference path is Murakumo-only
  (ADR-2605215000). Train rental for sim-trained policies is the
  subject of ADR-2605262200 (Council ratify pending).

## §9. First testbed: wadachi R1 Tokyo Shibuya 1km×1km outdoor scene

Recipe target: `wadachi-r1-tokyo23ku-shibuya-1km-261015`.

Layer composition:

- **Terrain**: SRTM 1-arc (30m) for `n35e139` tile. Sufficient
  resolution for vehicle-scale dynamics at 1km×1km. Shibuya is flat,
  3DEP-equivalent is unavailable for Japan but unnecessary for this
  scene.
- **Raster overlay**: Sentinel-2 L2A B432 RGB for tile `T54SUE` at the
  most recent cloud-free date. Texture purpose only; no semantic
  layer used in W1.
- **Vector buildings**: Overture 2604 release Japan extract, filtered
  to bbox. Building height attribute from Overture; default 8.0m for
  missing.
- **Vector roads**: Overture 2604 release Japan transportation extract,
  filtered to bbox. Road centerlines extruded into ribbon mesh; lane
  count + lane width from Overture attributes.
- **Tier-C props (W3+)**: Objaverse-XL passenger-car-set-vol2 NC
  subset, 50 instances placed along road centerlines with lane-
  jitter. Sim recordings derived from this scene at W3+ MUST carry
  `-nc-` infix.

Physics: `kami-genesis` rigid-body for vehicle dynamics + contact;
ground plane derived from terrain mesh.

Renderer: `kami-pbrt` with Embree CPU fallback for W1 (Vulkan RT GPU
path lands at e7m-sim R2 per ADR-2605261600 §R2).

Quality gate (G11): reference scene generated once on an isolated
trial machine running Isaac Sim with equivalent layer composition;
PSNR/SSIM/Chamfer/IoU minimum ≥ 0.75 across 32 evaluation viewpoints
sampled along a 200m road segment. Metrics CSV committed to
`90-docs/baien/sim-substrate-scoring-260526.md` (the e7m-sim scoring
doc per ADR-2605261600).

W1 ship target: 1 publishable scene (Tier A only), determinism test
green, no PSNR/SSIM eval yet (eval runs in W2).

# Consequences

**Positive**:

- Single SoT for how every R1+ outdoor sim consumer loads world
  geospatial data. Removes the per-actor reinvention risk that
  ADR-2605261600 §G3 anticipates ("Vulkan RT GPU-neutral + Embree
  fallback") — every actor will use the same fetcher + recipe + USD
  pipeline.
- Inherits the entire Tier A/B/C + G13 + Charter Rider scan framework
  from ADR-2605262400. No new policy invented; only the consumer
  changes.
- Proves the Omniverse-free outdoor sim stack end-to-end:
  Sentinel-2/SRTM/Overture → tinyusdz (kami-usd) → kami-rt + kami-
  genesis. Validates the ADR-2605261800 §D10 contingent-fallback
  bet that KAMI-native impls can match the proprietary stack at the
  primitives that matter for outdoor robotics sim.
- Reuses `e7m-dataset` (no new ingestion tool), `datasetPin` Lexicon
  (no new contract), and ADR-2605262400 §6 PII filter (extended for
  vision PII).
- Forward-compatible with iwakura ASIC silicon Wave 1 — the
  `kami-pbrt` Vulkan RT path lands at e7m-sim R2 and absorbs iwakura
  natively per ADR-2605261800 §D11.

**Negative / cost**:

- Disk + IPFS pin footprint grows. Per-region Sentinel-2 L2A tile is
  ~ 2 GB; SRTM 30m global one-time pin is ~ 100 GB; Overture 2604
  release Japan extract is ~ 15 GB; Objaverse-XL NC subset (cars +
  pedestrians + signs only) is ~ 50 GB. Wave 3 Mapillary city extracts
  are ~ 200 GB per major city. Pin retention policy lives in W3 ADR
  amendment.
- Mapillary face/plate/child blur preprocessing pass is non-trivial
  compute. Wave 3 estimate: ~ 0.5 GPU-hr per 100k frames on Murakumo
  EVO-X2. Counts against G12 capacity caps.
- PSNR/SSIM ≥ 0.75 gate vs Isaac Sim ref is hard; first Shibuya scene
  may score lower and require Council eval. ADR-2605261600 §G5
  anticipates this with "engineering-investment-bounded" framing —
  the W2 iteration loop is the absorbing mechanism.
- The `kami-genesis` solver is Apache-2.0 but younger than PhysX; some
  edge cases (high-friction tire models, complex articulated chains)
  may require contribution upstream to Genesis. Acceptable per
  ADR-2605261800 §D10 contingent-fallback policy.
- 90-day Mitsuba 3 upstream-PR-only hold (ADR-2605261800 §D11) means
  `kami-pbrt` rendering quality has a known ceiling until that hold
  resolves. Embree CPU fallback is the W1-W2 safe path.

**Forward-compatibility**:

- SceneRecipe TOML schema is extensible — future Tier-A sources
  (e.g. open IXP imagery, open building-interior 3D, open road-sign
  databases) plug in without ADR amendment.
- A potential future "active street-view capture" ADR (Council Lv6+)
  would introduce an `ActiveCaptureSource` orthogonal to this one;
  nothing in this design forecloses that path, but nothing in this
  design enables it either. Symmetric to ADR-2605262400 §7 passive-
  only discipline.

# Alternatives Considered

1. **Use Cesium 3D Tiles + Cesium ion**. Rejected — Cesium ion is
   commercial; OSS Cesium tileset generators exist but the toolchain
   maturity is below tinyusdz for our W1-W2 needs. CesiumJS client
   library itself is Apache-2.0 and may be vendored later if a web-
   based sim viewer is needed (out of scope).

2. **Use Google Earth Studio / Google Maps Platform SDK**. Rejected —
   commercial license + Charter Rider §2(c) surveillance ecosystem
   proximity + ADR-2605261800 §2(b) NVIDIA-adjacent SimReady tooling
   exclusion.

3. **Build a proprietary sim asset library from scratch**. Rejected —
   redundant with Pixar OpenUSD Apache-2.0 samples + Objaverse-XL
   permissive subset + Sentinel/SRTM/Overture coverage. Mission
   §1.6 (反個人主義, multi-generational priority) favors building
   on shared OSS rather than inventing parallel.

4. **Tier-A only (skip Mapillary + Objaverse-XL NC)**. Considered.
   Rejected by user 内部利用前提 decision. Mapillary visual realism +
   Objaverse-XL prop library are too valuable for wadachi R3 sim-to-
   real transfer to skip, given the G13 backstop is well-proven
   (ADR-2605262100 R1.4 + ADR-2605262400 Wave 3 both rely on it).

5. **Merge into ADR-2605262400 as a single mega-ADR**. Rejected —
   organism perception axis (netreg / DNS / BGP / web-graph) and
   robotics sim axis (geospatial raster + 3D vector + USD pipeline)
   have:
   - Different consumers (`kotodama.organism` vs `e7m-sim`).
   - Different invariants (passive-only network discipline vs
     Omniverse N1..N9 NEVER + PhysX N1..N9 NEVER + Genesis-only
     physics).
   - Different gates (R7/R8/R9 Kaizen rules vs G7/G8 nv-compat
     enforcement + G11 PSNR/SSIM target).
   - Different cold-path consumers (baien-moemoekyun training corpus
     vs `e7m-sim` USD stage).
   Merging would produce a doc that violates the "one decision per
   ADR" principle and is hard to navigate.

6. **Use NVIDIA PhysX via the nv-compat facade backing impl (i.e.
   leak PhysX in as the secret backend)**. Rejected — explicitly
   forbidden by ADR-2605261800 §2(b) N1..N9 NEVER. The nv-compat
   facade is API-compat only; backing impl must be `kami-genesis`.
   Anything else is a charter violation.

7. **Build a fully custom USD writer instead of using tinyusdz**.
   Rejected — `kami-usd` (tinyusdz-based) is already the canonical
   per ADR-2605261800. Reinventing the USD writer duplicates work
   and breaks the kami-engine R1.0 architecture.

# References

- ADR-2605170900 — etzhayyim/root canonical home for ADRs
- ADR-2605192100 — Mission Charter (Wellbecoming, 反個人主義)
- ADR-2605192200 — IP-Free-Release with Charter Compliance Rider v2.0
- ADR-2605215000 — Inference Murakumo-only (no commercial GPU rental)
- ADR-2605215100 — maps_sentinel_murakumo M1 T0 (Sentinel-2 prototype this ADR ports)
- ADR-2605241500 — Dataset CID substrate (DataLad + annex + IPFS)
- ADR-2605242000 — wadachi R0 (autonomous mobility, first consumer)
- ADR-2605261600 — e7m-sim R0 (robotics simulation substrate charter)
- ADR-2605261800 — kami-engine nv-compat (kami-usd + kami-genesis + kami-pbrt)
- ADR-2605262100 — baien-moemoekyun R1 Phase 0 (G13 NC carve-out precedent)
- ADR-2605262130 — Kotoba storage substrate unification
- ADR-2605262200 — CHARTER-RIDER §2(i) train-rental amendment (proposed-gated)
- ADR-2605262300 — baien-moemoekyun R2+ rental train architecture (gated)
- ADR-2605262400 — Public-data organism IPFS ingestion (sibling on network axis; shared framework)
- CHARTER-RIDER.md §2 — 8 prohibited categories + three-tier enforcement
- `70-tools/e7m-dataset/README.md` — fetcher + publish-ipfs + datasetPin contract
- `70-tools/e7m-sim/` — robotics simulation substrate (paths-reserved per ADR-2605261600 R0)
- `40-engine/kami-engine/kami-usd/` — tinyusdz-based USD emitter (per ADR-2605261800 R1.0)
- `40-engine/kami-engine/kami-genesis/` — Genesis 5-solver physics (per ADR-2605261800 R1.0)
- `40-engine/kami-engine/kami-pbrt/` — Mitsuba 3 / Embree renderer (per ADR-2605261800 R1.0)
