#!/usr/bin/env python3
"""kanjō 勘定 — unit tests (stdlib only; pytest-compatible AND runnable directly).

Run either way:
    python3 tests/test_kanjo.py          # plain-asserts harness (no pytest needed)
    python3 -m pytest tests/test_kanjo.py # standard pytest

No third-party imports (the repo root pulls langsmith via plugin autoload, which is
env-fragile; these tests stay dependency-free so they run anywhere). ADR-2606032000.
"""
from __future__ import annotations
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "methods"))

import kanjo_edn          # noqa: E402
import concept_map        # noqa: E402
import analyze            # noqa: E402
import ingest             # noqa: E402

SEED = os.path.join(HERE, "data", "seed-financial-facts.kotoba.edn")


# ── concept_map: GAAP normalization ──────────────────────────────────────────
def test_cross_gaap_revenue_normalizes_to_one_concept():
    """JP-GAAP, US-GAAP and IFRS revenue elements all land on :revenue."""
    assert concept_map.canonical("jppfs_cor:NetSales", "jgaap") == "revenue"
    assert concept_map.canonical("us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax", "usgaap") == "revenue"
    assert concept_map.canonical("ifrs-full:Revenue", "ifrs") == "revenue"


def test_ordinary_income_is_jgaap_only():
    """経常利益 maps under JGAAP but has NO US-GAAP / IFRS twin (honest non-comparability)."""
    assert concept_map.canonical("jppfs_cor:OrdinaryIncome", "jgaap") == "ordinary-income"
    assert concept_map.canonical("OrdinaryIncome", "usgaap") is None
    assert concept_map.canonical("OrdinaryIncome", "ifrs") is None
    note = concept_map.CONCEPTS["ordinary-income"][5]
    assert "JGAAP-only" in note


def test_unmapped_element_returns_none():
    assert concept_map.canonical("us-gaap:SomeUnknownTag", "usgaap") is None


# ── analyze: derived ratios + YoY + aggregates ───────────────────────────────
def test_derived_ratios_match_disclosed_arithmetic():
    """operating-margin / equity-ratio are exact ratios of disclosed facts."""
    _filings, facts = analyze.load(SEED)
    cy = analyze.by_company_year(facts)
    metrics = {(m[":fin.metric/company"], m[":fin.metric/fiscal-year"], m[":fin.metric/kind"]): m[":fin.metric/value"]
               for m in analyze.derive_metrics(cy)}
    # Apple FY2024: operating-income 123216 / revenue 391035 = 0.3151
    assert abs(metrics[("org.corp.us.apple", 2024, ":operating-margin")] - 123216 / 391035) < 1e-3
    # Apple equity-ratio: total-equity 56950 / total-assets 364980
    assert abs(metrics[("org.corp.us.apple", 2024, ":equity-ratio")] - 56950 / 364980) < 1e-3


def test_yoy_only_when_two_years_present():
    """Toyota has FY2023+FY2024 → YoY exists; single-year filers get none."""
    _filings, facts = analyze.load(SEED)
    cy = analyze.by_company_year(facts)
    metrics = analyze.derive_metrics(cy)
    toyota_yoy = [m for m in metrics if m[":fin.metric/company"] == "org.corp.jp.toyota"
                  and m[":fin.metric/kind"] == ":revenue-yoy"]
    apple_yoy = [m for m in metrics if m[":fin.metric/company"] == "org.corp.us.apple"
                 and m[":fin.metric/kind"] == ":revenue-yoy"]
    assert len(toyota_yoy) == 1                      # 45095000 vs 37154000
    assert abs(toyota_yoy[0][":fin.metric/value"] - (45095000 - 37154000) / 37154000) < 1e-3
    assert apple_yoy == []                            # only FY2024 in seed


