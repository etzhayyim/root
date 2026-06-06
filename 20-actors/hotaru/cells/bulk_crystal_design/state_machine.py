"""Phase state machine for the hotaru bulk_crystal_design (蛍) cell.

Single-crystal InP boule growth DESIGN (LEC / VGF / VB). Assembles a crystalGrowthDesign
record from a growth method + dopant + target wafer + In-sourcing — and STRUCTURALLY
forbids representing a physically grown crystal.

Invariants enforced:
  G2 — design-only/not-fabricated: the design's `fabricated` is forced to False; any
       attempt to set it true raises ValueError. A grown boule is unrepresentable
       through R3 (III-V fabrication PROHIBITED, ADR-2605265500 §2).
  G4 — conflict-mineral sourcing: InP consumes In (a conflict-mineral); :in-sourcing
       MUST be in {recycled, conflict-free-attested}; :unverified raises ValueError.
  G1-adjacent — the growth method must be a known OPEN bulk-growth method (LEC/VGF/VB);
       epitaxy methods (movpe/mbe) are NOT bulk-growth and are refused here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Open bulk single-crystal growth methods (the substrate-generation stage). MOVPE/MBE
# are epitaxy, not bulk growth, and are refused (kept out of hotaru's substrate scope).
ALLOWED_METHODS = ("lec", "vgf", "vertical-bridgman")
CLEAN_SOURCING = ("recycled", "conflict-free-attested")
KNOWN_DOPANTS = ("sulfur", "iron", "tin", "zinc", "undoped")


class GrowthPhase(Enum):
    INIT = "init"
    SCREENED = "screened"
    DESIGNED = "designed"


@dataclass
class GrowthState:
    phase: str = GrowthPhase.INIT.value
    crystal_id: str = ""
    material: str = "inp"
    method: str = "lec"
    dopant: str = "undoped"
    target_wafer: str = ""
    in_sourcing: str = "conflict-free-attested"
    fabricated: bool = False
    screened: bool = False
    sourcing: str = "representative"
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> GrowthState:
    return GrowthState(**d.get("cell_state", {}))


def _norm(v: str | None) -> str:
    return (v or "").lstrip(":")


def transition_to_screened(state: dict[str, Any]) -> dict[str, Any]:
    """G2/G4/method screen. Raises before a design can exist on any violation."""
    cs = _state(state)
    cs.crystal_id = state.get("crystal_id", cs.crystal_id)
    cs.material = _norm(state.get("material", cs.material)) or "inp"

    # G2: fabricated is structurally false; reject any true value outright.
    fab = state.get("fabricated", cs.fabricated)
    if fab is not False:
        raise ValueError(
            f"G2 violation: crystal {cs.crystal_id!r} cannot be :fabricated {fab!r}; "
            f"only false is permitted (III-V fabrication PROHIBITED through R3, "
            f"ADR-2605265500 §2 — a grown boule is unrepresentable)."
        )
    cs.fabricated = False

    method = _norm(state.get("method", cs.method))
    if method not in ALLOWED_METHODS:
        raise ValueError(
            f"bulk-growth method {method!r} not in {ALLOWED_METHODS}; epitaxy methods "
            f"(movpe/mbe) are not bulk crystal growth and are out of substrate scope."
        )
    cs.method = method

    # G4: In/Ga conflict-mineral sourcing must be clean.
    insrc = _norm(state.get("in_sourcing", cs.in_sourcing))
    if insrc not in CLEAN_SOURCING:
        raise ValueError(
            f"G4 violation: crystal {cs.crystal_id!r} :in-sourcing {insrc!r}; clean "
            f"sourcing {CLEAN_SOURCING} required (inherits hikari/himawari §G2)."
        )
    cs.in_sourcing = insrc

    dopant = _norm(state.get("dopant", cs.dopant))
    if dopant not in KNOWN_DOPANTS:
        raise ValueError(f"unknown dopant {dopant!r}; expected one of {KNOWN_DOPANTS}")
    cs.dopant = dopant
    cs.target_wafer = state.get("target_wafer", cs.target_wafer)
    cs.screened = True
    cs.phase = GrowthPhase.SCREENED.value
    return {"cell_state": cs.__dict__}


def transition_to_designed(state: dict[str, Any]) -> dict[str, Any]:
    """Materialize the crystalGrowthDesign record (only after the screen passes)."""
    cs = _state(state)
    if not cs.screened:
        raise ValueError("growth design requires a passed G2/G4 screen first")
    cs.payload = {
        "crystalId": cs.crystal_id,
        "material": cs.material,
        "method": cs.method,
        "dopant": cs.dopant,
        "targetWafer": cs.target_wafer,
        "inSourcing": cs.in_sourcing,
        "fabricated": False,  # G2 — invariant, never true
        "sourcing": cs.sourcing,
    }
    cs.phase = GrowthPhase.DESIGNED.value
    return {"cell_state": cs.__dict__}
