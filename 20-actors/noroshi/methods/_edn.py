"""Minimal EDN reader (subset: [] {} :kw "str" num bool nil) — ported from watatsuna/tsumugi.

Keeps keywords as ":ns/name" strings. Stdlib only. Used by cable_endpoint.py to read the watatsuna
submarine-cable seed without a dependency, mirroring the watatsuna analyzer's own parser for parity.
"""

from __future__ import annotations

import pathlib
import re

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
    if t == "true":
        return True
    if t == "false":
        return False
    if t == "nil":
        return None
    if t.startswith(":"):
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
    if t == "[":
        out = []
        while (x := _parse(it)) is not _END:
            out.append(x)
        return out
    if t == "{":
        out = {}
        while (k := _parse(it)) is not _END:
            v = _parse(it)
            out[k] = v
        return out
    if t in ("]", "}"):
        return _END
    return _atom(t)


def load_edn(path: pathlib.Path):
    return _parse(_tokens(pathlib.Path(path).read_text(encoding="utf-8")))
