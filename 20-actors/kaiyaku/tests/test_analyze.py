#!/usr/bin/env python3
"""kaiyaku 解約 — analyzer + Datom-emit tests (ADR-2606112200). Pure stdlib.

Verifies the constitutional invariants empirically:
  - ledger loads (nodes + 縁), seed is non-trivial and synthetic/representative only
  - N1: every member-tie points at a SERVICE, never a person
  - G2 edge-primary: burden is recomputed independently per tie and asserted equal;
    there is no per-member aggregate score in the readout
  - disclosed thresholds: unused-paid → :sever, dormant cost-free account → :sever,
    used tie → :keep
  - cascade-guard: a sever-able service with dependents downgrades to :review-cascade
  - Datom log emits ground datoms and flags derived readouts transient
  - determinism (two runs byte-identical)
"""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze, _burden  # noqa: E402
import datom_emit  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-en-ledger.kotoba.edn"


def test_load_nontrivial():
    nodes, edges = load(SEED)
    assert len(nodes) >= 9, f"expected a real seed, got {len(nodes)} nodes"
    assert len(edges) >= 10, f"expected a real 縁 ledger, got {len(edges)} edges"
    for e in edges:
        assert e[":en/from"] in nodes, f"dangling from: {e[':en/from']}"
        assert e[":en/to"] in nodes, f"dangling to: {e[':en/to']}"


def test_synthetic_only_no_pii():
    """G1: member-side facts are :synthetic; services :representative. No real PII."""
    nodes, edges = load(SEED)
    for n in nodes.values():
        if ":member/id" in n:
            assert n.get(":member/sourcing") == ":synthetic"
        else:
            assert n.get(":svc/sourcing") in (":representative", ":authoritative")
    for e in edges:
        assert e.get(":en/sourcing") == ":synthetic"


def test_ties_are_services_never_persons():
    """N1: 縁切り here is member↔SERVICE only — a tie target is always a :svc/* node."""
    nodes, edges = load(SEED)
    for e in edges:
        if e[":en/from"].startswith("member:"):
            assert ":svc/id" in nodes[e[":en/to"]], f"member tie to non-service: {e[':en/to']}"


def test_edge_primary_burden():
    """G2: burden = cost × unused-fraction + dormancy, recomputed independently."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    by_svc = {t["svc"]: t for t in res["ties"]}
    for e in edges:
        if e.get(":en/kind") not in (":subscribes", ":holds-account", ":recurring-charge"):
            continue
        cost = float(e.get(":en/monthly-cost-jpy", 0) or 0)
        usage = float(e.get(":en/usage-score", 0) or 0)
        last = min(float(e.get(":en/last-used-days", 0) or 0), 1000.0)
        expect = round(cost * (1 - min(usage, 100) / 100) + last / 1000.0, 4)
        assert abs(by_svc[e[":en/to"]]["burden"] - expect) < 1e-9
        assert by_svc[e[":en/to"]]["burden"] == _burden(e)
    # 反個人主義: the readout carries NO per-member score key
    assert not any(k.startswith("member_score") for k in res), res.keys()


def test_disclosed_thresholds():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    by_svc = {t["svc"]: t for t in res["ties"]}
    # unused paid video sub (usage 4, ¥1980) — :sever, BUT it depends on bank card?
    # no: video-a DEPENDS ON bank-i (video-a is the source), so video-a itself has no
    # dependents → plain :sever
    assert by_svc["svc:video-a"]["recommendation"] == ":sever"
    # gym: usage 10 < 20, cost 8800 > 500 → :sever (no dependents)
    assert by_svc["svc:gym-b"]["recommendation"] == ":sever"
    # well-used SaaS → :keep
    assert by_svc["svc:saas-c"]["recommendation"] == ":keep"
    # news usage 35 < 50 → :review
    assert by_svc["svc:news-d"]["recommendation"] == ":review"
    # dormant cost-free SNS account 420d → :sever (退会候補)
    assert by_svc["svc:sns-e"]["recommendation"] == ":sever"
    # unknown recurring card charge, usage 0, ¥550 → :sever
    assert by_svc["svc:merchant-g"]["recommendation"] == ":sever"
    # active bank account → :keep
    assert by_svc["svc:bank-i"]["recommendation"] == ":keep"


def test_cascade_guard():
    """依存 detection: legacy email F is dormant BUT two services SSO through it —
    a :sever must downgrade to :review-cascade, never auto-sever."""
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    by_svc = {t["svc"]: t for t in res["ties"]}
    f = by_svc["svc:mail-f"]
    assert f["dependents"] == ["svc:cloud-h", "svc:sns-e"]
    assert f["recommendation"] == ":review-cascade"


def test_recoverable_aggregate():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    sever_sum = sum(t["monthly_cost_jpy"] for t in res["ties"]
                    if t["recommendation"] == ":sever")
    assert res["recoverable_monthly_jpy"] == round(sever_sum, 2)
    assert res["recoverable_monthly_jpy"] > 0


def test_datoms_ground_and_transient():
    nodes, edges = load(SEED)
    res = analyze(nodes, edges)
    text = datom_emit.emit(nodes, edges, res, tx=7)
    assert ":svc/label" in text and ":en/monthly-cost-jpy" in text
    assert ":bond/is-transient true" in text, "derived readouts must be flagged transient (G2)"
    assert ":enkiri/recommendation" in text
    # every derived line sits under a transient-flagged entity; no plan executes here
    assert "execute" not in text


def test_determinism():
    nodes, edges = load(SEED)
    a = datom_emit.emit(nodes, edges, analyze(nodes, edges), tx=1)
    b = datom_emit.emit(nodes, edges, analyze(nodes, edges), tx=1)
    assert a == b


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok {fn.__name__}")
    print(f"{len(fns)} passed")
