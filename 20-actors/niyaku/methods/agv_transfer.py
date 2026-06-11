"""agv_transfer — automated guided vehicle (AGV) horizontal-transport core.

After the STS crane lands a box on the quay apron, a battery AGV carries it to
the yard stack. This module is the planning core behind the `yard_transfer` cell:

  * a **trapezoidal velocity profile** (accel → cruise → decel, or a triangular
    profile when the leg is too short to reach cruise) giving time-optimal,
    jerk-bounded travel time over a leg;
  * a **lane-segment conflict check** — two AGVs sharing a one-way segment must
    not have overlapping occupancy time windows (deadlock/collision avoidance);
  * a **greedy dispatch** that assigns moves to a fleet to minimise makespan.

stdlib-only · pywasm-ready. Pure planning compute; dispatches no real vehicle
(G12 no-server-key / G13 consent-bound).

Per ADR-2606082000 (niyaku R0).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class Agv:
    """Battery AGV kinematic envelope (electric, regenerative braking — G8)."""
    v_max: float = 6.0      # m/s
    a_max: float = 0.8      # m/s² (accel = decel)
    length_m: float = 16.0  # AGV + 40ft box footprint, for segment occupancy


def travel_time(distance_m: float, agv: Agv) -> float:
    """Time-optimal travel time over a straight leg under a trapezoidal profile.

    If the leg is long enough to reach ``v_max`` the profile is accel/cruise/
    decel; otherwise it is a symmetric triangular accel/decel that peaks below
    ``v_max``.
    """
    if distance_m < 0:
        raise ValueError("distance must be non-negative")
    if distance_m == 0:
        return 0.0
    a = agv.a_max
    v = agv.v_max
    d_to_vmax = v * v / a            # distance to accel to v_max then decel to 0
    if distance_m >= d_to_vmax:
        t_ramp = v / a               # accel + symmetric decel
        d_cruise = distance_m - d_to_vmax
        return 2.0 * t_ramp + d_cruise / v
    # triangular: peak velocity vp = sqrt(a * d); total t = 2 vp / a
    vp = math.sqrt(a * distance_m)
    return 2.0 * vp / a


@dataclass
class SegmentReservation:
    """One AGV's occupancy of a named one-way lane segment over [t_in, t_out]."""
    segment: str
    agv_id: str
    t_in: float
    t_out: float


def reservations_conflict(r1: SegmentReservation, r2: SegmentReservation) -> bool:
    """True iff two reservations share a segment and overlap in time.

    Touching at an endpoint (t_out == t_in) is NOT a conflict (one clears as the
    other enters). Different segments never conflict.
    """
    if r1.segment != r2.segment or r1.agv_id == r2.agv_id:
        return False
    return r1.t_in < r2.t_out and r2.t_in < r1.t_out


def find_conflicts(reservations: List[SegmentReservation]) -> List[Tuple[int, int]]:
    """All conflicting index pairs (i<j) in a reservation list."""
    out: List[Tuple[int, int]] = []
    for i in range(len(reservations)):
        for j in range(i + 1, len(reservations)):
            if reservations_conflict(reservations[i], reservations[j]):
                out.append((i, j))
    return out


@dataclass
class Move:
    move_id: str
    distance_m: float


@dataclass
class DispatchResult:
    # agv_id -> ordered list of move_ids
    assignment: Dict[str, List[str]] = field(default_factory=dict)
    # agv_id -> total busy time (s)
    finish_time: Dict[str, float] = field(default_factory=dict)

    def makespan(self) -> float:
        return max(self.finish_time.values()) if self.finish_time else 0.0


def dispatch(moves: List[Move], agv_ids: List[str], agv: Agv) -> DispatchResult:
    """Greedy makespan-minimising assignment: each move (longest-first) goes to
    the AGV that is currently free earliest (LPT — longest-processing-time rule).
    """
    if not agv_ids:
        raise ValueError("need at least one AGV")
    res = DispatchResult(
        assignment={a: [] for a in agv_ids},
        finish_time={a: 0.0 for a in agv_ids},
    )
    for mv in sorted(moves, key=lambda m: -m.distance_m):
        # pick the AGV that frees up soonest
        a = min(agv_ids, key=lambda x: res.finish_time[x])
        res.assignment[a].append(mv.move_id)
        res.finish_time[a] += travel_time(mv.distance_m, agv)
    return res
