"""chlorination — mizuho residual-disinfection dosing loop (R0 :representative).

The runnable, tested core behind the disinfection half of `water_supply`. It
proves the dosing loop holds a safe free-chlorine residual in distribution: the
residual decays (demand + time), a secondary-PI doser raises it back to a target
(default 0.5 mg/L, a typical distribution residual), and — critically — the dose
is STRUCTURALLY CLAMPED so the modeled residual can never exceed the regulatory
ceiling MAX_RESIDUAL_MGL = 4.0 mg/L (WHO guideline / US-EPA MRDL).

mizuho constitutional gates apply:
  - G4: a plain PI over a lumped residual model, never commercial UV/dosing
    firmware (Trojan UV / Évian / Nestlé Pure Life PROHIBITED).
  - G6 (anti-paternalism, no mandatory fluoridation): chlorine disinfection
    ("disinfect") is a community-wide public-health measure and runs without
    per-member consent; FLUORIDE ("fluoridate") is a personal-supplementation
    measure and REFUSES (SafetyError) unless per_member_consent=True.
  - G7: Murakumo-only inference (not used in this deterministic loop).
  - G10: live dosing is consent-gated; this module is offline sim only; cell.py
    .solve() stays Council-gated.
"""

from __future__ import annotations

from dataclasses import dataclass

from _substrate import PID, SafetyError, simulate

# WHO guideline value / US-EPA maximum residual disinfectant level for free
# chlorine. A modeled residual can NEVER exceed this — enforced by a structural
# clamp on the doser command, not merely by tuning.
MAX_RESIDUAL_MGL = 4.0

# Agents mizuho can model dosing for. "disinfect" = free chlorine (community-wide,
# no per-member consent). "fluoridate" = fluoride (personal supplementation;
# requires per-member consent under G6 anti-paternalism).
PERMITTED_AGENTS = ("disinfect", "fluoridate")


class ResidualChlorinePlant:
    """Free-chlorine residual dynamics in a distribution volume (a Plant).

    First-order: the residual decays first-order (bulk + wall demand) and the
    doser command (mg/L·s added) raises it.

        dC/dt = dose_command - k_decay * C

    The controlled process variable is the residual concentration (mg/L). Only a
    controller with integral action holds a sustained residual against decay,
    which is what the acceptance test asserts. The doser command itself is clamped
    by the caller so the residual can never integrate above the ceiling.
    """

    def __init__(self, residual_mgl: float = 0.0, k_decay: float = 0.05) -> None:
        self._residual = residual_mgl
        self._k_decay = k_decay

    def measure(self) -> float:
        return self._residual

    def step(self, command: float, dt: float) -> None:
        # command = dose rate (mg/L per second). Decay is first-order.
        dcdt = command - self._k_decay * self._residual
        self._residual += dcdt * dt
        if self._residual < 0.0:
            self._residual = 0.0
        # Structural hard ceiling: the modeled residual can NEVER exceed the
        # regulatory MRDL, regardless of controller command (defence in depth on
        # top of the clamped doser).
        if self._residual > MAX_RESIDUAL_MGL:
            self._residual = MAX_RESIDUAL_MGL


class ClampedDoser:
    """A PI doser whose output is STRUCTURALLY clamped so the residual can never

    exceed MAX_RESIDUAL_MGL. Each step we cap the dose so that, even instantaneously
    added, the residual cannot cross the ceiling: max_dose·dt ≤ ceiling − current.
    The clamp is independent of gains — no choice of kp/ki can drive the residual
    over the regulatory limit. Wraps a substrate PID (anti-windup) and exposes the
    .reset()/.step(error,dt) contract simulate() requires.
    """

    def __init__(self, plant: "ResidualChlorinePlant", pid: PID, dt: float) -> None:
        self._plant = plant
        self._pid = pid
        self._dt = dt

    def reset(self) -> None:
        self._pid.reset()

    def step(self, error: float, dt: float) -> float:
        raw = self._pid.step(error, dt)
        if raw < 0.0:
            raw = 0.0
        # Hard structural clamp: do not dose more than would reach the ceiling.
        headroom = MAX_RESIDUAL_MGL - self._plant.measure()
        max_dose_rate = max(0.0, headroom / dt) if dt > 0 else 0.0
        return min(raw, max_dose_rate)


