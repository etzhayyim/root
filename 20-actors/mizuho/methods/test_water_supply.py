"""Tests for mizuho water-supply operational loop.

    cd 20-actors/mizuho/methods
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest
"""

from __future__ import annotations

import pytest

from _substrate import SafetyError
from water_supply import (
    MAX_SERVICE_POPULATION,
    ReservoirPlant,
    commission_water_supply,
    to_datoms,
)


def test_supply_restores_level_after_demand_step():
    res = commission_water_supply(demand_step_lps=20.0)
    assert res.level_restored
    assert res.final_level_m == pytest.approx(3.0, abs=1e-2)  # back to service setpoint
    assert res.settling_seconds > 0
    assert res.final_pressure_bar > 0  # service pressure restored


def test_supply_restores_for_large_demand_step():
    # A bigger demand (more taps open) is also rejected back to the setpoint.
    res = commission_water_supply(demand_step_lps=80.0, service_population=1500)
    assert res.level_restored
    assert res.final_level_m == pytest.approx(3.0, abs=1e-2)


@pytest.mark.parametrize("use", ["weapon", "fire-control", "interdiction", "flood"])
def test_non_civilian_use_refused(use):
    with pytest.raises(SafetyError):
        commission_water_supply(demand_step_lps=20.0, use=use)


def test_community_scale_cap_enforced_g3():
    # A service population above the community-scale cap is N1 (a municipal
    # utility) and is structurally refused before any run.
    with pytest.raises(SafetyError):
        commission_water_supply(
            demand_step_lps=20.0, service_population=MAX_SERVICE_POPULATION + 1
        )


def test_at_cap_is_allowed():
    res = commission_water_supply(
        demand_step_lps=20.0, service_population=MAX_SERVICE_POPULATION
    )
    assert res.service_population == MAX_SERVICE_POPULATION
    assert res.level_restored


def test_reservoir_self_regulates():
    # No pump command: a gravity-fed tank with a head-dependent leak drains
    # toward a lower equilibrium (real first-order dynamics, not free fall to 0).
    tank = ReservoirPlant(area_m2=20.0, level_m=3.0, demand_lps=10.0)
    start = tank.measure()
    for _ in range(100):
        tank.step(0.0, 1.0)
    assert tank.measure() < start
    assert tank.measure() >= 0.0


def test_datoms_are_aggregate_dry_run_no_server_key():
    res = commission_water_supply(demand_step_lps=20.0)
    d = to_datoms(res, "spring-001")
    assert d[":water.supply/dry-run"] is True
    assert d[":water.supply/server-held-key"] is False
    assert d[":water.supply/representative"] is True
    assert d[":water.supply/level-restored"] is True
    assert d[":water.supply/service-population"] <= MAX_SERVICE_POPULATION
