#!/usr/bin/env python3
"""inochi 命 — analyzer + Datom-emit tests (ADR-2606073000). Pure stdlib.

Verifies the constitutional invariants empirically:
  - graph loads (nodes + 縁), seed is non-trivial
  - edge-primary (N1): restoration-priority is the integral of incident inbound pressures
    × IUCN weight — recomputed independently here and asserted equal
  - the most-pressured CR keystone ranks at the restoration top (sanity of the lens)
  - pressure 取-holder concentration is non-empty and ordered
  - Datom log emits ground datoms [e a v tx op] and flags derived readouts transient
  - determinism (two runs byte-identical)
"""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze, IUCN_WEIGHT  # noqa: E402
import datom_emit  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-biosphere-graph.kotoba.edn"


def test_load_nontrivial():
    nodes, edges = load(SEED)
    assert len(nodes) >= 20, f"expected a real seed, got {len(nodes)} nodes"
    assert len(edges) >= 30, f"expected a real 縁 web, got {len(edges)} edges"
    kinds = {n.get(":organism/kind") for n in nodes.values()}
    assert {":species", ":pressure"} <= kinds, f"missing core kinds: {kinds}"
    # every edge resolves to known endpoints (no dangling 縁)
    for e in edges:
        assert e[":en/from"] in nodes, f"dangling from: {e[':en/from']}"
        assert e[":en/to"] in nodes, f"dangling to: {e[':en/to']}"


def test_edge_primary_integral():
    """N1: restoration-priority MUST equal the independent integral of incident pressures."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    expect = {}
    for e in edges:
        if e.get(":en/kind") == ":pressures":
            dst = e[":en/to"]
            w = IUCN_WEIGHT.get(nodes[dst].get(":taxon/iucn"), 0.5)
            expect[dst] = expect.get(dst, 0.0) + float(e[":en/grasping-load"]) * w
    for nid, v in expect.items():
        assert abs(res["restoration"][nid] - v) < 1e-9, f"{nid}: {res['restoration'][nid]} != {v}"
    # there is NO stored per-node score key on any node (edge-primary only)
    for n in nodes.values():
        assert not any(k.startswith(":bond/") or k == ":biosphere/score-of-species" for k in n)


def test_restoration_top_is_critical():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    top = max(res["restoration"].items(), key=lambda kv: kv[1])[0]
    # the top bearer should be a CR/EN taxon or a high-pressure ecosystem — never LC noise
    iucn = nodes[top].get(":taxon/iucn")
    kind = nodes[top].get(":organism/kind")
    assert iucn in (":CR", ":EN", None) or kind in (":ecosystem", ":biome"), \
        f"top restoration node {top} has IUCN {iucn} — lens is mis-weighted"


def test_pressure_concentration_nonempty():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    assert res["pressure_out"], "no 取-holder pressure concentration computed"
    # every pressure 取-holder is actually a :pressure node
    for nid in res["pressure_out"]:
        assert nodes[nid].get(":organism/kind") == ":pressure"


def test_datom_emit_ground_and_transient():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    out = datom_emit.emit(nodes, edges, res, tx=7)
    assert ":add]" in out, "no ground :add datoms emitted"
    assert ":taxon/iucn" in out, "node attribute datoms missing"
    assert ":en/grasping-load" in out, "edge attribute datoms missing"
    # derived readouts must be flagged transient, NOT persisted as :add
    assert ":bond/is-transient true" in out
    assert ":bond/restoration-priority" in out
    # every :bond/* readout line must be op :derived (never persisted as :add)
    for line in out.splitlines():
        if line.startswith("[") and ":bond/" in line:
            assert ":derived]" in line, f"derived readout not flagged transient: {line}"
    # tx threads through
    assert " 7 :add]" in out


def test_determinism():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    a = datom_emit.emit(nodes, edges, res, tx=1)
    nodes2, edges2 = load(SEED)
    res2 = analyze(nodes2, edges2)
    b = datom_emit.emit(nodes2, edges2, res2, tx=1)
    assert a == b, "Datom emit is not deterministic"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
