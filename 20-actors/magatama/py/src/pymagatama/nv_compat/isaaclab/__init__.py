"""nv_compat.isaaclab — Isaac Lab 1.x public Python API surface (mirror).

Sub-namespaces:
  - envs (ManagerBasedRLEnv + DirectRLEnv + DirectMARLEnv + envs.mdp builders)
  - managers (ObservationManager / RewardManager / EventManager /
              TerminationManager — runtime layer over envs.mdp terms)
  - scene (InteractiveScene — terrain + assets + sensors + cloner composition)
  - sensors (RayCaster pattern-based ray bundle — heightfield scan for
             legged locomotion, obstacle bar for nav)
  - utils (utils.dr per-env DomainRandomizationCfg)
  - terrains (procedural height-field generators for legged locomotion)
  - algos (CEM + PPO trainers; SAC arrives at R1.x with off-policy buffer)
"""

from . import algos, managers, scene, sensors, terrains, utils

__all__ = ["algos", "managers", "scene", "sensors", "terrains", "utils"]
