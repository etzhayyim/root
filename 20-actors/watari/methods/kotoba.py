#!/usr/bin/env python3
"""kotoba.py — watari kotoba Datom-log writer (local, content-addressed). ADR-2606041827
+ ADR-2605262130 + ADR-2605312345.

The substrate boundary (root CLAUDE.md): canonical state is the **kotoba Datom log** —
content-addressed EAVT assertions, append-only (非終末論; the fix stream IS the trajectory, the
latest fix IS the current position). watari had a graph + analyzer + an R0 ingest stub but no
self-driving loop and no local log; this module is the **local, autonomous-loop** write path — the
same path shionome / ipaddress / yabai / sukashi / watatsuna use (`methods/autorun.py`): a
self-driving heartbeat appends content-addressed transactions to a local append-only EDN log with
NO external I/O, so watari can run its own observe→analyze→persist live-craft-situation cycle on
the Murakumo fleet without a human or a live node in the loop.

Constitutional posture is preserved by construction (watari hard rules): outputs are
situational-awareness, not surveillance / not targeting (G2 — aggregate lane/chokepoint/approach
density); a craft is a craft, NEVER a person — no position track is linked to a named individual,
no pattern-of-life (G4, the defining gate; operator is a company only). The loop persists exactly
what `analyze.py` already computes, with derived signals flagged :movement/derived.

  - graph_datoms(rows)         → EAVT assertions for every entity (craft / fix / leg / lane).
  - derived_datoms(craft, ln, a) → EAVT assertions for the analyzer's derived :movement/* signals
                                   (chokepoint-transit, lane-load by kind, stale-track tail),
                                   flagged :movement/derived.
  - make_tx / append_tx / read_log / head_cid / verify_chain — content-addressed commit-DAG.

EAVT = [op entity attribute value]; op is :db/add only (append-only — no :db/retract). Stdlib only.
Deterministic: the caller supplies tx_id + as_of (no wall clock) → resume-safe.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import _parse, _tokens  # noqa: E402  (the inline EDN reader lives in analyze.py)

LOG_DEFAULT = (pathlib.Path(__file__).resolve().parents[1] / "data"
               / "watari.datoms.kotoba.edn")

ID_KEYS = (":craft/id", ":craft.fix/id", ":craft.leg/id", ":lane/id")


def _add(entity: str, attr: str, value: Any) -> list:
    """One append-only EAVT assertion: [:db/add <entity> <attr> <value>]."""
    return [":db/add", entity, attr, value]


def graph_datoms(rows: list) -> list[list]:
    """Flatten the moving-craft graph into append-only EAVT assertions. E = the entity's id;
    cardinality-many list values fan out. Persists craft identity / position fixes / legs / lanes
    as-is — the seed carries operator-as-company only, never a person (G4)."""
    out: list[list] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        e = next((r[k] for k in ID_KEYS if k in r), None)
        if e is None:
            continue
        for k, v in r.items():
            if k in ID_KEYS:
                continue
            for item in (v if isinstance(v, list) else [v]):
                out.append(_add(e, k, item))
    return out


def derived_datoms(craft: dict, lanes: dict, a: dict) -> list[list]:
    """Flatten the analyzer's derived :movement/* signals into EAVT assertions, each flagged
    :movement/derived true (aggregate situational-awareness recomputed on read, never re-ingested
    as fact, never a per-craft follow/targeting feed — G2/G4). Mirrors analyze.render_datoms.
    `a` is analyze.analyze()."""
    out: list[list] = []
    for cp in sorted(a["choke_transit"], key=lambda k: -a["choke_transit"][k]):
        e = f"movement-choke-{cp}"
        out += [_add(e, ":movement/chokepoint", cp),
                _add(e, ":movement/chokepoint-transit", a["choke_transit"][cp]),
                _add(e, ":movement/derived", True)]
    for ln in sorted(a["lane_load"], key=lambda k: -a["lane_load"][k]):
        vk = len(a["lane_kind"][ln].get(":vessel", set()))
        ak = len(a["lane_kind"][ln].get(":aircraft", set()))
        e = f"movement-lane-{ln}"
        out += [_add(e, ":movement/lane", ln),
                _add(e, ":movement/lane-load", a["lane_load"][ln]),
                _add(e, ":movement/vessels", vk),
                _add(e, ":movement/aircraft", ak),
                _add(e, ":movement/derived", True)]
    for c in sorted(a["stale"]):
        fx = a["latest"][c]
        e = f"movement-stale-{c}"
        out += [_add(e, ":movement/craft", c),
                _add(e, ":movement/stale", True),
                _add(e, ":movement/last-seen", fx.get(":craft.fix/observed-at", "")),
                _add(e, ":movement/derived", True)]
    return out


def _canonical(datoms: list[list], prev_cid: str) -> bytes:
    return json.dumps({"prev": prev_cid, "datoms": datoms},
                      ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def tx_cid(datoms: list[list], prev_cid: str = "") -> str:
    """Content address = sha256 over (prev_cid, datoms) → a commit-DAG."""
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
        return v if v.startswith(":") else json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + " ".join(_edn_val(x) for x in v) + "]"
    return json.dumps(str(v), ensure_ascii=False)


def _tx_to_edn(tx: dict) -> str:
    datoms = " ".join("[" + " ".join(_edn_val(x) for x in d) + "]" for d in tx[":tx/datoms"])
    return (f'{{:tx/id {tx[":tx/id"]} :tx/as-of {tx[":tx/as-of"]} '
            f':tx/prev {json.dumps(tx[":tx/prev"])} :tx/cid {json.dumps(tx[":tx/cid"])} '
            f':tx/count {tx[":tx/count"]} :tx/datoms [{datoms}]}}')


def append_tx(tx: dict, log_path: pathlib.Path = LOG_DEFAULT) -> str:
    """Append ONE transaction to the append-only log (never rewrites). Returns the tx CID."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.write_text(";; watari kotoba Datom log — append-only EAVT transactions "
                            "(content-addressed DAG). Situational-awareness, never surveillance / "
                            "no person-tracking (G2/G4). DO NOT hand-edit. ADR-2606041827.\n",
                            encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(_tx_to_edn(tx) + "\n")
    return tx[":tx/cid"]


