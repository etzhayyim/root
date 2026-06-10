#!/usr/bin/env python3
"""rasen 螺旋 — analyzer + Datom-emit tests (ADR-2606101000). Pure stdlib.

Verifies the constitutional invariants empirically:
  - graph loads (nodes + 縁), seed is non-trivial, no dangling 縁
  - edge-primary (N1): gene care-priority is the integral of incident variant-association
    (attributed via :located-in) + gene-linkage edges × disclosed clinsig — recomputed
    independently here and asserted equal
  - the top care-priority gene is a pathogenic-linked gene (sanity of the lens)
  - locus burden is non-empty and every burden-bearer is a :variant
  - G1: no individual-genotype fields; allele frequency is population-aggregate only
  - Datom log emits ground datoms [e a v tx op] and flags derived readouts transient
  - determinism (two runs byte-identical)
"""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze, CLINSIG_WEIGHT  # noqa: E402
import datom_emit  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-genome-graph.kotoba.edn"


def test_load_nontrivial():
    nodes, edges = load(SEED)
    assert len(nodes) >= 30, f"expected a real seed, got {len(nodes)} nodes"
    assert len(edges) >= 40, f"expected a real 縁 web, got {len(edges)} edges"
    kinds = {n.get(":genome/kind") for n in nodes.values()}
    assert {":gene", ":variant", ":phenotype"} <= kinds, f"missing core kinds: {kinds}"
    for e in edges:
        assert e[":en/from"] in nodes, f"dangling from: {e[':en/from']}"
        assert e[":en/to"] in nodes, f"dangling to: {e[':en/to']}"


def test_edge_primary_integral():
    """N1: care-priority MUST equal the independent integral of incident clinical 縁."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    variant_gene = {e[":en/from"]: e[":en/to"] for e in edges if e.get(":en/kind") == ":located-in"}
    expect = {}
    for e in edges:
        k = e.get(":en/kind")
        w = CLINSIG_WEIGHT.get(e.get(":en/clinsig"), 0.3)
        load_ = float(e[":en/grasping-load"])
        if k == ":associated-with":
            gene = variant_gene.get(e[":en/from"])
            if gene:
                expect[gene] = expect.get(gene, 0.0) + load_ * w
        elif k == ":linked-to":
            expect[e[":en/from"]] = expect.get(e[":en/from"], 0.0) + load_ * w
    for nid, v in expect.items():
        assert abs(res["care"][nid] - v) < 1e-9, f"{nid}: {res['care'][nid]} != {v}"
    # there is NO stored per-node score key on any node (edge-primary only)
    for n in nodes.values():
        assert not any(k.startswith(":bond/") or k == ":genome/score-of-gene" for k in n)


def test_care_top_is_pathogenic_gene():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    top = max(res["care"].items(), key=lambda kv: kv[1])[0]
    assert nodes[top].get(":genome/kind") == ":gene", f"top care node {top} is not a gene"
    # the top gene must carry at least one disclosed pathogenic linkage/association
    incident_clinsig = {e.get(":en/clinsig") for e in edges
                        if e.get(":en/from") == top or e.get(":en/to") == top}
    located = {e[":en/from"] for e in edges if e.get(":en/kind") == ":located-in" and e[":en/to"] == top}
    for e in edges:
        if e.get(":en/from") in located:
            incident_clinsig.add(e.get(":en/clinsig"))
    assert ":pathogenic" in incident_clinsig, f"top gene {top} has no pathogenic evidence"


def test_locus_burden_nonempty_and_variant():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    assert res["burden"], "no locus burden computed"
    for nid in res["burden"]:
        assert nodes[nid].get(":genome/kind") == ":variant", f"burden-bearer {nid} is not a variant"


def test_g1_no_individual_genotypes_and_aggregate_only():
    """G1: PUBLIC reference only — no individual-genotype fields; freq is population-aggregate."""
    nodes, edges = load(SEED)
    FORBIDDEN_NODE = {":sample/id", ":individual/id", ":patient/id", ":genotype/call",
                      ":sequence/raw", ":family/id"}
    for n in nodes.values():
        assert not (set(n) & FORBIDDEN_NODE), f"individual-level field leaked: {set(n) & FORBIDDEN_NODE}"
    # every :allele-frequency edge originates from a :population node (aggregate, never a person)
    for e in edges:
        if e.get(":en/kind") == ":allele-frequency":
            src = nodes[e[":en/from"]]
            assert src.get(":genome/kind") == ":population", \
                f"allele-frequency not sourced from a population aggregate: {e[':en/from']}"
            assert 0.0 <= float(e[":en/grasping-load"]) <= 1.0


def test_datom_emit_ground_and_transient():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    out = datom_emit.emit(nodes, edges, res, tx=7)
    assert ":add]" in out, "no ground :add datoms emitted"
    assert ":gene/symbol" in out, "node attribute datoms missing"
    assert ":en/grasping-load" in out, "edge attribute datoms missing"
    assert ":en/clinsig" in out, "clinsig edge datoms missing"
    # derived readouts must be flagged transient, NOT persisted as :add
    assert ":bond/is-transient true" in out
    assert ":bond/care-priority" in out
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
