#!/usr/bin/env python3
"""Tests for the mitooshi proper-scoring engine (methods/score.py).

Standalone-runnable AND pytest-compatible (repo pytest plugin env is broken):
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_score.py
    python3 test_score.py
"""
from __future__ import annotations

import math
import sys

try:
    from score import (
        Forecast, Observation, brier_score, calibration_summary, categorical_logscore,
        climatology_gaussian, ensemble_crps, ensemble_pit, gaussian_crps, gaussian_logscore,
        gaussian_pit, persistence_gaussian, pinball_loss, quantile_pit, score_pair, score_set,
        skill_score,
    )
except ImportError:  # when run as a module
    from mitooshi.methods.score import (  # type: ignore
        Forecast, Observation, brier_score, calibration_summary, categorical_logscore,
        climatology_gaussian, ensemble_crps, ensemble_pit, gaussian_crps, gaussian_logscore,
        gaussian_pit, persistence_gaussian, pinball_loss, quantile_pit, score_pair, score_set,
        skill_score,
    )


# ───────────────────────────── CRPS ─────────────────────────────
def test_crps_standard_normal_at_mean():
    # Known closed-form value: CRPS(N(0,1), 0) = 2*phi(0) - 1/sqrt(pi) ≈ 0.23370.
    assert abs(gaussian_crps(0.0, 1.0, 0.0) - 0.23370) < 1e-4


def test_crps_collapses_to_abs_error_as_sigma_to_zero():
    assert abs(gaussian_crps(10.0, 1e-12, 11.0) - 1.0) < 1e-6


def test_crps_nonnegative_and_scales_with_sigma():
    assert gaussian_crps(0.0, 1.0, 3.0) > 0
    # a wider distribution that still covers the outcome scores better when off-target
    near = gaussian_crps(0.0, 1.0, 5.0)
    wide = gaussian_crps(0.0, 3.0, 5.0)
    assert wide < near  # honest uncertainty beats overconfident miss


def test_crps_better_forecast_scores_lower():
    good = gaussian_crps(10.0, 2.0, 10.2)
    bad = gaussian_crps(4.0, 2.0, 10.2)
    assert good < bad


# ───────────────────────────── log score / PIT ──────────────────
def test_logscore_minimized_near_mean():
    assert gaussian_logscore(10.0, 2.0, 10.0) < gaussian_logscore(10.0, 2.0, 16.0)


def test_pit_is_half_at_mean_and_monotone():
    assert abs(gaussian_pit(5.0, 2.0, 5.0) - 0.5) < 1e-9
    assert gaussian_pit(5.0, 2.0, 1.0) < 0.5 < gaussian_pit(5.0, 2.0, 9.0)


# ───────────────────────────── pinball / quantile ───────────────
def test_pinball_zero_when_median_equals_outcome():
    # single median quantile at the outcome → loss 0
    assert pinball_loss({0.5: 7.0}, 7.0) == 0.0


def test_pinball_positive_and_asymmetric():
    q = {0.1: 2.0, 0.5: 5.0, 0.9: 8.0}
    assert pinball_loss(q, 5.0) > 0
    # an outcome in the upper tail is penalised by the lower quantiles
    assert pinball_loss(q, 9.0) > pinball_loss(q, 5.0)


def test_quantile_pit_brackets():
    q = {0.1: 2.0, 0.5: 5.0, 0.9: 8.0}
    assert quantile_pit(q, 1.0) == 0.0   # below the span
    assert quantile_pit(q, 9.0) == 1.0   # above the span
    assert abs(quantile_pit(q, 5.0) - 0.5) < 1e-9


# ───────────────────────────── brier / categorical ──────────────
def test_brier_perfect_confident_is_zero():
    assert brier_score({"up": 1.0, "flat": 0.0, "down": 0.0}, "up") == 0.0


def test_brier_worst_confident_wrong():
    # confidently wrong: (1-0)^2 + (0-1)^2 = 2
    assert abs(brier_score({"up": 1.0, "down": 0.0}, "down") - 2.0) < 1e-9


def test_categorical_logscore_penalises_low_prob_truth():
    assert categorical_logscore({"a": 0.9, "b": 0.1}, "b") > categorical_logscore({"a": 0.9, "b": 0.1}, "a")


# ───────────────────────────── ensemble (energy-form CRPS) ──────
def test_ensemble_crps_known_value():
    # members {-1, 1}, y=0: term1 = (1+1)/2 = 1; term2 = (0+2+2+0)/(2*4) = 0.5 → 0.5
    assert abs(ensemble_crps([-1.0, 1.0], 0.0) - 0.5) < 1e-9


