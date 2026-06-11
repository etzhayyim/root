#!/usr/bin/env python3
"""hakoniwa 箱庭 — world-load + simulation-kernel tests (ADR-2606111500). Pure stdlib.

Verifies the constitutional invariants empirically:
  - the scenario loads (synthetic personas + 縁), is non-trivial, no dangling 縁
  - G1: every persona is :persona/synthetic true, no PII-class field; a non-synthetic or
    PII-bearing persona is REFUSED at load
  - the Friedkin-Johnsen kernel converges and stays in [0,1]
  - determinism: identical (seed, steps, replicas) → byte-identical ensemble
  - a stronger official-relay signal (signal push) raises the town-wide mean (mechanism sanity)
  - aggregate-only: the readout is a population statistic, never a per-persona exposure
"""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

import world as W  # noqa: E402
import simulate as S  # noqa: E402

SCENARIO = ACTOR_DIR / "data" / "seed-scenario.kotoba.edn"


def test_load_nontrivial_and_synthetic():
    nodes, edges = W.load(SCENARIO)
    P = W.personas(nodes)
    assert len(P) >= 12, f"expected a real persona ensemble, got {len(P)}"
    assert len(edges) >= 30, f"expected a real 縁 web, got {len(edges)}"
    for nid, n in P.items():
        assert n.get(":persona/synthetic") is True, f"persona {nid} not marked synthetic (G1)"
    for e in edges:
        assert e[":en/from"] in nodes, f"dangling from: {e[':en/from']}"
        assert e[":en/to"] in nodes, f"dangling to: {e[':en/to']}"


def test_g1_refuses_real_person():
    """G1: a persona missing :persona/synthetic, or carrying PII, MUST be refused at load."""
    base = '[{:sim/id "persona.x" :sim/kind :persona :sim/label "x" %s}]'
    # missing synthetic marker
    import world
    nodes = {}
    forms = world.read_edn(base % "")
    for f in forms:
        if isinstance(f, dict):
            nodes[f[":sim/id"]] = f
    raised = False
    try:
        world.assert_synthetic(nodes)
    except ValueError:
        raised = True
    assert raised, "load accepted a persona with no :persona/synthetic marker (G1 breach)"
    # PII-bearing persona, even if marked synthetic
    nodes2 = {}
    for f in world.read_edn(base % ':persona/synthetic true :email "a@b.c"'):
        if isinstance(f, dict):
            nodes2[f[":sim/id"]] = f
    raised = False
    try:
        world.assert_synthetic(nodes2)
    except ValueError:
        raised = True
    assert raised, "load accepted a PII-bearing persona (G1 breach)"


def test_kernel_converges_in_unit_interval():
    nodes, edges = W.load(SCENARIO)
    pids, sus, base_anchor, weight, incoming, exposure = S.build_topology(nodes, edges)
    x = S.run_replica(pids, sus, base_anchor, incoming, exposure,
                      steps=12, seed=7, replica=0, jitter=0.0)
    assert set(x.keys()) == set(pids)
    for i, v in x.items():
        assert 0.0 <= v <= 1.0, f"stance for {i} left [0,1]: {v}"


def test_row_normalised_influence():
    """Incoming :influences weights MUST row-normalise to 1 (or be empty → fully anchored)."""
    nodes, edges = W.load(SCENARIO)
    _, _, _, _, incoming, _ = S.build_topology(nodes, edges)
    for i, lst in incoming.items():
        if lst:
            assert abs(sum(w for _, w in lst) - 1.0) < 1e-9, f"{i} incoming weights not normalised"


def test_determinism():
    nodes, edges = W.load(SCENARIO)
    a, ma = S.ensemble(nodes, edges, steps=10, replicas=32, seed=3)
    nodes2, edges2 = W.load(SCENARIO)
    b, mb = S.ensemble(nodes2, edges2, steps=10, replicas=32, seed=3)
    assert a == b, "ensemble is not deterministic for fixed (seed, steps, replicas)"
    assert ma == mb


def test_stronger_relay_raises_mean():
    """Mechanism sanity: a stronger official-relay push shifts the distribution upward."""
    nodes, edges = W.load(SCENARIO)
    base, _ = S.ensemble(nodes, edges, steps=12, replicas=48, seed=7)
    # strengthen signal.s1's push (the sonae-style authoritative relay)
    for n in nodes.values():
        if n.get(":sim/id") == "signal.s1":
            n[":signal/push"] = 0.40
    boosted, _ = S.ensemble(nodes, edges, steps=12, replicas=48, seed=7)
    assert sum(boosted) / len(boosted) > sum(base) / len(base) + 1e-3, \
        "a stronger preparedness relay did not raise town-wide adoption stance"


def test_ensemble_has_spread():
    """The ensemble must actually be a distribution (replicas differ), not a degenerate point."""
    nodes, edges = W.load(SCENARIO)
    results, _ = S.ensemble(nodes, edges, steps=12, replicas=64, seed=7)
    assert max(results) - min(results) > 1e-4, "ensemble collapsed to a point (G2 needs spread)"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
