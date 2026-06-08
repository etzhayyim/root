"""Tests for agv_transfer — AGV horizontal-transport planning core."""

import math

import pytest

from agv_transfer import (
    Agv,
    Move,
    SegmentReservation,
    dispatch,
    find_conflicts,
    reservations_conflict,
    travel_time,
)


def test_zero_and_negative_distance():
    a = Agv()
    assert travel_time(0.0, a) == 0.0
    with pytest.raises(ValueError):
        travel_time(-1.0, a)


def test_trapezoidal_long_leg_reaches_cruise():
    a = Agv(v_max=6.0, a_max=0.8)
    d = 200.0
    t = travel_time(d, a)
    # hand-computed: ramp 2*(6/0.8)=15s over 2*(0.5*0.8*7.5^2)=45m; cruise 155m/6
    expected = 2 * (a.v_max / a.a_max) + (d - a.v_max**2 / a.a_max) / a.v_max
    assert t == pytest.approx(expected)
    # average speed below v_max (ramps cost time)
    assert d / t < a.v_max


def test_triangular_short_leg_below_cruise():
    a = Agv(v_max=6.0, a_max=0.8)
    d = 10.0                       # too short to reach v_max (needs 45 m)
    t = travel_time(d, a)
    vp = math.sqrt(a.a_max * d)
    assert vp < a.v_max
    assert t == pytest.approx(2 * vp / a.a_max)


def test_travel_time_monotone_in_distance():
    a = Agv()
    ts = [travel_time(d, a) for d in (5, 20, 45, 100, 300)]
    assert ts == sorted(ts)


def test_reservation_conflict_same_segment_overlap():
    r1 = SegmentReservation("S1", "AGV1", 0.0, 10.0)
    r2 = SegmentReservation("S1", "AGV2", 5.0, 15.0)
    assert reservations_conflict(r1, r2)


def test_reservation_touching_endpoints_no_conflict():
    r1 = SegmentReservation("S1", "AGV1", 0.0, 10.0)
    r2 = SegmentReservation("S1", "AGV2", 10.0, 20.0)
    assert not reservations_conflict(r1, r2)


def test_reservation_different_segment_or_same_agv():
    base = SegmentReservation("S1", "AGV1", 0.0, 10.0)
    assert not reservations_conflict(base, SegmentReservation("S2", "AGV2", 0.0, 10.0))
    assert not reservations_conflict(base, SegmentReservation("S1", "AGV1", 0.0, 10.0))


def test_find_conflicts_pairs():
    rs = [
        SegmentReservation("S1", "A", 0, 10),
        SegmentReservation("S1", "B", 5, 12),   # conflicts with 0
        SegmentReservation("S2", "C", 0, 10),    # different segment
    ]
    assert find_conflicts(rs) == [(0, 1)]


def test_dispatch_balances_makespan():
    a = Agv()
    moves = [Move(f"m{i}", d) for i, d in enumerate([100, 100, 100, 100])]
    res = dispatch(moves, ["AGV1", "AGV2"], a)
    # 4 equal moves over 2 AGVs → 2 each, balanced
    assert all(len(v) == 2 for v in res.assignment.values())
    t_single = travel_time(100, a)
    assert res.makespan() == pytest.approx(2 * t_single)


def test_dispatch_lpt_puts_long_jobs_first():
    a = Agv()
    moves = [Move("big", 300), Move("s1", 20), Move("s2", 20)]
    res = dispatch(moves, ["AGV1", "AGV2"], a)
    # the big move alone on one AGV, two small on the other
    sizes = sorted(len(v) for v in res.assignment.values())
    assert sizes == [1, 2]
    assert res.makespan() > 0


def test_dispatch_requires_agv():
    with pytest.raises(ValueError):
        dispatch([Move("m", 10)], [], Agv())
