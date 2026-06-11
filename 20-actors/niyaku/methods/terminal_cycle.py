"""terminal_cycle — end-to-end vessel-discharge orchestration.

Ties the four method cores into one deterministic discharge simulation, the
analytic backbone of the cell pipeline (berth → stow → spreader → hoist →
traverse → yard):

  stow_plan        → where each box sits + the no-rehandle discharge order
  crane_dynamics   → per-box hoist + anti-sway traverse time & residual sway
  agv_transfer     → quay-apron → yard legs dispatched across the AGV fleet
  isaac_sway_sim   → (optional) routes the crane traverse through the clean-room
                     isaacsim.core.api Cartpole instead of the analytic model

It returns a `DischargeReport` with the overall discharge time (the max of the
crane-bound and AGV-bound timelines, since they pipeline), terminal productivity
(moves/hour), the worst per-box residual sway, and a per-box ledger.

stdlib-only · pywasm-ready. Pure planning compute; moves no real equipment
(G12 no-server-key / G13 consent-bound).

Per ADR-2606082000 (niyaku R0).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from agv_transfer import Agv, Move, dispatch, travel_time
from crane_dynamics import GantryCrane, simulate_traverse
from stow_plan import Container, StowagePlan, build_stow_plan, discharge_sequence


@dataclass
class YardLayout:
    """Where the yard sits relative to each crane (drives AGV leg distance)."""
    apron_to_yard_m: float = 120.0
    per_row_offset_m: float = 6.0   # extra AGV distance per yard row index


@dataclass
class BoxMoveRecord:
    box_id: str
    crane_time_s: float
    residual_sway_m: float
    agv_id: str
    agv_time_s: float


@dataclass
class DischargeReport:
    records: List[BoxMoveRecord] = field(default_factory=list)
    crane_timeline_s: float = 0.0     # serial crane time (one STS, one box at a time)
    agv_makespan_s: float = 0.0       # parallel AGV fleet finish
    discharge_time_s: float = 0.0     # pipelined overall (max of the two)
    max_residual_sway_m: float = 0.0
    moves: int = 0

    def moves_per_hour(self) -> float:
        if self.discharge_time_s <= 0:
            return 0.0
        return 3600.0 * self.moves / self.discharge_time_s


def _traverse_distance(crane: GantryCrane, slot_row: int) -> float:
    """Ship→shore traverse distance for a box: outreach scaled by how far out in
    the vessel the row sits (outer rows are a longer reach), bounded by the rail.
    """
    base = min(crane.rail_length * 0.5, 25.0)
    return min(crane.rail_length, base + slot_row * 2.0)


def simulate_discharge(
    containers: List[Container],
    rotation: List[str],
    discharge_port: str,
    bays: int,
    rows: int,
    tiers: int,
    crane: Optional[GantryCrane] = None,
    agv: Optional[Agv] = None,
    agv_ids: Optional[List[str]] = None,
    yard: Optional[YardLayout] = None,
    plan: Optional[StowagePlan] = None,
    use_isaac: bool = False,
) -> DischargeReport:
    """Simulate discharging every box bound for ``discharge_port``.

    If ``plan`` is omitted a stow plan is built first. The crane works boxes
    serially in the no-rehandle discharge order; AGVs run the yard legs in
    parallel (dispatched LPT). ``use_isaac=True`` routes each crane traverse
    through the clean-room Isaac Cartpole (falls back to the analytic model if
    the Isaac surface is unavailable).
    """
    crane = crane or GantryCrane()
    agv = agv or Agv()
    agv_ids = agv_ids or ["AGV1", "AGV2", "AGV3"]
    yard = yard or YardLayout()
    plan = plan or build_stow_plan(containers, rotation, bays, rows, tiers)

    by_id = {c.box_id: c for c in containers}
    # only boxes assigned a slot AND bound for this port, in no-rehandle order
    seq = [
        b for b in discharge_sequence(plan, discharge_port)
        if by_id.get(b) and by_id[b].discharge_port == discharge_port
    ]

    isaac_run = None
    if use_isaac:
        try:
            import isaac_sway_sim as _sim
            if _sim.isaac_available():
                isaac_run = _sim.run_sts_transfer
        except Exception:
            isaac_run = None

    crane_timeline = 0.0
    max_sway = 0.0
    moves: List[Move] = []
    records: List[BoxMoveRecord] = []
    for box_id in seq:
        slot = plan.slot_of(box_id)
        dist = _traverse_distance(crane, slot.row)
        if isaac_run is not None:
            rep = isaac_run(x_target=min(dist / 15.0, 2.0), anti_sway=True, steps=4000)
            # Isaac sim is in normalised cart units; use analytic time for the
            # leg but carry the Isaac residual sway (rad → approx lateral m).
            res = simulate_traverse(crane, dist, max_time_s=300.0)
            crane_time = res.settle_time_s
            sway = abs(rep.residual_sway_rad) * crane.cable_length
        else:
            res = simulate_traverse(crane, dist, max_time_s=300.0)
            crane_time = res.settle_time_s
            sway = res.residual_sway_m
        # hoist: up clear of guides (tier-dependent) + down onto AGV
        hoist = (crane.cable_length * 0.4 + slot.tier * 2.6 + 12.0) / 1.5
        crane_time += hoist
        crane_timeline += crane_time
        max_sway = max(max_sway, sway)
        agv_dist = yard.apron_to_yard_m + slot.row * yard.per_row_offset_m
        moves.append(Move(box_id, agv_dist))
        records.append(BoxMoveRecord(box_id, round(crane_time, 2), round(sway, 4),
                                     "", round(travel_time(agv_dist, agv), 2)))

    disp = dispatch(moves, agv_ids, agv)
    # back-fill which AGV took each box
    box_to_agv = {bid: a for a, bids in disp.assignment.items() for bid in bids}
    for r in records:
        r.agv_id = box_to_agv.get(r.box_id, "")

    agv_makespan = disp.makespan()
    return DischargeReport(
        records=records,
        crane_timeline_s=round(crane_timeline, 2),
        agv_makespan_s=round(agv_makespan, 2),
        discharge_time_s=round(max(crane_timeline, agv_makespan), 2),
        max_residual_sway_m=round(max_sway, 4),
        moves=len(records),
    )
