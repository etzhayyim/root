#!/usr/bin/env python3
"""autorun.py — watari AUTONOMOUS live-moving-craft situational-awareness heartbeat on the kotoba
Datom log. ADR-2606041827.

This is what "kotoba で自律的に稼働する" means for watari, in the constitution-permitted form
(mirrors shionome / ipaddress / yabai / sukashi / watatsuna autorun). Each heartbeat the actor runs
its whole SITUATIONAL-AWARENESS pipeline ITSELF, with no human in the loop:

    observe (load the OFFLINE merged craft graph) → classify
      → analyze (latest as-of fix per craft → lane/corridor load by kind → chokepoint transit →
        approach congestion → freshness tail — aggregate-first, G2 awareness not surveillance)
      → PERSIST a content-addressed transaction to the append-only kotoba Datom log
        (graph datoms + derived :movement/* signals), linking the previous tx's CID.

Constitutional posture holds by construction: outputs are aggregate lane/chokepoint/approach
density framed toward safety + congestion-easing — NEVER a "follow this craft" / targeting feed
(G2); a craft is a craft, NEVER a person — no track is linked to a named individual, no
pattern-of-life (G4, the defining gate). The chokepoint-transit output composes with watatsuna's
static cable-load over the SAME chokepoint keywords (静↔動 maritime resilience).

The loop is deterministic / resume-safe (cycle drives tx-id + as-of → same CIDs) and append-only
(the fix stream IS the trajectory; 非終末論). WHAT STAYS GATED (G7): it NEVER pulls a live
AISStream / OpenSky / adsb.fi feed and NEVER pushes to a live kotoba node. Ingest is the offline
merged/seed graph; persistence is the LOCAL append-only log. Live ingest is Council + operator
gated. Stdlib only.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import analyze, classify, load_edn  # noqa: E402
from kotoba import (append_tx, derived_datoms, graph_datoms, head_cid,  # noqa: E402
                    make_tx, read_log, verify_chain)

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "data"
MERGED = DATA / "craft-graph.merged.kotoba.edn"
SEED = DATA / "seed-craft-graph.kotoba.edn"
LOG = DATA / "watari.datoms.kotoba.edn"
BASE_AS_OF = 20260608


def _graph_path(graph_path: pathlib.Path | None) -> pathlib.Path:
    if graph_path is not None:
        return graph_path
    return MERGED if MERGED.exists() else SEED


def run_cycle(cycle: int, graph_path: pathlib.Path | None = None,
              log_path: pathlib.Path = LOG) -> dict:
    """One autonomous heartbeat: observe → classify → analyze → persist a content-addressed Datom
    transaction (graph + derived :movement/* signals). cycle drives tx-id + as-of."""
    rows = load_edn(_graph_path(graph_path))      # observe — OFFLINE merged graph (G7: no live feed)
    craft, fixes, legs, lanes = classify(rows)
    a = analyze(craft, fixes, legs, lanes)        # aggregate situational-awareness signal (G2)
    datoms = graph_datoms(rows) + derived_datoms(craft, lanes, a)
    tx = make_tx(datoms, tx_id=cycle, as_of=BASE_AS_OF + cycle, prev_cid=head_cid(log_path))
    cid = append_tx(tx, log_path)                 # PERSIST to append-only LOCAL kotoba log
    top_choke = max(a["choke_transit"], key=lambda k: a["choke_transit"][k]) if a["choke_transit"] else "—"
    return {
        "cycle": cycle,
        "craft": len(craft),
        "fixes": len(fixes),
        "lanes": len(lanes),
        "chokepoints": len(a["choke_transit"]),
        "top_chokepoint": top_choke,
        "stale": len(a["stale"]),
        "datoms": len(datoms),
        "cid": cid,
    }


def run_autonomous(cycles: int = 3, graph_path: pathlib.Path | None = None,
                   log_path: pathlib.Path = LOG) -> dict:
    beats = [run_cycle(c, graph_path, log_path) for c in range(1, cycles + 1)]
    return {
        "cycles": cycles,
        "beats": beats,
        "log_length": len(read_log(log_path)),
        "head_cid": head_cid(log_path),
        "chain": verify_chain(log_path),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="watari autonomous moving-craft situational-awareness loop")
    ap.add_argument("--cycles", type=int, default=3, help="number of self-paced heartbeats")
    ap.add_argument("--graph", type=pathlib.Path, default=None, help="craft graph EDN (offline)")
    ap.add_argument("--log", type=pathlib.Path, default=LOG, help="kotoba Datom log path")
    ap.add_argument("--fresh", action="store_true", help="start a fresh log (remove existing)")
    args = ap.parse_args()
    if args.fresh and args.log.exists():
        args.log.unlink()
    res = run_autonomous(args.cycles, graph_path=args.graph, log_path=args.log)
    print("# watari — AUTONOMOUS moving-craft situational-awareness over the kotoba Datom log "
          "(offline ingest, LOCAL persist; live AIS/ADS-B feed / live-node push stays G7-gated)\n")
    for bt in res["beats"]:
        print(f"  ♥ cycle {bt['cycle']}: {bt['craft']} craft / {bt['fixes']} fixes / {bt['lanes']} lanes "
              f"· chokepoints {bt['chokepoints']} (top {bt['top_chokepoint']}) · stale-tail {bt['stale']} "
              f"+{bt['datoms']} datoms → cid {bt['cid'][:14]}…")
    ch = res["chain"]
    print(f"\n  log: {res['log_length']} tx · head {res['head_cid'][:14]}… · "
          f"chain {'OK ✓' if ch['ok'] else 'BROKEN at ' + str(ch['broken_at'])} · "
          f"situational-awareness, no person-tracking (G2/G4)")
