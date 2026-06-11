#!/usr/bin/env python3
"""hinagata 雛形 — analyzer + Datom-emit tests (ADR-2606111954). Pure stdlib.

Verifies the constitutional invariants empirically:
  - graph loads (nodes + 縁), seed is non-trivial, no dangling 縁
  - edge-primary (N1): template groundedness is the integral of incident clause
    :cites-statute/:mandated-by × disclosed optionality weight — recomputed independently
    here and asserted equal
  - the top-groundedness template rests on a statute-mandated clause (sanity of the lens)
  - statute pull is non-empty and every puller is a :statute node
  - G1: no advice / party / matter fields anywhere (commons, not the practice of law)
  - every :cites-statute / :mandated-by edge points clause/template → a real :statute node
  - Datom log emits ground datoms [e a v tx op] and flags derived readouts transient
  - determinism (two runs byte-identical)
"""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze, OPTIONALITY_WEIGHT, CITE_KINDS  # noqa: E402
import datom_emit  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-legal-template-graph.kotoba.edn"


def test_load_nontrivial():
    nodes, edges = load(SEED)
    assert len(nodes) >= 50, f"expected a real seed, got {len(nodes)} nodes"
    assert len(edges) >= 90, f"expected a real 縁 web, got {len(edges)} edges"
    kinds = {n.get(":lt/kind") for n in nodes.values()}
    assert {":template", ":clause", ":statute", ":jurisdiction", ":concept"} <= kinds, \
        f"missing core kinds: {kinds}"
    for e in edges:
        assert e[":en/from"] in nodes, f"dangling from: {e[':en/from']}"
        assert e[":en/to"] in nodes, f"dangling to: {e[':en/to']}"


def test_edge_primary_integral():
    """N1: template groundedness MUST equal the independent integral of incident statute 縁."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    # rebuild clause→templates and per-clause optionality weight independently
    clause_templates = {}
    for e in edges:
        if e.get(":en/kind") == ":has-clause":
            clause_templates.setdefault(e[":en/to"], []).append(e[":en/from"])
    expect = {}
    for e in edges:
        if e.get(":en/kind") not in CITE_KINDS:
            continue
        load_ = float(e[":en/binding-load"])
        src = e[":en/from"]
        if nodes.get(src, {}).get(":lt/kind") == ":clause":
            w = OPTIONALITY_WEIGHT.get(nodes[src].get(":clause/optionality"), 0.6)
            for tmpl in clause_templates.get(src, []):
                expect[tmpl] = expect.get(tmpl, 0.0) + load_ * w
        elif nodes.get(src, {}).get(":lt/kind") == ":template":
            expect[src] = expect.get(src, 0.0) + load_
    for nid, v in expect.items():
        assert abs(res["grounded"][nid] - v) < 1e-9, f"{nid}: {res['grounded'][nid]} != {v}"
    # there is NO stored per-template score key on any node (edge-primary only)
    for n in nodes.values():
        assert not any(k.startswith(":bond/") or k == ":lt/score-of-template" for k in n)


def test_top_groundedness_is_statute_mandated():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    top = max(res["grounded"].items(), key=lambda kv: kv[1])[0]
    assert nodes[top].get(":lt/kind") == ":template", f"top {top} is not a template"
    # the top template must own at least one clause that is :mandated-by a statute
    clauses = {e[":en/to"] for e in edges
               if e.get(":en/kind") == ":has-clause" and e[":en/from"] == top}
    mandated = any(e.get(":en/kind") == ":mandated-by" and e[":en/from"] in clauses
                   for e in edges)
    assert mandated, f"top template {top} has no statute-mandated clause"


def test_statute_pull_nonempty_and_is_statute():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    assert res["statute_pull"], "no statute pull computed"
    for nid in res["statute_pull"]:
        assert nodes[nid].get(":lt/kind") == ":statute", f"puller {nid} is not a statute"


def test_g1_commons_not_advice():
    """G1: a COMMONS — no advice / party / matter / client fields anywhere."""
    nodes, edges = load(SEED)
    FORBIDDEN = {":advice/text", ":matter/id", ":client/id", ":party/name", ":opinion",
                 ":recommendation", ":case/id", ":retainer"}
    for n in nodes.values():
        assert not (set(n) & FORBIDDEN), f"practice-of-law field leaked: {set(n) & FORBIDDEN}"
    # every statute-citation edge binds a clause OR template to a real statute node
    for e in edges:
        if e.get(":en/kind") in CITE_KINDS:
            assert nodes[e[":en/to"]].get(":lt/kind") == ":statute", \
                f"cites-statute target is not a statute: {e[':en/to']}"
            assert nodes[e[":en/from"]].get(":lt/kind") in (":clause", ":template"), \
                f"cites-statute source is not a clause/template: {e[':en/from']}"


def test_every_statute_has_public_source():
    """N3/G5: a statute is a DISCLOSED public fact — it must carry a citation + official URL."""
    nodes, _ = load(SEED)
    for nid, n in nodes.items():
        if n.get(":lt/kind") == ":statute":
            assert n.get(":statute/citation"), f"{nid} missing :statute/citation"
            assert str(n.get(":statute/url", "")).startswith("http"), \
                f"{nid} missing public :statute/url"


def test_datom_emit_ground_and_transient():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    out = datom_emit.emit(nodes, edges, res, tx=7)
    assert ":add]" in out, "no ground :add datoms emitted"
    assert ":template/title" in out, "node attribute datoms missing"
    assert ":en/binding-load" in out, "edge attribute datoms missing"
    assert ":mandated-by" in out, "statute-binding edge datoms missing"
    # derived readouts must be flagged transient, NOT persisted as :add
    assert ":bond/is-transient true" in out
    assert ":bond/groundedness" in out
    for line in out.splitlines():
        if line.startswith("[") and ":bond/" in line:
            assert ":derived]" in line, f"derived readout not flagged transient: {line}"
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
