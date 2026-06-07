"""Phase state machine for the karakuri service_resolve (絡繰) cell.

Graph: lookup -> tier-select -> tos-stance. Resolves a service against the :representative registry
(methods/command.py), selects the safest adapter tier, and reports both stance axes. G2 (tier choice
respects the browser-automation stance), G6 (no network), G8 (unknown service degrades honestly).
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

from command import (  # noqa: E402
    T2_ENGINE,
    TIER_T2,
    resolve_service,
    select_tier,
    t2_stance,
)

OUTCOME_UNKNOWN_SERVICE = "unknown-service"   # G8


class ResolvePhase(Enum):
    INIT = "init"
    LOOKED_UP = "looked_up"
    TIER_SELECTED = "tier_selected"
    RESOLVED = "resolved"
    REFUSED = "refused"


@dataclass
class ResolveState:
    phase: str = ResolvePhase.INIT.value
    service: str = ""
    rec: dict = field(default_factory=dict)
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> ResolveState:
    return ResolveState(**d.get("cell_state", {}))


def transition_lookup(state: dict[str, Any]) -> dict[str, Any]:
    """G8: resolve the service; an unknown service degrades honestly with no guess."""
    cs = _state(state)
    cs.service = state.get("service", cs.service)
    rec = resolve_service(cs.service)
    if rec is None:
        cs.phase = ResolvePhase.REFUSED.value
        cs.payload["outcome"] = OUTCOME_UNKNOWN_SERVICE
        return {"cell_state": cs.__dict__, "next_node": "end"}
    cs.rec = dict(rec)
    cs.phase = ResolvePhase.LOOKED_UP.value
    return {"cell_state": cs.__dict__, "next_node": "tier_select"}


def transition_tier_select(state: dict[str, Any]) -> dict[str, Any]:
    """G2: pick the safest adapter tier (official API > permitted browser-use > export)."""
    cs = _state(state)
    cs.payload["tier"] = select_tier(cs.rec)
    cs.phase = ResolvePhase.TIER_SELECTED.value
    return {"cell_state": cs.__dict__, "next_node": "tos_stance"}


def transition_tos_stance(state: dict[str, Any]) -> dict[str, Any]:
    """Report both stance axes (official-API + browser-automation) and the T2 engine if permitted."""
    cs = _state(state)
    cs.payload["officialApi"] = bool(cs.rec.get("official_api"))
    cs.payload["tosStance"] = cs.rec.get("tos")           # official-API axis
    cs.payload["t2Stance"] = t2_stance(cs.rec)             # browser-automation axis (G2)
    if cs.payload["tier"] == TIER_T2 and t2_stance(cs.rec) in ("permitted", "restricted"):
        cs.payload["t2Engine"] = T2_ENGINE                 # browser-use
    cs.phase = ResolvePhase.RESOLVED.value
    return {"cell_state": cs.__dict__, "next_node": "end"}
