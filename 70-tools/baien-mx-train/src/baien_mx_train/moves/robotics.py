"""Move 6 — robotics graft (ADR-2605242120).

Edge tier: scene description only. NO action head. NO actuator output.
Server tier: OpenVLA-style action head (stub; ships post-Council).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RoboticsTier = Literal["edge", "server"]


@dataclass(frozen=True)
class RoboticsSceneRow:
    """Edge-tier training row: scene description only (Move 1 image encoder)."""

    image: bytes  # SigLIP-compatible (224x224 RGB)
    scene_desc: str  # human-readable target (training label)
    env_meta: dict  # {"surface": ..., "objects": [...], "lighting": ...} — training-time only


@dataclass(frozen=True)
class RoboticsActionRow:
    """Server-tier training row: full action chunk (stub — ships post-Council)."""

    observation: dict  # multi-modal observation bundle
    action_chunk: list[list[float]]  # K timesteps x 7 DoF
    success_label: float  # 0.0..1.0


def assert_edge_no_actuation(tier: RoboticsTier) -> None:
    """Raise if caller attempts to load an action head on edge tier.

    Charter Rider §2(h) Wellbecoming: actuation from an under-specified edge LLM
    is a physical-world safety risk. Action heads are server-tier only and
    require Council ratification (ADR-2605242120 §Safety rationale).
    """
    if tier == "edge":
        raise RuntimeError(
            "robotics action head is server-tier only; edge tier supports "
            "scene description only (see ADR-2605242120)"
        )


def load_action_head_server(*, _tier: RoboticsTier) -> None:
    """Stub: OpenVLA-style action head loader. Ships post-Council ratification."""
    assert_edge_no_actuation(_tier)
    raise NotImplementedError(
        "Move 6 server action head pending Council ratification of action-policy "
        "safety review per ADR-2605242120 §Safety rationale"
    )
