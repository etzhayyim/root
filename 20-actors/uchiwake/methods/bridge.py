#!/usr/bin/env python3
"""bridge.py — uchiwake 内訳 LOCAL→LIVE kotoba-node push leg (exactly-once, G7-gated).
ADR-2606081800 (mirrors ibuki `methods/kotoba_bridge.py`, ADR-2606101200).

autorun.py persists the heartbeat to the LOCAL append-only kotoba Datom log. This module is the
separate, operator-gated leg that pushes those local transactions to a LIVE kotoba node (the
`datomic.transact` XRPC at :8077) and records an exactly-once cursor back on the local log, so the
live graph can always be mapped to the local commit-DAG and a crash / re-run never double-sends.

DISCIPLINE (constitution-preserving):
  - The actual network push is gated by `UCHIWAKE_KOTOBA_LIVE=1` (Council + operator). With the
    gate unset, `push()` refuses; the cursor/replay logic below is pure and runs offline.
  - no-server-key (G12): the push carries an UNSIGNED public-DID operator bearer — uchiwake holds
    no GS1/GLEIF/kotoba write key. Read-only against upstream records.
  - exactly-once: each push appends ONE `:bridge/*` checkpoint datom (the highest local tx-id
    sent). On replay the LAST checkpoint wins; only tx-ids beyond it are pending.
  - provenance: every remote transaction carries `:uchiwake.tx/{id,local-cid,local-prev,as-of}`
    so the remote graph round-trips to the local DAG.

stdlib only. Usage:
    python3 bridge.py --status                       # show the cursor (offline; no network)
    UCHIWAKE_KOTOBA_LIVE=1 python3 bridge.py --push   # G7 (refuses unless gated)
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kotoba import (LOG_DEFAULT, append_tx, head_cid, make_tx, read_log,  # noqa: E402
                    _edn_val)

GRAPH_DEFAULT = "uchiwake"
ENDPOINT_DEFAULT = os.environ.get("UCHIWAKE_KOTOBA_ENDPOINT",
                                  "http://127.0.0.1:8077/xrpc/com.kotoba.datomic.transact")
BASE_AS_OF = 26060816  # bridge-checkpoint as-of base (distinct from the heartbeat's 20260616)


def graph_cid(name: str) -> str:
    """The kotoba graph identifier for a graph NAME: KotobaCid::from_bytes(name), dag-cbor (0x71)
    multihash sha2-256 — the same CID a kotoba node derives for the named graph (ibuki parity)."""
    raw = bytes([0x01, 0x71, 0x12, 0x20]) + hashlib.sha256(name.encode("utf-8")).digest()
    return "b" + base64.b32encode(raw).decode("ascii").rstrip("=").lower()


def bridge_state(txs: list[dict]) -> dict:
    """Replay the durable push cursor from the local log: the LAST `:bridge/*` checkpoint wins.
    Returns {pushed_to, parent_commit}. A `:bridge/*` checkpoint is itself a normal local tx."""
    pushed_to, parent = 0, ""
    for tx in txs:
        for d in tx.get(":tx/datoms", []):
            # d = [:db/add <e> <attr> <value>]
            if len(d) < 4:
                continue
            _op, _e, a, v = d[0], d[1], d[2], d[3]
            if a == ":bridge/pushed-to-tx":
                pushed_to = v
            elif a == ":bridge/parent-commit":
                parent = v
    return {"pushed_to": pushed_to, "parent_commit": parent}


def pending_txs(txs: list[dict], state: dict) -> list[dict]:
    """The heartbeat transactions not yet pushed (id beyond the cursor; excludes `:bridge/*`
    checkpoint txs themselves)."""
    out = []
    for tx in txs:
        if tx.get(":tx/id", 0) <= state["pushed_to"]:
            continue
        if any(len(d) >= 3 and str(d[2]).startswith(":bridge/") for d in tx.get(":tx/datoms", [])):
            continue  # a checkpoint tx is not itself product data to push
        out.append(tx)
    return out


def tx_to_edn_vec(tx: dict) -> str:
    """One local transaction → the `tx_edn` string the transact lexicon takes: an EDN vector of
    [:db/add e a v] forms + `:uchiwake.tx/*` provenance meta, so the remote graph always maps
    back to the local commit-DAG."""
    meta_e = f"uchiwake-tx-{tx[':tx/id']}"
    forms = list(tx[":tx/datoms"]) + [
        [":db/add", meta_e, ":uchiwake.tx/id", tx[":tx/id"]],
        [":db/add", meta_e, ":uchiwake.tx/local-cid", tx[":tx/cid"]],
        [":db/add", meta_e, ":uchiwake.tx/local-prev", tx[":tx/prev"]],
        [":db/add", meta_e, ":uchiwake.tx/as-of", tx[":tx/as-of"]],
    ]
    return "[" + " ".join("[" + " ".join(_edn_val(x) for x in d) + "]" for d in forms) + "]"


def make_checkpoint(pending: list[dict], graph: str, endpoint: str, remote_cids: list[str],
                    log_path: pathlib.Path) -> dict:
    """Build the ONE exactly-once `:bridge/*` checkpoint tx recording the highest local tx-id
    pushed + the remote endpoint + the remote tx CIDs. Appended AFTER the remote transact
    succeeds. Pure — no I/O (the caller appends it)."""
    beat = bridge_state(read_log(log_path))["pushed_to"]  # informational
    e = f"bridge-{pending[-1][':tx/id']}"
    from urllib.parse import urlsplit
    datoms = [
        [":db/add", e, ":bridge/pushed-to-tx", pending[-1][":tx/id"]],
        [":db/add", e, ":bridge/parent-commit", head_cid(log_path)],
        [":db/add", e, ":bridge/graph", graph],
        [":db/add", e, ":bridge/graph-cid", graph_cid(graph)],
        [":db/add", e, ":bridge/endpoint-host", urlsplit(endpoint).netloc],
        [":db/add", e, ":bridge/remote-tx-cids", list(remote_cids)],
        [":db/add", e, ":bridge/count", len(pending)],
    ]
    return make_tx(datoms, tx_id=BASE_AS_OF + beat + 1, as_of=BASE_AS_OF + beat + 1,
                   prev_cid=head_cid(log_path))


def push(graph: str = GRAPH_DEFAULT, endpoint: str = ENDPOINT_DEFAULT,
         log_path: pathlib.Path = LOG_DEFAULT) -> dict:
    """Push every pending heartbeat tx to the LIVE kotoba node, then append one exactly-once
    `:bridge/*` checkpoint. G7: refuses unless `UCHIWAKE_KOTOBA_LIVE=1`."""
    if os.environ.get("UCHIWAKE_KOTOBA_LIVE") != "1":
        sys.exit("REFUSED (G7): live-node push requires UCHIWAKE_KOTOBA_LIVE=1 + Council. "
                 "Use --status to inspect the cursor offline.")
    txs = read_log(log_path)
    state = bridge_state(txs)
    pending = pending_txs(txs, state)
    if not pending:
        return {"pushed": 0, "pushed_to": state["pushed_to"], "graph_cid": graph_cid(graph)}
    import json as _json
    import urllib.request  # imported inside the gated path only (G7)
    remote_cids = []
    for tx in pending:
        body = _json.dumps({
            "graph": graph,
            "tx_edn": tx_to_edn_vec(tx),
            "expected_parent": state["parent_commit"],
        }).encode("utf-8")
        req = urllib.request.Request(endpoint, data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:   # noqa: S310 (operator-supplied endpoint)
            resp = _json.load(r)
        remote_cids.append(resp.get("tx_cid") or resp.get("cid") or "")
        state["parent_commit"] = remote_cids[-1]
    ck = make_checkpoint(pending, graph, endpoint, remote_cids, log_path)
    append_tx(ck, log_path)
    return {"pushed": len(pending), "pushed_to": pending[-1][":tx/id"],
            "graph_cid": graph_cid(graph), "remote_cids": remote_cids}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="uchiwake local→live kotoba-node push (exactly-once)")
    ap.add_argument("--status", action="store_true", help="show the cursor offline (no network)")
    ap.add_argument("--push", action="store_true", help="push pending txs to the live node (G7)")
    ap.add_argument("--graph", default=GRAPH_DEFAULT)
    ap.add_argument("--endpoint", default=ENDPOINT_DEFAULT)
    ap.add_argument("--log", type=pathlib.Path, default=LOG_DEFAULT)
    args = ap.parse_args()
    txs = read_log(args.log)
    state = bridge_state(txs)
    pend = pending_txs(txs, state)
    print(f"# uchiwake kotoba bridge — graph {args.graph} ({graph_cid(args.graph)[:16]}…)")
    print(f"  local log: {len(txs)} tx · cursor pushed-to {state['pushed_to']} · "
          f"pending {len(pend)} · parent-commit {state['parent_commit'][:14] or '∅'}")
    if args.push:
        res = push(args.graph, args.endpoint, args.log)
        print(f"  pushed {res['pushed']} tx → cursor now {res['pushed_to']}")
    elif not args.status:
        print("  (use --status to inspect, or UCHIWAKE_KOTOBA_LIVE=1 --push to push; G7)")
