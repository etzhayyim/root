#!/usr/bin/env python3
"""End-to-end tests for 扶持 (fuchi) analyze.py over the :representative seed.

Standalone-runnable: python3 test_analyze.py
"""
from __future__ import annotations

import sys

import analyze


def _rows():
    return {r["did"].split(":")[-1]: r for r in analyze.run()["rows"]}


def test_abel_auto_accepts():
    r = _rows()["abel"]
    assert r["route"] == ":auto" and r["outcome"] == "accepted"


def test_seth_goes_to_sbt_vote_and_passes():
    r = _rows()["seth"]
    assert r["route"].startswith(":sbt-vote") and r["outcome"] == "accepted"


def test_eve_escalates_to_council_lv7():
    r = _rows()["eve"]
    assert r["route"] == ":council-lv7" and r["outcome"] == "pending"


def test_cain_is_refused_by_rider():
    r = _rows()["cain"]
    assert r["route"] == ":refused" and r["outcome"] == "refused"


def test_noah_outreach_zero_share():
    r = _rows()["noah"]
    assert r["covenant"] == "outreach" and r["share"] == 0.0


def test_seth_in_kind_coverage_below_one():
    # seth carries an external liquidity residual → in-kind < 100%
    assert _rows()["seth"]["in_kind"] < 1.0


def test_every_derived_alloc_has_zero_cash():
    for d in analyze.run()["derived"]:
        assert d[":alloc/cash-usd-micros"] == 0
        assert d[":alloc/server-held-key"] is False


def test_refused_alloc_not_in_derived():
    dids = {d[":alloc/maintainer"].split(":")[-1] for d in analyze.run()["derived"]}
    assert "cain" not in dids


# ── R1 a/b/c end-to-end ─────────────────────────────────────────────────────
def test_seth_vote_finalized_after_timelock():
    # the route string carries the ✓ only when the 48h window has closed (R1b)
    assert "✓" in _rows()["seth"]["route"]


def test_provisioning_intents_emitted():
    res = analyze.run()
    assert res["intents"], "expected provisioning intents (R1a)"
    # every intent is a dry-run (published false, cash 0, keyless)
    for i in res["intents"]:
        assert i.published is False and i.cash_usd_micros == 0 and i.server_held_key is False


def test_seth_liquidity_intent_is_member_principal():
    res = analyze.run()
    liq = [i for i in res["intents"]
           if i.alloc_id.endswith("seth") and i.rail_kind == "liquidity-warifu"]
    assert liq and liq[0].member_principal is True


def test_toritate_ledger_is_cashless_no_liquidity():
    res = analyze.run()
    assert res["ledger"], "expected toritate ledger entries (R1c)"
    for e in res["ledger"]:
        assert e.cash_usd_micros == 0
    # liquidity is never booked as income → seth has no ledger entry > vocation/subsistence/care only
    cats = {e.category for e in res["ledger"]}
    assert cats <= {"subsistence-flow", "vocation-flow", "care-flow", "liberation-flow", "grant"}


def test_flow_graph_has_publicfund_source():
    res = analyze.run()
    assert any(f.flow_class == "publicfund-to-fuchi" for f in res["flows"])


# ── R1(d) coupling ──────────────────────────────────────────────────────────
def _coupling():
    return {c["earmark"].cohort_id: c for c in analyze.run()["coupling"]}


def test_sanae_cohort_funded_and_admissible():
    c = _coupling()["cohort-sanae-2026"]
    assert c["earmark"].funded is True and c["gate"]["admissible"] is True
    # 10% split exact
    assert c["earmark"].tithe_usd_micros == 6_000_000_000
    assert c["earmark"].earmark_usd_micros_yr == 54_000_000_000


def test_hataori_cohort_unfunded_refused():
    c = _coupling()["cohort-hataori-2026"]
    assert c["earmark"].funded is False and c["gate"]["admissible"] is False
    assert "G2" in c["gate"]["reason"]


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"test_analyze.py: {len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
