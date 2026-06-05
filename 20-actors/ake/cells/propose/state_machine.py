"""Phase state machine for the 朱 (ake) propose cell — the G1/G3/G4 intake membrane.

A member-signed correction enters here. It is SCREENED (rejected outright) unless:
  G1 — author-kind is 'member' and server-held-key is false (no-server-key + 信者-gated);
  G3 — target-kind ∈ {kg-fact, actor-profile} (impersonation unrepresentable);
  G4 — provenance (URL/CID) is present (an unsourced proposal never enters the log).
A SCREENED proposal is then RECORDED as an append-only :edit/* datom. REFUSAL gate, not a clamp.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_TARGET_KINDS = ("kg-fact", "actor-profile")


class ProposePhase(Enum):
    INIT = "init"
    SCREENED = "screened"
    RECORDED = "recorded"
    REFUSED = "refused"


@dataclass
class ProposeState:
    phase: str = ProposePhase.INIT.value
    edit_id: str = ""
    target_kind: str = ""
    target_entity: str = ""
    target_attr: str = ""
    op: str = "assert"
    author: str = ""
    author_kind: str = ""
    provenance: str = ""
    server_held_key: bool = False
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> ProposeState:
    return ProposeState(**d.get("cell_state", {}))


def _kw(v: Any) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()


def transition_to_screened(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.edit_id = state.get("edit_id", cs.edit_id)
    cs.target_kind = _kw(state.get("target_kind", cs.target_kind))
    cs.target_entity = state.get("target_entity", cs.target_entity)
    cs.target_attr = _kw(state.get("target_attr", cs.target_attr))
    cs.op = _kw(state.get("op", cs.op))
    cs.author = state.get("author", cs.author)
    cs.author_kind = _kw(state.get("author_kind", cs.author_kind))
    cs.provenance = state.get("provenance", cs.provenance) or ""
    cs.server_held_key = bool(state.get("server_held_key", cs.server_held_key))

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal = msg
        cs.phase = ProposePhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    if cs.target_kind not in _TARGET_KINDS:
        return refuse(f"G3: target-kind {cs.target_kind!r} unrepresentable (no impersonation)")
    if cs.author_kind != "member":
        return refuse("G1: author-kind must be 'member' (no-server-key + 信者-gated)")
    if cs.server_held_key:
        return refuse("G1/no-server-key: server-held-key must be false (ADR-2605231525)")
    if not cs.provenance.strip():
        return refuse("G4: an unsourced proposal is refused — provenance is mandatory")

    cs.refusal = ""
    cs.phase = ProposePhase.SCREENED.value
    return {"cell_state": cs.__dict__}


def transition_to_recorded(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    if cs.phase != ProposePhase.SCREENED.value:
        cs.refusal = "cannot record a proposal that was not screened clean"
        cs.phase = ProposePhase.REFUSED.value
        return {"cell_state": cs.__dict__}
    cs.payload = {
        "editId": cs.edit_id,
        "targetKind": cs.target_kind,
        "targetEntity": cs.target_entity,
        "targetAttr": cs.target_attr,
        "op": cs.op,
        "author": cs.author,
        "authorKind": "member",
        "serverHeldKey": False,
        "provenance": cs.provenance,
    }
    cs.phase = ProposePhase.RECORDED.value
    return {"cell_state": cs.__dict__}
