#!/usr/bin/env python3
"""kotoba.py — uchiwake 内訳 kotoba Datom-log writer (local, content-addressed).
ADR-2606081800 + ADR-2605262130 + ADR-2605312345.

The substrate boundary (root CLAUDE.md): canonical state is the **kotoba Datom log** —
content-addressed EAVT assertions, append-only. uchiwake had an ingest + analyzer + crosscheck
but no self-driving loop and no local log; this module is the **local, autonomous-loop** write
path — the same shape kanjō / shionome / ipaddress / watatsuna / watari / kabuto use
(`methods/autorun.py`): a self-driving heartbeat appends content-addressed transactions to a
local append-only EDN log with NO external I/O, so uchiwake can run its own
observe→analyze→persist product-resilience cycle on the Murakumo fleet without a human or a
live node in the loop.

Constitutional posture holds by construction (uchiwake hard rules): only public trade-item
FACTS (:product/:part/:material/:bom.edge/:process.step/:logistics.leg/:design.ref/
:company.ownership) + transparent concentration are representable — never a "who to hit" map and
never a clone/counterfeit recipe (G2/G4); derived :concentration/* carry :sourcing :synthesized
and are NEVER re-ingested as authoritative product facts (G5).

  - graph_datoms(rows)        → EAVT assertions for every product-graph entity. E = the
                                entity's id; lists fan out.
  - derived_datoms(derived)   → EAVT assertions for the analyzer's derived :concentration/*
                                (each tagged :sourcing :synthesized + :derived true, G5).
  - make_tx / append_tx / read_log / head_cid / verify_chain — content-addressed commit-DAG.

EAVT = [op entity attribute value]; op is :db/add only (append-only — no :db/retract). Stdlib
only. Deterministic: the caller supplies tx_id + as_of (no wall clock) → resume-safe.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uchiwake_edn  # noqa: E402

LOG_DEFAULT = (pathlib.Path(__file__).resolve().parents[1] / "data"
               / "uchiwake.datoms.kotoba.edn")

ID_KEYS = (":product/id", ":part/id", ":material/id", ":bom.edge/id",
           ":process.step/id", ":logistics.leg/id", ":design.ref/id",
           ":company.ownership/id", ":concentration/id")


def _add(entity: str, attr: str, value: Any) -> list:
    """One append-only EAVT assertion: [:db/add <entity> <attr> <value>]."""
    return [":db/add", entity, attr, value]


def _rows_to_datoms(rows: list) -> list[list]:
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


def graph_datoms(rows: list) -> list[list]:
    """Flatten the product graph (products / parts / materials / bom edges / process /
    logistics / design refs / ownership) into append-only EAVT assertions. E = the entity's id.
    Public trade-item facts only (G1)."""
    return _rows_to_datoms(rows)


def derived_datoms(derived: list) -> list[list]:
    """Flatten the analyzer's derived :concentration/* (material / process-country /
    ultimate-parent dependence) into append-only EAVT assertions. Each is tagged
    :concentration/sourcing :synthesized (G5) — a transparent uchiwake OBSERVATION, NEVER
    re-ingested as an authoritative product fact, NEVER a target-list or recipe (G2/G4)."""
    tagged = []
    for d in sorted(derived, key=lambda d: str(d.get(":concentration/id"))):  # PYTHONHASHSEED-stable
        d = dict(d)
        d.setdefault(":concentration/sourcing", ":synthesized")
        d.setdefault(":concentration/derived", True)
        tagged.append(d)
    return _rows_to_datoms(tagged)


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
        log_path.write_text(";; uchiwake kotoba Datom log — append-only EAVT transactions "
                            "(content-addressed DAG). Public product facts + :synthesized "
                            "concentration; resilience map, never a target-list/recipe (G2/G4). "
                            "DO NOT hand-edit. ADR-2606081800.\n",
                            encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(_tx_to_edn(tx) + "\n")
    return tx[":tx/cid"]


def read_log(log_path: pathlib.Path = LOG_DEFAULT) -> list[dict]:
    """Read the log back as a list of transaction dicts (uses the shared uchiwake_edn reader)."""
    if not log_path.exists():
        return []
    txs = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        form = uchiwake_edn.read_str(line)  # each log line is ONE top-level tx map
        if isinstance(form, dict):
            txs.append(form)
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

    here = _pl.Path(__file__).resolve().parents[1]
    g = here / "data" / "products.merged.kotoba.edn"
    if not g.exists():
        g = here / "data" / "seed-products.kotoba.edn"
    datoms = graph_datoms(uchiwake_edn.load_edn(g))
    tx = make_tx(datoms, tx_id=1, as_of=20260616, prev_cid="")
    print(f"# uchiwake kotoba Datom tx — {tx[':tx/count']} EAVT assertions, cid={tx[':tx/cid'][:18]}…")
