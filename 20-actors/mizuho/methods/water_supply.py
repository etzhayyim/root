"""water_supply — mizuho potable-water control loop (R0 :representative).

The runnable, tested core behind the `water_supply` cell. It proves a
community-scale supply actually holds pressure: a demand step (households open
taps) drops the reservoir level, the pump's secondary-PI loop drives inflow until
the level error integrates back to the service setpoint, and the modeled supply
restores service pressure.

This is the floating-point twin of an open-ot field-tier level/pressure loop.
mizuho constitutional gates apply: community-scale only (G3 — service population
is hard-capped here; a large municipal utility is N1, structurally unrepresentable),
no commercial water-utility software (G4 — this is a plain PI over a lumped tank,
not Veolia/Suez/Trojan firmware), Murakumo-only inference (G7 — not used in this
deterministic loop), and live actuation is consent-gated (G10 — this module is
offline sim only; cell.py .solve() stays Council-gated).
"""

from __future__ import annotations

from dataclasses import dataclass

from _substrate import PID, assert_civilian, simulate

# mizuho civilian-use allowlist (closed-world, N1). Water is for people + crops,
# never force. "supply" (potable distribution), "treat" (disinfection/filtration),
# "sample" (quality testing), "recycle" (greywater closed-loop), "irrigate"
# (mitsuho agricultural-grade dispatch).
PERMITTED_USES = ("supply", "treat", "sample", "recycle", "irrigate")

# G3 community-scale invariant: per-source service population is hard-capped.
# A request above the cap is N1 (a municipal utility) and is refused structurally.
MAX_SERVICE_POPULATION = 2500


class ReservoirPlant:
    """Community service-reservoir level dynamics (a Plant: measure/step).

    State is stored volume (litres). The pump command is inflow (L/s); a constant
    (settable) demand drains the tank. The controlled process variable is the
    water level (m) = volume / footprint-area; service pressure is proportional to
    head, so holding level holds pressure.

        dV/dt = inflow(command, L/s) - demand(L/s) - leak(level)
        level = V / area_m2 / 1000   (1 m^3 = 1000 L spread over area_m2)

    The reservoir is gravity-fed: distribution outflow ("leak") rises with head
    (`leak_coeff` L/s per metre of level), so the tank is self-regulating — a
    real first-order lag, not a pure integrator. Only a controller with integral
    action drives the level error to zero against a sustained demand, which is
    what the acceptance test asserts.
    """

    def __init__(
        self,
        area_m2: float = 20.0,
        level_m: float = 3.0,
        demand_lps: float = 0.0,
        max_level_m: float = 6.0,
        leak_coeff_lps_per_m: float = 100.0,
    ) -> None:
        self.area_m2 = area_m2
        self.max_level_m = max_level_m
        self._volume_l = level_m * area_m2 * 1000.0
        self._demand_lps = demand_lps
        self._leak_coeff = leak_coeff_lps_per_m

    def set_demand(self, demand_lps: float) -> None:
        """Apply a demand step (the disturbance the pump loop must reject)."""
        self._demand_lps = demand_lps

    @property
    def pressure_bar(self) -> float:
        """Service pressure (bar) ∝ static head (1 m water ≈ 0.0981 bar)."""
        return self.measure() * 0.0981

    def measure(self) -> float:
        return self._volume_l / (self.area_m2 * 1000.0)

    def step(self, command: float, dt: float) -> None:
        # command = pump inflow setpoint (L/s); cannot push the tank past its rim.
        # Gravity-fed distribution leak rises with head -> self-regulating tank.
        leak_lps = self._leak_coeff * self.measure()
        self._volume_l += (command - self._demand_lps - leak_lps) * dt
        if self._volume_l < 0.0:
            self._volume_l = 0.0
        max_v = self.max_level_m * self.area_m2 * 1000.0
        if self._volume_l > max_v:
            self._volume_l = max_v


@dataclass(frozen=True)
class WaterSupplyResult:
    """Outcome of a water-supply acceptance test (demand-step pressure recovery)."""

    use: str
    demand_step_lps: float
    setpoint_level_m: float
    final_level_m: float
    final_pressure_bar: float
    level_restored: bool
    settling_seconds: float
    service_population: int
    representative: bool  # G10: sims-only at R0


def commission_water_supply(
    demand_step_lps: float,
    use: str = "supply",
    setpoint_level_m: float = 3.0,
    area_m2: float = 20.0,
    service_population: int = 200,
    kp: float = 10.0,
    ki: float = 2.0,
    max_inflow_lps: float = 2000.0,
    steps: int = 4000,
    dt: float = 1.0,
) -> WaterSupplyResult:
    """Run the supply acceptance test. Raises (assert_civilian + G3) before any run.

    Apply `demand_step_lps`, run a secondary-PI pump loop, and confirm the level
    returns to `setpoint_level_m` (so service pressure is restored). Refuses a
    non-civilian use (N1) and refuses any request above the community-scale
    service-population cap (G3) — those are structurally unrepresentable here.
    """
    assert_civilian(use, PERMITTED_USES)  # N1 gate before any actuation modelling
    if service_population > MAX_SERVICE_POPULATION:
        from _substrate import SafetyError

        raise SafetyError(
            f"G3: service_population {service_population} exceeds the community-scale "
            f"cap {MAX_SERVICE_POPULATION}; a larger system is N1 (a municipal utility) "
            "and is structurally unrepresentable in mizuho"
        )

    tank = ReservoirPlant(area_m2=area_m2, level_m=setpoint_level_m, demand_lps=0.0)
    tank.set_demand(demand_step_lps)
    # Pump inflow is non-negative (a community pump cannot suck the tank down).
    pid = PID(kp=kp, ki=ki, out_min=0.0, out_max=max_inflow_lps)
    res = simulate(tank, pid, setpoint=setpoint_level_m, steps=steps, dt=dt, tol=1e-3)

    settling_seconds = res.settling_step * dt if res.settling_step >= 0 else -1.0
    return WaterSupplyResult(
        use=use,
        demand_step_lps=demand_step_lps,
        setpoint_level_m=setpoint_level_m,
        final_level_m=round(res.final_value, 4),
        final_pressure_bar=round(tank.pressure_bar, 4),
        level_restored=res.converged,
        settling_seconds=round(settling_seconds, 3),
        service_population=service_population,
        representative=True,
    )


def to_datoms(result: WaterSupplyResult, source_id: str) -> dict:
    """Project a supply acceptance result into kotoba EAVT-shaped datoms (G6/G9).

    Aggregate-only (no per-household consumption PII). The transactor appends these
    to the canonical Datom log; here we return the entity map a transactor writes.
    """
    return {
        ":water.supply/source-id": source_id,
        ":water.supply/use": result.use,
        ":water.supply/demand-step-lps": result.demand_step_lps,
        ":water.supply/setpoint-level-m": result.setpoint_level_m,
        ":water.supply/final-level-m": result.final_level_m,
        ":water.supply/final-pressure-bar": result.final_pressure_bar,
        ":water.supply/level-restored": result.level_restored,
        ":water.supply/settling-seconds": result.settling_seconds,
        ":water.supply/service-population": result.service_population,  # aggregate, ≤ G3 cap
        ":water.supply/representative": result.representative,          # G10
        ":water.supply/server-held-key": False,                        # no-server-key
        ":water.supply/dry-run": True,                                 # G10: R0 offline only
    }
