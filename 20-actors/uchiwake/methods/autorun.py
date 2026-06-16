#!/usr/bin/env python3
"""autorun.py — uchiwake 内訳 AUTONOMOUS product-resilience heartbeat on the kotoba Datom log.
ADR-2606081800.

This is what "kotoba で自律的に稼働する" means for uchiwake, in the constitution-permitted form
(mirrors kanjō / shionome / ipaddress / watatsuna / watari / kabuto autorun). Each heartbeat the
actor runs its whole product-BOM pipeline ITSELF, with no human in the loop:

    observe (load the OFFLINE merged product graph) → recursive BOM material-closure
      → material dependence + processing-jurisdiction load + ultimate-parent rollup (子会社)
        (:concentration/*, each :sourcing :synthesized)
      → PERSIST a content-addressed transaction to the append-only LOCAL kotoba Datom log
        (graph datoms + derived :concentration), linking the previous tx's CID.

Constitutional posture holds by construction (uchiwake G1/G2/G4/G5): only public trade-item facts
+ transparent concentration are representable — never a "who to hit" map and never a
clone/counterfeit recipe; derived :concentration/* carry :sourcing :synthesized and are NEVER
re-ingested as authoritative product facts; every datom is append-only :db/add.

The loop is deterministic / resume-safe (cycle drives tx-id + as_of → same CIDs; the derived path
sorts :concentration by id, so it is independent of PYTHONHASHSEED set-iteration order) and
append-only. WHAT STAYS GATED (G7): it NEVER fetches the live GS1/GLEIF/OFF universe and NEVER
pushes to a live kotoba node. Ingest is the offline merged/seed graph; persistence is the LOCAL
append-only log. Live universe ingest + the live-node push are Council + operator gated. Stdlib
only.
"""
from __future__ import annotations

import argparse
import pathlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import analyze  # noqa: E402
import uchiwake_edn  # noqa: E402
from kotoba import (append_tx, derived_datoms, graph_datoms, head_cid,  # noqa: E402
                    make_tx, read_log, verify_chain)

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "data"
MERGED = DATA / "products.merged.kotoba.edn"
SEED = DATA / "seed-products.kotoba.edn"
LOG = DATA / "uchiwake.datoms.kotoba.edn"
BASE_AS_OF = 20260616


def _graph_path(graph_path: pathlib.Path | None) -> pathlib.Path:
    if graph_path is not None:
        return graph_path
    return MERGED if MERGED.exists() else SEED


def run_cycle(cycle: int, graph_path: pathlib.Path | None = None,
              log_path: pathlib.Path = LOG) -> dict:
    """One autonomous heartbeat: observe → analyze concentration → persist a content-addressed
    Datom transaction (graph + derived :concentration). cycle drives tx-id + as_of."""
    gp = _graph_path(graph_path)
    rows = uchiwake_edn.load_edn(gp)               # observe — OFFLINE (G7: no live fetch)
    _md, derived = analyze(gp)                      # recursive BOM closure → :concentration
    datoms = graph_datoms(rows) + derived_datoms(derived)
    tx = make_tx(datoms, tx_id=cycle, as_of=BASE_AS_OF + cycle, prev_cid=head_cid(log_path))
    cid = append_tx(tx, log_path)                   # PERSIST to append-only LOCAL kotoba log
    g = uchiwake_edn.classify(rows)
    return {
        "cycle": cycle,
        "products": len(g["products"]),
        "parts": len(g["parts"]),
        "materials": len(g["materials"]),
        "bom": len(g["bom"]),
        "concentration": len(derived),
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
    ap = argparse.ArgumentParser(description="uchiwake autonomous product-resilience loop")
    ap.add_argument("--cycles", type=int, default=3, help="number of self-paced heartbeats")
    ap.add_argument("--graph", type=pathlib.Path, default=None, help="product graph EDN (offline)")
    ap.add_argument("--log", type=pathlib.Path, default=LOG, help="kotoba Datom log path")
    ap.add_argument("--fresh", action="store_true", help="start a fresh log (remove existing)")
    args = ap.parse_args()
    if args.fresh and args.log.exists():
        args.log.unlink()
    res = run_autonomous(args.cycles, graph_path=args.graph, log_path=args.log)
    print("# uchiwake — AUTONOMOUS product-BOM resilience over the kotoba Datom log "
          "(offline ingest, LOCAL persist; live GS1/GLEIF/OFF universe + live-node push stays "
          "G7-gated)\n")
    for bt in res["beats"]:
        print(f"  ♥ cycle {bt['cycle']}: {bt['products']} products / {bt['parts']} parts / "
              f"{bt['materials']} materials / {bt['bom']} BOM edges · concentration "
              f"{bt['concentration']} +{bt['datoms']} datoms → cid {bt['cid'][:14]}…")
    ch = res["chain"]
    print(f"\n  log: {res['log_length']} tx · head {res['head_cid'][:14]}… · "
          f"chain {'OK ✓' if ch['ok'] else 'BROKEN at ' + str(ch['broken_at'])} · "
          f"public product facts + :synthesized concentration, resilience map not a target (G2/G4)")
