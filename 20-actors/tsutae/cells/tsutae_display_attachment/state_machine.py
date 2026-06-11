"""Display attachment state machine — ADR-2605261300 phase `display` (joseph).

Laminates the (replaceable) display panel onto the assembled chassis and
calibrates the touch digitizer. Lamination uses a re-openable gasket/clip
mount (NOT permanent adhesive) so G3 repair-rightful holds at the display.
Emits `com.etzhayyim.tsutae.displayAttachedRecord`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DisplayPhase(Enum):
    INIT = "init"
    PANEL_VERIFIED = "panel_verified"
    LAMINATED = "laminated"
    TOUCH_CALIBRATED = "touch_calibrated"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class DisplayState:
    phase: DisplayPhase
    chassisId: str
    completionPct: int
    panel: dict[str, Any] | None = None
    lamination: dict[str, Any] | None = None
    touch: dict[str, Any] | None = None


def transition_to_panel_verified(state: dict[str, Any]) -> dict[str, Any]:
    s = DisplayState(**state.get("display_state", {}))
    s.panel = {
        "type": state.get("panelType", "LCD"),  # R1 = LCD; R2+ OLED
        "sizeIn": 6.1,
        "deadPixels": 0,
        "lotId": "DISP-2026-05-LOT-0007",
        "replaceable": True,
    }
    s.phase = DisplayPhase.PANEL_VERIFIED
    s.completionPct = 25
    return {"display_state": s.__dict__, "next_node": "laminate"}


def transition_to_laminated(state: dict[str, Any]) -> dict[str, Any]:
    s = DisplayState(**state.get("display_state", {}))
    s.lamination = {
        "method": "gasket-clip",  # NOT permanent adhesive (G3)
        "adhesiveGrams": 0.0,
        "robot": "robot:hitogata",  # R2+ class-A clean; R1 manual
        "bubbleCount": 0,
    }
    s.phase = DisplayPhase.LAMINATED
    s.completionPct = 55
    return {"display_state": s.__dict__, "next_node": "calibrate"}


def transition_to_touch_calibrated(state: dict[str, Any]) -> dict[str, Any]:
    s = DisplayState(**state.get("display_state", {}))
    s.touch = {"points": 5, "linearityErrPx": 1.2, "specLimitPx": 3.0, "accept": True}
    s.phase = DisplayPhase.TOUCH_CALIBRATED
    s.completionPct = 80
    return {"display_state": s.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = DisplayState(**state.get("display_state", {}))
    s.phase = DisplayPhase.ATTESTATION_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.tsutae.displayAttachedRecord",
        "chassisId": s.chassisId,
        "panel": s.panel,
        "lamination": s.lamination,
        "touch": s.touch,
        "accept": bool((s.touch or {}).get("accept")
                       and (s.lamination or {}).get("adhesiveGrams", 99) <= 5.0),
        "recordedAt": "2026-05-26T11:00:00Z",
    }
    return {"display_state": s.__dict__, "display_attached": record, "next_node": "end"}
