# 3DGS runbook — sparse preview → dense photoreal → Shibuya → physics

Status of the three asks (1 dense 3DGS · 2 Shibuya · 3 physics-integration).
The render path is fully wired (`kami-pipelines::GsplatAdapter` +
`shibuyaLoadSplat` / `shibuyaLoadSplatPly`); what remains is **GPU training**
(no CUDA on this host) and a **Mapillary client token** (only a website login
was stored).

## Now, no GPU — sparse SfM preview + physics (DONE)

Input: a Mapillary Street-Level-Sequences OpenSfM dataset (images +
`reconstruction.json` = poses + colored sparse points), 40 cities incl.
Tsuru 都留 (JP), Boston, Washington.

```sh
# colored sparse SfM points → .splat (real street imagery, no training)
python3 70-tools/scripts/sim/opensfm_to_splat.py \
  "<dataset>/Tsuru/reconstruction.json" \
  60-apps/.../svelte/static/shibuya/sfm_Tsuru.splat 60
```
- View: `splat.htm` (city selector).
- **#3 integration**: `splat.htm?physics=1` — `run_splat_physics_v1` renders the
  SfM cloud as backdrop with kami-genesis floating-base agents doing full
  physics on a ground plane inside it.
- The `sfm_*.splat` clouds are Mapillary CC-BY-SA → gitignored (local only).

## #1 — Dense photoreal 3DGS (GPU, offline)

The downloaded dataset is exactly the gsplat init (images + SfM poses + sparse
points). On a CUDA GPU pod (the repo's `trainGsplatFromMapillary` worker, Vultr/
RunPod per ADR-2605092800 — NOT this Mac):

```sh
# nerfstudio path (one city), or the repo worker gsplat_train_dumper.py
ns-process-data images --data <dataset>/Tsuru/images --output-dir /tmp/tsuru_ns
# (or import the OpenSfM poses directly to skip COLMAP)
ns-train splatfacto --data /tmp/tsuru_ns --max-num-iterations 15000
ns-export gaussian-splat --load-config <run>/config.yml --output-dir /tmp/tsuru_ply
```
Then drop the PLY beside the bundle and render it:
```sh
cp /tmp/tsuru_ply/splat.ply 60-apps/.../svelte/static/shibuya/shibuya.ply
# splat.htm / shibuya.htm 'G' → shibuyaLoadSplatPly renders the dense splat
```
Blocked here: no NVIDIA GPU on this host (Charter Rider §2(i) routes religious-
corp GPU through the Murakumo/Vultr pods, not local).

## #2a — Shibuya SPARSE preview, no GPU (DONE — real reconstruction)

With a Mapillary client token (stored in Keychain `MAPILLARY_TOKEN`) we fetched
real Shibuya imagery and ran CPU SfM — no GPU:

```sh
export MAPILLARY_TOKEN="$(security find-generic-password -s MAPILLARY_TOKEN -a etzhayyim -w)"
python3 70-tools/scripts/sim/mapillary_fetch.py --bbox 139.6985,35.6585,139.7025,35.6605 \
  --out .../shibuya_mapillary.manifest.json --limit 200
# download the thumbnails (manifest thumb_url) → /tmp/shibuya_imgs, then:
python3 -m venv /tmp/sfmvenv && /tmp/sfmvenv/bin/pip install pycolmap
/tmp/sfmvenv/bin/python 70-tools/scripts/sim/images_to_sfm_splat.py \
  /tmp/shibuya_imgs .../static/shibuya/sfm_Shibuya.splat 60
```
Result (verified): 80 images → COLMAP SfM → **19 registered images, 2,235
points** → `sfm_Shibuya.splat` → `splat.htm` (渋谷 default). Sparse + partial
(mixed-angle street photos); a single Mapillary sequence reconstructs denser.

## #2b — Shibuya DENSE photoreal (token + GPU)

The dataset has **no Shibuya** (Tsuru is the only JP city). For Shibuya:

```sh
# 1. generate a Mapillary CLIENT token (MLY|…) in the Mapillary dashboard
#    (the stored 1Password "Mapillary" item is a website login, not a token).
export MAPILLARY_TOKEN='MLY|…'
python3 70-tools/scripts/sim/mapillary_fetch.py \
  --bbox 139.6985,35.6585,139.7025,35.6605 \
  --out 70-tools/e7m-sim/scenes/shibuya/shibuya_mapillary.manifest.json --limit 150
# 2. enqueue the GPU training (existing pipeline):
#    com.etzhayyim.apps.maps.trainGsplatFromMapillary
#      { "lat":35.6595, "lng":139.7005, "radiusM":120, "mapillaryImageIds":[…] }
# 3. → shibuya.ply → shibuya.htm 'G'
```
Blocked here: (a) no client token, (b) GPU training is offline.

## Render hooks (wired, ready)

| hook | use |
|---|---|
| `shibuyaLoadSplat(bytes)` | load `.splat` (sparse preview) |
| `shibuyaLoadSplatPly(bytes)` | load `.ply` (dense trained 3DGS) |
| `shibuyaClearSplat()` | hide overlay |
| `run_splat_viewer_v1` | pure splat viewer (`splat.htm`) |
| `run_splat_physics_v1` | splat + physics agents (`splat.htm?physics=1`) |
