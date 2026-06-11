"""Phase state machine for the kamado decommission_plan (竈) cell.

§2(d)-permitted robotics on an EXISTING fossil refinery: shut down, purge, clean,
dismantle, remediate, or convert — NEVER expand/restart/extend a fossil unit. The
intervention guard is the G3 enforcement point; G5 keeps the actuation member/operator-
signed (no server key); G8 keeps anything outward gated.

Invariants enforced:
  G3 — intervention ∈ {decommission, remediate, convert, monitor}. :expand / :restart-fossil
       raise ValueError (life-extension of a fossil asset is not representable).
  G5 — no-server-key: the plan authorizes nothing; actuation = operator/member signature.
  G8 — outward-gated: real teardown is Council Lv6+ + operator; R0 = dry-run plan only.
  G9 — labor-liberation: robots take the H2S/benzene/pyrophoric hot-zone entry; freed
       workers route to the tenure-weighted Basic-High-Income cohort (ADR-2606032130).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

ALLOWED_INTERVENTION = ("decommission", "remediate", "convert", "monitor")
ALLOWED_CONVERT = ("hikari-solar", "synthesis-plant", "materials-recovery",
                   "remediated-land", "none")
ALLOWED_PRINCIPAL = ("operator", "member")


class PlanPhase(Enum):
    INIT = "init"
    SCOPED = "scoped"
    PLANNED = "planned"
    GATED = "gated"


@dataclass
class PlanState:
    phase: str = PlanPhase.INIT.value
    refinery: str = ""
    intervention: str = "decommission"
    convert_to: str = "none"
    principal: str = "operator"
    server_held_key: bool = False
    outward_gated: bool = True
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> PlanState:
    return PlanState(**d.get("cell_state", {}))


def _norm(v) -> str:
    return (v or "").lstrip(":") if isinstance(v, str) else str(v)


def transition_to_scoped(state: dict[str, Any]) -> dict[str, Any]:
    """G3: scope the intervention. Raises on any fossil life-extension."""
    cs = _state(state)
    cs.refinery = state.get("refinery", cs.refinery)
    cs.intervention = _norm(state.get("intervention", cs.intervention))
    if cs.intervention not in ALLOWED_INTERVENTION:
        raise ValueError(
            f"G3 violation: intervention {cs.intervention!r} is not representable; only "
            f"{ALLOWED_INTERVENTION} permitted on an existing fossil asset (§2(d) — "
            f"decommission/transition only; never expand/restart/extend a fossil unit)."
        )
    cs.convert_to = _norm(state.get("convert_to", cs.convert_to))
    if cs.convert_to not in ALLOWED_CONVERT:
        raise ValueError(f"unknown convert-to target {cs.convert_to!r}")
    cs.server_held_key = bool(state.get("server_held_key", cs.server_held_key))
    cs.phase = PlanPhase.SCOPED.value
    return {"cell_state": cs.__dict__}


def transition_to_planned(state: dict[str, Any]) -> dict[str, Any]:
    """G5: build the dry-run plan. The server holds no key; actuation is signed externally."""
    cs = _state(state)
    if cs.phase != PlanPhase.SCOPED.value:
        raise ValueError("plan requires a scoped intervention first (G3)")
    cs.principal = _norm(state.get("principal", cs.principal))
    if cs.principal not in ALLOWED_PRINCIPAL:
        raise ValueError(f"principal {cs.principal!r} must be operator|member (G5)")
    if cs.server_held_key or state.get("server_held_key"):
        raise ValueError("G5 violation: serverHeldKey must be false (member/operator signs)")
    cs.server_held_key = False
    cs.payload = {
        "refinery": cs.refinery, "intervention": cs.intervention,
        "convertTo": cs.convert_to, "principal": cs.principal, "serverHeldKey": False,
    }
    cs.phase = PlanPhase.PLANNED.value
    return {"cell_state": cs.__dict__}


def transition_to_gated(state: dict[str, Any]) -> dict[str, Any]:
    """G8: real teardown stays gated. R0 emits an intent, never an actuation."""
    cs = _state(state)
    if cs.phase != PlanPhase.PLANNED.value:
        raise ValueError("gate requires a planned intervention first")
    cs.outward_gated = True
    cs.payload["outwardGated"] = True
    cs.payload["status"] = "intent-only"   # G8: Council Lv6+ + operator before any actuation
    cs.phase = PlanPhase.GATED.value
    return {"cell_state": cs.__dict__}
