"""Recycling intake state machine — ADR-2605261300 phase `eol` (dan).

End-of-life take-back: non-destructive dismantling (reverse of chassis_assembly,
hand tools) → per-material sort → route the Al chassis to kanayama + Li cells to
hikari/recycler → per-material mass balance. Emits
`com.etzhayyim.tsutae.recyclingCertificate`. Closes the G10 take-back loop.

Constitutional guard:
  G10 — material recovery ≥80% by mass by R3; below target is flagged (accept=False)
  so the loss is surfaced rather than hidden.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

G10_RECOVERY_TARGET_PCT = 80.0


class RecyclingPhase(Enum):
    INIT = "init"
    DISMANTLED = "dismantled"
    MATERIALS_SORTED = "materials_sorted"
    KANAYAMA_ROUTED = "kanayama_routed"
    CERTIFICATE_EMITTED = "certificate_emitted"


@dataclass
class RecyclingState:
    phase: RecyclingPhase
    serial: str
    completionPct: int
    dismantle: dict[str, Any] | None = None
    sort: list[dict[str, Any]] | None = None
    recoveryGuard: dict[str, Any] | None = None


def transition_to_dismantled(state: dict[str, Any]) -> dict[str, Any]:
    s = RecyclingState(**state.get("recycling_state", {}))
    s.dismantle = {"method": "hand-tool-reverse", "modules": 9, "destructive": False}
    s.phase = RecyclingPhase.DISMANTLED
    s.completionPct = 25
    return {"recycling_state": s.__dict__, "next_node": "sort"}


def transition_to_materials_sorted(state: dict[str, Any]) -> dict[str, Any]:
    s = RecyclingState(**state.get("recycling_state", {}))
    s.sort = [
        {"material": "aluminum", "massG": 78.0, "route": "kanayama"},
        {"material": "li-cell", "massG": 42.0, "route": "battery-recycler"},
        {"material": "pcb-cu-au", "massG": 18.0, "route": "kanayama"},
        {"material": "glass", "massG": 24.0, "route": "cullet"},
        {"material": "polymer", "massG": 11.0, "route": "pyrolysis"},
    ]
    s.phase = RecyclingPhase.MATERIALS_SORTED
    s.completionPct = 55
    return {"recycling_state": s.__dict__, "next_node": "route"}


def transition_to_kanayama_routed(state: dict[str, Any]) -> dict[str, Any]:
    """G10 enforcement point: recovered-mass fraction vs ≥80% target."""
    s = RecyclingState(**state.get("recycling_state", {}))
    total = float(state.get("totalMassG", 200.0))
    recovered = sum(m["massG"] for m in (s.sort or []))
    pct = round(100.0 * recovered / total, 1) if total else 0.0
    accept = pct >= G10_RECOVERY_TARGET_PCT
    s.recoveryGuard = {
        "gate": "G10",
        "recoveredMassPct": pct,
        "targetPct": G10_RECOVERY_TARGET_PCT,
        "accept": accept,
        "reason": "take-back recovery meets target" if accept
                  else f"recovery {pct}% below {G10_RECOVERY_TARGET_PCT}% target (flagged, not hidden)",
    }
    s.phase = RecyclingPhase.KANAYAMA_ROUTED
    s.completionPct = 80
    return {"recycling_state": s.__dict__, "next_node": "certificate"}


def transition_to_certificate_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = RecyclingState(**state.get("recycling_state", {}))
    s.phase = RecyclingPhase.CERTIFICATE_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.tsutae.recyclingCertificate",
        "serial": s.serial,
        "dismantle": s.dismantle,
        "materialBalance": s.sort,
        "recoveryGuard": s.recoveryGuard,
        "accept": bool((s.recoveryGuard or {}).get("accept")),
        "recordedAt": "2026-05-26T16:00:00Z",
    }
    return {"recycling_state": s.__dict__, "recycling_certificate": record, "next_node": "end"}
