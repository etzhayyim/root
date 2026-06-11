# baien-graft-pipeline

Reference implementation of the **baien graft 3D-augmented dataset** pipeline
defined in [ADR-2605202115](../../90-docs/adr/2605202115-baien-graft-3d-augmented-dataset.md).

Generates schema-conformant samples of the form
`(image_2d, mesh, 4-view renders, multi-view caption)` for use as **3D-aware
text supervision** in baien Move 1 (image graft, frozen SigLIP + 1.58-bit
projector + frozen BitNet trunk).

Role separation:

| Stage                                 | Where                          | Tool                                     |
| ------------------------------------- | ------------------------------ | ---------------------------------------- |
| Image → mesh (generator)              | EVO-X2 (ADR-2605202345)        | `--generator hunyuan3d` (ComfyUI + kijai) **or** `--generator pixal3d` (TencentARC Pixal3D-T cascade @512) |
| Mesh → 4-view PNG render              | Mac (Apple Silicon, CGL/Metal) | moderngl standalone (skip for Pixal3D — it already emits 8 frames × 6 modes) |
| Image + renders → caption             | Mac (MPS)                      | Florence-2-large-ft                      |
| sample.json assembly                  | Mac                            | this package                             |

### Generator backends

`bgp-submit --generator <name>` selects the image→3D backend:

| name | underlying checkpoints | wall / sample (EVO-X2 ROCm) | extra outputs vs Hunyuan3D |
|---|---|---|---|
| `hunyuan3d` (default) | `hunyuan3d-dit-v2-0-fp16.safetensors` + `hunyuan3d-vae-v2-0-fp16.safetensors` | ~66 s | — |
| `pixal3d` | `TencentARC/Pixal3D-T` + `camenduru/dinov3-vitl16-pretrain-lvd1689m` + `Ruicheng/moge-2-vitl` | ~120 s (cascade@512, max_num_tokens=49,152, 8 frames) | shape SLAT (.npz) + tex SLAT (.npz) + 8 frames × 6 render modes (normal / clay / base_color / shaded_forest / shaded_sunset / shaded_courtyard) |

Endpoint config (env var or CLI flag):

```
BGP_GENERATOR=pixal3d                         # default backend
BGP_COMFY_URL=http://192.168.1.22:8188        # for hunyuan3d
BGP_PIXAL3D_URL=http://192.168.1.22:7860      # for pixal3d (locally-served Gradio Space)
```

Upstream Pixal3D Space: https://huggingface.co/spaces/TencentARC/Pixal3D
(Apache-2.0 wrapper; **per-checkpoint license** at the `TencentARC/Pixal3D-T`
model card — verify before any first-party redistribution per Charter Rider §2).

## Install

```bash
cd 70-tools/baien-graft-pipeline
uv venv --python 3.12 .venv
. .venv/bin/activate
pip install -e .
```

Notes:
- Florence-2 requires `transformers==4.45.2` (newer breaks `forced_bos_token_id`).
- Open3D / pyrender / pyglet do not work as the renderer on this stack —
  see ADR-2605202115 "Alternatives Considered" for dead-end log.

## Prerequisites on the EVO-X2 ComfyUI host

1. ComfyUI 0.21.1 portable + PyTorch ROCm 7.2.1
2. `custom_nodes/ComfyUI-Hunyuan3DWrapper` (kijai) installed
3. `models/diffusion_models/hunyuan3d-dit-v2-0-fp16.safetensors` (4.93 GB)
4. `models/vae/hunyuan3d-vae-v2-0-fp16.safetensors` (428 MB)
5. ComfyUI listening on `0.0.0.0:8188`
6. SSH access from Mac to EVO-X2 (alias `evo` in `~/.ssh/config`)

## Run

### 1. Place input images on the host

Copy the images you want to process into the ComfyUI `input/` directory on
EVO-X2. Image filenames here will match those passed to `--images`.

### 2. Submit batch generation

```bash
bgp-submit \
  --images chair.png,horse.png,flamingo.png,hamburger.png,teapot.png \
  --out-log ~/baien-graft/batch-001/jobs.json
```

This submits N prompts to the ComfyUI `/prompt` endpoint and polls `/history`
until all complete. ~66 s/sample sequential on EVO-X2.

### 3. Collect + render + caption + assemble

```bash
bgp-collect \
  --jobs-log ~/baien-graft/batch-001/jobs.json \
  --out-root ~/baien-graft/batch-001
```

For each successful job, this:

1. `scp`-pulls the GLB from EVO-X2 and the original image from the input/.
2. Renders 4 views (front / right / back / left) at 512×512 via moderngl.
3. Captions input image + 4 views + 2×2 tile via Florence-2.
4. Computes acceptance gate (4/4 noun-match + mesh sanity).
5. Writes `sample.json` per sample plus a top-level `batch_summary.json`.

## Schema

See ADR-2605202115 §D1 for the canonical schema. Each sample directory contains:

```
<slug>/
├── source/<image>            # original 2D input
├── mesh/hunyuan3d.glb        # Hunyuan3D-2 generated mesh
├── renders/                  # 4 views + 2×2 tile
│   ├── hunyuan3d_front.png
│   ├── hunyuan3d_right.png
│   ├── hunyuan3d_back.png
│   ├── hunyuan3d_left.png
│   └── hunyuan3d_4view_tile.png
└── sample.json               # schema-conformant top-level record
```

The supervision pair for baien Move 1 is
`sample.json#/baien_supervision_pair_v0/y_caption_3d_augmented` — a single
text blob (≈ 700 chars) concatenating the 2D caption with 4-view captions.
Only this text string (and the 2D image path) needs to flow into
`vertex_training_dataset_snapshot`; mesh + renders stay off-snapshot.

## Empirical results (Phase 3b, 2026-05-20)

| metric                                | value  |
| ------------------------------------- | ------ |
| input images                          | 10     |
| accepted (4/4 gate + sanity)          | 10     |
| ComfyUI gen total (sequential)        | 665 s  |
| Mac render + caption + assemble total | 149 s  |
| end-to-end per sample                 | ~ 81 s |

Acceptance was genuine, not lenient — Florence-2 sometimes generalised the
species (flamingo → "bird / crane / ostrich") but the gate captured the
preserved 3D essence (long neck, two figures, etc.) via Jaccard ≥ 0.10
between source and view noun stems.

## Substrate compliance

All tools and weights are OSS:

- ComfyUI (GPL-3.0)
- ComfyUI-Hunyuan3DWrapper (kijai) — MIT
- Hunyuan3D-2 (Tencent License, OSS, non-commercial)
- TripoSR weights — MIT
- moderngl — MIT
- Florence-2 — MIT
- trimesh — MIT

No SaaS API endpoints are called during sample generation. Charter Rider v2.0
§2(a)–(h) are not triggered. See [CHARTER-RIDER.md](../../CHARTER-RIDER.md).

## License

Apache 2.0 WITH **etzhayyim Charter Compliance Rider v2.0**. See repo root
`LICENSE`, `NOTICE`, `CHARTER-RIDER.md`. ADR-2605192200.
