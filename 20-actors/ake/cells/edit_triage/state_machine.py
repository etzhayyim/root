"""Phase state machine for the 朱 (ake) triage cell — the G2/G6 advisory membrane.

Scores a screened proposal (risk + quality, the Wikipedia ORES analogue) and assigns a route,
reusing the single source of truth in methods/triage.py. G2 INVARIANT: the model SCORES and the
PURE FUNCTION `route_for` routes — neither ever emits an accept/reject decision (非裁定). G6:
any LLM refinement of the scores is Murakumo-only. REFUSED if the proposal fails a hard gate.
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# single source of truth for scoring/routing — reuse methods/triage.py
_METHODS = pathlib.Path(__file__).resolve().parents[2] / "methods"
if str(_METHODS) not in sys.path:
    sys.path.insert(0, str(_METHODS))
from triage import score_edit  # noqa: E402


class TriagePhase(Enum):
    INIT = "init"
    TRIAGED = "triaged"
    REFUSED = "refused"


@dataclass
class TriageState:
    phase: str = TriagePhase.INIT.value
    edit: dict = field(default_factory=dict)   # the :edit/* proposal
    risk: str = ""
    quality: float = 0.0
    route: str = ""
    by: str = "murakumo:gemma3:4b"
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> TriageState:
    return TriageState(**d.get("cell_state", {}))


def triage(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.edit = dict(state.get("edit", cs.edit))
    cs.by = state.get("by", cs.by)
    try:
        t = score_edit(cs.edit, by=cs.by)
    except ValueError as e:
        cs.refusal = str(e)
        cs.phase = TriagePhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    cs.risk = t[":triage/risk"]
    cs.quality = t[":triage/quality"]
    cs.route = t[":triage/route"]
    cs.payload = {
        "editId": t[":triage/edit"],
        "risk": cs.risk.lstrip(":"),
        "quality": cs.quality,
        "route": cs.route.lstrip(":"),
        "by": cs.by,
    }
    cs.refusal = ""
    cs.phase = TriagePhase.TRIAGED.value
    return {"cell_state": cs.__dict__}
