"""Tests for the shared infra-robotics substrate.

Run (flat imports, isolated from the repo's broken pytest plugin env):

    cd 20-actors/kuni-umi/robotics
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest
"""

from __future__ import annotations

import math

import pytest

from control import PID, Droop, simulate
from kinematics import PlanarArm, Pose, joint_trajectory
from plant import FirstOrderPlant, MicrogridPlant
from safety import (
    SafetyEnvelope,
    SafetyError,
    assert_civilian,
    require_member_signature,
    witness_quorum_ok,
)

PERMITTED = ("install", "service", "inspect")


# ─── safety ─────────────────────────────────────────────────────────

def test_civilian_allowlist_passes():
    assert_civilian("install", PERMITTED)  # no raise


@pytest.mark.parametrize("use", ["weapon", "directed-energy", "fire-control", "interdiction"])
def test_forbidden_force_uses_rejected(use):
    with pytest.raises(SafetyError):
        assert_civilian(use, PERMITTED)


def test_unlisted_use_rejected_closed_world():
    with pytest.raises(SafetyError):
        assert_civilian("mining", PERMITTED)  # not forbidden, but not allowlisted


def test_server_signature_refused():
    with pytest.raises(SafetyError):
        require_member_signature(member_sig="m:sig", server_sig="s:sig")


def test_missing_member_signature_refused():
    with pytest.raises(SafetyError):
        require_member_signature(member_sig="", server_sig="")


def test_member_signature_accepted():
    require_member_signature(member_sig="m:ed25519:demo")  # no raise


def test_witness_quorum_requires_two():
    assert witness_quorum_ok(["did:r:a", "did:r:b"])["ok"] is True
    assert witness_quorum_ok(["did:r:a"])["ok"] is False
    assert witness_quorum_ok(["did:r:a"])["escalate_council_lv6"] is True


def test_witness_quorum_rejects_duplicates():
    assert witness_quorum_ok(["did:r:a", "did:r:a"])["ok"] is False


def test_envelope_flags_overspeed_and_human_proximity():
    env = SafetyEnvelope(max_joint_speed=1.0, human_proximity_speed=0.25)
    traj = [(0.0, 0.0), (0.5, 0.0)]  # 0.5 rad in dt=1 → rate 0.5
    assert env.check_trajectory(traj, dt=1.0, human_present=False)["ok"] is True
    res = env.check_trajectory(traj, dt=1.0, human_present=True)
    assert res["ok"] is False and res["violations"]


# ─── control + plant ────────────────────────────────────────────────

def test_pid_drives_first_order_to_setpoint():
    plant = FirstOrderPlant(gain=2.0, tau=1.5)
    pid = PID(kp=2.0, ki=1.0, kd=0.0, out_min=-50, out_max=50)
    res = simulate(plant, pid, setpoint=5.0, steps=4000, dt=0.01, tol=1e-2)
    assert res.converged
    assert res.final_value == pytest.approx(5.0, abs=1e-2)
    assert res.settling_step >= 0


def test_pid_rejects_constant_disturbance():
    plant = FirstOrderPlant(gain=1.0, tau=1.0, disturbance=3.0)
    pid = PID(kp=3.0, ki=2.0, out_min=-100, out_max=100)
    res = simulate(plant, pid, setpoint=0.0, steps=4000, dt=0.01, tol=1e-2)
    assert res.converged  # integral term cancels the disturbance


def test_pid_anti_windup_clamps_output():
    plant = FirstOrderPlant(gain=1.0, tau=1.0)
    pid = PID(kp=5.0, ki=5.0, out_min=-1.0, out_max=1.0)
    res = simulate(plant, pid, setpoint=100.0, steps=200, dt=0.01)
    assert all(-1.0 - 1e-9 <= cmd <= 1.0 + 1e-9 for _, _, cmd in res.trajectory)


def test_droop_raises_power_as_frequency_droops():
    droop = Droop(nominal=50.0, droop_r=0.05, p_base=100.0, p_min=0.0, p_max=200.0)
    assert droop.command(50.0) == pytest.approx(100.0)
    assert droop.command(49.5) > 100.0           # under-frequency → more power
    assert droop.command(40.0) == pytest.approx(200.0)  # clamped to p_max


def test_microgrid_droop_pi_restores_frequency_after_load_step():
    grid = MicrogridPlant(p_load=100.0, f=50.0)
    grid.set_load(140.0)  # +40 kW load step knocks frequency down
    # Secondary control: PI on frequency error drives the generation setpoint until
    # generation == load and the frequency error integrates to zero.
    pid = PID(kp=20.0, ki=40.0, out_min=0.0, out_max=200.0)
    res = simulate(grid, pid, setpoint=50.0, steps=6000, dt=0.01, tol=1e-2)
    assert res.final_value == pytest.approx(50.0, abs=2e-2)
    assert res.converged
    assert 0.0 <= grid.soc <= 1.0
    assert res.trajectory[-1][2] == pytest.approx(140.0, abs=1.0)  # gen tracks load


# ─── kinematics ──────────────────────────────────────────────────────

def test_fk_two_link_straight():
    arm = PlanarArm(link_lengths=(1.0, 1.0))
    pose = arm.fk((0.0, 0.0))
    assert pose.x == pytest.approx(2.0)
    assert pose.y == pytest.approx(0.0)


def test_fk_ik_roundtrip():
    arm = PlanarArm(link_lengths=(1.0, 0.8))
    target = (1.2, 0.5)
    sol = arm.ik2(*target, elbow_up=True)
    assert sol is not None
    pose = arm.fk(sol)
    assert (pose.x, pose.y) == pytest.approx(target, abs=1e-6)


def test_ik_unreachable_returns_none():
    arm = PlanarArm(link_lengths=(1.0, 1.0))
    assert arm.ik2(5.0, 0.0) is None
    assert arm.reachable(5.0, 0.0) is False
    assert arm.reachable(1.5, 0.0) is True


def test_joint_trajectory_endpoints_and_length():
    path = joint_trajectory((0.0, 0.0), (1.0, -0.5), steps=10)
    assert len(path) == 11
    assert path[0] == (0.0, 0.0)
    assert path[-1] == pytest.approx((1.0, -0.5))


def test_trajectory_respects_envelope():
    arm = PlanarArm(link_lengths=(1.0, 0.8))
    q0 = arm.ik2(1.0, 0.2)
    q1 = arm.ik2(1.2, 0.5)
    path = joint_trajectory(q0, q1, steps=50)
    env = SafetyEnvelope(max_joint_speed=1.0)
    assert env.check_trajectory(path, dt=0.1)["ok"] is True
