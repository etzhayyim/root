"""Phase state machine for the kiyome surface_cleaning (箒) cell.

This is the constitutional heart of kiyome: a cleaning pass into a private space (a home)
can only be attested if privacy-by-construction (G9) holds as a HARD invariant:
  - on_device_only      == True   (no imagery/sensor feed left the robot)
  - imagery_retained    == False  (no occupant imagery retained)
  - biometric_capture   == False  (N5 — no facial/biometric recognition of occupants)
Any violation raises — the cleaner robot is the opposite of a spy (ADR-2606032100 §G9).
G3 witness quorum (>=2 robot sigs + >=1 human attestation) is required to finalize a pass.

Transitions are pure and unit-tested; the cell's .solve() raises until Council activation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

ALLOWED_METHODS = ("sweep", "vacuum", "mop", "wipe")


class CleaningPhase(Enum):
    INIT = "init"
    TRAVERSED = "traversed"
    CLEANED = "cleaned"
    PASS_LOGGED = "pass_logged"


@dataclass
class CleaningState:
    phase: str = CleaningPhase.INIT.value
    site_id: str = "did:web:kiyome.etzhayyim.com/site/demo-0001"
    area_m2: int = 0
    method: str = "vacuum"
    # privacy-by-construction (G9 / N5) — hard invariants
    on_device_only: bool = True
    imagery_retained: bool = False
    biometric_capture: bool = False
    robot_sigs: list = field(default_factory=list)
    human_attestation: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> CleaningState:
    return CleaningState(**d.get("cell_state", {}))


def transition_to_traversed(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.phase = CleaningPhase.TRAVERSED.value
    cs.area_m2 = int(state.get("area_m2", 0))
    return {"cell_state": cs.__dict__, "next_node": "cleaned"}


def transition_to_cleaned(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    method = state.get("method", cs.method)
    if method not in ALLOWED_METHODS:
        raise ValueError(f"unknown cleaning method {method!r} not in {ALLOWED_METHODS}")
    cs.phase = CleaningPhase.CLEANED.value
    cs.method = method
    return {"cell_state": cs.__dict__, "next_node": "pass_logged"}


def transition_to_pass_logged(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.on_device_only = bool(state.get("on_device_only", True))
    cs.imagery_retained = bool(state.get("imagery_retained", False))
    cs.biometric_capture = bool(state.get("biometric_capture", False))
    cs.robot_sigs = list(state.get("robot_sigs", []))
    cs.human_attestation = state.get("human_attestation", "")

    # G9 privacy-by-construction — hard invariants (the cleaner robot is the opposite of a spy)
    if not cs.on_device_only:
        raise ValueError("G9 violation: imagery/sensor feed left the robot (on_device_only must be True)")
    if cs.imagery_retained:
        raise ValueError("G9 violation: occupant imagery retained (imagery_retained must be False)")
    if cs.biometric_capture:
        raise ValueError("N5 violation: biometric/facial recognition of occupants (biometric_capture must be False)")

    quorum_ok = len(cs.robot_sigs) >= 2 and bool(cs.human_attestation)
    cs.phase = CleaningPhase.PASS_LOGGED.value
    cs.payload = {
        "cleaning_pass": {
            "siteId": cs.site_id,
            "areaM2": cs.area_m2,
            "method": cs.method,
            "onDeviceOnly": True,        # G9 invariant (const true in lexicon)
            "imageryRetained": False,    # G9 invariant (const false in lexicon)
            "witnessQuorumMet": quorum_ok,
        }
    }
    return {"cell_state": cs.__dict__, "next_node": "end"}
