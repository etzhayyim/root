#!/usr/bin/env python3
"""shiori 栞 — analyzer + Datom-emit tests (ADR-2606082100). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze, SEVERITY_WEIGHT  # noqa: E402
import datom_emit  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-wellbecoming-graph.kotoba.edn"


def test_load_nontrivial():
    nodes, edges = load(SEED)
    assert len(nodes) >= 30, f"expected a real seed, got {len(nodes)} nodes"
    assert len(edges) >= 30, f"expected a real 縁 web, got {len(edges)} edges"
    kinds = {n.get(":organism/kind") for n in nodes.values()}
    assert {":cohort", ":detractor", ":driver", ":mitigator"} <= kinds, f"missing core kinds: {kinds}"
    for e in edges:
        assert e[":en/from"] in nodes, f"dangling from: {e[':en/from']}"
        assert e[":en/to"] in nodes, f"dangling to: {e[':en/to']}"


def test_g1_aggregate_only_no_person_scoring():
    """G1: cohort scale only — every :cohort is :aggregate, and no individual/affect/locator attr."""
    nodes, edges = load(SEED)
    banned = (":person/id", ":affect/score", ":sentiment", ":happiness-score", ":mood",
              ":biometric", ":individual", ":name/full", ":geo/lat", ":geo/lon", ":profile")
    for nid, n in nodes.items():
        for b in banned:
            assert b not in n, f"G1 violation: person-scoring attr {b} on {nid}"
        if n.get(":organism/kind") == ":cohort":
            assert n.get(":cohort/scope") == ":aggregate", \
                f"G1 violation: cohort node {nid} is not :aggregate"


def test_g1_anti_addictive_mitigators_are_not_engagement():
    """G1/§1.13: a mitigator (the relief shiori routes toward) may never be an engagement-
    maximising / addictive technique. Those kinds belong ONLY to the detractor/driver side."""
    nodes, _ = load(SEED)
    addictive = {":addictive-design", ":engagement-maximizing-design", ":algorithmic-feed"}
    for nid, n in nodes.items():
        if n.get(":organism/kind") == ":mitigator":
            assert n.get(":mitigator/kind") not in addictive, \
                f"anti-addictive violation: {nid} routes toward an engagement technique"


def test_edge_primary_burden_integral():
    """N1: wellbecoming-burden MUST equal the independent integral of incident :diminishes 縁."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    expect = {}
    for e in edges:
        if e.get(":en/kind") == ":diminishes":
            dst = e[":en/to"]
            sev = nodes[e[":en/from"]].get(":detractor/severity")
            w = SEVERITY_WEIGHT.get(sev, 0.5)
            expect[dst] = expect.get(dst, 0.0) + float(e[":en/load"]) * w
    for nid, v in expect.items():
        assert abs(res["burden"][nid] - v) < 1e-9, f"{nid}: {res['burden'][nid]} != {v}"
    # G2: no stored per-cohort score on any ground node
    for n in nodes.values():
        assert not any(k.startswith(":bond/") or k == ":shiori/score-of-cohort" for k in n)


def test_relief_gap_top_is_underserved_and_imperiled():
    """The top relief-gap cohort must bear at least one critical/severe detractor (the lens is
    not mis-weighted toward a low-severity, well-buffered cohort), and gap = burden − relief."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    top = max(res["gap"].items(), key=lambda kv: kv[1])[0]
    assert abs(res["gap"][top] - (res["burden"][top] - res["relief"].get(top, 0.0))) < 1e-9
    incident_sev = {
        nodes[e[":en/from"]].get(":detractor/severity")
        for e in edges if e.get(":en/kind") == ":diminishes" and e[":en/to"] == top
    }
    assert incident_sev & {":critical", ":severe"}, \
        f"top relief-gap cohort {top} bears no critical/severe detractor — lens mis-weighted"


def test_imposed_driver_is_structural_pattern_not_entity():
    """The top detraction 取-holder among DRIVERS must be a structural pattern (G1 = map-not-target):
    it carries a :driver/kind and no entity-identifying attribute."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    drivers = {nid: v for nid, v in res["imposed"].items()
               if nodes.get(nid, {}).get(":organism/kind") == ":driver"}
    assert drivers, "no driver imposed-load computed"
    top_drv = max(drivers.items(), key=lambda kv: kv[1])[0]
    assert nodes[top_drv].get(":driver/kind"), f"{top_drv} lacks a structural :driver/kind"
    for forbidden in (":org/id", ":company", ":person/id", ":ticker"):
        assert forbidden not in nodes[top_drv], f"driver {top_drv} names a real entity (G1)"


def test_unrouted_detractors_are_design_gaps():
    """Detractors that burden a cohort but have no :routes-to edge are surfaced as the
    intervention-design gap (routing coverage = 0)."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    for nid in res["unrouted_detractors"]:
        assert nodes[nid].get(":organism/kind") == ":detractor"
        assert res["route_coverage"].get(nid, 0.0) == 0.0
        assert res["imposed"].get(nid, 0.0) > 0.0
    # the seed deliberately leaves information-pollution / discrimination / sleep-deprivation unrouted
    assert "wb.detr.discrimination" in res["unrouted_detractors"]


def test_datom_emit_ground_and_transient():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    out = datom_emit.emit(nodes, edges, res, tx=7)
    assert ":add]" in out, "no ground :add datoms emitted"
    assert ":cohort/scope :aggregate" in out, "aggregate-scope marker missing from datoms (G1)"
    assert ":en/load" in out, "edge attribute datoms missing"
    assert ":bond/is-transient true" in out
    assert ":bond/relief-gap" in out
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
