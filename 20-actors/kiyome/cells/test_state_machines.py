"""State-machine tests for kiyome cells (R0). .solve() is NOT called (it raises).

Exercises kiyome's defining gate: a cleaning pass into a private space can only be
attested if privacy-by-construction (G9/N5) holds as a HARD invariant — on-device only,
no retained imagery, no biometric capture.
"""

import pytest

from surface_cleaning.cell import SurfaceCleaningCell
from surface_cleaning.state_machine import (
    CleaningPhase,
    transition_to_cleaned,
    transition_to_pass_logged,
    transition_to_traversed,
)


def _run(method="vacuum", on_device=True, imagery=False, biometric=False,
         robot_sigs=("r1", "r2"), human="steward-did"):
    s = transition_to_traversed({"area_m2": 60})
    s = transition_to_cleaned({**s, "method": method})
    s = transition_to_pass_logged({
        **s,
        "on_device_only": on_device,
        "imagery_retained": imagery,
        "biometric_capture": biometric,
        "robot_sigs": list(robot_sigs),
        "human_attestation": human,
    })
    return s


def test_happy_path_logs_private_pass():
    s = _run()
    assert s["cell_state"]["phase"] == CleaningPhase.PASS_LOGGED.value
    p = s["cell_state"]["payload"]["cleaning_pass"]
    assert p["onDeviceOnly"] is True
    assert p["imageryRetained"] is False
    assert p["witnessQuorumMet"] is True


def test_g9_blocks_off_device_feed():
    with pytest.raises(ValueError, match="G9 violation"):
        _run(on_device=False)


def test_g9_blocks_retained_imagery():
    with pytest.raises(ValueError, match="G9 violation"):
        _run(imagery=True)


def test_n5_blocks_biometric_capture():
    with pytest.raises(ValueError, match="N5 violation"):
        _run(biometric=True)


def test_unknown_method_rejected():
    with pytest.raises(ValueError, match="unknown cleaning method"):
        _run(method="pressure-wash-with-camera")


def test_g3_quorum_requires_two_robots_and_a_human():
    s = _run(robot_sigs=("r1",), human="steward-did")
    assert s["cell_state"]["payload"]["cleaning_pass"]["witnessQuorumMet"] is False
    s2 = _run(robot_sigs=("r1", "r2"), human="")
    assert s2["cell_state"]["payload"]["cleaning_pass"]["witnessQuorumMet"] is False


def test_solve_raises_at_r0():
    with pytest.raises(RuntimeError, match="R0 scaffold"):
        SurfaceCleaningCell().solve({})
