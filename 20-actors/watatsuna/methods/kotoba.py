#!/usr/bin/env python3
"""kotoba.py — watatsuna kotoba Datom-log writer (local, content-addressed). ADR-2606012600
+ ADR-2605262130 + ADR-2605312345.

The substrate boundary (root CLAUDE.md): canonical state is the **kotoba Datom log** —
content-addressed EAVT assertions, append-only (非終末論). watatsuna had a graph + analyzer but no
self-driving loop and no local log; this module is the **local, autonomous-loop** write path — the
same path shionome / ipaddress / yabai / sukashi use (`methods/autorun.py`): a self-driving
heartbeat appends content-addressed transactions to a local append-only EDN log with NO external
I/O, so watatsuna can run its own observe→analyze→persist submarine-cable-resilience cycle on the
Murakumo fleet without a human or a live node in the loop.

Constitutional posture is preserved by construction (watatsuna hard rules): every derived signal
is a RESILIENCE map (chokepoint-load, station-degree, cable-diversity, redundancy-gap) — never a
"where to cut" / interdiction framing (G2); public-record cable data only (G1); fault kinds record
only the public bulletin's own classification, never a sabotage verdict (G4). The loop persists
exactly what `analyze.py` already computes, with derived signals flagged :resilience/derived.

  - graph_datoms(rows)            → EAVT assertions for every entity (cable / station / link /
                                     segment / fault). E = the entity's id; lists fan out.
  - derived_datoms(cables, st, a) → EAVT assertions for the analyzer's derived :resilience/*
                                     signals (chokepoint-load, station degree/capacity,
                                     cable-diversity, redundancy-gap), flagged :resilience/derived.
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
               / "watatsuna.datoms.kotoba.edn")

ID_KEYS = (":cable/id", ":station/id", ":cable.link/id", ":cable.seg/id", ":cable.fault/id")


def _add(entity: str, attr: str, value: Any) -> list:
    """One append-only EAVT assertion: [:db/add <entity> <attr> <value>]."""
    return [":db/add", entity, attr, value]


def graph_datoms(rows: list) -> list[list]:
    """Flatten the submarine-cable graph into append-only EAVT assertions. E = the entity's id;
    cardinality-many list values (e.g. :station/chokepoint, :cable.seg/traverses) fan out."""
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


def derived_datoms(cables: dict, stations: dict, a: dict) -> list[list]:
    """Flatten the analyzer's derived :resilience/* signals into EAVT assertions, each flagged
    :resilience/derived true (a RESILIENCE map recomputed on read, never re-ingested as fact, and
    never an interdiction target-list — G2). Mirrors analyze.render_datoms. `a` is analyze.analyze()."""
    out: list[list] = []
    for cp in sorted(a["choke_load"], key=lambda k: -a["choke_load"][k]):
        e = f"resilience-choke-{cp}"
        out += [_add(e, ":resilience/chokepoint", cp),
                _add(e, ":resilience/chokepoint-load", a["choke_load"][cp]),
                _add(e, ":resilience/cable-count", a["choke_count"][cp]),
                _add(e, ":resilience/derived", True)]
    for s in sorted(stations, key=lambda k: -a["station_degree"][k]):
        if a["station_degree"][s] == 0:
            continue
        e = f"resilience-station-{s}"
        out += [_add(e, ":resilience/station", s),
                _add(e, ":resilience/station-degree", a["station_degree"][s]),
                _add(e, ":resilience/station-capacity-tbps", a["station_capacity"][s]),
                _add(e, ":resilience/derived", True)]
    for c in sorted(cables, key=lambda k: a["cable_diversity"][k]):
        e = f"resilience-cable-{c}"
        out += [_add(e, ":resilience/cable", c),
                _add(e, ":resilience/cable-diversity", a["cable_diversity"][c]),
                _add(e, ":resilience/derived", True)]
    # redundancy-gap: landing stations served by a single cable (routed to watatsumi 敷設, never to cut)
    for s in a["redundancy_gap"]:
        e = f"resilience-gap-{s}"
        out += [_add(e, ":resilience/redundancy-gap-station", s),
                _add(e, ":resilience/station-degree", a["station_degree"][s]),
                _add(e, ":resilience/derived", True)]
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
        log_path.write_text(";; watatsuna kotoba Datom log — append-only EAVT transactions "
                            "(content-addressed DAG). Resilience map, never interdiction. "
                            "DO NOT hand-edit. ADR-2606012600.\n", encoding="utf-8")
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
    g = here / "data" / "cable-graph.merged.kotoba.edn"
    if not g.exists():
        g = here / "data" / "seed-cable-graph.kotoba.edn"
    datoms = graph_datoms(load_edn(g))
    tx = make_tx(datoms, tx_id=1, as_of=20260608, prev_cid="")
    print(f"# watatsuna kotoba Datom tx — {tx[':tx/count']} EAVT assertions, cid={tx[':tx/cid'][:18]}…")
