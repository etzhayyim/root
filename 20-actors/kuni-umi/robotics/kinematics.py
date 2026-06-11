"""kinematics — install-robot motion model (planar serial arm FK/IK + trajectory).

The :representative motion layer for the install/service fleet (Otete arm and
siblings). A planar serial arm is enough to answer the questions an R0
operational loop must answer honestly:

  * is the target pose reachable within the arm's workspace?
  * what joint configuration reaches it (analytic 2-link IK; closed form)?
  * what joint-space trajectory gets there, and does it respect the safety
    envelope (safety.SafetyEnvelope.check_trajectory)?

When 40-engine/kami-engine is checked out, the same task scripts target the
Featherstone 6-DOF solver (giemon_arm6); the FK/IK contract here is the subset
the cells depend on, so the swap is mechanical.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Pose:
    """A planar end-effector pose."""

    x: float
    y: float
    theta: float = 0.0  # end-effector orientation (rad), = sum of joint angles


@dataclass(frozen=True)
class PlanarArm:
    """A planar serial arm defined by its link lengths (metres)."""

    link_lengths: tuple[float, ...]

    @property
    def max_reach(self) -> float:
        return sum(self.link_lengths)

    @property
    def min_reach(self) -> float:
        """Inner workspace radius (0 if any single link can fold inside the rest)."""
        longest = max(self.link_lengths)
        rest = self.max_reach - longest
        return max(0.0, longest - rest)

    def fk(self, joints: tuple[float, ...]) -> Pose:
        """Forward kinematics: joint angles (rad, relative) → end-effector Pose."""
        if len(joints) != len(self.link_lengths):
            raise ValueError(
                f"expected {len(self.link_lengths)} joints, got {len(joints)}"
            )
        x = y = theta = 0.0
        for length, q in zip(self.link_lengths, joints):
            theta += q
            x += length * math.cos(theta)
            y += length * math.sin(theta)
        return Pose(x=round(x, 9), y=round(y, 9), theta=round(theta, 9))

    def reachable(self, x: float, y: float) -> bool:
        r = math.hypot(x, y)
        return self.min_reach - 1e-9 <= r <= self.max_reach + 1e-9

    def ik2(self, x: float, y: float, elbow_up: bool = True) -> tuple[float, float] | None:
        """Analytic 2-link inverse kinematics. Requires exactly 2 links.

        Returns (q0, q1) in radians, or None if (x, y) is unreachable. `elbow_up`
        selects between the two mirror solutions.
        """
        if len(self.link_lengths) != 2:
            raise ValueError("ik2 requires a 2-link arm")
        l1, l2 = self.link_lengths
        r2 = x * x + y * y
        cos_q1 = (r2 - l1 * l1 - l2 * l2) / (2.0 * l1 * l2)
        if cos_q1 < -1.0 - 1e-9 or cos_q1 > 1.0 + 1e-9:
            return None  # unreachable
        cos_q1 = min(1.0, max(-1.0, cos_q1))
        sin_q1 = math.sqrt(max(0.0, 1.0 - cos_q1 * cos_q1))
        if elbow_up:
            sin_q1 = -sin_q1
        q1 = math.atan2(sin_q1, cos_q1)
        q0 = math.atan2(y, x) - math.atan2(l2 * math.sin(q1), l1 + l2 * math.cos(q1))
        return (round(q0, 9), round(q1, 9))


def joint_trajectory(
    q_start: tuple[float, ...],
    q_goal: tuple[float, ...],
    steps: int,
) -> list[tuple[float, ...]]:
    """Linear joint-space interpolation from q_start to q_goal over `steps` steps.

    Returns `steps + 1` configurations (inclusive of both endpoints). Pair with
    safety.SafetyEnvelope.check_trajectory to bound the per-step joint rate.
    """
    if len(q_start) != len(q_goal):
        raise ValueError("start and goal must have equal joint count")
    if steps < 1:
        raise ValueError("steps must be >= 1")
    path: list[tuple[float, ...]] = []
    for k in range(steps + 1):
        a = k / steps
        path.append(tuple(s + a * (g - s) for s, g in zip(q_start, q_goal)))
    return path
