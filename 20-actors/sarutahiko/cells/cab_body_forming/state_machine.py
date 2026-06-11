"""Cab body forming state machine — ADR-2605252500 L3.

Steel sheet (kanayama Wave 2 when available, external commodity R0/R1) hot
stamping → robotic spot welding → leak test.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CabPhase(Enum):
    INIT = "init"
    SHEET_LOT_VERIFIED = "sheet_lot_verified"
    HOT_STAMPING_COMPLETE = "hot_stamping_complete"
    SPOT_WELDING_COMPLETE = "spot_welding_complete"
    LEAK_TEST_PASSED = "leak_test_passed"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class CabState:
    phase: CabPhase
    chassisId: str
    completionPct: int
    sheetLot: dict[str, Any] | None = None
    stampedPanels: list[dict[str, Any]] | None = None
    spotWelds: dict[str, Any] | None = None
    leakTestResult: dict[str, Any] | None = None


def transition_to_sheet_lot_verified(state: dict[str, Any]) -> dict[str, Any]:
    s = CabState(**state.get("cab_state", {}))
    s.sheetLot = {
        "source": "external-commodity-R1",
        "note": "R2+ source from kanayama Wave 2 steel coil",
        "lotId": "STEEL-SHEET-2026-05-0021",
        "thicknessMm": 0.8,
    }
    s.phase = CabPhase.SHEET_LOT_VERIFIED
    s.completionPct = 15
    return {"cab_state": s.__dict__, "next_node": "stamp"}


def transition_to_hot_stamping_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = CabState(**state.get("cab_state", {}))
    s.stampedPanels = [
        {"panel": "roof", "stampingTempC": 900, "ipfsCid": "bafkreiroof..."},
        {"panel": "left_side", "stampingTempC": 900, "ipfsCid": "bafkreilside..."},
        {"panel": "right_side", "stampingTempC": 900, "ipfsCid": "bafkreirside..."},
        {"panel": "rear", "stampingTempC": 900, "ipfsCid": "bafkreirear..."},
        {"panel": "floor", "stampingTempC": 900, "ipfsCid": "bafkreifloor..."},
    ]
    s.phase = CabPhase.HOT_STAMPING_COMPLETE
    s.completionPct = 45
    return {"cab_state": s.__dict__, "next_node": "weld"}


def transition_to_spot_welding_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = CabState(**state.get("cab_state", {}))
    s.spotWelds = {
        "totalSpots": 2400,
        "robotPasses": 4,
        "videoCid": "bafkreispotweld...",
    }
    s.phase = CabPhase.SPOT_WELDING_COMPLETE
    s.completionPct = 75
    return {"cab_state": s.__dict__, "next_node": "leak"}


def transition_to_leak_test_passed(state: dict[str, Any]) -> dict[str, Any]:
    s = CabState(**state.get("cab_state", {}))
    s.leakTestResult = {
        "method": "pressure-decay",
        "leakRatePaPerS": 1.2,
        "limitPaPerS": 5.0,
        "accept": True,
    }
    s.phase = CabPhase.LEAK_TEST_PASSED
    s.completionPct = 92
    return {"cab_state": s.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = CabState(**state.get("cab_state", {}))
    s.phase = CabPhase.ATTESTATION_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.sarutahiko.cabBodyAttestation",
        "chassisId": s.chassisId,
        "sheetLot": s.sheetLot,
        "stampedPanels": s.stampedPanels,
        "spotWelds": s.spotWelds,
        "leakTestResult": s.leakTestResult,
        "recordedAt": "2026-05-26T11:00:00Z",
    }
    return {"cab_state": s.__dict__, "cab_body_attestation": record, "next_node": "end"}
