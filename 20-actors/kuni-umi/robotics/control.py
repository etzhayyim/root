"""control — closed-loop controllers + runner (the open-ot field-tier reference).

This is the deterministic Python reference of the field-tier control loops that
ship as fixed-point Rust WASM Function Blocks in
60-apps/etzhayyim-project-open-ot/cells/ (PID_LIMITED, DROOP_P_F, ...). The Rust
crates own the hard-RT, no-float, no-alloc deployment; this module is the
floating-point :representative twin used for offline acceptance tests, sim and
the kuni-umi commissioning harness (<=10 Hz coordination cadence).

Anything that drives a real device runs the Rust BFB under a certified safety
PLC. This module never touches hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from plant import Plant  # flat import (see __init__.py import convention)


@dataclass
class PID:
    """Limited PID with anti-windup — mirrors open-ot PID_LIMITED.

    Output is clamped to [out_min, out_max]; integration is held (conditional
    integration) whenever the unclamped command saturates, so the integral term
    cannot wind up while the actuator is railed.
    """

    kp: float
    ki: float = 0.0
    kd: float = 0.0
    out_min: float = float("-inf")
    out_max: float = float("inf")
    _integral: float = field(default=0.0, init=False)
    _prev_error: float | None = field(default=None, init=False)
    saturated: bool = field(default=False, init=False)

    def reset(self) -> None:
        self._integral = 0.0
        self._prev_error = None
        self.saturated = False

    def step(self, error: float, dt: float) -> float:
        deriv = 0.0
        if self._prev_error is not None and dt > 0:
            deriv = (error - self._prev_error) / dt
        # Tentative integral; only commit it if we do not saturate (anti-windup).
        tentative_integral = self._integral + error * dt
        raw = self.kp * error + self.ki * tentative_integral + self.kd * deriv
        clamped = min(self.out_max, max(self.out_min, raw))
        self.saturated = clamped != raw
        if not self.saturated:
            self._integral = tentative_integral
        self._prev_error = error
        return clamped


@dataclass
class Droop:
    """Proportional frequency/voltage droop — mirrors open-ot DROOP_P_F.

    A grid-forming source raises power as the measured quantity (frequency)
    droops below nominal: P = P_base + (1/R)·(nominal − measured), clamped to the
    source's power band. `R` is the per-unit droop slope (e.g. 0.05 = 5%).
    """

    nominal: float
    droop_r: float
    p_base: float = 0.0
    p_min: float = float("-inf")
    p_max: float = float("inf")

    def command(self, measured: float) -> float:
        p = self.p_base + (self.nominal - measured) / self.droop_r
        return min(self.p_max, max(self.p_min, p))


class DroopPI:
    """Primary droop (instantaneous) + secondary PI (zero steady-state error).

    The canonical grid-forming composite: a fast proportional droop arrests the
    frequency dive immediately while a slower PI trims the residual error to zero.
    Mirrors a device running the open-ot DROOP_P_F cell under an AGC/PI loop.

    `simulate` calls `step(error, dt)` with error = nominal − measured; the droop
    term recovers `measured` as `nominal − error`. Output is clamped to the droop
    power band so the composite never commands outside the source's limits.
    """

    def __init__(self, droop: "Droop", pid: "PID"):
        self.droop = droop
        self.pid = pid

    def reset(self) -> None:
        self.pid.reset()

    def step(self, error: float, dt: float) -> float:
        measured = self.droop.nominal - error
        cmd = self.droop.command(measured) + self.pid.step(error, dt)
        return min(self.droop.p_max, max(self.droop.p_min, cmd))


@dataclass(frozen=True)
class ControlResult:
    """Outcome of a closed-loop run. Deterministic for a given plant + controller."""

    setpoint: float
    final_value: float
    steady_error: float
    converged: bool
    settling_step: int          # first step after which |error| stays < tol; -1 if never
    max_abs_error: float
    steps: int
    trajectory: list[tuple[float, float, float]]  # (t, process_var, command)


def simulate(
    plant: Plant,
    controller: PID,
    setpoint: float,
    steps: int,
    dt: float,
    tol: float = 1e-3,
    settle_window: int = 10,
) -> ControlResult:
    """Run a PID closed loop against a plant and report convergence.

    `converged` is true iff the absolute tracking error stays below `tol` for the
    last `settle_window` steps. `settling_step` is the first index from which the
    error never again exceeds `tol`. Deterministic: same inputs ⇒ same trajectory.
    """
    controller.reset()
    traj: list[tuple[float, float, float]] = []
    errors: list[float] = []
    max_abs = 0.0
    for k in range(steps):
        pv = plant.measure()
        error = setpoint - pv
        cmd = controller.step(error, dt)
        traj.append((round(k * dt, 6), pv, cmd))
        errors.append(abs(error))
        max_abs = max(max_abs, abs(error))
        plant.step(cmd, dt)

    final_pv = plant.measure()
    steady_error = setpoint - final_pv

    # settling_step: first index from which every later error < tol.
    settling_step = -1
    for i in range(len(errors)):
        if all(e < tol for e in errors[i:]):
            settling_step = i
            break

    tail = errors[-settle_window:] if len(errors) >= settle_window else errors
    converged = bool(tail) and all(e < tol for e in tail)

    return ControlResult(
        setpoint=setpoint,
        final_value=round(final_pv, 6),
        steady_error=round(steady_error, 6),
        converged=converged,
        settling_step=settling_step,
        max_abs_error=round(max_abs, 6),
        steps=steps,
        trajectory=traj,
    )
