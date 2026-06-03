#!/usr/bin/env python3
"""kanjō 勘定 — minimal EDN-subset reader (stdlib only).

Parses the subset of EDN the kanjō seed / output files use: a top-level vector
of maps whose values are strings, doubles, longs, keywords, nil/true/false, and
nested vectors. No tagged literals, no sets, no symbols. Sufficient for reading
data/seed-financial-facts.kotoba.edn and the generated *.kotoba.edn outputs.

Returns Python: maps→dict (keyword keys as ":foo" strings), keywords→":foo"
strings, vectors→list. Mirrors kabuto/kanjo_edn shape so the actor family reads
its own substrate without a third-party EDN dependency.
"""
from __future__ import annotations


class _R:
    def __init__(self, s: str):
        self.s = s
        self.i = 0
        self.n = len(s)

    def peek(self):
        return self.s[self.i] if self.i < self.n else ""

    def skip_ws(self):
        while self.i < self.n:
            c = self.s[self.i]
            if c == ";":  # line comment
                while self.i < self.n and self.s[self.i] != "\n":
                    self.i += 1
            elif c in " \t\r\n,":
                self.i += 1
            else:
                break

    def read(self):
        self.skip_ws()
        if self.i >= self.n:
            return _EOF
        c = self.s[self.i]
        if c == "[":
            return self._vec("]")
        if c == "{":
            return self._map()
        if c == '"':
            return self._str()
        if c == ":":
            return self._kw()
        return self._atom()

    def _vec(self, close):
        self.i += 1  # consume [
        out = []
        while True:
            self.skip_ws()
            if self.peek() == close:
                self.i += 1
                return out
            v = self.read()
            if v is _EOF:
                raise ValueError("unterminated vector")
            out.append(v)

    def _map(self):
        self.i += 1  # consume {
        out = {}
        while True:
            self.skip_ws()
            if self.peek() == "}":
                self.i += 1
                return out
            k = self.read()
            v = self.read()
            out[k] = v

    def _str(self):
        self.i += 1  # consume opening quote
        buf = []
        while self.i < self.n:
            c = self.s[self.i]
            if c == "\\":
                self.i += 1
                nxt = self.s[self.i] if self.i < self.n else ""
                buf.append({"n": "\n", "t": "\t", "r": "\r"}.get(nxt, nxt))
            elif c == '"':
                self.i += 1
                return "".join(buf)
            else:
                buf.append(c)
            self.i += 1
        raise ValueError("unterminated string")

    def _kw(self):
        j = self.i
        self.i += 1
        while self.i < self.n and self.s[self.i] not in ' \t\r\n,[]{}"':
            self.i += 1
        return self.s[j:self.i]  # keep leading ':'

    def _atom(self):
        j = self.i
        while self.i < self.n and self.s[self.i] not in ' \t\r\n,[]{}"':
            self.i += 1
        tok = self.s[j:self.i]
        if tok == "nil":
            return None
        if tok == "true":
            return True
        if tok == "false":
            return False
        try:
            if any(ch in tok for ch in ".eE") and tok.lstrip("-+").replace(".", "", 1).replace("e", "", 1).replace("E", "", 1).replace("-", "", 1).replace("+", "", 1).isdigit():
                return float(tok)
            return int(tok)
        except ValueError:
            return tok  # bare symbol — kept as string


_EOF = object()


def read_all(text: str):
    """Read every top-level form; return the first vector found (the dataset)."""
    r = _R(text)
    forms = []
    while True:
        v = r.read()
        if v is _EOF:
            break
        forms.append(v)
    for f in forms:
        if isinstance(f, list):
            return f
    return forms[0] if forms else []


def read_file(path: str):
    with open(path, "r") as f:
        return read_all(f.read())
