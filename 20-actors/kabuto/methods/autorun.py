#!/usr/bin/env python3
"""autorun.py — kabuto AUTONOMOUS public-company-supply-chain resilience heartbeat on the kotoba
Datom log. ADR-2606022000.

This is what "kotoba で自律的に稼働する" means for kabuto, in the constitution-permitted form
(mirrors shionome / ipaddress / yabai / sukashi / watatsuna / watari autorun). Each heartbeat the
actor runs its whole supply-chain RESILIENCE pipeline ITSELF, with no human in the loop:

    observe (load the OFFLINE merged public-company graph) → classify
      → analyze (in/out degree → single-source → sector × commodity concentration → jurisdiction /
        region-bloc load → intermediaries / tier-depth / cross-bloc corridors / market-cap HHI —
        aggregate-first, G2 RESILIENCE + accountability map not a target-list)
      → PERSIST a content-addressed transaction to the append-only kotoba Datom log
        (graph datoms + derived :supply/* signals), linking the previous tx's CID.

Constitutional posture holds by construction: every derived signal is framed toward supply
diversification + corporate-power accountability — NEVER a "who to hit" / raid / takeover map (G2);
public listed-company public-record data only (G1); concentration is an observation, never an
antitrust/sanctions verdict (G4). The loop persists exactly what analyze.py computes, derived
flagged :supply/derived.

The loop is deterministic / resume-safe (cycle drives tx-id + as-of → same CIDs) and append-only.
WHAT STAYS GATED (G7 / G11): it NEVER fetches the live GLEIF/EDGAR/exchange universe and NEVER
pushes to a live kotoba node or posts to atproto. Ingest is the offline merged graph; persistence
is the LOCAL append-only log. Live full-universe ingest + live-node push + social posting are
Council + operator gated. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import analyze, classify, load_edn  # noqa: E402
from kotoba import (append_tx, derived_datoms, graph_datoms, head_cid,  # noqa: E402
                    make_tx, read_log, verify_chain)


def _canonical_order(datoms: list[list]) -> list[list]:
    """Sort datoms by canonical JSON so the tx is DETERMINISTIC regardless of analyze's internal
    ordering. kabuto's analyze builds `intermediaries`/`tier_depth` by iterating Python `set`s
    (PYTHONHASHSEED-randomized) and breaks score ties in set-iteration order — so the raw datom
    order varies per process. EAVT assertions are an unordered set (order carries no meaning), so a
    canonical sort here makes the content-addressed CID reproducible / resume-safe without touching
    the shared analyze.py."""
    return sorted(datoms, key=lambda d: json.dumps(d, ensure_ascii=False, sort_keys=True))

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "data"
MERGED = DATA / "companies.merged.kotoba.edn"
SEED = DATA / "seed-public-companies.kotoba.edn"
LOG = DATA / "kabuto.datoms.kotoba.edn"
BASE_AS_OF = 20260609


def _graph_path(graph_path: pathlib.Path | None) -> pathlib.Path:
    if graph_path is not None:
        return graph_path
    return MERGED if MERGED.exists() else SEED


def run_cycle(cycle: int, graph_path: pathlib.Path | None = None,
              log_path: pathlib.Path = LOG) -> dict:
    """One autonomous heartbeat: observe → classify → analyze → persist a content-addressed Datom
    transaction (graph + derived :supply/* signals). cycle drives tx-id + as-of."""
    rows = load_edn(_graph_path(graph_path))      # observe — OFFLINE merged graph (G7: no live fetch)
    companies, addresses, contacts, edges, processes = classify(rows)
    a = analyze(companies, edges)                 # aggregate RESILIENCE signal (G2)
    datoms = _canonical_order(graph_datoms(rows) + derived_datoms(a))  # deterministic / resume-safe
    tx = make_tx(datoms, tx_id=cycle, as_of=BASE_AS_OF + cycle, prev_cid=head_cid(log_path))
    cid = append_tx(tx, log_path)                 # PERSIST to append-only LOCAL kotoba log
    top_systemic = max(a["systemic"], key=lambda k: a["systemic"][k]) if a["systemic"] else "—"
    return {
        "cycle": cycle,
        "companies": len(companies),
        "edges": len(edges),
        "single_source": len(a["single_source"]),
        "intermediaries": len(a["intermediaries"]),
        "cap_hhi": a.get("cap_hhi", 0.0),
        "top_systemic": top_systemic,
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
    ap = argparse.ArgumentParser(description="kabuto autonomous supply-chain resilience loop")
    ap.add_argument("--cycles", type=int, default=3, help="number of self-paced heartbeats")
    ap.add_argument("--graph", type=pathlib.Path, default=None, help="public-company graph EDN (offline)")
    ap.add_argument("--log", type=pathlib.Path, default=LOG, help="kotoba Datom log path")
    ap.add_argument("--fresh", action="store_true", help="start a fresh log (remove existing)")
    args = ap.parse_args()
    if args.fresh and args.log.exists():
        args.log.unlink()
    res = run_autonomous(args.cycles, graph_path=args.graph, log_path=args.log)
    print("# kabuto — AUTONOMOUS public-company supply-chain resilience over the kotoba Datom log "
          "(offline ingest, LOCAL persist; live GLEIF/EDGAR universe / live-node push stays G7/G11-gated)\n")
    for bt in res["beats"]:
        print(f"  ♥ cycle {bt['cycle']}: {bt['companies']} companies / {bt['edges']} supply-edges "
              f"· single-source {bt['single_source']} · intermediaries {bt['intermediaries']} "
              f"· cap-HHI {bt['cap_hhi']} +{bt['datoms']} datoms → cid {bt['cid'][:14]}…")
    ch = res["chain"]
    print(f"\n  log: {res['log_length']} tx · head {res['head_cid'][:14]}… · "
          f"chain {'OK ✓' if ch['ok'] else 'BROKEN at ' + str(ch['broken_at'])} · "
          f"resilience + accountability map, never a target-list (G2/G4)")
