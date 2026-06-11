#!/usr/bin/env python3
"""autorun.py — kosatsu (高札) AUTONOMOUS crime/sanctions competing-claim heartbeat on the kotoba
Datom log. ADR-2606072000.

This is what "kotoba で自律的に稼働する" means for kosatsu, in the constitution-permitted form
(mirrors the infra-intel/observatory family's autorun). Each heartbeat the actor runs its whole
competing-claim pipeline ITSELF, no human in the loop:

    observe (load the OFFLINE designation-graph seed) → weave (validate every authority / subject /
      designation event against the gates; raises on a violation)
      → report (aggregate, politically-neutral: agreement index, per-subject divergence
        {contested | unanimous | single-asserter}, by-authority coverage, co-designation —
        every designation an ATTRIBUTED append-only event, asserter + as-of)
      → PERSIST a content-addressed transaction to the append-only kotoba Datom log
        (graph datoms + derived :kosatsu.div/* signals), linking the previous tx's CID.

Constitutional posture holds by construction: etzhayyim authors NO designation (every designation
carries its own `:asserter` — a sovereign/body, never etzhayyim), NO verdict, NO per-subject score.
The computed divergence class makes "crime varies by political stance" a NEUTRAL fact. The loop
persists exactly what weave + report produced; derived flagged :kosatsu.div/derived.

The loop is deterministic / resume-safe: `_canonical_order` sorts datoms by canonical JSON before
hashing so the CID is reproducible across processes regardless of any set-iteration order inside
report (verified stable under PYTHONHASHSEED=random). Append-only. WHAT STAYS GATED (G7/G8): no
live designation-list ingest, no live-node push, no live posting (posts are dry-run, owned by
social.py). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _edn import load_edn  # noqa: E402
from kotoba import (append_tx, derived_datoms, graph_datoms, head_cid,  # noqa: E402
                    make_tx, read_log, verify_chain)
from weave import report, weave  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "data"
SEED = DATA / "seed-designation-graph.kotoba.edn"
LOG = DATA / "kosatsu.datoms.kotoba.edn"
BASE_AS_OF = 20260609


def _canonical_order(datoms: list[list]) -> list[list]:
    """Sort datoms by canonical JSON so the tx is DETERMINISTIC regardless of any set-iteration
    order inside report (PYTHONHASHSEED-randomized). EAVT is an unordered set, so a canonical sort
    makes the content-addressed CID reproducible / resume-safe."""
    return sorted(datoms, key=lambda d: json.dumps(d, ensure_ascii=False, sort_keys=True))


def run_cycle(cycle: int, seed_path: pathlib.Path = SEED, log_path: pathlib.Path = LOG) -> dict:
    """One autonomous heartbeat: observe → weave (validate) → report → persist a content-addressed
    Datom transaction (graph + derived :kosatsu.div/* signals). cycle drives tx-id + as-of."""
    g = weave(load_edn(seed_path))                # observe + VALIDATE (raises on any gate)
    r = report(g)                                 # aggregate, politically-neutral (G2/G4/G9)
    datoms = _canonical_order(graph_datoms(g) + derived_datoms(r))  # deterministic / resume-safe
    tx = make_tx(datoms, tx_id=cycle, as_of=BASE_AS_OF + cycle, prev_cid=head_cid(log_path))
    cid = append_tx(tx, log_path)                 # PERSIST to append-only LOCAL kotoba log
    ai = r["agreement_index"]
    return {
        "cycle": cycle,
        "authorities": r["authority_count"],
        "subjects": r["subject_count"],
        "designations": r["designation_count"],
        "contested": ai["contested"],
        "unanimous": ai["unanimous"],
        "single_asserter": ai["single_asserter"],
        "datoms": len(datoms),
        "cid": cid,
    }


def run_autonomous(cycles: int = 3, seed_path: pathlib.Path = SEED,
                   log_path: pathlib.Path = LOG) -> dict:
    beats = [run_cycle(c, seed_path, log_path) for c in range(1, cycles + 1)]
    return {
        "cycles": cycles,
        "beats": beats,
        "log_length": len(read_log(log_path)),
        "head_cid": head_cid(log_path),
        "chain": verify_chain(log_path),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="kosatsu autonomous competing-claim loop")
    ap.add_argument("--cycles", type=int, default=3, help="number of self-paced heartbeats")
    ap.add_argument("--seed", type=pathlib.Path, default=SEED, help="designation-graph seed EDN (offline)")
    ap.add_argument("--log", type=pathlib.Path, default=LOG, help="kotoba Datom log path")
    ap.add_argument("--fresh", action="store_true", help="start a fresh log (remove existing)")
    args = ap.parse_args()
    if args.fresh and args.log.exists():
        args.log.unlink()
    res = run_autonomous(args.cycles, seed_path=args.seed, log_path=args.log)
    print("# kosatsu (高札) — AUTONOMOUS competing-claim over the kotoba Datom log "
          "(offline seed, LOCAL persist; live ingest / posting stays G7/G8-gated)\n")
    for bt in res["beats"]:
        print(f"  ♥ cycle {bt['cycle']}: {bt['authorities']} authorities / {bt['subjects']} subjects "
              f"/ {bt['designations']} designations · contested {bt['contested']} · unanimous "
              f"{bt['unanimous']} · single-asserter {bt['single_asserter']} "
              f"+{bt['datoms']} datoms → cid {bt['cid'][:14]}…")
    ch = res["chain"]
    print(f"\n  log: {res['log_length']} tx · head {res['head_cid'][:14]}… · "
          f"chain {'OK ✓' if ch['ok'] else 'BROKEN at ' + str(ch['broken_at'])} · "
          f"every designation ATTRIBUTED; no designation/verdict/score authored by etzhayyim (G2/G4)")
