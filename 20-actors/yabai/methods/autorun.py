#!/usr/bin/env python3
"""autorun.py — yabai AUTONOMOUS heartbeat loop on the kotoba Datom log. ADR-2605301400 §T3.

This is what "kotoba で自律的に稼働する" means for yabai, in the constitution-permitted form
(mirrors shionome / ipaddress autorun). Each heartbeat the actor runs its whole DEFENSIVE CTI
pipeline ITSELF, with no human in the loop:

    observe (load the OFFLINE merged CTI / passive-DNS graph) → classify
      → G6/G10 GUARD (assert every :access/* record is encrypted — hard-stop on plaintext PII)
      → analyze (fast-flux candidates, hosting concentration, IOC TLP/category load, IP-movement
        churn, cert-SAN pivots, encryption self-audit — aggregate-first, DEFENSIVE context)
      → PERSIST a content-addressed transaction to the append-only kotoba Datom log
        (graph datoms + derived :cti/* signals), linking the previous tx's CID into a commit-DAG.

Separation of duties is preserved: yabai SCORES risk context; the Council authorizes enforcement;
tadori holds case-anchored evidence. This loop does neither enforcement nor de-anonymisation — it
only weaves defensive signal and persists it.

The loop is deterministic / resume-safe (cycle drives tx-id + as-of → same CIDs on re-run) and
append-only (every cycle grows the log, never rewrites). WHAT STAYS GATED (G7 / G8): it NEVER
pulls a live CT-log / passive-DNS feed and NEVER pushes to a live kotoba node. Ingest is the
offline merged graph; persistence is the LOCAL append-only log. Live CTI ingest
(`methods/ingest.py --live`) and the live-node push (`methods/transact.py`) are Council Lv6+ +
operator gated. Vendor feeds (SecurityTrails/DNSDB/Recorded-Future) are `:feature-flagged-input`,
never system-of-record (tadori G4 discipline). Stdlib only.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import analyze  # noqa: E402
from kotoba import (append_tx, assert_access_encrypted, derived_datoms,  # noqa: E402
                    graph_datoms, head_cid, make_tx, read_log, verify_chain)
from yabai_edn import classify, load_edn  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "data"
MERGED = DATA / "passive-dns.merged.kotoba.edn"
SEED = DATA / "seed-passive-dns.kotoba.edn"
LOG = DATA / "yabai.datoms.kotoba.edn"
BASE_AS_OF = 20260608


def _graph_path(graph_path: pathlib.Path | None) -> pathlib.Path:
    if graph_path is not None:
        return graph_path
    return MERGED if MERGED.exists() else SEED


def run_cycle(cycle: int, graph_path: pathlib.Path | None = None,
              log_path: pathlib.Path = LOG) -> dict:
    """One autonomous heartbeat: observe → G6/G10 guard → analyze → persist a content-addressed
    Datom transaction (graph + derived :cti/* signals). cycle drives tx-id + as-of."""
    rows = load_edn(_graph_path(graph_path))      # observe — OFFLINE merged graph (G7: no live pull)
    assert_access_encrypted(rows)                 # G6/G10 — hard-stop on plaintext access PII
    b = classify(rows)
    a = analyze(b)                                # aggregate DEFENSIVE signal (not enforcement)
    datoms = graph_datoms(rows) + derived_datoms(a)
    tx = make_tx(datoms, tx_id=cycle, as_of=BASE_AS_OF + cycle, prev_cid=head_cid(log_path))
    cid = append_tx(tx, log_path)                 # PERSIST to append-only LOCAL kotoba log (G8)
    return {
        "cycle": cycle,
        "domains": a["n_domains"],
        "pdns": a["n_pdns"],
        "iocs": a["n_ioc"],
        "fast_flux": len(a["fast_flux"]),
        "access_encrypted": a["access_encrypted"],
        "access_total": a["access_total"],
        "plaintext_violations": a["plaintext_violations"],
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
    ap = argparse.ArgumentParser(description="yabai autonomous CTI heartbeat loop")
    ap.add_argument("--cycles", type=int, default=3, help="number of self-paced heartbeats")
    ap.add_argument("--graph", type=pathlib.Path, default=None, help="CTI graph EDN (offline)")
    ap.add_argument("--log", type=pathlib.Path, default=LOG, help="kotoba Datom log path")
    ap.add_argument("--fresh", action="store_true", help="start a fresh log (remove existing)")
    args = ap.parse_args()
    if args.fresh and args.log.exists():
        args.log.unlink()
    res = run_autonomous(args.cycles, graph_path=args.graph, log_path=args.log)
    print("# yabai — AUTONOMOUS CTI run over the kotoba Datom log "
          "(offline ingest, LOCAL persist; live CT/PDNS pull / live-node push stays G7/G8-gated)\n")
    for bt in res["beats"]:
        enc = f"{bt['access_encrypted']}/{bt['access_total']}"
        print(f"  ♥ cycle {bt['cycle']}: {bt['domains']} dom / {bt['pdns']} pdns / {bt['iocs']} IOC "
              f"· fast-flux {bt['fast_flux']} · access-enc {enc} (viol {bt['plaintext_violations']}) "
              f"+{bt['datoms']} datoms → cid {bt['cid'][:14]}…")
    ch = res["chain"]
    print(f"\n  log: {res['log_length']} tx · head {res['head_cid'][:14]}… · "
          f"chain {'OK ✓' if ch['ok'] else 'BROKEN at ' + str(ch['broken_at'])} · "
          f"G6/G10 access-encryption invariant held")
