#!/usr/bin/env python3
"""maps — legacy vertex_spatial → kotoba :feature/* normalizer + ingest (R0).

ADR-2606064500. Reads a legacy RisingWave `vertex_spatial` export (the rows the maps Worker
used to `SELECT`) and normalizes each row into a kotoba-EDN `:feature/*` entity, stamps the
H3-cell spatial index (:feature.cell/rN) when an `h3` package is present, and converts to a
`kg.ingest_batch` body for the kotoba Datom log.

This is the WRITE half of the migration (ADR-2606064500 §3/§4). It is the maps counterpart of
watari/methods/ingest.py + kamado/methods/ingest.py.

CONSTITUTIONAL (ADR-2606064500 gates):
  - G4 no-server-key: the live push is a member/operator-DID-signed CACAO batch
    (KOTOBA_AUTH bearer); the maps Worker holds no platform key.
  - G7 outward-gated: live `kg.ingest_batch` push (network) requires BOTH
    MAPS_OPERATOR_GATE=1 (operator attestation) AND an explicit --push flag. Default mode is
    OFFLINE: it normalizes to stdout / an EDN file and tags everything :representative (G3).

stdlib only (real H3 used only if `h3` is installed). Usage:
    python3 ingest.py --export data/ingest/sample-vertex-spatial.json [--out OUTDIR]
    python3 ingest.py --export <f> --push     # refused unless MAPS_OPERATOR_GATE=1 (G7)
"""
from __future__ import annotations
import sys, os, json, math, pathlib, urllib.request

# H3 resolutions the client queries (the app's zoom→LOD ladder) — see ontology §2.
CELL_RESOLUTIONS = (2, 4, 6, 8, 10, 12)

# legacy vertex_spatial.label (PascalCase) → kotoba :feature/label keyword
_LABEL_MAP = {
    "Place": ":place", "Road": ":road", "Railway": ":railway", "Building": ":building",
    "River": ":river", "Lake": ":lake", "Coastline": ":coastline", "AdminArea": ":admin-area",
    "Mountain": ":mountain", "Port": ":port", "Airport": ":airport", "Station": ":station",
    "BusStop": ":bus-stop", "BusRoute": ":bus-route", "SeaRoute": ":sea-route",
    "AirRoute": ":air-route", "LegalEntity": ":legal-entity", "LandRegistry": ":registry",
    "SatelliteScene": ":satellite-scene", "Spot": ":place",
}


def _label(legacy):
    return _LABEL_MAP.get(legacy, ":" + str(legacy).strip().lower().replace(" ", "-"))


def _h3_cell(lat, lon, res):
    import h3
    try:
        return h3.latlng_to_cell(lat, lon, res)       # h3 >= 4
    except AttributeError:
        return h3.geo_to_h3(lat, lon, res)            # h3 == 3


def _stamp_cells(lat, lon):
    """Owning H3 cell at each queryable resolution, or {} when h3 is absent (the TS adapter
    stamps them at ingest in that case — ADR-2606064500 §3)."""
    if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
        return {}, False
    try:
        return {f":feature.cell/r{r}": _h3_cell(lat, lon, r) for r in CELL_RESOLUTIONS}, True
    except Exception:
        return {}, False


def normalize_row(row):
    """One legacy vertex_spatial row → a kotoba :feature/* dict (+ H3 cells if available)."""
    fid = row.get("vertex_id") or row.get("id")
    if not fid:
        return None
    lat, lon = row.get("lat"), row.get("lng", row.get("lon"))
    props = row.get("props")
    if isinstance(props, str):
        try:
            props = json.loads(props)
        except Exception:
            props = {}
    props = props or {}
    feat = {
        ":feature/id": str(fid),
        ":feature/label": _label(row.get("label")),
        ":feature/sourcing": ":representative",  # G3: a migrated export is bounded, not live
    }
    for key, attr in (("name", ":feature/name"), ("display_name", ":feature/display-name"),
                      ("category", ":feature/category"), ("source_did", ":feature/source-did")):
        v = row.get(key)
        if v not in (None, ""):
            feat[attr] = v
    if isinstance(lat, (int, float)):
        feat[":feature/lat"] = lat
    if isinstance(lon, (int, float)):
        feat[":feature/lon"] = lon
    h = props.get("heightM", props.get("height_m"))
    if isinstance(h, (int, float)):
        feat[":feature/height-m"] = float(h)
    lv = props.get("levels", props.get("floors"))
    if isinstance(lv, (int, float)):
        feat[":feature/levels"] = int(lv)
    geom = props.get("geometry")
    if geom is not None:
        feat[":feature/geometry"] = json.dumps(geom, ensure_ascii=False)
    # remaining props → JSON bag (read-through only, never a query key)
    rest = {k: v for k, v in props.items()
            if k not in ("geometry", "heightM", "height_m", "levels", "floors")}
    if rest:
        feat[":feature/props"] = json.dumps(rest, ensure_ascii=False)
    cells, _ = _stamp_cells(lat, lon)
    feat.update(cells)
    return feat


