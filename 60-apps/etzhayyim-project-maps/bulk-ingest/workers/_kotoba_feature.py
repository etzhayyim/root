"""_kotoba_feature — vertex_spatial row → kotoba :feature/* mapping for the bulk-ingest dumpers.

ADR-2606064500 (R2). The canonical legacy-row → kotoba Datom shape used by the `kotoba`
substrate-writer mode. Kept in lockstep with `20-actors/maps/methods/ingest.py` (_LABEL_MAP)
and `maps-spatial-ontology.kotoba.edn` (`:feature/label` keywords); a test asserts the label
map matches the canonical one so the two write paths (the maps Worker adapter + the bulk
dumpers) never disagree on a stored keyword.

stdlib only; real H3 cells stamped when an `h3` package is importable, else deferred (the cell
index is stamped wherever h3 is available — the maps adapter or a dumper image that ships h3).
"""
from __future__ import annotations
import json
from typing import Any, Iterable

# H3 resolutions the maps client queries (the zoom→LOD ladder; ontology §2).
CELL_RESOLUTIONS = (2, 4, 6, 8, 10, 12)

# legacy vertex_spatial.label (PascalCase) → kotoba :feature/label keyword.
# MUST equal 20-actors/maps/methods/ingest.py _LABEL_MAP (asserted by test_kotoba_substrate.py).
_LABEL_MAP = {
    "Place": ":place", "Road": ":road", "Railway": ":railway", "Building": ":building",
    "River": ":river", "Lake": ":lake", "Coastline": ":coastline", "AdminArea": ":admin-area",
    "Mountain": ":mountain", "Port": ":port", "Airport": ":airport", "Station": ":station",
    "BusStop": ":bus-stop", "BusRoute": ":bus-route", "SeaRoute": ":sea-route",
    "AirRoute": ":air-route", "LegalEntity": ":legal-entity", "LandRegistry": ":registry",
    "SatelliteScene": ":satellite-scene", "Spot": ":place",
}


def fold_label(label: Any) -> str:
    """Legacy PascalCase label → :feature/label keyword (lowercase-kebab)."""
    if not label:
        return ":unknown"
    s = str(label)
    if s.startswith(":"):
        return s
    return _LABEL_MAP.get(s, ":" + s.strip().lower().replace(" ", "-"))


def stamp_cells(lat: Any, lon: Any) -> dict[str, str]:
    """Owning H3 cell at each queryable resolution, or {} when h3 is absent / coords missing.
    Uses latlng_to_cell DIRECTLY at each res (matches the TS adapter + ingest.py; H3 is not
    perfectly hierarchical, so stamp and query must use the same method)."""
    if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
        return {}
    try:
        import h3
        def cell(r):
            try:
                return h3.latlng_to_cell(lat, lon, r)   # h3 >= 4
            except AttributeError:
                return h3.geo_to_h3(lat, lon, r)        # h3 == 3
        return {f"feature.cell/r{r}": cell(r) for r in CELL_RESOLUTIONS}
    except Exception:
        return {}


_PROMOTED = ("geometry", "heightM", "height_m", "levels", "floors")


def row_to_entity(row: dict[str, Any]) -> dict[str, Any] | None:
    """One vertex_spatial row dict → a kg.ingest_batch entity {id, type, label_en, claims}."""
    fid = row.get("vertex_id") or row.get("id")
    if not fid:
        return None
    lat = row.get("lat")
    lon = row.get("lng", row.get("lon"))
    props = row.get("props")
    if isinstance(props, str):
        try:
            props = json.loads(props)
        except Exception:
            props = {}
    props = props or {}

    claims: list[dict[str, str]] = [
        {"pred": "feature/label", "value": fold_label(row.get("label"))},
        {"pred": "feature/sourcing", "value": ":representative"},  # G3 — a bulk feed is bounded
    ]

    def add(pred: str, value: Any) -> None:
        if value not in (None, ""):
            claims.append({"pred": pred, "value": str(value)})

    add("feature/name", row.get("name"))
    add("feature/display-name", row.get("display_name"))
    add("feature/category", row.get("category"))
    add("feature/source-did", row.get("source_did"))
    if isinstance(lat, (int, float)):
        add("feature/lat", lat)
    if isinstance(lon, (int, float)):
        add("feature/lon", lon)
    h = props.get("heightM", props.get("height_m"))
    if isinstance(h, (int, float)):
        add("feature/height-m", float(h))
    lv = props.get("levels", props.get("floors"))
    if isinstance(lv, (int, float)):
        add("feature/levels", int(lv))
    geom = props.get("geometry")
    if geom is not None:
        add("feature/geometry", json.dumps(geom, ensure_ascii=False))
    rest = {k: v for k, v in props.items() if k not in _PROMOTED}
    if rest:
        add("feature/props", json.dumps(rest, ensure_ascii=False))
    for k, v in stamp_cells(lat, lon).items():
        add(k, v)

    return {
        "id": str(fid),
        "type": "maps-feature",
        "label_en": row.get("name") or row.get("display_name") or str(fid),
        "claims": claims,
        "relations": [],
    }


def rows_to_batch(rows: Iterable[dict[str, Any]]) -> dict[str, list]:
    """vertex_spatial rows → a kg.ingest_batch body."""
    entities = [e for e in (row_to_entity(r) for r in rows) if e is not None]
    return {"entities": entities}
