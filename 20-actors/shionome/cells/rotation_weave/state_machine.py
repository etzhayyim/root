"""Phase state machine for the 潮目 (shionome) rotation_weave cell.

Ranks bucket→bucket rotation pairs (capital-movement kinds) by magnitude. Aggregate, edge-
primary; no per-bucket score. Self-contained so the cell suite runs standalone.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

CAPITAL_MOVEMENT_KINDS = ("rotation", "fund-inflow", "fund-outflow", "fx-flow")


class WeavePhase(Enum):
    INIT = "init"
    WOVEN = "woven"


@dataclass
class WeaveState:
    phase: str = WeavePhase.INIT.value
    flows: list = field(default_factory=list)
    pairs: list = field(default_factory=list)


def _kw(v: Any) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()


def transition_to_woven(state: dict[str, Any]) -> dict[str, Any]:
    cs = WeaveState(**state.get("cell_state", {}))
    cs.flows = state.get("flows", cs.flows)
    pairs: dict[tuple, float] = {}
    for f in cs.flows:
        if _kw(f.get("kind")) not in CAPITAL_MOVEMENT_KINDS:
            continue
        src, tgt = f.get("source"), f.get("target")
        if src and tgt and src != "external" and tgt != "external" and src != tgt:
            pairs[(src, tgt)] = pairs.get((src, tgt), 0.0) + float(f.get("magnitude", 0.0))
    cs.pairs = sorted(([s, t, round(m, 4)] for (s, t), m in pairs.items()),
                      key=lambda x: (-x[2], x[0], x[1]))
    cs.phase = WeavePhase.WOVEN.value
    return {"cell_state": cs.__dict__}
