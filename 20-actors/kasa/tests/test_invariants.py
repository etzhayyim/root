#!/usr/bin/env python3
"""kasa 嵩 — charter-invariant + gate tests (stdlib only; pytest-compatible AND direct).

    python3 tests/test_invariants.py
    python3 -m pytest tests/test_invariants.py

Complements tests/test_kasa.py (arithmetic + admissibility) with the LOAD-BEARING structural
invariants: kasa is NON-ADJUDICATING (G2), gives NO FORECAST (G4 — measured/estimated actuals
only; future projection is mitooshi 見通し), is a PLANNING lens not a targeting list (G9), sources
are public-only (G1), seed obs are sourcing-honest (G5), and every derived number is flagged
:synthesized. ADR-2606072000.
"""
from __future__ import annotations
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "methods"))

import analyze        # noqa: E402
import sources        # noqa: E402
import kasa_edn       # noqa: E402

SEED = os.path.join(HERE, "data", "seed-compute-capacity.kotoba.edn")
VALID_SOURCING = {":authoritative", ":representative", ":estimated", ":synthesized"}


def _report():
    series, obs, srcs = analyze.load(SEED)
    sy = analyze.by_series_year(obs)
    growth = analyze.derive_growth(sy)
    aggs = analyze.aggregates(series, sy)
    return analyze.report(series, obs, srcs, sy, growth, aggs), growth, aggs


def test_report_is_non_adjudicating_no_forecast():
    md, _g, _a = _report()
    assert "non-adjudicating" in md.lower()
    assert "no forecast" in md.lower()


def test_report_states_no_forecast_no_targeting():
    """G4/G9: the report must EXPLICITLY disclaim forecasting + targeting, and must not leak an
    adjudication artifact (a country ranking verdict, a buy/sell call, a target list)."""
    md, _g, _a = _report()
    assert "does not forecast" in md.lower()
    assert "targeting list" in md.lower()
    for verdict in ("目標株価", "buy/sell", "export-control list:", "target list:"):
        assert verdict.lower() not in md.lower(), f"adjudication/targeting artifact leaked: {verdict!r}"


def test_every_seed_obs_sourcing_is_valid_and_honest():
    """G5: every observation carries a valid sourcing; NONE is :authoritative in the R0 seed
    (the seed is headline :representative + :estimated only — no exact dataset row yet)."""
    rows = kasa_edn.read_file(SEED)
    obs = [r for r in rows if ":compute.obs/id" in r]
    assert obs, "seed must contain observations"
    for o in obs:
        s = o.get(":compute.obs/sourcing")
        assert s in VALID_SOURCING, f"{o[':compute.obs/id']} has invalid sourcing {s!r}"
        assert s != ":authoritative", "R0 seed must NOT claim :authoritative (it is headline/estimated)"


def test_estimated_obs_carry_a_method():
    """G5: an :estimated observation MUST document HOW (method non-empty); a :representative one
    needs no method. This is what separates an honest nowcast from an unsourced number."""
    rows = kasa_edn.read_file(SEED)
    for o in (r for r in rows if r.get(":compute.obs/sourcing") == ":estimated"):
        assert o.get(":compute.obs/method", "").strip(), f"{o[':compute.obs/id']} :estimated but no method"


def test_no_future_year_observations():
    """G4: kasa records PAST/PRESENT actuals only — no observation may be dated in the future
    (future projection is mitooshi 見通し, structurally out of scope here)."""
    rows = kasa_edn.read_file(SEED)
    CURRENT_YEAR = 2026  # the actor's 'now' per repo currentDate
    for o in (r for r in rows if ":compute.obs/id" in r):
        assert int(o[":compute.obs/year"]) <= CURRENT_YEAR, f"{o[':compute.obs/id']} is a future-dated obs"


def test_all_seed_sources_are_admissible():
    """G1: every source referenced by the seed must pass the public-source admissibility gate."""
    rows = kasa_edn.read_file(SEED)
    srcs = {r[":compute.source/id"]: r for r in rows if ":compute.source/id" in r}
    for s in srcs.values():
        pub = s[":compute.source/publisher"]
        access = s.get(":compute.source/access")
        assert sources.admissible(pub, access), f"seed source {s[':compute.source/id']} publisher {pub} not admissible (G1)"


def test_derived_values_are_synthesized():
    """G5: growth + aggregates are :synthesized — never presented as a reported observation."""
    _md, growth, aggs = _report()
    for g in growth:
        assert g[":compute.growth/sourcing"] == ":synthesized"
    for a in aggs:
        assert a[":compute.agg/sourcing"] == ":synthesized"


def test_aggregates_never_mix_scale_or_double_count():
    """G12: each aggregate is single-(domain,metric,unit,scale); memory stays out of semiconductor."""
    _md, _g, aggs = _report()
    keys = [(a[":compute.agg/key"], a[":compute.agg/metric"], a[":compute.agg/unit"], a[":compute.agg/scale"], a[":compute.agg/year"]) for a in aggs]
    assert len(keys) == len(set(keys)), "aggregate keys must be unique per (domain,metric,unit,scale,year)"
    # semiconductor aggregate must never absorb dram/nand (distinct domain keys exist)
    domains = {a[":compute.agg/key"] for a in aggs}
    assert {":semiconductor", ":dram", ":nand"} <= domains


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
    print(f"kasa test_invariants: {passed}/{len(fns)} passed")
    return passed == len(fns)


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
