#!/usr/bin/env python3
"""osm_to_citymesh — OpenStreetMap (Overpass `out geom`) → e7m-sim city scene
+ a kotoba (datomic) EAVT asset-registry transaction.

Projects OSM into local ENU metres (origin = bbox centre, z-up) and emits:
  1. <out.scene.json> — buildings (footprint AABB + height), roads (polylines +
     width), and POINT OBJECTS (poles / street-lamps / traffic-signals / trees /
     hydrants / benches …) the kami-genesis Shibuya sim renders + makes clickable.
  2. <out>.assets.edn — a kotoba/datomic transaction (entity maps) registering
     EVERY object as an asset entity with :asset/kind :asset/installYear
     :asset/company :asset/costJpy :geo/* :osm/id, loadable via the kotoba EAVT
     store (kotoba-datomic transact).
  3. <out>.assets.schema.edn — the attribute schema.

Data provenance: position / kind / OSM `operator`→company / `start_date`→year /
`height` are REAL (OpenStreetMap, ODbL). installYear / company / costJpy that
OSM does not carry are DETERMINISTICALLY SYNTHESIZED from the OSM id (plausible,
reproducible) and flagged `:asset/dataProvenance "synthesized-demo"` so a real
municipal asset-management DB can later overwrite them.

Usage:
  python3 osm_to_citymesh.py <in.osm.json> <out.scene.json> [name]
"""
import json
import math
import sys

# Synthesis tables (clearly NOT authoritative — placeholder until a real asset DB).
COMPANY_BY_KIND = {
    "building": ["三井不動産", "東急不動産", "住友不動産", "野村不動産", "森ビル"],
    "road": "東京都建設局",
    "traffic_signals": "警視庁 交通管制",
    "street_lamp": "東京電力パワーグリッド",
    "utility_pole": "東京電力パワーグリッド",
    "tree": "渋谷区 みどり公園課",
    "fire_hydrant": "東京消防庁",
    "bench": "渋谷区",
    "vending_machine": "ダイドードリンコ",
    "telephone": "NTT東日本",
    "waste_basket": "渋谷区",
    "drinking_water": "渋谷区水道局",
    "advertising": "東急エージェンシー",
    "_default": "渋谷区",
}
INSTALL_BASE = {
    "building": 1985, "road": 1970, "traffic_signals": 1998, "tree": 2005,
    "street_lamp": 2000, "utility_pole": 1992, "fire_hydrant": 1995,
    "bench": 2008, "vending_machine": 2012, "telephone": 1990,
    "waste_basket": 2010, "drinking_water": 2002, "advertising": 2015, "_default": 2000,
}
COST_FLAT_JPY = {
    "traffic_signals": 3_500_000, "tree": 280_000, "street_lamp": 240_000,
    "utility_pole": 180_000, "fire_hydrant": 420_000, "bench": 90_000,
    "vending_machine": 550_000, "telephone": 350_000, "waste_basket": 45_000,
    "drinking_water": 380_000, "advertising": 1_200_000, "_default": 150_000,
}
RENDER_H = {
    "traffic_signals": 5.0, "street_lamp": 5.5, "utility_pole": 9.0, "tree": 6.0,
    "fire_hydrant": 0.7, "bench": 0.5, "vending_machine": 1.8, "telephone": 1.4,
    "waste_basket": 0.8, "drinking_water": 1.0, "advertising": 3.5, "_default": 2.0,
}


def resolve_height(tags):
    h = tags.get("height")
    if h:
        try:
            return max(3.0, min(200.0, float(str(h).split()[0].replace("m", ""))))
        except ValueError:
            pass
    lv = tags.get("building:levels")
    if lv:
        try:
            return max(3.0, min(200.0, float(lv) * 3.3))
        except ValueError:
            pass
    return 12.0


def road_width(tags):
    lanes = tags.get("lanes")
    if lanes:
        try:
            return max(2.5, float(lanes) * 3.25)
        except ValueError:
            pass
    return {
        "motorway": 14.0, "trunk": 12.0, "primary": 12.0, "secondary": 9.0,
        "tertiary": 7.0, "residential": 5.5, "living_street": 5.0,
        "service": 4.0, "pedestrian": 6.0, "footway": 2.5, "path": 2.0,
        "cycleway": 2.5, "steps": 2.0,
    }.get(tags.get("highway", ""), 5.0)


def node_kind(tags):
    if tags.get("natural") == "tree":
        return "tree"
    if tags.get("highway") == "traffic_signals":
        return "traffic_signals"
    if tags.get("highway") == "street_lamp" or tags.get("man_made") == "street_lamp":
        return "street_lamp"
    if tags.get("power") in ("pole", "tower") or tags.get("man_made") == "utility_pole":
        return "utility_pole"
    if tags.get("emergency") == "fire_hydrant":
        return "fire_hydrant"
    if tags.get("amenity"):
        return tags["amenity"]
    if tags.get("advertising"):
        return "advertising"
    if tags.get("man_made"):
        return tags["man_made"]
    return None


