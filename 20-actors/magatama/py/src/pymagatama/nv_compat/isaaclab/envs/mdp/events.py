"""Event terms — reset / mid-episode events.

Each mdp event function takes the env + optional params and may mutate the
env state (e.g. reset joint positions, randomise physics). Returns None.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class EventTerm:
    """One event term in a manager-based env config.

    `mode` follows Isaac Lab convention:
      - "reset"    — fires on episode reset
      - "interval" — fires every N steps within an episode
      - "startup"  — fires once at env construction
    """
    func: Callable
    mode: str = "reset"
    interval_steps: int = 0  # only used when mode == "interval"
    params: dict = field(default_factory=dict)

    def evaluate(self, env) -> None:
        self.func(env, **self.params)


# Seedable LCG matching nv_compat conventions.
class _Lcg:
    def __init__(self, seed: int):
        self.state = (seed * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF

    def next_u01(self) -> float:
        self.state = (self.state * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        return ((self.state >> 33) & 0x7FFFFFFF) / float(1 << 31)


# ── Standard event functions ──────────────────────────────────────────────

def reset_joints_by_offset(env, position_range: tuple = (-0.1, 0.1),
                           velocity_range: tuple = (-0.1, 0.1),
                           seed: Optional[int] = None,
                           asset_cfg: Optional[str] = None) -> None:
    """Reset joints to default + uniform offset in (low, high)."""
    rng = _Lcg(seed if seed is not None else 0)
    pos = list(env.get_joint_positions())
    vel = list(env.get_joint_velocities())
    for i in range(len(pos)):
        pos[i] = position_range[0] + (position_range[1] - position_range[0]) * rng.next_u01()
    for i in range(len(vel)):
        vel[i] = velocity_range[0] + (velocity_range[1] - velocity_range[0]) * rng.next_u01()
    env.set_joint_positions(pos)
    env.set_joint_velocities(vel)


def reset_joints_to_default(env, asset_cfg: Optional[str] = None) -> None:
    """Reset joints to zero (or env-defined default)."""
    defaults = getattr(env, "_default_joint_pos", None)
    n_pos = len(env.get_joint_positions())
    pos = defaults if defaults is not None else [0.0] * n_pos
    env.set_joint_positions(list(pos))
    env.set_joint_velocities([0.0] * n_pos)


def randomize_rigid_body_mass(env, mass_range: tuple = (0.8, 1.2),
                              seed: Optional[int] = None,
                              asset_cfg: Optional[str] = None,
                              body_name: Optional[str] = None) -> None:
    """Randomise a rigid body's mass within mass_range. For Cartpole this
    affects cart_mass; for DP it affects link1 mass. Defaults to cart_mass.

    The env must expose `_cartpole_cfg.cart_mass` and `_dp_cfg.{m1, m2}` for
    this to land (matches the existing ManagerBasedRLEnv state layout).
    """
    rng = _Lcg(seed if seed is not None else 0)
    new_mass = mass_range[0] + (mass_range[1] - mass_range[0]) * rng.next_u01()
    cfg = getattr(env, "_cartpole_cfg", None)
    if cfg is not None:
        # CartpoleConfig is mutable dataclass.
        cfg.cart_mass = new_mass
        return
    dp_cfg = getattr(env, "_dp_cfg", None)
    if dp_cfg is not None:
        dp_cfg.m1 = new_mass
