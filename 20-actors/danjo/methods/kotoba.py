#!/usr/bin/env python3
"""kotoba.py — danjo kotoba Datom-log writer (local, content-addressed). ADR-2605301600
+ ADR-2605262130 + ADR-2605312345.

The substrate boundary (root CLAUDE.md): canonical state is the **kotoba Datom log** —
content-addressed EAVT assertions, append-only (非終末論). danjo had a JSON corpus + an open
detector method-pack + an analyzer but no self-driving loop and no local log; this module is the
**local, autonomous-loop** write path — the same path shionome / ipaddress / yabai / sukashi /
watatsuna / watari / kabuto / kanjō use (`methods/autorun.py`): a self-driving heartbeat appends
content-addressed transactions to a local append-only EDN log with NO external I/O, so danjo can
run its own observe→cross-reference→persist public-accountability cycle on the Murakumo fleet
without a human or a live node in the loop.

Constitutional posture is preserved by construction (danjo discipline): the censor's EYE, never the
SWORD — only FACTUAL discrepancy observations over the public record are representable, NEVER a
verdict of wrongdoing (G4: `:danjo.obs/non-adjudicating` is always true and no verdict attr exists);
every observation cites ≥2 source-record CIDs (G5) + an open method-note CID (G6). The loop persists
exactly what `analyze.run_all` already produced (each observation already passed build_observation's
structural non-adjudication self-check).

  - graph_datoms(records)        → EAVT assertions for every public procurement record (the input
                                   the open detectors cross-reference). E = the record CID.
  - derived_datoms(observations) → EAVT assertions for each danjo.discrepancyObservation, flagged
                                   :danjo.obs/non-adjudicating true (G4) + :representative.
  - make_tx / append_tx / read_log / head_cid / verify_chain — content-addressed commit-DAG.

EAVT = [op entity attribute value]; op is :db/add only (append-only — no :db/retract). Stdlib only.
Deterministic: the caller supplies tx_id + as_of (no wall clock) → resume-safe.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
from typing import Any

LOG_DEFAULT = (pathlib.Path(__file__).resolve().parents[1] / "data" / "persisted"
               / "danjo.datoms.kotoba.edn")

# fields that would make a persisted observation a VERDICT — must NEVER appear (G4, structural).
_FORBIDDEN_VERDICT_TOKENS = ("verdict", "guilt", "wrongdoing", "finding", "culprit",
                             "illegal", "crime", "violation", "unlawful", "fraud", "sanction")


def _add(entity: str, attr: str, value: Any) -> list:
    """One append-only EAVT assertion: [:db/add <entity> <attr> <value>]."""
    return [":db/add", entity, attr, value]


def graph_datoms(records: list[dict]) -> list[list]:
    """Flatten the public procurement corpus into append-only EAVT assertions. E = the record's
    public-record CID; attrs are namespaced :gov.procurement/*. Public pre-published record only
    (G3) — danjo re-fetches nothing."""
    out: list[list] = []
    for r in records:
        if not isinstance(r, dict):
            continue
        e = r.get("cid")
        if not e:
            continue
        for k, v in r.items():
            if k == "cid":
                continue
            out.append(_add(e, f":gov.procurement/{k}", v))
    return out


def _obs_id(o: dict) -> str:
    """A stable, deterministic entity id for an observation (category + first source CID)."""
    cid0 = (o.get("sourceRecordCids") or ["?"])[0]
    return f"danjo-obs:{o.get('category', '?')}:{cid0}"


def derived_datoms(observations: list[dict]) -> list[list]:
    """Flatten danjo.discrepancyObservation records into append-only EAVT assertions, each carrying
    :danjo.obs/non-adjudicating true (G4 — a FACT, never a verdict), ≥2 source CIDs (G5), and the
    open method-note CID (G6). RAISES if a verdict token ever creeps into an attr (G4 structural)."""
    out: list[list] = []
    for o in observations:
        e = _obs_id(o)
        out += [
            _add(e, ":danjo.obs/category", ":" + str(o.get("category", "?")).lstrip(":")),
            _add(e, ":danjo.obs/non-adjudicating", True),
            _add(e, ":danjo.obs/pattern", o.get("observedPattern", "")),
            _add(e, ":danjo.obs/source-record-cids", list(o.get("sourceRecordCids", []))),
            _add(e, ":danjo.obs/method-note-cid", o.get("methodNoteCid", "")),
            _add(e, ":danjo.obs/known-false-positive-modes", list(o.get("knownFalsePositiveModes", []))),
            _add(e, ":danjo.obs/sourcing", ":representative"),
        ]
    # G4 structural self-check: no verdict token may appear in any attribute we persist.
    for d in out:
        attr = str(d[2]).lower()
        if any(tok in attr for tok in _FORBIDDEN_VERDICT_TOKENS):
            raise ValueError(f"G4: verdict attr {d[2]!r} is unrepresentable in a danjo observation")
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
        log_path.write_text(";; danjo kotoba Datom log — append-only EAVT transactions "
                            "(content-addressed DAG). The censor's EYE, never the SWORD: "
                            "non-adjudicating observations only (G4). DO NOT hand-edit. ADR-2605301600.\n",
                            encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(_tx_to_edn(tx) + "\n")
    return tx[":tx/cid"]


# ── minimal EDN reader (subset) for read-back, consistent with the actor family ──
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


def read_log(log_path: pathlib.Path = LOG_DEFAULT) -> list[dict]:
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
