#!/usr/bin/env python3
"""kadode 門出 — analyzer + Datom-emit + UPL-boundary tests (ADR-2606112238). Pure stdlib.

Verifies the constitutional invariants empirically:
  - graph loads (nodes + 縁), no dangling 縁
  - G1 (the defining boundary): EVERY negotiation-needing scenario resolves to a NEGOTIATING
    route (union/lawyer) — NEVER to 使者/self. The 使者/self routes are never marked can-negotiate.
  - every scenario reaches a recommended lawful route
  - every employer-risk pattern has at least one countering legal ground
  - edge-primary: ground-support is the integral of incident :supported-by edges
  - Datom log emits ground datoms + flags derived readouts transient
  - determinism
"""
import sys, pathlib
ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
from analyze import load, analyze, recommend_route, NEGOTIATING_ACTORS  # noqa: E402
import datom_emit  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-resignation-graph.kotoba.edn"


def test_load_nontrivial():
    nodes, edges = load(SEED)
    assert len(nodes) >= 30 and len(edges) >= 40, f"{len(nodes)} nodes / {len(edges)} 縁"
    kinds = {n.get(":lx/kind") for n in nodes.values()}
    assert {":scenario", ":ground", ":document", ":route", ":risk"} <= kinds
    for e in edges:
        assert e[":en/from"] in nodes and e[":en/to"] in nodes, f"dangling 縁: {e}"


def test_g1_upl_invariant_holds_for_every_scenario():
    """THE defining boundary: negotiation ⇒ union/lawyer, never a 使者/self relay."""
    nodes, edges = load(SEED)
    for nid, n in nodes.items():
        if n.get(":lx/kind") != ":scenario":
            continue
        rec = recommend_route(nid, nodes, edges)
        if rec["needs_negotiation"]:
            assert rec["route_actor"] in NEGOTIATING_ACTORS, \
                f"G1 VIOLATION: {nid} needs negotiation but routed to {rec['route_actor']}"
            assert rec["can_negotiate"] is True


def test_messenger_and_self_routes_cannot_negotiate():
    nodes, _ = load(SEED)
    for n in nodes.values():
        if n.get(":lx/kind") == ":route" and n.get(":route/actor") in (":worker-self", ":kadode-messenger"):
            assert n.get(":route/can-negotiate") is False, \
                f"{n[':lx/id']} (使者/self) must not be able to negotiate (G1)"


def test_every_scenario_routes():
    nodes, edges = load(SEED)
    for nid, n in nodes.items():
        if n.get(":lx/kind") == ":scenario":
            assert recommend_route(nid, nodes, edges)["route"], f"{nid} has no route"


def test_every_risk_has_a_countering_ground():
    nodes, edges = load(SEED)
    countered = {e[":en/to"] for e in edges if e.get(":en/kind") == ":counters"}
    for nid, n in nodes.items():
        if n.get(":lx/kind") == ":risk":
            assert nid in countered, f"employer risk {nid} has no countering legal ground"


def test_edge_primary_ground_support():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    expect = {}
    for e in edges:
        if e.get(":en/kind") == ":supported-by":
            expect[e[":en/from"]] = expect.get(e[":en/from"], 0.0) + float(e[":en/weight"])
    for sid, v in expect.items():
        assert abs(res["ground_support"][sid] - v) < 1e-9
    # no stored per-scenario score on any node (edge-primary only)
    for n in nodes.values():
        assert not any(k.startswith(":bond/") for k in n)


def test_grounds_have_public_source():
    nodes, _ = load(SEED)
    for nid, n in nodes.items():
        if n.get(":lx/kind") == ":ground":
            assert n.get(":ground/citation"), f"{nid} missing citation"
            assert str(n.get(":ground/url", "")).startswith("http"), f"{nid} missing public url"


def test_datom_emit_ground_and_transient():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    out = datom_emit.emit(nodes, edges, res, tx=7)
    assert " 7 :add]" in out and ":route/can-negotiate" in out
    assert ":upl-bound" in out, "UPL-boundary edges must be in the Datom log"
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
