#!/usr/bin/env python3
"""autorun.py — sukashi AUTONOMOUS ad-tech-supply-chain + fraud-observatory heartbeat on the
kotoba Datom log. ADR-2606071600.

This is what "kotoba で自律的に稼働する" means for sukashi, in the constitution-permitted form
(mirrors shionome / ipaddress / yabai autorun). Each heartbeat the actor runs its whole OBSERVATORY
pipeline ITSELF, with no human in the loop:

    observe (load the OFFLINE merged ad-supply-chain graph) → classify
      → analyze (authorization-handshake integrity / account-id collision / delivery-infra
        concentration / shared-infra scam-network clustering / category load — aggregate-first, G4
        non-adjudicating, fraud signals :synthesized on fictional entities only)
      → PERSIST a content-addressed transaction to the append-only kotoba Datom log
        (graph datoms + derived :adsupply/* + :adfraud/* signals), linking the previous tx's CID.

Constitutional posture is preserved by construction: OBSERVATORY not an ad network (G2); public
IAB transparency files only (G1); REAL firms carry NO fraud signal, every signal is
non-adjudicating + :synthesized (G4); no personal PII (G9). The loop asserts nothing new as fact —
it persists exactly what analyze.py computes, with derived signals flagged :derived.

The loop is deterministic / resume-safe (cycle drives tx-id + as-of → same CIDs on re-run) and
append-only. WHAT STAYS GATED (G7 / G11 / G12): it NEVER crawls live ads.txt/sellers.json/WHOIS and
NEVER pushes to a live kotoba node; it never places/clicks an ad or evades anti-bot. Ingest is the
offline merged graph; persistence is the LOCAL append-only log. Live full-web crawl
(`methods/ingest.py` + SUKASHI_OPERATOR_GATE) and the live-node push (`methods/transact.py`) are
Council Lv6+ + operator gated. Stdlib only.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import analyze  # noqa: E402
from kotoba import (append_tx, derived_datoms, graph_datoms, head_cid,  # noqa: E402
                    make_tx, read_log, verify_chain)
from sukashi_edn import classify, load_edn  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "data"
MERGED = DATA / "ad-supply-chain.merged.kotoba.edn"
SEED = DATA / "seed-ad-supply-chain.kotoba.edn"
LOG = DATA / "sukashi.datoms.kotoba.edn"
BASE_AS_OF = 20260608


def _graph_path(graph_path: pathlib.Path | None) -> pathlib.Path:
    if graph_path is not None:
        return graph_path
    return MERGED if MERGED.exists() else SEED


def run_cycle(cycle: int, graph_path: pathlib.Path | None = None,
              log_path: pathlib.Path = LOG) -> dict:
    """One autonomous heartbeat: observe → classify → analyze → persist a content-addressed Datom
    transaction (graph + derived :adsupply/* + :adfraud/* signals). cycle drives tx-id + as-of."""
    rows = load_edn(_graph_path(graph_path))      # observe — OFFLINE merged graph (G7: no live crawl)
    adtech, auth, creatives, delivery, fraud = classify(rows)
    a = analyze(adtech, auth, creatives, delivery, fraud)   # aggregate observatory signal (G4)
    datoms = graph_datoms(rows) + derived_datoms(a)
    tx = make_tx(datoms, tx_id=cycle, as_of=BASE_AS_OF + cycle, prev_cid=head_cid(log_path))
    cid = append_tx(tx, log_path)                 # PERSIST to append-only LOCAL kotoba log
    top_cluster = a["clusters"][0] if a["clusters"] else None
    return {
        "cycle": cycle,
        "adtech": len(adtech),
        "auth_edges": len(auth),
        "delivery_edges": len(delivery),
        "fraud_signals": len(fraud),
        "scam_clusters": len(a["clusters"]),
        "top_cluster_members": (top_cluster["members"] if top_cluster else 0),
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
    ap = argparse.ArgumentParser(description="sukashi autonomous ad-supply-chain observatory loop")
    ap.add_argument("--cycles", type=int, default=3, help="number of self-paced heartbeats")
    ap.add_argument("--graph", type=pathlib.Path, default=None, help="ad-supply-chain graph EDN (offline)")
    ap.add_argument("--log", type=pathlib.Path, default=LOG, help="kotoba Datom log path")
    ap.add_argument("--fresh", action="store_true", help="start a fresh log (remove existing)")
    args = ap.parse_args()
    if args.fresh and args.log.exists():
        args.log.unlink()
    res = run_autonomous(args.cycles, graph_path=args.graph, log_path=args.log)
    print("# sukashi — AUTONOMOUS ad-supply-chain + fraud observatory over the kotoba Datom log "
          "(offline ingest, LOCAL persist; live crawl / live-node push stays G7/G11-gated)\n")
    for bt in res["beats"]:
        print(f"  ♥ cycle {bt['cycle']}: {bt['adtech']} adtech / {bt['auth_edges']} auth-edges / "
              f"{bt['delivery_edges']} delivery / {bt['fraud_signals']} fraud-sig "
              f"· scam-clusters {bt['scam_clusters']} (top {bt['top_cluster_members']} members) "
              f"+{bt['datoms']} datoms → cid {bt['cid'][:14]}…")
    ch = res["chain"]
    print(f"\n  log: {res['log_length']} tx · head {res['head_cid'][:14]}… · "
          f"chain {'OK ✓' if ch['ok'] else 'BROKEN at ' + str(ch['broken_at'])} · "
          f"observatory-only / non-adjudicating (G2/G4)")
