---
id: doc-adr-2605262500-operator-runbook-260527
title: "ADR-2605262500 Operator Runbook — fetch → assemble → eval"
status: active
doc_type: how-to
topic: adr-2605262500-operator-runbook
authoritative: false
last_verified: 2026-05-27
authoritative_for:
  - operator-facing entry point for ADR-2605262500 production rollout
related:
  - adr-2605262500-robotics-world-data-ingestion-and-usd-pipeline
  - doc-adr-2605262500-implementation-retrospective-260527
  - CLAUDE.md (row #71)
supersedes: []
superseded_by: []
---

# ADR-2605262500 Operator Runbook — fetch → assemble → eval

**Audience**: operators running ADR-2605262500 production workloads.
**Tool versions** verified at: 2026-05-27 (cycle 42).

This runbook is the **operational** companion to the 39-cycle
implementation retrospective (`adr-2605262500-implementation-retrospective-260527.md`).
The retrospective explains _what was built_; this runbook explains
_what to type_.

## Quick start (1 command)

```bash
python3 70-tools/scripts/diagnose/e7m_preflight.py --filter ADR-2605262500
```

- Exit 0 → env ready, proceed to "Daily workflow" below.
- Exit 1 → at least one check failed; read the printed operator action
  items, run the per-tool `check` to diagnose, fix, retry.

## Prerequisites

```bash
pip install onnxruntime numpy pillow pyarrow scipy pyyaml httpx onnx
```

Optional but recommended:

```bash
pip install jsonschema       # enables scene.schema.json G10 gate
pip install rasterio         # enables W2.4 proper geospatial bilinear (deferred)
```

## One-time operator setup

### 1. Download face-detector ONNX model (choose ONE)

```bash
mkdir -p /var/etzhayyim/models

# Option A — CenterFace (Star-Clouds, MIT)
curl -L https://github.com/Star-Clouds/CenterFace/raw/master/models/onnx/centerface.onnx \
    -o /var/etzhayyim/models/face.onnx

# Option B — yolov8-face (Ultralytics, AGPL-3 or Apache-2.0 re-impl)
# Use the post-processed export (not raw 8400-anchor output)

# Option C — RetinaFace (insightface, post-processed Nx15 export)
```

### 2. (Optional) Age classifier ONNX for G5 child-fail-closed

```bash
curl -L https://.../age-classifier.onnx \
    -o /var/etzhayyim/models/age.onnx
```

Without age classifier, `child_face_count` is always 0 ("indeterminate")
and frames are NOT auto-rejected. Caller applies jurisdiction policy
separately.

### 3. Mapillary token (free tier)

```bash
# Sign up at https://www.mapillary.com/dashboard/developers
export MAPILLARY_TOKEN=<your-token>
```

### 4. Configure env

```bash
# Vision PII filter backend (auto-detect if you don't know your model's type)
export ETZ_VISION_PII_BACKEND=auto
export ETZ_VISION_PII_FACE_MODEL=/var/etzhayyim/models/face.onnx
export ETZ_VISION_PII_AGE_MODEL=/var/etzhayyim/models/age.onnx   # optional

# PDS (defaults to https://pds.etzhayyim.com; only override for staging)
# export ETZ_E7M_PDS_URL=https://pds.staging.etzhayyim.com
```

### 5. Pre-flight validation

```bash
python3 70-tools/scripts/diagnose/e7m_preflight.py
```

Must show `PREFLIGHT: PASS  (4/4 checks)` before proceeding.

## Daily workflow

### Step A — Fetch data

```bash
# Sentinel-2 imagery (Tier A, free)
e7m-dataset pull sentinel2 --tile-id T54SUE \
    --datetime-range "2024-04-01/2024-09-30" \
    --cloud-cover-max 15.0

# SRTM elevation (Tier A, public domain)
e7m-dataset pull srtm --tile-id n35e139

# Overture vector (Tier A, CDLA-Permissive)
e7m-dataset pull overture --release 2024-12-12.0 \
    --theme buildings --type-name building
e7m-dataset pull overture --release 2024-12-12.0 \
    --theme transportation --type-name segment

# Mapillary street imagery (Tier C, vision PII filter applied at fetch)
e7m-dataset pull mapillary \
    --bbox 139.69 35.65 139.71 35.67 \
    --token "$MAPILLARY_TOKEN"
```

Each fetch stages bytes under `${ETZ_DATASET_ROOT}/datasets-staging/`
+ writes a manifest row. Operator then commits via `datalad save` +
`e7m-dataset publish-ipfs`.

### Step B — Inspect + dry-run scene

```bash
# Validate operator's local scene.yaml without writing output:
python3 70-tools/e7m-sim/scripts/assemble_diagnose.py inspect \
    70-tools/e7m-sim/scenes/wadachi-r1-shibuya-1km/scene.yaml

python3 70-tools/e7m-sim/scripts/assemble_diagnose.py dry-run \
    70-tools/e7m-sim/scenes/wadachi-r1-shibuya-1km/scene.yaml
# → reports usda_sha256 + layer/prop counts
# → writes NO files
```

### Step C — Production assemble

```bash
python3 70-tools/e7m-sim/scripts/assemble-usd-scene.py \
    70-tools/e7m-sim/scenes/wadachi-r1-shibuya-1km/scene.yaml \
    --out /var/etzhayyim/scenes-out/wadachi-shibuya/
# → writes scene.usda + manifest.json + textures/Layer1_raster_overlay.png
```

The output dir is self-contained — `tar czf scene.tar.gz <out>` ships
the full scene to any fleet node.

### Step D — Quality gate (G11)

```bash
# Scalar mode (operator already has Isaac Sim metrics)
python3 70-tools/e7m-sim/scripts/eval_sim_metrics.py \
    --psnr-db 28.5 --ssim 0.91 --chamfer-m 0.032 --iou 0.81
# → exit 0 = PASS, 1 = FAIL with per-metric notes

# File I/O mode (compare candidate artifacts to Isaac Sim references)
python3 70-tools/e7m-sim/scripts/eval_sim_metrics.py \
    --candidate-image candidate.png --reference-image isaac-sim-ref.png \
    --candidate-pc candidate.npy   --reference-pc isaac-sim-ref.npy
```

The Isaac Sim references must be produced ONCE on a one-time-use
isolated trial machine never connected to religious-corp infra
(ADR-2605261600 G5 constitutional invariant). Only the metrics CSV
or the reference frame/pc files cross the boundary back.

## Troubleshooting

### "vision_pii_diagnose check" reports ✘ for ETZ_VISION_PII_FACE_MODEL

Set the env var to a downloaded ONNX model path. Run `classify`:

```bash
python3 -m e7m_dataset.vision_pii_diagnose classify \
    /var/etzhayyim/models/face.onnx
# → reports kind (centerface / yolov8-face / retinaface / generic)
# → if kind is unexpected, you've got a non-standard model export
```

### "PREFLIGHT: FAIL" but each per-tool check passes when run standalone

Likely a `PYTHONPATH` issue. Run from repo root with explicit path:

```bash
export PYTHONPATH=70-tools/e7m-dataset/src
python3 70-tools/scripts/diagnose/e7m_preflight.py
```

### `assemble_diagnose` reports `Charter scan: stub-no-e7m-dataset`

Defensive fallback — assemble runs fine, but the Charter Rider §2
scan is using the stub path because `e7m_dataset.charter` isn't on
the Python import path. For the full real-scanner integration, set
`PYTHONPATH=70-tools/e7m-dataset/src` before running diagnostics:

```bash
PYTHONPATH=70-tools/e7m-dataset/src \
    python3 70-tools/e7m-sim/scripts/assemble_diagnose.py inspect <scene.yaml>
# Charter scan: passed-recipe-scan  (scope: scene-recipe-yaml+parquet-text)
```

Production `assemble-usd-scene.py` does NOT depend on this — it uses
the same defensive fallback automatically.

### Mapillary fetch produces 0 redacted frames

```bash
# Smoke-test the backend end-to-end
python3 -m e7m_dataset.vision_pii_diagnose smoke \
    /var/etzhayyim/models/face.onnx
# → if "detections=0", the face model is rejecting your synthetic image
#   (this is normal for the synthetic test; on real Mapillary frames
#    you should see detections)
```

### "Charter Rider §2 scan FAILED" during assemble

Your scene.yaml or referenced Parquet contains a `§2(a)..(h)` violation
keyword. Per `vision_pii_filter` is a runtime catch — fix the source
data before reattempting.

Check the source:

```bash
python3 70-tools/e7m-sim/scripts/assemble_diagnose.py inspect <scene.yaml>
# Look at the "Charter scan" line at the bottom
```

### "Drift detected" from deps.toml verifier

Either restore the missing file or remove the orphan entry. Run:

```bash
python3 70-tools/scripts/lint/verify_deps_toml_paths.py
# Full repo audit; identifies which entries are orphaned
```

## Reference

### Backend selection summary

| Operator's model export | `ETZ_VISION_PII_BACKEND` |
|---|---|
| CenterFace ONNX (heatmap+scale+offset) | `centerface-onnx` |
| yolov8-face ONNX (Nx{5,6,7,15,16}) | `yolov8-face-onnx` |
| RetinaFace post-processed (Nx{15,16}) | `retinaface-onnx` |
| Don't know / mixed | `auto` |
| Tests / dry-run only | `stub-allow` + `ETZ_VISION_PII_ALLOW_STUB=1` |

### Tier-A vs Tier-C licensing

| Tier | Sources | Publishability |
|---|---|---|
| A | Sentinel-2 / SRTM / 3DEP / OSM / Overture / MS-Buildings / OpenUSD | publishable (with attribution) |
| C | Mapillary CC-BY-SA / Objaverse-XL NC | G13 fleet-internal carve-out (`-nc-` infix + judah LiteLLM + SBT-gate) |

Tier-C derived sim recordings MUST NOT publish externally.

### Constitutional invariants (cannot be amended without Council Lv6+ ≥3)

- **G2** Vision PII filter is MANDATORY for Mapillary fetch
- **G4** Tier-C scenes require `-nc-` infix
- **G5** Child face detected → full frame rejected (no partial blur)
- **G7** NVIDIA PhysX NEVER; `kami-genesis` only
- **G8** OptiX/RTX Renderer/Replicator NEVER; `kami-pbrt` + Embree only
- **G9** Murakumo-only inference; no commercial GPU rental
- **G11** PSNR/SSIM/Chamfer/IoU composite ≥ 0.75 for production scenes
- **G12** R1 ≤ 1 GPU-hr-eq/actor/day Murakumo cap

### Diagnostic CLI quick reference

| Concern | Command |
|---|---|
| Unified preflight | `python3 70-tools/scripts/diagnose/e7m_preflight.py` |
| Vision PII filter | `python3 -m e7m_dataset.vision_pii_diagnose check\|classify\|smoke` |
| PDS resolver | `python3 -m e7m_dataset.pds_diagnose check\|parse\|resolve` |
| Assembler | `python3 70-tools/e7m-sim/scripts/assemble_diagnose.py check\|inspect\|dry-run` |
| Book-keeping | `python3 70-tools/scripts/lint/verify_deps_toml_paths.py` |

### Related docs

- **ADR**: `90-docs/adr/2605262500-robotics-world-data-ingestion-and-usd-pipeline.md`
- **Retrospective**: `90-docs/baien/adr-2605262500-implementation-retrospective-260527.md`
- **CLAUDE.md**: row #71 — operating-time summary
- **Sibling ADR**: `90-docs/adr/2605262400-public-data-organism-ipfs-ingestion.md`
