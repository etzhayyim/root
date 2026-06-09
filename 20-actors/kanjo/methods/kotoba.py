#!/usr/bin/env python3
"""kotoba.py — kanjō kotoba Datom-log writer (local, content-addressed). ADR-2606032000
+ ADR-2605262130 + ADR-2605312345.

The substrate boundary (root CLAUDE.md): canonical state is the **kotoba Datom log** —
content-addressed EAVT assertions, append-only (非終末論; a 訂正報告書 asserts a NEW fact + sets
:fin.fact/superseded-by, never deletes — G11). kanjō had a concept-map + ingest + analyzer but no
self-driving loop and no local log; this module is the **local, autonomous-loop** write path — the
same path shionome / ipaddress / yabai / sukashi / watatsuna / watari / kabuto use
(`methods/autorun.py`): a self-driving heartbeat appends content-addressed transactions to a local
append-only EDN log with NO external I/O, so kanjō can run its own observe→analyze→persist
financial-disclosure cycle on the Murakumo fleet without a human or a live node in the loop.

Constitutional posture is preserved by construction (kanjō hard rules): only disclosed primary-
filing FACTS + transparent ratios are representable — never a rating, valuation, solvency verdict,
forecast, or buy/sell call (G2/G4); derived :fin.metric / :fin.agg are flagged :synthesized and
NEVER re-ingested as disclosed facts (G5).

  - graph_datoms(rows)            → EAVT assertions for every disclosed entity (filing / fact /
                                    concept). E = the entity's id; lists fan out.
  - derived_datoms(metrics, aggs) → EAVT assertions for the analyzer's derived :fin.metric +
                                    :fin.agg (each already carries :sourcing :synthesized, G5).
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
import kanjo_edn  # noqa: E402

LOG_DEFAULT = (pathlib.Path(__file__).resolve().parents[1] / "data"
               / "kanjo.datoms.kotoba.edn")

ID_KEYS = (":fin.filing/id", ":fin.fact/id", ":fin.concept/id",
           ":fin.metric/id", ":fin.agg/id")


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
    """Flatten the disclosed-fact graph (filings / facts / concepts) into append-only EAVT
    assertions. E = the entity's id. Disclosed primary-filing facts only (G1)."""
    return _rows_to_datoms(rows)


def derived_datoms(metrics: list, aggs: list) -> list[list]:
    """Flatten the analyzer's derived :fin.metric (ratios / YoY) + :fin.agg (sector/currency
    aggregates) into append-only EAVT assertions. Each dict already carries :sourcing :synthesized
    (G5) — these are transparent observations, NEVER re-ingested as disclosed facts, NEVER a
    rating/valuation/forecast (G2/G4)."""
    return _rows_to_datoms(list(metrics) + list(aggs))


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
        log_path.write_text(";; kanjo kotoba Datom log — append-only EAVT transactions "
                            "(content-addressed DAG). Disclosed facts + :synthesized ratios; "
                            "non-adjudicating, no advice/forecast. DO NOT hand-edit. ADR-2606032000.\n",
                            encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(_tx_to_edn(tx) + "\n")
    return tx[":tx/cid"]


def read_log(log_path: pathlib.Path = LOG_DEFAULT) -> list[dict]:
    """Read the log back as a list of transaction dicts (uses the shared kanjo_edn reader)."""
    if not log_path.exists():
        return []
    txs = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        # each log line is ONE top-level tx map; read_all returns it as a dict
        form = kanjo_edn.read_all(line)
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
    g = here / "data" / "facts.merged.kotoba.edn"
    if not g.exists():
        g = here / "data" / "seed-financial-facts.kotoba.edn"
    datoms = graph_datoms(kanjo_edn.read_file(str(g)))
    tx = make_tx(datoms, tx_id=1, as_of=20260609, prev_cid="")
    print(f"# kanjo kotoba Datom tx — {tx[':tx/count']} EAVT assertions, cid={tx[':tx/cid'][:18]}…")
