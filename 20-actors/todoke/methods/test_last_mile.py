"""Tests for methods/last_mile.py — sequencer correctness, G7 envelope, courier sizing.

The PARITY contract: this Python sequencer and the Rust `todoke-route` crate must return
the SAME visiting order on the shared fixtures. The Rust side pins
[0, 4, 2, 3, 1] / length 30 in `route/src/lib.rs::sequences_collinear_stops_in_order`;
``test_parity_collinear_matches_rust`` pins the identical result here.
"""

import pytest

from last_mile import (
    EnvelopeViolation,
    Stop,
    courier_freed_hours,
    displacement_cohort_size,
    plan_last_mile,
)

_COLLINEAR = [
    Stop(0, 0.0, 0.0, "sidewalk"),
    Stop(1, 30.0, 0.0, "doorpath"),
    Stop(2, 10.0, 0.0, "sidewalk"),
    Stop(3, 20.0, 0.0, "doorpath"),
    Stop(4, 5.0, 0.0, "crosswalk"),
]


def test_parity_collinear_matches_rust():
    order, length = plan_last_mile(_COLLINEAR, sae_level=4, commanded_mps=1.0)
    assert order == [0, 4, 2, 3, 1]          # identical to the Rust crate fixture
    assert abs(length - 30.0) < 1e-6


def test_two_opt_removes_crossing_on_square():
    sq = [
        Stop(0, 0.0, 0.0, "sidewalk"),
        Stop(1, 0.0, 10.0, "sidewalk"),
        Stop(2, 10.0, 10.0, "sidewalk"),
        Stop(3, 10.0, 0.0, "sidewalk"),
    ]
    _, length = plan_last_mile(sq, commanded_mps=1.5)
    assert length <= 30.0 + 1e-6


def test_g7_refuses_sae_5():
    with pytest.raises(EnvelopeViolation, match="exceeds ceiling"):
        plan_last_mile(_COLLINEAR, sae_level=5, commanded_mps=1.0)


def test_g7_refuses_road_zone():
    stops = _COLLINEAR + [Stop(9, 40.0, 0.0, "road")]
    with pytest.raises(EnvelopeViolation, match="outside todoke ODD"):
        plan_last_mile(stops, commanded_mps=1.0)


def test_g7_refuses_speed_over_cap():
    with pytest.raises(EnvelopeViolation, match="exceeds"):
        plan_last_mile(_COLLINEAR, commanded_mps=3.0)


def test_empty_refused():
    with pytest.raises(EnvelopeViolation, match="no stops"):
        plan_last_mile([])


def test_courier_sizing_is_positive():
    assert courier_freed_hours(1.0e7, 2200, 0.3) > 0
    assert displacement_cohort_size(1.0e7, 0.3) == 3_000_000
