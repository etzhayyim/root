"""Phase state machine for kawaraban outlet_ingest — G4/G5 membrane.

An outlet is INGESTED only if its access is a PUBLIC facing page
(:open / :registration-wall). :paywall / :proprietary-terminal are REFUSED — only the
public page is mirrored, never a paid terminal (G4; kanjo §2(c) anti-gatekeeping). Refusal,
never coercion.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any

OPEN_ACCESS = ("open", "registration-wall")
OUTLET_KINDS = ("public-broadcaster", "wire-agency", "newspaper", "magazine", "digital-native", "ngo-press")


class Phase(Enum):
    INIT = "init"
    INGESTED = "ingested"
    REFUSED = "refused"


@dataclass
class State:
    phase: str = Phase.INIT.value
    outlet_id: str = ""
    name: str = ""
    kind: str = "wire-agency"
    access: str = "open"
    refusal: str = ""
    payload: dict = None


def _norm(v: str | None) -> str:
    return (v or "").lstrip(":")


def ingest(state: dict[str, Any]) -> dict[str, Any]:
    cs = State(**state.get("cell_state", {}))
    cs.outlet_id = state.get("outlet_id", cs.outlet_id)
    cs.name = state.get("name", cs.name)
    cs.kind = _norm(state.get("kind", cs.kind))
    cs.access = _norm(state.get("access", cs.access))

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal, cs.phase = msg, Phase.REFUSED.value
        return {"cell_state": cs.__dict__}

    if not cs.outlet_id or not cs.name:
        return refuse("outlet needs id + name (G5 provenance)")
    if cs.access not in OPEN_ACCESS:
        return refuse(f"G4: access {cs.access!r} is not a public facing page; paywall/terminal not mirrored")
    if cs.kind not in OUTLET_KINDS:
        return refuse(f"unknown outlet kind {cs.kind!r}")

    cs.payload = {"outletId": cs.outlet_id, "name": cs.name, "kind": cs.kind,
                  "access": cs.access, "sourcing": "representative"}
    cs.refusal, cs.phase = "", Phase.INGESTED.value
    return {"cell_state": cs.__dict__}
