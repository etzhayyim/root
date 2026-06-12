"""yabai — shared minimal EDN reader + datom classifier (stdlib only).

Ported from kabuto/ipaddress readers (same subset: vectors [], maps {}, :keyword,
"string", number, bool, nil). Keeps the yabai CTI cells dependency-free. ADR-2605301400 §T3.
"""
from __future__ import annotations
import re
import pathlib

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


def load_edn(path: pathlib.Path):
    it = _tokens(pathlib.Path(path).read_text(encoding='utf-8'))
    return _parse(it)


_BUCKETS = (
    (":domain/id", "domains"), (":pdns/id", "pdns"), (":iphist/id", "iphist"),
    (":tlscert/id", "certs"), (":indicator/id", "indicators"), (":access/id", "access"),
    (":btobs/id", "btobs"),
)
_KEYED = {"domains"}


def classify(rows):
    out = {name: ({} if name in _KEYED else []) for _k, name in _BUCKETS}
    for r in rows:
        if not isinstance(r, dict):
            continue
        for key, name in _BUCKETS:
            if key in r:
                if name in _KEYED:
                    out[name][r[key]] = r
                else:
                    out[name].append(r)
                break
    return out


def edn_str(s: str) -> str:
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


def edn_val(x):
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