def start_year(tags):
    sd = tags.get("start_date") or tags.get("year_of_construction")
    if sd:
        for tok in str(sd).replace("-", " ").split():
            if tok.isdigit() and len(tok) == 4:
                return int(tok)
    return None


def synth_attrs(kind, osm_id, tags, area_m2=None, height_m=None, length_m=None, width_m=None):
    """Return (attrs dict, provenance). Real OSM values win; the rest are
    deterministically synthesized from the OSM id."""
    real = bool(tags.get("operator")) or start_year(tags) is not None

    company = tags.get("operator")
    if not company:
        c = COMPANY_BY_KIND.get(kind, COMPANY_BY_KIND["_default"])
        company = c[osm_id % len(c)] if isinstance(c, list) else c

    yr = start_year(tags)
    if yr is None:
        base = INSTALL_BASE.get(kind, INSTALL_BASE["_default"])
        yr = min(2024, base + (osm_id % max(1, 2024 - base)))

    if kind == "building":
        floor_area = (area_m2 or 100.0) * max(1.0, (height_m or 12.0) / 3.3)
        cost = floor_area * 350_000.0
    elif kind == "road":
        cost = (length_m or 10.0) * (width_m or 5.0) * 25_000.0
    else:
        cost = float(COST_FLAT_JPY.get(kind, COST_FLAT_JPY["_default"]))
    cost *= 1.0 + ((osm_id % 41) - 20) / 200.0  # ±10% deterministic

    return (
        {"installYear": int(yr), "company": company, "costJpy": int(round(cost))},
        "osm" if real else "synthesized-demo",
    )


