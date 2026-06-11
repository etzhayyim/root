"""Phase state machine for the nusa fiber_provenance (幣) cell.

The defining G1 cell: a cultivar becomes a fibre-use provenance record ONLY after the
THC-class screen passes. The screen is the third enforcement point of the `:thc-class`
invariant (after the ontology schema and the lexicon `const`).

Invariants enforced:
  G1 — low-THC/fibre-and-ritual-only: :thc-class MUST be one of {fiber, low-thc}. Any
       other value (psychoactive, high-thc, unknown, missing) raises ValueError BEFORE a
       provenance record can exist.
  G2 — non-recreational: the record carries fibre uses only; never a consumption mode.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# G1: the only THC classes for which a provenance record may be produced.
ALLOWED_THC_CLASSES = ("fiber", "low-thc")
# Ritual/industrial fibre uses are the only permitted use kinds (G2).
ALLOWED_FIBER_USES = (
    "shimenawa", "haraegushi", "oonusa", "aratae", "textile", "rope", "paper", "seed-oil-food",
)


class ProvenancePhase(Enum):
    INIT = "init"
    SCREENED = "screened"
    RECORDED = "recorded"


@dataclass
class ProvenanceState:
    phase: str = ProvenancePhase.INIT.value
    cultivar: str = ""
    thc_class: str = "fiber"
    fiber_use: list = field(default_factory=list)
    region: list = field(default_factory=list)
    screened: bool = False
    sourcing: str = "representative"
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> ProvenanceState:
    return ProvenanceState(**d.get("cell_state", {}))


def _norm(cls: str | None) -> str:
    """Normalize an EDN-style keyword (':low-thc') or plain string ('low-thc')."""
    return (cls or "").lstrip(":")


def transition_to_screened(state: dict[str, Any]) -> dict[str, Any]:
    """G1: THC-class screen. Raises ValueError on any non-fibre/low-THC cultivar."""
    cs = _state(state)
    cs.cultivar = state.get("cultivar", cs.cultivar)
    cls = _norm(state.get("thc_class", cs.thc_class))
    if cls not in ALLOWED_THC_CLASSES:
        raise ValueError(
            f"G1 violation: cultivar {cs.cultivar!r} has thc-class {cls!r}; "
            f"only {ALLOWED_THC_CLASSES} permitted. nusa is fibre/ritual-only — "
            f"recreational/high-THC is excluded by construction (no provenance record produced)."
        )
    cs.thc_class = cls
    cs.fiber_use = list(state.get("fiber_use", cs.fiber_use))
    # G2: reject any use that is not a fibre/ritual use (e.g. a consumption mode).
    for u in cs.fiber_use:
        if _norm(u) not in ALLOWED_FIBER_USES:
            raise ValueError(
                f"G2 violation: fibre-use {u!r} is not a permitted fibre/ritual use "
                f"{ALLOWED_FIBER_USES}; nusa emits no consumption/intoxication use."
            )
    cs.region = list(state.get("region", cs.region))
    cs.screened = True
    cs.phase = ProvenancePhase.SCREENED.value
    return {"cell_state": cs.__dict__}


def transition_to_recorded(state: dict[str, Any]) -> dict[str, Any]:
    """Materialize the provenance record (only reachable after the screen passes)."""
    cs = _state(state)
    if not cs.screened:
        raise ValueError("provenance record requires a passed THC-class screen first (G1)")
    cs.payload = {
        "cultivar": cs.cultivar,
        "thcClass": cs.thc_class,
        "fiberUse": cs.fiber_use,
        "region": cs.region,
        "screened": True,
        "sourcing": cs.sourcing,
    }
    cs.phase = ProvenancePhase.RECORDED.value
    return {"cell_state": cs.__dict__}
