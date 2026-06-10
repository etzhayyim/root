"""Phase state machine for the tedai app_resolve (手代) cell.

Graph: lookup -> tier-select -> stance. Resolves an app against the :representative registry
(methods/desktop.py), selects the safest adapter tier, and reports the synthetic-input stance.
G2 (tier choice respects the stance), G6 (no actuation), G8 (unknown app degrades honestly),
N7 (browser apps route to karakuri).
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_METHODS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "methods"))
if _METHODS not in sys.path:
    sys.path.insert(0, _METHODS)

from desktop import (  # noqa: E402
    T2_ENGINE,
    TIER_T2,
    resolve_app,
    select_tier,
    t2_stance,
)

OUTCOME_UNKNOWN_APP = "unknown-app"          # G8
OUTCOME_ROUTE_KARAKURI = "route-to-karakuri"  # N7


class ResolvePhase(Enum):
    INIT = "init"
    LOOKED_UP = "looked_up"
    TIER_SELECTED = "tier_selected"
    RESOLVED = "resolved"
    REFUSED = "refused"
    ROUTED = "routed"


@dataclass
class ResolveState:
    phase: str = ResolvePhase.INIT.value
    app: str = ""
    rec: dict = field(default_factory=dict)
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> ResolveState:
    return ResolveState(**d.get("cell_state", {}))


def transition_lookup(state: dict[str, Any]) -> dict[str, Any]:
    """G8/N7: resolve the app; unknown degrades honestly, browser apps route to karakuri."""
    cs = _state(state)
    cs.app = state.get("app", cs.app)
    rec = resolve_app(cs.app)
    if rec is None:
        cs.phase = ResolvePhase.REFUSED.value
        cs.payload["outcome"] = OUTCOME_UNKNOWN_APP
        return {"cell_state": cs.__dict__, "next_node": "end"}
    if rec.get("route") == "karakuri":
        cs.phase = ResolvePhase.ROUTED.value
        cs.payload["outcome"] = OUTCOME_ROUTE_KARAKURI
        cs.payload["route"] = "karakuri"
        return {"cell_state": cs.__dict__, "next_node": "end"}
    cs.rec = dict(rec)
    cs.phase = ResolvePhase.LOOKED_UP.value
    return {"cell_state": cs.__dict__, "next_node": "tier_select"}


def transition_tier_select(state: dict[str, Any]) -> dict[str, Any]:
    """G2: pick the safest adapter tier (scripting API > permitted vision-pointer > file-level)."""
    cs = _state(state)
    cs.payload["tier"] = select_tier(cs.rec)
    cs.phase = ResolvePhase.TIER_SELECTED.value
    return {"cell_state": cs.__dict__, "next_node": "stance"}


def transition_stance(state: dict[str, Any]) -> dict[str, Any]:
    """Report the T1 surface + synthetic-input stance and the on-device engine if T2 is permitted."""
    cs = _state(state)
    cs.payload["t1Surface"] = cs.rec.get("t1_surface", "")
    cs.payload["t2Stance"] = t2_stance(cs.rec)             # synthetic-input axis (G2)
    if cs.payload["tier"] == TIER_T2 and t2_stance(cs.rec) in ("permitted", "restricted"):
        cs.payload["t2Engine"] = T2_ENGINE                 # on-device vision (G4)
    cs.phase = ResolvePhase.RESOLVED.value
    return {"cell_state": cs.__dict__, "next_node": "end"}