def read_log(log_path: pathlib.Path = LOG_DEFAULT) -> list[dict]:
    """Read the log back as a list of transaction dicts (uses analyze.py's inline EDN reader)."""
    if not log_path.exists():
        return []
    txs = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        txs.append(_parse(_tokens(line)))
    return txs


def head_cid(log_path: pathlib.Path = LOG_DEFAULT) -> str:
    txs = read_log(log_path)
    return txs[-1][":tx/cid"] if txs else ""


def verify_chain(log_path: pathlib.Path = LOG_DEFAULT) -> dict:
    """Recompute every CID from its datoms + prev; verify the DAG is intact. {ok, length, broken_at}."""
    txs = read_log(log_path)
    prev = ""
    for i, tx in enumerate(txs):
        expect = tx_cid(tx.get(":tx/datoms", []), prev)
        if tx.get(":tx/cid") != expect or tx.get(":tx/prev") != prev:
            return {"ok": False, "length": len(txs), "broken_at": i}
        prev = tx[":tx/cid"]
    return {"ok": True, "length": len(txs), "broken_at": -1}


if __name__ == "__main__":
    import pathlib as _pl
    from analyze import load_edn

    here = _pl.Path(__file__).resolve().parents[1]
    g = here / "data" / "craft-graph.merged.kotoba.edn"
    if not g.exists():
        g = here / "data" / "seed-craft-graph.kotoba.edn"
    datoms = graph_datoms(load_edn(g))
    tx = make_tx(datoms, tx_id=1, as_of=20260608, prev_cid="")
    print(f"# watari kotoba Datom tx — {tx[':tx/count']} EAVT assertions, cid={tx[':tx/cid'][:18]}…")