def edn_str(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def edn_entity(ent):
    parts = [':db/id ' + edn_str(ent["id"])]
    for k, v in ent["kv"]:
        if isinstance(v, str):
            parts.append(f"{k} {edn_str(v)}")
        elif isinstance(v, float):
            parts.append(f"{k} {v}")
        else:
            parts.append(f"{k} {v}")
    return "{" + " ".join(parts) + "}"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else "city"
    data = json.load(open(src))
    els = data["elements"]
    ways = [e for e in els if e.get("type") == "way" and e.get("geometry")]
    nodes = [e for e in els if e.get("type") == "node" and "lat" in e]

    lats = [p["lat"] for e in ways for p in e["geometry"]]
    lngs = [p["lon"] for e in ways for p in e["geometry"]]
    lat0, lng0 = sum(lats) / len(lats), sum(lngs) / len(lngs)
    m_per_lat = 111_320.0
    m_per_lng = 111_320.0 * math.cos(math.radians(lat0))

    def to_m(lon, lat):
        return [(lon - lng0) * m_per_lng, (lat - lat0) * m_per_lat]

    def back_lat(y):
        return round(lat0 + y / m_per_lat, 7)

    def back_lng(x):
        return round(lng0 + x / m_per_lng, 7)

    buildings, roads, objects, entities = [], [], [], []

    for e in ways:
        tags = e.get("tags", {})
        oid = e["id"]
        pts = [to_m(p["lon"], p["lat"]) for p in e["geometry"]]
        if tags.get("building"):
            xs = [q[0] for q in pts]
            ys = [q[1] for q in pts]
            aabb = [min(xs), min(ys), max(xs), max(ys)]
            h = round(resolve_height(tags), 2)
            area = max(1.0, (aabb[2] - aabb[0]) * (aabb[3] - aabb[1]))
            buildings.append({"aabb": [round(v, 2) for v in aabb], "height": h})
            attrs, prov = synth_attrs("building", oid, tags, area_m2=area, height_m=h)
            cx, cy = (aabb[0] + aabb[2]) / 2, (aabb[1] + aabb[3]) / 2
            entities.append({"id": f"{name}/b{oid}", "kv": [
                (":asset/osmId", oid), (":asset/kind", "building"),
                (":geo/lat", back_lat(cy)), (":geo/lng", back_lng(cx)),
                (":geo/x", round(cx, 2)), (":geo/y", round(cy, 2)),
                (":asset/heightM", h), (":asset/installYear", attrs["installYear"]),
                (":asset/company", attrs["company"]), (":asset/costJpy", attrs["costJpy"]),
                (":asset/dataProvenance", prov)]})
        elif tags.get("highway"):
            w = round(road_width(tags), 2)
            length = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
            roads.append({"path": [[round(x, 2), round(y, 2)] for x, y in pts], "width": w})
            attrs, prov = synth_attrs("road", oid, tags, length_m=length, width_m=w)
            cx, cy = pts[len(pts) // 2]
            entities.append({"id": f"{name}/r{oid}", "kv": [
                (":asset/osmId", oid), (":asset/kind", "road"),
                (":geo/lat", back_lat(cy)), (":geo/lng", back_lng(cx)),
                (":geo/x", round(cx, 2)), (":geo/y", round(cy, 2)),
                (":asset/installYear", attrs["installYear"]),
                (":asset/company", attrs["company"]), (":asset/costJpy", attrs["costJpy"]),
                (":asset/dataProvenance", prov)]})

    for e in nodes:
        tags = e.get("tags", {})
        kind = node_kind(tags)
        if not kind:
            continue
        oid = e["id"]
        x, y = to_m(e["lon"], e["lat"])
        attrs, prov = synth_attrs(kind, oid, tags)
        objects.append({
            "id": f"{name}/n{oid}", "kind": kind,
            "pos": [round(x, 2), round(y, 2)], "h": RENDER_H.get(kind, RENDER_H["_default"]),
            "attrs": {**attrs, "provenance": prov},
        })
        entities.append({"id": f"{name}/n{oid}", "kv": [
            (":asset/osmId", oid), (":asset/kind", kind),
            (":geo/lat", round(e["lat"], 7)), (":geo/lng", round(e["lon"], 7)),
            (":geo/x", round(x, 2)), (":geo/y", round(y, 2)),
            (":asset/installYear", attrs["installYear"]),
            (":asset/company", attrs["company"]), (":asset/costJpy", attrs["costJpy"]),
            (":asset/dataProvenance", prov)]})

    allx = [b["aabb"][0] for b in buildings] + [b["aabb"][2] for b in buildings] + \
           [p[0] for r in roads for p in r["path"]] + [o["pos"][0] for o in objects]
    ally = [b["aabb"][1] for b in buildings] + [b["aabb"][3] for b in buildings] + \
           [p[1] for r in roads for p in r["path"]] + [o["pos"][1] for o in objects]
    scene = {
        "name": name,
        "source": "OpenStreetMap via Overpass (ODbL)",
        "origin": {"lat": round(lat0, 7), "lng": round(lng0, 7)},
        "bbox_m": [round(min(allx), 2), round(min(ally), 2),
                   round(max(allx), 2), round(max(ally), 2)],
        "buildings": [
            {"aabb": [round(v, 2) for v in b["aabb"]], "height": b["height"]}
            for b in buildings
        ],
        "roads": roads,
        "objects": objects,
    }
    with open(dst, "w") as f:
        json.dump(scene, f, separators=(",", ":"))
        f.write("\n")

    # kotoba EAVT asset-registry transaction + schema (EDN).
    base = dst.rsplit(".scene.json", 1)[0] if dst.endswith(".scene.json") else dst
    schema_path = base + ".assets.schema.edn"
    tx_path = base + ".assets.edn"
    schema = [
        (":asset/osmId", "long", "one", " :db/unique :db.unique/identity"),
        (":asset/kind", "string", "one", ""),
        (":asset/installYear", "long", "one", ""),
        (":asset/company", "string", "one", ""),
        (":asset/costJpy", "long", "one", ""),
        (":asset/heightM", "double", "one", ""),
        (":asset/dataProvenance", "string", "one", ""),
        (":geo/lat", "double", "one", ""),
        (":geo/lng", "double", "one", ""),
        (":geo/x", "double", "one", ""),
        (":geo/y", "double", "one", ""),
    ]
    with open(schema_path, "w") as f:
        f.write(";; kotoba EAVT asset schema — Shibuya digital twin (ADR-2605312200)\n[\n")
        for ident, vt, card, extra in schema:
            f.write(f" {{:db/ident {ident} :db/valueType :db.type/{vt} "
                    f":db/cardinality :db.cardinality/{card}{extra}}}\n")
        f.write("]\n")
    with open(tx_path, "w") as f:
        f.write(f";; kotoba/datomic transaction — {len(entities)} Shibuya assets "
                "from OpenStreetMap (ODbL).\n")
        f.write(";; installYear/company/costJpy are SYNTHESIZED (dataProvenance) "
                "unless OSM-derived; replace from a real asset DB.\n[\n")
        for ent in entities:
            f.write(" " + edn_entity(ent) + "\n")
        f.write("]\n")

    print(f"wrote {dst}: {len(buildings)} buildings, {len(roads)} roads, "
          f"{len(objects)} objects; {len(entities)} kotoba entities → {tx_path}")


if __name__ == "__main__":
    main()
