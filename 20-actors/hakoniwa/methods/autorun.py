#!/usr/bin/env python3
"""autorun.py — hakoniwa 箱庭 AUTONOMOUS heartbeat loop on the kotoba Datom log. ADR-2606111500.

"kotoba で自律的に稼働する" for hakoniwa, in the constitution-permitted form. Each heartbeat the
actor runs its whole pipeline ITSELF, with no human in the loop:

    load box (synthetic personas) → simulate (Friedkin-Johnsen K-replica ensemble)
      → distribution (quantiles + histogram; G2 distribution-only)
      → narrate (Murakumo fleet, graceful template fallback; G5)
      → draft + EMIT a social post (G2 no-point + G3 no-steer scanned)
      → PERSIST a content-addressed transaction (box + distribution + post) to the append-only
        kotoba Datom log (非終末論 / commit-DAG)

R1 — LIVE OPERATION + SOCIAL EMISSION AUTHORIZED (Council Lv7+ unanimity, founder 1/1,
2026-06-11). The post status is `:published` when a member-DID author is supplied (G7 — the
member signs, the server never does). Persistence to the canonical kotoba Datom log IS the
substrate emission; the external AT-Proto relay is a downstream projection delivered by an
operator transport when present (substrate-only otherwise — honest, never a silent no-op).

The loop is deterministic + idempotent-by-CID: it links each tx to the previous one's content
address, so the log is a verifiable commit-DAG that only ever grows. The caller supplies the
cycle index (→ tx-id + as-of), so a re-run reproduces the same CIDs (resume-safe).

Stdlib only.
"""
from __future__ import annotations
import argparse
import pathlib

import world as W
import simulate as S
import distribution as D
import murakumo as M
import social as SOC
from kotoba import (append_tx, distribution_datoms, head_cid, make_tx, post_datoms,
                    read_log, verify_chain, world_datoms)

HERE = pathlib.Path(__file__).resolve().parent
SEED = HERE.parent / "data" / "seed-scenario.kotoba.edn"
LOG = HERE.parent / "data" / "hakoniwa.datoms.kotoba.edn"
BASE_AS_OF = 20260611


def _scenario_label(nodes: dict) -> str:
    outs = W.outcomes(nodes)
    if outs:
        return next(iter(outs.values())).get(":sim/label", "outcome")
    return "outcome"


def run_cycle(cycle: int, *, seed_path: pathlib.Path = SEED, log_path: pathlib.Path = LOG,
              steps: int = S.DEFAULT_STEPS, replicas: int = S.DEFAULT_REPLICAS,
              seed: int = S.DEFAULT_SEED, author: str = "", publish: bool = False,
              transport=None) -> dict:
    """One autonomous heartbeat. cycle drives tx-id + as-of (deterministic / resume-safe)."""
    nodes, edges = W.load(seed_path)                       # G1: refuses any non-synthetic persona
    results, meta = S.ensemble(nodes, edges, steps=steps, replicas=replicas, seed=seed)
    dist = D.distribution(results)
    label = _scenario_label(nodes)

    narr = M.narrate(label, dist)                          # G5: Murakumo, graceful fallback
    status = ":published" if (publish and author) else ":dry-run"
    post = SOC.draft_distribution_post(label, dist, narration=narr["text"],
                                       author=author, status=status)
    post[":post/narration-via"] = narr["via"]
    receipt = SOC.emit(post, transport=transport)          # G2/G3 re-scanned at the boundary

    datoms = (world_datoms(nodes, edges, meta)
              + distribution_datoms(dist)
              + post_datoms([post], prefix=f"post-c{cycle}"))
    tx = make_tx(datoms, tx_id=cycle, as_of=BASE_AS_OF + cycle, prev_cid=head_cid(log_path))
    cid = append_tx(tx, log_path)                          # PERSIST to append-only kotoba log
    return {
        "cycle": cycle,
        "scenario": label,
        "p50": dist["quantiles"][":p50"],
        "spread": (dist["quantiles"][":p90"] - dist["quantiles"][":p10"]),
        "narration_via": narr["via"],
        "post_status": post[":post/status"],
        "emit": receipt,
        "datoms": len(datoms),
        "cid": cid,
    }


def run_autonomous(cycles: int = 3, *, seed_path: pathlib.Path = SEED, log_path: pathlib.Path = LOG,
                   author: str = "", publish: bool = False, transport=None) -> dict:
    """Drive `cycles` self-paced heartbeats. Each appends one content-addressed tx. Returns the
    run summary + final head CID + chain verification."""
    beats = [run_cycle(c, seed_path=seed_path, log_path=log_path, author=author,
                       publish=publish, transport=transport)
             for c in range(1, cycles + 1)]
    return {
        "cycles": cycles,
        "beats": beats,
        "log_length": len(read_log(log_path)),
        "head_cid": head_cid(log_path),
        "chain": verify_chain(log_path),
        "fleet": M.fleet_available(),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="hakoniwa 箱庭 autonomous heartbeat loop")
    ap.add_argument("--cycles", type=int, default=3, help="number of self-paced heartbeats")
    ap.add_argument("--log", type=pathlib.Path, default=LOG, help="kotoba Datom log path")
    ap.add_argument("--fresh", action="store_true", help="start a fresh log (remove existing)")
    ap.add_argument("--author", default="", help="member DID (required to :publish; G7)")
    ap.add_argument("--publish", action="store_true",
                    help="emit :published posts (R1-authorized; needs --author). Default dry-run.")
    args = ap.parse_args()
    if args.fresh and args.log.exists():
        args.log.unlink()
    res = run_autonomous(args.cycles, log_path=args.log, author=args.author, publish=args.publish)
    mode = "LIVE :published" if args.publish and args.author else "dry-run"
    print(f"# hakoniwa 箱庭 — AUTONOMOUS run over the kotoba Datom log  "
          f"(mode={mode}, Murakumo fleet={'up' if res['fleet'] else 'offline→template fallback'})\n")
    for b in res["beats"]:
        print(f"  ♥ cycle {b['cycle']}: {b['scenario'][:28]:<28} "
              f"p50={b['p50']:.2f} spread={b['spread']:.2f} "
              f"narrate={b['narration_via']:<18} post={b['post_status']:<11} "
              f"+{b['datoms']} datoms → cid {b['cid'][:14]}…")
    ch = res["chain"]
    print(f"\n  log: {res['log_length']} tx · head {res['head_cid'][:14]}… · "
          f"chain {'OK ✓' if ch['ok'] else 'BROKEN at ' + str(ch['broken_at'])}")
    print(f"  emission: substrate=kotoba-datom-log (canonical) · "
          f"external_relay={res['beats'][-1]['emit']['external_relay']}")
