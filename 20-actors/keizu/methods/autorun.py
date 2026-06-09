#!/usr/bin/env python3
"""autorun.py — keizu (系図) AUTONOMOUS government-power-relations heartbeat on the kotoba Datom log.
ADR-2606066000.

This is what "kotoba で自律的に稼働する" means for keizu, in the constitution-permitted form
(mirrors shionome / ipaddress / yabai / sukashi / watatsuna / watari / kabuto / kanjō / danjo
autorun). Each heartbeat the actor runs its whole power-relations pipeline ITSELF, no human in the
loop:

    observe (load the OFFLINE relation-graph seed) → weave (validate every node/rel/committee/
      money/statement against the gates; raises on a violation)
      → concentration (aggregate, edge-primary: committee cross-organ, cross-committee seats,
        connector seats, money/payer HHI, revolving-door, award-and-fund co-occurrence,
        by-jurisdiction — all computed on read from edges/flows, never a per-person score)
      → PERSIST a content-addressed transaction to the append-only kotoba Datom log
        (graph datoms + derived :keizu.conc/* signals), linking the previous tx's CID.

Constitutional posture holds by construction: an accountability MAP, never a target-list; FACTUAL +
non-adjudicating (a revolving-door chain / award-and-fund co-occurrence is a co-occurrence of
disclosed flows, NOT an allegation — `:keizu.conc/non-adjudicating true`); no-doxxing (PII node
attrs unrepresentable, validated by weave); edge-primary (no per-person score). The loop persists
exactly what weave + concentration produced; derived flagged :keizu.conc/derived.

The loop is deterministic / resume-safe: `_canonical_order` sorts datoms by canonical JSON before
hashing so the CID is reproducible across processes regardless of any set-iteration order inside
concentration (verified stable under PYTHONHASHSEED=random); EAVT is an unordered set, so order
carries no meaning. Append-only. WHAT STAYS GATED (G7/G8): no live ingest, no live-node push, no
live social posting (posts are dry-run, owned by analyze.py/social.py). Stdlib only.
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
from weave import concentration, weave  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "data"
SEED = DATA / "seed-relation-graph.kotoba.edn"
LOG = DATA / "keizu.datoms.kotoba.edn"
BASE_AS_OF = 20260609


def _canonical_order(datoms: list[list]) -> list[list]:
    """Sort datoms by canonical JSON so the tx is DETERMINISTIC regardless of any set-iteration
    order inside concentration (PYTHONHASHSEED-randomized). EAVT assertions are an unordered set,
    so a canonical sort makes the content-addressed CID reproducible / resume-safe."""
    return sorted(datoms, key=lambda d: json.dumps(d, ensure_ascii=False, sort_keys=True))


def run_cycle(cycle: int, seed_path: pathlib.Path = SEED, log_path: pathlib.Path = LOG) -> dict:
    """One autonomous heartbeat: observe → weave (validate) → concentration → persist a
    content-addressed Datom transaction (graph + derived :keizu.conc/* signals). cycle drives
    tx-id + as-of."""
    g = weave(load_edn(seed_path))                # observe + VALIDATE (raises on any gate)
    c = concentration(g)                          # aggregate, edge-primary (G4)
    datoms = _canonical_order(graph_datoms(g) + derived_datoms(c))  # deterministic / resume-safe
    tx = make_tx(datoms, tx_id=cycle, as_of=BASE_AS_OF + cycle, prev_cid=head_cid(log_path))
    cid = append_tx(tx, log_path)                 # PERSIST to append-only LOCAL kotoba log
    return {
        "cycle": cycle,
        "nodes": c["node_count"],
        "rels": c["rel_count"],
        "committees": c["committee_count"],
        "money": c["money_count"],
        "money_hhi": c["money_concentration"]["hhi"],
        "revolving": len(c["revolving_door"]),
        "award_fund": len(c["award_and_fund"]),
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
    ap = argparse.ArgumentParser(description="keizu autonomous government-power-relations loop")
    ap.add_argument("--cycles", type=int, default=3, help="number of self-paced heartbeats")
    ap.add_argument("--seed", type=pathlib.Path, default=SEED, help="relation-graph seed EDN (offline)")
    ap.add_argument("--log", type=pathlib.Path, default=LOG, help="kotoba Datom log path")
    ap.add_argument("--fresh", action="store_true", help="start a fresh log (remove existing)")
    args = ap.parse_args()
    if args.fresh and args.log.exists():
        args.log.unlink()
    res = run_autonomous(args.cycles, seed_path=args.seed, log_path=args.log)
    print("# keizu (系図) — AUTONOMOUS government-power-relations over the kotoba Datom log "
          "(offline seed, LOCAL persist; live ingest / posting stays G7/G8-gated)\n")
    for bt in res["beats"]:
        print(f"  ♥ cycle {bt['cycle']}: {bt['nodes']} nodes / {bt['rels']} rels / "
              f"{bt['committees']} committees / {bt['money']} money · money-HHI {bt['money_hhi']} "
              f"· revolving {bt['revolving']} · award-fund {bt['award_fund']} "
              f"+{bt['datoms']} datoms → cid {bt['cid'][:14]}…")
    ch = res["chain"]
    print(f"\n  log: {res['log_length']} tx · head {res['head_cid'][:14]}… · "
          f"chain {'OK ✓' if ch['ok'] else 'BROKEN at ' + str(ch['broken_at'])} · "
          f"accountability map, never a target-list; edge-primary, non-adjudicating (G4)")
