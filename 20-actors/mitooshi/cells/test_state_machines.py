#!/usr/bin/env python3
"""State-machine tests for mitooshi cells (R0). .solve() is NOT called (it raises).

Standalone-runnable AND pytest-compatible (repo pytest plugin env is broken):
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_state_machines.py
    python3 test_state_machines.py
"""
from __future__ import annotations

import sys

from series_ingest.cell import SeriesIngestCell
from series_ingest.state_machine import IngestPhase, transition_to_recorded, transition_to_screened
from forecast_issue.cell import ForecastIssueCell
from forecast_issue.state_machine import IssuePhase, issue
from online_update.cell import OnlineUpdateCell
from online_update.state_machine import UpdatePhase, apply_correction, propose_update
from calibration_gate.cell import CalibrationGateCell
from calibration_gate.state_machine import GatePhase, review_promotion
from backtest_score.cell import BacktestScoreCell
from backtest_score.state_machine import ScorePhase, score_batch


# ───────────────────────────── series_ingest (G4) ──────────────────────────
def _ingest(source_class="public-broadcast"):
    s = transition_to_screened({
        "cell_state": {}, "series_id": "s-malacca-transit", "source_class": source_class,
        "source": "AISStream", "kind": ":transit-load",
        "obs": [{"observed_at": 200, "value": 3.0}, {"observed_at": 100, "value": 2.0}],
    })
    return transition_to_recorded(s)


def test_series_ingest_public_source_records():
    cs = _ingest()["cell_state"]
    assert cs["phase"] == IngestPhase.RECORDED.value
    assert cs["payload"]["latestAt"] == 200 and cs["payload"]["latestValue"] == 3.0  # append-only, latest=current


def test_series_ingest_accepts_edn_keyword_source_class():
    cs = _ingest(source_class=":gov-open-data")["cell_state"]
    assert cs["phase"] == IngestPhase.RECORDED.value


def test_series_ingest_refuses_proprietary_terminal():
    s = transition_to_screened({
        "cell_state": {}, "series_id": "s-x", "source_class": "bloomberg-terminal",
        "source": "Bloomberg", "kind": ":price-index", "obs": [],
    })
    assert s["cell_state"]["phase"] == IngestPhase.REFUSED.value
    assert "G4" in s["cell_state"]["refusal"]


def test_series_ingest_cell_solve_raises():
    try:
        SeriesIngestCell().solve({})
        assert False
    except RuntimeError as e:
        assert "Council Lv6+" in str(e)


# ───────────────────────────── forecast_issue (G1/G2) ──────────────────────
def test_forecast_issue_valid_gaussian():
    out = issue({"cell_state": {}, "forecast_id": "f1", "series_id": "s1",
                 "dist_kind": "gaussian", "use": "resilience", "info_as_of": 100,
                 "horizon": 3, "mean": 3.2, "sd": 0.8})
    cs = out["cell_state"]
    assert cs["phase"] == IssuePhase.ISSUED.value
    assert cs["payload"]["targetAt"] == 103 and cs["payload"]["pointAsserted"] is False


def test_forecast_issue_refuses_point_assertion():
    out = issue({"cell_state": {}, "forecast_id": "f", "dist_kind": "gaussian",
                 "use": "planning", "mean": 1.0, "sd": 1.0, "point_asserted": True})
    assert out["cell_state"]["phase"] == IssuePhase.REFUSED.value
    assert "G1" in out["cell_state"]["refusal"]


def test_forecast_issue_refuses_speculative_use():
    out = issue({"cell_state": {}, "forecast_id": "f", "dist_kind": "gaussian",
                 "use": "trade", "mean": 1.0, "sd": 1.0})
    assert out["cell_state"]["phase"] == IssuePhase.REFUSED.value
    assert "G2" in out["cell_state"]["refusal"]


def test_forecast_issue_refuses_degenerate_gaussian():
    out = issue({"cell_state": {}, "forecast_id": "f", "dist_kind": "gaussian",
                 "use": "nowcast", "mean": 1.0, "sd": 0.0})
    assert out["cell_state"]["phase"] == IssuePhase.REFUSED.value


def test_forecast_issue_refuses_unnormalized_categorical():
    out = issue({"cell_state": {}, "forecast_id": "f", "dist_kind": "categorical",
                 "use": "early-warning", "probs": {"up": 0.5, "down": 0.2}})
    assert out["cell_state"]["phase"] == IssuePhase.REFUSED.value


# ───────────────────────────── online_update (G8) ──────────────────────────
def test_online_update_proposes_bias_and_inflation():
    # model systematically under-forecasts by ~+2, claimed sd 1 but residuals wider
    res = [{"error": 2.1, "sd": 1.0}, {"error": 1.9, "sd": 1.0}, {"error": 2.0, "sd": 1.0},
           {"error": 2.3, "sd": 1.0}, {"error": 1.7, "sd": 1.0}]
    out = propose_update({"cell_state": {}, "model_id": "m1", "from_version": 1,
                          "residuals": res, "trigger": ":residual-drift", "runtime": ":baien-edge"})
    cs = out["cell_state"]
    assert cs["phase"] == UpdatePhase.PROPOSED.value
    assert cs["proposed"]["toVersion"] == 2
    assert cs["proposed"]["biasCorr"] > 0          # learned the positive systematic bias
    assert cs["proposed"]["promoted"] is False     # promotion is the gate's job