def normalize(export):
    """export = {"rows": [<vertex_spatial row>, ...]} (or a bare list)."""
    rows = export.get("rows", export) if isinstance(export, dict) else export
    feats, stamped, unstamped = {}, 0, 0
    for r in rows:
        f = normalize_row(r)
        if not f:
            continue
        feats[f[":feature/id"]] = f
        if any(k.startswith(":feature.cell/") for k in f):
            stamped += 1
        elif ":feature/lat" in f:
            unstamped += 1
    return feats, stamped, unstamped


def to_kg_batch(feats):
    """:feature/* dicts → kg.ingest_batch body (kamado/watari shape).
    Also stamps :feature/name-token search-index claims (ADR-2606064500 R2; search.py reads
    them via AVET — the name-search successor to vertex_spatial `name LIKE`)."""
    try:
        from search import name_tokens  # same tokenizer the read path uses
    except Exception:
        name_tokens = None
    entities = []
    for fid, f in feats.items():
        claims = [{"pred": k.lstrip(":"), "value": str(v)}
                  for k, v in f.items() if k != ":feature/id" and v not in (None, "")]
        if name_tokens is not None:
            toks = set()
            for nk in (":feature/name", ":feature/display-name"):
                if f.get(nk):
                    toks |= name_tokens(str(f[nk]))
            claims.extend({"pred": "feature/name-token", "value": t} for t in sorted(toks))
        entities.append({
            "id": fid,
            "type": "maps-feature",
            "label_en": f.get(":feature/name") or f.get(":feature/display-name") or fid,
            "claims": claims,
            "relations": [],
        })
    return {"entities": entities}


def _edn_val(v):
    """Serialize a Python value as EDN (keywords kept verbatim, strings quoted)."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        if v.startswith(":"):           # already a keyword
            return v
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return '"' + str(v) + '"'


def render_features_edn(feats):
    """:feature/* dicts → a kotoba-EDN vector (the backfill artifact, R1)."""
    lines = [";; maps — backfilled :feature/* graph (ADR-2606064500 R1).",
             ";; legacy vertex_spatial export normalized to kotoba EAVT, deduped vs seed.",
             "["]
    for fid in sorted(feats):
        f = feats[fid]
        pairs = " ".join(f"{k} {_edn_val(v)}" for k, v in f.items() if v not in (None, ""))
        lines.append(" {" + pairs + "}")
    lines.append("]")
    return "\n".join(lines) + "\n"


def dedup_vs_seed(feats, seed_path):
    """Drop features whose :feature/id already exists in the seed (seed identity wins)."""
    try:
        import analyze
        seed_feats, _, _ = analyze.classify(analyze.load_edn(seed_path))
    except Exception:
        seed_feats = {}
    kept = {fid: f for fid, f in feats.items() if fid not in seed_feats}
    return kept, len(feats) - len(kept)


def push_batch(batch, auth, endpoint, nsid="com.etzhayyim.apps.kotobase.kg.ingest_batch"):
    url = f"{endpoint.rstrip('/')}/xrpc/{nsid}"
    data = json.dumps(batch, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"authorization": f"Bearer {auth}",
                                          "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read().decode("utf-8")


def main(argv):
    if "--export" not in argv:
        sys.exit(__doc__)
    export_path = pathlib.Path(argv[argv.index("--export") + 1])
    export = json.loads(export_path.read_text(encoding="utf-8"))
    feats, stamped, unstamped = normalize(export)
    batch = to_kg_batch(feats)

    print(f"maps ingest (offline, :representative): {len(feats)} features normalized "
          f"({stamped} H3-stamped, {unstamped} await TS-adapter stamping) "
          f"from {export_path.name}")

    actor_root = pathlib.Path(__file__).resolve().parent.parent
    outdir = pathlib.Path(argv[argv.index("--out") + 1]) if "--out" in argv \
        else actor_root / "out"

    if "--emit-edn" in argv:
        # R1 backfill artifact: merged :feature/* EDN, deduped vs the seed (seed identity wins)
        seed_path = actor_root / "data" / "seed-spatial-graph.kotoba.edn"
        kept, dropped = dedup_vs_seed(feats, seed_path)
        outdir.mkdir(parents=True, exist_ok=True)
        dst = outdir / "spatial-graph.backfilled.kotoba.edn"
        dst.write_text(render_features_edn(kept), encoding="utf-8")
        print(f"backfill: {len(kept)} new features (+{dropped} already in seed) → {dst}")
        return

    if "--push" in argv:
        if os.environ.get("MAPS_OPERATOR_GATE") != "1":
            sys.exit("maps G7: live kg.ingest_batch push is Council+operator gated. "
                     "Set MAPS_OPERATOR_GATE=1 with attestation to enable. "
                     "Default offline mode writes the batch locally.")
        auth = os.environ.get("KOTOBA_AUTH")
        endpoint = os.environ.get("KOTOBA_ENDPOINT")
        if not (auth and endpoint):
            sys.exit("maps G4/G7: --push needs KOTOBA_AUTH (member/operator DID bearer) + "
                     "KOTOBA_ENDPOINT. The maps Worker holds no server key (no-server-key).")
        status, body = push_batch(batch, auth, endpoint)
        print(f"pushed {len(batch['entities'])} entities → kotoba [{status}]: {body[:200]}")
        return

    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "features.kg-batch.json").write_text(
        json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {outdir/'features.kg-batch.json'} "
          f"({len(batch['entities'])} entities; --push to ingest, G7-gated)")


if __name__ == "__main__":
    main(sys.argv)
