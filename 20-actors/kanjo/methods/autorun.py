#!/usr/bin/env python3
"""autorun.py — kanjō AUTONOMOUS financial-disclosure heartbeat on the kotoba Datom log.
ADR-2606032000.

This is what "kotoba で自律的に稼働する" means for kanjō, in the constitution-permitted form
(mirrors shionome / ipaddress / yabai / sukashi / watatsuna / watari / kabuto autorun). Each
heartbeat the actor runs its whole disclosure pipeline ITSELF, with no human in the loop:

    observe (load the OFFLINE merged disclosed-fact graph) → split filings / facts
      → by-company-year → derive ratios + YoY (:synthesized) → sector/currency aggregates
        (coverage-honest, no cross-currency FX sums)
      → PERSIST a content-addressed transaction to the append-only kotoba Datom log
        (graph datoms + derived :fin.metric + :fin.agg), linking the previous tx's CID.

Constitutional posture holds by construction: only disclosed primary-filing FACTS + transparent
ratios are representable — never a rating, valuation, solvency verdict, FORECAST, or buy/sell call
(G2/G4); derived metrics/aggregates carry :sourcing :synthesized and are NEVER re-ingested as
disclosed facts (G5); a restatement is a new fact + :superseded-by, never a deletion (G11, 非終末論).

The loop is deterministic / resume-safe (cycle drives tx-id + as-of → same CIDs; the derived path
uses no PYTHONHASHSEED-randomized set iteration — by-company-year + metric-inputs are dict-ordered,
aggregates are sorted) and append-only. WHAT STAYS GATED (G7): it NEVER fetches live EDGAR/EDINET
and NEVER pushes to a live kotoba node. Ingest is the offline merged/seed graph; persistence is the
LOCAL append-only log. Live universe ingest is Council + operator gated. Stdlib only.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kanjo_edn  # noqa: E402
from analyze import aggregates, by_company_year, derive_metrics  # noqa: E402
from kotoba import (append_tx, derived_datoms, graph_datoms, head_cid,  # noqa: E402
                    make_tx, read_log, verify_chain)

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "data"
MERGED = DATA / "facts.merged.kotoba.edn"
SEED = DATA / "seed-financial-facts.kotoba.edn"
LOG = DATA / "kanjo.datoms.kotoba.edn"
BASE_AS_OF = 20260609


def _graph_path(graph_path: pathlib.Path | None) -> pathlib.Path:
    if graph_path is not None:
        return graph_path
    return MERGED if MERGED.exists() else SEED


def run_cycle(cycle: int, graph_path: pathlib.Path | None = None,
              log_path: pathlib.Path = LOG) -> dict:
    """One autonomous heartbeat: observe → derive ratios/YoY + aggregates → persist a
    content-addressed Datom transaction (graph + derived :fin.metric + :fin.agg). cycle drives
    tx-id + as-of."""
    rows = kanjo_edn.read_file(str(_graph_path(graph_path)))   # observe — OFFLINE (G7: no live fetch)
    facts = [r for r in rows if isinstance(r, dict) and ":fin.fact/id" in r]
    filings = [r for r in rows if isinstance(r, dict) and ":fin.filing/id" in r]
    cy = by_company_year(facts)
    metrics = derive_metrics(cy)                  # :synthesized ratios + YoY (G5)
    aggs = aggregates(cy)                          # coverage-honest sector/currency aggregates
    datoms = graph_datoms(rows) + derived_datoms(metrics, aggs)
    tx = make_tx(datoms, tx_id=cycle, as_of=BASE_AS_OF + cycle, prev_cid=head_cid(log_path))
    cid = append_tx(tx, log_path)                  # PERSIST to append-only LOCAL kotoba log
    return {
        "cycle": cycle,
        "filings": len(filings),
        "facts": len(facts),
        "companies": len(cy),
        "metrics": len(metrics),
        "aggregates": len(aggs),
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
    ap = argparse.ArgumentParser(description="kanjo autonomous financial-disclosure loop")
    ap.add_argument("--cycles", type=int, default=3, help="number of self-paced heartbeats")
    ap.add_argument("--graph", type=pathlib.Path, default=None, help="disclosed-fact graph EDN (offline)")
    ap.add_argument("--log", type=pathlib.Path, default=LOG, help="kotoba Datom log path")
    ap.add_argument("--fresh", action="store_true", help="start a fresh log (remove existing)")
    args = ap.parse_args()
    if args.fresh and args.log.exists():
        args.log.unlink()
    res = run_autonomous(args.cycles, graph_path=args.graph, log_path=args.log)
    print("# kanjo — AUTONOMOUS financial-disclosure over the kotoba Datom log "
          "(offline ingest, LOCAL persist; live EDGAR/EDINET / live-node push stays G7-gated)\n")
    for bt in res["beats"]:
        print(f"  ♥ cycle {bt['cycle']}: {bt['filings']} filings / {bt['facts']} facts / "
              f"{bt['companies']} companies · metrics {bt['metrics']} · aggregates {bt['aggregates']} "
              f"+{bt['datoms']} datoms → cid {bt['cid'][:14]}…")
    ch = res["chain"]
    print(f"\n  log: {res['log_length']} tx · head {res['head_cid'][:14]}… · "
          f"chain {'OK ✓' if ch['ok'] else 'BROKEN at ' + str(ch['broken_at'])} · "
          f"disclosed facts + :synthesized ratios, non-adjudicating / no forecast (G2/G4)")
