"""pooled_route — ainori multi-stop pooled sequencing, REUSING the todoke route core.

Per ADR-2606071500 (and the manifest `:actor/reuses` claim). ainori does NOT ship a second
routing engine: it reuses todoke's `methods/last_mile` sequencing primitives (`Stop`,
`_nearest_neighbour`, `_two_opt` — themselves the Python mirror of the Rust `todoke-route`
crate, sumitsubo pattern). The parity test pins ainori's `sequence_stops` to todoke's
`plan_last_mile` order on a shared fixture, so the two cannot drift.

The ONE thing ainori does NOT inherit from todoke is the *safety envelope*: todoke's ODD is
pedestrian (sidewalk/crosswalk/doorpath/bikelane; `road` is refused), while ainori is
VEHICULAR. ainori keeps its own SAE-L4 vehicular envelope in agent.py (G3) and reuses only the
geometric stop-sequencing. Sequencing has no charter content; the envelope does — so only the
envelope is actor-specific.
"""
from __future__ import annotations

import os
import sys

# Reuse the todoke route core (one sequencer, not a second engine).
_TODOKE_METHODS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "todoke", "methods")
)
if _TODOKE_METHODS not in sys.path:
    sys.path.insert(0, _TODOKE_METHODS)

from last_mile import (  # type: ignore  # noqa: E402  (todoke route core — reused, not reimplemented)
    Stop,
    _nearest_neighbour,
    _two_opt,
    plan_last_mile,
)


def sequence_stops(stops: list) -> tuple[list, float]:
    """Order a list of Stops (stops[0] pinned as origin) and return (order_of_ids, length_m).

    This IS todoke's sequencing core — the same `_nearest_neighbour` + `_two_opt` primitives the
    Rust crate mirrors. The parity test asserts it matches `todoke.plan_last_mile` order, so
    ainori provably reuses rather than reimplements the engine. No safety envelope is applied
    here (sequencing is charter-neutral; ainori's vehicular envelope lives in agent.py, G3)."""
    if not stops:
        return [], 0.0
    seq = _two_opt(_nearest_neighbour(stops), stops)
    length = sum(stops[seq[i]].dist(stops[seq[i + 1]]) for i in range(len(seq) - 1))
    return [stops[i].id for i in seq], length


def pooled_route(carrier_origin: tuple, rider_points: list) -> dict:
    """Build a pooled vehicular route: the carrier's origin (id 0) plus each rider's pickup /
    dropoff point, sequenced by the reused todoke core to minimise added distance (G11 — fill a
    trip already happening). `carrier_origin` is (x, y); `rider_points` is a list of
    {id, x, y, zone}. Returns {order, lengthM, occupancy}."""
    stops = [Stop(0, float(carrier_origin[0]), float(carrier_origin[1]), "arterial")]
    for p in rider_points:
        stops.append(Stop(int(p["id"]), float(p["x"]), float(p["y"]), p.get("zone", "arterial")))
    order, length = sequence_stops(stops)
    return {"order": order, "lengthM": length, "occupancy": len(rider_points)}
