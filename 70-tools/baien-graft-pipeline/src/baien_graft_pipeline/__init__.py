"""baien graft 3D-augmented dataset pipeline (ADR-2605202115).

Two CLIs:
- `bgp-submit`  — submit N images to ComfyUI Hunyuan3D-2 workflow, poll until done
- `bgp-collect` — pull GLBs, render 4-view via moderngl, caption via Florence-2,
                  assemble schema-conformant sample.json per input
"""

__version__ = "0.1.0"
