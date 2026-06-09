#!/usr/bin/env python3
"""kotoba.py — kosatsu (高札) kotoba Datom-log writer (local, content-addressed). ADR-2606072000
+ ADR-2605262130 + ADR-2605312345.

The substrate boundary (root CLAUDE.md): canonical state is the **kotoba Datom log** —
content-addressed EAVT assertions, append-only (非終末論; every designation is an append-only
ATTRIBUTED event — asserter + as-of :listed/:delisted — never overwritten). kosatsu had weave +
report + a dry-run bridge but no self-driving loop and no local log; this module is the **local,
autonomous-loop** write path — the same path the infra-intel/observatory family uses
(shionome / yabai / kabuto / danjo / keizu …): a self-driving heartbeat appends content-addressed
transactions to a local append-only EDN log with NO external I/O, so kosatsu can run its own
observe→weave→persist competing-claim cycle on the Murakumo fleet without a human or a live node in
the loop.

Constitutional posture is preserved by construction (kosatsu hard rules): etzhayyim authors NO
designation (every designation carries an `:asserter` — a sovereign/body, never etzhayyim), NO
verdict, NO per-subject score. The computed `divergence` {contested | unanimous | single-asserter}
makes "crime varies by political stance" a NEUTRAL fact, not a judgement. The loop persists exactly
what weave + report produced; derived flagged :kosatsu.div/derived.

  - graph_datoms(g)   → EAVT assertions for every entity (authority / subject / designation event).
  - derived_datoms(r) → EAVT assertions for the aggregate competing-claim signals (agreement index,
                        per-subject divergence class, by-authority, co-designation), flagged
                        :kosatsu.div/derived. Never a per-subject score / verdict.
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
               / "kosatsu.datoms.kotoba.edn")

ID_KEYS = (":authority/id", ":subject/id", ":designation/id")


def _add(entity: str, attr: str, value: Any) -> list:
    """One append-only EAVT assertion: [:db/add <entity> <attr> <value>]."""
    return [":db/add", entity, attr, value]


def _flatten(rows, out: list) -> None:
    items = rows.values() if isinstance(rows, dict) else rows
    for row in items:
        if not isinstance(row, dict):
            continue
        e = next((row[k] for k in ID_KEYS if k in row), None)
        if e is None:
            continue
        for k, v in row.items():
            if k in ID_KEYS:
                continue
            for item in (v if isinstance(v, list) else [v]):
                out.append(_add(e, k, item))


def graph_datoms(g: dict) -> list[list]:
    """Flatten the woven competing-claim graph into append-only EAVT assertions. Each designation
    is an ATTRIBUTED event (it carries its own :asserter — etzhayyim authors none)."""
    out: list[list] = []
    _flatten(g["authorities"], out)
    _flatten(g["subjects"], out)
    _flatten(g["designations"], out)
    return out


def derived_datoms(r: dict, *, prefix: str = "kosatsu.div") -> list[list]:
    """Flatten the aggregate competing-claim report into EAVT assertions, each flagged
    :kosatsu.div/derived true (a politically-neutral observation recomputed on read — NEVER a
    verdict or a per-subject score). `r` is report()."""
    out: list[list] = []
    ai = r["agreement_index"]
    e = f"{prefix}-agreement"
    out += [_add(e, ":kosatsu.div/authority-count", r["authority_count"]),
            _add(e, ":kosatsu.div/subject-count", r["subject_count"]),
            _add(e, ":kosatsu.div/designation-count", r["designation_count"]),
            _add(e, ":kosatsu.div/contested", ai["contested"]),
            _add(e, ":kosatsu.div/single-asserter", ai["single_asserter"]),
            _add(e, ":kosatsu.div/unanimous", ai["unanimous"]),
            _add(e, ":kosatsu.div/contested-ratio", ai["contested_ratio"]),
            _add(e, ":kosatsu.div/derived", True)]
    # per-subject divergence — the {contested | unanimous | single-asserter} neutral fact
    for d in r["divergence"]:
        es = f"{prefix}-subject-{d['subject']}"
        out += [_add(es, ":kosatsu.div/subject", d["subject"]),
                _add(es, ":kosatsu.div/class", ":" + str(d["class"]).lstrip(":")),
                _add(es, ":kosatsu.div/listing", d["listing"]),
                _add(es, ":kosatsu.div/delisted", d["delisted"]),
                _add(es, ":kosatsu.div/silent", d["silent"]),
                _add(es, ":kosatsu.div/derived", True)]
    # by-authority coverage (how many subjects each asserter lists) — NOT a ranking of legitimacy
    for a in r["by_authority"]:
        ea = f"{prefix}-authority-{a['authority']}"
        out += [_add(ea, ":kosatsu.div/authority", a["authority"]),
                _add(ea, ":kosatsu.div/jurisdiction", a["jurisdiction"]),
                _add(ea, ":kosatsu.div/listed-subjects", a["listed_subjects"]),
                _add(ea, ":kosatsu.div/derived", True)]
    # co-designation (subjects an asserter lists under one program)
    for i, c in enumerate(r["co_designation"]):
        ec = f"{prefix}-codesig-{i}"
        out += [_add(ec, ":kosatsu.div/asserter", c["asserter"]),
                _add(ec, ":kosatsu.div/program", c["program"]),
                _add(ec, ":kosatsu.div/co-designation-count", c["count"]),
                _add(ec, ":kosatsu.div/derived", True)]
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
        log_path.write_text(";; kosatsu kotoba Datom log — append-only EAVT transactions "
                            "(content-addressed DAG). Every designation is an ATTRIBUTED event; "
                            "etzhayyim authors no designation, no verdict, no score. ADR-2606072000.\n",
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
    from weave import report, weave

    g = weave(load_edn(_pl.Path(__file__).resolve().parents[1] / "data" / "seed-designation-graph.kotoba.edn"))
    datoms = graph_datoms(g) + derived_datoms(report(g))
    tx = make_tx(datoms, tx_id=1, as_of=20260609, prev_cid="")
    print(f"# kosatsu kotoba Datom tx — {tx[':tx/count']} EAVT assertions, cid={tx[':tx/cid'][:18]}…")
