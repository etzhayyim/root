#!/usr/bin/env python3
"""maps — kotoba-native transit reads (ADR-2606064500 R2 aux). stdlib only.

The READ complement to the GTFS aux write path (maps-transit-ontology: :transit.trip/* +
:transit.stop-time/*). These are the kotoba-native successors to the legacy RisingWave
reads `cmdNextDeparturesAtStop` (idx_maps_stop_time_stop_dep) and "all trips on a route"
(idx_maps_trip_route) — each becomes a single AVET probe over the Datom log, sorted client-side.

  next_departures_at_stop(endpoint, stop_id, after, limit):
      AVET(:transit.stop-time/stop, stop_id) → stop-times → filter departure ≥ after →
      sort by :transit.stop-time/departure-time (HH:MM:SS text, sortable) → top N.

  trips_on_route(endpoint, route_id):
      AVET(:transit.trip/route, route_id) → trips.

GTFS departure_time may exceed 24:00:00 (past-midnight trips); it stays textual and sorts
correctly as text within a service day. Fail-soft: any error → empty list.

Usage (library): from transit import next_departures_at_stop
"""
from __future__ import annotations
import json, urllib.request

QUERY_NSID = "com.etzhayyim.apps.kotoba.graph.sparql"
_TIMEOUT = 5


def _avet(endpoint: str, predicate: str, objects, limit: int = 2000) -> list[dict]:
    """One AVET predicate+object probe → entity dicts {id, claims:[{pred,value}]}."""
    body = {"index": "avet", "predicate": predicate, "objects": list(objects), "limit": limit}
    req = urllib.request.Request(
        f"{endpoint.rstrip('/')}/xrpc/{QUERY_NSID}",
        data=json.dumps(body).encode(), headers={"content-type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            return json.loads(r.read()).get("entities", [])
    except Exception:
        return []


def _claims(entity: dict) -> dict[str, str]:
    return {c["pred"]: c["value"] for c in entity.get("claims", []) if c.get("pred")}


def next_departures_at_stop(endpoint: str, stop_id: str,
                            after: str = "00:00:00", limit: int = 10) -> list[dict]:
    """Next scheduled departures at a stop, sorted by departure time (the (a) read pattern).
    Returns [{trip, departure, arrival, headsign, sequence}], earliest first, after >= `after`."""
    rows = []
    for e in _avet(endpoint, "transit.stop-time/stop", [stop_id]):
        c = _claims(e)
        dep = c.get("transit.stop-time/departure-time")
        if not dep or dep < after:
            continue
        rows.append({
            "stopTime": e.get("id"),
            "trip": c.get("transit.stop-time/trip"),
            "departure": dep,
            "arrival": c.get("transit.stop-time/arrival-time"),
            "headsign": c.get("transit.stop-time/headsign"),
            "sequence": c.get("transit.stop-time/sequence"),
        })
    rows.sort(key=lambda r: r["departure"])  # text sort is correct within a service day
    return rows[:limit]


def trips_on_route(endpoint: str, route_id: str, limit: int = 2000) -> list[dict]:
    """All trips on a route (idx_maps_trip_route successor)."""
    out = []
    for e in _avet(endpoint, "transit.trip/route", [route_id], limit):
        c = _claims(e)
        out.append({"trip": e.get("id"), "headsign": c.get("transit.trip/headsign"),
                    "service": c.get("transit.trip/service"),
                    "direction": c.get("transit.trip/direction")})
    return out
