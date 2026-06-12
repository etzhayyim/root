#!/usr/bin/env python3
"""ingest.py — meisai 明細: member card-statement EDN → kotoba EAVT datoms. ADR-2606122400.

Intake = the statement EDN the MEMBER-PRINCIPAL fetch leg wrote locally. The fetch leg is
com-junkawasaki/computer-use-clj `examples/sumitclub_meisai.clj` — a read-only computer-use agent
the member runs on their OWN machine against their OWN card account (karakuri 絡繰 T2 posture),
on Murakumo-conformant local inference (Ollama gemma 4 QAT — ADR-2605215000), with credentials
vault-injected (`type_secret`) so no secret ever reaches a model, a log, or this actor. It emits:

    {:source :sumitclub
     :source/url "https://www.sumitclub.jp/…"
     :statement/month "2026-05"
     :statement/total-jpy 46540
     :statement/rows [{:date "2026-05-02" :merchant "AMAZON.CO.JP" :amount_jpy 3980} …]}

meisai itself does NO network I/O and holds NO credential: it reads that local file, normalizes
each row into append-only EAVT datoms, and persists via kotoba.py. Two gates are STRUCTURAL here:

  - **G2 credential-unrepresentable**: a credential-shaped key (password / secret / otp / cvv /
    pin / token / credential) or a PAN-shaped value (13-19 digit run, spaces/dashes allowed)
    anywhere in the intake RAISES — a card number or secret cannot enter the Datom log.
  - **G5 provenance**: every statement tx carries the intake file's content CID; row entity ids
    are deterministic content hashes → re-ingest of the same intake is a no-op (dedup by CID).

Stdlib only. Deterministic (no wall clock, no randomness).
"""
from __future__ import annotations

import hashlib
import pathlib
import re
from typing import Any

import kotoba

_FORBIDDEN_KEY_TOKENS = ("password", "secret", "otp", "cvv", "credential", "token", "pin")
# 13-19 consecutive digits, optionally space/dash-grouped → a primary account number shape.
_PAN_RE = re.compile(r"(?:\d[ -]?){13,19}")


def intake_cid(raw: bytes) -> str:
    """Content address of the intake file bytes (G5 provenance + dedup key)."""
    return "b" + hashlib.sha256(raw).hexdigest()


def _walk(node: Any, path: str = ""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk(k, path)
            yield from _walk(v, f"{path}/{k}")
    elif isinstance(node, list):
        for x in node:
            yield from _walk(x, path)
    else:
        yield path, node


def guard(doc: Any) -> None:
    """G2 structural gate: refuse credential-shaped keys and PAN-shaped values anywhere."""
    for path, leaf in _walk(doc):
        s = str(leaf)
        low = s.lower()
        if any(tok in low for tok in _FORBIDDEN_KEY_TOKENS) and low.startswith(":"):
            raise ValueError(f"G2: credential-shaped key {s!r} is unrepresentable in meisai")
        digits = _PAN_RE.search(s)
        if digits and len(re.sub(r"\D", "", digits.group())) >= 13:
            raise ValueError(f"G2: PAN-shaped value at {path or '/'} is unrepresentable in meisai")


def _kw(v: Any) -> str:
    """':sumitclub' → 'sumitclub' (keyword → bare name for entity-id use)."""
    return str(v).lstrip(":")


def statement_datoms(doc: dict, cid: str) -> list[list]:
    """Statement intake map (kotoba.parse_edn shape — keys like ':statement/month') →
    append-only EAVT datoms. E(statement) = meisai-stmt:<source>:<month>;
    E(row) = meisai-row:<sha256(stmt|idx|date|merchant|amount)[:16]> (deterministic)."""
    guard(doc)
    source = _kw(doc.get(":source", "unknown"))
    month = str(doc.get(":statement/month", "?"))
    rows = doc.get(":statement/rows") or []
    stmt_e = f"meisai-stmt:{source}:{month}"
    out = [
        kotoba.add(stmt_e, ":meisai.stmt/source", ":" + source),
        kotoba.add(stmt_e, ":meisai.stmt/month", month),
        kotoba.add(stmt_e, ":meisai.stmt/row-count", len(rows)),
        kotoba.add(stmt_e, ":meisai.stmt/intake-cid", cid),
    ]
    if doc.get(":statement/total-jpy") is not None:
        out.append(kotoba.add(stmt_e, ":meisai.stmt/total-jpy", int(doc[":statement/total-jpy"])))
    if doc.get(":source/url"):
        out.append(kotoba.add(stmt_e, ":meisai.stmt/source-url", str(doc[":source/url"])))
    for i, r in enumerate(rows):
        date = str(r.get(":date", "?"))
        merchant = str(r.get(":merchant", "?"))
        amount = int(r.get(":amount_jpy", 0))
        h = hashlib.sha256(f"{stmt_e}|{i}|{date}|{merchant}|{amount}".encode("utf-8")).hexdigest()
        row_e = f"meisai-row:{h[:16]}"
        out += [
            kotoba.add(row_e, ":meisai.row/stmt", stmt_e),
            kotoba.add(row_e, ":meisai.row/index", i),
            kotoba.add(row_e, ":meisai.row/date", date),
            kotoba.add(row_e, ":meisai.row/merchant", merchant),
            kotoba.add(row_e, ":meisai.row/amount-jpy", amount),
        ]
        if r.get(":note"):
            out.append(kotoba.add(row_e, ":meisai.row/note", str(r[":note"])))
    return out


def load_statement(path: pathlib.Path) -> tuple[dict, str]:
    """Read one intake EDN file → (doc, content-cid)."""
    raw = path.read_bytes()
    return kotoba.parse_edn(raw.decode("utf-8")), intake_cid(raw)
