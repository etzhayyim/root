#!/usr/bin/env python3
"""autorun.py — watatsuna AUTONOMOUS submarine-cable-resilience heartbeat on the kotoba Datom log.
ADR-2606012600.

This is what "kotoba で自律的に稼働する" means for watatsuna, in the constitution-permitted form
(mirrors shionome / ipaddress / yabai / sukashi autorun). Each heartbeat the actor runs its whole
RESILIENCE pipeline ITSELF, with no human in the loop:

    observe (load the OFFLINE merged cable graph) → classify
      → analyze (cable⇄station incidence → station degree/capacity → chokepoint-load →
        cable-diversity → redundancy-gap — aggregate-first, G2 RESILIENCE map not interdiction)
      → PERSIST a content-addressed transaction to the append-only kotoba Datom log
        (graph datoms + derived :resilience/* signals), linking the previous tx's CID.

Constitutional posture holds by construction: every derived signal is framed toward redundancy /
diverse routing / faster repair — NEVER a "where to cut" target-list (G2, mirrors watatsumi N8);
public-record cable data only (G1); fault kinds carry only the public bulletin's own classification
(G4). The redundancy-gap output is what watatsumi's 敷設 robotics fleet plans diverse routes off —
to LAY/repair, never to cut.

The loop is deterministic / resume-safe (cycle drives tx-id + as-of → same CIDs) and append-only.
WHAT STAYS GATED (G7): it NEVER pulls a live TeleGeography feed / cable-ship AIS / live fault
bulletin and NEVER pushes to a live kotoba node. Ingest is the offline merged graph; persistence is
the LOCAL append-only log. Live planet-scale ingest is Council + operator gated. Stdlib only.
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
MERGED = DATA / "cable-graph.merged.kotoba.edn"
SEED = DATA / "seed-cable-graph.kotoba.edn"
LOG = DATA / "watatsuna.datoms.kotoba.edn"
BASE_AS_OF = 20260608


def _graph_path(graph_path: pathlib.Path | None) -> pathlib.Path:
    if graph_path is not None:
        return graph_path
    return MERGED if MERGED.exists() else SEED


def run_cycle(cycle: int, graph_path: pathlib.Path | None = None,
              log_path: pathlib.Path = LOG) -> dict:
    """One autonomous heartbeat: observe → classify → analyze → persist a content-addressed Datom
    transaction (graph + derived :resilience/* signals). cycle drives tx-id + as-of."""
    rows = load_edn(_graph_path(graph_path))      # observe — OFFLINE merged graph (G7: no live feed)
    cables, stations, links, segs, faults = classify(rows)
    a = analyze(cables, stations, links, segs, faults)   # aggregate RESILIENCE signal (G2)
    datoms = graph_datoms(rows) + derived_datoms(cables, stations, a)
    tx = make_tx(datoms, tx_id=cycle, as_of=BASE_AS_OF + cycle, prev_cid=head_cid(log_path))
    cid = append_tx(tx, log_path)                 # PERSIST to append-only LOCAL kotoba log
    top_choke = max(a["choke_load"], key=lambda k: a["choke_load"][k]) if a["choke_load"] else "—"
    return {
        "cycle": cycle,
        "cables": len(cables),
        "stations": len(stations),
        "segments": len(segs),
        "faults": len(faults),
        "chokepoints": len(a["choke_load"]),
        "top_chokepoint": top_choke,
        "redundancy_gaps": len(a["redundancy_gap"]),
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
    ap = argparse.ArgumentParser(description="watatsuna autonomous cable-resilience loop")
    ap.add_argument("--cycles", type=int, default=3, help="number of self-paced heartbeats")
    ap.add_argument("--graph", type=pathlib.Path, default=None, help="cable graph EDN (offline)")
    ap.add_argument("--log", type=pathlib.Path, default=LOG, help="kotoba Datom log path")
    ap.add_argument("--fresh", action="store_true", help="start a fresh log (remove existing)")
    args = ap.parse_args()
    if args.fresh and args.log.exists():
        args.log.unlink()
    res = run_autonomous(args.cycles, graph_path=args.graph, log_path=args.log)
    print("# watatsuna — AUTONOMOUS submarine-cable resilience over the kotoba Datom log "
          "(offline ingest, LOCAL persist; live feed / live-node push stays G7-gated)\n")
    for bt in res["beats"]:
        print(f"  ♥ cycle {bt['cycle']}: {bt['cables']} cables / {bt['stations']} stations / "
              f"{bt['segments']} segs / {bt['faults']} faults · chokepoints {bt['chokepoints']} "
              f"(top {bt['top_chokepoint']}) · redundancy-gaps {bt['redundancy_gaps']} "
              f"+{bt['datoms']} datoms → cid {bt['cid'][:14]}…")
    ch = res["chain"]
    print(f"\n  log: {res['log_length']} tx · head {res['head_cid'][:14]}… · "
          f"chain {'OK ✓' if ch['ok'] else 'BROKEN at ' + str(ch['broken_at'])} · "
          f"resilience map, never interdiction (G2)")
