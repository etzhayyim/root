# baien-mx Move 1 data-gen runbook

Stages the baien-graft pipeline so it produces enough `(image, caption)`
rows to feed `e7m bench mx-train --phase A/B/C` per ADR-2605232500.

**This runbook is GPU-bound (ROCm gfx1151 on EVO-X2).** It must be
sequenced **after** any in-flight `e7m bench core4` run or it will
serialize on the iGPU.

## 0. Pre-flight

- EVO-X2 reachable: `ssh evo "tasklist | findstr python"` shows no
  lm-eval / mx-train python running.
- ComfyUI running on `http://192.168.1.22:8188` (per ADR-2605202345).
- Optional Pixal3D Gradio Space at `http://192.168.1.22:7860` if you
  want the 12× row multiplier (per `70-tools/baien-graft-pipeline/`
  Pixal3D backend).

## 1. Stage input images on EVO-X2

ComfyUI reads images from `<comfy>\input\`. We need a small starter
set of **public-domain / CC0** images (Charter Rider §2 clean). 10
diverse-object images is the Phase A target.

Recommended starter set (Pexels / CC0):

```
chair.jpg     horse.jpg     apple.jpg     bicycle.jpg     teapot.jpg
flamingo.jpg  hamburger.jpg pencil.jpg    cactus.jpg      cube.jpg
```

(Replace with any single-object photos you own + can publish.)

Stage them:

```bash
# 1. drop the 10 images into the local repo
mkdir -p ~/baien-graft-inputs
# put your 10 chosen images there

# 2. scp to EVO-X2 ComfyUI input dir
scp ~/baien-graft-inputs/*.{jpg,png} evo:"C:/Users/gad/ComfyUI/ComfyUI_windows_portable/ComfyUI/input/"
```

## 2. Kick off data-gen (Hunyuan3D-2 default backend)

```bash
cd 70-tools/baien-graft-pipeline
. .venv/bin/activate

bgp-submit \
  --comfy-url http://192.168.1.22:8188 \
  --images chair.jpg,horse.jpg,apple.jpg,bicycle.jpg,teapot.jpg,flamingo.jpg,hamburger.jpg,pencil.jpg,cactus.jpg,cube.jpg \
  --out-log ~/baien-graft/batch-001/jobs.json \
  --max-wait-sec 7200
```

Estimated wall on EVO-X2 ROCm: **~11 min** for 10 images (66 s/sample
× 10 sequential).

## 3. (Optional) Pixal3D backend for 12× row multiplier

Per ADR-2605202115 amendment 2026-05-23. Each Pixal3D sample yields
8 frames × 6 render modes = 48 view variants vs Hunyuan3D's 1:

```bash
bgp-submit \
  --generator pixal3d \
  --pixal3d-url http://192.168.1.22:7860 \
  --images chair.jpg,horse.jpg \
  --out-log ~/baien-graft/batch-001-pixal/jobs.json
```

Wall is ~120 s / sample (Pixal3D cascade@512) but the row yield more
than compensates.

## 4. Post-process to baien-graft `sample.json` format

For Hunyuan3D-2 output:

```bash
bgp-collect \
  --jobs-log ~/baien-graft/batch-001/jobs.json \
  --out-dir ~/baien-graft/batch-001/
```

For Pixal3D output: the Gradio Space already returns paths; the
collector reads the JSON envelope from `pixal3d.py`'s `_provenance`
field and synthesizes a sample.json per generated mesh.

## 5. Phase-target sample counts

| Phase | Required samples (Hunyuan3D, 4 views/sample) | Required samples (Pixal3D, 48 views/sample) | Wall (Hunyuan3D) |
|---|---|---|---|
| A smoke (100 rows) | **25 images** | 3 images | ~28 min |
| B bootstrap (1000 rows) | **250 images** | 21 images | ~4.6 h |
| C scale (10000 rows) | **2500 images** | 209 images | ~46 h |

## 6. Hand off to mx-train

```bash
# verify the directory tree (each <slug>/ has sample.json + view_*.png)
ls -la ~/baien-graft/batch-001/

# launch Phase A:
e7m bench mx-train \
  --phase A \
  --graft-data-dir ~/baien-graft/batch-001 \
  --dry-run                     # 1st: validate wiring (~80s)

e7m bench mx-train \
  --phase A \
  --graft-data-dir ~/baien-graft/batch-001
                                 # 2nd: real Phase A training (~80s on ROCm)
```

## 7. Eval after Phase A

```bash
# the trainer auto-calls eval if state.decision goes to commit/abort;
# manual re-eval:
python -m baien_mx_train.eval \
  --graft-data-dir ~/baien-graft/batch-001 \
  --projector-path baien-mx-out/mx-move1-iter-00/projector
```

## 8. Commit (if eval gate passes)

If `visual_microbench ≥ 60%` AND `text_microbench Δ ≥ -3 pp`:

```bash
# the commit_node appends to 90-docs/baien/multimodal-models.jsonl
# then codegen the TS module:
node 70-tools/scripts/llm-registry/gen-multimodal-entries.mjs

# review the diff; flip `available: true` per entry as appropriate;
# git commit + PR
```

## Risks / caveats

- **Conflict with Core 3'**: do not run this runbook while
  `e7m bench core4` is in flight — both compete for the iGPU.
- **License chain**: each input image must be CC0 / public domain or
  owned. Charter Rider §2 review applies if any image carries
  attribution requirements.
- **Pixal3D Gradio Space**: HF-hosted Space is ZeroGPU + rate-limited;
  for production volume, clone the Space locally on EVO-X2.
- **Disk**: ~30 MB / sample for Hunyuan3D (GLB + 4 renders). Pixal3D
  is ~500 MB / sample (48 renders + SLAT). Phase C (2500 Hunyuan
  samples) = ~75 GB; plan disk accordingly.
