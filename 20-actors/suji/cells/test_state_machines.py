"""suji (筋) — cell state-machine tests (load_solve coded cell + R0 scaffold gating)."""

from __future__ import annotations

import importlib
import pathlib
import sys

_CELLS = pathlib.Path(__file__).resolve().parent
if str(_CELLS) not in sys.path:
    sys.path.insert(0, str(_CELLS))

from load_solve.cell import LoadSolveCell  # noqa: E402
from load_solve.state_machine import (  # noqa: E402
    FORBIDDEN_CLINICAL_KEYS,
    LoadPhase,
    LoadState,
    transition_assert_nondiagnostic,
    transition_emit,
    transition_muscle_distribute,
    transition_static_inverse_dynamics,
)

_LAP_POSTURE = {
    "postureId": "p-lap", "headFlexDeg": 44.0, "trunkFlexDeg": 20.0,
    "shoulderFlexDeg": 15.0, "armsSupported": False,
}


def _run_to_emit() -> LoadState:
    s = LoadState(posture=dict(_LAP_POSTURE))
    s = transition_static_inverse_dynamics(s)
    s = transition_muscle_distribute(s)
    s = transition_assert_nondiagnostic(s)
    s = transition_emit(s)
    return s


def test_full_pipeline_reaches_emit() -> None:
    s = _run_to_emit()
    assert s.phase == LoadPhase.EMITTED.value
    assert any(d.get("load/joint") == "cervicothoracic" for d in s.emitted)
    assert any("muscle/mvc-pct" in d for d in s.emitted)


def test_cervical_load_present_and_large_for_lap() -> None:
    s = LoadState(posture=dict(_LAP_POSTURE))
    s = transition_static_inverse_dynamics(s)
    cerv = next(j for j in s.joint_loads if j["joint"] == "cervicothoracic")
    assert cerv["compressiveKgf"] > 15.0       # deep flexion → heavy neck load
    assert cerv["multVsHead"] > 3.0


def test_phase_order_enforced() -> None:
    s = LoadState(posture=dict(_LAP_POSTURE))
    for bad in (transition_muscle_distribute, transition_assert_nondiagnostic, transition_emit):
        try:
            bad(s)
            assert False, f"{bad.__name__} should require its predecessor phase"
        except ValueError:
            pass


def test_nondiagnostic_gate_refuses_clinical_key() -> None:
    s = _run_to_emit()
    s.phase = LoadPhase.DISTRIBUTED.value
    s.muscle_tensions.append({"group": "x", "mvcPct": 1.0, "diagnosis": "cervicalgia"})
    try:
        transition_assert_nondiagnostic(s)
        assert False, "G1 gate must refuse a clinical key"
    except ValueError as e:
        assert "non-diagnostic" in str(e)


def test_forbidden_set_covers_core_clinical_terms() -> None:
    assert {"diagnosis", "prescription", "treatment"} <= set(FORBIDDEN_CLINICAL_KEYS)


def test_solve_is_r0_gated() -> None:
    try:
        LoadSolveCell().solve({"posture": _LAP_POSTURE})
        assert False, "R0 cell .solve() must raise"
    except RuntimeError as e:
        assert "R0 scaffold" in str(e)
