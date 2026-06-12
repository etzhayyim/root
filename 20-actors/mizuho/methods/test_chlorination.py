"""Tests for mizuho residual-dosing (chlorination) operational loop.

    cd 20-actors/mizuho/methods
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest
"""

from __future__ import annotations

import pytest

from _substrate import PID, SafetyError, simulate
from chlorination import (
    MAX_RESIDUAL_MGL,
    ClampedDoser,
    ResidualChlorinePlant,
    commission_dosing,
    to_datoms,
)


def test_chlorine_holds_target_residual_without_consent():
    # Community-wide disinfection: no per-member consent needed (G6).
    res = commission_dosing(agent="disinfect", target_residual_mgl=0.5)
    assert res.residual_held
    assert res.final_residual_mgl == pytest.approx(0.5, abs=1e-2)
    assert res.ceiling_respected
    assert res.settling_seconds > 0


def test_residual_never_exceeds_regulatory_ceiling():
    # Even commanding a target right at the ceiling, the modeled residual must
    # never cross MAX_RESIDUAL_MGL.
    res = commission_dosing(agent="disinfect", target_residual_mgl=3.9)
    assert res.max_residual_mgl <= MAX_RESIDUAL_MGL + 1e-9
    assert res.ceiling_respected


def test_clamp_holds_even_with_aggressive_gains():
    # The clamp is structural — no choice of gains can drive the residual over
    # the regulatory ceiling.
    plant = ResidualChlorinePlant(residual_mgl=0.0, k_decay=0.0)
    pid = PID(kp=1000.0, ki=1000.0, out_min=0.0, out_max=1e6)
    doser = ClampedDoser(plant, pid, dt=0.1)
    res = simulate(plant, doser, setpoint=999.0, steps=3000, dt=0.1, tol=1e-3)
    worst = max(pv for _, pv, _ in res.trajectory)
    assert worst <= MAX_RESIDUAL_MGL + 1e-9


def test_target_above_ceiling_refused():
    with pytest.raises(SafetyError):
        commission_dosing(agent="disinfect", target_residual_mgl=MAX_RESIDUAL_MGL + 0.1)


def test_fluoride_without_consent_refused_g6():
    # No mandatory fluoridation — anti-paternalism (G6).
    with pytest.raises(SafetyError):
        commission_dosing(agent="fluoridate", target_residual_mgl=0.7)


def test_fluoride_with_consent_passes():
    res = commission_dosing(
        agent="fluoridate", target_residual_mgl=0.7, per_member_consent=True
    )
    assert res.residual_held
    assert res.final_residual_mgl == pytest.approx(0.7, abs=1e-2)
    assert res.ceiling_respected


def test_unknown_agent_refused():
    with pytest.raises(SafetyError):
        commission_dosing(agent="bleach-the-river", target_residual_mgl=0.5)


def test_datoms_are_dry_run_no_server_key():
    res = commission_dosing(agent="disinfect", target_residual_mgl=0.5)
    d = to_datoms(res, "spring-001")
    assert d[":water.dosing/dry-run"] is True
    assert d[":water.dosing/server-held-key"] is False
    assert d[":water.dosing/ceiling-respected"] is True
    assert d[":water.dosing/ceiling-mgl"] == MAX_RESIDUAL_MGL
