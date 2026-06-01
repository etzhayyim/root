"""baien-moemoekyun-train — 2B BitNet 1.58 backbone + MoE residual experts.

Authoritative references:
  - ADR-2605261900 (R0 charter, architecture)
  - ADR-2605262100 (R1 sub-charter, Phase 0 freeze-train on EVO-X2 ROCm)
  - ADR-2605262300 (R2+ sub-charter, RunPod B200 — gated on ADR-2605262200 amendment)
"""

__version__ = "0.1.0-r1.0"

from .moe import BaienMoEResidual
from .attach import BitNetFFNWithMoE, attach_moe_to_model, freeze_backbone_verify

__all__ = [
    "BaienMoEResidual",
    "BitNetFFNWithMoE",
    "attach_moe_to_model",
    "freeze_backbone_verify",
]
