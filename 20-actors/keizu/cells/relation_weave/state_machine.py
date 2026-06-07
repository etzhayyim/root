"""Phase state machine for the 系図 (keizu) relation_weave cell.

Derives a committee's cross-organ count from its member seats' organs — aggregate, edge-primary
(G4). A finding describes ties/diversity, never a per-person score. Self-contained.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WeavePhase(Enum):
    INIT = "init"
    WOVEN = "woven"
    REFUSED = "refused"


@dataclass
class WeaveState:
    phase: str = WeavePhase.INIT.value
    nodes: dict = field(default_factory=dict)
    committees: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    refusal: str = ""


def _state(d: dict[str, Any]) -> WeaveState:
    return WeaveState(**d.get("cell_state", {}))


def transition_to_woven(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.nodes = state.get("nodes", cs.nodes)
    cs.committees = state.get("committees", cs.committees)
    if not cs.committees:
        cs.refusal = "no committees to weave"
        cs.phase = WeavePhase.REFUSED.value
        return {"cell_state": cs.__dict__}
    for c in cs.committees:
        organs = sorted({cs.nodes.get(m, {}).get("organ", "(unknown)") for m in c.get("members", [])})
        cs.findings.append({
            "committee": c.get("id"),
            "member_count": len(c.get("members", [])),
            "distinct_organs": len(organs),
            "organs": organs,
        })
    cs.phase = WeavePhase.WOVEN.value
    return {"cell_state": cs.__dict__}
