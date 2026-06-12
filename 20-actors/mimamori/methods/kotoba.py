#!/usr/bin/env python3
"""kotoba.py — mimamori 見守り kotoba Datom-log writer. ADR-2606112300 + ADR-2605312345.

Canonical state is the **kotoba Datom log** (root CLAUDE.md substrate boundary):
content-addressed EAVT assertions, append-only (永久記憶 / 非終末論). This module is
mimamori's write path onto that log, mirroring the shionome pattern (ADR-2606091000):
each transaction is content-addressed (sha256 over its canonical datoms + the previous
tx's CID → a commit-DAG); a tamper of any earlier tx breaks every later CID.

  - bond_datoms(engine)    → EAVT assertions from a replayed Mishmeret engine
  - coverage_datoms(c, n)  → AGGREGATE-ONLY coverage assertions (G5: counts, no DID)
  - make_tx / tx_cid       → a content-addressed transaction (links prev CID)
  - append_tx              → append ONE transaction line (never rewrites)
  - read_log / head_cid / verify_chain — read back + verify the DAG

EAVT = [:db/add entity attribute value] — :db/add only (no retract; exit is itself an
appended state datom). Stdlib only. Deterministic (caller supplies tx_id + as_of).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any

LOG_DEFAULT = pathlib.Path(__file__).resolve().parents[1] / "data" / "mimamori.datoms.kotoba.edn"


def _add(entity: str, attr: str, value: Any) -> list:
    return [":db/add", entity, attr, value]


def bond_datoms(engine) -> list[list]:
    """Flatten a replayed Mishmeret engine's append-only (e, a, v, tx, op) datoms into
    kotoba EAVT assertions. The engine's own validator already enforced G1/G2 — every
    attr here is whitelist-clean by construction."""
    return [_add(e, a, v) for (e, a, v, _tx, _op) in engine.datoms]


def coverage_datoms(c: dict, cycle: int) -> list[list]:
    """AGGREGATE-ONLY coverage assertions (G5): counts only, no DID ever enters these."""
    eid = f"coverage.{cycle}"
    out = [_add(eid, ":mimamori.coverage/cycle", cycle)]
    for k in ("members_total", "with_keeper", "offers_pending", "unkept_count",
              "active_bonds", "relays"):
        out.append(_add(eid, f":mimamori.coverage/{k.replace('_', '-')}", c[k]))
    return out


def _canonical(datoms: list[list], prev_cid: str) -> bytes:
    return json.dumps({"prev": prev_cid, "datoms": datoms},
                      ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def tx_cid(datoms: list[list], prev_cid: str = "") -> str:
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
    """Append ONE transaction (the log only ever grows — 永久記憶)."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.write_text(";; mimamori kotoba Datom log — append-only EAVT transactions "
                            "(content-addressed DAG). DO NOT hand-edit. ADR-2606112300.\n",
                            encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(_tx_to_edn(tx) + "\n")
    return tx[":tx/cid"]


def read_log(log_path: pathlib.Path = LOG_DEFAULT) -> list[dict]:
    import sys as _sys
    _sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from _edn import _parse, _tokens
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
    """Recompute every CID from (datoms, prev) — {ok, length, broken_at}."""
    txs = read_log(log_path)
    prev = ""
    for i, tx in enumerate(txs):
        if tx.get(":tx/cid") != tx_cid(tx.get(":tx/datoms", []), prev) \
                or tx.get(":tx/prev") != prev:
            return {"ok": False, "length": len(txs), "broken_at": i}
        prev = tx[":tx/cid"]
    return {"ok": True, "length": len(txs), "broken_at": -1}
