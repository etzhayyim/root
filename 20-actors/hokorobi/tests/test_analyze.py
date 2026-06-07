#!/usr/bin/env python3
"""hokorobi 綻び — analyzer + Datom-emit tests (ADR-2606073400). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze, SII_WEIGHT  # noqa: E402
import datom_emit  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-finrisk-graph.kotoba.edn"


def test_load_nontrivial():
    nodes, edges = load(SEED)
    assert len(nodes) >= 25, f"expected a real seed, got {len(nodes)} nodes"
    assert len(edges) >= 30, f"expected a real 縁 web, got {len(edges)} edges"
    kinds = {n.get(":organism/kind") for n in nodes.values()}
    assert {":institution", ":risk", ":bearer"} <= kinds, f"missing core kinds: {kinds}"
    for e in edges:
        assert e[":en/from"] in nodes, f"dangling from: {e[':en/from']}"
        assert e[":en/to"] in nodes, f"dangling to: {e[':en/to']}"


def test_edge_primary_systemic_integral():
    """N1: systemic-risk MUST equal the independent integral of incident risk 縁."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    risk = {":exposes", ":interconnects", ":underfunds", ":protection-gap"}
    expect = {}
    for e in edges:
        if e.get(":en/kind") in risk:
            dst = e[":en/to"]
            w = SII_WEIGHT.get(nodes[dst].get(":inst/sii"), 0.6)
            expect[dst] = expect.get(dst, 0.0) + float(e[":en/risk-load"]) * w
    for nid, v in expect.items():
        assert abs(res["systemic"][nid] - v) < 1e-9, f"{nid}: {res['systemic'][nid]} != {v}"
    # no stored per-node score key on any node (edge-primary only)
    for n in nodes.values():
        assert not any(k.startswith(":bond/") or k == ":hokorobi/solvency-of-bank" for k in n)


def test_systemic_top_is_significant():
    """The top systemic-risk node should be a G-SIB-tier institution or a public bearer —
    never a small/mid institution (the disclosed weight must dominate)."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    top = max(res["systemic"].items(), key=lambda kv: kv[1])[0]
    sii = nodes[top].get(":inst/sii")
    kind = nodes[top].get(":organism/kind")
    assert sii in (":g-sib", ":d-sib", ":large", None) or kind == ":bearer", \
        f"top systemic node {top} has SII {sii} — lens is mis-weighted"


def test_risk_source_concentration_nonempty():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    assert res["risk_out"], "no 取-holder risk-source concentration computed"
    # 取-holders are :risk sources OR institutions propagating contagion (:interconnects)
    for nid in res["risk_out"]:
        assert nodes[nid].get(":organism/kind") in (":risk", ":institution")
    # at least one pure :risk source is present (the primary 取-holder class)
    assert any(nodes[nid].get(":organism/kind") == ":risk" for nid in res["risk_out"])


def test_datom_emit_ground_and_transient():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    out = datom_emit.emit(nodes, edges, res, tx=7)
    assert ":add]" in out, "no ground :add datoms emitted"
    assert ":inst/sii" in out, "node attribute datoms missing"
    assert ":en/risk-load" in out, "edge attribute datoms missing"
    assert ":bond/is-transient true" in out
    assert ":bond/systemic-risk-concentration" in out
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
