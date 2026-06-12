#!/usr/bin/env python3
"""kotoba.py — kabuto kotoba Datom-log writer (local, content-addressed). ADR-2606022000
+ ADR-2605262130 + ADR-2605312345.

The substrate boundary (root CLAUDE.md): canonical state is the **kotoba Datom log** —
content-addressed EAVT assertions, append-only (非終末論). `methods/transact.py` is the OTHER write
path: an HTTP push into a *running* kotoba node (operator-gated). This module is the **local,
autonomous-loop** write path — the same path shionome / ipaddress / yabai / sukashi / watatsuna /
watari use (`methods/autorun.py`): a self-driving heartbeat appends content-addressed transactions
to a local append-only EDN log with NO external I/O, so kabuto can run its own
observe→analyze→persist public-company-supply-chain cycle on the Murakumo fleet without a human or
a live node in the loop.

Constitutional posture is preserved by construction (kabuto hard rules): every derived signal is a
RESILIENCE + accountability map (single-source / concentration / tier-depth / cross-bloc corridors)
— never a "who to hit" / raid / takeover target-list (G2); public listed-company public-record data
only (G1); concentration is an observation, never an antitrust/sanctions verdict (G4). The loop
persists exactly what `analyze.py` already computes, with derived signals flagged :supply/derived.

  - graph_datoms(rows)            → EAVT assertions for every entity (company / address / contact /
                                    supply-edge / process). E = the entity's id; lists fan out.
  - derived_datoms(companies, a)  → EAVT assertions for the analyzer's derived :supply/* signals,
                                    flagged :supply/derived (mirrors analyze.render_datoms).
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
from kabuto_edn import _parse, _tokens  # noqa: E402

LOG_DEFAULT = (pathlib.Path(__file__).resolve().parents[1] / "data"
               / "kabuto.datoms.kotoba.edn")

ID_KEYS = (":company/id", ":company.address/id", ":company.contact/id",
           ":supply.edge/id", ":company.process/id")


def _add(entity: str, attr: str, value: Any) -> list:
    """One append-only EAVT assertion: [:db/add <entity> <attr> <value>]."""
    return [":db/add", entity, attr, value]


def graph_datoms(rows: list) -> list[list]:
    """Flatten the public-company supply-chain graph into append-only EAVT assertions. E = the
    entity's id; cardinality-many list values fan out. Listed-company public-record facts only;
    the seed carries no personal PII (G1)."""
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


def derived_datoms(a: dict) -> list[list]:
    """Flatten the analyzer's derived :supply/* concentration signals into EAVT assertions, each
    flagged :supply/derived true (a RESILIENCE + accountability map recomputed on read, never
    re-ingested as fact, never a target-list — G2/G4). Mirrors analyze.render_datoms.
    `a` is analyze.analyze()."""
    out: list[list] = []
    for i, (c, commodity, sup, crit) in enumerate(a["single_source"]):
        e = f"supply-single-{i}"
        out += [_add(e, ":supply/single-source-customer", c), _add(e, ":supply/commodity", commodity),
                _add(e, ":supply/sole-supplier", sup), _add(e, ":supply/criticality", crit),
                _add(e, ":supply/derived", True)]
    for country, load in sorted(a["jurisdiction_load"].items(), key=lambda kv: -kv[1]):
        e = f"supply-juris-{country}"
        out += [_add(e, ":supply/jurisdiction", country),
                _add(e, ":supply/jurisdiction-load", round(load, 2)), _add(e, ":supply/derived", True)]
    for sup, load in sorted(a["systemic"].items(), key=lambda kv: -kv[1]):
        e = f"supply-systemic-{sup}"
        out += [_add(e, ":supply/systemic-supplier", sup),
                _add(e, ":supply/out-degree", a["out_deg"].get(sup, 0)),
                _add(e, ":supply/outward-criticality", round(load, 2)), _add(e, ":supply/derived", True)]
    for c, secs, load, idx in a["diversification"]:
        e = f"supply-divers-{c}"
        out += [_add(e, ":supply/diversification-customer", c), _add(e, ":supply/supplier-sectors", secs),
                _add(e, ":supply/inbound-criticality", load), _add(e, ":supply/diversification-index", idx),
                _add(e, ":supply/derived", True)]
    for n, ind, outd, score in a["intermediaries"]:
        e = f"supply-inter-{n}"
        out += [_add(e, ":supply/intermediary", n), _add(e, ":supply/in-degree", ind),
                _add(e, ":supply/out-degree", outd), _add(e, ":supply/betweenness", score),
                _add(e, ":supply/derived", True)]
    for n, d in a["tier_depth"]:
        e = f"supply-tier-{n}"
        out += [_add(e, ":supply/tier-depth-node", n), _add(e, ":supply/tier-depth", d),
                _add(e, ":supply/derived", True)]
    for bloc, load in sorted(a["bloc_load"].items(), key=lambda kv: -kv[1]):
        e = f"supply-bloc-{bloc}"
        out += [_add(e, ":supply/region-bloc", bloc), _add(e, ":supply/bloc-load", round(load, 2)),
                _add(e, ":supply/derived", True)]
    for commodity, nsup, hhi in a["commodity_hhi"]:
        e = f"supply-commodity-{str(commodity).lstrip(':')}"
        out += [_add(e, ":supply/commodity", str(commodity).lstrip(":")),
                _add(e, ":supply/commodity-suppliers", nsup), _add(e, ":supply/commodity-hhi", hhi),
                _add(e, ":supply/derived", True)]
    for corridor, load in a["cross_corridors"]:
        e = f"supply-corridor-{corridor}"
        out += [_add(e, ":supply/cross-bloc-corridor", corridor),
                _add(e, ":supply/cross-bloc-load", round(load, 2)), _add(e, ":supply/derived", True)]
    for c, score, ss, secs, load, cross in a["resilience"]:
        e = f"supply-resil-{c}"
        out += [_add(e, ":supply/resilience-customer", c), _add(e, ":supply/resilience-score", score),
                _add(e, ":supply/single-source-count", ss), _add(e, ":supply/derived", True)]
    for sec, cap in a.get("sector_cap_rank", []):
        e = f"supply-capsec-{str(sec).lstrip(':')}"
        out += [_add(e, ":supply/cap-sector", str(sec).lstrip(":")),
                _add(e, ":supply/cap-sector-busd", round(cap, 1)), _add(e, ":supply/derived", True)]
    if a.get("cap_count"):
        e = "supply-cap-hhi"
        out += [_add(e, ":supply/cap-hhi", a["cap_hhi"]), _add(e, ":supply/cap-total-busd", a["total_cap"]),
                _add(e, ":supply/cap-covered", a["cap_count"]),
                _add(e, ":supply/cap-coverage-pct", a["cap_coverage"]), _add(e, ":supply/derived", True)]
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
        log_path.write_text(";; kabuto kotoba Datom log — append-only EAVT transactions "
                            "(content-addressed DAG). Resilience + accountability map, never a "
                            "target-list. DO NOT hand-edit. ADR-2606022000.\n", encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(_tx_to_edn(tx) + "\n")
    return tx[":tx/cid"]


def read_log(log_path: pathlib.Path = LOG_DEFAULT) -> list[dict]:
    """Read the log back as a list of transaction dicts (uses the shared kabuto_edn reader)."""
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
    from kabuto_edn import load_edn

    here = _pl.Path(__file__).resolve().parents[1]
    g = here / "data" / "companies.merged.kotoba.edn"
    if not g.exists():
        g = here / "data" / "seed-public-companies.kotoba.edn"
    datoms = graph_datoms(load_edn(g))
    tx = make_tx(datoms, tx_id=1, as_of=20260609, prev_cid="")
    print(f"# kabuto kotoba Datom tx — {tx[':tx/count']} EAVT assertions, cid={tx[':tx/cid'][:18]}…")
