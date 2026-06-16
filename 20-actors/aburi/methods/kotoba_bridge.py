#!/usr/bin/env python3
"""aburi 炙り → kotoba engine transact bridge (R0: dry-run default, network INJECTED).
ADR-2606161630 (the ibuki kotoba_bridge pattern, ADR-2606101200).

Takes the member's local aburi exposure log (the append-only commit-DAG `autorun` built) and
transacts the un-pushed transactions to the LIVE kotoba engine at :8077, one `datomic.transact`
call per local tx, oldest first. Properties:

  - exactly-once cursor — a durable `:aburi-bridge/*` checkpoint ON the local log records the
    highest local tx id pushed + the remote parent commit; a re-run pushes only what is new.
  - commit-DAG chaining — the previous push's remote `commit_cid` is sent as `expected_parent`
    (optimistic concurrency / fork detection on the engine side).
  - provenance — every pushed tx carries `:aburi.tx/{id,local-cid,local-prev,as-of}`.
  - host allowlist — only the kotoba fleet (loopback + EVO-X2 LAN, ADR-2605215000).
  - no-server-key — the operator bearer is an UNSIGNED token whose `sub` is the node's PUBLIC
    operator DID (an env var, never a secret); no key material is held or read. The network leg is
    INJECTED (tests pass a fake), so the loop is a pure function and runs offline.
  - G7 dry-run by default — a live push requires ABURI_KOTOBA_LIVE=1 AND member-sig + operator +
    Council (the member's exposure leaving the device is an outward act); otherwise it EXPORTS the
    transact bodies without sending. R0 = dry-run; live is the Council-gated step.

    python3 methods/kotoba_bridge.py                 # dry-run: show pending transacts
    ABURI_KOTOBA_LIVE=1 ABURI_KOTOBA_OPERATOR_DID=did:web:… python3 methods/kotoba_bridge.py
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kotoba  # noqa: E402

ALLOWED_KOTOBA_HOSTS = frozenset({"127.0.0.1:8077", "localhost:8077", "192.168.1.70:8077"})
DEFAULT_ENDPOINT = "http://127.0.0.1:8077/xrpc/com.etzhayyim.apps.kotoba.datomic.transact"
DEFAULT_GRAPH = "aburi"
LIVE_ENV = "ABURI_KOTOBA_LIVE"
ENV_OPERATOR_DID = "ABURI_KOTOBA_OPERATOR_DID"
BASE_AS_OF = 2606161630


class KotobaBoundaryViolation(ValueError):
    """Raised when a transact push targets a host outside the kotoba fleet allowlist."""


def assert_kotoba(endpoint: str) -> None:
    parts = urlsplit(endpoint)
    if parts.scheme != "http" or parts.netloc.lower() not in ALLOWED_KOTOBA_HOSTS:
        raise KotobaBoundaryViolation(
            f"kotoba endpoint {endpoint!r} is outside the fleet allowlist "
            f"({sorted(ALLOWED_KOTOBA_HOSTS)}) — ADR-2605215000")


def tx_to_edn_vec(tx: dict) -> str:
    """One local transaction → the `tx_edn` string the transact lexicon takes: an EDN vector of
    [:db/add e a v] forms + `:aburi.tx/*` provenance meta."""
    meta_e = f"aburi-tx-{tx[':tx/id']}"
    forms = list(tx[":tx/datoms"]) + [
        [":db/add", meta_e, ":aburi.tx/id", tx[":tx/id"]],
        [":db/add", meta_e, ":aburi.tx/local-cid", tx[":tx/cid"]],
        [":db/add", meta_e, ":aburi.tx/local-prev", tx[":tx/prev"]],
        [":db/add", meta_e, ":aburi.tx/as-of", tx[":tx/as-of"]],
    ]
    return "[" + " ".join("[" + " ".join(kotoba._edn_val(x) for x in d) + "]" for d in forms) + "]"


def operator_bearer() -> str:
    """Unsigned JWT: {alg:none}.{sub: node_public_did}.unsigned-loopback. No key held (the `sub`
    is a PUBLIC operator DID from an env var)."""
    import base64
    did = os.environ.get(ENV_OPERATOR_DID, "")
    if not did:
        raise KotobaBoundaryViolation(
            f"live push requires {ENV_OPERATOR_DID} (the node's PUBLIC operator DID, not a secret)")
    enc = lambda d: base64.urlsafe_b64encode(  # noqa: E731
        json.dumps(d, separators=(",", ":")).encode()).decode().rstrip("=")
    return f"{enc({'alg': 'none'})}.{enc({'sub': did})}.unsigned-loopback"


def _default_transport(url: str, body: dict, timeout_s: float = 60.0) -> dict:
    assert_kotoba(url)
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {operator_bearer()}"}
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"kotoba transact HTTP {e.code}: {e.read().decode()[:200]}") from None


def bridge_state(txs: list[dict]) -> dict:
    """Replay the durable push cursor: the LAST `:aburi-bridge/*` checkpoint wins."""
    pushed_to, parent = 0, ""
    for tx in txs:
        for d in tx.get(":tx/datoms", []):
            if len(d) < 4:
                continue
            _op, _e, a, v = d[0], d[1], d[2], d[3]
            if a == ":aburi-bridge/pushed-to-tx":
                pushed_to = v
            elif a == ":aburi-bridge/parent-commit":
                parent = v
    return {"pushed_to": pushed_to, "parent_commit": parent}


def graph_id(graph: str) -> str:
    return graph if (graph.startswith("b") and len(graph) > 40) else graph


def push(log_path: pathlib.Path = None, *, graph: str = DEFAULT_GRAPH,
         endpoint: str = DEFAULT_ENDPOINT, transport=None, live: bool | None = None) -> dict:
    """Push every local tx the cursor has not yet sent (oldest first). Dry-run unless live.
    Transport is INJECTED (None → real HTTP; tests pass a fake). After a live push, ONE
    `:aburi-bridge/*` checkpoint tx is appended (the exactly-once cursor)."""
    if log_path is None:
        log_path = kotoba.LOG_DEFAULT
    assert_kotoba(endpoint)
    g = graph_id(graph)

    txs = kotoba.read_log(log_path)
    state = bridge_state(txs)
    pending = [tx for tx in txs if tx.get(":tx/id", 0) > state["pushed_to"]
               and not _is_bridge_tx(tx)]
    bodies = [{"graph": g, "tx_edn": tx_to_edn_vec(tx)} for tx in pending]

    is_live = (os.environ.get(LIVE_ENV) == "1") if live is None else live
    if not is_live:
        return {"mode": "dry-run", "pending": len(bodies), "bodies": bodies,
                "pushed_to": state["pushed_to"], "head": kotoba.head_cid(log_path)}

    t = transport or _default_transport
    remote_cids, datoms_confirmed = [], 0
    last_commit = state["parent_commit"]
    for tx, body in zip(pending, bodies):
        if last_commit:
            body["expected_parent"] = last_commit
        out = t(endpoint, body)
        if out.get("status") not in ("ok", "committed", "success"):
            raise RuntimeError(f"kotoba transact refused tx {tx[':tx/id']}: {out}")
        remote_cids.append(out.get("tx_cid", ""))
        last_commit = out.get("commit_cid", "") or last_commit
        datoms_confirmed += out.get("datom_count", len(tx[":tx/datoms"]))

    if pending:
        beat = len(txs) + 1
        e = f"aburi-bridge-{beat}"
        ck_datoms = [
            kotoba.add(e, ":aburi-bridge/pushed-to-tx", pending[-1][":tx/id"]),
            kotoba.add(e, ":aburi-bridge/parent-commit", last_commit),
            kotoba.add(e, ":aburi-bridge/graph", graph),
            kotoba.add(e, ":aburi-bridge/endpoint-host", urlsplit(endpoint).netloc),
            kotoba.add(e, ":aburi-bridge/remote-tx-cids", remote_cids),
            kotoba.add(e, ":aburi-bridge/beat", beat),
        ]
        ck = kotoba.make_tx(ck_datoms, tx_id=beat, as_of=BASE_AS_OF + beat,
                            prev_cid=kotoba.head_cid(log_path))
        kotoba.append_tx(ck, log_path)

    return {"mode": "live", "pushed": len(pending), "remote_tx_cids": remote_cids,
            "parent_commit": last_commit, "datoms_confirmed": datoms_confirmed,
            "pushed_to": pending[-1][":tx/id"] if pending else state["pushed_to"]}


def _is_bridge_tx(tx: dict) -> bool:
    return any(len(d) >= 3 and str(d[2]).startswith(":aburi-bridge/")
              for d in tx.get(":tx/datoms", []))


def main(argv):
    log = pathlib.Path(argv[argv.index("--log") + 1]) if "--log" in argv else kotoba.LOG_DEFAULT
    res = push(log)
    if res["mode"] == "dry-run":
        print(f"# aburi kotoba-bridge DRY-RUN — {res['pending']} tx pending past cursor "
              f"{res['pushed_to']} (set {LIVE_ENV}=1 + member-sig + Council to push)")
    else:
        print(f"# aburi kotoba-bridge LIVE — pushed {res['pushed']} tx, "
              f"{res['datoms_confirmed']} datoms, head commit {res['parent_commit'][:18]}…")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