def test_aggregates_never_cross_currency():
    """Sector aggregates are keyed by (sector, currency) — JPY and USD never summed together."""
    _filings, facts = analyze.load(SEED)
    cy = analyze.by_company_year(facts)
    aggs = analyze.aggregates(cy)
    # every aggregate id encodes a single currency; no agg mixes jpy+usd
    currencies = {a[":fin.agg/id"].split(".")[-3] for a in aggs}
    assert currencies <= {"jpy", "usd", "eur", "gbp"}
    for a in aggs:
        assert a[":fin.agg/n"] >= 1


def test_metrics_are_synthesized_not_facts():
    """G5: every derived metric is :synthesized (never a disclosed fact)."""
    _filings, facts = analyze.load(SEED)
    cy = analyze.by_company_year(facts)
    for m in analyze.derive_metrics(cy):
        assert m[":fin.metric/sourcing"] == ":synthesized"


# ── ingest: primary-disclosure parsers ───────────────────────────────────────
def test_edgar_parser_scales_to_millions_and_filters_to_annual():
    edgar = {"cik": 320193, "facts": {"us-gaap": {
        "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": [
            {"end": "2024-09-28", "val": 391035000000, "fy": 2024, "fp": "FY", "form": "10-K", "accn": "X", "filed": "2024-11-01"}]}},
        "NetIncomeLoss": {"units": {"USD": [
            {"end": "2024-09-28", "val": 93736000000, "fy": 2024, "fp": "FY", "form": "10-K", "accn": "X", "filed": "2024-11-01"},
            {"end": "2024-06-29", "val": 1, "fy": 2024, "fp": "Q3", "form": "10-Q", "accn": "Y", "filed": "2024-08-01"}]}}}}}
    _fl, fa = ingest.parse_edgar_companyfacts(edgar, "org.corp.us.apple")
    rev = [f for f in fa if f[":fin.fact/concept"] == ":revenue"][0]
    assert rev[":fin.fact/value"] == 391035.0            # base units → millions
    assert rev[":fin.fact/sourcing"] == ":authoritative"
    # the Q3 10-Q net-income point is excluded (annual 10-K only)
    ni = [f for f in fa if f[":fin.fact/concept"] == ":net-income"]
    assert len(ni) == 1 and ni[0][":fin.fact/value"] == 93736.0


def test_edinet_parser_drops_unmapped_and_keeps_ordinary_income():
    edinet = {"company": "org.corp.jp.nintendo", "accounting": "jgaap", "fiscalYear": 2024,
              "currency": "jpy", "periodEnd": "2024-03-31",
              "elements": [{"element": "jppfs_cor:NetSales", "value": 1671900, "scale": "millions", "context": "consolidated"},
                           {"element": "jppfs_cor:OrdinaryIncome", "value": 670813, "scale": "millions", "context": "consolidated"},
                           {"element": "jppfs_cor:UnmappedJunk", "value": 1, "scale": "millions", "context": "consolidated"}]}
    _fl, fa = ingest.parse_edinet_elements(edinet, "org.corp.jp.nintendo")
    concepts = {f[":fin.fact/concept"] for f in fa}
    assert concepts == {":revenue", ":ordinary-income"}   # junk dropped
    assert all(f[":fin.fact/sourcing"] == ":authoritative" for f in fa)


# ── edn round-trip ───────────────────────────────────────────────────────────
def test_edn_reader_parses_seed():
    rows = kanjo_edn.read_file(SEED)
    facts = [r for r in rows if ":fin.fact/id" in r]
    filings = [r for r in rows if ":fin.filing/id" in r]
    assert len(facts) == 36 and len(filings) == 6
    # values are floats, keywords keep their colon
    rev = [f for f in facts if f[":fin.fact/id"].endswith("toyota.2024.pl.revenue.consolidated")][0]
    assert rev[":fin.fact/value"] == 45095000.0
    assert rev[":fin.fact/concept"] == ":revenue"


# ── plain-asserts harness (no pytest) ────────────────────────────────────────
if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        t()
        print(f"  ✓ {t.__name__}")
        passed += 1
    print(f"\nkanjō tests: {passed}/{len(tests)} passed")
