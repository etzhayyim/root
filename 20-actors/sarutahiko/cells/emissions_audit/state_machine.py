"""Emissions audit state machine — ADR-2605252500 G8 cross-cutting.

Euro 7 + 日本ポスト新長期排出ガス規制 + Bharat Stage VI continuous compliance.
R0-R1 tailpipe + R2+ zero tailpipe (G7 transition).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EmissionsPhase(Enum):
    INIT = "init"
    EURO7_SCANNED = "euro7_scanned"
    JAPAN_PNLT_SCANNED = "japan_pnlt_scanned"
    BHARAT_VI_SCANNED = "bharat_vi_scanned"
    RECORD_EMITTED = "record_emitted"


@dataclass
class EmissionsState:
    phase: EmissionsPhase
    chassisId: str
    completionPct: int
    euro7Findings: dict[str, Any] | None = None
    japanPostNLTFindings: dict[str, Any] | None = None
    bharatViFindings: dict[str, Any] | None = None
    overallAccept: bool | None = None


def transition_to_euro7_scanned(state: dict[str, Any]) -> dict[str, Any]:
    s = EmissionsState(**state.get("emissions_state", {}))
    s.euro7Findings = {
        "nox_mg_per_km": 90, "nox_limit_mg_per_km": 200,
        "particulate_mg_per_km": 4.5, "particulate_limit_mg_per_km": 10,
        "co_mg_per_km": 750, "co_limit_mg_per_km": 1500,
        "accept": True,
    }
    s.phase = EmissionsPhase.EURO7_SCANNED
    s.completionPct = 30
    return {"emissions_state": s.__dict__, "next_node": "japan"}


def transition_to_japan_pnlt_scanned(state: dict[str, Any]) -> dict[str, Any]:
    s = EmissionsState(**state.get("emissions_state", {}))
    s.japanPostNLTFindings = {
        "nox_g_per_kWh": 0.30, "nox_limit_g_per_kWh": 0.40,
        "particulate_g_per_kWh": 0.008, "particulate_limit_g_per_kWh": 0.010,
        "accept": True,
    }
    s.phase = EmissionsPhase.JAPAN_PNLT_SCANNED
    s.completionPct = 60
    return {"emissions_state": s.__dict__, "next_node": "bharat"}


def transition_to_bharat_vi_scanned(state: dict[str, Any]) -> dict[str, Any]:
    s = EmissionsState(**state.get("emissions_state", {}))
    s.bharatViFindings = {
        "nox_g_per_kWh": 0.42, "nox_limit_g_per_kWh": 0.46,
        "particulate_g_per_kWh": 0.009, "particulate_limit_g_per_kWh": 0.010,
        "accept": True,
    }
    s.phase = EmissionsPhase.BHARAT_VI_SCANNED
    s.completionPct = 90
    return {"emissions_state": s.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = EmissionsState(**state.get("emissions_state", {}))
    s.overallAccept = all([
        (s.euro7Findings or {}).get("accept") is True,
        (s.japanPostNLTFindings or {}).get("accept") is True,
        (s.bharatViFindings or {}).get("accept") is True,
    ])
    s.phase = EmissionsPhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.sarutahiko.emissionsAuditRecord",
        "chassisId": s.chassisId,
        "euro7Findings": s.euro7Findings,
        "japanPostNLTFindings": s.japanPostNLTFindings,
        "bharatViFindings": s.bharatViFindings,
        "overallAccept": s.overallAccept,
        "regulatoryBasis": [
            "EU Regulation (EU) 2024/1257 — Euro 7",
            "日本 ポスト新長期排出ガス規制",
            "Bharat Stage VI",
        ],
        "phaseGate": "R0-R1 tailpipe permitted under G7 transition; R2+ requires zero tailpipe",
        "recordedAt": "2026-05-26T19:00:00Z",
    }
    return {"emissions_state": s.__dict__, "emissions_audit_record": record, "next_node": "end"}
