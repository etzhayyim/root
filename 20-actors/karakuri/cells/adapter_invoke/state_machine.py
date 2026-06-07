"""Phase state machine for the karakuri adapter_invoke (絡繰) cell.

The cell drives one ServiceOp through the safest adapter, in a dry-run at R0. It wires the offline
planner (methods/command.py) and the browser-use T2 plan builder (methods/t2_browser.py) into the
manifest state graph:

    tos-gate  ->  mutate-gate  ->  dry-run  ->  execute-gated

Invariants enforced here as pure, unit-tested transitions (the cell's .solve() raises until Council
activation):
  G2 — official-API-first / ToS-honest: a browser-automation-prohibited service (incl. Google +
       Facebook, which are :api-ok but browser-prohibited and resolve to T1) refuses the T2 browser-use
       adapter; the op terminates as :refused without a plan or execution.
  G5 — read-default / mutate-gated: :read ops are read-allowed; any mutating op is marked
       awaiting-member-sig (the dry-run plan is still built; only EXECUTION needs the signature).
  G6 — outward-gated: at R0 the execute-gate ALWAYS reports gated — no live network call. Live
       execution is Council Lv6+ + operator gated.
  G8 — sourcing-honesty: an unknown service degrades to :unknown-service, never a guess.

The T2 path embeds the browser-use action plan, in which detection-evasion is structurally
unrepresentable (t2_browser.BROWSER_ACTIONS has no evasion verb; G2 / N2).
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# The planner + browser-use plan builder live in ../../methods.
_METHODS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "methods"))
if _METHODS not in sys.path:
    sys.path.insert(0, _METHODS)

from command import (  # noqa: E402  (path set above)
    SAFETY_READ,
    TIER_T2,
    TOS_REFUSED,
    ServiceOp,
    plan,
)
from t2_browser import build_browser_plan  # noqa: E402


class AdapterPhase(Enum):
    INIT = "init"
    TOS_CHECKED = "tos_checked"
    MUTATE_CHECKED = "mutate_checked"
    PLANNED = "planned"
    EXECUTE_GATED = "execute_gated"
    REFUSED = "refused"


# Adapter outcomes recorded on the payload.
OUTCOME_REFUSED_TOS = "refused-automation-prohibited"   # G2
OUTCOME_UNKNOWN_SERVICE = "unknown-service"             # G8
EXECUTE_GATE = "gated-council-lv6-operator"             # G6


@dataclass
class AdapterState:
    phase: str = AdapterPhase.INIT.value
    line: str = ""
    prefer_tier: str = ""
    op: dict = field(default_factory=dict)
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> AdapterState:
    return AdapterState(**d.get("cell_state", {}))


def transition_tos_gate(state: dict[str, Any]) -> dict[str, Any]:
    """Build the ServiceOp and apply the ToS gate (G2 / G8); refuse browser automation up front."""
    cs = _state(state)
    cs.line = state.get("line", cs.line)
    cs.prefer_tier = state.get("prefer_tier", cs.prefer_tier) or ""

    op = plan(cs.line, prefer_tier=(cs.prefer_tier or None))
    cs.op = dict(op.__dict__)

    if not op.service_known:
        cs.phase = AdapterPhase.REFUSED.value
        cs.payload["adapterOutcome"] = OUTCOME_UNKNOWN_SERVICE   # G8 — no guess
        return {"cell_state": cs.__dict__, "next_node": "end"}

    if op.tos_gate == TOS_REFUSED:
        cs.phase = AdapterPhase.REFUSED.value
        cs.payload["adapterOutcome"] = OUTCOME_REFUSED_TOS       # G2 — browser automation refused
        cs.payload["note"] = op.note
        return {"cell_state": cs.__dict__, "next_node": "end"}

    cs.phase = AdapterPhase.TOS_CHECKED.value
    return {"cell_state": cs.__dict__, "next_node": "mutate_gate"}


def transition_mutate_gate(state: dict[str, Any]) -> dict[str, Any]:
    """G5: reads are read-allowed; mutating ops are marked awaiting-member-sig (plan still builds)."""
    cs = _state(state)
    safety = cs.op.get("safety")
    cs.payload["mutateGate"] = "read-allowed" if safety == SAFETY_READ else "awaiting-member-sig"
    cs.phase = AdapterPhase.MUTATE_CHECKED.value
    return {"cell_state": cs.__dict__, "next_node": "dry_run"}


def transition_dry_run(state: dict[str, Any]) -> dict[str, Any]:
    """Build the dry-run adapter plan; for a T2 op, embed the browser-use action plan (G6 dry-run)."""
    cs = _state(state)
    op = ServiceOp(**cs.op)
    plan_desc: dict[str, Any] = {"tier": op.adapter_tier, "dryRun": True}

    if op.adapter_tier == TIER_T2:
        bp = build_browser_plan(op)                 # browser-use steps; raises if not eligible
        plan_desc["engine"] = bp["engine"]          # "browser-use"
        plan_desc["runtime"] = bp["runtime"]        # langgraph->wasm
        plan_desc["detectionEvasion"] = bp["detection_evasion"]  # False — unrepresentable (G2/N2)
        plan_desc["steps"] = bp["steps"]

    cs.payload["plan"] = plan_desc
    cs.phase = AdapterPhase.PLANNED.value
    return {"cell_state": cs.__dict__, "next_node": "execute_gated"}


def transition_execute_gated(state: dict[str, Any]) -> dict[str, Any]:
    """G6: at R0 there is no live execution; the execute-gate always reports gated (operator+Council)."""
    cs = _state(state)
    cs.payload["executeGate"] = EXECUTE_GATE   # G6 — Council Lv6+ + operator
    cs.payload["executed"] = False             # R0 invariant: never executed
    cs.phase = AdapterPhase.EXECUTE_GATED.value
    return {"cell_state": cs.__dict__, "next_node": "end"}
