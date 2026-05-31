#!/usr/bin/env python3
"""osm_to_citymesh — OpenStreetMap (Overpass `out geom`) → e7m-sim city scene.

Projects building footprints + roads into local ENU metres (origin = bbox
centre, z-up) and emits a compact scene JSON the kami-genesis Shibuya sim loads.

Buildings are reduced to an axis-aligned footprint box + height (the collision
proxy used by `kami_genesis::Obstacle::Aabb`; polygon-accurate collision is a
documented follow-up). Roads are kept as metre-space polylines + width for the
drivable ribbon render.

Source data is OpenStreetMap (ODbL) — application-consumed, per deps.toml.

Usage:
  python3 osm_to_citymesh.py <in.osm.json> <out.scene.json> [name]
"""
import json
import math
import sys


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


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else "city"
    data = json.load(open(src))
    els = [e for e in data["elements"] if e.get("type") == "way" and e.get("geometry")]

    # Origin = mean of all node lat/lng.
    lats = [p["lat"] for e in els for p in e["geometry"]]
    lngs = [p["lon"] for e in els for p in e["geometry"]]
    lat0, lng0 = sum(lats) / len(lats), sum(lngs) / len(lngs)
    m_per_lat = 111_320.0
    m_per_lng = 111_320.0 * math.cos(math.radians(lat0))

    def to_m(p):
        return [(p["lon"] - lng0) * m_per_lng, (p["lat"] - lat0) * m_per_lat]

    buildings, roads = [], []
    for e in els:
        tags = e.get("tags", {})
        pts = [to_m(p) for p in e["geometry"]]
        if tags.get("building"):
            xs = [q[0] for q in pts]
            ys = [q[1] for q in pts]
            buildings.append({
                "aabb": [min(xs), min(ys), max(xs), max(ys)],
                "height": round(resolve_height(tags), 2),
            })
        elif tags.get("highway"):
            roads.append({
                "path": [[round(x, 2), round(y, 2)] for x, y in pts],
                "width": round(road_width(tags), 2),
            })

    allx = [b["aabb"][0] for b in buildings] + [b["aabb"][2] for b in buildings] + \
           [p[0] for r in roads for p in r["path"]]
    ally = [b["aabb"][1] for b in buildings] + [b["aabb"][3] for b in buildings] + \
           [p[1] for r in roads for p in r["path"]]
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
    }
    with open(dst, "w") as f:
        json.dump(scene, f, separators=(",", ":"))
        f.write("\n")
    print(f"wrote {dst}: {len(buildings)} buildings, {len(roads)} roads, "
          f"bbox {scene['bbox_m']}")


if __name__ == "__main__":
    main()
