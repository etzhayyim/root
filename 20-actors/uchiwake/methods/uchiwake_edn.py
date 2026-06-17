"""uchiwake 内訳 — shared minimal EDN reader + datom classifier (stdlib only).

Ported from the kabuto/watatsuna readers (same subset: vectors [], maps {},
:keyword, "string", number, bool, nil). Keeps uchiwake's cells dependency-free so
they run on any python3 with no install step. ADR-2606081800.
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


def read_str(text: str):
    """Parse the first top-level form from EDN text (1:1 with read-edn in the .cljc port).
    Used to read one append-only kotoba Datom-log line back (one tx map per line)."""
    return _parse(_tokens(text))


# ── classify the flat datom vector into entity buckets ───────────────────────
def classify(rows):
    """Return a dict of entity buckets keyed/listed by uchiwake entity kind."""
    out = {
        'products': {}, 'parts': {}, 'materials': {},
        'bom': [], 'process': [], 'logistics': [], 'design': [], 'ownership': [],
    }
    for r in rows:
        if not isinstance(r, dict):
            continue
        if ':product/id' in r:
            out['products'][r[':product/id']] = r
        elif ':part/id' in r:
            out['parts'][r[':part/id']] = r
        elif ':material/id' in r:
            out['materials'][r[':material/id']] = r
        elif ':bom.edge/id' in r:
            out['bom'].append(r)
        elif ':process.step/id' in r:
            out['process'].append(r)
        elif ':logistics.leg/id' in r:
            out['logistics'].append(r)
        elif ':design.ref/id' in r:
            out['design'].append(r)
        elif ':company.ownership/id' in r:
            out['ownership'].append(r)
    return out


def edn_str(s: str) -> str:
    """EDN-escape a python string into a quoted EDN string literal."""
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


# ── GTIN helpers ─────────────────────────────────────────────────────────────
def normalize_gtin(gtin: str) -> str:
    """Left-zero-pad any GTIN-8/12/13 to the canonical 14-digit GTIN-14."""
    d = ''.join(ch for ch in str(gtin) if ch.isdigit())
    return d.zfill(14)


def gtin_check_digit_ok(gtin: str) -> bool:
    """Validate the GS1 mod-10 check digit of a GTIN (any length 8/12/13/14)."""
    d = ''.join(ch for ch in str(gtin) if ch.isdigit())
    if len(d) not in (8, 12, 13, 14):
        return False
    body, check = d[:-1], int(d[-1])
    # GS1: rightmost body digit weighted x3, alternating.
    total = 0
    for i, ch in enumerate(reversed(body)):
        total += int(ch) * (3 if i % 2 == 0 else 1)
    return (10 - (total % 10)) % 10 == check