def test_online_update_correction_reduces_systematic_error():
    res = [{"error": 2.0, "sd": 1.0}] * 6
    out = propose_update({"cell_state": {}, "model_id": "m", "from_version": 1,
                          "residuals": res, "runtime": "baien-edge", "alpha": 1.0})
    bias = out["cell_state"]["proposed"]["biasCorr"]
    # applying the learned bias to a mu that was 2 low lands on the observed value
    new_mu, _ = apply_correction(mean=8.0, sd=1.0, bias_corr=bias, var_infl=1.0)
    assert abs(new_mu - 10.0) < 1e-6


def test_online_update_rejects_commercial_gpu_runtime():
    out = propose_update({"cell_state": {}, "model_id": "m", "residuals": [{"error": 1.0, "sd": 1.0}],
                          "runtime": "runpod-a100"})
    assert out["cell_state"]["phase"] == UpdatePhase.REJECTED.value
    assert "G8" in out["cell_state"]["rejection"]


def test_online_update_rejects_empty_residuals():
    out = propose_update({"cell_state": {}, "model_id": "m", "residuals": [], "runtime": "baien-edge"})
    assert out["cell_state"]["phase"] == UpdatePhase.REJECTED.value


# ───────────────────────────── calibration_gate (G7/G9/G12) ────────────────
def _promote(skill=0.3, deviation=0.1, signed_by="did:web:etzhayyim.com:member:op", point=False):
    return review_promotion({"cell_state": {}, "model_id": "m1", "to_version": 2,
                             "skill": skill, "deviation": deviation, "signed_by": signed_by,
                             "point_asserted_any": point})


def test_calibration_gate_clears_skilled_calibrated_signed():
    cs = _promote()["cell_state"]
    assert cs["phase"] == GatePhase.CLEARED.value
    assert cs["payload"]["promoted"] is True and cs["payload"]["serverHeldKey"] is False


def test_calibration_gate_refuses_unskilled():
    cs = _promote(skill=-0.1)["cell_state"]
    assert cs["phase"] == GatePhase.REFUSED.value and "G12" in cs["refusal"]


def test_calibration_gate_refuses_miscalibrated():
    cs = _promote(deviation=0.9)["cell_state"]
    assert cs["phase"] == GatePhase.REFUSED.value and "G7" in cs["refusal"]


def test_calibration_gate_refuses_server_signature():
    cs = _promote(signed_by="server-key-1")["cell_state"]
    assert cs["phase"] == GatePhase.REFUSED.value and "G9" in cs["refusal"]


def test_calibration_gate_refuses_unsigned():
    cs = _promote(signed_by="")["cell_state"]
    assert cs["phase"] == GatePhase.REFUSED.value and "G9" in cs["refusal"]


def test_calibration_gate_refuses_point_assertion():
    cs = _promote(point=True)["cell_state"]
    assert cs["phase"] == GatePhase.REFUSED.value and "G1" in cs["refusal"]


# ───────────────────────────── backtest_score (G5/G12) ─────────────────────
def _pair(fid="f", info=100, mean=10.0, sd=1.0, at=101, y=10.0, point=False, use="resilience"):
    return {"forecast": {"forecastId": fid, "distKind": "gaussian", "infoAsOf": info,
                         "mean": mean, "sd": sd, "pointAsserted": point, "use": use},
            "obs": {"obsId": "o", "observedAt": at, "value": y}}


def test_backtest_score_scores_a_clean_batch():
    out = score_batch({"cell_state": {}, "model_id": "m", "baseline_primary": 1.0,
                       "pairs": [_pair(y=10.2), _pair(fid="g", y=9.8)]})
    cs = out["cell_state"]
    assert cs["phase"] == ScorePhase.SCORED.value
    assert cs["payload"]["n"] == 2 and cs["payload"]["metric"] == "crps"
    assert cs["payload"]["skilled"] is True   # beats the weak baseline 1.0


def test_backtest_score_refuses_leak():
    out = score_batch({"cell_state": {}, "model_id": "m", "pairs": [_pair(info=100, at=100)]})
    assert out["cell_state"]["phase"] == ScorePhase.REFUSED.value
    assert "G5 LEAK" in out["cell_state"]["refusal"]


def test_backtest_score_refuses_point_assertion():
    out = score_batch({"cell_state": {}, "model_id": "m", "pairs": [_pair(point=True)]})
    assert out["cell_state"]["phase"] == ScorePhase.REFUSED.value
    assert "G1" in out["cell_state"]["refusal"]


def test_backtest_score_refuses_empty_batch():
    out = score_batch({"cell_state": {}, "model_id": "m", "pairs": []})
    assert out["cell_state"]["phase"] == ScorePhase.REFUSED.value


# ───────────────────────────── solve() stubs raise ─────────────────────────
def test_remaining_cells_solve_raises():
    for cell in (ForecastIssueCell(), OnlineUpdateCell(), CalibrationGateCell(), BacktestScoreCell()):
        try:
            cell.solve({})
            assert False, f"{cell.__class__.__name__}.solve should raise"
        except RuntimeError:
            pass


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
    print(f"cells: {passed}/{len(fns)} tests passed")
    return passed == len(fns)


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
