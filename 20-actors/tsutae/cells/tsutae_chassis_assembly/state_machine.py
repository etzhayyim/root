"""Chassis assembly state machine — ADR-2605261300 phase `chassis` (zebulun).

Integrates the PCB into the igata HPDC Al chassis with battery + speaker +
camera module(s) + USB-C + (removable) cellular module — all screw-fastened.
Emits `com.etzhayyim.tsutae.chassisAttestation` with a per-component DID chain.

Constitutional guards:
  G6 (§2(c) anti-surveillance) — microphone HARDWARE kill switch mandatory;
      a chassis without it is rejected.
  G3 (§2(e) repair-rightful) — modular screw-fastened; adhesive ≤5 g/assembly;
      battery + display + camera + USB-C + speaker + SIM + cellular + mic all
      independently replaceable. Excess adhesive / parts-pairing is rejected.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

G3_ADHESIVE_LIMIT_G = 5.0
G3_REQUIRED_REPLACEABLE = (
    "battery", "display", "camera", "usb_c", "speaker", "sim", "cellular", "microphone",
)


class ChassisPhase(Enum):
    INIT = "init"
    COMPONENTS_STAGED = "components_staged"
    MIC_KILLSWITCH_VERIFIED = "mic_killswitch_verified"
    REPAIR_MODULARITY_CHECKED = "repair_modularity_checked"
    CHASSIS_ASSEMBLED = "chassis_assembled"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class ChassisState:
    phase: ChassisPhase
    chassisId: str
    completionPct: int
    components: list[dict[str, Any]] | None = None
    micGuard: dict[str, Any] | None = None
    repairGuard: dict[str, Any] | None = None
    fasteners: dict[str, Any] | None = None


def transition_to_components_staged(state: dict[str, Any]) -> dict[str, Any]:
    s = ChassisState(**state.get("chassis_state", {}))
    s.components = [
        {"slot": "chassis", "part": "igata-Al-HPDC", "did": "did:web:etzhayyim.com:igata"},
        {"slot": "battery", "part": "LFP-3000mAh", "did": "did:web:etzhayyim.com:hikari", "replaceable": True},
        {"slot": "display", "part": "LCD-6.1in", "did": "representative", "replaceable": True},
        {"slot": "camera", "part": "open-isp-12MP", "did": "representative", "replaceable": True},
        {"slot": "usb_c", "part": "USB-C-PD", "did": "representative", "replaceable": True},
        {"slot": "speaker", "part": "8ohm-spk", "did": "representative", "replaceable": True},
        {"slot": "sim", "part": "nano-SIM-tray", "did": "representative", "replaceable": True},
        {"slot": "cellular", "part": "LTE-module-removable", "did": "representative", "replaceable": True},
        {"slot": "microphone", "part": "MEMS-mic", "did": "representative", "replaceable": True},
    ]
    s.phase = ChassisPhase.COMPONENTS_STAGED
    s.completionPct = 15
    return {"chassis_state": s.__dict__, "next_node": "mic_guard"}


def transition_to_mic_killswitch_verified(state: dict[str, Any]) -> dict[str, Any]:
    """G6 enforcement point: a hardware mic kill switch is mandatory."""
    s = ChassisState(**state.get("chassis_state", {}))
    present = state.get("micKillSwitch", True)
    s.micGuard = {
        "gate": "G6",
        "micHardwareKillSwitch": present,
        "cellularRemovable": True,
        "accept": bool(present),
        "reason": "hardware mic kill switch present" if present
                  else "missing hardware mic kill switch (§2(c) N4 invariant)",
    }
    s.phase = ChassisPhase.MIC_KILLSWITCH_VERIFIED
    s.completionPct = 35
    return {"chassis_state": s.__dict__, "next_node": "repair_guard"}


def transition_to_repair_modularity_checked(state: dict[str, Any]) -> dict[str, Any]:
    """G3 enforcement point: modular, low-adhesive, no parts-pairing."""
    s = ChassisState(**state.get("chassis_state", {}))
    adhesive_g = float(state.get("adhesiveGrams", 0.0))
    parts_pairing = bool(state.get("partsPairing", False))
    replaceable = {c["slot"] for c in (s.components or []) if c.get("replaceable")}
    all_replaceable = set(G3_REQUIRED_REPLACEABLE).issubset(replaceable)
    accept = adhesive_g <= G3_ADHESIVE_LIMIT_G and all_replaceable and not parts_pairing
    s.repairGuard = {
        "gate": "G3",
        "adhesiveGrams": adhesive_g,
        "adhesiveLimitG": G3_ADHESIVE_LIMIT_G,
        "allModulesReplaceable": all_replaceable,
        "partsPairing": parts_pairing,
        "accept": accept,
        "reason": "screw-fastened modular, no parts-pairing" if accept
                  else "excess adhesive / non-modular / parts-pairing rejected (§2(e) N7)",
    }
    s.phase = ChassisPhase.REPAIR_MODULARITY_CHECKED
    s.completionPct = 55
    return {"chassis_state": s.__dict__, "next_node": "assemble"}


def transition_to_chassis_assembled(state: dict[str, Any]) -> dict[str, Any]:
    s = ChassisState(**state.get("chassis_state", {}))
    s.fasteners = {"type": "torx-T5", "count": 9, "pentalobe": False, "robot": "robot:otete"}
    s.phase = ChassisPhase.CHASSIS_ASSEMBLED
    s.completionPct = 80
    return {"chassis_state": s.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = ChassisState(**state.get("chassis_state", {}))
    s.phase = ChassisPhase.ATTESTATION_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.tsutae.chassisAttestation",
        "chassisId": s.chassisId,
        "components": s.components,
        "micGuard": s.micGuard,
        "repairGuard": s.repairGuard,
        "fasteners": s.fasteners,
        "accept": bool((s.micGuard or {}).get("accept") and (s.repairGuard or {}).get("accept")),
        "recordedAt": "2026-05-26T10:00:00Z",
    }
    return {"chassis_state": s.__dict__, "chassis_attestation": record, "next_node": "end"}
