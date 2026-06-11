"""weld_ndt_inspection state machine — ADR-2606013400 (L3 100% RT/UT/PT hull-seam NDT).

R0 scaffold: phase transitions are structural placeholders. The cell's .solve()
raises RuntimeError until Council Lv6+ ratifies the R1 activation ADR-2606013415.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WeldNdtInspectionPhase(Enum):
    INIT = "init"
    SEAMS_REGISTERED = "seams_registered"
    RT_UT_PT_RUN = "rt_ut_pt_run"
    DEFECTS_DISPOSITIONED = "defects_dispositioned"
    RECORD_EMITTED = "record_emitted"


@dataclass
class CellState:
    phase: str = WeldNdtInspectionPhase.INIT.value
    vesselId: str = "NAGI-COASTAL-0001"
    vesselClass: str = "Nagi 凪"
    completionPct: int = 0
    robotSignatures: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)

def transition_to_seams_registered(state: dict[str, Any]) -> dict[str, Any]:
    """INIT -> SEAMS_REGISTERED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = WeldNdtInspectionPhase.SEAMS_REGISTERED.value
    cs.completionPct = 25
    return {"cell_state": cs.__dict__, "next_node": "rt_ut_pt_run"}
def transition_to_rt_ut_pt_run(state: dict[str, Any]) -> dict[str, Any]:
    """SEAMS_REGISTERED -> RT_UT_PT_RUN."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = WeldNdtInspectionPhase.RT_UT_PT_RUN.value
    cs.completionPct = 50
    return {"cell_state": cs.__dict__, "next_node": "defects_dispositioned"}
def transition_to_defects_dispositioned(state: dict[str, Any]) -> dict[str, Any]:
    """RT_UT_PT_RUN -> DEFECTS_DISPOSITIONED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = WeldNdtInspectionPhase.DEFECTS_DISPOSITIONED.value
    cs.completionPct = 75
    return {"cell_state": cs.__dict__, "next_node": "record_emitted"}
def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    """DEFECTS_DISPOSITIONED -> RECORD_EMITTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = WeldNdtInspectionPhase.RECORD_EMITTED.value
    cs.completionPct = 100
    return {"cell_state": cs.__dict__, "next_node": "end"}
