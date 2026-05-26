"""isaaclab.algos — RL training algorithms (kami-native subset).

R1.x scope:
  - CEM (Cross-Entropy Method): pure-stdlib ES-style trainer for low-DOF
    control tasks (Cartpole 4-obs × 1-act). No PyTorch/numpy dependency.

Future R1.x adds:
  - PPO (with manual auto-diff MLP) when G5 gate ±10% Isaac Sim baseline
    comparison needs an RL-trained reference.
  - SAC for off-policy continuous control.

These are kami-native; upstream Isaac Lab uses skrl / rsl_rl / rl_games as
separate packages. The nv_compat surface chooses to ship a minimal in-tree
trainer (CEM) so that the "training works" loop closes end-to-end without
extra dependencies. Users can still wire skrl / rsl_rl externally.
"""

from .cem import CEMConfig, CEMResult, CEMTrainer, LinearPolicy

__all__ = ["CEMConfig", "CEMResult", "CEMTrainer", "LinearPolicy"]
