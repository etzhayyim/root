"""nv_compat.isaaclab — Isaac Lab 1.x public Python API surface (mirror).

Sub-namespaces:
  - envs (ManagerBasedRLEnv + DirectRLEnv + DirectMARLEnv + envs.mdp builders)
  - managers (ObservationManager / RewardManager / EventManager /
              TerminationManager — runtime layer over envs.mdp terms)
  - scene (InteractiveScene — terrain + assets + sensors + cloner composition)
  - sensors (RayCaster pattern-based ray bundle — heightfield scan for
             legged locomotion, obstacle bar for nav)
  - sim    (SimulationContext singleton lifecycle wrapper — step/reset/pause
            /stop, physics + render callback registries, instance() lookup)
  - markers (VisualizationMarkers — 3D viz primitives at world poses;
             pre-built SPHERE / CUBOID / COORDINATE_FRAME / ARROW_* cfgs)
  - controllers (DifferentialIKController — Jacobian-based IK with DLS /
             pseudoinverse; pairs with envs.mdp.JointPositionAction)
  - utils  (utils.dr per-env DomainRandomizationCfg; utils.math quaternion +
            Euler + frame-transform helpers)
  - terrains (procedural height-field generators for legged locomotion)
  - algos  (CEM + PPO trainers; SAC arrives at R1.x with off-policy buffer)
"""

from . import (
    algos, controllers, managers, markers, scene, sensors, sim, terrains, utils,
)

__all__ = [
    "algos", "controllers", "managers", "markers", "scene", "sensors", "sim",
    "terrains", "utils",
]
