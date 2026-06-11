#!/usr/bin/env python3
"""kotoba.py — hakoniwa 箱庭 kotoba Datom-log writer. ADR-2606111500 + ADR-2605312345.

The substrate boundary (root CLAUDE.md): canonical state is the **kotoba Datom log** —
content-addressed EAVT assertions, append-only (非終末論). This is hakoniwa's write path onto
that log. The log materialises as an append-only EDN transaction file
(`data/hakoniwa.datoms.kotoba.edn`); each transaction is content-addressed (sha256 over its
canonical datoms + the previous tx CID → a commit-DAG), mirroring shionome (ADR-2606072200)
and the content-addressed head of ADR-2606066000. Not RisingWave / SQL / Datomic (N7).

  - world_datoms(nodes, edges, meta) → EAVT for the box (personas / entities / signals /
    outcomes / 縁 / run-config). Every persona carries :persona/synthetic true (G1).
  - distribution_datoms(dist)        → EAVT for the outcome DISTRIBUTION quantiles. There is
    NO point datom — :forecast/point-asserted false is asserted instead (G2).
  - post_datoms(posts)               → EAVT for each social post.
  - make_tx / append_tx / read_log / head_cid / verify_chain — the content-addressed DAG.

EAVT = [op entity attribute value]; op is :db/add only (append-only — no :db/retract,
非終末論). Stdlib only. Deterministic (caller supplies tx_id + as-of; no wall clock).
"""
from __future__ import annotations
import hashlib
import json
import pathlib
from typing import Any

LOG_DEFAULT = pathlib.Path(__file__).resolve().parents[1] / "data" / "hakoniwa.datoms.kotoba.edn"


def _add(entity: str, attr: str, value: Any) -> list:
    return [":db/add", entity, attr, value]


def world_datoms(nodes: dict, edges: list, meta: dict) -> list[list]:
    """Flatten the box into append-only EAVT assertions (nodes, 縁, run config)."""
    out: list[list] = []
    for nid, n in nodes.items():
        for a, v in n.items():
            if a == ":sim/id" or v is None:
                continue
            out.append(_add(nid, a, v))
    for e in edges:
        eid = f"en.{e[':en/from']}.{e[':en/kind'].lstrip(':')}.{e[':en/to']}"
        for a, v in e.items():
            if v is None:
                continue
            out.append(_add(eid, a, v))
    run = "run.hakoniwa"
    for a, v in [(":run/steps", meta.get("steps")), (":run/replicas", meta.get("replicas")),
                 (":run/seed", meta.get("seed")), (":run/jitter", meta.get("jitter")),
                 (":run/kernel", ":friedkin-johnsen")]:
        if v is not None:
            out.append(_add(run, a, v))
    return out


def distribution_datoms(dist: dict, outcome: str = "outcome.adoption") -> list[list]:
    """The outcome DISTRIBUTION as append-only EAVT — quantiles + mean/stdev. NO point datom;
    :forecast/point-asserted false is the structural marker (G2 / 非終末論)."""
    out: list[list] = []
    for qk, qv in dist["quantiles"].items():
        out.append(_add(outcome, f":forecast/{qk.lstrip(':')}", round(qv, 6)))
    out.append(_add(outcome, ":forecast/mean", round(dist["mean"], 6)))
    out.append(_add(outcome, ":forecast/stdev", round(dist["stdev"], 6)))
    out.append(_add(outcome, ":forecast/kind", ":distribution"))
    out.append(_add(outcome, ":forecast/point-asserted", False))   # G2 — never a point
    return out


def post_datoms(posts: list[dict], prefix: str = "post") -> list[list]:
    out: list[list] = []
    for i, p in enumerate(posts):
        pid = f"{prefix}-{p.get(':post/subject', i)}"
        for a, v in p.items():
            if v is None:
                continue
            out.append(_add(pid, a, v))
    return out


