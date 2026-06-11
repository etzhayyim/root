#!/usr/bin/env python3
"""kotoba.py — yabai kotoba Datom-log writer (local, content-addressed). ADR-2605301400
§T3 + ADR-2605262130 + ADR-2605312345.

The substrate boundary (root CLAUDE.md): canonical state is the **kotoba Datom log** —
content-addressed EAVT assertions, append-only (G10 / 非終末論). `methods/transact.py` is the
OTHER write path: an HTTP push into a *running* kotoba node (operator-JWT / CACAO gated, verified
live 2026-06-03). This module is the **local, autonomous-loop** write path — the same path
shionome / ipaddress use (`methods/autorun.py`): a self-driving heartbeat appends content-addressed
transactions to a local append-only EDN log with NO external I/O, so yabai can run its own
observe→analyze→persist CTI cycle on the Murakumo fleet without a human or a live node in the loop.

G6/G10 (constitutional) is enforced HERE at the local write too, not only in transact.py: every
`:access/*` access-audit record carries accessor identity / IP / device PII and MUST live behind
a `com.etzhayyim.encrypted.*` envelope (`:cti.attr/encrypted true`). `assert_access_encrypted`
RAISES before any persist if a plaintext access record is present — so the autonomous loop can
NEVER write plaintext PII to the log, by construction.

  - graph_datoms(rows)   → EAVT assertions for every CTI entity (domains / pdns / iphist / certs /
                           indicators / access). Access records carry only the encrypted-envelope
                           markers (the seed never holds plaintext PII).
  - derived_datoms(a)    → EAVT assertions for the analyzer's derived :cti/* signals (fast-flux,
                           hosting concentration, IOC load, IP-movement, cert pivots, encryption
                           self-audit), flagged :cti/derived true (recomputed, never re-ingested).
  - assert_access_encrypted(rows) → G6/G10 guard; raises PlaintextAccessError on a violation.
  - make_tx / append_tx / read_log / head_cid / verify_chain — the content-addressed commit-DAG.

EAVT = [op entity attribute value]; op is :db/add only (append-only — no :db/retract). E = the
entity's stable id string. Stdlib only. Deterministic: the caller supplies tx_id + as_of.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yabai_edn import _parse, _tokens, edn_val  # noqa: E402

LOG_DEFAULT = (pathlib.Path(__file__).resolve().parents[1] / "data"
               / "yabai.datoms.kotoba.edn")

ID_KEYS = (":domain/id", ":pdns/id", ":iphist/id", ":tlscert/id", ":indicator/id", ":access/id")


class PlaintextAccessError(ValueError):
    """Raised when an :access/* record lacks :cti.attr/encrypted true (G6/G10 violation)."""


def assert_access_encrypted(rows: list) -> None:
    """G6/G10: REFUSE to proceed if any access-audit record is plaintext. Mirrors
    transact.check_encryption_invariant, but raises so the autonomous loop hard-stops rather
    than ever persisting plaintext accessor PII to the local log."""
    bad = [r.get(":access/id") for r in rows
           if isinstance(r, dict) and ":access/id" in r
           and r.get(":cti.attr/encrypted") is not True]
    if bad:
        raise PlaintextAccessError(
            f"{len(bad)} access-audit record(s) lack :cti.attr/encrypted true (G6/G10): {bad}. "
            "Encrypt accessor PII into a com.etzhayyim.encrypted.* envelope first.")


def _add(entity: str, attr: str, value: Any) -> list:
    """One append-only EAVT assertion: [:db/add <entity> <attr> <value>]."""
    return [":db/add", entity, attr, value]


def graph_datoms(rows: list) -> list[list]:
    """Flatten the merged CTI graph into append-only EAVT assertions. Enforces G6/G10 first.
    E = the entity's id; cardinality-many list values fan out (mirrors transact.rows_to_datoms)."""
    assert_access_encrypted(rows)
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


def derived_datoms(concentration: dict, *, prefix: str = "cti") -> list[list]:
    """Flatten the analyzer's derived :cti/* signals into EAVT assertions, each flagged
    :cti/derived true (defensive RESILIENCE signals recomputed on read, never re-ingested as
    fact). `concentration` is the dict returned by analyze.analyze()."""
    a = concentration
    out: list[list] = []
    for i, (dom, nips, ttl) in enumerate(a["fast_flux"]):
        e = f"{prefix}-fastflux-{i}"
        out += [_add(e, ":cti/fast-flux-domain", dom),
                _add(e, ":cti/distinct-ips", nips),
                _add(e, ":cti/ttl", ttl),
                _add(e, ":cti/derived", True)]
    for pt, n in sorted(a["ptype_load"].items(), key=lambda kv: -kv[1]):
        e = f"{prefix}-hosting-{str(pt).lstrip(':')}"
        out += [_add(e, ":cti/hosting-concentration", pt),
                _add(e, ":cti/observations", n),
                _add(e, ":cti/derived", True)]
    for tlp, n in sorted(a["tlp_load"].items(), key=lambda kv: -kv[1]):
        e = f"{prefix}-tlp-{str(tlp).lstrip(':')}"
        out += [_add(e, ":cti/ioc-tlp-load", tlp),
                _add(e, ":cti/indicators", n),
                _add(e, ":cti/derived", True)]
    for cat, n in sorted(a["cat_load"].items(), key=lambda kv: -kv[1]):
        e = f"{prefix}-cat-{str(cat).lstrip(':')}"
        out += [_add(e, ":cti/ioc-category-load", cat),
                _add(e, ":cti/indicators", n),
                _add(e, ":cti/derived", True)]
    for ip, n in a["ip_movement"]:
        e = f"{prefix}-ipmove-{str(ip).lstrip(':')}"
        out += [_add(e, ":cti/ip-movement", ip),
                _add(e, ":cti/history-observations", n),
                _add(e, ":cti/derived", True)]
    for i, (subj, nsan, anom) in enumerate(a["cert_pivot"]):
        e = f"{prefix}-certpivot-{i}"
        out += [_add(e, ":cti/cert-pivot", subj),
                _add(e, ":cti/san-count", nsan),
                _add(e, ":cti/anomaly", anom),
                _add(e, ":cti/derived", True)]
    e = f"{prefix}-access-audit"
    out += [_add(e, ":cti/access-audit-total", a["access_total"]),
            _add(e, ":cti/access-encrypted", a["access_encrypted"]),
            _add(e, ":cti/plaintext-violations", a["plaintext_violations"]),
            _add(e, ":cti/derived", True)]
    return out


def _canonical(datoms: list[list], prev_cid: str) -> bytes:
    return json.dumps({"prev": prev_cid, "datoms": datoms},
                      ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def tx_cid(datoms: list[list], prev_cid: str = "") -> str:
    """Content address of a transaction = sha256 over (prev_cid, datoms) → a commit-DAG."""
    return "b" + hashlib.sha256(_canonical(datoms, prev_cid)).hexdigest()


def make_tx(datoms: list[list], *, tx_id: int, as_of: int, prev_cid: str = "") -> dict:
    """Build a content-addressed transaction (caller supplies tx_id + as_of — no wall clock)."""
    return {
        ":tx/id": tx_id,
        ":tx/as-of": as_of,
        ":tx/prev": prev_cid,
        ":tx/cid": tx_cid(datoms, prev_cid),
        ":tx/count": len(datoms),
        ":tx/datoms": datoms,
    }


def _tx_to_edn(tx: dict) -> str:
    """Serialize one transaction as a single-line EDN map (reuses yabai_edn.edn_val)."""
    datoms = " ".join("[" + " ".join(edn_val(x) for x in d) + "]" for d in tx[":tx/datoms"])
    return (f'{{:tx/id {tx[":tx/id"]} :tx/as-of {tx[":tx/as-of"]} '
            f':tx/prev {edn_val(tx[":tx/prev"])} :tx/cid {edn_val(tx[":tx/cid"])} '
            f':tx/count {tx[":tx/count"]} :tx/datoms [{datoms}]}}')


def append_tx(tx: dict, log_path: pathlib.Path = LOG_DEFAULT) -> str:
    """Append ONE transaction to the append-only log (never rewrites). Returns the tx CID."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.write_text(";; yabai kotoba Datom log — append-only EAVT transactions "
                            "(content-addressed DAG; G6/G10: no plaintext :access PII). "
                            "DO NOT hand-edit. ADR-2605301400 §T3.\n", encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(_tx_to_edn(tx) + "\n")
    return tx[":tx/cid"]


def read_log(log_path: pathlib.Path = LOG_DEFAULT) -> list[dict]:
    """Read the log back as a list of transaction dicts (uses the shared yabai_edn reader)."""
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
    """The content-addressed HEAD = the last transaction's CID."""
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
    from yabai_edn import load_edn

    here = _pl.Path(__file__).resolve().parents[1]
    g = here / "data" / "passive-dns.merged.kotoba.edn"
    if not g.exists():
        g = here / "data" / "seed-passive-dns.kotoba.edn"
    datoms = graph_datoms(load_edn(g))  # raises if any plaintext :access PII (G6/G10)
    tx = make_tx(datoms, tx_id=1, as_of=20260608, prev_cid="")
    print(f"# yabai kotoba Datom tx — {tx[':tx/count']} EAVT assertions, cid={tx[':tx/cid'][:18]}… "
          "(G6/G10 access-encryption invariant held)")
