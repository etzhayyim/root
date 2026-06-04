"""Phase state machine for the todoke route_sequencing (順路) cell.

This cell turns an accepted deliveryJob into a safety-validated lastMileRoute. The route
math is the SAME algorithm as the Rust `todoke-route` crate, reached through
``methods.last_mile`` (one model, two runtimes — ADR-2606033600). The G7 safety envelope is
enforced here as a hard refusal: a plan that exceeds the sidewalk-speed cap, enters a
vehicular road (N2), or assumes SAE level > 4 (N2) raises rather than yields a route.

Transitions are pure and unit-tested; the cell's .solve() raises until Council activation.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Reach the actor's methods/ package (sibling of cells/) without a hard dependency on
# install layout — mirrors how sanae's methods are imported in-tree.
_ACTOR_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ACTOR_ROOT not in sys.path:
    sys.path.insert(0, _ACTOR_ROOT)

from methods.last_mile import (  # noqa: E402
    EnvelopeViolation,
    Stop,
    plan_last_mile,
)


class RoutePhase(Enum):
    INIT = "init"
    JOB_LOADED = "job_loaded"
    ENVELOPE_CHECKED = "envelope_checked"
    SEQUENCED = "sequenced"
    ROUTE_EMITTED = "route_emitted"


@dataclass
class RouteState:
    phase: str = RoutePhase.INIT.value
    job_id: str = "did:web:todoke.etzhayyim.com/job/demo-0001"
    sae_level: int = 4
    commanded_mps: float = 1.5
    stops: list = field(default_factory=list)  # list of dicts {id,x,y,zone}
    order: list = field(default_factory=list)
    length_m: float = 0.0
    envelope_ok: bool = False
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> RouteState:
    return RouteState(**d.get("cell_state", {}))


def transition_to_job_loaded(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.phase = RoutePhase.JOB_LOADED.value
    cs.job_id = state.get("job_id", cs.job_id)
    cs.stops = list(state.get("stops", []))
    cs.sae_level = int(state.get("sae_level", cs.sae_level))
    cs.commanded_mps = float(state.get("commanded_mps", cs.commanded_mps))
    return {"cell_state": cs.__dict__, "next_node": "check_envelope"}


def _to_stops(raw: list[dict]) -> list[Stop]:
    return [Stop(int(s["id"]), float(s["x"]), float(s["y"]), str(s["zone"]).lower()) for s in raw]


def transition_to_envelope_checked(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.phase = RoutePhase.ENVELOPE_CHECKED.value
    try:
        # G7 dry-run: re-using the same plan_last_mile envelope gate the emit step uses.
        plan_last_mile(_to_stops(cs.stops), cs.sae_level, cs.commanded_mps)
        cs.envelope_ok = True
        cs.refusal = ""
        nxt = "sequence"
    except EnvelopeViolation as e:
        cs.envelope_ok = False
        cs.refusal = str(e)
        nxt = "refused"
    return {"cell_state": cs.__dict__, "next_node": nxt}


def transition_to_sequenced(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    if not cs.envelope_ok:
        raise EnvelopeViolation(f"G7: cannot sequence a refused job ({cs.refusal})")
    cs.phase = RoutePhase.SEQUENCED.value
    order, length = plan_last_mile(_to_stops(cs.stops), cs.sae_level, cs.commanded_mps)
    cs.order = order
    cs.length_m = round(length, 3)
    return {"cell_state": cs.__dict__, "next_node": "emit_route"}


def transition_to_route_emitted(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.phase = RoutePhase.ROUTE_EMITTED.value
    cs.payload = {
        "last_mile_route": {
            "jobId": cs.job_id,
            "order": cs.order,
            "lengthM": cs.length_m,
            "saeLevel": cs.sae_level,
            "commandedMps": cs.commanded_mps,
            "envelopeOk": cs.envelope_ok,
            "saeWithinCeiling": cs.sae_level <= 4,  # N2 invariant surfaced on the record
        }
    }
    return {"cell_state": cs.__dict__, "next_node": "end"}
