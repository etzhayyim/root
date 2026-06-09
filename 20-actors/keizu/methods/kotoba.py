#!/usr/bin/env python3
"""kotoba.py — keizu (系図) kotoba Datom-log writer (local, content-addressed). ADR-2606066000
+ ADR-2605262130 + ADR-2605312345.

The substrate boundary (root CLAUDE.md): canonical state is the **kotoba Datom log** —
content-addressed EAVT assertions, append-only (非終末論). keizu had weave + concentration + a
dry-run export but no self-driving loop and no local log; this module is the **local,
autonomous-loop** write path — the same path shionome / ipaddress / yabai / sukashi / watatsuna /
watari / kabuto / kanjō / danjo use (`methods/autorun.py`): a self-driving heartbeat appends
content-addressed transactions to a local append-only EDN log with NO external I/O, so keizu can
run its own observe→weave→persist government-power-relations cycle on the Murakumo fleet without a
human or a live node in the loop.

Constitutional posture is preserved by construction (keizu hard rules): an accountability MAP,
NEVER a target-list; edge-primary — every derived signal is a concentration/co-occurrence computed
on read from edges/flows, never a per-person score (G4); FACTUAL + non-adjudicating — a
co-occurrence of two disclosed flows is not an allegation; no-doxxing — PII node attrs are
unrepresentable (validated upstream by weave). The loop persists exactly what weave + concentration
already produced, derived flagged :keizu.conc/derived.

  - graph_datoms(g)        → EAVT assertions for every entity (node / committee / rel / money /
                            statement). E = the entity's id; lists fan out.
  - derived_datoms(c)      → EAVT assertions for the aggregate, edge-primary concentration metrics
                            (counts, money/payer HHI + shares, committee cross-organ, cross-committee
                            seats, connector seats, revolving-door, award-and-fund, by-jurisdiction),
                            flagged :keizu.conc/derived. Never a per-person score.
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
from _edn import _parse, _tokens  # noqa: E402

LOG_DEFAULT = (pathlib.Path(__file__).resolve().parents[1] / "data"
               / "keizu.datoms.kotoba.edn")

ID_KEYS = (":node/id", ":committee/id", ":rel/id", ":money/id", ":statement/id")


def _add(entity: str, attr: str, value: Any) -> list:
    """One append-only EAVT assertion: [:db/add <entity> <attr> <value>]."""
    return [":db/add", entity, attr, value]


def _flatten(row: dict, out: list) -> None:
    e = next((row[k] for k in ID_KEYS if k in row), None)
    if e is None:
        return
    for k, v in row.items():
        if k in ID_KEYS:
            continue
        for item in (v if isinstance(v, list) else [v]):
            out.append(_add(e, k, item))


def graph_datoms(g: dict) -> list[list]:
    """Flatten the woven relation graph into append-only EAVT assertions. Power-entity nodes only
    (PII node attrs are unrepresentable, validated upstream by weave)."""
    out: list[list] = []
    for row in g["nodes"].values():
        _flatten(row, out)
    for row in g["committees"].values():
        _flatten(row, out)
    for row in g["rels"]:
        _flatten(row, out)
    for row in g["money"]:
        _flatten(row, out)
    for row in g["statements"]:
        _flatten(row, out)
    return out


def derived_datoms(c: dict, *, prefix: str = "keizu.conc") -> list[list]:
    """Flatten the aggregate, edge-primary concentration metrics into EAVT assertions, each flagged
    :keizu.conc/derived true (an accountability map recomputed on read, NEVER a per-person score or
    a target-list — G4). `c` is concentration()."""
    out: list[list] = []
    # headline counts
    e = f"{prefix}-counts"
    out += [_add(e, ":keizu.conc/node-count", c["node_count"]),
            _add(e, ":keizu.conc/committee-count", c["committee_count"]),
            _add(e, ":keizu.conc/rel-count", c["rel_count"]),
            _add(e, ":keizu.conc/money-count", c["money_count"]),
            _add(e, ":keizu.conc/statement-count", c["statement_count"]),
            _add(e, ":keizu.conc/derived", True)]
    # money concentration (by payee) + payer concentration — HHI + ranked shares
    mc, pc = c["money_concentration"], c["payer_concentration"]
    em = f"{prefix}-money"
    out += [_add(em, ":keizu.conc/money-hhi", mc["hhi"]),
            _add(em, ":keizu.conc/money-total", mc["total"]),
            _add(em, ":keizu.conc/payer-hhi", pc["hhi"]),
            _add(em, ":keizu.conc/derived", True)]
    for payee, share in mc["shares"]:
        e = f"{prefix}-payee-{payee}"
        out += [_add(e, ":keizu.conc/payee", payee), _add(e, ":keizu.conc/share", round(share, 4)),
                _add(e, ":keizu.conc/derived", True)]
    for payer, share in pc["shares"]:
        e = f"{prefix}-payer-{payer}"
        out += [_add(e, ":keizu.conc/payer", payer), _add(e, ":keizu.conc/share", round(share, 4)),
                _add(e, ":keizu.conc/derived", True)]
    # committee cross-organ concentration
    for r in c["committee_cross_organ"]:
        e = f"{prefix}-xorgan-{r['committee']}"
        out += [_add(e, ":keizu.conc/committee", r["committee"]),
                _add(e, ":keizu.conc/member-count", r["member_count"]),
                _add(e, ":keizu.conc/distinct-organs", r["distinct_organs"]),
                _add(e, ":keizu.conc/derived", True)]
    # cross-committee seats (co-membership) + cross-organ connector seats
    for r in c["cross_committee_seats"]:
        e = f"{prefix}-xseat-{r['seat']}"
        out += [_add(e, ":keizu.conc/seat", r["seat"]),
                _add(e, ":keizu.conc/committee-count", r["committee_count"]),
                _add(e, ":keizu.conc/derived", True)]
    for r in c["connector_seats"]:
        e = f"{prefix}-connector-{r['seat']}"
        out += [_add(e, ":keizu.conc/connector-seat", r["seat"]),
                _add(e, ":keizu.conc/organs-bridged", r["organs_bridged"]),
                _add(e, ":keizu.conc/derived", True)]
    # revolving-door chains (as-of) + award-and-fund co-occurrence (FACTUAL, non-adjudicating)
    for i, r in enumerate(c["revolving_door"]):
        e = f"{prefix}-revolving-{i}"
        out += [_add(e, ":keizu.conc/revolving-from", r["from_label"]),
                _add(e, ":keizu.conc/revolving-to", r["to_label"]),
                _add(e, ":keizu.conc/as-of", r["as_of"]),
                _add(e, ":keizu.conc/non-adjudicating", True),
                _add(e, ":keizu.conc/derived", True)]
    for r in c["award_and_fund"]:
        e = f"{prefix}-awardfund-{r['node']}"
        out += [_add(e, ":keizu.conc/award-and-fund-node", r["node"]),
                _add(e, ":keizu.conc/received-total", r["received_total"]),
                _add(e, ":keizu.conc/donated-total", r["donated_total"]),
                _add(e, ":keizu.conc/non-adjudicating", True),  # co-occurrence, NOT an allegation
                _add(e, ":keizu.conc/derived", True)]
    # by-jurisdiction
    for j in c["by_jurisdiction"]:
        e = f"{prefix}-juris-{j['jurisdiction']}"
        out += [_add(e, ":keizu.conc/jurisdiction", j["jurisdiction"]),
                _add(e, ":keizu.conc/nodes", j["nodes"]),
                _add(e, ":keizu.conc/committees", j["committees"]),
                _add(e, ":keizu.conc/money-total", j["money_total"]),
                _add(e, ":keizu.conc/derived", True)]
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
        log_path.write_text(";; keizu kotoba Datom log — append-only EAVT transactions "
                            "(content-addressed DAG). Accountability map, never a target-list; "
                            "edge-primary, non-adjudicating, no-doxxing. DO NOT hand-edit. ADR-2606066000.\n",
                            encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(_tx_to_edn(tx) + "\n")
    return tx[":tx/cid"]


def read_log(log_path: pathlib.Path = LOG_DEFAULT) -> list[dict]:
    """Read the log back as a list of transaction dicts (uses the shared _edn reader)."""
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
    from _edn import load_edn
    from weave import weave

    g = weave(load_edn(_pl.Path(__file__).resolve().parents[1] / "data" / "seed-relation-graph.kotoba.edn"))
    datoms = graph_datoms(g)
    tx = make_tx(datoms, tx_id=1, as_of=20260609, prev_cid="")
    print(f"# keizu kotoba Datom tx — {tx[':tx/count']} EAVT assertions, cid={tx[':tx/cid'][:18]}…")
