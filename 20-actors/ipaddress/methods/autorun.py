#!/usr/bin/env python3
"""autorun.py — ipaddress AUTONOMOUS heartbeat loop on the kotoba Datom log. ADR-2605301400 §T2.

This is what "kotoba で自律的に稼働する" means for ipaddress, in the constitution-permitted form
(mirrors shionome/methods/autorun.py). Each heartbeat the actor runs its whole pipeline ITSELF,
with no human in the loop:

    observe (load the OFFLINE merged IP/ASN graph) → classify
      → analyze concentration (RIR coverage, ASN prefix-load, hosting-class HHI — edge-primary,
        aggregate-first, G2 RESILIENCE map not a target-list)
      → PERSIST a content-addressed transaction to the append-only kotoba Datom log
        (graph datoms + derived :ipnet/* concentration), linking the previous tx's CID.

The loop is fully self-driving and idempotent-by-CID: it links each transaction to the previous
one's content address, so the log is a verifiable commit-DAG that only ever grows (append-only /
非終末論). It is deterministic — the caller supplies the cycle index, which drives the tx-id +
as-of — so a re-run reproduces the same CIDs (resume-safe).

WHAT STAYS GATED (G7 / G8): this loop NEVER pulls from a live RIR/RDAP portal and NEVER pushes to
a live kotoba node. Ingest is the offline merged graph; persistence is the LOCAL append-only log.
Live full-universe RIR/RDAP ingest (`methods/ingest.py --live`) and the live-node push
(`methods/transact.py --graph <CID> --cacao`) are Council Lv6+ + operator gated — the ONE
remaining step is a human gate flip, by constitutional design. Autonomy here = the actor drives
its own observe→analyze→persist cycle over its own substrate, not that it speaks to the world
unsupervised. No host is port/vuln-scanned (akuma/aratame caseMandate boundary, not 1次 collection).

Stdlib only.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import analyze  # noqa: E402
from ip_edn import classify, load_edn  # noqa: E402
from kotoba import (append_tx, derived_datoms, graph_datoms, head_cid,  # noqa: E402
                    make_tx, read_log, verify_chain)

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "data"
MERGED = DATA / "ip-network.merged.kotoba.edn"
SEED = DATA / "seed-ip-network.kotoba.edn"
LOG = DATA / "ipaddress.datoms.kotoba.edn"
BASE_AS_OF = 20260608


def _graph_path(graph_path: pathlib.Path | None) -> pathlib.Path:
    if graph_path is not None:
        return graph_path
    return MERGED if MERGED.exists() else SEED


def run_cycle(cycle: int, graph_path: pathlib.Path | None = None,
              log_path: pathlib.Path = LOG) -> dict:
    """One autonomous heartbeat: observe → classify → analyze → persist a content-addressed
    Datom transaction (graph + derived :ipnet/* concentration). Returns a heartbeat summary.
    cycle drives tx-id + as-of (deterministic / resume-safe)."""
    rows = load_edn(_graph_path(graph_path))      # observe — OFFLINE merged graph (G7: no live pull)
    b = classify(rows)                            # bucket entities
    a = analyze(b)                                # aggregate concentration, edge-primary (G2)
    datoms = graph_datoms(rows) + derived_datoms(a)
    tx = make_tx(datoms, tx_id=cycle, as_of=BASE_AS_OF + cycle, prev_cid=head_cid(log_path))
    cid = append_tx(tx, log_path)                 # PERSIST to append-only LOCAL kotoba log (G8)
    top = a["asn_prefix"][0] if a["asn_prefix"] else (None, "—", 0, None, None)
    return {
        "cycle": cycle,
        "rirs": len(b["rirs"]),
        "asns": len(b["asns"]),
        "ranges": a["v4"] + a["v6"],
        "prefix_hhi": a["prefix_hhi"],
        "space_hhi": a["space_hhi"],
        "top_asn": top[1],
        "datoms": len(datoms),
        "cid": cid,
    }


def run_autonomous(cycles: int = 3, graph_path: pathlib.Path | None = None,
                   log_path: pathlib.Path = LOG) -> dict:
    """Drive `cycles` self-paced heartbeats. Each appends one content-addressed transaction to
    the kotoba Datom log. Returns the run summary + final head CID + chain verification."""
    beats = [run_cycle(c, graph_path, log_path) for c in range(1, cycles + 1)]
    return {
        "cycles": cycles,
        "beats": beats,
        "log_length": len(read_log(log_path)),
        "head_cid": head_cid(log_path),
        "chain": verify_chain(log_path),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="ipaddress autonomous heartbeat loop")
    ap.add_argument("--cycles", type=int, default=3, help="number of self-paced heartbeats")
    ap.add_argument("--graph", type=pathlib.Path, default=None, help="IP/ASN graph EDN (offline)")
    ap.add_argument("--log", type=pathlib.Path, default=LOG, help="kotoba Datom log path")
    ap.add_argument("--fresh", action="store_true", help="start a fresh log (remove existing)")
    args = ap.parse_args()
    if args.fresh and args.log.exists():
        args.log.unlink()
    res = run_autonomous(args.cycles, graph_path=args.graph, log_path=args.log)
    print("# ipaddress — AUTONOMOUS run over the kotoba Datom log "
          "(offline ingest, LOCAL persist; live RIR pull / live-node push stays G7/G8-gated)\n")
    for bt in res["beats"]:
        print(f"  ♥ cycle {bt['cycle']}: {bt['rirs']} RIR / {bt['asns']} ASN / "
              f"{bt['ranges']} ranges · prefix-HHI {bt['prefix_hhi']} space-HHI {bt['space_hhi']} "
              f"· top-ASN {bt['top_asn']:<14} +{bt['datoms']} datoms → cid {bt['cid'][:14]}…")
    ch = res["chain"]
    print(f"\n  log: {res['log_length']} tx · head {res['head_cid'][:14]}… · "
          f"chain {'OK ✓' if ch['ok'] else 'BROKEN at ' + str(ch['broken_at'])}")
