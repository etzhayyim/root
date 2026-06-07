"""autorun.py — 潮目 (shionome) AUTONOMOUS heartbeat loop on the kotoba Datom log. ADR-2606072200.

This is what "kotoba で自律的に稼働する" means for shionome, in the constitution-permitted form.
Each heartbeat the actor runs its whole pipeline ITSELF, with no human in the loop:

    observe (load public-source batch) → ingest + VALIDATE (G1/G2/G3, トレードはしない)
      → weave → aggregate concentration (edge-primary, G4)
      → draft DRY-RUN social posts (G5 mirror, G2 no-trade body scan)
      → PERSIST a content-addressed transaction to the append-only kotoba Datom log (G10)

The loop is fully self-driving and idempotent-by-CID: it links each transaction to the
previous one's content address, so the log is a verifiable commit-DAG that only ever grows
(non-eschatological / append-only). It is deterministic — the caller supplies the cycle index,
which drives the tx-id + as-of — so a re-run reproduces the same CIDs (resume-safe).

WHAT STAYS GATED (G8 / G7): this loop NEVER posts to an external network and NEVER ingests
from a live portal. Posts are dry-run; ingest is offline. Live external publication + live
market-data ingest are Council Lv6+ + operator + member-signature gated — the ONE remaining
step is a human gate flip, by constitutional design. Autonomy here = the actor drives its own
observe→analyze→persist cycle over its own substrate, not that it speaks to the world unsupervised.

Stdlib only.
"""

from __future__ import annotations

import argparse
import pathlib

from _edn import load_edn
from kotoba import (append_tx, graph_datoms, head_cid, make_tx, post_datoms,
                    read_log, verify_chain)
from social import draft_netflow_post, draft_regime_post, draft_rotation_post
from weave import concentration, weave

HERE = pathlib.Path(__file__).resolve().parent
SEED = HERE.parent / "data" / "seed-capital-flow-graph.kotoba.edn"
LOG = HERE.parent / "data" / "shionome.datoms.kotoba.edn"
BASE_AS_OF = 20260607


def _draft_posts(g: dict, c: dict) -> list[dict]:
    allsrcs = sorted({s for f in g["flows"] for s in f.get(":flow/sources", [])})
    posts = []
    if allsrcs:
        if c["net_flow_by_bucket"]:
            posts.append(draft_netflow_post(c["net_flow_by_bucket"], allsrcs))
        if c["rotation_pairs"]:
            posts.append(draft_rotation_post(c["rotation_pairs"], allsrcs))
        posts.append(draft_regime_post(c["regime"], allsrcs))
    return posts


def run_cycle(cycle: int, seed_path: pathlib.Path = SEED, log_path: pathlib.Path = LOG) -> dict:
    """One autonomous heartbeat: observe → validate → weave → analyze → dry-run post → persist
    a content-addressed Datom transaction. Returns a heartbeat summary. cycle drives tx-id +
    as-of (deterministic / resume-safe)."""
    g = weave(load_edn(seed_path))                       # observe + VALIDATE (raises on any gate)
    c = concentration(g)                                 # aggregate, edge-primary (G4)
    posts = _draft_posts(g, c)                           # DRY-RUN, no-trade body-scanned (G2/G5)
    datoms = graph_datoms(g) + post_datoms(posts, prefix=f"post-c{cycle}")
    tx = make_tx(datoms, tx_id=cycle, as_of=BASE_AS_OF + cycle, prev_cid=head_cid(log_path))
    cid = append_tx(tx, log_path)                        # PERSIST to append-only kotoba log (G10)
    return {
        "cycle": cycle,
        "regime": c["regime"]["regime"],
        "top_inflow": (c["net_flow_by_bucket"][0]["label"] if c["net_flow_by_bucket"] else "—"),
        "datoms": len(datoms),
        "posts": len(posts),
        "cid": cid,
    }


def run_autonomous(cycles: int = 3, seed_path: pathlib.Path = SEED,
                   log_path: pathlib.Path = LOG) -> dict:
    """Drive `cycles` self-paced heartbeats. Each appends one content-addressed transaction to
    the kotoba Datom log. Returns the run summary + final head CID + chain verification."""
    beats = [run_cycle(c, seed_path, log_path) for c in range(1, cycles + 1)]
    return {
        "cycles": cycles,
        "beats": beats,
        "log_length": len(read_log(log_path)),
        "head_cid": head_cid(log_path),
        "chain": verify_chain(log_path),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="潮目 (shionome) autonomous heartbeat loop")
    ap.add_argument("--cycles", type=int, default=3, help="number of self-paced heartbeats")
    ap.add_argument("--log", type=pathlib.Path, default=LOG, help="kotoba Datom log path")
    ap.add_argument("--fresh", action="store_true", help="start a fresh log (remove existing)")
    args = ap.parse_args()
    if args.fresh and args.log.exists():
        args.log.unlink()
    res = run_autonomous(args.cycles, log_path=args.log)
    print("# 潮目 (shionome) — AUTONOMOUS run over the kotoba Datom log "
          "(dry-run posts, offline ingest; live publish/ingest stays G8-gated)\n")
    for b in res["beats"]:
        print(f"  ♥ cycle {b['cycle']}: regime={b['regime']:<13} top-inflow={b['top_inflow']:<14} "
              f"+{b['datoms']} datoms, {b['posts']} dry-run posts → cid {b['cid'][:14]}…")
    ch = res["chain"]
    print(f"\n  log: {res['log_length']} tx · head {res['head_cid'][:14]}… · "
          f"chain {'OK ✓' if ch['ok'] else 'BROKEN at ' + str(ch['broken_at'])}")
