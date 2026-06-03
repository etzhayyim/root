"""State-machine tests for hataori cells (R0). .solve() is NOT called (it raises).

Exercises the constitutional heart of hataori: a finished lot CANNOT be attested unless
G9 (no worker below Basic-High-Income) AND G2 (displaced cohort registered for the
Displacement Dividend) both hold, and N4 (no overproduction) is respected.
"""

import pytest

from finishing_packing.cell import FinishingPackingCell
from finishing_packing.state_machine import (
    FinishingPhase,
    transition_to_finished,
    transition_to_folded,
    transition_to_lot_attested,
)


def _run(quantity=50, ceiling=50, no_below_bhi=True, dividend=True,
         cohort="hataori-C13-7531-global-2026", robot_sigs=("r1", "r2")):
    s = transition_to_finished({"quantity": quantity, "made_to_need_ceiling": ceiling, "offcut_waste_permille": 80})
    s = transition_to_folded(s)
    s = transition_to_lot_attested({
        **s,
        "displaced_cohort_id": cohort,
        "no_worker_below_bhi": no_below_bhi,
        "dividend_attested": dividend,
        "robot_sigs": list(robot_sigs),
    })
    return s


def test_happy_path_emits_lot_and_provenance():
    s = _run()
    assert s["cell_state"]["phase"] == FinishingPhase.LOT_ATTESTED.value
    p = s["cell_state"]["payload"]
    assert p["finished_lot"]["quantity"] == 50
    assert p["fair_labor_provenance"]["noWorkerBelowBhi"] is True
    assert p["fair_labor_provenance"]["dividendAttested"] is True
    assert p["fair_labor_provenance"]["displacedCohortId"]


def test_g9_blocks_below_bhi_reemployment():
    with pytest.raises(ValueError, match="G9 violation"):
        _run(no_below_bhi=False)


def test_g2_blocks_unfunded_displacement():
    with pytest.raises(ValueError, match="G2 violation"):
        _run(dividend=False)


def test_g2_blocks_missing_cohort():
    with pytest.raises(ValueError, match="G2 violation"):
        _run(cohort="")


def test_n4_blocks_overproduction():
    with pytest.raises(ValueError, match="N4 violation"):
        _run(quantity=1000, ceiling=50)


def test_solve_raises_at_r0():
    with pytest.raises(RuntimeError, match="R0 scaffold"):
        FinishingPackingCell().solve({})
