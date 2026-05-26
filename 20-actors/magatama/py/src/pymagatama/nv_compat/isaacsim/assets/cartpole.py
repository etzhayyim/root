"""Cartpole asset wrapper — bundles URDF + defaults + DOF metadata.

Mirrors the upstream pattern `isaacsim.assets.Cartpole(prim_path=...)`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _load_cartpole_urdf() -> str:
    """Load the kami-native cartpole URDF from 70-tools/e7m-sim/scenes."""
    # Walk up from this file to repo root.
    here = Path(__file__).resolve()
    # path: .../pymagatama/nv_compat/isaacsim/assets/cartpole.py
    # repo root is 7 levels up (file/assets/isaacsim/nv_compat/pymagatama/src/py/magatama/20-actors/<root>)
    for ancestor in here.parents:
        candidate = ancestor / "70-tools" / "e7m-sim" / "scenes" / "cartpole" / "cartpole.urdf"
        if candidate.exists():
            return candidate.read_text()
    raise FileNotFoundError("Could not locate cartpole.urdf — repo layout changed?")


@dataclass
class Cartpole:
    """Pre-configured Cartpole asset.

    Auto-loads kami-native cartpole.urdf, exposes default joint positions
    + DOF metadata. Construction:

        from pymagatama.nv_compat.isaacsim.assets import Cartpole
        from pymagatama.nv_compat.isaacsim.core.api import World, Articulation

        cart = Cartpole(prim_path="/World/Cartpole_0")
        w = World()
        art = Articulation(prim_path=cart.prim_path, name=cart.name,
                            urdf_text=cart.urdf_text)
        w.add_articulation(art)
        art.set_joint_positions(cart.default_joint_positions)
    """
    prim_path: str = "/World/Cartpole"
    name: str = "cartpole"
    urdf_text: str = field(default_factory=_load_cartpole_urdf)
    joint_names: tuple = ("slider_to_cart", "cart_to_pole")
    dof_count: int = 2
    default_joint_positions: tuple = (0.0, 0.0)
    default_joint_velocities: tuple = (0.0, 0.0)
    # Joint limits (from URDF — kept here for convenience without re-parsing).
    joint_lower_limits: tuple = (-2.4, -3.14159)
    joint_upper_limits: tuple = (2.4, 3.14159)
    effort_limits: tuple = (100.0, 0.0)  # pole un-actuated per URDF
