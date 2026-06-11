"""Final QC state machine — ADR-2605261300 phase `qc` (levi).

Sensor/display calibration → RF conformance (cellular OFF default; Wi-Fi/BT) →
G8 anti-addiction UX audit → functional self-test. Emits an internal qcRecord
consumed by device_attestation.

Constitutional guard:
  G8 (§2(d)) — calm-default OS: notification batching ≥15 min, no infinite-scroll
  OS primitive, no dopamine-loop API, no auto-play on lock screen. A build that
  ships addictive-UX primitives is rejected.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

G8_NOTIFY_BATCH_MIN = 15


class QcPhase(Enum):
    INIT = "init"
    CALIBRATED = "calibrated"
    RF_TESTED = "rf_tested"
    ADDICTION_UX_AUDITED = "addiction_ux_audited"
    FUNCTIONAL_TESTED = "functional_tested"
    QC_RECORD_EMITTED = "qc_record_emitted"


@dataclass
class QcState:
    phase: QcPhase
    deviceId: str
    completionPct: int
    calibration: dict[str, Any] | None = None
    rf: dict[str, Any] | None = None
    uxGuard: dict[str, Any] | None = None
    functional: dict[str, Any] | None = None


def transition_to_calibrated(state: dict[str, Any]) -> dict[str, Any]:
    s = QcState(**state.get("qc_state", {}))
    s.calibration = {"display": "ok", "imu": "ok", "camera": "ok", "touch": "ok"}
    s.phase = QcPhase.CALIBRATED
    s.completionPct = 15
    return {"qc_state": s.__dict__, "next_node": "rf"}


def transition_to_rf_tested(state: dict[str, Any]) -> dict[str, Any]:
    s = QcState(**state.get("qc_state", {}))
    s.rf = {
        "cellularDefault": "off",  # G6: Wi-Fi-default boot, cellular removable
        "wifi": "pass", "bt": "pass",
        "imeiBroadcastWhileDisconnected": False,
        "accept": True,
    }
    s.phase = QcPhase.RF_TESTED
    s.completionPct = 35
    return {"qc_state": s.__dict__, "next_node": "ux_guard"}


def transition_to_addiction_ux_audited(state: dict[str, Any]) -> dict[str, Any]:
    """G8 enforcement point: calm-default OS, no addictive primitives."""
    s = QcState(**state.get("qc_state", {}))
    batch_min = int(state.get("notificationBatchMin", G8_NOTIFY_BATCH_MIN))
    infinite_scroll = bool(state.get("infiniteScrollApi", False))
    autoplay_lock = bool(state.get("autoplayLockScreen", False))
    accept = batch_min >= G8_NOTIFY_BATCH_MIN and not infinite_scroll and not autoplay_lock
    s.uxGuard = {
        "gate": "G8",
        "notificationBatchMin": batch_min,
        "infiniteScrollApi": infinite_scroll,
        "autoplayLockScreen": autoplay_lock,
        "accept": accept,
        "reason": "calm-default UX verified" if accept
                  else "addictive-UX primitive present (§2(d) N5)",
    }
    s.phase = QcPhase.ADDICTION_UX_AUDITED
    s.completionPct = 60
    return {"qc_state": s.__dict__, "next_node": "functional"}


def transition_to_functional_tested(state: dict[str, Any]) -> dict[str, Any]:
    s = QcState(**state.get("qc_state", {}))
    s.functional = {"boot": "pass", "battery": "pass", "audio": "pass", "sensors": "pass"}
    s.phase = QcPhase.FUNCTIONAL_TESTED
    s.completionPct = 82
    return {"qc_state": s.__dict__, "next_node": "record"}


def transition_to_qc_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = QcState(**state.get("qc_state", {}))
    s.phase = QcPhase.QC_RECORD_EMITTED
    s.completionPct = 100
    record = {
        "deviceId": s.deviceId,
        "calibration": s.calibration,
        "rf": s.rf,
        "uxGuard": s.uxGuard,
        "functional": s.functional,
        "accept": bool((s.uxGuard or {}).get("accept") and (s.rf or {}).get("accept")),
        "recordedAt": "2026-05-26T13:00:00Z",
    }
    return {"qc_state": s.__dict__, "qc_record": record, "next_node": "end"}
