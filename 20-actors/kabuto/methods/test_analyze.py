#!/usr/bin/env python3
"""Tests for the kabuto 兜 supply-chain concentration analyzer (methods/analyze.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_analyze.py
    python3 test_analyze.py

Covers the concentration roll-ups (single-source, per-commodity HHI, jurisdiction load,
diversification, intermediaries, tier depth) and their mathematical bounds, plus the
load-bearing charter invariant: kabuto is a resilience/accountability map, NEVER a
target-list — the report and social posts state it, and single-source findings exist to be
diversified, not exploited (G2).
"""
from __future__ import annotations

import pathlib
import sys

try:
    from kabuto_edn import classify, load_edn
    from analyze import analyze, render_datoms, render_report
except ImportError:
    from kabuto.methods.kabuto_edn import classify, load_edn  # type: ignore
    from kabuto.methods.analyze import analyze, render_datoms, render_report  # type: ignore

_SEED = pathlib.Path(__file__).resolve().parent.parent / "data" / "seed-public-companies.kotoba.edn"


def _load():
    rows = load_edn(_SEED)
    companies, addresses, contacts, edges, processes = classify(rows)
    return companies, addresses, contacts, edges, processes, analyze(companies, edges)


def test_classify_buckets_the_seed():
    companies, addresses, contacts, edges, processes, _ = _load()
    assert len(companies) >= 100          # a substantial public-company seed
    assert len(edges) >= 50               # disclosed supply edges present


def test_single_source_findings_are_high_criticality():
    *_, a = _load()
    # every single-source dependency surfaced is high-criticality (>= 0.7) by construction
    for cust, commodity, sup, crit in a["single_source"]:
        assert crit >= 0.7


def test_commodity_hhi_is_bounded_zero_to_one():
    *_, a = _load()
    assert a["commodity_hhi"], "expected per-commodity HHI rows"
    # row = (commodity, supplier_count, hhi)
    for commodity, n_sup, hhi in a["commodity_hhi"]:
        # HHI = Σ(share²) ∈ (0, 1]
        assert 0.0 < hhi <= 1.0
        # a single disclosed supplier ⇒ monopoly HHI of exactly 1.0
        if n_sup == 1:
            assert hhi == 1.0


def test_jurisdiction_load_is_non_negative():
    *_, a = _load()
    assert a["jurisdiction_load"]
    assert all(v >= 0 for v in a["jurisdiction_load"].values())


def test_diversification_sorted_brittle_first():
    *_, a = _load()
    idxs = [row[3] for row in a["diversification"]]
    assert idxs == sorted(idxs)           # lowest (most brittle) diversification index first


def test_intermediaries_score_is_in_times_out():
    *_, a = _load()
    for node, ind, outd, score in a["intermediaries"]:
        assert score == ind * outd        # betweenness proxy = in-degree × out-degree


def test_render_datoms_marked_derived():
    companies, addresses, contacts, edges, processes, a = _load()
    edn = render_datoms(companies, a)
    assert ":derived" in edn or "derived" in edn   # never re-ingested as authoritative


def test_g2_report_is_not_a_target_list():
    companies, addresses, contacts, edges, processes, a = _load()
    md = render_report(companies, addresses, contacts, edges, processes, a)
    assert "target-list" in md            # the framing invariant is stated in the report


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"kabuto analyze.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
