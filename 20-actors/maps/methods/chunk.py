#!/usr/bin/env python3
"""maps — kotoba-native chunk read (ADR-2606064500 §2). stdlib only.

The HTTP Python reference for `cmdGetChunk` — the maps-3d / 2D-overlay hot-path. It completes
the read-surface symmetry: transit.py / search.py / reverse.py each have an HTTP reader; this
is the cell-chunk one (previously only the TS adapter `queryByCells` + the in-memory
`kotoba_local` proved it). Same AVET cell probe, same grouped-GeoJSON output shape as the
legacy getChunk, so a kotoba-served chunk is drop-in for the KAMI renderer.

  get_chunk(endpoint, h3_cells, lod, labels, limit):
      AVET(:feature.cell/r{lod}, h3_cells)  → candidates
      → group by the feature's owning r{lod} cell → by :feature/label → GeoJSON Feature[]
      (per-label per-cell cap = limit). Returns {chunks: {cell: {label: [...]}}, lod, total}.

Fail-soft: any error → empty chunks. Labels are folded to the stored kebab keyword.
"""
from __future__ import annotations
import json, urllib.request

QUERY_NSID = "com.etzhayyim.apps.kotoba.graph.sparql"
_TIMEOUT = 5

# legacy PascalCase label → :feature/label keyword (subset; mirrors search/_kotoba_feature).
_LABEL_MAP = {
    "Place": ":place", "Road": ":road", "Railway": ":railway", "Building": ":building",
    "River": ":river", "Lake": ":lake", "Coastline": ":coastline", "AdminArea": ":admin-area",
    "Mountain": ":mountain", "Port": ":port", "Airport": ":airport", "Station": ":station",
    "BusStop": ":bus-stop", "BusRoute": ":bus-route", "SeaRoute": ":sea-route",
    "AirRoute": ":air-route", "LegalEntity": ":legal-entity", "LandRegistry": ":registry",
}


def fold_label(label: str) -> str:
    if label.startswith(":"):
        return label
    return _LABEL_MAP.get(label, ":" + label.strip().lower().replace(" ", "-"))


def _avet(endpoint, predicate, objects, limit=8000):
    body = {"index": "avet", "predicate": predicate, "objects": list(objects), "limit": limit}
    req = urllib.request.Request(
        f"{endpoint.rstrip('/')}/xrpc/{QUERY_NSID}",
        data=json.dumps(body).encode(), headers={"content-type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            return json.loads(r.read()).get("entities", [])
    except Exception:
        return []


def _feature(entity, lod):
    """A matching entity → (owning-cell, label, GeoJSON Feature)."""
    c = {}
    for cl in entity.get("claims", []):
        p, v = cl.get("pred"), cl.get("value")
        if p:
            c.setdefault(p, v)  # first wins (cell attrs are single-valued; name-token is many)
    owner = c.get(f"feature.cell/r{lod}")
    label = c.get("feature/label")
    geom = None
    if c.get("feature/geometry"):
        try:
            geom = json.loads(c["feature/geometry"])
        except Exception:
            geom = None
    if geom is None and c.get("feature/lat") and c.get("feature/lon"):
        try:
            geom = {"type": "Point", "coordinates": [float(c["feature/lon"]), float(c["feature/lat"])]}
        except (TypeError, ValueError):
            geom = None
    feat = {
        "type": "Feature", "geometry": geom,
        "properties": {"id": entity.get("id"), "name": c.get("feature/name"),
                       "label": label, "category": c.get("feature/category"),
                       "heightM": c.get("feature/height-m"), "levels": c.get("feature/levels")},
    }
    return owner, label, feat


def get_chunk(endpoint, h3_cells, lod, labels=None, limit=500):
    """getChunk-equivalent: per requested cell, the features owning it, grouped by label."""
    cells = list(dict.fromkeys(str(c) for c in h3_cells))  # dedup, keep order
    want = {fold_label(str(l)) for l in labels} if labels else None
    chunks = {c: {} for c in cells}
    cellset = set(cells)
    total = 0
    for e in _avet(endpoint, f"feature.cell/r{int(lod)}", cells):
        owner, label, feat = _feature(e, int(lod))
        if owner not in cellset or not label:
            continue
        if want is not None and label not in want:
            continue
        bucket = chunks[owner].setdefault(label, [])
        if len(bucket) >= limit:
            continue
        bucket.append(feat)
        total += 1
    return {"chunks": chunks, "lod": int(lod), "total": total}
