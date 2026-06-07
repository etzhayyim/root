"""Phase state machine for the karakuri command_plan (絡繰) cell.

Graph: parse -> classify -> charter-scan -> plan. Wires the Murakumo-only NL planner
(methods/nl_plan.py) and the ServiceOp gates (methods/command.py) into the manifest graph:

  parse        — NL brief -> a `<service> <noun>.<verb>` command (deterministic heuristic at R0;
                 the live Murakumo path is operator-gated, G4).
  classify     — command -> a gated ServiceOp (safety + ToS + mutate gates; G2/G5).
  charter-scan — Charter-Rider §2(a)-(h) scan of the brief + op (N6); a dirty brief plans nothing.
  plan         — assemble the dry-run CommandPlan (G6).
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

from command import plan as plan_op  # noqa: E402
from nl_plan import INFERENCE_MURAKUMO, charter_scan, heuristic_parse  # noqa: E402


class PlanPhase(Enum):
    INIT = "init"
    PARSED = "parsed"
    CLASSIFIED = "classified"
    SCANNED = "scanned"
    PLANNED = "planned"
    REFUSED = "refused"


@dataclass
class PlanState:
    phase: str = PlanPhase.INIT.value
    brief: str = ""
    command_line: str = ""
    op: dict = field(default_factory=dict)
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> PlanState:
    return PlanState(**d.get("cell_state", {}))


def transition_parse(state: dict[str, Any]) -> dict[str, Any]:
    """G4: NL brief -> command (deterministic fallback; live Murakumo path operator-gated elsewhere)."""
    cs = _state(state)
    cs.brief = state.get("brief", cs.brief)
    cmd = heuristic_parse(cs.brief)
    if not cmd:
        cs.phase = PlanPhase.REFUSED.value
        cs.payload["outcome"] = "no-confident-parse"   # G8 — never guesses a service
        return {"cell_state": cs.__dict__, "next_node": "end"}
    cs.command_line = cmd
    cs.phase = PlanPhase.PARSED.value
    return {"cell_state": cs.__dict__, "next_node": "classify"}


def transition_classify(state: dict[str, Any]) -> dict[str, Any]:
    """G2/G5: turn the command into a gated ServiceOp (safety + ToS + mutate gates applied)."""
    cs = _state(state)
    cs.op = dict(plan_op(cs.command_line).__dict__)
    cs.phase = PlanPhase.CLASSIFIED.value
    return {"cell_state": cs.__dict__, "next_node": "charter_scan"}


def transition_charter_scan(state: dict[str, Any]) -> dict[str, Any]:
    """N6: scan the brief + resolved op; a dirty brief plans nothing."""
    cs = _state(state)
    op = cs.op
    clean, hits = charter_scan(f"{cs.brief} {op.get('service')} {op.get('noun')} {op.get('verb')}")
    cs.payload["charterClean"] = clean
    cs.payload["charterHits"] = hits
    cs.phase = PlanPhase.SCANNED.value
    return {"cell_state": cs.__dict__, "next_node": "plan"}


def transition_plan(state: dict[str, Any]) -> dict[str, Any]:
    """G6: assemble the dry-run CommandPlan; a charter-dirty brief yields an empty op list (N6)."""
    cs = _state(state)
    ops = [cs.op] if cs.payload.get("charterClean") else []
    cs.payload["brief"] = cs.brief
    cs.payload["ops"] = ops
    cs.payload["inference"] = INFERENCE_MURAKUMO    # G4
    cs.payload["dryRun"] = True                      # G6
    cs.payload["mutateGate"] = cs.op.get("mutate_gate") if ops else None
    cs.phase = PlanPhase.PLANNED.value
    return {"cell_state": cs.__dict__, "next_node": "end"}
