#!/usr/bin/env python3
"""maps — kotoba read-surface readiness verifier (ADR-2606064500 R1). stdlib only.

The operator readiness check for the R1 cut-over: after `KOTOBA_ENDPOINT` is wired and the
`vertex_spatial` backfill lands, run this against the live endpoint to confirm ALL four
kotoba-native reads actually return — chunk (getChunk) · search · reverse · transit. It is the
runnable form of the 4-read integration test (test_chunk.py); the test proves the loop, this
lets an operator re-prove it on the live substrate before flipping reads kotoba-primary.

  verify_reads(endpoint, lat, lon, res, ring, query, stop_id) →
    { chunk:{ok,count}, search:{ok,count}, reverse:{ok,nearest}, transit:{ok,count}, allOk }

Fail-soft: each read degrades to ok=False (never raises), so the report is always emitted.

CLI: python3 verify.py --endpoint http://127.0.0.1:8077 [--lat .. --lon .. --query .. --stop ..]
     exit 0 iff allOk (a clean R1 readiness gate for a script / CronJob).
"""
from __future__ import annotations
import json, sys

from chunk import get_chunk
from search import search_places
from reverse import reverse_geocode
from transit import next_departures_at_stop

# Tokyo Station anchor — the maps-3d walkable default; override on the CLI for other backfills.
DEFAULT = {"lat": 35.6812, "lon": 139.7671, "res": 10, "ring": 2,
           "query": "tok", "stop_id": "f.station.tokyo"}


def _ring_cells(lat, lon, res, ring):
    try:
        import h3
        return list(h3.grid_disk(h3.latlng_to_cell(lat, lon, res), ring))
    except Exception:
        return []


def verify_reads(endpoint, *, lat, lon, res=10, ring=2, query="", stop_id="") -> dict:
    report: dict = {}

    cells = _ring_cells(lat, lon, res, ring)
    ch = get_chunk(endpoint, cells, res) if cells else {"total": 0}
    report["chunk"] = {"ok": ch.get("total", 0) > 0, "count": ch.get("total", 0),
                       "note": None if cells else "h3 unavailable — cannot probe cells"}

    sr = search_places(endpoint, query) if query else []
    report["search"] = {"ok": len(sr) > 0, "count": len(sr)}

    rg = reverse_geocode(endpoint, lat, lon, res=res, ring=ring)
    report["reverse"] = {"ok": len(rg) > 0, "nearest": rg[0]["id"] if rg else None}

    td = next_departures_at_stop(endpoint, stop_id) if stop_id else []
    report["transit"] = {"ok": len(td) > 0, "count": len(td)}

    report["allOk"] = all(v.get("ok") for k, v in report.items() if k != "allOk")
    return report


def _arg(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


def main(argv):
    endpoint = _arg(argv, "--endpoint")
    if not endpoint:
        sys.exit("usage: verify.py --endpoint URL [--lat L --lon L --res R --ring K "
                 "--query Q --stop STOP_ID]")
    rep = verify_reads(
        endpoint,
        lat=float(_arg(argv, "--lat", DEFAULT["lat"])),
        lon=float(_arg(argv, "--lon", DEFAULT["lon"])),
        res=int(_arg(argv, "--res", DEFAULT["res"])),
        ring=int(_arg(argv, "--ring", DEFAULT["ring"])),
        query=_arg(argv, "--query", DEFAULT["query"]),
        stop_id=_arg(argv, "--stop", DEFAULT["stop_id"]),
    )
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    sys.exit(0 if rep["allOk"] else 1)


if __name__ == "__main__":
    main(sys.argv)
