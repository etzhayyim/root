"""Section joining state machine — ADR-2605252200 L5a.

Final ring-to-ring multi-pass TIG welding + 100% radiographic test + post-weld
heat treatment (PWHT). The terminal weld that closes the pressure boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SectionJoiningPhase(Enum):
    INIT = "init"
    SECTIONS_ALIGNED = "sections_aligned"
    MULTIPASS_TIG_COMPLETE = "multipass_tig_complete"
    RT_100PCT_PASSED = "rt_100pct_passed"
    PWHT_COMPLETE = "pwht_complete"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class SectionJoiningState:
    phase: SectionJoiningPhase
    craftId: str
    completionPct: int
    sectionPairs: list[dict[str, Any]] | None = None
    multiPassDetails: list[dict[str, Any]] | None = None
    rtResults: list[dict[str, Any]] | None = None
    pwhtRecord: dict[str, Any] | None = None
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_sections_aligned(state: dict[str, Any]) -> dict[str, Any]:
    sj = SectionJoiningState(**state.get("section_joining_state", {}))
    sj.sectionPairs = [
        {"sectionA": 0, "sectionB": 1, "alignmentToleranceMm": 0.8},
        {"sectionA": 1, "sectionB": 2, "alignmentToleranceMm": 0.6},
    ]
    sj.phase = SectionJoiningPhase.SECTIONS_ALIGNED
    sj.completionPct = 20
    return {"section_joining_state": sj.__dict__, "next_node": "tig"}


def transition_to_multipass_tig_complete(state: dict[str, Any]) -> dict[str, Any]:
    sj = SectionJoiningState(**state.get("section_joining_state", {}))
    sj.multiPassDetails = [
        {"sectionPair": "0-1", "passes": 6, "videoCid": "bafkreitig01..."},
        {"sectionPair": "1-2", "passes": 6, "videoCid": "bafkreitig12..."},
    ]
    sj.phase = SectionJoiningPhase.MULTIPASS_TIG_COMPLETE
    sj.completionPct = 55
    return {"section_joining_state": sj.__dict__, "next_node": "rt"}


def transition_to_rt_100pct_passed(state: dict[str, Any]) -> dict[str, Any]:
    sj = SectionJoiningState(**state.get("section_joining_state", {}))
    sj.rtResults = [
        {"sectionPair": "0-1", "rtFilmCid": "bafkreirt01...", "coveragePct": 100, "indications": []},
        {"sectionPair": "1-2", "rtFilmCid": "bafkreirt12...", "coveragePct": 100, "indications": []},
    ]
    sj.phase = SectionJoiningPhase.RT_100PCT_PASSED
    sj.completionPct = 75
    return {"section_joining_state": sj.__dict__, "next_node": "pwht"}


def transition_to_pwht_complete(state: dict[str, Any]) -> dict[str, Any]:
    sj = SectionJoiningState(**state.get("section_joining_state", {}))
    sj.pwhtRecord = {
        "soakTemperatureC": 620,
        "soakDurationMinutes": 240,
        "rampUpCPerHour": 110,
        "rampDownCPerHour": 80,
        "thermocoupleLogCid": "bafkreipwhtlog...",
    }
    sj.phase = SectionJoiningPhase.PWHT_COMPLETE
    sj.completionPct = 90
    return {"section_joining_state": sj.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    sj = SectionJoiningState(**state.get("section_joining_state", {}))
    sj.robotSignatures = [
        {"robotDid": "did:web:etzhayyim.com:ama-unit-1", "role": "weld_lead",
         "timestamp": "2026-05-26T15:00:00Z", "signature": "..."},
        {"robotDid": "did:web:etzhayyim.com:tako-unit-1", "role": "interior_witness",
         "timestamp": "2026-05-26T15:00:05Z", "signature": "..."},
    ]
    sj.phase = SectionJoiningPhase.ATTESTATION_EMITTED
    sj.completionPct = 100
    record = {
        "$type": "com.etzhayyim.watatsumi.sectionJoiningAttestation",
        "craftId": sj.craftId,
        "sectionPairs": sj.sectionPairs,
        "multiPassDetails": sj.multiPassDetails,
        "rtResults": sj.rtResults,
        "pwhtRecord": sj.pwhtRecord,
        "attestingRobots": sj.robotSignatures,
        "recordedAt": "2026-05-26T15:00:10Z",
    }
    return {
        "section_joining_state": sj.__dict__,
        "section_joining_attestation": record,
        "next_node": "end",
    }
