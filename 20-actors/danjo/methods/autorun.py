#!/usr/bin/env python3
"""autorun.py — danjo AUTONOMOUS public-accountability cross-reference heartbeat on the kotoba
Datom log. ADR-2605301600.

This is what "kotoba で自律的に稼働する" means for danjo, in the constitution-permitted form
(mirrors shionome / ipaddress / yabai / sukashi / watatsuna / watari / kabuto / kanjō autorun).
Each heartbeat the actor runs its whole oversight pipeline ITSELF, with no human in the loop:

    observe (load the OFFLINE pre-published procurement corpus + the OPEN method-pack)
      → run every IMPLEMENTED open detector (R0/R1: single-bidder-streak) → build
        danjo.discrepancyObservation records (each passes build_observation's structural
        non-adjudication self-check: G4 nonAdjudicating, G5 ≥2 source CIDs, G6 method-note CID)
      → PERSIST a content-addressed transaction to the append-only kotoba Datom log
        (procurement-record graph datoms + derived observation datoms), linking the previous CID.

Constitutional posture holds by construction: the censor's EYE, never the SWORD — only FACTUAL
discrepancy observations over the public record are representable, NEVER a verdict of wrongdoing
(G4; no verdict attr exists, the loop's derived_datoms raises if one ever appears); passive-only
ingestion of the pre-published corpus (G3 — danjo re-fetches nothing); every observation cites ≥2
source-record CIDs (G5) + an open method-note CID (G6). Named-party publication stays G10 + 1 SBT =
1 vote gated — this loop persists observations to the LOCAL log only, it publishes nothing.

The loop is deterministic / resume-safe (cycle drives tx-id + as-of → same CIDs; detector iterates
list/dict order with no set iteration) and append-only. WHAT STAYS GATED (G3/G10): no live portal
fetch, no live-node push, no named-party publication. Stdlib only.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import load_json, run_all  # noqa: E402
from kotoba import (append_tx, derived_datoms, graph_datoms, head_cid,  # noqa: E402
                    make_tx, read_log, verify_chain)

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "data"
CORPUS = DATA / "corpus.seed.json"
METHODS = HERE / "v1-jp-seed.json"
LOG = DATA / "persisted" / "danjo.datoms.kotoba.edn"
BASE_AS_OF = 20260609


def run_cycle(cycle: int, corpus_path: pathlib.Path = CORPUS, methods_path: pathlib.Path = METHODS,
              log_path: pathlib.Path = LOG) -> dict:
    """One autonomous heartbeat: observe corpus + open methods → run detectors → persist a
    content-addressed Datom transaction (procurement graph + discrepancy observations). cycle
    drives tx-id + as-of."""
    corpus = load_json(corpus_path)              # observe — OFFLINE pre-published corpus (G3)
    methods = load_json(methods_path)            # the OPEN method-pack (G6)
    records = corpus.get("procurementRecords", [])
    observations = run_all(corpus, methods)      # FACTUAL discrepancy observations (G4 non-adjudicating)
    datoms = graph_datoms(records) + derived_datoms(observations)
    tx = make_tx(datoms, tx_id=cycle, as_of=BASE_AS_OF + cycle, prev_cid=head_cid(log_path))
    cid = append_tx(tx, log_path)                # PERSIST to append-only LOCAL kotoba log
    return {
        "cycle": cycle,
        "records": len(records),
        "methods": len(methods.get("methods", [])),
        "observations": len(observations),
        "datoms": len(datoms),
        "cid": cid,
    }


def run_autonomous(cycles: int = 3, corpus_path: pathlib.Path = CORPUS,
                   methods_path: pathlib.Path = METHODS, log_path: pathlib.Path = LOG) -> dict:
    beats = [run_cycle(c, corpus_path, methods_path, log_path) for c in range(1, cycles + 1)]
    return {
        "cycles": cycles,
        "beats": beats,
        "log_length": len(read_log(log_path)),
        "head_cid": head_cid(log_path),
        "chain": verify_chain(log_path),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="danjo autonomous public-accountability cross-reference loop")
    ap.add_argument("--cycles", type=int, default=3, help="number of self-paced heartbeats")
    ap.add_argument("--corpus", type=pathlib.Path, default=CORPUS, help="pre-published corpus JSON (offline)")
    ap.add_argument("--methods", type=pathlib.Path, default=METHODS, help="open method-pack JSON")
    ap.add_argument("--log", type=pathlib.Path, default=LOG, help="kotoba Datom log path")
    ap.add_argument("--fresh", action="store_true", help="start a fresh log (remove existing)")
    args = ap.parse_args()
    if args.fresh and args.log.exists():
        args.log.unlink()
    res = run_autonomous(args.cycles, corpus_path=args.corpus, methods_path=args.methods, log_path=args.log)
    print("# danjo — AUTONOMOUS public-accountability cross-reference over the kotoba Datom log "
          "(offline corpus, LOCAL persist; live fetch / named-party publish stays G3/G10-gated)\n")
    for bt in res["beats"]:
        print(f"  ♥ cycle {bt['cycle']}: {bt['records']} procurement records / {bt['methods']} open "
              f"methods → {bt['observations']} discrepancy observation(s) "
              f"+{bt['datoms']} datoms → cid {bt['cid'][:14]}…")
    ch = res["chain"]
    print(f"\n  log: {res['log_length']} tx · head {res['head_cid'][:14]}… · "
          f"chain {'OK ✓' if ch['ok'] else 'BROKEN at ' + str(ch['broken_at'])} · "
          f"the censor's EYE, never the SWORD — non-adjudicating (G4)")
