"""Phase state machine for the 朱 (ake) promote cell — the G8/G9 no-server-key membrane.

An accepted edit is CLEARED for promotion (append the revision; optionally
:representative→:authoritative) ONLY if:
  the review outcome was 'accepted' (not pending/rejected);
  G9 — the promotion is member/operator-signed (a server signature is REFUSED, no-server-key);
  G4 — a sourcing promotion to :authoritative carries verifiable provenance;
  G8 — published stays false (live publish into the served registry is Council Lv6+ + operator).
REFUSAL gate (like mitooshi calibration_gate / noroshi precursor_safety), not an auto-promoter.
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_METHODS = pathlib.Path(__file__).resolve().parents[2] / "methods"
if str(_METHODS) not in sys.path:
    sys.path.insert(0, str(_METHODS))
from triage import _verifiable_provenance  # noqa: E402


class PromotePhase(Enum):
    INIT = "init"
    CLEARED = "cleared"
    REFUSED = "refused"


@dataclass
class PromoteState:
    phase: str = PromotePhase.INIT.value
    edit_id: str = ""
    entity: str = ""
    attr: str = ""
    value: str = ""
    outcome: str = "pending"
    to_sourcing: str = "representative"
    provenance: str = ""
    signed_by: str = ""
    as_of: int = 0
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> PromoteState:
    return PromoteState(**d.get("cell_state", {}))


def review_promotion(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.edit_id = state.get("edit_id", cs.edit_id)
    cs.entity = state.get("entity", cs.entity)
    cs.attr = str(state.get("attr", cs.attr)).lstrip(":")
    cs.value = state.get("value", cs.value)
    cs.outcome = str(state.get("outcome", cs.outcome)).lstrip(":")
    cs.to_sourcing = str(state.get("to_sourcing", cs.to_sourcing)).lstrip(":")
    cs.provenance = state.get("provenance", cs.provenance) or ""
    cs.signed_by = state.get("signed_by", cs.signed_by) or ""
    cs.as_of = int(state.get("as_of", cs.as_of))

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal = msg
        cs.phase = PromotePhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    if cs.outcome != "accepted":
        return refuse(f"outcome {cs.outcome!r} is not 'accepted'; nothing to promote")
    if not cs.signed_by or cs.signed_by.lower().startswith("server"):
        return refuse("G9: promotion needs a member/operator signature; server signature refused")
    if cs.to_sourcing == "authoritative" and not _verifiable_provenance(cs.provenance):
        return refuse("G4: promotion to :authoritative requires verifiable provenance (URL/CID)")

    cs.payload = {
        "editId": cs.edit_id, "entity": cs.entity, "attr": cs.attr, "value": cs.value,
        "sourcing": cs.to_sourcing, "asOf": cs.as_of, "signedBy": cs.signed_by,
        "serverHeldKey": False,
        "promoted": True,
        "published": False,   # G8 — live publish is Council Lv6+ + operator
    }
    cs.refusal = ""
    cs.phase = PromotePhase.CLEARED.value
    return {"cell_state": cs.__dict__}
