#!/usr/bin/env python3
"""kasa 嵩 — unit tests (stdlib only; pytest-compatible AND runnable directly).

Run either way:
    python3 tests/test_kasa.py           # plain-asserts harness (no pytest needed)
    python3 -m pytest tests/test_kasa.py # standard pytest

No third-party imports (the repo root pulls a fragile pytest plugin via autoload; these tests
stay dependency-free so they run anywhere). ADR-2606072000.
"""
from __future__ import annotations
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "methods"))

import kasa_edn      # noqa: E402
import sources       # noqa: E402
import analyze       # noqa: E402
import ingest        # noqa: E402

SEED = os.path.join(HERE, "data", "seed-compute-capacity.kotoba.edn")


# ── edn reader: scientific notation (frontier-training FLOP) ──────────────────
def test_edn_reads_scientific_notation():
    rows = kasa_edn.read_file(SEED)
    o = next(r for r in rows if r.get(":compute.obs/id") == "obs.cap.flops.frontier-training.world.2024")
    assert abs(o[":compute.obs/value"] - 5.0e25) < 1e20


def test_seed_loads_series_obs_sources():
    series, obs, srcs = analyze.load(SEED)
    assert len(series) == 11
    assert len(obs) == 52
    assert len(srcs) == 8


# ── sources: G1 admissibility ────────────────────────────────────────────────
def test_public_sources_admissible():
    assert sources.admissible("sia")
    assert sources.admissible(":epoch-ai", ":open-dataset")
    assert sources.admissible("top500", ":public-list")


def test_paid_terminals_prohibited():
    assert not sources.admissible("bloomberg-terminal")
    assert not sources.admissible("gartner-report")
    # IDC headline press-release is fine, but the paid terminal/report is not (the §2(e) split)
    assert sources.admissible("idc", ":press-release")
    assert not sources.admissible("idc", ":paid-terminal")


# ── analyze: YoY + CAGR arithmetic ───────────────────────────────────────────
def test_yoy_matches_arithmetic():
    """Semiconductor 2024 YoY = 628/527-1 = +19.2%."""
    _s, obs, _src = analyze.load(SEED)
    sy = analyze.by_series_year(obs)
    g = {(x[":compute.growth/series"], x[":compute.growth/kind"], x[":compute.growth/to-year"]): x[":compute.growth/value"]
         for x in analyze.derive_growth(sy)}
    assert abs(g[("cap.semi.revenue.world", ":yoy", 2024)] - (628.0 / 527.0 - 1)) < 1e-3


def test_cagr_matches_arithmetic():
    """SSD CAGR 2020→2024 = (650/207)^(1/4)-1."""
    _s, obs, _src = analyze.load(SEED)
    sy = analyze.by_series_year(obs)
    g = {(x[":compute.growth/series"], x[":compute.growth/kind"]): x[":compute.growth/value"]
         for x in analyze.derive_growth(sy)}
    expected = (650.0 / 207.0) ** (1 / 4) - 1
    assert abs(g[("cap.flops.frontier-training.world", ":cagr")] - ((5.0e25 / 3.0e23) ** (1 / 4) - 1)) < 1e-2
    assert abs(g[("cap.storage.ssd-capacity.world", ":cagr")] - expected) < 1e-3


def test_yoy_skips_non_consecutive_years():
    """A gap in years must NOT produce a YoY (only consecutive pairs)."""
    sy = {"s": {2020: 100.0, 2022: 200.0}}  # 2021 missing
    g = analyze.derive_growth(sy)
    yoys = [x for x in g if x[":compute.growth/kind"] == ":yoy"]
    assert yoys == []  # no consecutive pair → no YoY
    cagrs = [x for x in g if x[":compute.growth/kind"] == ":cagr"]
    assert len(cagrs) == 1  # span CAGR still computed


# ── analyze: coverage-honest aggregates, no double-count ──────────────────────
def test_storage_aggregate_sums_hdd_plus_ssd():
    """storage exabytes 2024 = HDD 1010 + SSD 650 = 1660, n=2."""
    series, obs, _src = analyze.load(SEED)
    sy = analyze.by_series_year(obs)
    aggs = analyze.aggregates(series, sy)
    a = next(x for x in aggs if x[":compute.agg/key"] == ":storage" and x[":compute.agg/year"] == 2024)
    assert abs(a[":compute.agg/sum"] - 1660.0) < 1e-6
    assert a[":compute.agg/n"] == 2


