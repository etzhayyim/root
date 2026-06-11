"""Air emissions audit state machine — ADR-2605252400 G8 cross-cutting.

Continuous PFC / SO₂ / NOx / particulate / dioxin / VOC stack monitoring
vs EU IED 2010/75/EU + 日本大気汚染防止法 + EN 12457 solid-waste leachate.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EmissionsPhase(Enum):
    INIT = "init"
    PFC_SCANNED = "pfc_scanned"
    SO2_NOX_SCANNED = "so2_nox_scanned"
    PARTICULATE_DIOXIN_SCANNED = "particulate_dioxin_scanned"
    LEACHATE_TESTED = "leachate_tested"
    RECORD_EMITTED = "record_emitted"


@dataclass
class EmissionsState:
    phase: EmissionsPhase
    lotId: str
    completionPct: int
    pfcFindings: dict[str, Any] | None = None
    so2NoxFindings: dict[str, Any] | None = None
    particulateDioxinFindings: dict[str, Any] | None = None
    leachateFindings: dict[str, Any] | None = None
    overallAccept: bool | None = None


def transition_to_pfc_scanned(state: dict[str, Any]) -> dict[str, Any]:
    s = EmissionsState(**state.get("emissions_state", {}))
    s.pfcFindings = {
        "cf4_ppm": 0.0,  # Wave 1 Al recycling produces no PFC (only Hall-Héroult does)
        "c2f6_ppm": 0.0,
        "gwp_co2eq_kg": 0.0,
        "accept": True,
    }
    s.phase = EmissionsPhase.PFC_SCANNED
    s.completionPct = 25
    return {"emissions_state": s.__dict__, "next_node": "so2_nox"}


def transition_to_so2_nox_scanned(state: dict[str, Any]) -> dict[str, Any]:
    s = EmissionsState(**state.get("emissions_state", {}))
    s.so2NoxFindings = {
        "so2_mg_per_nm3": 18, "so2_limit_mg_per_nm3": 50,
        "nox_mg_per_nm3": 95, "nox_limit_mg_per_nm3": 200,
        "accept": True,
    }
    s.phase = EmissionsPhase.SO2_NOX_SCANNED
    s.completionPct = 50
    return {"emissions_state": s.__dict__, "next_node": "particulate"}


def transition_to_particulate_dioxin_scanned(state: dict[str, Any]) -> dict[str, Any]:
    s = EmissionsState(**state.get("emissions_state", {}))
    s.particulateDioxinFindings = {
        "pm10_mg_per_nm3": 4.2, "pm10_limit_mg_per_nm3": 10,
        "dioxin_ng_TEQ_per_nm3": 0.04, "dioxin_limit_ng_TEQ_per_nm3": 0.1,
        "voc_mg_per_nm3": 11, "voc_limit_mg_per_nm3": 20,
        "accept": True,
    }
    s.phase = EmissionsPhase.PARTICULATE_DIOXIN_SCANNED
    s.completionPct = 75
    return {"emissions_state": s.__dict__, "next_node": "leachate"}


def transition_to_leachate_tested(state: dict[str, Any]) -> dict[str, Any]:
    s = EmissionsState(**state.get("emissions_state", {}))
    s.leachateFindings = {
        "method": "EN 12457-2",
        "pb_mg_per_l": 0.02, "pb_limit_mg_per_l": 0.5,
        "cd_mg_per_l": 0.001, "cd_limit_mg_per_l": 0.04,
        "accept": True,
    }
    s.phase = EmissionsPhase.LEACHATE_TESTED
    s.completionPct = 90
    return {"emissions_state": s.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = EmissionsState(**state.get("emissions_state", {}))
    s.overallAccept = all([
        (s.pfcFindings or {}).get("accept") is True,
        (s.so2NoxFindings or {}).get("accept") is True,
        (s.particulateDioxinFindings or {}).get("accept") is True,
        (s.leachateFindings or {}).get("accept") is True,
    ])
    s.phase = EmissionsPhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.kanayama.airEmissionsAuditRecord",
        "lotId": s.lotId,
        "pfcFindings": s.pfcFindings,
        "so2NoxFindings": s.so2NoxFindings,
        "particulateDioxinFindings": s.particulateDioxinFindings,
        "leachateFindings": s.leachateFindings,
        "overallAccept": s.overallAccept,
        "regulatoryBasis": [
            "EU IED 2010/75/EU",
            "日本 大気汚染防止法",
            "EN 12457-2",
        ],
        "recordedAt": "2026-05-26T17:00:00Z",
    }
    return {
        "emissions_state": s.__dict__,
        "air_emissions_audit_record": record,
        "next_node": "end",
    }
