"""Tests for crane_dynamics — gantry anti-sway physics core."""

import math

import pytest

from crane_dynamics import (
    AntiSwayController,
    GantryCrane,
    lift_cycle_time,
    moves_per_hour,
    simulate_traverse,
    zv_shaper,
)


def test_natural_frequency_and_period():
    c = GantryCrane(cable_length=30.0, gravity=9.81)
    w = c.natural_frequency()
    assert w == pytest.approx(math.sqrt(9.81 / 30.0))
    assert c.sway_period() == pytest.approx(2 * math.pi / w)
    # longer cable ⇒ slower sway
    assert GantryCrane(cable_length=60.0).natural_frequency() < w


def test_hanging_load_is_stable_equilibrium():
    """No input, small initial sway → it decays (gravity restores)."""
    c = GantryCrane(cable_length=20.0, sway_damping=0.05)
    state = [0.0, 0.0, 0.15, 0.0]  # 0.15 rad initial sway
    peak0 = abs(state[2])
    for _ in range(4000):
        state = c.step(state, 0.0, 1.0 / 100.0)
    assert abs(state[2]) < peak0          # decayed
    assert abs(state[2]) < 0.05
    assert all(math.isfinite(v) for v in state)


def test_trolley_velocity_envelope_enforced():
    c = GantryCrane(velocity_max=2.0, accel_max=5.0)
    state = [0.0, 0.0, 0.0, 0.0]
    for _ in range(2000):
        state = c.step(state, 5.0, 1.0 / 100.0)  # max push forever
    assert abs(state[1]) <= 2.0 + 1e-6           # clamped to velocity_max


def test_accel_command_is_saturated():
    c = GantryCrane(accel_max=0.6)
    d = c.derivatives([0, 0, 0, 0], 100.0)  # absurd command
    assert d[1] == pytest.approx(0.6)        # x_acc clamped
    d = c.derivatives([0, 0, 0, 0], -100.0)
    assert d[1] == pytest.approx(-0.6)


def test_simulate_traverse_reaches_and_damps_sway():
    c = GantryCrane(cable_length=25.0, accel_max=0.7, velocity_max=4.0)
    res = simulate_traverse(c, x_target=30.0, max_time_s=300.0)
    assert res.reached
    assert abs(res.final_x - 30.0) <= 0.10
    assert res.residual_sway_m <= 0.05
    assert res.settle_time_s > 0.0


def test_anti_sway_beats_no_control_on_residual():
    c = GantryCrane(cable_length=25.0)
    with_ctrl = simulate_traverse(c, 25.0, AntiSwayController(), max_time_s=300.0)
    # a degenerate controller with zero sway feedback rings far more
    naive = simulate_traverse(
        c, 25.0, AntiSwayController(k_theta=0.0, k_thetad=0.0), max_time_s=300.0
    )
    assert with_ctrl.peak_sway_m < naive.peak_sway_m


def test_traverse_target_beyond_rail_raises():
    c = GantryCrane(rail_length=60.0)
    with pytest.raises(ValueError):
        simulate_traverse(c, x_target=80.0)


def test_zv_shaper_amplitudes_sum_to_one():
    c = GantryCrane(cable_length=30.0, sway_damping=0.02)
    imp = zv_shaper(c)
    assert len(imp) == 2
    t0, a0 = imp[0]
    t1, a1 = imp[1]
    assert t0 == 0.0
    assert a0 + a1 == pytest.approx(1.0)
    assert t1 == pytest.approx(c.sway_period() / 2.0, rel=0.05)  # ~half period


def test_cycle_time_and_productivity():
    c = GantryCrane(cable_length=25.0)
    t = lift_cycle_time(c, traverse_m=30.0, hoist_up_m=20.0, hoist_down_m=18.0)
    assert t > 0.0
    mph = moves_per_hour(t)
    assert 5.0 < mph < 120.0          # a sane STS productivity band
    with pytest.raises(ValueError):
        moves_per_hour(0.0)
