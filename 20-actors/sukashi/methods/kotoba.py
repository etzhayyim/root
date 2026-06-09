#!/usr/bin/env python3
"""kotoba.py — sukashi kotoba Datom-log writer (local, content-addressed). ADR-2606071600
+ ADR-2605262130 + ADR-2605312345.

The substrate boundary (root CLAUDE.md): canonical state is the **kotoba Datom log** —
content-addressed EAVT assertions, append-only (非終末論). `methods/transact.py` is the OTHER
write path: an HTTP push into a *running* kotoba node (operator-JWT / CACAO gated). This module is
the **local, autonomous-loop** write path — the same path shionome / ipaddress / yabai use
(`methods/autorun.py`): a self-driving heartbeat appends content-addressed transactions to a local
append-only EDN log with NO external I/O, so sukashi can run its own observe→analyze→persist
ad-tech-supply-chain + fraud-observatory cycle on the Murakumo fleet without a human or a live node
in the loop.

Constitutional posture is preserved by construction (sukashi hard rules): this is an OBSERVATORY,
never an ad network (G2); inputs are public IAB transparency files only (G1); every fraud signal is
non-adjudicating + `:synthesized` on a clearly-fictional entity (G4); real firms carry no fraud
signal. The loop persists exactly what `analyze.py` already computes — nothing new is asserted as
fact, and derived signals are flagged `:derived`, never re-ingested.

  - graph_datoms(rows)   → EAVT assertions for every entity (adtech / auth-edge / creative /
                           delivery-edge / fraud-signal). E = the entity's id; lists fan out.
  - derived_datoms(a)    → EAVT assertions for the analyzer's derived :adsupply/* + :adfraud/*
                           signals (unconfirmed-rate, infra/registrar/whois concentration, scam
                           clusters, category load), flagged :derived true.
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
from sukashi_edn import _parse, _tokens  # noqa: E402

LOG_DEFAULT = (pathlib.Path(__file__).resolve().parents[1] / "data"
               / "sukashi.datoms.kotoba.edn")

ID_KEYS = (":adtech/id", ":adauth.edge/id", ":adcreative/id",
           ":addelivery.edge/id", ":adfraud.signal/id")


def _add(entity: str, attr: str, value: Any) -> list:
    """One append-only EAVT assertion: [:db/add <entity> <attr> <value>]."""
    return [":db/add", entity, attr, value]


def graph_datoms(rows: list) -> list[list]:
    """Flatten the ad-supply-chain graph into append-only EAVT assertions. E = the entity's id;
    cardinality-many list values fan out (mirrors transact.rows_to_datoms)."""
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


def derived_datoms(a: dict, *, prefix: str = "adsupply") -> list[list]:
    """Flatten the analyzer's derived :adsupply/* + :adfraud/* signals into EAVT assertions, each
    flagged :derived true (aggregate observatory signals recomputed on read, never re-ingested as
    fact — G4 non-adjudication). `a` is the dict returned by analyze.analyze()."""
    out: list[list] = []
    for s, unc, dec, rate in a["unconfirmed_rate"]:
        e = f"{prefix}-unconf-{s}"
        out += [_add(e, ":adsupply/seller", s), _add(e, ":adsupply/unconfirmed", unc),
                _add(e, ":adsupply/declared", dec), _add(e, ":adsupply/unconfirmed-rate", rate),
                _add(e, ":adsupply/derived", True)]
    for s, n in a["seller_fan_rank"]:
        e = f"{prefix}-fanout-{s}"
        out += [_add(e, ":adsupply/seller", s), _add(e, ":adsupply/seller-fan-out", n),
                _add(e, ":adsupply/derived", True)]
    for s, fan, btw in a["seller_betweenness"]:
        e = f"{prefix}-btw-{s}"
        out += [_add(e, ":adsupply/seller", s), _add(e, ":adsupply/seller-betweenness", btw),
                _add(e, ":adsupply/seller-fan-in", fan), _add(e, ":adsupply/derived", True)]
    for asn, load, n in a["infra_rank"]:
        e = f"{prefix}-asn-{asn}"
        out += [_add(e, ":adsupply/asn", asn), _add(e, ":adsupply/infra-concentration", load),
                _add(e, ":adsupply/scam-creatives", n), _add(e, ":adsupply/derived", True)]
    for reg, load, n in a["registrar_rank"]:
        e = f"{prefix}-reg-{reg}"
        out += [_add(e, ":adsupply/registrar", reg), _add(e, ":adsupply/registrar-fraud-load", load),
                _add(e, ":adsupply/registrar-cooccurrence", n), _add(e, ":adsupply/derived", True)]
    for org, load, n in a["whois_rank"]:
        e = f"{prefix}-whois-{org}"
        out += [_add(e, ":adsupply/whois-org", org), _add(e, ":adsupply/whois-fraud-load", load),
                _add(e, ":adsupply/whois-cooccurrence", n), _add(e, ":adsupply/derived", True)]
    for c in a["clusters"]:
        e = f"adfraud-cluster-{c['asn']}|{c['registrar']}"
        out += [_add(e, ":adfraud/cluster-asn", c["asn"]),
                _add(e, ":adfraud/cluster-registrar", c["registrar"]),
                _add(e, ":adfraud/cluster-members", c["members"]),
                _add(e, ":adfraud/cluster-confidence", c["conf_sum"]),
                _add(e, ":adfraud/cluster-corroboration", c["corroboration"]),
                _add(e, ":adfraud/network-rank", c["rank_score"]),
                _add(e, ":adfraud/derived", True)]
    for cat, load in a["category_rank"]:
        e = f"adfraud-cat-{str(cat).lstrip(':')}"
        out += [_add(e, ":adfraud/category", str(cat).lstrip(":")),
                _add(e, ":adfraud/category-load", round(load, 2)),
                _add(e, ":adfraud/derived", True)]
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
        log_path.write_text(";; sukashi kotoba Datom log — append-only EAVT transactions "
                            "(content-addressed DAG). Observatory only; fraud signals are "
                            ":synthesized + non-adjudicating. DO NOT hand-edit. ADR-2606071600.\n",
                            encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(_tx_to_edn(tx) + "\n")
    return tx[":tx/cid"]


def read_log(log_path: pathlib.Path = LOG_DEFAULT) -> list[dict]:
    """Read the log back as a list of transaction dicts (uses the shared sukashi_edn reader)."""
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
    from sukashi_edn import load_edn

    here = _pl.Path(__file__).resolve().parents[1]
    g = here / "data" / "ad-supply-chain.merged.kotoba.edn"
    if not g.exists():
        g = here / "data" / "seed-ad-supply-chain.kotoba.edn"
    datoms = graph_datoms(load_edn(g))
    tx = make_tx(datoms, tx_id=1, as_of=20260608, prev_cid="")
    print(f"# sukashi kotoba Datom tx — {tx[':tx/count']} EAVT assertions, cid={tx[':tx/cid'][:18]}…")
