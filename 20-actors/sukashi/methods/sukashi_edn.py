"""sukashi 透かし — shared minimal EDN reader + datom classifier (stdlib only).

Ported from the kabuto/watatsuna/tsumugi readers (same subset: vectors [], maps {},
:keyword, "string", number, bool, nil). Keeps sukashi's cells dependency-free so they
run on any python3 with no install step. ADR-2606071600.
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
    """Return (adtech, auth_edges, creatives, delivery_edges, fraud_signals).

    adtech is keyed by :adtech/id; the rest are lists in document order.
    """
    adtech, auth, creatives, delivery, fraud = {}, [], [], [], []
    for r in rows:
        if not isinstance(r, dict):
            continue
        if ':adtech/id' in r:
            adtech[r[':adtech/id']] = r
        elif ':adauth.edge/id' in r:
            auth.append(r)
        elif ':adcreative/id' in r:
            creatives.append(r)
        elif ':addelivery.edge/id' in r:
            delivery.append(r)
        elif ':adfraud.signal/id' in r:
            fraud.append(r)
    return adtech, auth, creatives, delivery, fraud


def edn_str(s: str) -> str:
    """EDN-escape a python string into a quoted EDN string literal."""
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'
