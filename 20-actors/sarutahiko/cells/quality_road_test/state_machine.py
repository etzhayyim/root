"""Quality road test state machine — ADR-2605252500 L5c.

Roller dynamometer + 50 km public-road test. Norimichi driver (SAE Level 3
driver-in-seat). G12 KPI: max speed ≤90 km/h civilian / autonomous ≤ Level 4.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RoadTestPhase(Enum):
    INIT = "init"
    DYNO_RUN_COMPLETE = "dyno_run_complete"
    G12_KPI_VERIFIED = "g12_kpi_verified"
    PUBLIC_ROAD_TEST_COMPLETE = "public_road_test_complete"
    NORIMICHI_ATTESTATION = "norimichi_attestation"
    RECORD_EMITTED = "record_emitted"


@dataclass
class RoadTestState:
    phase: RoadTestPhase
    chassisId: str
    completionPct: int
    dynoResult: dict[str, Any] | None = None
    g12KpiCheck: dict[str, Any] | None = None
    publicRoadResult: dict[str, Any] | None = None
    norimichiAttestation: dict[str, Any] | None = None


def transition_to_dyno_run_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = RoadTestState(**state.get("road_test_state", {}))
    s.dynoResult = {
        "maxWheelPowerKw": 320,
        "maxWheelTorqueNm": 2100,
        "fuelConsumption_l_per_100km": 22.5,  # Wave 1 R1 B100 transition
        "brakeStoppingDistanceM": 38,
    }
    s.phase = RoadTestPhase.DYNO_RUN_COMPLETE
    s.completionPct = 35
    return {"road_test_state": s.__dict__, "next_node": "g12"}


def transition_to_g12_kpi_verified(state: dict[str, Any]) -> dict[str, Any]:
    s = RoadTestState(**state.get("road_test_state", {}))
    s.g12KpiCheck = {
        "maxSpeedKmh": 85,
        "maxSpeedLimitKmh": 90,
        "autonomyLevel": "L0-manual-R1",
        "autonomyMaxLevel": 4,
        "rangeKm": 850,
        "rangeMinKm": 800,
        "gvwrT": 36,
        "gvwrMaxT": 40,
        "accept": True,
    }
    s.phase = RoadTestPhase.G12_KPI_VERIFIED
    s.completionPct = 55
    return {"road_test_state": s.__dict__, "next_node": "road"}


def transition_to_public_road_test_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = RoadTestState(**state.get("road_test_state", {}))
    s.publicRoadResult = {
        "routeDistanceKm": 50,
        "averageSpeedKmh": 65,
        "incidents": [],
        "videoCid": "bafkreiroadtest...",
    }
    s.phase = RoadTestPhase.PUBLIC_ROAD_TEST_COMPLETE
    s.completionPct = 80
    return {"road_test_state": s.__dict__, "next_node": "norimichi"}


def transition_to_norimichi_attestation(state: dict[str, Any]) -> dict[str, Any]:
    s = RoadTestState(**state.get("road_test_state", {}))
    s.norimichiAttestation = {
        "norimichiDid": "did:web:etzhayyim.com:norimichi-unit-1",
        "humanDriverSbtDid": "did:web:etzhayyim.com:adherent:test-driver-001#sbt",
        "saeLevel": 3,
        "saeMaxLevel": 4,
        "timestamp": "2026-05-26T18:30:00Z",
        "signature": "...",
    }
    s.phase = RoadTestPhase.NORIMICHI_ATTESTATION
    s.completionPct = 92
    return {"road_test_state": s.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = RoadTestState(**state.get("road_test_state", {}))
    s.phase = RoadTestPhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.sarutahiko.roadTestRecord",
        "chassisId": s.chassisId,
        "dynoResult": s.dynoResult,
        "g12KpiCheck": s.g12KpiCheck,
        "publicRoadResult": s.publicRoadResult,
        "norimichiAttestation": s.norimichiAttestation,
        "overallAccept": True,
        "recordedAt": "2026-05-26T18:35:00Z",
    }
    return {"road_test_state": s.__dict__, "road_test_record": record, "next_node": "end"}
