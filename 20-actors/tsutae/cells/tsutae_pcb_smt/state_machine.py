"""PCB SMT state machine — ADR-2605261300 phase `smt` (naphtali).

Surface-mount assembly of the mainboard: component sourcing (open SoC + PMIC +
passives) → G9 open-SoC guard → solder-paste + pick-and-place (Tedama/Otete) →
AOI + solder X-ray (Mimi) → pcbAttestation. Emits `com.etzhayyim.tsutae.pcbAttestation`.

Constitutional guard: G9 (§2(b) anti-IP-locking) — open RISC-V SoC mandatory;
Snapdragon / Apple A / closed Helio / closed Exynos are rejected by construction.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

# G9: open SoC allow-list (R1 third-party open RISC-V; R2+ iwakura). Anything
# not on this list is rejected — proprietary SoC is NEVER permitted (N1).
OPEN_SOC_ALLOWLIST = (
    "StarFive-JH7110",
    "SiFive-HiFive-Unmatched",
    "Allwinner-D1",
    "iwakura",  # silicon Wave 1, R2+
)
PROPRIETARY_SOC_DENYLIST = (
    "Snapdragon",
    "Apple-A",
    "Exynos",
    "Helio",
    "Dimensity",
)


class PcbPhase(Enum):
    INIT = "init"
    COMPONENTS_SOURCED = "components_sourced"
    SOC_GUARD_CHECKED = "soc_guard_checked"
    SMT_PLACED = "smt_placed"
    AOI_PASSED = "aoi_passed"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class PcbState:
    phase: PcbPhase
    boardId: str
    completionPct: int
    components: list[dict[str, Any]] | None = None
    socGuard: dict[str, Any] | None = None
    placements: list[dict[str, Any]] | None = None
    aoi: dict[str, Any] | None = None


def _is_open_soc(soc: str) -> bool:
    if any(soc.startswith(p) for p in PROPRIETARY_SOC_DENYLIST):
        return False
    return any(soc.startswith(a) for a in OPEN_SOC_ALLOWLIST)


def transition_to_components_sourced(state: dict[str, Any]) -> dict[str, Any]:
    s = PcbState(**state.get("pcb_state", {}))
    soc = state.get("soc", "StarFive-JH7110")
    s.components = [
        {"ref": "U1", "kind": "soc", "part": soc, "supplierDid": "did:web:etzhayyim.com:silicon"},
        {"ref": "U2", "kind": "pmic", "part": "open-pmic-r0", "supplierDid": "did:web:etzhayyim.com:silicon"},
        {"ref": "U3", "kind": "lpddr", "part": "LPDDR4X-4GB", "supplierDid": "did:web:etzhayyim.com:silicon"},
        {"ref": "C1..C220", "kind": "passive", "part": "MLCC+R+L", "supplierDid": "representative"},
    ]
    s.phase = PcbPhase.COMPONENTS_SOURCED
    s.completionPct = 15
    return {"pcb_state": s.__dict__, "next_node": "soc_guard"}


def transition_to_soc_guard_checked(state: dict[str, Any]) -> dict[str, Any]:
    """G9 enforcement point: reject any proprietary/closed SoC."""
    s = PcbState(**state.get("pcb_state", {}))
    soc = state.get("soc", "StarFive-JH7110")
    accept = _is_open_soc(soc)
    s.socGuard = {
        "gate": "G9",
        "soc": soc,
        "openSoc": accept,
        "accept": accept,
        "reason": "open RISC-V SoC verified" if accept
                  else "proprietary/closed SoC rejected (§2(b) N1 invariant)",
    }
    s.phase = PcbPhase.SOC_GUARD_CHECKED
    s.completionPct = 30
    return {"pcb_state": s.__dict__, "next_node": "place"}


def transition_to_smt_placed(state: dict[str, Any]) -> dict[str, Any]:
    s = PcbState(**state.get("pcb_state", {}))
    s.placements = [
        {"stage": "solder-paste-stencil", "robot": "robot:tedama"},
        {"stage": "pick-and-place", "robot": "robot:tedama", "componentCount": 224},
        {"stage": "reflow", "profileCid": "bafkreireflow..."},
    ]
    s.phase = PcbPhase.SMT_PLACED
    s.completionPct = 60
    return {"pcb_state": s.__dict__, "next_node": "aoi"}


def transition_to_aoi_passed(state: dict[str, Any]) -> dict[str, Any]:
    s = PcbState(**state.get("pcb_state", {}))
    s.aoi = {
        "robot": "robot:mimi",
        "opticalDefects": 0,
        "xrayVoidPct": 1.8,  # spec < 25% on BGA
        "specVoidLimitPct": 25.0,
        "accept": True,
    }
    s.phase = PcbPhase.AOI_PASSED
    s.completionPct = 85
    return {"pcb_state": s.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = PcbState(**state.get("pcb_state", {}))
    s.phase = PcbPhase.ATTESTATION_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.tsutae.pcbAttestation",
        "boardId": s.boardId,
        "components": s.components,
        "socGuard": s.socGuard,
        "placements": s.placements,
        "aoi": s.aoi,
        "accept": bool((s.socGuard or {}).get("accept") and (s.aoi or {}).get("accept")),
        "recordedAt": "2026-05-26T09:00:00Z",
    }
    return {"pcb_state": s.__dict__, "pcb_attestation": record, "next_node": "end"}
