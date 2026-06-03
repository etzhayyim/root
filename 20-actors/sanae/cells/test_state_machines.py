"""State-machine tests for sanae cells (R0). .solve() is NOT called (it raises)."""

import pytest

from autonomous_weeding.cell import AutonomousWeedingCell
from autonomous_weeding.state_machine import (
    WeedingPhase,
    transition_to_classified,
    transition_to_pass_logged,
    transition_to_scanned,
    transition_to_weed_cleared,
)


def _run(state, weeds=10, cleared=9, method="mechanical", robot_sigs=None, human="agronomist-did"):
    s = transition_to_scanned({**state, "rows": 40})
    s = transition_to_classified({**s, "weeds_detected": weeds})
    s = transition_to_weed_cleared({**s, "weeds_cleared": cleared, "method": method})
    s = transition_to_pass_logged({**s, "robot_sigs": robot_sigs or ["r1", "r2"], "human_attestation": human})
    return s


def test_happy_path_reaches_pass_logged():
    s = _run({})
    assert s["cell_state"]["phase"] == WeedingPhase.PASS_LOGGED.value
    rec = s["cell_state"]["payload"]["weeding_pass_record"]
    assert rec["herbicideFree"] is True
    assert rec["witnessQuorumMet"] is True
    assert rec["weedsCleared"] <= rec["weedsDetected"]


def test_g9_rejects_herbicide_method():
    with pytest.raises(ValueError, match="G9 violation"):
        _run({}, method="glyphosate")


def test_laser_method_allowed():
    s = _run({}, method="laser")
    assert s["cell_state"]["method"] == "laser"
    assert s["cell_state"]["herbicide_free"] is True


def test_g3_quorum_requires_two_robots_and_a_human():
    s = _run({}, robot_sigs=["r1"], human="agronomist-did")  # only 1 robot
    assert s["cell_state"]["payload"]["weeding_pass_record"]["witnessQuorumMet"] is False
    s2 = _run({}, robot_sigs=["r1", "r2"], human="")          # no human
    assert s2["cell_state"]["payload"]["weeding_pass_record"]["witnessQuorumMet"] is False


def test_solve_raises_at_r0():
    with pytest.raises(RuntimeError, match="R0 scaffold"):
        AutonomousWeedingCell().solve({})
