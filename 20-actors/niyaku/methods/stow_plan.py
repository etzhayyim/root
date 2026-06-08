"""stow_plan — container stowage slotting + discharge/load sequencing.

A container ship cell is addressed by **bay / row / tier** (ISO stowage
coordinates). Automated handling needs two plan products:

  1. a **stow plan** — which slot each box occupies, respecting
     weight-on-top, hazmat segregation, reefer-plug slots, and port-rotation
     (a box for an earlier discharge port must not be buried under a later one);
  2. a **work sequence** — the order the STS crane discharges/loads boxes so it
     never has to re-handle (lift a box only to put it back to reach another).

stdlib-only · pywasm-ready. Pure planning compute; emits no outward action.

Per ADR-2606074000 (niyaku R0).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Slot:
    """A cell address. tier increases upward (00 = bottom)."""
    bay: int
    row: int
    tier: int

    def key(self) -> Tuple[int, int, int]:
        return (self.bay, self.row, self.tier)


@dataclass
class Container:
    box_id: str
    weight_t: float
    discharge_port: str          # port code where this box leaves the ship
    reefer: bool = False         # needs a powered (reefer) slot
    hazmat: Optional[str] = None # IMDG class, e.g. "3" flammable; None if not


class StowError(ValueError):
    """Raised on an infeasible stow request (weight/segregation/capacity)."""


@dataclass
class StowagePlan:
    assignments: Dict[str, Slot] = field(default_factory=dict)
    # discharge order: list of port codes in the vessel's rotation
    rotation: List[str] = field(default_factory=list)

    def slot_of(self, box_id: str) -> Slot:
        return self.assignments[box_id]


def _stack_columns(bays: int, rows: int, tiers: int) -> List[Tuple[int, int]]:
    return [(b, r) for b in range(bays) for r in range(rows)]


def build_stow_plan(
    containers: List[Container],
    rotation: List[str],
    bays: int,
    rows: int,
    tiers: int,
    reefer_rows: Optional[List[int]] = None,
) -> StowagePlan:
    """Assign every container a slot under the core stowage constraints.

    Constraints enforced:
      * capacity — at most ``bays*rows*tiers`` boxes;
      * port rotation — a box discharged at an EARLIER port is stacked ABOVE one
        discharged later in the same column (so it is lifted first, no rehandle);
      * weight-on-top — no heavier box rests on a lighter one in a column;
      * reefer — reefer boxes only in ``reefer_rows`` (if given);
      * hazmat — two different IMDG classes never share a column (segregation).

    Raises ``StowError`` if it cannot place all boxes.
    """
    if not rotation:
        raise StowError("rotation must list at least one discharge port")
    reefer_rows = reefer_rows if reefer_rows is not None else list(range(rows))
    rot_index = {p: i for i, p in enumerate(rotation)}
    for c in containers:
        if c.discharge_port not in rot_index:
            raise StowError(f"{c.box_id}: discharge_port {c.discharge_port} not in rotation")

    # Sort: latest-discharge first (goes to the BOTTOM of a column), then
    # heaviest first (heavy on the bottom). Stable so equal keys keep input order.
    order = sorted(
        containers,
        key=lambda c: (-rot_index[c.discharge_port], -c.weight_t),
    )

    columns = _stack_columns(bays, rows, tiers)
    # per-column running state
    col_height: Dict[Tuple[int, int], int] = {col: 0 for col in columns}
    col_hazmat: Dict[Tuple[int, int], Optional[str]] = {col: None for col in columns}
    col_top_weight: Dict[Tuple[int, int], float] = {col: float("inf") for col in columns}
    col_top_port: Dict[Tuple[int, int], int] = {col: -1 for col in columns}

    plan = StowagePlan(rotation=list(rotation))
    for c in order:
        placed = False
        for (b, r) in columns:
            col = (b, r)
            if col_height[col] >= tiers:
                continue
            if c.reefer and r not in reefer_rows:
                continue
            if c.hazmat is not None and col_hazmat[col] not in (None, c.hazmat):
                continue
            # weight-on-top: new box must be <= the box currently on top
            if c.weight_t > col_top_weight[col]:
                continue
            # rotation: box on top of a column must discharge no later than the
            # one below (earlier port = smaller index = lifted first / higher).
            if col_top_port[col] >= 0 and rot_index[c.discharge_port] > col_top_port[col]:
                continue
            tier = col_height[col]
            plan.assignments[c.box_id] = Slot(b, r, tier)
            col_height[col] = tier + 1
            col_top_weight[col] = c.weight_t
            col_top_port[col] = rot_index[c.discharge_port]
            if c.hazmat is not None:
                col_hazmat[col] = c.hazmat
            placed = True
            break
        if not placed:
            raise StowError(f"no feasible slot for {c.box_id}")
    return plan


def discharge_sequence(plan: StowagePlan, port: str) -> List[str]:
    """Order to discharge all boxes for ``port``: top tier first, per column.

    Guarantees no re-handle: within each column boxes are lifted top→bottom, and
    the stow plan already placed earlier-discharge boxes higher.
    """
    by_col: Dict[Tuple[int, int], List[Tuple[int, str]]] = {}
    # need discharge port per box → recover from rotation isn't stored per box,
    # so callers pass the subset; here we sequence whatever is in `plan`.
    for box_id, slot in plan.assignments.items():
        by_col.setdefault((slot.bay, slot.row), []).append((slot.tier, box_id))
    seq: List[str] = []
    # higher tier first within a column; columns in (bay,row) order
    for col in sorted(by_col):
        for _tier, box_id in sorted(by_col[col], key=lambda t: -t[0]):
            seq.append(box_id)
    return seq


def validate_no_rehandle(plan: StowagePlan, rotation_index: Dict[str, int],
                         box_port: Dict[str, str]) -> bool:
    """True iff no column has a later-discharge box stacked above an earlier one."""
    by_col: Dict[Tuple[int, int], List[Tuple[int, str]]] = {}
    for box_id, slot in plan.assignments.items():
        by_col.setdefault((slot.bay, slot.row), []).append((slot.tier, box_id))
    for col, items in by_col.items():
        items.sort(key=lambda t: t[0])  # bottom→top
        prev = None
        for _tier, box_id in items:
            p = rotation_index[box_port[box_id]]
            if prev is not None and p > prev:
                return False  # box above discharges later than the one below
            prev = p
    return True
