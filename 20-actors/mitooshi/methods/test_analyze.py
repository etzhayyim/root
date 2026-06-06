#!/usr/bin/env python3
"""Tests for the mitooshi backtest analyzer (methods/analyze.py) over the seed graph.

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_analyze.py
    python3 test_analyze.py
"""
from __future__ import annotations

import pathlib
import sys

try:
    from analyze import backtest, load_edn, render_reliability, render_reliability_datoms
except ImportError:
    from mitooshi.methods.analyze import (  # type: ignore
        backtest, load_edn, render_reliability, render_reliability_datoms,
    )

SEED = pathlib.Path(__file__).resolve().parent.parent / "data" / "seed-forecast-graph.kotoba.edn"


def _res():
    return backtest(load_edn(SEED))


def _card(res, model):
    return next(c for c in res["cards"] if c["model"] == model)


def test_seed_parses_four_models_all_distribution_kinds():
    res = _res()
    assert len(res["cards"]) == 4
    dists = {c["dist"] for c in res["cards"]}
    assert dists == {"gaussian", "quantile", "categorical", "ensemble"}


def test_ensemble_model_scored_with_energy_crps():
    c = _card(_res(), "m-e-edge")
    assert c["metric"] == "CRPS" and c["dist"] == "ensemble" and c["n"] == 3
    assert 0 <= c["mean_primary"] < 1.0
    assert c["skill_vs_climatology"] is not None


def test_gaussian_model_skilled_against_both_baselines():
    c = _card(_res(), "m-ewma-drift")
    assert c["metric"] == "CRPS" and c["n"] == 6
    assert c["skill_vs_climatology"] > 0
    assert c["skill_vs_persistence"] > 0
    assert c["skilled"] is True


def test_quantile_model_scored_with_pinball():
    c = _card(_res(), "m-q-edge")
    assert c["metric"] == "pinball" and c["n"] == 3
    assert 0 < c["mean_primary"] < 1.0
    assert c["skill_vs_persistence"] is None  # no gaussian-persistence baseline for quantile


def test_categorical_model_scored_with_brier():
    c = _card(_res(), "m-c-edge")
    assert c["metric"] == "Brier" and c["n"] == 3
    assert 0 <= c["mean_primary"] <= 2.0
    assert c["skill_vs_climatology"] is not None  # beats/loses vs class-frequency climatology


def test_gaussian_pit_mean_reflects_slight_positive_bias():
    c = _card(_res(), "m-ewma-drift")
    assert 0.4 < c["pit_mean"] < 0.7


def test_leak_free_all_forecasts_scored_none_dropped():
    # smoke: backtest never raised a G5 leak → every forecast's obs is strictly after info.
    res = _res()
    assert sum(c["n"] for c in res["cards"]) == 15  # 6 gaussian + 3 quantile + 3 categorical + 3 ensemble


def test_reliability_diagram_has_a_section_per_model():
    res = _res()
    md = render_reliability(res)
    for c in res["cards"]:
        assert c["name"] in md
    assert "PIT mean" in md and "uniform ideal" in md


def test_reliability_datoms_emit_calib_records():
    res = _res()
    edn = render_reliability_datoms(res)
    assert edn.count(":fc.calib/id") == len(res["cards"])
    assert ":fc.calib/pit-mean" in edn and ":fc.calib/hist" in edn


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
    print(f"analyze.py: {passed}/{len(fns)} tests passed")
    return passed == len(fns)


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
