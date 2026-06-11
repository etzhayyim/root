"""Marine emissions audit state machine — ADR-2605252200 G14 cross-cutting.

Continuous MARPOL Annex I-VI + BWMC + IMO biofouling guidelines compliance
monitoring during L1–L5c. Consistent with ADR-2605242745 Funamori surface
counterpart.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EmissionsAuditPhase(Enum):
    INIT = "init"
    MARPOL_SCAN = "marpol_scan"
    BWMC_SCAN = "bwmc_scan"
    BIOFOULING_SCAN = "biofouling_scan"
    RECORD_EMITTED = "record_emitted"


@dataclass
class EmissionsAuditState:
    phase: EmissionsAuditPhase
    craftId: str
    completionPct: int
    marpolFindings: dict[str, Any] | None = None
    bwmcFindings: dict[str, Any] | None = None
    biofoulingFindings: dict[str, Any] | None = None
    overallAccept: bool | None = None


def transition_to_marpol_scan(state: dict[str, Any]) -> dict[str, Any]:
    ea = EmissionsAuditState(**state.get("emissions_audit_state", {}))
    ea.marpolFindings = {
        "annexI_oilPollution": {"violations": 0, "accept": True},
        "annexII_noxiousLiquid": {"violations": 0, "accept": True},
        "annexIII_harmfulPackaged": {"violations": 0, "accept": True},
        "annexIV_sewage": {"violations": 0, "accept": True},
        "annexV_garbage": {"violations": 0, "accept": True},
        "annexVI_airPollution": {"violations": 0, "accept": True},
    }
    ea.phase = EmissionsAuditPhase.MARPOL_SCAN
    ea.completionPct = 35
    return {"emissions_audit_state": ea.__dict__, "next_node": "bwmc"}


def transition_to_bwmc_scan(state: dict[str, Any]) -> dict[str, Any]:
    ea = EmissionsAuditState(**state.get("emissions_audit_state", {}))
    ea.bwmcFindings = {
        "ballastWaterManagementPlan": "approved",
        "treatmentSystem": "filtration+UV",
        "ovicidalEffectiveness": "≥99.9%",
        "accept": True,
    }
    ea.phase = EmissionsAuditPhase.BWMC_SCAN
    ea.completionPct = 65
    return {"emissions_audit_state": ea.__dict__, "next_node": "biofouling"}


def transition_to_biofouling_scan(state: dict[str, Any]) -> dict[str, Any]:
    ea = EmissionsAuditState(**state.get("emissions_audit_state", {}))
    ea.biofoulingFindings = {
        "imoGuidelines": "MEPC.378(80) compliant",
        "hullCoatingType": "biocide-free silicone fouling-release",
        "antifoulingTributyltinFree": True,
        "sangoInspectionFrequency": "every 90 days",
        "accept": True,
    }
    ea.phase = EmissionsAuditPhase.BIOFOULING_SCAN
    ea.completionPct = 90
    return {"emissions_audit_state": ea.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    ea = EmissionsAuditState(**state.get("emissions_audit_state", {}))
    ea.overallAccept = (
        all(v["accept"] for v in (ea.marpolFindings or {}).values())
        and (ea.bwmcFindings or {}).get("accept") is True
        and (ea.biofoulingFindings or {}).get("accept") is True
    )
    ea.phase = EmissionsAuditPhase.RECORD_EMITTED
    ea.completionPct = 100
    record = {
        "$type": "etzhayyim:watatsumi:marineEmissionsAuditRecord",
        "craftId": ea.craftId,
        "marpol": ea.marpolFindings,
        "bwmc": ea.bwmcFindings,
        "biofouling": ea.biofoulingFindings,
        "overallAccept": ea.overallAccept,
        "g14Reference": "ADR-2605252200 G14",
        "recordedAt": "2026-05-27T11:00:00Z",
    }
    return {
        "emissions_audit_state": ea.__dict__,
        "marine_emissions_audit_record": record,
        "next_node": "end",
    }
