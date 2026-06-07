"""Phase state machine for the 潮目 (shionome) flow_graph cell.

Indexes screened flows into per-bucket inflow/outflow totals (capital-movement kinds only).
Self-contained so the cell suite runs standalone.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

CAPITAL_MOVEMENT_KINDS = ("rotation", "fund-inflow", "fund-outflow", "fx-flow")


class GraphPhase(Enum):
    INIT = "init"
    INDEXED = "indexed"


@dataclass
class GraphState:
    phase: str = GraphPhase.INIT.value
    flows: list = field(default_factory=list)
    net: dict = field(default_factory=dict)


def _kw(v: Any) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()


def transition_to_indexed(state: dict[str, Any]) -> dict[str, Any]:
    cs = GraphState(**state.get("cell_state", {}))
    cs.flows = state.get("flows", cs.flows)
    net: dict[str, float] = {}
    for f in cs.flows:
        if _kw(f.get("kind")) not in CAPITAL_MOVEMENT_KINDS:
            continue
        mag = float(f.get("magnitude", 0.0))
        tgt, src = f.get("target"), f.get("source")
        if tgt and tgt != "external":
            net[tgt] = net.get(tgt, 0.0) + mag
        if src and src != "external":
            net[src] = net.get(src, 0.0) - mag
    cs.net = {k: round(v, 4) for k, v in net.items()}
    cs.phase = GraphPhase.INDEXED.value
    return {"cell_state": cs.__dict__}
