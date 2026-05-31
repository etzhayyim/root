"""DoublePendulum asset wrapper."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def _load_dp_urdf() -> str:
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "70-tools" / "e7m-sim" / "scenes" / "double_pendulum" / "double_pendulum.urdf"
        if candidate.exists():
            return candidate.read_text()
    raise FileNotFoundError("Could not locate double_pendulum.urdf")


@dataclass
class DoublePendulum:
    """Pre-configured 2-link revolute serial chain (double pendulum)."""
    prim_path: str = "/World/DoublePendulum"
    name: str = "double_pendulum"
    urdf_text: str = field(default_factory=_load_dp_urdf)
    joint_names: tuple = ("shoulder", "elbow")
    dof_count: int = 2
    # q=0 = both links hanging straight down (stable equilibrium).
    default_joint_positions: tuple = (0.0, 0.0)
    default_joint_velocities: tuple = (0.0, 0.0)
    joint_lower_limits: tuple = (-3.14159, -3.14159)
    joint_upper_limits: tuple = (3.14159, 3.14159)
    effort_limits: tuple = (50.0, 50.0)
    # Convenience: link 1 and 2 each 1 m long, 1 kg uniform rod
    link_masses: tuple = (1.0, 1.0)
    link_lengths: tuple = (1.0, 1.0)
