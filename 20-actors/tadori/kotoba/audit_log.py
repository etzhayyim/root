#!/usr/bin/env python3
"""audit_log.py — tadori autonomous self-audit kotoba Datom log (local, content-addressed).
ADR-2605301400 §D1 (G2/G3/G5/G12) + ADR-2605262130 + ADR-2605312345.

Why tadori's autonomous loop is DIFFERENT from ipaddress/yabai/shionome:

  tadori is AUTHORIZED-INVESTIGATION-ONLY (G3): every write of a case-anchored OBSERVATION /
  attribution / PII datom requires a `caseMandate`. **No case → Phase 0 dry-run only.** So tadori
  must NOT blindly autonomously-persist observation datoms the way ipaddress/yabai do — that would
  violate G3. Instead, the constitution-permitted autonomous act for tadori is the **silenTadori
  review self-audit heartbeat** (Charter §1.12 Transparent Force, G5): each cycle the actor
  recomputes its 9 structural zero-counters over the OFFLINE staged corpus and persists ONE
  append-only, on-chain-monitorable AUDIT datom — **no observation, no PII, no case data** ever
  touches this log. The audit only commits a clean bill when the staged corpus is gate-clean; any
  nonzero counter HALTS (G12 Bonsai prune), persisting nothing.

This module is the content-addressed commit-DAG write path for that audit heartbeat (the same
shape shionome/ipaddress/yabai use), but the only datoms it ever holds are silenTadoriReview
counters — by construction it can never leak case-anchored intel.

  - review_datoms(review, cycle) → EAVT assertions for one silenTadoriReview heartbeat
  - make_tx / append_tx / read_log / head_cid / verify_chain — content-addressed DAG
  - assert_all_clear(review) → G12 guard; raises SilenReviewHalt on any nonzero counter

EAVT = [op entity attribute value]; op is :db/add only (append-only — no :db/retract, G2).
Stdlib only. Deterministic: the caller supplies tx_id + as_of (no wall clock).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
from typing import Any

LOG_DEFAULT = (pathlib.Path(__file__).resolve().parents[1] / "data" / "persisted"
               / "tadori.silen-review.datoms.kotoba.edn")

# the 9 silenTadoriReview zero-counters (ADR-2605301400 §D1 / lexicon silenTadoriReview)
COUNTERS = ("noncase-write", "plaintext-pii", "proprietary-sor", "enforcement-action",
            "platform-held-key", "murakumo-bypass", "mass-surveillance", "adherent-deanon",
            "non-kotoba-store")


class SilenReviewHalt(RuntimeError):
    """Raised when a silenTadoriReview counter is nonzero — G12 halt (Bonsai seed-tier prune)."""


def assert_all_clear(review: dict) -> None:
    """G12: any nonzero structural counter HALTS. The autonomous loop must persist a passing
    audit ONLY when every counter is zero — a violation halts and writes nothing."""
    nonzero = {k: review[k] for k in COUNTERS if review.get(k, 0) != 0}
    if nonzero:
        raise SilenReviewHalt(
            f"silenTadoriReview HALT (G12): nonzero counter(s) {nonzero} — "
            "tadori prunes to Bonsai seed-tier + routes to chigiri.disputeMediation; "
            "no audit datom persisted.")


def _add(entity: str, attr: str, value: Any) -> list:
    return [":db/add", entity, attr, value]


def review_datoms(review: dict, cycle: int) -> list[list]:
    """Flatten ONE silenTadoriReview heartbeat into append-only EAVT assertions. Holds only the
    9 zero-counters + informational audit totals + the Transparent-Force flag (G5). NEVER any
    observation / PII / case-anchored datom."""
    e = f"silen-tadori-review:cycle-{cycle}"
    out = [
        _add(e, ":tadori.review/cycle", cycle),
        _add(e, ":tadori.review/phase", 0),                 # Phase 0 — no case, dry-run posture
        _add(e, ":tadori.review/transparent-force-logged", True),  # G5
    ]
    for k in COUNTERS:
        out.append(_add(e, f":tadori.review/{k}", review.get(k, 0)))
    out += [
        _add(e, ":tadori.review/sources-audited", review.get("sources-audited", 0)),
        _add(e, ":tadori.review/obs-audited", review.get("obs-audited", 0)),
        _add(e, ":tadori.review/obs-without-case", review.get("obs-without-case", 0)),
        _add(e, ":tadori.review/all-clear", True),          # only reached if assert_all_clear passed
        _add(e, ":tadori.review/derived", True),
    ]
    return out


def _canonical(datoms: list[list], prev_cid: str) -> bytes:
    return json.dumps({"prev": prev_cid, "datoms": datoms},
                      ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def tx_cid(datoms: list[list], prev_cid: str = "") -> str:
    """Content address = sha256 over (prev_cid, datoms) → commit-DAG (G2 append-only proof)."""
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
    """Append ONE audit transaction to the append-only log (never rewrites). Returns the tx CID."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.write_text(";; tadori silenTadoriReview self-audit log — append-only EAVT "
                            "(content-addressed DAG). Audit counters ONLY; no observation / PII / "
                            "case data (G3). DO NOT hand-edit. ADR-2605301400 §D1.\n",
                            encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(_tx_to_edn(tx) + "\n")
    return tx[":tx/cid"]


# ── minimal EDN reader (subset) for read-back, consistent with ip_edn/yabai_edn ──
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
    txs = read_log(log_path)
    prev = ""
    for i, tx in enumerate(txs):
        expect = tx_cid(tx.get(":tx/datoms", []), prev)
        if tx.get(":tx/cid") != expect or tx.get(":tx/prev") != prev:
            return {"ok": False, "length": len(txs), "broken_at": i}
        prev = tx[":tx/cid"]
    return {"ok": True, "length": len(txs), "broken_at": -1}
