"""suji (筋) — load/segment physics tests, incl. the Hansraj 2014 validation anchor."""

from __future__ import annotations

import math

from load import cervical_load, solve_posture_loads
from posture import (
    EXTERNAL_MONITOR_EYE_LEVEL,
    LAPTOP_ON_LAP,
    posture_from_workstation,
)
from segment import GRAVITY, build_body, head_mass_kg


def test_segment_masses_sum_plausibly() -> None:
    body = build_body(70.0, 1.70)
    # sagittal subset (head, trunk, pelvis, one-side limb) is a fraction of body mass < 1.
    total = sum(s.mass_kg for s in body.segments.values())
    assert 0.4 * 70 < total < 0.75 * 70  # the modelled subset, not the whole body
    assert build_body(70).seg("head_neck").mass_kg > 0


def test_head_mass_matches_hansraj_head() -> None:
    # Hansraj uses a ~12 lb (5.44 kg) head; Winter's 8.1% at 67 kg ≈ 5.4 kg.
    assert abs(head_mass_kg(67.0) - 5.44) < 0.3


def test_reproduces_hansraj_table() -> None:
    """Cervical compressive load multiplier must track Hansraj (2014) within 10%."""
    head_w = head_mass_kg(70.0) * GRAVITY
    # Hansraj published multipliers of head weight (neutral→1×, up to ~5× at 60°).
    expected = {0: 1.0, 15: 2.25, 30: 3.33, 45: 4.08, 60: 5.0}
    for deg, mult in expected.items():
        got = cervical_load(deg, head_w).multiplier_vs_head
        assert abs(got - mult) / mult < 0.10, f"{deg}°: got {got:.2f}, expected {mult}"


def test_cervical_load_monotonic_in_flexion() -> None:
    head_w = head_mass_kg(70.0) * GRAVITY
    loads = [cervical_load(d, head_w).compressive_load_kgf for d in range(0, 61, 5)]
    assert all(b >= a for a, b in zip(loads, loads[1:]))


def test_cervical_load_rejects_bad_input() -> None:
    for bad in [(-1.0, 0.02), (50.0, 0.0)]:
        try:
            cervical_load(30.0, bad[0], extensor_arm_m=bad[1])
            assert False, "expected ValueError"
        except ValueError:
            pass


def test_laptop_lap_loads_more_than_eye_level_monitor() -> None:
    body = build_body(70.0, 1.70)
    lap = solve_posture_loads(body, posture_from_workstation(LAPTOP_ON_LAP))
    mon = solve_posture_loads(body, posture_from_workstation(EXTERNAL_MONITOR_EYE_LEVEL))
    assert lap.cervical.compressive_load_kgf > mon.cervical.compressive_load_kgf
    # eye-level monitor should be near head weight (~1.x×), lap should be multiples.
    assert mon.cervical.multiplier_vs_head < 2.0
    assert lap.cervical.multiplier_vs_head > 3.0


def test_unsupported_arms_load_shoulder_more() -> None:
    body = build_body(70.0, 1.70)
    sup = posture_from_workstation(EXTERNAL_MONITOR_EYE_LEVEL)        # arms supported
    unsup = posture_from_workstation(LAPTOP_ON_LAP)                   # arms unsupported
    sh_sup = next(j for j in solve_posture_loads(body, sup).joints if j.joint == "shoulder")
    sh_unsup = next(j for j in solve_posture_loads(body, unsup).joints if j.joint == "shoulder")
    assert sh_unsup.moment_nm > sh_sup.moment_nm
