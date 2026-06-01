"""grand_block_assembly state machine — ADR-2606013400 (L2 grand-block erection + joining on building dock).

R0 scaffold: phase transitions are structural placeholders. The cell's .solve()
raises RuntimeError until Council Lv6+ ratifies the R1 activation ADR-2606013415.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GrandBlockAssemblyPhase(Enum):
    INIT = "init"
    BLOCKS_STAGED = "blocks_staged"
    ALIGNED_ON_DOCK = "aligned_on_dock"
    BLOCK_JOINS_WELDED = "block_joins_welded"
    HULL_GIRDER_QA = "hull_girder_qa"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class CellState:
    phase: str = GrandBlockAssemblyPhase.INIT.value
    vesselId: str = "NAGI-COASTAL-0001"
    vesselClass: str = "Nagi 凪"
    completionPct: int = 0
    robotSignatures: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)

def transition_to_blocks_staged(state: dict[str, Any]) -> dict[str, Any]:
    """INIT -> BLOCKS_STAGED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = GrandBlockAssemblyPhase.BLOCKS_STAGED.value
    cs.completionPct = 20
    return {"cell_state": cs.__dict__, "next_node": "aligned_on_dock"}
def transition_to_aligned_on_dock(state: dict[str, Any]) -> dict[str, Any]:
    """BLOCKS_STAGED -> ALIGNED_ON_DOCK."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = GrandBlockAssemblyPhase.ALIGNED_ON_DOCK.value
    cs.completionPct = 40
    return {"cell_state": cs.__dict__, "next_node": "block_joins_welded"}
def transition_to_block_joins_welded(state: dict[str, Any]) -> dict[str, Any]:
    """ALIGNED_ON_DOCK -> BLOCK_JOINS_WELDED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = GrandBlockAssemblyPhase.BLOCK_JOINS_WELDED.value
    cs.completionPct = 60
    return {"cell_state": cs.__dict__, "next_node": "hull_girder_qa"}
def transition_to_hull_girder_qa(state: dict[str, Any]) -> dict[str, Any]:
    """BLOCK_JOINS_WELDED -> HULL_GIRDER_QA."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = GrandBlockAssemblyPhase.HULL_GIRDER_QA.value
    cs.completionPct = 80
    return {"cell_state": cs.__dict__, "next_node": "attestation_emitted"}
def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    """HULL_GIRDER_QA -> ATTESTATION_EMITTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = GrandBlockAssemblyPhase.ATTESTATION_EMITTED.value
    cs.completionPct = 100
    return {"cell_state": cs.__dict__, "next_node": "end"}