def test_ensemble_crps_reduces_to_abs_error_for_singleton():
    assert abs(ensemble_crps([3.0], 5.0) - 2.0) < 1e-9


def test_ensemble_crps_tight_correct_beats_vague():
    tight = ensemble_crps([9.9, 10.0, 10.1], 10.0)
    vague = ensemble_crps([2.0, 10.0, 18.0], 10.0)
    assert tight < vague


def test_ensemble_pit_fraction_at_or_below():
    assert ensemble_pit([1.0, 2.0, 3.0, 4.0], 2.5) == 0.5


def test_score_pair_valid_ensemble():
    fc = Forecast("e", "ensemble", info_as_of=100, members=[9.0, 10.0, 11.0])
    r = score_pair(fc, Observation("o", observed_at=101, value=10.0))
    assert "crps" in r and "pit" in r and r["crps"] >= 0


# ───────────────────────────── baselines + skill ────────────────
def test_climatology_and_persistence():
    hist = [4.0, 5.0, 6.0, 5.0, 4.0]
    mu_c, sd_c = climatology_gaussian(hist)
    assert abs(mu_c - 4.8) < 1e-9 and sd_c > 0
    mu_p, sd_p = persistence_gaussian(hist)
    assert mu_p == 4.0 and sd_p > 0


def test_skill_positive_when_model_beats_baseline():
    assert skill_score(0.5, 1.0) == 0.5            # half the error → skill 0.5
    assert skill_score(1.5, 1.0) < 0               # worse than baseline → negative


# ───────────────────────────── leak-free pair scorer (G5) ───────
def test_score_pair_rejects_lookahead_leak():
    fc = Forecast("f", "gaussian", info_as_of=100, mean=10.0, sd=2.0)
    leak = Observation("o", observed_at=100, value=10.0)  # NOT strictly after
    try:
        score_pair(fc, leak)
        assert False, "expected G5 leak ValueError"
    except ValueError as e:
        assert "G5 LEAK" in str(e)


def test_score_pair_rejects_point_assertion():
    fc = Forecast("f", "gaussian", info_as_of=100, mean=10.0, sd=2.0, point_asserted=True)
    ob = Observation("o", observed_at=101, value=10.0)
    try:
        score_pair(fc, ob)
        assert False, "expected G1 ValueError"
    except ValueError as e:
        assert "G1" in str(e)


def test_score_pair_rejects_speculative_use():
    fc = Forecast("f", "gaussian", info_as_of=100, mean=10.0, sd=2.0, use="trade")
    ob = Observation("o", observed_at=101, value=10.0)
    try:
        score_pair(fc, ob)
        assert False, "expected G2 ValueError"
    except ValueError as e:
        assert "G2" in str(e)


def test_score_pair_valid_gaussian():
    fc = Forecast("f", "gaussian", info_as_of=100, mean=10.0, sd=2.0)
    ob = Observation("o", observed_at=101, value=11.0)
    r = score_pair(fc, ob)
    assert "crps" in r and "log_score" in r and "pit" in r
    assert r["crps"] > 0


# ───────────────────────────── calibration ──────────────────────
def test_calibration_uniform_pit_low_deviation():
    pits = [(i + 0.5) / 20 for i in range(20)]  # evenly spread → near-uniform
    c = calibration_summary(pits, bins=10)
    assert abs(c["pit_mean"] - 0.5) < 1e-9
    assert c["deviation"] < 1e-9


def test_calibration_clustered_pit_high_deviation():
    pits = [0.01] * 20  # all in the first bin → maximally miscalibrated
    c = calibration_summary(pits, bins=10)
    assert c["deviation"] > 1.5


# ───────────────────────────── set-level skill (G12) ────────────
def test_score_set_marks_skilled_only_when_beating_baseline():
    pairs = [
        (Forecast(f"f{i}", "gaussian", info_as_of=100 + i, mean=10.0, sd=2.0),
         Observation(f"o{i}", observed_at=200 + i, value=10.0 + 0.1 * i))
        for i in range(5)
    ]
    # baseline that is much worse (huge CRPS)
    baseline = [{"crps": 5.0} for _ in range(5)]
    res = score_set(pairs, baseline=baseline)
    assert res["n"] == 5
    assert res["skilled"] is True and res["skill"] > 0
    # a strong baseline the model cannot beat → honest not-skilled
    res2 = score_set(pairs, baseline=[{"crps": 0.01} for _ in range(5)])
    assert res2["skilled"] is False


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
    print(f"score.py: {passed}/{len(fns)} tests passed")
    return passed == len(fns)


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
