#!/usr/bin/env python3
"""tanemaki 種蒔き — analyzer + Datom-emit + steward-boundary tests (ADR-2606122000). Pure stdlib.

Verifies the constitutional invariants empirically:
  - graph loads (nodes + 縁), no dangling 縁
  - G1 (the defining boundary): NO screen-conflicting org ever routes to :propose; there is no
    :fund route at all — funding is the members' vote, not a tanemaki output
  - G4: the disclosed rubric weights sum to 1.0 (a skewed rubric raises)
  - G5: thin evidence / undetermined screens route to :insufficient-evidence, never :propose
  - N1 edge-primary: dd-fit is the integral of incident :meets edges; no stored org score
  - G6: every seed org is synthetic (fictional)
  - Datom log emits ground datoms (incl. the public :screened DD trail) + flags deriveds transient
  - determinism
"""
import sys, pathlib
ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
from analyze import load, analyze, recommend_route, criteria, COVERAGE_FLOOR, ROUTES  # noqa: E402
import datom_emit  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-stewardship-graph.kotoba.edn"


def test_load_nontrivial():
    nodes, edges = load(SEED)
    assert len(nodes) >= 30 and len(edges) >= 60, f"{len(nodes)} nodes / {len(edges)} 縁"
    kinds = {n.get(":fs/kind") for n in nodes.values()}
    assert {":org", ":screen", ":criterion", ":source", ":instrument", ":milestone"} <= kinds
    for e in edges:
        assert e[":en/from"] in nodes and e[":en/to"] in nodes, f"dangling 縁: {e}"


def test_g1_no_conflicted_org_is_proposable():
    """THE defining boundary: a screen :conflicts ⇒ :excluded, never :propose."""
    nodes, edges = load(SEED)
    for nid, n in nodes.items():
        if n.get(":fs/kind") != ":org":
            continue
        rec = recommend_route(nid, nodes, edges)
        if rec["conflicts"]:
            assert rec["route"] == ":excluded", \
                f"G1 VIOLATION: {nid} has conflicts {rec['conflicts']} but routed {rec['route']}"


def test_g1_no_fund_route_exists():
    """tanemaki cannot emit a funding decision — :fund is not a route."""
    assert ":fund" not in ROUTES and set(ROUTES) == {":excluded", ":insufficient-evidence", ":propose"}
    nodes, edges = load(SEED)
    for nid, n in nodes.items():
        if n.get(":fs/kind") == ":org":
            assert recommend_route(nid, nodes, edges)["route"] in ROUTES


def test_g4_rubric_weights_sum_to_one():
    nodes, _ = load(SEED)
    crit = criteria(nodes)  # raises on a skewed rubric
    assert abs(sum(float(c.get(":criterion/weight", 0)) for c in crit.values()) - 1.0) < 1e-9
    # and a tampered rubric raises (rubric integrity is enforced, not assumed)
    tampered = dict(nodes)
    cid = next(iter(crit))
    tampered[cid] = dict(tampered[cid]); tampered[cid][":criterion/weight"] = 0.99
    try:
        criteria(tampered)
        raise SystemExit("FAIL: skewed rubric did not raise")
    except AssertionError:
        pass


def test_g5_thin_evidence_never_proposes():
    nodes, edges = load(SEED)
    for nid, n in nodes.items():
        if n.get(":fs/kind") != ":org":
            continue
        rec = recommend_route(nid, nodes, edges)
        if rec["route"] == ":propose":
            assert rec["evidence_coverage"] >= COVERAGE_FLOOR, \
                f"{nid} proposed below the evidence floor"
            assert not rec["undetermined"] and not rec["conflicts"]
            assert all(f == ":conforms" for f in rec["screen_findings"].values()), \
                f"{nid} proposed without clearing every screen"


def test_seed_exercises_all_three_routes():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    routes = {r["route"] for r in res["orgs"].values()}
    assert routes == {":excluded", ":insufficient-evidence", ":propose"}, routes


def test_edge_primary_no_stored_score():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    # dd-fit equals the hand-computed integral of incident :meets edges
    crit = criteria(nodes)
    for oid, r in res["orgs"].items():
        per = {}
        for e in edges:
            if e.get(":en/kind") == ":meets" and e.get(":en/from") == oid and e.get(":en/to") in crit:
                per[e[":en/to"]] = per.get(e[":en/to"], 0.0) + float(e[":en/weight"])
        expect = sum(float(crit[c][":criterion/weight"]) * min(1.0, w) for c, w in per.items())
        assert abs(r["dd_fit"] - round(expect, 6)) < 1e-9, oid
    # no stored per-org score on any node (edge-primary only)
    for n in nodes.values():
        assert not any(k.startswith(":bond/") for k in n)


def test_g6_every_seed_org_is_synthetic():
    nodes, _ = load(SEED)
    for nid, n in nodes.items():
        if n.get(":fs/kind") == ":org":
            assert n.get(":org/synthetic") is True, \
                f"G6 VIOLATION: {nid} is not marked synthetic — a real org in the seed is " \
                f"reputational adjudication (real-org DD is G7-gated)"


def test_screens_carry_disclosed_basis():
    nodes, _ = load(SEED)
    for nid, n in nodes.items():
        if n.get(":fs/kind") == ":screen":
            assert n.get(":screen/basis"), f"{nid} missing its disclosed charter anchor"
            assert n.get(":screen/code"), f"{nid} missing code"


def test_datom_emit_ground_and_transient():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    out = datom_emit.emit(nodes, edges, res, tx=7)
    assert " 7 :add]" in out and ":criterion/weight" in out
    assert ":en/finding" in out, "the public :screened DD trail must be in the Datom log"
    assert ":bond/is-transient true" in out
    for line in out.splitlines():
        if line.startswith("[") and ":bond/" in line:
            assert ":derived]" in line


def test_determinism():
    nodes, edges = load(SEED)
    a = datom_emit.emit(nodes, edges, analyze(nodes, edges), 1)
    nodes2, edges2 = load(SEED)
    b = datom_emit.emit(nodes2, edges2, analyze(nodes2, edges2), 1)
    assert a == b


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
