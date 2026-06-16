#!/usr/bin/env python3
"""kotoba.py — aburi 炙り kotoba Datom-log writer (local, content-addressed). ADR-2606161630
+ ADR-2605262130 + ADR-2605312345.

Canonical state is the kotoba Datom log — content-addressed EAVT assertions, append-only
(非終末論). aburi persists the MEMBER'S OWN tracker-exposure graph (built from their OWN consented
privacy exports) through the same local autonomous-loop write path the observatory family uses
(meisai / danjo / shionome `methods/autorun.py`): a heartbeat appends content-addressed
transactions to a LOCAL append-only EDN log with NO external I/O.

Constitutional posture preserved by construction (the meisai discipline):
  - G7 local-only — the member's exposure log lives under the gitignored `data/local/` and is
    NEVER committed, pinned, or published. The PUBLIC representative seed is separate.
  - G8 no credential / raw identifier — `ingest.guard` raises on credential-shaped keys and
    raw-identifier / PAN-shaped values; only exposure STRUCTURE is persisted, never raw values.

EAVT = [op entity attribute value]; op is :db/add only (append-only — no :db/retract). Stdlib
only. Deterministic: the caller supplies tx_id + as_of (no wall clock) → resume-safe. The
canonical-JSON tx-CID encoder is byte-identical to meisai's, so any future .cljc port builds the
same commit-DAG.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
from typing import Any

# the member's OWN exposure log — under the gitignored data/local/ (G7)
LOG_DEFAULT = (pathlib.Path(__file__).resolve().parents[1] / "data" / "local" / "persisted"
               / "aburi.datoms.kotoba.edn")


def add(entity: str, attr: str, value: Any) -> list:
    """One append-only EAVT assertion: [:db/add <entity> <attr> <value>]."""
    return [":db/add", entity, attr, value]


def _canonical(datoms: list[list], prev_cid: str) -> bytes:
    return json.dumps({"prev": prev_cid, "datoms": datoms},
                      ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def tx_cid(datoms: list[list], prev_cid: str = "") -> str:
    """Content address = sha256 over (prev_cid, datoms) → a commit-DAG."""
    return "b" + hashlib.sha256(_canonical(datoms, prev_cid)).hexdigest()


def content_cid(raw: bytes) -> str:
    """Content address of arbitrary intake bytes (G5 provenance + dedup key)."""
    return "b" + hashlib.sha256(raw).hexdigest()


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
        log_path.write_text(";; aburi kotoba Datom log — append-only EAVT transactions "
                            "(content-addressed DAG). MEMBER-OWN tracker-exposure structure only; "
                            "this file lives under the gitignored data/local/ and is NEVER "
                            "committed, pinned, or published (G7). DO NOT hand-edit. "
                            "ADR-2606161630.\n",
                            encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(_tx_to_edn(tx) + "\n")
    return tx[":tx/cid"]


# ── minimal EDN reader (subset) for read-back + export intake, consistent with the family ──
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
_END = object()


def _tokens(s: str):
    for m in _TOK.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t


def _atom(t: str):
    if t.startswith('"'):
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t == 'true':
        return True
    if t == 'false':
        return False
    if t == 'nil':
        return None
    if t.startswith(':'):
        return t
    try:
        return int(t)
    except ValueError:
        try:
            return float(t)
        except ValueError:
            return t


def _parse(it):
    t = next(it)
    if t == '[':
        out = []
        while (x := _parse(it)) is not _END:
            out.append(x)
        return out
    if t == '{':
        out = {}
        while (k := _parse(it)) is not _END:
            v = _parse(it)
            out[k] = v
        return out
    if t in (']', '}'):
        return _END
    return _atom(t)


def parse_edn(s: str):
    """Parse ONE EDN form (map / vector / atom) from a string."""
    return _parse(_tokens(s))


def read_log(log_path: pathlib.Path = LOG_DEFAULT) -> list[dict]:
    if not log_path.exists():
        return []
    txs = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        txs.append(parse_edn(line))
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
