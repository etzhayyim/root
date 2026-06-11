"""Image→3D generator registry for baien-graft (ADR-2605202115).

Two backends today:

  - hunyuan3d  ComfyUI Hunyuan3D-2 (single mesh, ~66s/sample on EVO-X2 ROCm).
                Existing default; well-tested.

  - pixal3d    TencentARC Pixal3D-T cascade @512 (DINOv3 + MoGe-2,
                8 frames × 6 render modes, GLB with PBR textures).
                Higher fidelity, more outputs per sample, larger budget.

Both adapters return a normalized record that downstream (caption,
gate, sample.json assembly) can consume identically.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class GeneratorSpec:
    name: str
    description: str
    workflow_fn: Callable[..., dict[str, Any]] | None   # ComfyUI workflow factory (if applicable)
    api_endpoint: str | None                            # HTTP endpoint base if not ComfyUI
    license: str
    typical_runtime_sec: int                            # per-sample wall on EVO-X2 ROCm
    outputs: list[str]                                  # output product names


from .hunyuan3d import hunyuan3d_workflow  # noqa: E402
from .pixal3d import pixal3d_request_body  # noqa: E402


GENERATOR_REGISTRY: dict[str, GeneratorSpec] = {
    "hunyuan3d": GeneratorSpec(
        name="hunyuan3d",
        description="ComfyUI Hunyuan3D-2 (kijai wrapper); legacy default",
        workflow_fn=hunyuan3d_workflow,
        api_endpoint=None,
        license="tencent-hunyuan-community",
        typical_runtime_sec=66,
        outputs=["glb"],
    ),
    "pixal3d": GeneratorSpec(
        name="pixal3d",
        description="TencentARC Pixal3D-T cascade @512 (DINOv3 + MoGe-2); pixel-aligned high-fidelity",
        workflow_fn=None,
        api_endpoint="http://192.168.1.22:7860",  # default Gradio Space hosted on EVO-X2 (if mirrored locally)
        license="see https://huggingface.co/TencentARC/Pixal3D-T",
        typical_runtime_sec=120,                  # @spaces.GPU(duration=120) in upstream Space
        outputs=["glb", "shape_slat_npz", "tex_slat_npz",
                 "render_normal_x8", "render_clay_x8", "render_base_color_x8",
                 "render_shaded_forest_x8", "render_shaded_sunset_x8",
                 "render_shaded_courtyard_x8"],
    ),
}
