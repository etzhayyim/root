"""ipaddress — shared minimal EDN reader + datom classifier (stdlib only).

Ported from kabuto/watatsuna readers (same subset: vectors [], maps {}, :keyword,
"string", number, bool, nil). Keeps the ipaddress cells dependency-free so they run
on any python3 with no install step. ADR-2605301400 §T2.
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
_BUCKETS = (
    (":rir/id", "rirs"), (":asn/id", "asns"), (":iprange/id", "ranges"),
    (":ip/id", "ips"), (":net.announce/id", "announces"), (":net.member/id", "members"),
    (":geo/id", "geos"), (":rdns/id", "rdns"), (":whois/id", "whois"),
)


def classify(rows):
    """Return dict bucket-name → (dict keyed by id for entities, list for edges)."""
    out = {name: {} for _k, name in _BUCKETS}
    keyed = {"rirs", "asns", "ranges", "ips"}
    for name in out:
        if name not in keyed:
            out[name] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        for key, name in _BUCKETS:
            if key in r:
                if name in keyed:
                    out[name][r[key]] = r
                else:
                    out[name].append(r)
                break
    return out


def edn_str(s: str) -> str:
    """EDN-escape a python string into a quoted EDN string literal."""
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


def edn_val(x):
    """Render a python value as EDN (keyword strings pass through unquoted)."""
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, (int, float)):
        return str(x)
    if isinstance(x, list):
        return "[" + " ".join(edn_val(i) for i in x) + "]"
    if isinstance(x, str):
        return x if x.startswith(":") else edn_str(x)
    return edn_str(str(x))


def to_edn(recs, header_lines):
    lines = list(header_lines) + ["["]
    for r in recs:
        lines.append(" {" + " ".join(f"{k} {edn_val(v)}" for k, v in r.items()) + "}")
    lines.append("]")
    return "\n".join(lines) + "\n"
