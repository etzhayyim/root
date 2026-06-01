---
id: adr-2605312600-shibuya-3dgs-mapillary-sfm-and-splat-physics-integration
title: "ADR-2605312600: Shibuya 3DGS — real Mapillary imagery → CPU SfM → splat viewer + physics integration"
status: accepted
doc_type: adr
topic: shibuya-3dgs-sfm-splat-physics
authoritative: true
last_verified: 2026-05-31
priority: 5.5
axis: architecture
weight: 0.5
priority_note: "Realizes the 3DGS path for the Shibuya digital twin end-to-end with a real Mapillary client token, GPU-free: fetch real Shibuya street imagery → CPU COLMAP SfM (pycolmap) → colored sparse 3-D points → gravity-aligned .splat → kami GsplatAdapter, plus a splat viewer and a splat+physics integration (#D) where kami-genesis agents do full physics on the reconstructed street. Dense photoreal 3DGS remains a GPU gsplat-training step. Secrets (token) kept in Keychain only; Mapillary-derived data (images/manifest/sfm splat) gitignored (CC-BY-SA)."
authoritative_for:
  - Mapillary client-token acquisition + image fetch (mapillary_fetch.py) for Shibuya
  - CPU SfM → .splat tool (images_to_sfm_splat.py) incl. camera-plane gravity alignment
  - kami-app-shibuya splat viewer (run_splat_viewer_v1) + splat-physics (run_splat_physics_v1)
  - 3DGS data-handling policy (token→Keychain, derived data gitignored CC-BY-SA)
depends_on:
  - adr-2605312200-shibuya-digital-twin-kotoba-asset-linkage-and-mapillary-3dgs
  - adr-2605311900-shibuya-street-digital-twin-osm-citymesh-fullphysics-sim
  - adr-2605092800-gsplat-preview-qc
related:
  - adr-2605311800-kami-genesis-3d-spatial-articulation-and-contact-solver
supersedes: []
superseded_by: []
---

# ADR-2605312600: Shibuya 3DGS — Mapillary imagery → CPU SfM → splat viewer + physics

> **ID note**: drafted as 2605312400, re-issued as 2605312600 after that id was
> concurrently committed by the 申文 (moushibumi) actor ADR in a parallel
> session; content unchanged.

**Status**: accepted
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

ADR-2605312200 wired the `GsplatAdapter` render path + the Mapillary acquisition
front but was blocked: the stored "Mapillary" 1Password item was a website
login, not an API client token. The founder then supplied a real Mapillary
**client token** (`MLY|…`) and a downloaded Mapillary Street-Level-Sequences
OpenSfM dataset (40 cities; no Shibuya — Tsuru is the only JP city), and asked
to (1) make a dense 3DGS, (2) do Shibuya, (3) integrate the splat with the
physics sim.

# Decision

Realize the 3DGS path end-to-end, **GPU-free for the sparse preview**, and
integrate it with the physics sim. The dense photoreal optimization stays an
offline GPU step (no NVIDIA GPU on this host; Charter Rider §2(i) routes
religious-corp GPU through Vultr/RunPod pods).

## 1. Real Shibuya imagery (token → fetch)

Token validated against the Graph API (HTTP 200) and stored in the macOS
**Keychain** (`service=MAPILLARY_TOKEN`) — never committed.
`mapillary_fetch.py` pulled 200 real Shibuya-Scramble images (ids + poses +
thumb URLs).

## 2. CPU SfM → .splat (no GPU)

`70-tools/scripts/sim/images_to_sfm_splat.py` runs COLMAP via **pycolmap**
(extract → exhaustive match → incremental mapping) on a folder of street photos,
takes the largest reconstruction, and writes its colored sparse points as an
antimatter15 `.splat`. It **gravity-aligns**: the plane through the camera
centres gives "up"; rotate its normal → +Y, drop the ground to y≈0, scale
horizontally — so the cloud loads gravity-correct.
`opensfm_to_splat.py` does the same for the dataset's pre-computed OpenSfM
reconstructions (Tsuru / Boston / Washington). Verified: 80 Shibuya images →
19 registered → **2,235 points** → `sfm_Shibuya.splat`.

## 3. Viewer + physics integration (#D)

`kami-app-shibuya` exposes `run_splat_viewer_v1` (sky + GsplatAdapter, orbit) and
`run_splat_physics_v1` (+ ground plane + kami-genesis floating-base agents doing
full physics on the gravity-aligned street). `splat.htm` selects the scene
(渋谷 default) and `?physics=1` enables agents. Render hooks `shibuyaLoadSplat`
/ `shibuyaLoadSplatPly` accept the trained dense PLY drop-in.

# Consequences

**Positive**

- A real Shibuya 3-D reconstruction (from real street photos) renders now, with
  no GPU, and agents do physics on it — the full digital-twin loop is visible.
- Reproducible tools (`mapillary_fetch` / `images_to_sfm_splat` / `opensfm_to_splat`)
  + GSPLAT-RUNBOOK.md cover sparse-now and dense-via-GPU.

**Negative / honest limitations**

- The Shibuya cloud is **sparse and partial** (19/80 images registered — mixed-
  angle street photos). A single Mapillary sequence reconstructs denser.
- **Dense photoreal 3DGS is not done** — gsplat optimization is an offline GPU
  job; only the SfM sparse preview runs here. Procedural splatting was rejected.
- Physics agents share the cloud's frame but collide only with a flat ground
  plane (not the splat geometry); splat-as-collision is future work.

# Verification (directly observed)

- Graph API token validate → HTTP 200; `mapillary_fetch.py` → 200 Shibuya images.
- 80 images downloaded → `images_to_sfm_splat.py` (pycolmap) → 19 registered,
  2,235 points → gravity-aligned `sfm_Shibuya.splat` (ground y≈0).
- `splat.htm` (渋谷) and `splat.htm?physics=1` render in-browser (WebGPU).

# Alternatives Considered

1. **Dense gsplat training in-session.** Rejected — no local NVIDIA GPU; it is
   the documented Vultr/RunPod step (`trainGsplatFromMapillary`).
2. **Procedural splatting for instant density.** Rejected by the founder — no
   real detail; SfM/gsplat from real imagery is the route.
3. **Committing the Mapillary-derived clouds.** Rejected — CC-BY-SA + token-
   adjacent; kept local + gitignored, only tools/runbook committed.

# References

- ADR-2605312200 (kotoba asset linkage + GsplatAdapter wire + Mapillary front)
- ADR-2605092800 (gsplat preview/QC + trainGsplatFromMapillary)
- `70-tools/scripts/sim/{mapillary_fetch,images_to_sfm_splat,opensfm_to_splat}.py`
- `70-tools/e7m-sim/scenes/shibuya/GSPLAT-RUNBOOK.md`
- `40-engine/kami-engine/kami-app-shibuya/src/lib.rs` (run_splat_viewer_v1 / run_splat_physics_v1)
