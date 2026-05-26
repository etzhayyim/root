"""isaacsim.assets — pre-configured robot asset wrappers.

Mirrors `isaacsim.assets` (Isaac Sim 4.x) for the robots that the kami
substrate can simulate today. Each wrapper bundles:
  - URDF text (loaded from 70-tools/e7m-sim/scenes/<robot>/<robot>.urdf)
  - Default joint positions (rest pose)
  - DOF metadata (joint names, count, limits)
  - Optional default sensor mounts (cameras, IMUs)

Standard upstream Isaac Sim asset names (Franka, UR10, ANYmal, Cassie,
Carter, Jetbot) require their respective URDFs which aren't yet vendored
into religious-corp substrate. The R1.x asset surface starts with the
substrate-native robots (Cartpole, DoublePendulum, PlanarChain) and grows
as more URDFs land.
"""

from .cartpole import Cartpole
from .double_pendulum import DoublePendulum
from .planar_chain import PlanarChain

__all__ = ["Cartpole", "DoublePendulum", "PlanarChain"]
