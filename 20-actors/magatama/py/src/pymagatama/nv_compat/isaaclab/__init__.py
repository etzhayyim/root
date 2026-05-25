"""nv_compat.isaaclab — Isaac Lab 1.x public Python API surface (mirror).

Sub-namespaces:
  - envs (ManagerBasedRLEnv + CartpoleEnvCfg)
  - utils (utils.dr per-env DomainRandomizationCfg)
  - terrains (procedural height-field generators for legged locomotion)
"""

from . import terrains, utils

__all__ = ["terrains", "utils"]
