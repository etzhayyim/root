"""Phase state machine for the tedai actuate_invoke (手代) cell.

Graph: plan-op -> stance-gate -> mutate-gate -> build-adapter-plan -> dry-run-emit. Wires
methods/desktop.py + methods/t2_vision.py into the gated invocation path: a T2 op gets a vision
plan only when its stance gate is clean (G2); every op stops at a dry-run emission (G6); live
actuation funnels exclusively through methods/actuate_live.py (which refuses at R0).

G2 (stance gate) · G5 (mutate/outward gate carried) · G6 (dry-run only) · G8 (honest degradation).
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
    STANCE_OK,
    TIER_T2,
    plan as plan_op,
)
from t2_vision import T2NotEligible, build_vision_plan  # noqa: E402

OUTCOME_STANCE_REFUSED = "refused-stance"        # G2
OUTCOME_NOT_INVOKABLE = "not-invokable"          # G8 (unknown app / karakuri route)


class InvokePhase(Enum):
    INIT = "init"
    PLANNED = "planned"
    STANCE_OK = "stance_ok"
    GATED = "gated"
    EMITTED = "emitted"
    REFUSED = "refused"


@dataclass
class InvokeState:
    phase: str = InvokePhase.INIT.value
    line: str = ""
    op: dict = field(default_factory=dict)
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> InvokeState:
    return InvokeState(**d.get("cell_state", {}))


def transition_plan_op(state: dict[str, Any]) -> dict[str, Any]:
    """Parse + plan the command line into a DesktopOp; refuse non-invokable shapes honestly (G8)."""
    cs = _state(state)
    cs.line = state.get("line", cs.line)
    op = plan_op(cs.line)
    cs.op = op.__dict__
    if not op.app_known or op.route:
        cs.phase = InvokePhase.REFUSED.value
        cs.payload["outcome"] = OUTCOME_NOT_INVOKABLE
        cs.payload["note"] = op.note
        return {"cell_state": cs.__dict__, "next_node": "end"}
    cs.phase = InvokePhase.PLANNED.value
    return {"cell_state": cs.__dict__, "next_node": "stance_gate"}


def transition_stance_gate(state: dict[str, Any]) -> dict[str, Any]:
    """G2: a refused stance gate ends the invocation — there is no override parameter."""
    cs = _state(state)
    if cs.op.get("stance_gate") != STANCE_OK:
        cs.phase = InvokePhase.REFUSED.value
        cs.payload["outcome"] = OUTCOME_STANCE_REFUSED
        cs.payload["note"] = cs.op.get("note", "")
        return {"cell_state": cs.__dict__, "next_node": "end"}
    cs.phase = InvokePhase.STANCE_OK.value
    return {"cell_state": cs.__dict__, "next_node": "mutate_gate"}


def transition_mutate_gate(state: dict[str, Any]) -> dict[str, Any]:
    """G5: carry the mutate/outward gate forward; the plan itself never satisfies it."""
    cs = _state(state)
    cs.payload["mutateGate"] = cs.op.get("mutate_gate")
    cs.payload["destructive"] = cs.op.get("destructive", False)
    cs.phase = InvokePhase.GATED.value
    return {"cell_state": cs.__dict__, "next_node": "build_adapter_plan"}


def transition_build_adapter_plan(state: dict[str, Any]) -> dict[str, Any]:
    """Build the tier's dry-run adapter plan: T2 → t2_vision; T1/T3 → declarative stub (R1 drivers)."""
    cs = _state(state)
    from desktop import DesktopOp  # local to keep dataclass reconstruction near use

    op = DesktopOp(**cs.op)
    if op.adapter_tier == TIER_T2:
        try:
            cs.payload["adapterPlan"] = build_vision_plan(op)
        except T2NotEligible as e:  # defence in depth — stance gate should have caught it
            cs.phase = InvokePhase.REFUSED.value
            cs.payload["outcome"] = OUTCOME_STANCE_REFUSED
            cs.payload["note"] = str(e)
            return {"cell_state": cs.__dict__, "next_node": "end"}
    else:
        cs.payload["adapterPlan"] = {
            "tier": op.adapter_tier,
            "dry_run": True,                        # G6
            "note": "T1/T3 driver layer is R1+ (OS accessibility permissions / file adapters)",
        }
    cs.phase = InvokePhase.EMITTED.value
    cs.payload["dryRun"] = True                     # G6 invariant — actuation only via actuate_live
    return {"cell_state": cs.__dict__, "next_node": "end"}
