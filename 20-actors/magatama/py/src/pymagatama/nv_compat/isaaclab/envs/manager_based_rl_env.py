"""isaaclab.envs.ManagerBasedRLEnv mirror.

R1.1 scope: CartpoleEnvCfg (mirrors isaaclab_tasks.manager_based.classic.cartpole
.CartpoleEnvCfg) + ManagerBasedRLEnv wrapper. Multi-env vectorization arrives
in R1.5 via kami-genesis WGSL compute (Phase D).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from ..._kernel import (
    ArticulatedSystem,
    CartpoleConfig,
    CartpoleState,
    cartpole_cfg_from_urdf,
    cartpole_step,
    parse_urdf,
)


# Mirror Lcg seeded RNG with kami_shugyo::cartpole_env::Lcg.
class _Lcg:
    def __init__(self, seed: int):
        self.state = (seed * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF

    def next_f32_centered(self, half_range: float) -> float:
        self.state = (self.state * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        u = ((self.state >> 33) & 0x7FFFFFFF) / float(1 << 31)
        return (u * 2.0 - 1.0) * half_range


@dataclass
class CartpoleEnvCfg:
    """Mirror of isaaclab_tasks.manager_based.classic.cartpole.CartpoleEnvCfg.

    Loaded directly from 70-tools/e7m-sim/scenes/cartpole/scene.yaml or set
    programmatically.
    """
    num_envs: int = 1                  # R1.1 = 1 env; R1.5 vectorizes via WGSL
    physics_dt: float = 1.0 / 60.0
    decimation: int = 2
    gravity: float = 9.81
    urdf_text: str = ""

    # reward weights (match scene.yaml)
    alive: float = 1.0
    terminating: float = -2.0
    pole_pos_penalty: float = -1.0
    cart_vel_penalty: float = -0.01
    pole_vel_penalty: float = -0.005

    # termination
    max_episode_length_s: float = 5.0
    pole_bounds: tuple[float, float] = (-0.2, 0.2)
    cart_bounds: tuple[float, float] = (-2.4, 2.4)


class ManagerBasedRLEnv:
    """Mirror of isaaclab.envs.ManagerBasedRLEnv (Cartpole-only at R1.1)."""

    def __init__(self, cfg: CartpoleEnvCfg, system: Optional[ArticulatedSystem] = None):
        self.cfg = cfg
        if system is None:
            if not cfg.urdf_text:
                raise ValueError("provide system or cfg.urdf_text")
            system = parse_urdf(cfg.urdf_text)
        self.system = system
        self._cartpole_cfg: CartpoleConfig = cartpole_cfg_from_urdf(
            system, gravity=cfg.gravity, dt=cfg.physics_dt
        )
        self._state = CartpoleState()
        self._max_steps = int(round(cfg.max_episode_length_s / cfg.physics_dt))
        self._steps = 0
        self._rng = _Lcg(0)

    @property
    def num_envs(self) -> int:
        return self.cfg.num_envs

    @property
    def observation_space(self) -> dict:
        return {"shape": (4,), "low": -math.inf, "high": math.inf}

    @property
    def action_space(self) -> dict:
        return {"shape": (1,), "low": -self._cartpole_cfg.force_mag,
                "high": self._cartpole_cfg.force_mag}

    def reset(self, seed: Optional[int] = None) -> tuple[list[float], dict]:
        if seed is not None:
            self._rng = _Lcg(seed)
        self._state = CartpoleState(
            x=self._rng.next_f32_centered(0.05),
            x_dot=self._rng.next_f32_centered(0.05),
            theta=self._rng.next_f32_centered(0.05),
            theta_dot=self._rng.next_f32_centered(0.05),
        )
        self._steps = 0
        return self._obs(), {}

    def step(self, action: list[float]) -> tuple[list[float], float, bool, bool, dict]:
        for _ in range(self.cfg.decimation):
            cartpole_step(self._state, float(action[0]), self._cartpole_cfg)
        self._steps += self.cfg.decimation

        terminated = (
            self._state.theta < self.cfg.pole_bounds[0]
            or self._state.theta > self.cfg.pole_bounds[1]
            or self._state.x < self.cfg.cart_bounds[0]
            or self._state.x > self.cfg.cart_bounds[1]
        )
        truncated = self._steps >= self._max_steps

        c = self.cfg
        reward = (
            c.alive
            + (c.terminating if terminated else 0.0)
            + c.pole_pos_penalty * self._state.theta * self._state.theta
            + c.cart_vel_penalty * self._state.x_dot * self._state.x_dot
            + c.pole_vel_penalty * self._state.theta_dot * self._state.theta_dot
        )
        return self._obs(), reward, terminated, truncated, {}

    def _obs(self) -> list[float]:
        return [self._state.x, self._state.x_dot, self._state.theta, self._state.theta_dot]
