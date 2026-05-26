"""nv_compat.isaaclab — Isaac Lab 1.x public Python API surface (mirror).

Sub-namespaces:
  - envs (ManagerBasedRLEnv + CartpoleEnvCfg + envs.mdp term builders)
  - managers (ObservationManager / RewardManager / EventManager /
              TerminationManager — runtime layer over envs.mdp terms)
  - utils (utils.dr per-env DomainRandomizationCfg)
  - terrains (procedural height-field generators for legged locomotion)
  - algos (CEM trainer; PPO / SAC arrive at R1.x when full ML stack lands)
"""

from . import algos, managers, terrains, utils

__all__ = ["algos", "managers", "terrains", "utils"]
