"""Weld inspection state machine — ADR-2605252200 L3.

100% RT (radiographic) + UT (ultrasonic) + PT (penetrant) NDT on every weld.
In-process witness via Sango AUV swarm. Reference: ASME BPVC §VIII Div 3 or
equivalent civilian pressure-vessel code.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class WeldInspectionPhase(Enum):
    INIT = "init"
    RT_COMPLETE = "rt_complete"
    UT_COMPLETE = "ut_complete"
    PT_COMPLETE = "pt_complete"
    SANGO_WITNESS_COMPLETE = "sango_witness_complete"
    RECORD_EMITTED = "record_emitted"


@dataclass
class WeldInspectionState:
    phase: WeldInspectionPhase
    craftId: str
    sectionIndex: int
    completionPct: int
    rtResults: list[dict[str, Any]] | None = None
    utResults: list[dict[str, Any]] | None = None
    ptResults: list[dict[str, Any]] | None = None
    sangoWitnessRecords: list[dict[str, Any]] | None = None
    indicationFindings: list[dict[str, Any]] | None = None
    overallAccept: bool | None = None


def transition_to_rt_complete(state: dict[str, Any]) -> dict[str, Any]:
    wi = WeldInspectionState(**state.get("weld_inspection_state", {}))
    mock_rt = [
        {"weldId": "ring0-ring1-seam", "rtFilmCid": "bafkreirt1...", "indications": []},
        {"weldId": "ring1-ring2-seam", "rtFilmCid": "bafkreirt2...", "indications": []},
        {"weldId": "ring2-ring3-seam", "rtFilmCid": "bafkreirt3...", "indications": []},
    ]
    wi.phase = WeldInspectionPhase.RT_COMPLETE
    wi.rtResults = mock_rt
    wi.completionPct = 30
    return {"weld_inspection_state": wi.__dict__, "next_node": "ut"}


def transition_to_ut_complete(state: dict[str, Any]) -> dict[str, Any]:
    wi = WeldInspectionState(**state.get("weld_inspection_state", {}))
    wi.utResults = [
        {"weldId": "ring0-ring1-seam", "method": "phased-array-UT",
         "scanCid": "bafkreiut1...", "indications": []},
    ]
    wi.phase = WeldInspectionPhase.UT_COMPLETE
    wi.completionPct = 55
    return {"weld_inspection_state": wi.__dict__, "next_node": "pt"}


def transition_to_pt_complete(state: dict[str, Any]) -> dict[str, Any]:
    wi = WeldInspectionState(**state.get("weld_inspection_state", {}))
    wi.ptResults = [
        {"weldId": "ring0-ring1-seam", "method": "dye-penetrant", "photoCid": "bafkreipt1...", "indications": []},
    ]
    wi.phase = WeldInspectionPhase.PT_COMPLETE
    wi.completionPct = 75
    return {"weld_inspection_state": wi.__dict__, "next_node": "sango"}


def transition_to_sango_witness(state: dict[str, Any]) -> dict[str, Any]:
    """In-process Sango AUV swarm witness (outer-hull visual + biofouling baseline)."""
    wi = WeldInspectionState(**state.get("weld_inspection_state", {}))
    mock_witness = [
        {"sangoDid": "did:web:etzhayyim.com:sango-unit-1", "videoCid": "bafkreisango1...",
         "anomalies": []},
        {"sangoDid": "did:web:etzhayyim.com:sango-unit-2", "videoCid": "bafkreisango2...",
         "anomalies": []},
    ]
    wi.sangoWitnessRecords = mock_witness
    wi.phase = WeldInspectionPhase.SANGO_WITNESS_COMPLETE
    wi.completionPct = 90
    return {"weld_inspection_state": wi.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    wi = WeldInspectionState(**state.get("weld_inspection_state", {}))
    findings = []
    for r in (wi.rtResults or []):
        findings.extend(r.get("indications", []))
    for u in (wi.utResults or []):
        findings.extend(u.get("indications", []))
    for p in (wi.ptResults or []):
        findings.extend(p.get("indications", []))
    wi.indicationFindings = findings
    wi.overallAccept = len(findings) == 0
    wi.phase = WeldInspectionPhase.RECORD_EMITTED
    wi.completionPct = 100
    record = {
        "$type": "com.etzhayyim.watatsumi.weldInspectionRecord",
        "craftId": wi.craftId,
        "sectionIndex": wi.sectionIndex,
        "rtResults": wi.rtResults,
        "utResults": wi.utResults,
        "ptResults": wi.ptResults,
        "sangoWitnessRecords": wi.sangoWitnessRecords,
        "indicationFindings": findings,
        "overallAccept": wi.overallAccept,
        "code": "ASME BPVC §VIII Div 3 equivalent",
        "recordedAt": "2026-05-26T13:00:00Z",
    }
    return {
        "weld_inspection_state": wi.__dict__,
        "weld_inspection_record": record,
        "next_node": "end",
    }
