"""launch_commissioning state machine — ADR-2606013400 (L5b float-out + inclining test + dock trial).

R0 scaffold: phase transitions are structural placeholders. The cell's .solve()
raises RuntimeError until Council Lv6+ ratifies the R1 activation ADR-2606013415.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LaunchCommissioningPhase(Enum):
    INIT = "init"
    FLOATED_OUT = "floated_out"
    INCLINING_TEST_DONE = "inclining_test_done"
    DOCK_TRIAL_DONE = "dock_trial_done"
    RECORD_EMITTED = "record_emitted"


@dataclass
class CellState:
    phase: str = LaunchCommissioningPhase.INIT.value
    vesselId: str = "NAGI-COASTAL-0001"
    vesselClass: str = "Nagi 凪"
    completionPct: int = 0
    robotSignatures: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)

def transition_to_floated_out(state: dict[str, Any]) -> dict[str, Any]:
    """INIT -> FLOATED_OUT."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = LaunchCommissioningPhase.FLOATED_OUT.value
    cs.completionPct = 25
    return {"cell_state": cs.__dict__, "next_node": "inclining_test_done"}
def transition_to_inclining_test_done(state: dict[str, Any]) -> dict[str, Any]:
    """FLOATED_OUT -> INCLINING_TEST_DONE."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = LaunchCommissioningPhase.INCLINING_TEST_DONE.value
    cs.completionPct = 50
    return {"cell_state": cs.__dict__, "next_node": "dock_trial_done"}
def transition_to_dock_trial_done(state: dict[str, Any]) -> dict[str, Any]:
    """INCLINING_TEST_DONE -> DOCK_TRIAL_DONE."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = LaunchCommissioningPhase.DOCK_TRIAL_DONE.value
    cs.completionPct = 75
    return {"cell_state": cs.__dict__, "next_node": "record_emitted"}
def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    """DOCK_TRIAL_DONE -> RECORD_EMITTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = LaunchCommissioningPhase.RECORD_EMITTED.value
    cs.completionPct = 100
    return {"cell_state": cs.__dict__, "next_node": "end"}
