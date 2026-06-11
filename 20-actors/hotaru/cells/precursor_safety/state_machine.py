"""Phase state machine for the hotaru precursor_safety (蛍) cell.

The G3/G4 safety membrane. A design clears safety review ONLY after:
  G4 — every conflict-mineral element it consumes (In/Ga) carries a clean :in-sourcing
       attestation ∈ {recycled, conflict-free-attested}; :unverified REFUSES review
       (inherits hikari/himawari §G2 — In/Ga barred from panel sourcing).
  G3 — every hazardous precursor (PH3 acute-toxic-pyrophoric, red-P flammable) is
       acknowledged; an unacknowledged acute-toxic precursor REFUSES review.
  export-control posture (none/ear/itar) is recorded for the jurisdictional-risk
       attestation ADR-2605265500 §2 requires.

This is a REFUSAL gate (like todoke's safety envelope): it does not clamp — it refuses
to clear a design that violates G3/G4.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

CLEAN_SOURCING = ("recycled", "conflict-free-attested")
ACUTE_HAZARDS = ("acute-toxic-pyrophoric", "acute-toxic")
EXPORT_POSTURES = ("none", "ear", "itar")


class SafetyPhase(Enum):
    INIT = "init"
    CLEARED = "cleared"
    REFUSED = "refused"


@dataclass
class SafetyState:
    phase: str = SafetyPhase.INIT.value
    design_id: str = ""
    in_sourcing: str = "conflict-free-attested"
    # list of {name, hazard_class, conflict_mineral, export_control, acknowledged}
    precursors: list = field(default_factory=list)
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> SafetyState:
    return SafetyState(**d.get("cell_state", {}))


def _norm(v: str | None) -> str:
    return (v or "").lstrip(":")


def review(state: dict[str, Any]) -> dict[str, Any]:
    """G3/G4 refusal gate. Sets phase=cleared or phase=refused(+reason)."""
    cs = _state(state)
    cs.design_id = state.get("design_id", cs.design_id)
    cs.in_sourcing = _norm(state.get("in_sourcing", cs.in_sourcing))
    cs.precursors = list(state.get("precursors", cs.precursors))

    # G4: conflict-mineral In/Ga sourcing must be clean.
    uses_conflict = any(p.get("conflict_mineral") for p in cs.precursors)
    if uses_conflict and cs.in_sourcing not in CLEAN_SOURCING:
        cs.refusal = (
            f"G4: design {cs.design_id!r} consumes a conflict-mineral element (In/Ga) "
            f"with :in-sourcing {cs.in_sourcing!r}; clean sourcing "
            f"{CLEAN_SOURCING} required (inherits hikari/himawari §G2)."
        )
        cs.phase = SafetyPhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    # G3: every acute-toxic precursor must be acknowledged.
    for p in cs.precursors:
        if _norm(p.get("hazard_class")) in ACUTE_HAZARDS and not p.get("acknowledged"):
            cs.refusal = (
                f"G3: acute-toxic precursor {p.get('name')!r} "
                f"({p.get('hazard_class')!r}) is not acknowledged; review refused."
            )
            cs.phase = SafetyPhase.REFUSED.value
            return {"cell_state": cs.__dict__}
        ec = _norm(p.get("export_control", "none"))
        if ec not in EXPORT_POSTURES:
            cs.refusal = f"export-control posture {ec!r} not in {EXPORT_POSTURES}"
            cs.phase = SafetyPhase.REFUSED.value
            return {"cell_state": cs.__dict__}

    cs.payload = {
        "designId": cs.design_id,
        "inSourcing": cs.in_sourcing,
        "precursorCount": len(cs.precursors),
        "exportControls": sorted({_norm(p.get("export_control", "none")) for p in cs.precursors}),
        "cleared": True,
    }
    cs.refusal = ""
    cs.phase = SafetyPhase.CLEARED.value
    return {"cell_state": cs.__dict__}
