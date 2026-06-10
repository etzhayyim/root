"""test_grounding.py — 潮目 (shionome) stock-layer entity-grounding bridge. ADR-2606072200. Standalone.

Hermetic: the core functions are pure (fed inline fixtures), so the suite never depends on a
sibling actor's file contents. One conditional check exercises the real kabuto/hokorobi ledgers
IF present (and the fail-open path otherwise), so it is green either way.
"""
from __future__ import annotations

import pathlib

from _t import run
from grounding import (LAYER_GROUNDING, ground, ground_equities, grounding_roadmap,
                       hokorobi_institutions, kabuto_equity_constituents,
                       kanjo_disclosed_companies, load_ledger, systemic_overlay)

ROOT = pathlib.Path(__file__).resolve().parents[3]


# ── kabuto constituent extraction ────────────────────────────────────────────────
def _kab_fixture():
    return [
        {":company/id": "org.corp.us.apple", ":company/name": "Apple", ":company/ticker": "AAPL",
         ":company/country": "US", ":company/sector": ":electronics", ":company/market-cap-busd": 3300.0,
         ":company/sourcing": ":representative"},
        {":company/id": "org.corp.tw.tsmc", ":company/name": "TSMC", ":company/ticker": "2330.TW",
         ":company/market-cap-busd": 950.0, ":company/sourcing": ":representative"},
        {":company/id": "org.corp.jp.x", ":company/name": "Unsized Co", ":company/ticker": "9999.T"},  # no market-cap
        {":address/of": "org.corp.us.apple", ":address/city": "Cupertino"},   # NOT a company record
        {":supply.edge/from": "a", ":supply.edge/to": "b"},                   # NOT a company record
    ]


def test_kabuto_filters_non_company_records():
    cons = kabuto_equity_constituents(_kab_fixture())
    assert len(cons) == 3   # 3 companies; address + supply-edge skipped
    assert {c["name"] for c in cons} == {"Apple", "TSMC", "Unsized Co"}


def test_kabuto_parses_size_and_sector():
    cons = {c["name"]: c for c in kabuto_equity_constituents(_kab_fixture())}
    assert cons["Apple"]["market_cap_busd"] == 3300.0
    assert cons["Apple"]["sector"] == "electronics"     # keyword normalized
    assert cons["Unsized Co"]["market_cap_busd"] is None


# ── hokorobi institution extraction ──────────────────────────────────────────────
def _hok_fixture():
    return [
        {":organism/id": "fin.inst.jpmorgan", ":organism/kind": ":institution", ":organism/label": "JPMorgan Chase",
         ":inst/sector": ":bank", ":inst/sii": ":g-sib", ":inst/jurisdiction": "US", ":organism/sourcing": ":authoritative"},
        {":organism/id": "fin.inst.allianz", ":organism/kind": ":institution", ":organism/label": "Allianz",
         ":inst/sector": ":insurer", ":inst/sii": ":large", ":inst/jurisdiction": "DE", ":organism/sourcing": ":authoritative"},
        {":organism/id": "fin.inst.regional", ":organism/kind": ":institution", ":organism/label": "Regional bank",
         ":inst/sector": ":bank", ":inst/sii": ":mid", ":inst/jurisdiction": "US", ":organism/sourcing": ":representative"},
        {":organism/id": "risk.leverage", ":organism/kind": ":risk-source"},   # NOT an institution
        {":en/from": "a", ":en/to": "b", ":en/risk-load": 0.7},                # an edge, NOT an institution
    ]


def test_hokorobi_filters_to_institutions():
    insts = hokorobi_institutions(_hok_fixture())
    assert len(insts) == 3   # risk-source + edge skipped
    assert {i["label"] for i in insts} == {"JPMorgan Chase", "Allianz", "Regional bank"}


def test_systemic_overlay_counts_and_sourcing():
    ov = systemic_overlay(hokorobi_institutions(_hok_fixture()))
    assert ov["institutions"] == 3
    assert ov["by_sector"] == {"bank": 2, "insurer": 1}
    assert ov["authoritative"] == 2 and ov["representative"] == 1
    assert ov["no_trade_notice"] is True


# ── equities grounding math (the honesty contract) ───────────────────────────────
def test_ground_equities_value_coverage_math():
    cons = kabuto_equity_constituents(_kab_fixture())
    g = ground_equities(115.0, cons, universe=55000)
    assert g["grounded_entities"] == 3
    assert g["entities_with_size"] == 2
    # (3300 + 950) busd = 4.25 tn  →  4.25 / 115
    assert abs(g["grounded_market_cap_usd_tn"] - 4.25) < 1e-9
    assert abs(g["value_coverage_of_layer"] - round(4.25 / 115.0, 4)) < 1e-9


def test_ground_equities_value_coverage_is_lower_bound():
    # one sized + one unsized company → coverage is explicitly a lower bound
    g = ground_equities(115.0, kabuto_equity_constituents(_kab_fixture()))
    assert g["value_coverage_is_lower_bound"] is True


def test_ground_equities_count_coverage_fraction():
    g = ground_equities(115.0, kabuto_equity_constituents(_kab_fixture()), universe=55000)
    assert g["universe_sourcing"] == "representative"   # honesty: not a live count
    assert abs(g["count_coverage_of_universe"] - round(3 / 55000, 5)) < 1e-9


def test_ground_equities_top_constituents_sorted():
    g = ground_equities(115.0, kabuto_equity_constituents(_kab_fixture()))
    tops = g["top_constituents"]
    assert tops[0]["name"] == "Apple" and tops[1]["name"] == "TSMC"


def test_ground_equities_no_trade_notice():
    assert ground_equities(115.0, [])["no_trade_notice"] is True


