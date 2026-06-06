#!/usr/bin/env python3
"""maps — kotoba-native reverse geocoding (ADR-2606064500 R2). stdlib (real H3 if installed).

The kotoba-native successor to `cmdPlaceReverseGeocode` (legacy: bbox SELECT around the point,
nearest by distance). kotoba has no bbox scan — but the H3-cell index IS a proximity index:
the query point's owning cell + its grid_disk ring bound the candidate set, then haversine
ranks them. O(ring cells), no scan.

  reverse_geocode(endpoint, lat, lon, res, ring, labels, limit):
      cell  = latlng_to_cell(lat, lon, res)
      cells = grid_disk(cell, ring)                       # the point's cell + `ring` rings
      cands = AVET(:feature.cell/r{res}, cells)           # candidates (one index probe set)
      → haversine(point, candidate) → label-filter → sort nearest-first → top N.

Needs `h3` for the cell+ring (the maps adapter / a dumper image ship it); without it, returns
[] (the haversine ranker itself is pure and always testable). Fail-soft: any error → [].

Usage (library): from reverse import reverse_geocode, haversine_m
"""
from __future__ import annotations
import json, math, urllib.request

QUERY_NSID = "com.etzhayyim.apps.kotoba.graph.sparql"
_TIMEOUT = 5
_EARTH_R = 6_371_000.0  # mean Earth radius, metres


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two WGS84 points, in metres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * _EARTH_R * math.asin(min(1.0, math.sqrt(a)))


def _ring_cells(lat: float, lon: float, res: int, ring: int):
    """The point's owning H3 cell + `ring` rings around it, or None if h3 is unavailable."""
    try:
        import h3
        try:
            cell = h3.latlng_to_cell(lat, lon, res)          # h3 >= 4
            return list(h3.grid_disk(cell, ring))
        except AttributeError:
            cell = h3.geo_to_h3(lat, lon, res)               # h3 == 3
            return list(h3.k_ring(cell, ring))
    except Exception:
        return None


def _avet(endpoint: str, predicate: str, objects, limit: int = 4000) -> list[dict]:
    body = {"index": "avet", "predicate": predicate, "objects": list(objects), "limit": limit}
    req = urllib.request.Request(
        f"{endpoint.rstrip('/')}/xrpc/{QUERY_NSID}",
        data=json.dumps(body).encode(), headers={"content-type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            return json.loads(r.read()).get("entities", [])
    except Exception:
        return []


def reverse_geocode(endpoint: str, lat: float, lon: float, *, res: int = 10, ring: int = 2,
                    labels=None, limit: int = 5) -> list[dict]:
    """Nearest features to (lat, lon), nearest first. Returns
    [{id, name, label, lat, lon, distanceM}]. Empty if h3 absent or nothing in range."""
    cells = _ring_cells(lat, lon, res, ring)
    if not cells:
        return []
    want = None
    if labels:
        want = {l if str(l).startswith(":") else f":{l}" for l in labels}
    out = []
    for e in _avet(endpoint, f"feature.cell/r{res}", cells):
        flat = None
        flon = None
        name = None
        label = None
        for c in e.get("claims", []):
            p, v = c.get("pred"), c.get("value")
            if p == "feature/lat":
                try: flat = float(v)
                except (TypeError, ValueError): pass
            elif p == "feature/lon":
                try: flon = float(v)
                except (TypeError, ValueError): pass
            elif p == "feature/name":
                name = v
            elif p == "feature/label":
                label = v
        if flat is None or flon is None:
            continue
        if want is not None and label not in want:
            continue
        out.append({"id": e.get("id"), "name": name, "label": label,
                    "lat": flat, "lon": flon, "distanceM": round(haversine_m(lat, lon, flat, flon), 1)})
    out.sort(key=lambda r: r["distanceM"])
    return out[:limit]