def test_memory_never_summed_into_semiconductor():
    """DRAM + NAND must stay in their OWN domain keys — never folded into :semiconductor (no double-count)."""
    series, obs, _src = analyze.load(SEED)
    sy = analyze.by_series_year(obs)
    aggs = analyze.aggregates(series, sy)
    semi = next(x for x in aggs if x[":compute.agg/key"] == ":semiconductor" and x[":compute.agg/year"] == 2024)
    assert semi[":compute.agg/n"] == 1               # only the semi series, not + dram + nand
    assert abs(semi[":compute.agg/sum"] - 628.0) < 1e-6
    assert any(x[":compute.agg/key"] == ":dram" for x in aggs)
    assert any(x[":compute.agg/key"] == ":nand" for x in aggs)


def test_flops_petaflops_not_summed_with_raw_flop():
    """TOP500 (:petaflops) and frontier-training (:ones) share unit :flops but DIFFERENT scale —
    they must NOT be summed into one meaningless aggregate (separate rows, n=1 each)."""
    series, obs, _src = analyze.load(SEED)
    sy = analyze.by_series_year(obs)
    aggs = analyze.aggregates(series, sy)
    flops = [x for x in aggs if x[":compute.agg/key"] == ":flops" and x[":compute.agg/year"] == 2024]
    assert len(flops) == 2                           # flops-installed + flops-training, kept apart
    assert all(x[":compute.agg/n"] == 1 for x in flops)


# ── analyze: derived growth + aggregates are :synthesized ─────────────────────
def test_growth_and_aggregates_are_synthesized():
    series, obs, _src = analyze.load(SEED)
    sy = analyze.by_series_year(obs)
    for g in analyze.derive_growth(sy):
        assert g[":compute.growth/sourcing"] == ":synthesized"
    for a in analyze.aggregates(series, sy):
        assert a[":compute.agg/sourcing"] == ":synthesized"


# ── ingest: G1 gate + merge precedence + round-trip ──────────────────────────
def test_ingest_refuses_prohibited_publisher():
    obj = {"source": "src.bb", "publisher": "bloomberg-terminal", "access": "paid-terminal",
           "rows": [{"series": "cap.semi.revenue.world", "year": 2025, "value": 700.0}]}
    try:
        ingest.rows_to_obs(obj)
        raised = False
    except SystemExit:
        raised = True
    assert raised, "ingest must refuse a prohibited (paid-terminal) publisher (G1)"


def test_ingest_accepts_public_rows():
    obj = {"source": "src.epoch", "publisher": "epoch-ai", "access": "open-dataset",
           "rows": [{"series": "cap.flops.frontier-training.world", "year": 2025,
                     "value": 1.0e26, "sourcing": "estimated", "method": "test"}]}
    out = ingest.rows_to_obs(obj)
    assert len(out) == 1
    assert out[0][":compute.obs/id"] == "obs.cap.flops.frontier-training.world.2025"
    assert out[0][":compute.obs/sourcing"] == ":estimated"


def test_merge_authoritative_beats_representative():
    """An :authoritative ingested row overrides a :representative seed row of the same id."""
    auth = {":compute.obs/id": "obs.cap.semi.revenue.world.2024", ":compute.obs/series": "cap.semi.revenue.world",
            ":compute.obs/year": 2024, ":compute.obs/value": 627.6, ":compute.obs/source": "src.sia",
            ":compute.obs/method": "", ":compute.obs/sourcing": ":authoritative"}
    merged = ingest.merge_with_seed([], [auth])
    row = next(r for r in merged if r.get(":compute.obs/id") == "obs.cap.semi.revenue.world.2024")
    assert row[":compute.obs/sourcing"] == ":authoritative"
    assert abs(row[":compute.obs/value"] - 627.6) < 1e-6


# ── report renders ───────────────────────────────────────────────────────────
def test_report_renders_growth_and_snapshot():
    series, obs, srcs = analyze.load(SEED)
    sy = analyze.by_series_year(obs)
    md = analyze.report(series, obs, srcs, sy, analyze.derive_growth(sy), analyze.aggregates(series, sy))
    assert "年間増加量" in md
    assert "World compute snapshot" in md
    assert "1,660 EB" in md  # storage aggregate rendered


# ── harness ──────────────────────────────────────────────────────────────────
def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
    print(f"kasa test_kasa: {passed}/{len(fns)} passed")
    return passed == len(fns)


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
