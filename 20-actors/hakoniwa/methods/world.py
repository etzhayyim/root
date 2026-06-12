#!/usr/bin/env python3
"""hakoniwa 箱庭 — world-graph loader for the forward-simulation scenario.

ADR-2606111500. Reads a kotoba-EDN scenario graph (:sim/* nodes + :en/* 縁 over the
hakoniwa-scenario-ontology) into plain dicts. The world is a CONTAINED miniature (箱庭)
populated ONLY by FICTIONAL latent personas — never real people.

CONSTITUTIONAL (read before any change):
  G1 — every :persona is SYNTHETIC (:persona/synthetic true): a cohort archetype, NOT a real
    individual. No PII, no real-person profile, no re-identifiable trait. `assert_synthetic`
    enforces this at load time and refuses to load a graph that violates it.
  G2 — the only thing hakoniwa asserts is a DISTRIBUTION (see distribution.py); never a point.
  G3 — the simulation is routed to RESILIENCE; :outcome/use enumerates resilience uses only.

Pure stdlib (no numpy) — runnable inside a kotoba pywasm actor (componentize-py).
"""
from __future__ import annotations
import re
import pathlib

# ── minimal EDN reader (subset: vectors [], maps {}, :keyword, "string", num, bool, nil)
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')

# fields that would indicate a real-person model — FORBIDDEN by G1 (no PII, ever)
FORBIDDEN_PERSONA_FIELDS = {
    ":person/id", ":person/name", ":individual/id", ":user/id", ":account/id",
    ":email", ":phone", ":address", ":geo/point", ":device/id", ":biometric",
    ":real-name", ":dob", ":ssn", ":handle",
}


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


_END = object()


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
            out[k] = _parse(it)
        return out
    if t in (']', '}'):
        return _END
    return _atom(t)


def read_edn(text: str):
    return _parse(_tokens(text))


def assert_synthetic(nodes: dict):
    """G1: every persona MUST be synthetic and MUST carry no PII-class field. Raises on breach."""
    for nid, n in nodes.items():
        if n.get(":sim/kind") != ":persona":
            continue
        if n.get(":persona/synthetic") is not True:
            raise ValueError(f"G1 violation: persona {nid} is not marked :persona/synthetic true")
        leaked = set(n) & FORBIDDEN_PERSONA_FIELDS
        if leaked:
            raise ValueError(f"G1 violation: persona {nid} carries PII-class field(s) {leaked}")


def load(path: pathlib.Path):
    """Return (nodes_by_id, edges) from a scenario EDN graph; enforces G1 (synthetic personas)."""
    forms = read_edn(path.read_text(encoding="utf-8"))
    nodes, edges = {}, []
    for f in forms:
        if not isinstance(f, dict):
            continue
        if ":sim/id" in f:
            nodes[f[":sim/id"]] = f
        elif ":en/from" in f and ":en/to" in f:
            edges.append(f)
    assert_synthetic(nodes)
    return nodes, edges


def personas(nodes: dict):
    return {nid: n for nid, n in nodes.items() if n.get(":sim/kind") == ":persona"}


def signals(nodes: dict):
    return {nid: n for nid, n in nodes.items() if n.get(":sim/kind") == ":signal"}


def outcomes(nodes: dict):
    return {nid: n for nid, n in nodes.items() if n.get(":sim/kind") == ":outcome"}
