"""kabuto 兜 — shared minimal EDN reader + datom classifier (stdlib only).

Ported from the watatsuna/tsumugi readers (same subset: vectors [], maps {},
:keyword, "string", number, bool, nil). Keeps kabuto's cells dependency-free so
they run on any python3 with no install step. ADR-2606022000.
"""
from __future__ import annotations
import re
import pathlib

# ── minimal EDN reader (subset) ──────────────────────────────────────────────
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
        return t  # keep keywords as ":ns/name" strings
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


def load_edn(path: pathlib.Path):
    it = _tokens(pathlib.Path(path).read_text(encoding='utf-8'))
    return _parse(it)


# ── classify the flat datom vector into entity buckets ───────────────────────
def classify(rows):
    """Return (companies, addresses, contacts, edges, processes) keyed/listed."""
    companies, addresses, contacts, edges, processes = {}, [], [], [], []
    for r in rows:
        if not isinstance(r, dict):
            continue
        if ':company/id' in r:
            companies[r[':company/id']] = r
        elif ':company.address/id' in r:
            addresses.append(r)
        elif ':company.contact/id' in r:
            contacts.append(r)
        elif ':supply.edge/id' in r:
            edges.append(r)
        elif ':company.process/id' in r:
            processes.append(r)
    return companies, addresses, contacts, edges, processes


def edn_str(s: str) -> str:
    """EDN-escape a python string into a quoted EDN string literal."""
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'
