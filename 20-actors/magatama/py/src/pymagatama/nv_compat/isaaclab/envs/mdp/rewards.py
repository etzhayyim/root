"""Reward terms — composable reward function builders.

Each mdp reward function takes an env + optional params and returns a scalar.
RewGroup composes multiple weighted RewTerm into the final scalar reward.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class RewTerm:
    """One reward term in a manager-based env config.

    Final contribution = weight * func(env, **params).
    """
    func: Callable
    weight: float = 1.0
    params: dict = field(default_factory=dict)

    def evaluate(self, env) -> float:
        return self.weight * float(self.func(env, **self.params))


@dataclass
class RewGroup:
    """Composes multiple RewTerm into a scalar reward (sum of weighted terms)."""
    terms: dict = field(default_factory=dict)

    def evaluate(self, env) -> float:
        return sum(term.evaluate(env) for term in self.terms.values())

    def evaluate_breakdown(self, env) -> dict:
        """Per-term contributions (debug)."""
        return {name: term.evaluate(env) for name, term in self.terms.items()}

    def add(self, name: str, term: RewTerm) -> "RewGroup":
        self.terms[name] = term
        return self


# ── Standard reward functions ─────────────────────────────────────────────

def is_alive(env, asset_cfg: Optional[str] = None) -> float:
    """1.0 if the env is not in a terminated state."""
    return 0.0 if getattr(env, "_terminated", False) else 1.0


def is_terminated(env, asset_cfg: Optional[str] = None) -> float:
    """1.0 if env is in a terminated state (use with negative weight)."""
    return 1.0 if getattr(env, "_terminated", False) else 0.0


def joint_pos_l2(env, asset_cfg: Optional[str] = None,
                 joint_names: Optional[list] = None) -> float:
    """Sum of squared joint positions (penalises deviation from zero).

    If `joint_names` is given, only those joints (by index in the env's
    joint list) contribute. For Cartpole conventionally [1] = pole.
    """
    pos = env.get_joint_positions()
    if joint_names is None:
        return sum(p * p for p in pos)
    return sum(pos[i] * pos[i] for i in joint_names if i < len(pos))


def joint_vel_l2(env, asset_cfg: Optional[str] = None,
                 joint_names: Optional[list] = None) -> float:
    """Sum of squared joint velocities."""
    vel = env.get_joint_velocities()
    if joint_names is None:
        return sum(v * v for v in vel)
    return sum(vel[i] * vel[i] for i in joint_names if i < len(vel))


def action_l2(env, asset_cfg: Optional[str] = None) -> float:
    """L2 of last action (penalises large control effort)."""
    a = getattr(env, "_last_action", []) or []
    return sum(x * x for x in a)


def action_rate_l2(env, asset_cfg: Optional[str] = None) -> float:
    """L2 of action delta from previous step (penalises jerky control)."""
    a = getattr(env, "_last_action", []) or []
    prev = getattr(env, "_prev_action", []) or [0.0] * len(a)
    return sum((a[i] - prev[i]) ** 2 for i in range(min(len(a), len(prev))))


def joint_torques_l2(env, asset_cfg: Optional[str] = None) -> float:
    """L2 of last torques applied (mirrors action_l2 when there's no
    separate controller path; falls back to action_l2 when torques are
    not exposed)."""
    torques = getattr(env, "_last_torques", None)
    if torques is None:
        return action_l2(env, asset_cfg)
    return sum(t * t for t in torques)
