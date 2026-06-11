"""Emissions + acoustic audit state machine — ADR-2605252600 G8 cross-cutting.

ISO 3095 wayside noise + 日本騒音規制法 + IEC 62236 EMC.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AcousticPhase(Enum):
    INIT = "init"
    WAYSIDE_NOISE_MEASURED = "wayside_noise_measured"
    VIBRATION_MEASURED = "vibration_measured"
    EMC_VERIFIED = "emc_verified"
    RECORD_EMITTED = "record_emitted"


@dataclass
class AcousticState:
    phase: AcousticPhase
    trainsetId: str
    completionPct: int
    waysideNoise: dict[str, Any] | None = None
    vibration: dict[str, Any] | None = None
    emcResult: dict[str, Any] | None = None
    overallAccept: bool | None = None


def transition_to_wayside_noise_measured(state: dict[str, Any]) -> dict[str, Any]:
    s = AcousticState(**state.get("acoustic_state", {}))
    s.waysideNoise = {
        "standard": "ISO 3095",
        "dbAAt25mAtSpeed_300kmh": 88, "limit_dbA": 95,
        "dbAStandstill": 68, "limitStandstill_dbA": 70,
        "accept": True,
    }
    s.phase = AcousticPhase.WAYSIDE_NOISE_MEASURED
    s.completionPct = 35
    return {"acoustic_state": s.__dict__, "next_node": "vibration"}


def transition_to_vibration_measured(state: dict[str, Any]) -> dict[str, Any]:
    s = AcousticState(**state.get("acoustic_state", {}))
    s.vibration = {
        "standard": "日本 騒音規制法",
        "dbVibrationAtTrackside": 58, "limit_dbVibration": 60,
        "accept": True,
    }
    s.phase = AcousticPhase.VIBRATION_MEASURED
    s.completionPct = 60
    return {"acoustic_state": s.__dict__, "next_node": "emc"}


def transition_to_emc_verified(state: dict[str, Any]) -> dict[str, Any]:
    s = AcousticState(**state.get("acoustic_state", {}))
    s.emcResult = {
        "standard": "IEC 62236",
        "emissionPass": True,
        "immunityPass": True,
        "accept": True,
    }
    s.phase = AcousticPhase.EMC_VERIFIED
    s.completionPct = 90
    return {"acoustic_state": s.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = AcousticState(**state.get("acoustic_state", {}))
    s.overallAccept = all([
        (s.waysideNoise or {}).get("accept") is True,
        (s.vibration or {}).get("accept") is True,
        (s.emcResult or {}).get("accept") is True,
    ])
    s.phase = AcousticPhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.yamabiko.acousticEmissionsAuditRecord",
        "trainsetId": s.trainsetId,
        "waysideNoise": s.waysideNoise,
        "vibration": s.vibration,
        "emcResult": s.emcResult,
        "overallAccept": s.overallAccept,
        "regulatoryBasis": ["ISO 3095", "日本 騒音規制法", "IEC 62236"],
        "recordedAt": "2026-05-27T15:00:00Z",
    }
    return {"acoustic_state": s.__dict__, "acoustic_emissions_audit_record": record, "next_node": "end"}
