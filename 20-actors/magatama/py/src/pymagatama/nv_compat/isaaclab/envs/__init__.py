"""isaaclab.envs — Manager + Direct + MARL env families + mdp + task registry."""

from __future__ import annotations

from . import mdp
from .cartpole_direct_env import CartpoleDirectEnv, CartpoleDirectEnvCfg
from .direct_marl_env import DirectMARLEnv, DirectMARLEnvCfg
from .direct_rl_env import DirectRLEnv, DirectRLEnvCfg, SimCfg
from .manager_based_rl_env import CartpoleEnvCfg, ManagerBasedRLEnv
from .task_registry import (
    TaskSpec,
    all_task_ids,
    clear_registry,
    get_task_spec,
    make,
    num_registered,
    parse_env_cfg,
    register,
    unregister,
)
from .two_cartpole_marl_env import TwoCartpoleMARLEnv, TwoCartpoleMARLEnvCfg

__all__ = [
    "ManagerBasedRLEnv", "CartpoleEnvCfg",
    "DirectRLEnv", "DirectRLEnvCfg", "SimCfg",
    "CartpoleDirectEnv", "CartpoleDirectEnvCfg",
    "DirectMARLEnv", "DirectMARLEnvCfg",
    "TwoCartpoleMARLEnv", "TwoCartpoleMARLEnvCfg",
    "mdp",
    # task registry
    "TaskSpec", "register", "unregister", "get_task_spec",
    "all_task_ids", "num_registered", "clear_registry",
    "make", "parse_env_cfg",
]