def test_ground_equities_empty_is_zero_not_crash():
    g = ground_equities(115.0, [])
    assert g["grounded_entities"] == 0 and g["value_coverage_of_layer"] == 0.0


# ── full report + ungrounded honesty ─────────────────────────────────────────────
def _pyramid_fixture():
    return {"layers": [
        {"asset_class": "equities", "usd_tn": 115.0},
        {"asset_class": "gold", "usd_tn": 16.0},
        {"asset_class": "derivatives", "usd_tn": 600.0},
    ]}


def test_ground_full_report_shape():
    rep = ground(_pyramid_fixture(), _kab_fixture(), _hok_fixture())
    for k in ("equities", "systemic_institutions_overlay", "ungrounded_layers", "summary"):
        assert k in rep
    assert rep["summary"]["no_trade_notice"] is True


def test_ground_names_ungrounded_layers():
    rep = ground(_pyramid_fixture(), _kab_fixture(), _hok_fixture())
    # equities is grounded (kabuto present); gold + derivatives are NOT
    assert "equities" not in rep["ungrounded_layers"]
    assert set(rep["ungrounded_layers"]) == {"gold", "derivatives"}
    assert rep["summary"]["layers_with_entity_grounding"] == 1
    assert rep["summary"]["pyramid_layers"] == 3


def test_ground_total_named_entities():
    rep = ground(_pyramid_fixture(), _kab_fixture(), _hok_fixture())
    assert rep["summary"]["total_named_entities"] == 3 + 3   # 3 cos + 3 institutions


def test_no_kabuto_means_equities_ungrounded():
    # fail-open: no kabuto ledger → equities falls into ungrounded, no crash
    rep = ground(_pyramid_fixture(), [], _hok_fixture())
    assert "equities" in rep["ungrounded_layers"]
    assert rep["summary"]["layers_with_entity_grounding"] == 0


# ── kanjō disclosure depth (equities layer enrichment) ───────────────────────────
def _kanjo_fixture():
    return [
        {":fin.filing/id": "fil.a", ":fin.filing/company": "org.corp.us.apple", ":fin.filing/fiscal-year": 2024},
        {":fin.filing/id": "fil.t", ":fin.filing/company": "org.corp.tw.tsmc", ":fin.filing/fiscal-year": 2024},
        {":fin.fact/id": "fact.x", ":fin.fact/company": "org.corp.us.apple"},   # a fact, not a filing
    ]


def test_kanjo_disclosed_companies_extracts_filing_companies():
    disc = kanjo_disclosed_companies(_kanjo_fixture())
    assert disc == {"org.corp.us.apple", "org.corp.tw.tsmc"}   # facts ignored, dedup


def test_ground_equities_disclosure_depth():
    cons = kabuto_equity_constituents(_kab_fixture())   # ids: apple, tsmc, jp.x
    g = ground_equities(115.0, cons, disclosed_ids={"org.corp.us.apple", "org.corp.tw.tsmc"})
    assert g["with_disclosed_financials"] == 2
    assert set(g["disclosed_sample"]) == {"Apple", "TSMC"}


def test_ground_equities_depth_defaults_zero():
    g = ground_equities(115.0, kabuto_equity_constituents(_kab_fixture()))
    assert g["with_disclosed_financials"] == 0


# ── per-layer grounding roadmap ───────────────────────────────────────────────────
def test_roadmap_covers_every_layer():
    roadmap = grounding_roadmap(_pyramid_fixture())
    assert {r["asset_class"] for r in roadmap} == {"equities", "gold", "derivatives"}


def test_roadmap_equities_grounded_rest_ungroundable():
    roadmap = {r["asset_class"]: r for r in grounding_roadmap(_pyramid_fixture())}
    assert roadmap["equities"]["status"] == "grounded"
    assert roadmap["equities"]["source_actor"] == "kabuto"
    assert roadmap["gold"]["status"] == "ungroundable-at-r0"
    assert roadmap["derivatives"]["status"] == "ungroundable-at-r0"
    # every ungroundable layer states a non-empty reason (honesty contract)
    assert all(r["reason"] for r in roadmap.values())


def test_layer_grounding_registry_well_formed():
    for ac, spec in LAYER_GROUNDING.items():
        assert spec["status"] in ("grounded", "ungroundable-at-r0")
        assert "reason" in spec and spec["reason"]
        if spec["status"] == "grounded":
            assert spec["source_actor"]


def test_ground_report_has_roadmap_and_depth():
    rep = ground(_pyramid_fixture(), _kab_fixture(), _hok_fixture(), _kanjo_fixture())
    assert "roadmap" in rep and len(rep["roadmap"]) == 3
    assert rep["equities"]["with_disclosed_financials"] >= 1   # apple overlaps


def test_ground_without_kanjo_still_works():
    rep = ground(_pyramid_fixture(), _kab_fixture(), _hok_fixture())   # kanjo omitted
    assert rep["equities"]["with_disclosed_financials"] == 0


# ── fail-open loader ──────────────────────────────────────────────────────────────
def test_load_ledger_missing_returns_empty():
    assert load_ledger(ROOT / "20-actors" / "nonesuch" / "missing.edn") == []


def test_real_sibling_ledgers_present_or_fail_open():
    # exercises the REAL kabuto/hokorobi ledgers if checked out; green either way (fail-open).
    kab = load_ledger(ROOT / "20-actors" / "kabuto" / "data" / "seed-public-companies.kotoba.edn")
    if kab:
        assert len(kabuto_equity_constituents(kab)) > 100   # the real seed has >100 companies
    else:
        assert kabuto_equity_constituents(kab) == []        # fail-open path


if __name__ == "__main__":
    run("grounding", [(n, f) for n, f in sorted(globals().items())
                      if n.startswith("test_") and callable(f)])
