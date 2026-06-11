#!/usr/bin/env python3
"""kotoba.py — ipaddress kotoba Datom-log writer (local, content-addressed). ADR-2605301400
§T2 + ADR-2605262130 + ADR-2605312345.

The substrate boundary (root CLAUDE.md): canonical state is the **kotoba Datom log** —
content-addressed EAVT assertions, append-only (G10 / 非終末論). `methods/transact.py` is the
OTHER write path: an HTTP push into a *running* kotoba node (operator-CACAO / JWT gated, verified
live 2026-06-03). This module is the **local, autonomous-loop** write path — the same path
shionome uses (`methods/autorun.py`): a self-driving heartbeat appends content-addressed
transactions to a local append-only EDN log with NO external I/O, so the actor can run its own
observe→analyze→persist cycle on the Murakumo fleet without a human or a live node in the loop.
The kotoba engine ingests this exact body shape; nothing here is a RisingWave / SQL / Datomic
store (N7). When an operator flips the G7/G8 gate, the same datoms flow through transact.py to
the live node.

  - graph_datoms(rows)   → EAVT assertions for every entity in the merged IP/ASN graph
  - derived_datoms(b, a) → EAVT assertions for the analyzer's :ipnet/* concentration (flagged
                           :ipnet/derived true — recomputed, never re-ingested as authoritative)
  - make_tx(...)         → a content-addressed transaction (links to prev CID → commit-DAG)
  - append_tx(...)       → append ONE transaction line to the append-only log (never rewrites)
  - read_log / head_cid / verify_chain — read back + verify the content-addressed DAG

EAVT = [op entity attribute value]; op is :db/add only (append-only — there is no :db/retract,
non-eschatological). E = the entity's stable id string (the kotoba node hashes it to a CID;
cardinality-many values fan out, matching transact.py's `rows_to_datoms`). Stdlib only.
Deterministic: the caller supplies tx_id + as_of (no wall clock) so a re-run reproduces the same
CIDs (resume-safe), mirroring shionome.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ip_edn import _parse, _tokens, edn_val  # noqa: E402

LOG_DEFAULT = (pathlib.Path(__file__).resolve().parents[1] / "data"
               / "ipaddress.datoms.kotoba.edn")

# entity-id keys, in priority order (same set transact.py uses for E selection)
ID_KEYS = (":rir/id", ":asn/id", ":iprange/id", ":ip/id", ":net.announce/id",
           ":net.member/id", ":geo/id", ":rdns/id", ":whois/id")


def _add(entity: str, attr: str, value: Any) -> list:
    """One append-only EAVT assertion: [:db/add <entity> <attr> <value>]."""
    return [":db/add", entity, attr, value]


def graph_datoms(rows: list) -> list[list]:
    """Flatten the merged IP/ASN graph (flat list of entity maps) into append-only EAVT
    assertions. E = the entity's id; cardinality-many list values fan out into one datom each
    (mirrors transact.rows_to_datoms so the local log and the live-node push are isomorphic)."""
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


def derived_datoms(concentration: dict, *, prefix: str = "ipnet") -> list[list]:
    """Flatten the analyzer's derived :ipnet/* concentration metrics into EAVT assertions, each
    flagged :ipnet/derived true (G2/G10: a RESILIENCE map recomputed on read, never re-ingested
    as :authoritative fact). `concentration` is the dict returned by analyze.analyze()."""
    a = concentration
    out: list[list] = []
    for rir, addr in sorted(a["rir_addr"].items(), key=lambda kv: -kv[1]):
        e = f"{prefix}-rir-{str(rir).lstrip(':')}"
        out += [_add(e, ":ipnet/rir", rir),
                _add(e, ":ipnet/ranges", a["rir_ranges"].get(rir, 0)),
                _add(e, ":ipnet/addresses", addr),
                _add(e, ":ipnet/derived", True)]
    for aid, name, pref, cls, _cc in a["asn_prefix"]:
        e = f"{prefix}-asn-{str(aid).lstrip(':')}"
        out += [_add(e, ":ipnet/asn-prefix-load", aid),
                _add(e, ":ipnet/asn-name", name),
                _add(e, ":ipnet/prefixes", pref),
                _add(e, ":ipnet/hosting-class", cls),
                _add(e, ":ipnet/derived", True)]
    for cls, addr in sorted(a["hosting_addr"].items(), key=lambda kv: -kv[1]):
        e = f"{prefix}-hclass-{str(cls).lstrip(':')}"
        out += [_add(e, ":ipnet/hosting-class-load", cls),
                _add(e, ":ipnet/addresses", addr),
                _add(e, ":ipnet/derived", True)]
    for cc, addr in sorted(a["country_addr"].items(), key=lambda kv: -kv[1]):
        e = f"{prefix}-cc-{cc}"
        out += [_add(e, ":ipnet/country-load", cc),
                _add(e, ":ipnet/addresses", addr),
                _add(e, ":ipnet/derived", True)]
    e = f"{prefix}-hhi"
    out += [_add(e, ":ipnet/space-hhi", a["space_hhi"]),
            _add(e, ":ipnet/prefix-hhi", a["prefix_hhi"]),
            _add(e, ":ipnet/v4-ranges", a["v4"]),
            _add(e, ":ipnet/v6-ranges", a["v6"]),
            _add(e, ":ipnet/derived", True)]
    return out


def _canonical(datoms: list[list], prev_cid: str) -> bytes:
    """Canonical bytes for content addressing: stable JSON of (prev_cid, datoms)."""
    return json.dumps({"prev": prev_cid, "datoms": datoms},
                      ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def tx_cid(datoms: list[list], prev_cid: str = "") -> str:
    """Content address of a transaction = sha256 over (prev_cid, datoms). Linking prev_cid in
    makes the log a commit-DAG (a tamper of any earlier tx breaks every later CID)."""
    return "b" + hashlib.sha256(_canonical(datoms, prev_cid)).hexdigest()


def make_tx(datoms: list[list], *, tx_id: int, as_of: int, prev_cid: str = "") -> dict:
    """Build a content-addressed transaction. tx_id + as_of are supplied by the caller (no wall
    clock — keeps the log deterministic + resume-safe)."""
    return {
        ":tx/id": tx_id,
        ":tx/as-of": as_of,
        ":tx/prev": prev_cid,
        ":tx/cid": tx_cid(datoms, prev_cid),
        ":tx/count": len(datoms),
        ":tx/datoms": datoms,
    }


def _tx_to_edn(tx: dict) -> str:
    """Serialize one transaction as a single-line EDN map (the kotoba ingest body shape).
    Reuses ip_edn.edn_val so the datom rendering matches transact.py exactly."""
    datoms = " ".join("[" + " ".join(edn_val(x) for x in d) + "]" for d in tx[":tx/datoms"])
    return (f'{{:tx/id {tx[":tx/id"]} :tx/as-of {tx[":tx/as-of"]} '
            f':tx/prev {edn_val(tx[":tx/prev"])} :tx/cid {edn_val(tx[":tx/cid"])} '
            f':tx/count {tx[":tx/count"]} :tx/datoms [{datoms}]}}')


def append_tx(tx: dict, log_path: pathlib.Path = LOG_DEFAULT) -> str:
    """Append ONE transaction to the append-only log (never rewrites existing lines). Returns
    the tx CID. This is the only mutation: the log only ever grows (G10 / 非終末論)."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.write_text(";; ipaddress kotoba Datom log — append-only EAVT transactions "
                            "(content-addressed DAG). DO NOT hand-edit. ADR-2605301400 §T2.\n",
                            encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(_tx_to_edn(tx) + "\n")
    return tx[":tx/cid"]


def read_log(log_path: pathlib.Path = LOG_DEFAULT) -> list[dict]:
    """Read the log back as a list of transaction dicts (uses the shared ip_edn reader)."""
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
    """The content-addressed HEAD = the last transaction's CID (ADR-2606066000 head pointer)."""
    txs = read_log(log_path)
    return txs[-1][":tx/cid"] if txs else ""


def verify_chain(log_path: pathlib.Path = LOG_DEFAULT) -> dict:
    """Recompute every CID from its datoms + prev and verify the DAG is intact (no tampering).
    Returns {ok, length, broken_at}. The integrity proof of the append-only log."""
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
    from ip_edn import load_edn

    here = _pl.Path(__file__).resolve().parents[1]
    g = here / "data" / "ip-network.merged.kotoba.edn"
    if not g.exists():
        g = here / "data" / "seed-ip-network.kotoba.edn"
    datoms = graph_datoms(load_edn(g))
    tx = make_tx(datoms, tx_id=1, as_of=20260608, prev_cid="")
    print(f"# ipaddress kotoba Datom tx — {tx[':tx/count']} EAVT assertions, "
          f"cid={tx[':tx/cid'][:18]}…")
