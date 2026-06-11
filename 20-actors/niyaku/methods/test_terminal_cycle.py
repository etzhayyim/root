"""Tests for terminal_cycle — end-to-end vessel-discharge orchestration."""

import pytest

from agv_transfer import Agv
from crane_dynamics import GantryCrane
from stow_plan import Container
from terminal_cycle import DischargeReport, YardLayout, simulate_discharge


def _boxes(n, port="JPYOK"):
    return [Container(f"B{i}", 20.0 - i, port) for i in range(n)]


def test_basic_discharge_runs_all_boxes():
    r = simulate_discharge(_boxes(6), ["JPYOK"], "JPYOK", bays=2, rows=2, tiers=3)
    assert isinstance(r, DischargeReport)
    assert r.moves == 6
    assert len(r.records) == 6
    assert r.discharge_time_s > 0
    assert 10 < r.moves_per_hour() < 200       # sane STS productivity band
    assert all(rec.agv_id for rec in r.records)  # every box got an AGV


def test_only_target_port_discharged():
    boxes = (
        _boxes(3, "JPYOK")
        + [Container(f"R{i}", 15.0, "NLRTM") for i in range(3)]
    )
    r = simulate_discharge(boxes, ["JPYOK", "NLRTM"], "JPYOK",
                           bays=3, rows=2, tiers=3)
    assert r.moves == 3
    assert all(rec.box_id.startswith("B") for rec in r.records)


def test_discharge_is_max_of_crane_and_agv():
    r = simulate_discharge(_boxes(4), ["JPYOK"], "JPYOK", bays=2, rows=2, tiers=2)
    assert r.discharge_time_s == pytest.approx(max(r.crane_timeline_s, r.agv_makespan_s))


def test_more_agvs_do_not_raise_crane_bound_time():
    """The single STS crane is the bottleneck; adding AGVs cannot speed it past
    the serial crane timeline."""
    common = dict(rotation=["JPYOK"], discharge_port="JPYOK", bays=2, rows=2, tiers=3)
    r2 = simulate_discharge(_boxes(6), agv_ids=["A1", "A2"], **common)
    r5 = simulate_discharge(_boxes(6), agv_ids=["A1", "A2", "A3", "A4", "A5"], **common)
    assert r2.crane_timeline_s == pytest.approx(r5.crane_timeline_s)
    assert r5.agv_makespan_s <= r2.agv_makespan_s
    # crane-bound: overall time equals the crane timeline in both
    assert r5.discharge_time_s == pytest.approx(r5.crane_timeline_s)


def test_empty_port_zero_productivity():
    r = simulate_discharge(_boxes(3, "JPYOK"), ["JPYOK", "SGSIN"], "SGSIN",
                           bays=2, rows=2, tiers=2)
    assert r.moves == 0
    assert r.discharge_time_s == 0.0
    assert r.moves_per_hour() == 0.0


def test_accepts_prebuilt_plan():
    from stow_plan import build_stow_plan
    boxes = _boxes(4)
    plan = build_stow_plan(boxes, ["JPYOK"], bays=2, rows=2, tiers=2)
    r = simulate_discharge(boxes, ["JPYOK"], "JPYOK", bays=2, rows=2, tiers=2, plan=plan)
    assert r.moves == 4


def test_custom_crane_yard_agv():
    r = simulate_discharge(
        _boxes(3), ["JPYOK"], "JPYOK", bays=2, rows=2, tiers=2,
        crane=GantryCrane(cable_length=20.0), agv=Agv(v_max=4.0),
        yard=YardLayout(apron_to_yard_m=200.0),
    )
    assert r.moves == 3
    assert r.max_residual_sway_m >= 0.0


def test_isaac_path_runs_or_falls_back():
    """use_isaac=True must produce a valid report whether or not the Isaac
    surface is importable (it falls back to the analytic model)."""
    r = simulate_discharge(_boxes(3), ["JPYOK"], "JPYOK",
                           bays=2, rows=2, tiers=2, use_isaac=True)
    assert r.moves == 3
    assert r.discharge_time_s > 0
