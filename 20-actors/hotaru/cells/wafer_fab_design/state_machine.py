"""Phase state machine for the hotaru wafer_fab_design (蛍) cell.

Boule → wire-saw → lap → CMP → epi-ready surface SPEC design. Assembles a waferSpec
record. STRUCTURALLY forbids representing a manufactured wafer.

Invariants enforced:
  G2 — design-only/not-fabricated: `fabricated` is forced False; any true value raises
       (a manufactured wafer is unrepresentable through R3, ADR-2605265500 §2).
  spec-sanity — diameter must be one of the known substrate sizes; EPD (etch-pit
       density) must be a positive integer (bulk crystal-quality metric).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Known InP substrate diameters in micrometers (minor-units; matches lexicon diameterUm).
KNOWN_DIAMETERS_UM = (50800, 76200, 100000)  # 2-inch / 3-inch / 4-inch
KNOWN_ORIENTATIONS = ("(100)", "(111)", "(110)")


class WaferPhase(Enum):
    INIT = "init"
    SCREENED = "screened"
    SPECIFIED = "specified"


@dataclass
class WaferState:
    phase: str = WaferPhase.INIT.value
    wafer_id: str = ""
    material: str = "inp"
    diameter_um: int = 50800
    orientation: str = "(100)"
    epd_cm2: int = 5000
    doping: str = "sulfur-n"
    fabricated: bool = False
    screened: bool = False
    sourcing: str = "representative"
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> WaferState:
    return WaferState(**d.get("cell_state", {}))


def _norm(v: str | None) -> str:
    return (v or "").lstrip(":")


def transition_to_screened(state: dict[str, Any]) -> dict[str, Any]:
    """G2 + spec-sanity screen. Raises before a spec can exist on any violation."""
    cs = _state(state)
    cs.wafer_id = state.get("wafer_id", cs.wafer_id)
    cs.material = _norm(state.get("material", cs.material)) or "inp"

    fab = state.get("fabricated", cs.fabricated)
    if fab is not False:
        raise ValueError(
            f"G2 violation: wafer {cs.wafer_id!r} cannot be :fabricated {fab!r}; only "
            f"false is permitted (a manufactured wafer is unrepresentable through R3)."
        )
    cs.fabricated = False

    dia = state.get("diameter_um", cs.diameter_um)
    if dia not in KNOWN_DIAMETERS_UM:
        raise ValueError(f"diameter {dia!r} um not in known substrate sizes {KNOWN_DIAMETERS_UM}")
    cs.diameter_um = dia

    ori = state.get("orientation", cs.orientation)
    if ori not in KNOWN_ORIENTATIONS:
        raise ValueError(f"orientation {ori!r} not in {KNOWN_ORIENTATIONS}")
    cs.orientation = ori

    epd = state.get("epd_cm2", cs.epd_cm2)
    if not isinstance(epd, int) or epd <= 0:
        raise ValueError(f"epd-cm2 must be a positive integer; got {epd!r}")
    cs.epd_cm2 = epd

    cs.doping = _norm(state.get("doping", cs.doping))
    cs.screened = True
    cs.phase = WaferPhase.SCREENED.value
    return {"cell_state": cs.__dict__}


def transition_to_specified(state: dict[str, Any]) -> dict[str, Any]:
    """Materialize the waferSpec record (only after the screen passes)."""
    cs = _state(state)
    if not cs.screened:
        raise ValueError("wafer spec requires a passed G2/spec screen first")
    cs.payload = {
        "waferId": cs.wafer_id,
        "material": cs.material,
        "diameterUm": cs.diameter_um,
        "orientation": cs.orientation,
        "epdCm2": cs.epd_cm2,
        "doping": cs.doping,
        "fabricated": False,  # G2 — invariant, never true
        "sourcing": cs.sourcing,
    }
    cs.phase = WaferPhase.SPECIFIED.value
    return {"cell_state": cs.__dict__}