@dataclass(frozen=True)
class DosingResult:
    """Outcome of a residual-dosing acceptance test."""

    agent: str
    target_residual_mgl: float
    final_residual_mgl: float
    max_residual_mgl: float
    residual_held: bool
    ceiling_respected: bool  # modeled residual never exceeded MAX_RESIDUAL_MGL
    settling_seconds: float
    representative: bool  # G10: sims-only at R0


def commission_dosing(
    agent: str = "disinfect",
    target_residual_mgl: float = 0.5,
    per_member_consent: bool = False,
    k_decay: float = 0.05,
    kp: float = 0.4,
    ki: float = 0.15,
    steps: int = 4000,
    dt: float = 0.1,
) -> DosingResult:
    """Run the dosing acceptance test. Raises before any run on a gate violation.

    G6 (anti-paternalism): chlorine disinfection runs without per-member consent
    (community-wide public-health measure); fluoride REFUSES unless
    `per_member_consent=True`. The structural clamp guarantees the modeled residual
    never exceeds MAX_RESIDUAL_MGL whatever the target/gains.
    """
    if agent not in PERMITTED_AGENTS:
        raise SafetyError(
            f"dosing agent {agent!r} is not permitted; allowlist {PERMITTED_AGENTS!r}"
        )
    if agent == "fluoridate" and not per_member_consent:
        raise SafetyError(
            "G6: fluoride dosing requires per_member_consent=True (no mandatory "
            "fluoridation; anti-paternalism). Chlorine disinfection needs no consent."
        )
    if target_residual_mgl > MAX_RESIDUAL_MGL:
        raise SafetyError(
            f"target residual {target_residual_mgl} mg/L exceeds the regulatory "
            f"ceiling {MAX_RESIDUAL_MGL} mg/L (WHO/EPA); structurally refused"
        )

    plant = ResidualChlorinePlant(residual_mgl=0.0, k_decay=k_decay)
    pid = PID(kp=kp, ki=ki, out_min=0.0, out_max=MAX_RESIDUAL_MGL)
    doser = ClampedDoser(plant, pid, dt)
    res = simulate(plant, doser, setpoint=target_residual_mgl, steps=steps, dt=dt, tol=1e-3)

    # max residual ever modeled across the whole trajectory.
    max_residual = max((pv for _, pv, _ in res.trajectory), default=0.0)
    settling_seconds = res.settling_step * dt if res.settling_step >= 0 else -1.0
    return DosingResult(
        agent=agent,
        target_residual_mgl=target_residual_mgl,
        final_residual_mgl=round(res.final_value, 4),
        max_residual_mgl=round(max_residual, 4),
        residual_held=res.converged,
        ceiling_respected=max_residual <= MAX_RESIDUAL_MGL + 1e-9,
        settling_seconds=round(settling_seconds, 3),
        representative=True,
    )


def to_datoms(result: DosingResult, source_id: str) -> dict:
    """Project a dosing acceptance result into kotoba EAVT-shaped datoms.

    Aggregate-only. The transactor appends these to the canonical Datom log.
    """
    return {
        ":water.dosing/source-id": source_id,
        ":water.dosing/agent": result.agent,
        ":water.dosing/target-residual-mgl": result.target_residual_mgl,
        ":water.dosing/final-residual-mgl": result.final_residual_mgl,
        ":water.dosing/max-residual-mgl": result.max_residual_mgl,
        ":water.dosing/ceiling-mgl": MAX_RESIDUAL_MGL,
        ":water.dosing/residual-held": result.residual_held,
        ":water.dosing/ceiling-respected": result.ceiling_respected,  # G: hard clamp held
        ":water.dosing/settling-seconds": result.settling_seconds,
        ":water.dosing/representative": result.representative,        # G10
        ":water.dosing/server-held-key": False,                       # no-server-key
        ":water.dosing/dry-run": True,                                # G10: R0 offline only
    }
