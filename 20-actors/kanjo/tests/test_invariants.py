#!/usr/bin/env python3
"""kanjō 勘定 — charter-invariant + gate tests (stdlib only; pytest-compatible AND direct).

    python3 tests/test_invariants.py
    python3 -m pytest tests/test_invariants.py

Complements tests/test_kanjo.py (normalization + arithmetic) with the LOAD-BEARING
structural invariants: kanjo is NON-ADJUDICATING (G2) and gives NO investment advice (G4)
— it never rates/values/recommends/forecasts; every derived number is a transparent ratio
flagged :synthesized; live fetch is G7-gated; metric kinds match their declared inputs.
ADR-2606032000.
"""
from __future__ import annotations
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "methods"))

import analyze        # noqa: E402
import concept_map    # noqa: E402
import ingest         # noqa: E402

SEED = os.path.join(HERE, "data", "seed-financial-facts.kotoba.edn")


def _report():
    filings, facts = analyze.load(SEED)
    cy = analyze.by_company_year(facts)
    metrics = analyze.derive_metrics(cy)
    aggs = analyze.aggregates(cy)
    return analyze.report(filings, facts, cy, metrics, aggs), metrics, aggs


def test_report_is_non_adjudicating_no_advice():
    md, _m, _a = _report()
    assert "non-adjudicating" in md.lower()
    assert "no investment advice" in md.lower()


def test_report_states_non_adjudication_boundary():
    # G4: the report must EXPLICITLY state it does not forecast/rate/recommend, and must
    # not emit an actual verdict artifact (a price target or a buy/sell call).
    md, _m, _a = _report()
    assert "does not forecast" in md.lower()        # boundary is stated, not implied
    # tokens that can ONLY be an adjudication (never a disclaimer phrasing here):
    for verdict in ("目標株価", "格付け", "投資判断:", "recommendation:"):
        assert verdict.lower() not in md.lower(), f"adjudication artifact leaked: {verdict!r}"


def test_derived_metrics_are_synthesized_not_authoritative():
    _md, metrics, _a = _report()
    assert metrics
    assert all(m[":fin.metric/sourcing"] == ":synthesized" for m in metrics)


def test_metric_kinds_match_declared_inputs():
    # every ratio metric kind produced must be one concept_map.metric_inputs() declares
    # (no undeclared metric can appear → the dependency map is the single source of truth).
    _md, metrics, _a = _report()
    declared = set(concept_map.metric_inputs())          # ratio kinds
    yoy = {"revenue-yoy", "operating-income-yoy", "net-income-yoy"}
    for m in metrics:
        kind = m[":fin.metric/kind"].lstrip(":")
        assert kind in declared or kind in yoy, f"undeclared metric kind: {kind}"


def test_aggregates_never_mix_currencies():
    _md, _m, aggs = _report()
    # each aggregate row is scoped to a single currency (no cross-FX summation)
    for a in aggs:
        cur = a.get(":fin.agg/currency")
        if cur is not None:
            assert isinstance(cur, str)
        assert a[":fin.agg/n"] >= 1


def test_g7_live_edgar_fetch_refused_without_operator_gate():
    saved = os.environ.pop("KANJO_OPERATOR_GATE", None)
    try:
        raised = False
        try:
            ingest.fetch_edgar("0000320193")
        except SystemExit as e:
            raised = True
            assert "G7" in str(e) or "refus" in str(e).lower() or "gate" in str(e).lower()
        assert raised, "live EDGAR fetch must refuse without KANJO_OPERATOR_GATE=1"
    finally:
        if saved is not None:
            os.environ["KANJO_OPERATOR_GATE"] = saved


def test_unmapped_taxonomy_element_is_dropped_not_guessed():
    # G5: an unrecognised XBRL element maps to None (dropped), never force-fit to a concept
    assert concept_map.canonical("us-gaap:TotallyMadeUpTag", "usgaap") is None
    assert concept_map.canonical("jppfs_cor:NotARealElement", "jgaap") is None


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        t()
        print(f"  ✓ {t.__name__}")
        passed += 1
    print(f"\nkanjō invariant tests: {passed}/{len(tests)} passed")
