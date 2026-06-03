"""Phase state machine for the sanae autonomous_weeding (草薙) cell.

Herbicide-free: the only weed-clearing methods are :mechanical and :laser (G9). A pass
record carries the witness signatures (>=2 robot + >=1 human, G3) and an explicit
herbicide-free assertion. Transitions are pure and unit-tested; the cell's .solve()
raises until Council activation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

ALLOWED_METHODS = ("mechanical", "laser")  # G9: NO chemical herbicide


class WeedingPhase(Enum):
    INIT = "init"
    SCANNED = "scanned"
    CLASSIFIED = "classified"
    WEED_CLEARED = "weed_cleared"
    PASS_LOGGED = "pass_logged"


@dataclass
class WeedingState:
    phase: str = WeedingPhase.INIT.value
    parcel_id: str = "did:web:sanae.etzhayyim.com/parcel/demo-0001"
    rows_scanned: int = 0
    weeds_detected: int = 0
    weeds_cleared: int = 0
    method: str = "mechanical"
    herbicide_free: bool = True
    robot_sigs: list = field(default_factory=list)
    human_attestation: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> WeedingState:
    return WeedingState(**d.get("cell_state", {}))


def transition_to_scanned(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.phase = WeedingPhase.SCANNED.value
    cs.rows_scanned = int(state.get("rows", 0))
    return {"cell_state": cs.__dict__, "next_node": "classify"}


def transition_to_classified(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.phase = WeedingPhase.CLASSIFIED.value
    cs.weeds_detected = int(state.get("weeds_detected", 0))
    return {"cell_state": cs.__dict__, "next_node": "weed_cleared"}


def transition_to_weed_cleared(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    method = state.get("method", cs.method)
    if method not in ALLOWED_METHODS:
        # G9 enforcement: a non-mechanical/laser method is a constitutional violation
        raise ValueError(f"G9 violation: weeding method {method!r} not in {ALLOWED_METHODS} (no herbicide)")
    cs.phase = WeedingPhase.WEED_CLEARED.value
    cs.method = method
    cs.herbicide_free = True
    cs.weeds_cleared = min(int(state.get("weeds_cleared", cs.weeds_detected)), cs.weeds_detected)
    return {"cell_state": cs.__dict__, "next_node": "pass_logged"}


def transition_to_pass_logged(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.phase = WeedingPhase.PASS_LOGGED.value
    cs.robot_sigs = list(state.get("robot_sigs", []))
    cs.human_attestation = state.get("human_attestation", "")
    # G3 witness quorum: >=2 robot sigs + >=1 human attestation to finalize a pass record
    quorum_ok = len(cs.robot_sigs) >= 2 and bool(cs.human_attestation)
    cs.payload = {
        "weeding_pass_record": {
            "parcelId": cs.parcel_id,
            "rowsScanned": cs.rows_scanned,
            "weedsDetected": cs.weeds_detected,
            "weedsCleared": cs.weeds_cleared,
            "method": cs.method,
            "herbicideFree": cs.herbicide_free,
            "witnessQuorumMet": quorum_ok,
        }
    }
    return {"cell_state": cs.__dict__, "next_node": "end"}
