"""Phase state machine for the hataori finishing_packing (畳) cell.

This is the constitutional heart of hataori: the terminal cell that emits a finished
garment lot ONLY together with a fair-labor provenance record (G9). A lot cannot be
attested unless BOTH hold:
  - G9: no displaced worker is re-employed below the Basic-High-Income standard
        (noWorkerBelowBhi == True), and
  - G2: the displaced cohort is registered for the tenure-weighted Displacement Dividend
        (dividendAttested == True; ADR-2606032130).
A violation raises — robotics-without-redistribution is constitutionally invalid (the
actor exists to END sweatshop labour, not to recreate a worse one). N4: no fast-fashion
overproduction — quantity must not exceed the made-to-need ceiling.

Transitions are pure and unit-tested; the cell's .solve() raises until Council activation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FinishingPhase(Enum):
    INIT = "init"
    FINISHED = "finished"
    FOLDED = "folded"
    LOT_ATTESTED = "lot_attested"


@dataclass
class FinishingState:
    phase: str = FinishingPhase.INIT.value
    lot_id: str = "did:web:hataori.etzhayyim.com/lot/demo-0001"
    garment_type: str = "work-shirt"
    quantity: int = 0
    made_to_need_ceiling: int = 0
    offcut_waste_permille: int = 0
    # provenance inputs (G9 / G2)
    displaced_cohort_id: str = ""
    no_worker_below_bhi: bool = True
    dividend_attested: bool = False
    robot_sigs: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> FinishingState:
    return FinishingState(**d.get("cell_state", {}))


def transition_to_finished(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.phase = FinishingPhase.FINISHED.value
    cs.quantity = int(state.get("quantity", 0))
    cs.made_to_need_ceiling = int(state.get("made_to_need_ceiling", cs.quantity))
    # N4: no fast-fashion overproduction
    if cs.quantity > cs.made_to_need_ceiling:
        raise ValueError(
            f"N4 violation: quantity {cs.quantity} exceeds made-to-need ceiling {cs.made_to_need_ceiling}"
        )
    cs.offcut_waste_permille = int(state.get("offcut_waste_permille", 0))
    return {"cell_state": cs.__dict__, "next_node": "folded"}


def transition_to_folded(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.phase = FinishingPhase.FOLDED.value
    return {"cell_state": cs.__dict__, "next_node": "lot_attested"}


def transition_to_lot_attested(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.displaced_cohort_id = state.get("displaced_cohort_id", "")
    cs.no_worker_below_bhi = bool(state.get("no_worker_below_bhi", True))
    cs.dividend_attested = bool(state.get("dividend_attested", False))
    cs.robot_sigs = list(state.get("robot_sigs", []))

    # G9: the actor exists to END sweatshop labour
    if not cs.no_worker_below_bhi:
        raise ValueError(
            "G9 violation: a displaced worker would be re-employed below the Basic-High-Income standard"
        )
    # G2: no live displacement without a funded tenure-weighted dividend cohort (ADR-2606032130)
    if not cs.dividend_attested or not cs.displaced_cohort_id:
        raise ValueError(
            "G2 violation: displaced cohort not registered for the Displacement Dividend (ADR-2606032130)"
        )

    cs.phase = FinishingPhase.LOT_ATTESTED.value
    cs.payload = {
        "finished_lot": {
            "lotId": cs.lot_id,
            "garmentType": cs.garment_type,
            "quantity": cs.quantity,
            "offcutWastePermille": cs.offcut_waste_permille,
        },
        "fair_labor_provenance": {
            "lotId": cs.lot_id,
            "displacedCohortId": cs.displaced_cohort_id,
            "noWorkerBelowBhi": True,   # G9 invariant (const true in lexicon)
            "dividendAttested": cs.dividend_attested,
        },
    }
    return {"cell_state": cs.__dict__, "next_node": "end"}
