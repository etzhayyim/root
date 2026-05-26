"""isaaclab.algos — RL training algorithms (kami-native subset).

R1.x scope:
  - CEM (Cross-Entropy Method): pure-stdlib ES-style trainer for low-DOF
    control tasks (Cartpole 4-obs × 1-act). No PyTorch/numpy dependency.
  - PPO (Proximal Policy Optimization): stdlib-only policy-gradient trainer
    with manual-backprop 2-layer MLP, diagonal Gaussian policy, GAE-λ, and
    Adam optimizer. The canonical Isaac Lab RL algorithm.
  - SAC (Soft Actor-Critic): off-policy MaxEnt actor-critic trainer with
    twin Q networks + Polyak soft-update + auto-tuned entropy temperature.
    Pairs with iter 55 ReplayBuffer for sample-efficient continuous control.

These are kami-native; upstream Isaac Lab uses skrl / rsl_rl / rl_games as
separate packages. The nv_compat surface ships minimal in-tree trainers
(CEM + PPO + SAC) so that the "training works" loop closes end-to-end
without extra dependencies. Users can still wire skrl / rsl_rl externally.
"""

from .cem import CEMConfig, CEMResult, CEMTrainer, LinearPolicy
from .ppo import (
    MLP,
    GaussianPolicy,
    PPOConfig,
    PPOResult,
    PPOTrainer,
    ValueFunction,
)
from .sac import QNetwork, SACConfig, SACResult, SACTrainer

__all__ = [
    "CEMConfig", "CEMResult", "CEMTrainer", "LinearPolicy",
    "PPOConfig", "PPOResult", "PPOTrainer",
    "SACConfig", "SACResult", "SACTrainer", "QNetwork",
    "MLP", "GaussianPolicy", "ValueFunction",
]
