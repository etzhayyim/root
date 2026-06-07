#!/usr/bin/env python3
"""asobi 遊び — analyzer + Datom-emit tests (ADR-2606073200). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze, ACCESS_WEIGHT  # noqa: E402
import datom_emit  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-asobi-graph.kotoba.edn"


def test_load_nontrivial():
    nodes, edges = load(SEED)
    assert len(nodes) >= 25, f"expected a real seed, got {len(nodes)} nodes"
    assert len(edges) >= 30, f"expected a real 縁 web, got {len(edges)} edges"
    kinds = {n.get(":organism/kind") for n in nodes.values()}
    assert {":work", ":practice", ":enclosure"} <= kinds, f"missing core kinds: {kinds}"
    for e in edges:
        assert e[":en/from"] in nodes, f"dangling from: {e[':en/from']}"
        assert e[":en/to"] in nodes, f"dangling to: {e[':en/to']}"


def test_edge_primary_openness_integral():
    """N1: participation-openness MUST equal the independent integral of opening 縁."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    opening = {":open-access", ":teaches", ":participates", ":hosts", ":performs"}
    expect = {}
    for e in edges:
        if e.get(":en/kind") in opening:
            dst = e[":en/to"]
            w = ACCESS_WEIGHT.get(nodes[dst].get(":work/access"), 0.6)
            expect[dst] = expect.get(dst, 0.0) + float(e[":en/access-load"]) * w
    for nid, v in expect.items():
        assert abs(res["openness"][nid] - v) < 1e-9, f"{nid}: {res['openness'][nid]} != {v}"
    # no stored per-node score key on any node (edge-primary only)
    for n in nodes.values():
        assert not any(k.startswith(":bond/") or k == ":asobi/popularity-of-work" for k in n)


def test_openness_top_is_open_access():
    """The most-open node should be a public-domain / open-license work — never proprietary."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    top = max(res["openness"].items(), key=lambda kv: kv[1])[0]
    acc = nodes[top].get(":work/access")
    kind = nodes[top].get(":organism/kind")
    assert acc in (":public-domain", ":open-license", None) or kind in (":event", ":venue"), \
        f"top openness node {top} has access {acc} — lens is mis-weighted"


def test_enclosure_concentration_nonempty():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    assert res["enclosure_out"], "no 取-holder enclosure concentration computed"
    for nid in res["enclosure_out"]:
        assert nodes[nid].get(":organism/kind") == ":enclosure"


def test_datom_emit_ground_and_transient():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    out = datom_emit.emit(nodes, edges, res, tx=7)
    assert ":add]" in out, "no ground :add datoms emitted"
    assert ":work/access" in out, "node attribute datoms missing"
    assert ":en/access-load" in out, "edge attribute datoms missing"
    assert ":bond/is-transient true" in out
    assert ":bond/participation-openness" in out
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