def _canonical(datoms: list[list], prev_cid: str) -> bytes:
    return json.dumps({"prev": prev_cid, "datoms": datoms},
                      ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def tx_cid(datoms: list[list], prev_cid: str = "") -> str:
    """Content address of a transaction = sha256 over (prev_cid, datoms). Linking prev_cid makes
    the log a commit-DAG (tampering any earlier tx breaks every later CID)."""
    return "b" + hashlib.sha256(_canonical(datoms, prev_cid)).hexdigest()


def make_tx(datoms: list[list], *, tx_id: int, as_of: int, prev_cid: str = "") -> dict:
    return {
        ":tx/id": tx_id,
        ":tx/as-of": as_of,
        ":tx/prev": prev_cid,
        ":tx/cid": tx_cid(datoms, prev_cid),
        ":tx/count": len(datoms),
        ":tx/datoms": datoms,
    }


def _edn_val(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        if v.startswith(":"):
            return v
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + " ".join(_edn_val(x) for x in v) + "]"
    return json.dumps(str(v), ensure_ascii=False)


def _tx_to_edn(tx: dict) -> str:
    datoms = " ".join("[" + " ".join(_edn_val(x) for x in d) + "]" for d in tx[":tx/datoms"])
    return (f'{{:tx/id {tx[":tx/id"]} :tx/as-of {tx[":tx/as-of"]} '
            f':tx/prev {json.dumps(tx[":tx/prev"])} :tx/cid {json.dumps(tx[":tx/cid"])} '
            f':tx/count {tx[":tx/count"]} :tx/datoms [{datoms}]}}')


def append_tx(tx: dict, log_path: pathlib.Path = LOG_DEFAULT) -> str:
    """Append ONE transaction to the append-only log (never rewrites). Returns the tx CID. This
    is the only mutation: the log only ever grows (非終末論)."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.write_text(";; hakoniwa 箱庭 kotoba Datom log — append-only EAVT transactions "
                            "(content-addressed DAG). DO NOT hand-edit. ADR-2606111500.\n",
                            encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(_tx_to_edn(tx) + "\n")
    return tx[":tx/cid"]


def _read_tokens(s: str):
    import re
    tok = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
    for m in tok.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t


def _atom(t: str):
    if t.startswith('"'):
        return json.loads(t)
    if t == "true":
        return True
    if t == "false":
        return False
    if t == "nil":
        return None
    if t.startswith(":"):
        return t
    try:
        return int(t)
    except ValueError:
        try:
            return float(t)
        except ValueError:
            return t


_END = object()


def _parse(it):
    t = next(it)
    if t == "[":
        out = []
        while (x := _parse(it)) is not _END:
            out.append(x)
        return out
    if t == "{":
        out = {}
        while (k := _parse(it)) is not _END:
            out[k] = _parse(it)
        return out
    if t in ("]", "}"):
        return _END
    return _atom(t)


def read_log(log_path: pathlib.Path = LOG_DEFAULT) -> list[dict]:
    if not log_path.exists():
        return []
    txs = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        txs.append(_parse(_read_tokens(line)))
    return txs


def head_cid(log_path: pathlib.Path = LOG_DEFAULT) -> str:
    txs = read_log(log_path)
    return txs[-1][":tx/cid"] if txs else ""


def verify_chain(log_path: pathlib.Path = LOG_DEFAULT) -> dict:
    """Recompute every CID from its datoms + prev and verify the DAG is intact. The integrity
    proof of the append-only log. Returns {ok, length, broken_at}."""
    txs = read_log(log_path)
    prev = ""
    for i, tx in enumerate(txs):
        expect = tx_cid(tx.get(":tx/datoms", []), prev)
        if tx.get(":tx/cid") != expect or tx.get(":tx/prev") != prev:
            return {"ok": False, "length": len(txs), "broken_at": i}
        prev = tx[":tx/cid"]
    return {"ok": True, "length": len(txs), "broken_at": -1}
