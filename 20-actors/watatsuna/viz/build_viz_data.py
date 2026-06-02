#!/usr/bin/env python3
"""watatsuna 綿津綱 — build the resilience visualization.

Reads a cable graph (merged if present, else seed), runs the analyzer, and emits:
  - viz/cable-resilience.json   (payload, for programmatic / kami-engine consumption)
  - viz/cable-resilience.htm    (self-contained canvas viewer, data inlined — opens via file://)

The viewer is an aggregate-first RESILIENCE map (G2): stations sized by landed capacity,
coloured by their chokepoint; segments arc through the chokepoints they traverse; a ranked
chokepoint-load panel. It is NOT a target-list — it surfaces where to ADD redundancy.

HONEST: 2D equirectangular canvas (no external deps, no build step). The kami-engine WASM
3D resilience globe (kanae-style, ADR-2605302300) is deferred to a later increment; this
payload is the data contract it would consume.

Usage:  python3 viz/build_viz_data.py [graph.edn]
"""
from __future__ import annotations
import sys, json, pathlib

ACTOR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR / "methods"))
import analyze  # noqa: E402


def build_payload(graph_path: pathlib.Path):
    rows = analyze.load_edn(graph_path)
    cables, stations, links, segs, faults = analyze.classify(rows)
    a = analyze.analyze(cables, stations, links, segs, faults)

    st_out = []
    for s, meta in stations.items():
        if a["station_degree"][s] == 0:
            continue
        if ":station/lat" not in meta or ":station/lon" not in meta:
            continue
        st_out.append({
            "id": s, "name": meta.get(":station/name", s),
            "country": meta.get(":station/country", "??"),
            "lat": meta[":station/lat"], "lon": meta[":station/lon"],
            "degree": a["station_degree"][s],
            "capacity": a["station_capacity"][s],
            "chokepoints": [c.lstrip(":") for c in (meta.get(":station/chokepoint") or [])],
            "cables": sorted(cables[c].get(":cable/name", c)
                             for c in a["station_cables"][s]),
        })

    seg_out = []
    for sg in segs:
        fr, to = stations.get(sg[":cable.seg/from"]), stations.get(sg[":cable.seg/to"])
        if not fr or not to:
            continue
        if ":station/lat" not in fr or ":station/lat" not in to:
            continue
        seg_out.append({
            "from": [fr[":station/lat"], fr[":station/lon"]],
            "to": [to[":station/lat"], to[":station/lon"]],
            "traverses": [c.lstrip(":") for c in (sg.get(":cable.seg/traverses") or [])],
            "cable": cables.get(sg[":cable.seg/cable"], {}).get(":cable/name", sg[":cable.seg/cable"]),
        })

    choke_out = [{"name": cp.lstrip(":"), "load": a["choke_load"][cp], "count": a["choke_count"][cp]}
                 for cp in sorted(a["choke_load"], key=lambda k: -a["choke_load"][k])]

    fault_out = [{
        "id": f[":cable.fault/id"],
        "cable": cables.get(f.get(":cable.fault/cable"), {}).get(":cable/name", f.get(":cable.fault/cable")),
        "kind": str(f.get(":cable.fault/kind", "")).lstrip(":"),
        "detected": f.get(":cable.fault/detected-at", ""),
        "restored": f.get(":cable.fault/restored-at") or "open",
    } for f in faults]

    return {
        "source": graph_path.name,
        "cables": len(cables), "stations": len(st_out),
        "totalCapacity": round(sum(a["cap"].values()), 1),
        "chokepoints": choke_out, "station_list": st_out,
        "segments": seg_out, "faults": fault_out,
    }


def main():
    graph = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if graph is None:
        merged = ACTOR / "data" / "cable-graph.merged.kotoba.edn"
        graph = merged if merged.exists() else ACTOR / "data" / "seed-cable-graph.kotoba.edn"
    payload = build_payload(graph)

    vdir = ACTOR / "viz"
    vdir.mkdir(exist_ok=True)
    (vdir / "cable-resilience.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    data_js = json.dumps(payload, ensure_ascii=False)
    for tpl_name, out_name in (("_template.htm", "cable-resilience.htm"),
                               ("_globe_template.htm", "cable-globe.htm")):
        tpl = (vdir / tpl_name).read_text(encoding="utf-8")
        html = tpl.replace("__VIZ_DATA__", data_js).replace("__SOURCE__", payload["source"])
        (vdir / out_name).write_text(html, encoding="utf-8")

    print(f"viz built from {graph.name}: {payload['stations']} stations · "
          f"{payload['cables']} cables · {payload['totalCapacity']} Tbps · "
          f"{len(payload['chokepoints'])} chokepoints")
    print(f"✓ wrote viz/cable-resilience.json + viz/cable-resilience.htm + viz/cable-globe.htm")


if __name__ == "__main__":
    main()
