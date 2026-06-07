#!/usr/bin/env python3
"""tsugite 継ぎ手 — analyzer + Datom-emit tests (ADR-2606073800). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze, VITALITY_WEIGHT  # noqa: E402
import datom_emit  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-peoples-graph.kotoba.edn"


def test_load_nontrivial():
    nodes, edges = load(SEED)
    assert len(nodes) >= 25, f"expected a real seed, got {len(nodes)} nodes"
    assert len(edges) >= 30, f"expected a real 縁 web, got {len(edges)} edges"
    kinds = {n.get(":organism/kind") for n in nodes.values()}
    assert {":people", ":language", ":pressure", ":haven"} <= kinds, f"missing core kinds: {kinds}"
    for e in edges:
        assert e[":en/from"] in nodes, f"dangling from: {e[':en/from']}"
        assert e[":en/to"] in nodes, f"dangling to: {e[':en/to']}"


def test_g1_aggregate_only_no_person_tracking():
    """G1: collective scale only — every :people is :aggregate, and no individual/locator attr."""
    nodes, edges = load(SEED)
    banned = (":person/id", ":geo/lat", ":geo/lon", ":location/current", ":biometric",
              ":individual", ":name/full", ":phone", ":passport")
    for nid, n in nodes.items():
        for b in banned:
            assert b not in n, f"G1 violation: person-tracking attr {b} on {nid}"
        if n.get(":organism/kind") == ":people":
            assert n.get(":people/scope") == ":aggregate", \
                f"G1 violation: people node {nid} is not :aggregate"


def test_edge_primary_continuity_integral():
    """N1: continuity-need MUST equal the independent integral of incident pressure 縁."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    pressure = {":displaces", ":erases"}
    expect = {}
    for e in edges:
        if e.get(":en/kind") in pressure:
            dst = e[":en/to"]
            w = VITALITY_WEIGHT.get(nodes[dst].get(":lang/vitality"), 0.6)
            expect[dst] = expect.get(dst, 0.0) + float(e[":en/peril-load"]) * w
    for nid, v in expect.items():
        assert abs(res["continuity"][nid] - v) < 1e-9, f"{nid}: {res['continuity'][nid]} != {v}"
    for n in nodes.values():
        assert not any(k.startswith(":bond/") or k == ":tsugite/score-of-people" for k in n)


def test_continuity_top_is_imperiled():
    """The top continuity-need bearer should be a high-pressure people or a CR/SE language —
    never a :safe/:vulnerable tongue with little pressure."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    top = max(res["continuity"].items(), key=lambda kv: kv[1])[0]
    vit = nodes[top].get(":lang/vitality")
    kind = nodes[top].get(":organism/kind")
    assert kind == ":people" or vit in (":critically-endangered", ":severely-endangered",
                                        ":definitely-endangered"), \
        f"top continuity node {top} (vitality {vit}) — lens is mis-weighted"


def test_protection_and_fragility_nonempty():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    assert res["protection"], "no protection buffer computed"
    assert res["fragility"], "no transmission fragility computed"
    # a revitalized language (Māori/Hawaiian) must carry a protection buffer
    assert any(k.startswith("ppl.lang.") for k in res["protection"])


def test_datom_emit_ground_and_transient():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    out = datom_emit.emit(nodes, edges, res, tx=7)
    assert ":add]" in out, "no ground :add datoms emitted"
    assert ":people/scope :aggregate" in out, "aggregate-scope marker missing from datoms (G1)"
    assert ":en/peril-load" in out, "edge attribute datoms missing"
    assert ":bond/is-transient true" in out
    assert ":bond/continuity-need" in out
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
