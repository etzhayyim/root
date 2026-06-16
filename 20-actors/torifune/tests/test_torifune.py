#!/usr/bin/env python3
"""torifune 鳥船 — sim + carbon + disposal + datom-emit tests (ADR-2606162355). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from ascent_sim import (load, simulate, check_g1, CIVILIAN_TRAJ, CIVILIAN_PAYLOAD,  # noqa: E402
                        BANNED_ATTRS, REGIME_DV)
import carbon_balance  # noqa: E402
import disposal_plan  # noqa: E402
import datom_emit  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-ama-vehicle.kotoba.edn"


def test_load_nontrivial():
    nodes, edges = load(SEED)
    assert len(nodes) >= 18, f"expected a real seed, got {len(nodes)} nodes"
    assert len(edges) >= 12, f"expected a real 縁 web, got {len(edges)} edges"
    kinds = {n.get(":organism/kind") for n in nodes.values()}
    assert {":vehicle", ":stage", ":engine", ":propellant", ":mission",
            ":payload", ":trajectory", ":disposal-plan"} <= kinds, f"missing kinds: {kinds}"
    for e in edges:
        assert e[":en/from"] in nodes, f"dangling from: {e[':en/from']}"
        assert e[":en/to"] in nodes, f"dangling to: {e[':en/to']}"


def test_g1_no_strike_profile():
    """G1: civilian launch ONLY — no strike trajectory, no munition payload, no weapon attr."""
    nodes, edges = load(SEED)
    assert check_g1(nodes) is True
    for n in nodes.values():
        for b in BANNED_ATTRS:
            assert b not in n, f"G1 violation: weapon attr {b} present"
        if n.get(":organism/kind") == ":trajectory":
            assert n.get(":traj/class") in CIVILIAN_TRAJ
        if n.get(":organism/kind") == ":payload":
            assert n.get(":payload/class") in CIVILIAN_PAYLOAD
    # a strike trajectory must be REFUSED, not silently accepted
    bad = dict(nodes)
    bad["lv.traj.strike"] = {":organism/id": "lv.traj.strike",
                             ":organism/kind": ":trajectory", ":traj/class": ":depressed-strike"}
    try:
        check_g1(bad)
        assert False, "G1 must refuse a depressed-strike trajectory"
    except ValueError:
        pass
    # a munition payload must be REFUSED
    bad2 = dict(nodes)
    bad2["lv.payload.muni"] = {":organism/id": "lv.payload.muni",
                               ":organism/kind": ":payload", ":payload/class": ":munition"}
    try:
        check_g1(bad2)
        assert False, "G1 must refuse a munition payload"
    except ValueError:
        pass


def test_ascent_reaches_orbit():
    """Δv margin to the target regime must be positive (the Ama class can reach orbit)."""
    nodes, edges = load(SEED)
    res = simulate(nodes, edges)
    assert res["target_regime"] == ":leo-low"
    assert res["dv_margin_ms"] > 0, f"insufficient Δv: margin {res['dv_margin_ms']}"
    # total Δv must equal the sum of per-stage Δv (edge-primary / on-read integral, N1)
    assert abs(res["total_dv_ms"] - sum(s["dv_ms"] for s in res["per_stage"])) < 1e-6
    # required Δv is the disclosed regime constant (non-adjudicating, G8)
    assert res["required_dv_ms"] == REGIME_DV[":leo-low"]


def test_carbon_g2_zero_net():
    """G2: the Ama vehicle is fueled only by net≤0 propellant ⇒ net balance ≤ 0, no disfavored."""
    nodes, edges = load(SEED)
    res = carbon_balance.balance(nodes, edges)
    assert res["g2_pass"], f"G2 fail: net {res['net_kgco2e']} / disfavored {res['used_disfavored']}"
    assert res["net_kgco2e"] <= 0.0
    assert not res["used_disfavored"], "no disfavored propellant should be fueled into Ama"


def test_disposal_g5_required():
    """G5: every mission carries a disposal plan; a mission without one is refused."""
    nodes, edges = load(SEED)
    res = disposal_plan.plan(nodes, edges)
    assert res["missions"], "no mission found"
    for m in res["missions"]:
        assert m["plans"], f"mission {m['mission']} has no disposal plan"
    # a mission with no :disposes edge must raise (G5)
    edges_no_disp = [e for e in edges if e.get(":en/kind") != ":disposes"]
    try:
        disposal_plan.plan(nodes, edges_no_disp)
        assert False, "G5 must refuse a mission with no disposal plan"
    except ValueError:
        pass


def test_datom_emit_ground_and_transient():
    nodes, edges = load(SEED)
    out = datom_emit.emit(nodes, edges, tx=7)
    assert ":add]" in out, "no ground :add datoms emitted"
    assert ":vehicle/class" in out, "node attribute datoms missing"
    assert ":en/kind" in out, "edge attribute datoms missing"
    assert ":bond/is-transient true" in out
    assert ":bond/dv-margin-ms" in out
    # no strike/munition attr ever appears in the emitted log (G1)
    for bad in (":traj/impact-point", ":payload/warhead", ":depressed-strike", ":munition"):
        assert bad not in out, f"G1 violation in datom log: {bad}"
    for line in out.splitlines():
        if line.startswith("[") and ":bond/" in line:
            assert ":derived]" in line, f"derived not flagged transient: {line}"
    assert " 7 :add]" in out


def test_determinism():
    nodes, edges = load(SEED)
    a = datom_emit.emit(nodes, edges, tx=1)
    nodes2, edges2 = load(SEED)
    b = datom_emit.emit(nodes2, edges2, tx=1)
    assert a == b, "Datom emit is not deterministic"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
