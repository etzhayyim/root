"""Phase state machine for the kamado feedstock_guard (竈) cell.

The defining G1 cell: a refining run becomes an admissible synthesis ONLY after the
feedstock-class screen passes. The screen is the third enforcement point of the
`:feedstock/class` invariant (after the ontology schema and the lexicon `const`),
mirrored on nusa's `:thc-class` guard.

Invariants enforced:
  G1 — closed-loop-carbon-only: feedstock-class MUST be one of
       {biogenic, captured-co2, recycled-carbon, existing-inventory-decommission}.
       `fossil-virgin-crude` (or any fossil-extracted source) raises ValueError BEFORE a
       synthesis record can exist — kamado cannot operate a fossil-fed refinery.
  G2 — net-atmospheric-carbon Δ ≤ tolerance: the run carries a carbon balance and is
       admissible only if it passes D3 (renewable-powered + closed-loop carbon).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# G1: the only feedstock classes for which a synthesis run may be produced.
ALLOWED_FEEDSTOCK = ("biogenic", "captured-co2", "recycled-carbon",
                     "existing-inventory-decommission")
ALLOWED_ENERGY = ("hikari-renewable", "grid-mixed")  # G2: renewable for D3; grid only for non-D3 sim
ALLOWED_FATE = ("combusted-fuel", "durable-material")

# physical constant (see methods/carbon_balance.py)
C_PROD = 3.10
PROCESS = {"hikari-renewable": 0.04, "grid-mixed": 0.22}
D3_TOLERANCE = 0.15


class GuardPhase(Enum):
    INIT = "init"
    SCREENED = "screened"
    BALANCED = "balanced"
    ADMITTED = "admitted"


@dataclass
class GuardState:
    phase: str = GuardPhase.INIT.value
    feedstock: str = "biogenic"
    energy: str = "hikari-renewable"
    fate: str = "combusted-fuel"
    screened: bool = False
    net_delta: float = 0.0
    passes_d3: bool = False
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> GuardState:
    return GuardState(**d.get("cell_state", {}))


def _norm(v) -> str:
    return (v or "").lstrip(":") if isinstance(v, str) else str(v)


def transition_to_screened(state: dict[str, Any]) -> dict[str, Any]:
    """G1: feedstock-class screen. Raises ValueError on any fossil feedstock."""
    cs = _state(state)
    cs.feedstock = _norm(state.get("feedstock", cs.feedstock))
    if cs.feedstock not in ALLOWED_FEEDSTOCK:
        raise ValueError(
            f"G1 violation: feedstock-class {cs.feedstock!r} is not representable; "
            f"only {ALLOWED_FEEDSTOCK} permitted. kamado refines closed-loop carbon ONLY — "
            f"fossil-virgin-crude is excluded by construction (no synthesis run produced). "
            f"Robotics cannot neutralize fossil carbon; only the feedstock can."
        )
    cs.energy = _norm(state.get("energy", cs.energy))
    cs.fate = _norm(state.get("fate", cs.fate))
    if cs.fate not in ALLOWED_FATE:
        raise ValueError(f"unknown product fate {cs.fate!r}")
    cs.screened = True
    cs.phase = GuardPhase.SCREENED.value
    return {"cell_state": cs.__dict__}


def transition_to_balanced(state: dict[str, Any]) -> dict[str, Any]:
    """G2/D3: compute the net atmospheric carbon Δ (mirror of carbon_balance.balance)."""
    cs = _state(state)
    if not cs.screened:
        raise ValueError("carbon balance requires a passed feedstock screen first (G1)")
    origin = -C_PROD if cs.feedstock in ("biogenic", "captured-co2") else (
        -C_PROD * 0.85 if cs.feedstock == "recycled-carbon" else 0.0)
    process = PROCESS.get(cs.energy, 0.22)
    fate = C_PROD if cs.fate == "combusted-fuel" else 0.0
    cs.net_delta = round(origin + process + fate, 3)
    cs.passes_d3 = cs.net_delta <= D3_TOLERANCE
    cs.phase = GuardPhase.BALANCED.value
    return {"cell_state": cs.__dict__}


def transition_to_admitted(state: dict[str, Any]) -> dict[str, Any]:
    """A synthesis run is admissible only if it is closed-loop AND passes D3."""
    cs = _state(state)
    if not cs.passes_d3:
        raise ValueError(
            f"G2 violation: net atmospheric Δ {cs.net_delta:+.2f} tCO2e/t > {D3_TOLERANCE}; "
            f"design does not pass D3 (use renewable energy + closed-loop carbon / lock the carbon)."
        )
    cs.payload = {
        "feedstockClass": cs.feedstock, "energy": cs.energy, "productFate": cs.fate,
        "netDeltaTco2ePerT": cs.net_delta, "passesD3": True, "screened": True,
    }
    cs.phase = GuardPhase.ADMITTED.value
    return {"cell_state": cs.__dict__}
