"""plant — deterministic physical-plant simulation (the kami-genesis stand-in).

Until the 40-engine/kami-engine Rust submodule is checked out, the physics layer
is a set of honest `:representative` lumped-parameter plant models in pure
Python. They are intentionally simple (first-order lags, a swing-equation
microgrid) but *real* dynamics: the closed-loop controllers in control.py must
actually stabilise them, which is what the acceptance tests assert.

A `Plant` is anything with `measure() -> float` and `step(command, dt)`. Domain
actors add their own plants (water reservoir, gas-concentration, fibre coupler)
in their `methods/`; the two below are shared because they are reused across
domains and by the kuni-umi commissioning harness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class Plant(Protocol):
    """A controllable physical plant."""

    def measure(self) -> float:
        """Return the current process variable (the controlled quantity)."""
        ...

    def step(self, command: float, dt: float) -> None:
        """Advance the plant by `dt` seconds under actuator `command`."""
        ...


@dataclass
class FirstOrderPlant:
    """Generic first-order lag: τ·ẋ = −x + K·u  (+ constant disturbance d).

    The canonical test plant — a PID with ki>0 drives x to any reachable setpoint
    with zero steady-state error. Used to validate the controller + runner before
    trusting domain plants.
    """

    gain: float = 1.0
    tau: float = 1.0
    disturbance: float = 0.0
    x: float = 0.0

    def measure(self) -> float:
        return self.x

    def step(self, command: float, dt: float) -> None:
        dxdt = (-self.x + self.gain * command + self.disturbance) / self.tau
        self.x += dxdt * dt


@dataclass
class MicrogridPlant:
    """Islanded microgrid frequency dynamics (swing equation) + battery SoC.

    The controlled quantity is bus frequency (Hz). Frequency moves with the
    active-power imbalance between dispatchable generation `command` (the droop /
    PI setpoint, in kW) and the (uncontrolled) load:

        2H · df/dt = (P_gen − P_load) / S_base · f_nom − D·(f − f_nom)

    where H is the inertia constant (s), D a damping coefficient, S_base the base
    power (kW). Net generation also charges/discharges the battery, tracked as
    state-of-charge so the commissioning harness can assert it stays in band.

    This is the :representative twin of the open-ot DROOP_P_F / ANTI_ISLANDING /
    SOC_KALMAN field-tier cells (60-apps/etzhayyim-project-open-ot/cells/).
    """

    f_nom: float = 50.0           # nominal frequency (Hz)
    inertia_h: float = 4.0        # inertia constant (s)
    damping_d: float = 1.5        # load/damping coefficient (pu/Hz)
    s_base: float = 200.0         # base power (kW)
    p_load: float = 100.0         # current load (kW) — set by a load step
    battery_kwh: float = 500.0    # battery capacity (kWh)
    soc: float = 0.6              # state of charge [0,1]
    f: float = 50.0               # current frequency (Hz)

    def measure(self) -> float:
        return self.f

    def set_load(self, p_load_kw: float) -> None:
        """Apply a load step (the disturbance the controller must reject)."""
        self.p_load = p_load_kw

    def step(self, command: float, dt: float) -> None:
        # command = dispatchable generation setpoint (kW).
        imbalance_pu = (command - self.p_load) / self.s_base
        dfdt = (imbalance_pu * self.f_nom - self.damping_d * (self.f - self.f_nom)) / (
            2.0 * self.inertia_h
        )
        self.f += dfdt * dt
        # Net power flows to/from the battery (kW·h over dt seconds).
        net_kwh = (command - self.p_load) * (dt / 3600.0)
        self.soc = min(1.0, max(0.0, self.soc + net_kwh / self.battery_kwh))
