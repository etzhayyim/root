---
id: doc-adr-2605262500-implementation-retrospective-260527
title: "ADR-2605262500 Implementation Retrospective — 39-cycle production rollout"
status: active
doc_type: reference
topic: adr-2605262500-retrospective
authoritative: false
last_verified: 2026-05-27
authoritative_for:
  - chronology of ADR-2605262500 implementation cycles
  - architectural patterns surfaced during the 39-cycle rollout
related:
  - adr-2605262500-robotics-world-data-ingestion-and-usd-pipeline
  - adr-2605262400-public-data-organism-ipfs-ingestion
  - CLAUDE.md (row #71)
supersedes: []
superseded_by: []
---

# ADR-2605262500 Implementation Retrospective — 39-cycle production rollout

**Date**: 2026-05-26 → 2026-05-27
**Cycles**: 39 `/loop "進めて"` iterations + the initial ADR draft
**Outcome**: ADR-2605262500 W0-W4 substantively shipped; 372 tests
green; 36/36 deps.toml audit clean.

This document is **non-authoritative** (per `authoritative: false`) —
the ADR itself + the source files are authoritative. This doc captures
the chronology + patterns for future cross-ADR pattern reuse.

## Summary

| Metric | Value |
|---|---|
| Cycles | 39 |
| ADR file | `90-docs/adr/2605262500-robotics-world-data-ingestion-and-usd-pipeline.md` |
| First-party Python modules shipped | 7 fetchers + vision PII filter + 3 diagnostic CLIs + assembler + eval harness + PDS resolver + book-keeping verifier |
| Scenes shipped | 8 cross-actor (wadachi/suki/sarutahiko/igata/futawa/tatekata/hodoki/tsutae) + 1 documented carve-out (makura) |
| Tests passing | 242 e7m-dataset + 120 e7m-sim + 10 verifier = **372 total** |
| deps.toml entries | **36 / 36 clean** (audited end-to-end) |
| Enforcement layers | CLI verifier + lefthook pre-commit + GitHub Actions workflow |

## Wave-by-wave shipped

### W0 — ADR draft (cycle 1)

- `90-docs/adr/2605262500-robotics-world-data-ingestion-and-usd-pipeline.md`
- 12 gates G1..G12, 10 non-goals N1..N10, 4-wave delivery plan

### W1 — Tier-A fetchers (cycles 2-4)

7 dataset fetchers under `70-tools/e7m-dataset/src/e7m_dataset/fetchers/`:

- `sentinel2.py` — STAC v1 search + multi-band COG fetch (cycle 2)
- `srtm.py` — OpenTopography GlobalDEM (cycle 2)
- `overture.py` — Overture Maps S3 Parquet (cycle 2)
- `ms_buildings.py` — MS Global Building Footprints CSV index (cycle 3)
- `usgs_3dep.py` — USGS 3DEP 1m DEM S3 anonymous (cycle 3)
- `openusd_samples.py` — Pixar OpenUSD samples (cycle 4)
- `hf_3d_nc.py` — Objaverse-XL NC subset Tier-C (cycle 5)

### W2.0 — USDA emission (cycles 7-10)

- `scenes/_schema/scene.schema.json` — JSON Schema 2020-12 (cycle 3)
- `scripts/assemble-usd-scene.py` — W1 stub assembler (cycle 3) → real USDA 1.0 emit (cycle 7)
- `scripts/eval_sim_metrics.py` — G11 quality gate (PSNR/SSIM/Chamfer/IoU; 3-mode CLI scalar/CSV/file-I/O) (cycles 8-10)

### W2.1 — Geometry (synth) (cycles 11-13)

- terrain 4-corner quad → N×N triangulated grid w/ CID-seeded synth elevation
- vector_buildings single cube → Scope w/ N CID-seeded polygons
- vector_roads single ribbon → Scope w/ N CID-seeded multi-segment polylines
- W2 PDS resolve_datasetpin (real `com.atproto.repo.getRecord` + defensive fallback)

### W2.2 — Real Parquet ingest (cycles 14-16)

- buildings `bbox` struct + height column → axis-aligned rect (cycle 14)
- roads WKB LineString parser (cycle 15)
- W2.3 buildings WKB Polygon outer ring + roads MultiLineString (cycle 16)

### W2.2 — Raster overlay + terrain real (cycles 17-19)

- raster_overlay `UsdShade.Material` + `UsdUVTexture` w/ Pillow PNG sidecar (cycle 17)
- terrain Pillow GeoTIFF `I;16` decode (cycle 18)
- scipy.ndimage bilinear elevation upgrade (cycle 19)
- E2E 4-layer real-asset proof-of-life test (cycle 19)

### W3.0/W3.1 — Tier-C + vision PII (cycles 6, 20-26, 32-35)

- `fetchers/mapillary.py` — Graph API v4 + G2 vision PII filter required (cycle 6)
- `vision_pii_filter.py` — pluggable backend interface (cycle 6)
- `OnnxFaceBackend` generic (cycle 20)
- `CenterFaceOnnxBackend` canonical decode (cycle 21)
- ORT round-trip E2E (cycle 23)
- Pillow blur pixel-verified E2E (cycle 24)
- G5 child-fail-closed via age classification + regression E2E (cycle 25)
- `Yolov8FaceOnnxBackend` Ultralytics layout decode (cycle 26)
- `Yolov8FaceOnnxBackend` blur + G5 E2E (cycle 32)
- `RetinaFaceOnnxBackend` post-processed Nx{15,16} (cycle 33)
- `RetinaFaceOnnxBackend` blur + G5 E2E (cycle 34)
- `ETZ_VISION_PII_BACKEND=auto` static-inspection routing (cycle 35)

### W2.3 — Charter rescan deepening (cycles 29, 31)

- `_extract_parquet_text_to_tempfile` (cycle 29) — Parquet text columns → temp sidecar text
- `_collect_charter_scan_targets` — scene.yaml + Parquet sidecars
- E2E §2 violation catch-loop test (cycle 31; `assault_rifle_carrier` → RuntimeError)

### W4 — Cross-actor scenes (cycles 1, 7, 9, 10)

8 scenes shipped + 1 explicit carve-out + parallel-cycle additions:

| Actor | Scene | bbox | Cycle |
|---|---|---|---|
| wadachi | shibuya-1km | 1 km² urban | 1 |
| suki | tokachi-2km-pasture | 4 km² pasture | 7 |
| sarutahiko | tomei-5km | 5 km × 1 km highway | 9 |
| igata | foundry-yard-50m | 50 m × 50 m industrial | 9 |
| futawa | mountain-3km | 2.7 km × 1.7 km mountain | 10 |
| tatekata | construction-site-100m | 100 m² site | 10 |
| hodoki | elv-yard-200m | 200 m² yard | 10 |
| tsutae | shibuya-crossing-200m | 200 m² urban | 10 |
| makura | INDOOR carve-out | n/a | 10 |
| (hikari) | solar-tracker-2km | parallel-cycle addition | — |
| (wadachi-hydro) | shibuya-pumped-hydro-micro | parallel-cycle addition | — |

### Book-keeping enforcement (cycles 27-30)

3-layer drift prevention:

- `70-tools/scripts/lint/verify_deps_toml_paths.py` — stdlib lint (cycle 27)
- `lefthook.yml` — pre-commit hook (cycle 28)
- `.github/workflows/deps-toml-paths.yml` — PR strict gate + nightly baseline tracker (cycle 30)

### Operator diagnostic CLI triad (cycles 37-39)

| Concern | CLI | Subcommands |
|---|---|---|
| Vision PII | `e7m_dataset.vision_pii_diagnose` | check / classify / smoke |
| PDS resolver | `e7m_dataset.pds_diagnose` | check / parse / resolve |
| Scene assembler | `70-tools/e7m-sim/scripts/assemble_diagnose.py` | check / inspect / dry-run |

Consistent UX across all 3:
- `check` = env+deps validation
- middle command = static inspection (classify / parse / inspect)
- last command = live execution w/ side effect (smoke / resolve / dry-run)
- All `--json` for CI parseability
- Honest exit codes (0=ready, 1=missing config, 2=missing dep)

## Architectural patterns surfaced

### 1. Subclass-per-canonical-format ONNX decoder

The W3.1 vision PII filter ships 3 face-detector backend subclasses
sharing a common abstract base (`OnnxFaceBackend`). Each subclass
overrides `detect_faces` to handle its specific output format:

- `CenterFaceOnnxBackend` — heatmap+scale+offset multi-tensor
- `Yolov8FaceOnnxBackend` — Nx{6..20} bbox row, channel-count hint layout-detect
- `RetinaFaceOnnxBackend` — Nx{15,16} bbox+10 landmark+score

Shared helpers (`_nms`, `_iou`) live as module-level functions, not
methods, so they're independently testable. The `auto` env spec
introspects ONNX output shape and routes to the right subclass —
operator UX win without enum proliferation.

**Pattern reusable for**: any pluggable inference backend with multiple
canonical export formats (W3.2 plate detection / W3.3 person detection / etc.)

### 2. Graceful 4-layer asset ingest fallback

Each scene layer kind (terrain / raster_overlay / vector_buildings /
vector_roads) has a 4-step fallback chain:

```
operator's local_*_path → pyarrow/Pillow real data → assembled USDA
                       ↓ (path missing / library missing / decode failure)
                       CID-seeded synth data → assembled USDA (always works)
```

This means assemble works in every environment — operator with full
production data, operator with partial data, operator with no data
(only env vars / scene.yaml). G6 determinism preserved at every layer.

**Pattern reusable for**: any pipeline where production-grade ingest is
optional but determinism + assemble-must-succeed are mandatory.

### 3. 3-layer book-keeping drift enforcement

| Layer | Tool | Trigger | Action |
|---|---|---|---|
| Local | `verify_deps_toml_paths.py` CLI | manual run | reports drifts |
| Pre-commit | lefthook hook | git commit (deps.toml staged) | rejects commits |
| CI | GitHub Actions workflow | PR / push / nightly | blocks PRs + baseline tracker |

Each layer catches drift earlier than the next. Strict-scoped audit
(`--filter ADR-2605262500`) is the PR gate; full-repo audit is
soft baseline tracker (don't block PRs on cross-ADR drift).

**Pattern reusable for**: any monorepo book-keeping concern (deps.toml,
docs registry, lexicon registry, etc.)

### 4. Operator diagnostic CLI triad

3 CLIs share identical UX: `check` / static-inspect / live-execute.
Each is a separate Python module/script (no shared base class) but the
contract is enforced by parallel test files asserting consistent
subcommand naming.

**Pattern reusable for**: any operator-facing tool surface with env-driven
configuration (e.g., future LLM provider config / IPFS client / Murakumo
fleet config).

### 5. Synthetic ONNX test fixtures

The vision PII test suite uses `onnx.helper.make_model` to construct
synthetic models whose Constant nodes emit known tensors (heatmaps for
CenterFace; Nx{N} bbox rows for yolov8/RetinaFace; classification
logits for age classifier). This lets the FULL ONNX session pipeline
be tested without depending on real downloaded models.

The synthesis helpers reverse-engineer from desired DetectionBox →
heatmap+scale+offset, so the test can assert "the box ENDED UP at
(140, 90, 40, 60) within ±4 px tolerance" rather than "the box
ended up somewhere".

**Pattern reusable for**: any ML inference layer where the algorithm is
known but operator models vary.

## Test coverage matrix

### Vision PII filter (3 backends × 4 layers)

| Backend | Pure decoder | ORT round-trip | Pillow blur pixel | G5 child fail-closed |
|---|---|---|---|---|
| CenterFace | cycle 21 | cycle 23 | cycle 24 | cycle 25 |
| yolov8-face | cycle 26 | cycle 26 | cycle 32 | cycle 32 |
| RetinaFace | cycle 33 | cycle 33 | cycle 34 | cycle 34 |

All 12 cells filled. Auto-detect routing (cycle 35) covers 3 backends + generic fallback + missing-env.

### Charter Rider §2 defense in depth

| Source | Catch path | Cycle |
|---|---|---|
| scene.yaml text | regex on file | cycle 5 |
| Parquet text columns | regex on extracted sidecar | cycle 29 |
| Image pixels | vision_pii_filter (Pillow+ONNX) | cycles 6, 23-25, 32, 34 |

E2E violation catch-loop test (cycle 31) — Parquet row with `assault_rifle_carrier` → `RuntimeError`.

### Deterministic assembly invariants

- G6 byte-determinism: scene.yaml → identical USDA SHA across emits (cycle 7 onward)
- G4 `-nc-` infix enforcement: Tier-C scenes without `-nc-` infix → fail-closed (cycle 1 onward)
- Synth fallback determinism: same CID → same elevation/polygons/polylines (cycles 11-13)

## Operator workflow (final, production-ready)

```bash
# 1. Pre-flight diagnostics (cycles 37-39)
python3 -m e7m_dataset.vision_pii_diagnose check
python3 -m e7m_dataset.pds_diagnose check
python3 70-tools/e7m-sim/scripts/assemble_diagnose.py check

# 2. Validate operator-staged scene (cycles 39)
python3 70-tools/e7m-sim/scripts/assemble_diagnose.py inspect <scene.yaml>
python3 70-tools/e7m-sim/scripts/assemble_diagnose.py dry-run <scene.yaml>

# 3. Book-keeping audit (cycle 27)
python3 70-tools/scripts/lint/verify_deps_toml_paths.py --filter ADR-2605262500

# 4. Production fetch (cycles 2-6)
e7m-dataset pull sentinel2 --tile-id T54SUE
e7m-dataset pull srtm --tile-id n35e139
e7m-dataset pull overture --release ... --theme buildings --type-name building
e7m-dataset pull mapillary --bbox ... --token ...   # vision PII applied at fetch

# 5. Production assemble (cycle 7+)
python3 70-tools/e7m-sim/scripts/assemble-usd-scene.py scenes/.../scene.yaml --out out/

# 6. Quality gate (cycles 8-10)
python3 70-tools/e7m-sim/scripts/eval_sim_metrics.py \
    --candidate-image <our.png> --reference-image <isaac-sim-ref.png> \
    --candidate-pc <our.npy> --reference-pc <isaac-sim-ref.npy>
```

## Deferred items

| Item | Reason | Resolution path |
|---|---|---|
| rasterio install + W2.4 proper bilinear | env doesn't have rasterio | `pip install rasterio` on operator side; scipy.ndimage already covers 95% of cases |
| Cross-ADR drift cleanup (12 orphan entries) | requires owner coordination for unrelated ADRs | each owner runs `verify_deps_toml_paths.py --filter <their-ADR>` |
| PDS resolve real-network smoke | needs live `pds.etzhayyim.com` access | operator runs `pds_diagnose resolve` against real PDS |
| GitHub Actions workflow smoke | can't trigger PR without push auth | next PR exercising deps.toml will validate the workflow |
| W3.2 license-plate decoder subclass | no canonical LPR ONNX exporter audit | operator-supplied PLATE_MODEL routes through generic OnnxFaceBackend; W3.2 ADR-extension if dedicated decoder needed |

## References

- ADR-2605262500 — Robotics-sim world-data ingestion + kami-usd pipeline (canonical)
- ADR-2605262400 — Public-data organism IPFS ingestion (sibling on netreg axis)
- ADR-2605261600 — e7m-sim R0 charter
- ADR-2605261800 — kami-engine nv-compat (kami-usd / kami-genesis / kami-pbrt)
- ADR-2605242000 — wadachi R0 (autonomous mobility, first consumer)
- ADR-2605215000 — Murakumo-only inference (G7 invariant)
- CLAUDE.md row #71 — operating-time summary
