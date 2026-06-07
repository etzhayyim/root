#!/usr/bin/env python3
"""hoshimori 星守 — analyzer + Datom-emit tests (ADR-2606073600). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze, REGIME_WEIGHT  # noqa: E402
import datom_emit  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-orbit-graph.kotoba.edn"


def test_load_nontrivial():
    nodes, edges = load(SEED)
    assert len(nodes) >= 25, f"expected a real seed, got {len(nodes)} nodes"
    assert len(edges) >= 30, f"expected a real 縁 web, got {len(edges)} edges"
    kinds = {n.get(":organism/kind") for n in nodes.values()}
    assert {":shell", ":operator", ":hazard", ":service"} <= kinds, f"missing core kinds: {kinds}"
    for e in edges:
        assert e[":en/from"] in nodes, f"dangling from: {e[':en/from']}"
        assert e[":en/to"] in nodes, f"dangling to: {e[':en/to']}"


def test_g1_no_precise_ephemeris():
    """G1: NO interception-grade state vector — no per-object lat/lon/alt/velocity attrs."""
    nodes, edges = load(SEED)
    banned = (":geo/lat", ":geo/lon", ":eph/state-vector", ":obj/altitude-km",
              ":obj/velocity", ":tle/line1", ":tle/line2")
    for n in nodes.values():
        for b in banned:
            assert b not in n, f"G1 violation: precise-ephemeris attr {b} present"


def test_edge_primary_congestion_integral():
    """N1: congestion MUST equal the independent integral of incident hazard/occupancy 縁."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    hazard = {":congests", ":imperils"}
    expect = {}
    for e in edges:
        if e.get(":en/kind") in hazard:
            dst = e[":en/to"]
            w = REGIME_WEIGHT.get(nodes[dst].get(":shell/regime"), 0.6)
            expect[dst] = expect.get(dst, 0.0) + float(e[":en/orbit-load"]) * w
    for nid, v in expect.items():
        assert abs(res["congestion"][nid] - v) < 1e-9, f"{nid}: {res['congestion'][nid]} != {v}"
    for n in nodes.values():
        assert not any(k.startswith(":bond/") or k == ":hoshimori/threat-of-object" for k in n)


def test_congestion_top_is_leo_low():
    """The most-congested regime should be LEO-low (megaconstellation + debris band)."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    top = max(res["congestion"].items(), key=lambda kv: kv[1])[0]
    assert nodes[top].get(":shell/regime") == ":leo-low", \
        f"top congestion node {top} is not LEO-low — lens is mis-weighted"


def test_stewardship_and_fragility_nonempty():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    assert res["stewardship"], "no stewardship buffer computed"
    assert res["fragility"], "no service-dependency fragility computed"
    # PNT-on-MEO must be a top fragility (GNSS critically depends on MEO)
    assert "orbit.svc.pnt" in res["fragility"]


def test_datom_emit_ground_and_transient():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    out = datom_emit.emit(nodes, edges, res, tx=7)
    assert ":add]" in out, "no ground :add datoms emitted"
    assert ":shell/regime" in out, "node attribute datoms missing"
    assert ":en/orbit-load" in out, "edge attribute datoms missing"
    assert ":bond/is-transient true" in out
    assert ":bond/congestion-concentration" in out
    for line in out.splitlines():
        if line.startswith("[") and ":bond/" in line:
            assert ":derived]" in line, f"derived readout not flagged transient: {line}"
    assert " 7 :add]" in out


def test_determinism():
    nodes, edges = load(SEED)
    a = datom_emit.emit(nodes, edges, analyze(nodes, edges), tx=1)
    nodes2, edges2 = load(SEED)
    b = datom_emit.emit(nodes2, edges2, analyze(nodes2, edges2), tx=1)
    assert a == b, "Datom emit is not deterministic"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
