#!/usr/bin/env python3
"""subaru 昴 — link-budget + coverage + stewardship + datom-emit tests (ADR-2606162355)."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from link_budget import (load, link_budget, check_g1, BANNED_ATTRS,  # noqa: E402
                         COMMONS_ENTITLEMENT)
import coverage as cov_mod  # noqa: E402
import stewardship as stw_mod  # noqa: E402
import datom_emit  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-constellation.kotoba.edn"


def test_load_nontrivial():
    nodes, edges = load(SEED)
    assert len(nodes) >= 14, f"expected a real seed, got {len(nodes)} nodes"
    assert len(edges) >= 12, f"expected a real 縁 web, got {len(edges)} edges"
    kinds = {n.get(":organism/kind") for n in nodes.values()}
    assert {":constellation", ":bus", ":shell", ":link", ":service-area",
            ":entitlement", ":disposal-plan"} <= kinds, f"missing kinds: {kinds}"
    for e in edges:
        assert e[":en/from"] in nodes, f"dangling from: {e[':en/from']}"
        assert e[":en/to"] in nodes, f"dangling to: {e[':en/to']}"


def test_g1_no_surveillance_relay():
    """G1: connectivity commons — no DPI/user-location/targeting-relay attr; aggregate areas."""
    nodes, edges = load(SEED)
    assert check_g1(nodes) is True
    for n in nodes.values():
        for b in BANNED_ATTRS:
            assert b not in n, f"G1 violation: surveillance/targeting attr {b} present"
        if n.get(":organism/kind") == ":service-area":
            assert n.get(":area/region"), "service-area must be an aggregate region (G1)"
    # introducing a DPI attribute must be REFUSED
    bad = dict(nodes)
    bad["con.link.tap"] = {":organism/id": "con.link.tap", ":organism/kind": ":link",
                           ":link/dpi": True}
    try:
        check_g1(bad)
        assert False, "G1 must refuse a deep-packet-inspection link"
    except ValueError:
        pass
    # introducing a user-location attribute must be REFUSED
    bad2 = dict(nodes)
    bad2["con.u.1"] = {":organism/id": "con.u.1", ":organism/kind": ":service-area",
                       ":area/region": "x", ":user/location": "geo"}
    try:
        check_g1(bad2)
        assert False, "G1 must refuse a user-location attribute"
    except ValueError:
        pass


def test_g3_commons_entitlement_only():
    """G3: cash≡0 §1.16 in-kind — no subscription / ad-supported entitlement is representable."""
    nodes, edges = load(SEED)
    for n in nodes.values():
        if n.get(":organism/kind") == ":entitlement":
            assert n.get(":entitlement/kind") in COMMONS_ENTITLEMENT
    bad = dict(nodes)
    bad["con.ent.sub"] = {":organism/id": "con.ent.sub", ":organism/kind": ":entitlement",
                          ":entitlement/kind": ":subscription"}
    try:
        check_g1(bad)
        assert False, "G3 must refuse a subscription entitlement"
    except ValueError:
        pass


def test_link_budgets_close():
    """Every link budget must close (positive margin)."""
    nodes, edges = load(SEED)
    res = link_budget(nodes, edges)
    assert res["links"], "no links"
    assert res["all_closed"], f"a link does not close: min margin {res['min_margin_db']}"


def test_coverage_ss_reach():
    """§1.16 reach must count only unconnected/disaster priority areas."""
    nodes, edges = load(SEED)
    res = cov_mod.coverage(nodes, edges)
    assert res["n_priority"] >= 3, "expected several §1.16-priority service areas"
    # urban baseline (already connected) must NOT count toward §1.16 reach
    baseline = next(r for r in res["areas"] if r["area"] == "con.area.urban-baseline")
    assert baseline["ss_priority"] is False
    # reach equals the sum of coverage over priority areas (on-read integral, N1)
    expect = sum(r["coverage_pct"] for r in res["areas"] if r["ss_priority"])
    assert abs(res["ss_reach"] - expect) < 1e-9


def test_stewardship_g5():
    """G5: occupied shell carries a disposal plan + darksat; missing plan is refused."""
    nodes, edges = load(SEED)
    res = stw_mod.stewardship(nodes, edges)
    assert res["g5_pass"], f"G5 fail: {res}"
    assert res["darksat_all"], "darksat must be applied to all buses (G5)"
    # an occupied shell with no disposal plan must raise
    edges_no_disp = [e for e in edges if e.get(":en/kind") != ":disposes"]
    try:
        stw_mod.stewardship(nodes, edges_no_disp)
        assert False, "G5 must refuse an occupied shell with no disposal plan"
    except ValueError:
        pass


def test_datom_emit_ground_and_transient():
    nodes, edges = load(SEED)
    out = datom_emit.emit(nodes, edges, tx=7)
    assert ":add]" in out, "no ground :add datoms emitted"
    assert ":entitlement/kind" in out, "node attribute datoms missing"
    assert ":en/kind" in out, "edge attribute datoms missing"
    assert ":bond/is-transient true" in out
    assert ":bond/ss-reach" in out
    # no surveillance/targeting attr ever appears in the emitted log (G1)
    for bad in (":link/dpi", ":user/location", ":relay/targeting", ":subscription"):
        assert bad not in out, f"G1/G3 violation in datom log: {bad}"
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
