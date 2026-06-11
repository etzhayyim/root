"""Phase state machine for the tedai intent_plan (手代) cell.

Graph: parse-brief -> prohibition-scan -> emit-plan. Turns a member brief (at R0: a list of literal
`tedai …` command lines; the NL → command leg is the Murakumo planner at R1, G4) into gated
DesktopOps. The prohibition scan refuses a brief that asks for surveillance or detection-evasion in
intent (G8/G2/N1/N2) BEFORE any op is planned — the verb sets in t2_vision.py make those
unrepresentable at the step level; this scan refuses them at the intent level.

G2/G8 (prohibition scan) · G5 (each op carries its mutate gate) · G6 (dry-run plans only).
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

from desktop import plan as plan_op  # noqa: E402

# Intent-level prohibition markers (G8 surveillance / G2 evasion / N1 / N2). A brief whose text
# carries one of these is refused before planning; the per-step vocabularies in t2_vision.py are
# the structural backstop.
PROHIBITED_INTENTS: tuple[str, ...] = (
    "keylog", "keylogger", "spy", "surveil", "monitor my employee", "watch my kid",
    "track my partner", "record their screen", "their camera", "their microphone",
    "bypass anti-cheat", "bypass anticheat", "bypass drm", "evade detection",
    "without them knowing", "someone else's computer",
)

OUTCOME_PROHIBITED = "refused-prohibited-intent"


class PlanPhase(Enum):
    INIT = "init"
    PARSED = "parsed"
    SCANNED = "scanned"
    PLANNED = "planned"
    REFUSED = "refused"


@dataclass
class PlanState:
    phase: str = PlanPhase.INIT.value
    brief: str = ""
    command_lines: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> PlanState:
    return PlanState(**d.get("cell_state", {}))


def transition_parse_brief(state: dict[str, Any]) -> dict[str, Any]:
    """Collect the brief text + literal command lines (R0; NL→command is the R1 Murakumo leg, G4)."""
    cs = _state(state)
    cs.brief = state.get("brief", cs.brief)
    cs.command_lines = list(state.get("command_lines", cs.command_lines))
    if not cs.command_lines:
        raise ValueError("intent_plan: no command lines supplied (R0 takes literal `tedai …` lines)")
    cs.phase = PlanPhase.PARSED.value
    return {"cell_state": cs.__dict__, "next_node": "prohibition_scan"}


def transition_prohibition_scan(state: dict[str, Any]) -> dict[str, Any]:
    """G8/G2: refuse a brief that asks for surveillance or detection-evasion in intent."""
    cs = _state(state)
    text = " ".join([cs.brief, *cs.command_lines]).lower()
    hits = [marker for marker in PROHIBITED_INTENTS if marker in text]
    if hits:
        cs.phase = PlanPhase.REFUSED.value
        cs.payload["outcome"] = OUTCOME_PROHIBITED
        cs.payload["markers"] = hits
        return {"cell_state": cs.__dict__, "next_node": "end"}
    cs.phase = PlanPhase.SCANNED.value
    return {"cell_state": cs.__dict__, "next_node": "emit_plan"}


def transition_emit_plan(state: dict[str, Any]) -> dict[str, Any]:
    """G5/G6: plan each command line into a gated, dry-run DesktopOp."""
    cs = _state(state)
    if cs.phase != PlanPhase.SCANNED.value:
        raise ValueError("intent_plan: emit_plan reached without a clean prohibition scan")
    ops = [plan_op(line) for line in cs.command_lines]
    cs.payload["ops"] = [op.__dict__ for op in ops]
    cs.payload["dryRun"] = True                     # G6 invariant
    cs.payload["mutatingCount"] = sum(1 for op in ops if op.safety != "read")
    cs.phase = PlanPhase.PLANNED.value
    return {"cell_state": cs.__dict__, "next_node": "end"}
