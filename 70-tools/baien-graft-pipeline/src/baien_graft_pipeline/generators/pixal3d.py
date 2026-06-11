"""Pixal3D adapter — TencentARC pixel-aligned image→3D cascade.

Upstream: https://huggingface.co/spaces/TencentARC/Pixal3D
Underlying checkpoints (auto-pulled by the pipeline on first call):

  - `TencentARC/Pixal3D-T`                          (main cascade)
  - `camenduru/dinov3-vitl16-pretrain-lvd1689m`     (image-conditioning backbone)
  - `Ruicheng/moge-2-vitl`                          (wild-image camera estimator)

Compared to Hunyuan3D-2, Pixal3D-T outputs strictly more per sample:

  per-image artifacts
    1× glb mesh (with PBR textures)
    1× shape SLAT (sparse latent .npz)
    1× tex   SLAT (sparse latent .npz)
    8× normal renders
    8× clay renders
    8× base_color renders
    8× shaded_forest renders
    8× shaded_sunset renders
    8× shaded_courtyard renders

A baien-MX training sample (image, mesh, 4-view, multi-view caption)
slices 4 of the 8 frames for the 4-view product, drops the SLAT (we
re-derive at training time), and feeds the 6 render-mode variants
through Florence-2 as multi-view caption inputs.

Runtime model:
  - Default ComfyUI mode is NOT supported (no kijai wrapper as of
    2026-05-23). We invoke the Gradio Space API directly via HTTP.
  - Hosting options:
      a) public Space at huggingface.co/spaces/TencentARC/Pixal3D
         (ZeroGPU; rate-limited; OK for ≤10-image smoke runs)
      b) clone the Space and serve locally on EVO-X2 ROCm; pin the
         endpoint URL via env `BGP_PIXAL3D_URL`.

`pixal3d_request_body(image_path, ...)` returns the JSON envelope
expected by the Gradio `/api/generate_3d` endpoint.
"""

from __future__ import annotations

from typing import Any

# Cascade defaults — match the upstream Space's `512_cascade` preset.
DEFAULT_HR_RESOLUTION = 512
DEFAULT_LR_RESOLUTION = 512
DEFAULT_MAX_NUM_TOKENS = 49152
DEFAULT_NUM_FRAMES = 8


def pixal3d_request_body(
    image_path: str,
    *,
    seed: int = 42,
    hr_resolution: int = DEFAULT_HR_RESOLUTION,
    max_num_tokens: int = DEFAULT_MAX_NUM_TOKENS,
    num_frames: int = DEFAULT_NUM_FRAMES,
) -> dict[str, Any]:
    """Build the Gradio API request envelope for Pixal3D's `generate_3d`.

    The Gradio Space schema (as of 2026-05-23, SDK 6.14) accepts:

      {
        "data": [
          { "path": "/local/path/to/image.png", "url": null, "size": null },
          <seed:int>, <resolution:int>, ... sampling params ...
        ]
      }

    For brevity we use the same defaults as the Space's preset, exposing
    only `seed` + `hr_resolution` knobs to callers.
    """
    return {
        "fn_index": 0,  # generate_3d entry; verify against the Space's UI graph
        "data": [
            {"path": image_path, "url": None, "size": None},
            int(seed),
            int(hr_resolution),
            # sparse-structure sampler override (use Space defaults — None)
            None,
            # shape-slat sampler override
            None,
            # tex-slat sampler override
            None,
            # cascade pipeline_type
            f"{hr_resolution}_cascade",
            int(max_num_tokens),
            int(num_frames),
        ],
        "_pipeline": {
            "pipeline_type": f"{hr_resolution}_cascade",
            "max_num_tokens": max_num_tokens,
            "num_frames": num_frames,
        },
        "_provenance": {
            "model_id": "TencentARC/Pixal3D-T",
            "backbone": "camenduru/dinov3-vitl16-pretrain-lvd1689m",
            "depth_camera": "Ruicheng/moge-2-vitl",
            "license": "see https://huggingface.co/TencentARC/Pixal3D-T",
            "adapter_version": 1,
        },
    }
