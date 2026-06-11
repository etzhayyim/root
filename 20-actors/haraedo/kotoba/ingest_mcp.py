#!/usr/bin/env python3
"""haraedo 祓戸 — ingest seed.edn into a live kotoba node via MCP.

ADR-2606010200. This kotoba build exposes the Datom store through the MCP
JSON-RPC endpoint (`POST /mcp`), NOT a bulk EDN /transact route. So we flatten
each seed entity map into (graph, subject, predicate, object) datoms and assert
them one-by-one via the `kotoba_datom_create` tool, then `kotoba commit` seals
them. Murakumo-only invariant is untouched (no LLM call here).

Usage:
    python3 ingest_mcp.py [--url http://127.0.0.1:8077] [--graph com.etzhayyim.haraedo] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request

SEED = os.path.join(os.path.dirname(__file__), "seed.edn")


# --------------------------------------------------------------------------- #
# minimal EDN reader (covers the seed subset: maps/vectors/sets/kw/str/num/bool)
# --------------------------------------------------------------------------- #
class _Kw(str):
    """An EDN keyword; carries its name without the leading ':'."""


class _EdnReader:
    DELIM = set(' \t\r\n,{}[]()";')

    def __init__(self, s):
        self.s = s
        self.i = 0
        self.n = len(s)

    def _skip(self):
        while self.i < self.n:
            c = self.s[self.i]
            if c in " \t\r\n,":
                self.i += 1
            elif c == ";":
                while self.i < self.n and self.s[self.i] != "\n":
                    self.i += 1
            else:
                break

    def read(self):
        self._skip()
        if self.i >= self.n:
            raise EOFError
        c = self.s[self.i]
        if c == "{":
            return self._read_map()
        if c == "[":
            return self._read_seq("]")
        if c == "(":
            return self._read_seq(")")
        if c == "#" and self.i + 1 < self.n and self.s[self.i + 1] == "{":
            self.i += 1
            return set(self._read_seq("}"))
        if c == '"':
            return self._read_str()
        if c == ":":
            return self._read_kw()
        return self._read_atom()

    def _read_seq(self, close):
        self.i += 1
        out = []
        while True:
            self._skip()
            if self.i >= self.n:
                raise EOFError("unterminated seq")
            if self.s[self.i] == close:
                self.i += 1
                return out
            out.append(self.read())

    def _read_map(self):
        self.i += 1
        out = {}
        while True:
            self._skip()
            if self.i >= self.n:
                raise EOFError("unterminated map")
            if self.s[self.i] == "}":
                self.i += 1
                return out
            k = self.read()
            v = self.read()
            out[k] = v

    def _read_str(self):
        self.i += 1
        buf = []
        while self.i < self.n:
            c = self.s[self.i]
            if c == "\\":
                nxt = self.s[self.i + 1]
                buf.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, nxt))
                self.i += 2
                continue
            if c == '"':
                self.i += 1
                return "".join(buf)
            buf.append(c)
            self.i += 1
        raise EOFError("unterminated string")

    def _read_kw(self):
        self.i += 1
        start = self.i
        while self.i < self.n and self.s[self.i] not in self.DELIM:
            self.i += 1
        return _Kw(self.s[start:self.i])

    def _read_atom(self):
        start = self.i
        while self.i < self.n and self.s[self.i] not in self.DELIM:
            self.i += 1
        tok = self.s[start:self.i]
        if tok == "true":
            return True
        if tok == "false":
            return False
        if tok == "nil":
            return None
        try:
            return int(tok)
        except ValueError:
            pass
        try:
            return float(tok)
        except ValueError:
            return tok


def _obj_str(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, _Kw):
        return str(v)
    return str(v)


def _subject_of(entity):
    """Identity = the key ending in /id, else .../code."""
    for k in entity:
        if isinstance(k, _Kw) and k.endswith("/id"):
            return _obj_str(entity[k])
    for k in entity:
        if isinstance(k, _Kw) and k.endswith("/code"):
            return _obj_str(entity[k])
    return None


def flatten(entities):
    """Yield (subject, predicate, object) datoms; set values fan out."""
    for ent in entities:
        if not isinstance(ent, dict):
            continue
        subj = _subject_of(ent)
        if subj is None:
            continue
        for k, v in ent.items():
            pred = str(k)  # keyword name already strips leading ':'
            if isinstance(v, set):
                for member in sorted(_obj_str(m) for m in v):
                    yield subj, pred, member
            else:
                yield subj, pred, _obj_str(v)


# --------------------------------------------------------------------------- #
# MCP transport
# --------------------------------------------------------------------------- #
def mcp_call(url, name, arguments, rid=1, token=None):
    body = json.dumps({
        "jsonrpc": "2.0", "id": rid, "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }).encode()
    req = urllib.request.Request(url + "/mcp", data=body,
                                 headers={"content-type": "application/json"})
    if token:
        req.add_header("authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def cli_put(url, graph, s, p, o):
    """Assert one quad via the `kotoba quad put` CLI (auto-auths via Keychain identity)."""
    r = subprocess.run(
        ["kotoba", "--url", url, "quad", "put", graph, s, p, o],
        capture_output=True, text=True, timeout=30,
    )
    return r.returncode == 0, (r.stderr or r.stdout).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.environ.get("KOTOBA_URL", "http://127.0.0.1:8077"))
    ap.add_argument("--graph", default="com.etzhayyim.haraedo")
    ap.add_argument("--token", default=os.environ.get("KOTOBA_TOKEN"))
    ap.add_argument("--via", choices=["cli", "mcp"], default="cli",
                    help="cli = `kotoba quad put` (auto-auth via Keychain); mcp = raw /mcp (needs --token JWT)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(SEED, encoding="utf-8") as f:
        entities = _EdnReader(f.read()).read()
    datoms = list(flatten(entities))
    print(f"parsed {len(entities)} entities → {len(datoms)} datoms (graph={args.graph})")

    if args.dry_run:
        for s, p, o in datoms[:12]:
            print(f"  {s}  {p}  {o}")
        print(f"  … ({len(datoms)} total)")
        return 0

    ok = err = 0
    for n, (s, p, o) in enumerate(datoms, 1):
        try:
            if args.via == "cli":
                good, msg = cli_put(args.url, args.graph, s, p, o)
                if good:
                    ok += 1
                else:
                    err += 1
                    if err <= 3:
                        print(f"  ERR {s} {p}: {msg}")
            else:
                res = mcp_call(args.url, "kotoba_datom_create",
                               {"graph": args.graph, "subject": s, "predicate": p, "object": o},
                               rid=n, token=args.token)
                if "error" in res:
                    err += 1
                    if err <= 3:
                        print(f"  ERR {s} {p}: {res['error']}")
                else:
                    ok += 1
        except Exception as e:  # noqa: BLE001
            err += 1
            if err <= 3:
                print(f"  EXC {s} {p}: {e}")
    print(f"asserted {ok} ok / {err} err / {len(datoms)} total")
    print("→ run `kotoba commit` to seal the hot arrangement into ProllyTrees")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
