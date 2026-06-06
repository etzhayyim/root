"""suji (筋) — muscle %MVC + Rohmert strain tests."""

from __future__ import annotations

import math

from analyze import analyze_all
from load import solve_posture_loads
from muscle import SPECS, solve_muscle_tensions
from posture import LAPTOP_ON_LAP, posture_from_workstation
from segment import build_body
from strain import endurance_minutes, muscle_strain, session_strain, stiffness_band


def test_muscle_mvc_in_range_and_nonneg() -> None:
    body = build_body(70.0, 1.70)
    posture = posture_from_workstation(LAPTOP_ON_LAP)
    loads = solve_posture_loads(body, posture)
    tensions = solve_muscle_tensions(body, posture, loads)
    assert {t.name for t in tensions} == set(SPECS)
    for t in tensions:
        assert t.force_n >= 0
        assert 0 <= t.mvc_pct < 100  # holding a static posture, never maximal


def test_endurance_falls_with_load() -> None:
    assert endurance_minutes(50.0) < endurance_minutes(25.0) < endurance_minutes(15.0)
    # the classic ~15% MVC sustainability threshold: low load → effectively unlimited
    assert math.isinf(endurance_minutes(5.0))
    # representative fit anchors
    assert abs(endurance_minutes(50.0) - 1.0) < 0.6
    assert abs(endurance_minutes(25.0) - 5.0) < 2.5


def test_stiffness_grows_with_load_and_time() -> None:
    body = build_body(70.0, 1.70)
    posture = posture_from_workstation(LAPTOP_ON_LAP)
    tensions = solve_muscle_tensions(body, posture, solve_posture_loads(body, posture))
    high = next(t for t in tensions if t.name == "cervical_extensors")
    s_short = muscle_strain(high, 10.0)
    s_long = muscle_strain(high, 120.0)
    assert 0 <= s_short.stiffness_index <= s_long.stiffness_index < 1.0


def test_stiffness_band_thresholds() -> None:
    assert stiffness_band(0.1) == "low"
    assert stiffness_band(0.3) == "moderate"
    assert stiffness_band(0.6) == "high"
    assert stiffness_band(0.9) == "very-high"


def test_strain_rejects_negative_session() -> None:
    body = build_body()
    t = solve_muscle_tensions(body, posture_from_workstation(LAPTOP_ON_LAP),
                              solve_posture_loads(body, posture_from_workstation(LAPTOP_ON_LAP)))[0]
    try:
        muscle_strain(t, -5.0)
        assert False
    except ValueError:
        pass


def test_end_to_end_lap_worse_than_monitor() -> None:
    results = analyze_all(session_minutes=120.0)
    lap = next(r for r in results if r.workstation == "laptop-on-lap")
    mon = next(r for r in results if r.workstation == "external-monitor+keyboard")
    assert lap.worst_stiffness.stiffness_index > mon.worst_stiffness.stiffness_index
    # the headline: eye-level monitor cuts cervical load substantially
    reduction = 1 - mon.loads.cervical.compressive_load_kgf / lap.loads.cervical.compressive_load_kgf
    assert reduction > 0.4
