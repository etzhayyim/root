"""Observation terms — composable observation builders.

Each mdp observation function takes an env (with get_joint_positions /
get_joint_velocities accessors) and returns a list of floats. Functions
support an optional `asset_cfg` parameter naming a specific articulation,
matching the Isaac Lab pattern.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class ObsTerm:
    """One observation term in a manager-based env config.

    `func` is called as `func(env, **params)` and must return a list[float]
    (or a single float). `scale` multiplies the raw output; `clip` caps to
    (low, high) magnitude.
    """
    func: Callable
    params: dict = field(default_factory=dict)
    scale: float = 1.0
    clip: Optional[tuple] = None  # (low, high) or None

    def evaluate(self, env) -> list:
        raw = self.func(env, **self.params)
        if not isinstance(raw, list):
            raw = [raw]
        out = [x * self.scale for x in raw]
        if self.clip is not None:
            low, high = self.clip
            out = [max(low, min(high, v)) for v in out]
        return out


@dataclass
class ObsGroup:
    """Composes multiple ObsTerm into a single observation vector.

    Iteration order is insertion order (dict-of-terms or ordered list).
    """
    terms: dict = field(default_factory=dict)

    def evaluate(self, env) -> list:
        out = []
        for _name, term in self.terms.items():
            out.extend(term.evaluate(env))
        return out

    def add(self, name: str, term: ObsTerm) -> "ObsGroup":
        self.terms[name] = term
        return self


# ── Standard observation functions ────────────────────────────────────────

def joint_pos_rel(env, asset_cfg: Optional[str] = None) -> list:
    """Joint positions relative to default (or absolute if no defaults)."""
    return list(env.get_joint_positions())


def joint_vel_rel(env, asset_cfg: Optional[str] = None) -> list:
    """Joint velocities."""
    return list(env.get_joint_velocities())


def base_lin_vel(env, asset_cfg: Optional[str] = None) -> list:
    """Base body linear velocity. For Cartpole the cart is treated as base."""
    pos = env.get_joint_positions()
    vel = env.get_joint_velocities()
    # Heuristic: first joint velocity component is the base linear vel (cart for Cartpole).
    # Real impl reads link_state but this matches the existing _state pattern.
    return [vel[0] if vel else 0.0, 0.0, 0.0]


def base_ang_vel(env, asset_cfg: Optional[str] = None) -> list:
    """Base body angular velocity. For Cartpole there is no rotation base."""
    return [0.0, 0.0, 0.0]


def last_action(env, asset_cfg: Optional[str] = None) -> list:
    """Most recently applied action (or [0,...] if none yet)."""
    return list(getattr(env, "_last_action", []) or [0.0])


def generated_commands(env, command_name: str = "default") -> list:
    """User-injected command vectors (target joint pose / velocity / pose).

    Stored on env via `env._commands[command_name] = [...]`; defaults to [].
    """
    commands = getattr(env, "_commands", {})
    return list(commands.get(command_name, []))
