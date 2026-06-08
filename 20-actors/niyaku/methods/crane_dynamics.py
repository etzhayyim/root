"""crane_dynamics — gantry / ship-to-shore (STS) crane anti-sway physics core.

The defining control problem of automated container handling is **anti-sway**:
a quay crane moves a 20-40 t container suspended on cables while the trolley
traverses 30-50 m ship→shore. The suspended load is a pendulum; an aggressive
trolley move excites residual sway that must settle to < a few cm at the target
before the spreader can land the box on a stack tier. This is the classical
*cart + hanging payload* model — the same topology as Isaac Sim's Cartpole
(prismatic trolley + revolute load), which is why ``isaac_sway_sim`` can drive
the load through the clean-room ``isaacsim.core.api`` surface.

This module is the **analytic/control core**: physically-correct hanging
pendulum, a state-feedback anti-sway position controller, and a ZV
input-shaper (the technique most container terminals actually deploy).

stdlib-only · pywasm-ready · no NumPy. All state is plain ``list``/``float``.

Per ADR-2606074000 (niyaku R0). Methods are pure compute (no outward action,
G-no-server-key); they do not move a real crane.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple

# Sign convention
#   x        : trolley position along the quay rail (m), shore-positive
#   theta    : load swing angle from vertical (rad); theta>0 ⇒ load lags +x
#   cable    : hoist cable length from trolley to load CG (m)
# Equilibrium is the load hanging straight down (theta = 0) — the STABLE point,
# unlike the inverted Cartpole. Gravity restores the load toward theta = 0.


@dataclass
class GantryCrane:
    """Reduced-order single-pendulum-on-trolley model of an STS / RTG crane.

    The trolley is treated as acceleration-commanded (its own servo loop is far
    faster than the sway mode), so the control input ``u`` is trolley
    acceleration (m/s²), saturated at ``accel_max``.
    """

    cable_length: float = 30.0      # m, spreader+load below trolley
    gravity: float = 9.81           # m/s²
    sway_damping: float = 0.02      # dimensionless viscous damping ratio proxy
    accel_max: float = 0.6          # m/s², trolley accel envelope (comfort/safety)
    velocity_max: float = 4.0       # m/s, trolley max traverse speed
    rail_length: float = 60.0       # m, usable trolley travel

    def natural_frequency(self) -> float:
        """Undamped sway natural frequency ω = sqrt(g / L) (rad/s)."""
        return math.sqrt(self.gravity / self.cable_length)

    def sway_period(self) -> float:
        """Sway period T = 2π / ω (s) — sets the input-shaper impulse spacing."""
        return 2.0 * math.pi / self.natural_frequency()

    # ── dynamics ────────────────────────────────────────────────────────────

    def derivatives(self, state: List[float], u: float) -> List[float]:
        """Continuous-time state derivative for state = [x, x_dot, theta, theta_dot].

        Full (non-linearised) hanging-pendulum-on-trolley with viscous sway
        damping. Trolley acceleration equals the (clamped) command ``u``.
        """
        x, x_dot, theta, theta_dot = state
        a = self._clamp(u, self.accel_max)
        L = self.cable_length
        g = self.gravity
        # theta'' = -(g/L) sinθ - (a/L) cosθ - 2ζω θ'
        zeta_w = self.sway_damping * self.natural_frequency()
        theta_acc = (
            -(g / L) * math.sin(theta)
            - (a / L) * math.cos(theta)
            - 2.0 * zeta_w * theta_dot
        )
        return [x_dot, a, theta_dot, theta_acc]

    def step(self, state: List[float], u: float, dt: float) -> List[float]:
        """Advance one step by classic RK4 (stable for the stiff sway mode)."""
        def add(s: List[float], k: List[float], h: float) -> List[float]:
            return [s[i] + h * k[i] for i in range(4)]

        k1 = self.derivatives(state, u)
        k2 = self.derivatives(add(state, k1, dt / 2.0), u)
        k3 = self.derivatives(add(state, k2, dt / 2.0), u)
        k4 = self.derivatives(add(state, k3, dt), u)
        nxt = [
            state[i] + (dt / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i])
            for i in range(4)
        ]
        # enforce the trolley velocity envelope (servo limit)
        nxt[1] = self._clamp(nxt[1], self.velocity_max)
        return nxt

    @staticmethod
    def _clamp(v: float, lim: float) -> float:
        return max(-lim, min(lim, v))


# ── anti-sway state-feedback controller ─────────────────────────────────────


@dataclass
class AntiSwayController:
    """PD trolley positioning + sway-rate feedback.

    u = -kp (x - x_target) - kd x_dot + k_theta θ + k_thetad θ_dot

    The sway terms actively bleed pendulum energy so the load arrives quiet.
    Their sign is POSITIVE because here the equilibrium is the load hanging at
    θ=0 and trolley acceleration couples as -a/L into θ̈ (a forward push drives
    θ negative); a positive θ feedback therefore stiffens the restoring term
    (θ̈ ← -(g+k_theta)/L · θ) rather than cancelling it. Gains are normalised to
    the crane's natural frequency so a longer cable (slower sway) needs no
    re-tuning.
    """

    kp: float = 0.4
    kd: float = 1.7
    k_theta: float = 5.0
    k_thetad: float = 3.0

    def command(self, crane: GantryCrane, state: List[float], x_target: float) -> float:
        x, x_dot, theta, theta_dot = state
        w = crane.natural_frequency()
        u = (
            -self.kp * w * w * (x - x_target)
            - self.kd * w * x_dot
            + self.k_theta * theta
            + self.k_thetad / w * theta_dot
        )
        return crane._clamp(u, crane.accel_max)


# ── ZV input shaper (open-loop anti-sway, the terminal-deployed technique) ───


def zv_shaper(crane: GantryCrane) -> List[Tuple[float, float]]:
    """Zero-Vibration (ZV) input shaper impulses [(time_s, amplitude), ...].

    Two impulses spaced half a damped sway period cancel residual oscillation
    of a command applied through them. Returns normalised amplitudes summing
    to 1. This is the classic Singer-Seering shaper used on cranes.
    """
    zeta = crane.sway_damping
    w = crane.natural_frequency()
    wd = w * math.sqrt(max(1e-9, 1.0 - zeta * zeta))
    td = math.pi / wd  # half damped period
    k = math.exp(-zeta * math.pi / math.sqrt(max(1e-9, 1.0 - zeta * zeta)))
    a0 = 1.0 / (1.0 + k)
    a1 = k / (1.0 + k)
    return [(0.0, a0), (td, a1)]


# ── high-level traverse simulation ──────────────────────────────────────────


@dataclass
class TraverseResult:
    reached: bool
    settle_time_s: float
    residual_sway_m: float
    peak_sway_m: float
    final_x: float
    steps: int
    trajectory: List[List[float]] = field(default_factory=list)


def simulate_traverse(
    crane: GantryCrane,
    x_target: float,
    controller: AntiSwayController | None = None,
    dt: float = 1.0 / 50.0,
    max_time_s: float = 120.0,
    pos_tol_m: float = 0.10,
    sway_tol_m: float = 0.05,
    record: bool = False,
) -> TraverseResult:
    """Drive the trolley from rest at x=0 to ``x_target`` under anti-sway control.

    "Settled" = trolley within ``pos_tol_m`` of target AND the lateral load
    excursion (L·sinθ) within ``sway_tol_m`` AND sway rate near zero.
    Returns timing + residual-sway metrics used by the terminal's KPI gate.
    """
    if abs(x_target) > crane.rail_length:
        raise ValueError(f"x_target {x_target} exceeds rail_length {crane.rail_length}")
    ctrl = controller or AntiSwayController()
    state = [0.0, 0.0, 0.0, 0.0]
    L = crane.cable_length
    n = int(max_time_s / dt)
    peak = 0.0
    settle_time = -1.0
    traj: List[List[float]] = []
    for i in range(n):
        u = ctrl.command(crane, state, x_target)
        state = crane.step(state, u, dt)
        sway = abs(L * math.sin(state[2]))
        peak = max(peak, sway)
        if record:
            traj.append(list(state))
        settled = (
            abs(state[0] - x_target) <= pos_tol_m
            and sway <= sway_tol_m
            and abs(state[3]) <= 0.01
        )
        if settled and settle_time < 0.0:
            settle_time = (i + 1) * dt
            break
    residual = abs(L * math.sin(state[2]))
    return TraverseResult(
        reached=settle_time >= 0.0,
        settle_time_s=settle_time if settle_time >= 0.0 else max_time_s,
        residual_sway_m=residual,
        peak_sway_m=peak,
        final_x=state[0],
        steps=i + 1,
        trajectory=traj,
    )


def lift_cycle_time(
    crane: GantryCrane,
    traverse_m: float,
    hoist_up_m: float,
    hoist_down_m: float,
    hoist_speed_mps: float = 1.5,
) -> float:
    """Single-box cycle time estimate (s): hoist-up → traverse → hoist-down.

    Used by ``stow_plan`` to estimate berth productivity (moves/hour). The
    traverse term reuses the anti-sway settle time so the estimate reflects
    real sway-limited motion, not an unphysical bang-bang move.
    """
    res = simulate_traverse(crane, traverse_m)
    hoist = (hoist_up_m + hoist_down_m) / max(1e-6, hoist_speed_mps)
    return res.settle_time_s + hoist


def moves_per_hour(cycle_time_s: float) -> float:
    """Convert a per-box cycle time to the terminal productivity KPI."""
    if cycle_time_s <= 0:
        raise ValueError("cycle_time_s must be positive")
    return 3600.0 / cycle_time_s
