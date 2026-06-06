#!/usr/bin/env python3
"""End-to-end LEARNING-LOOP integration test for mitooshi 見通し.

This is the test that proves the answer to *「事実からモデル誤差・weight を修正・学習する
architecture」* actually closes: a deliberately biased + overconfident model is corrected by
its OWN residuals, its error drops, its calibration improves, and only then is it promoted —
and promotion is refused without a member signature (no-server-key).

The full cycle exercised across the actor's own modules:

  forecast (v1, biased+overconfident)  →  score_pair  →  residuals (fact − forecast)
     →  online_update.propose_update  →  bias_corr + var_infl  (the learned weights)
     →  apply_correction  →  forecast (v2)  →  score_pair  →  error DOWN, calibration UP
     →  calibration_gate.review_promotion  →  CLEARED (member-signed) / REFUSED (unsigned)

Run:  python3 test_learning_loop.py    (standalone; adds methods/ + cells/ to the path)
"""
from __future__ import annotations

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT / "methods"))
sys.path.insert(0, str(_ROOT / "cells"))

from score import (  # noqa: E402
    Forecast, Observation, calibration_summary, gaussian_crps, score_pair, skill_score,
)
from online_update.state_machine import UpdatePhase, apply_correction, propose_update  # noqa: E402
from calibration_gate.state_machine import GatePhase, review_promotion  # noqa: E402

# A model that systematically UNDER-forecasts by ~2 (the dominant defect) and is slightly
# mis-dispersed (claims sd=1.0 while its post-bias residual spread is ~0.78). These are
# exactly the two things online_update repairs: bias (mean residual) and dispersion
# (residual std / claimed sd → variance-inflation factor).
_Y = [10.0, 12.0, 9.0, 13.0, 11.0]
_MU_V1 = [8.4, 9.5, 8.0, 10.0, 9.0]   # errors y-mu = [1.6, 2.5, 1.0, 3.0, 2.0], mean≈2.02
_SD_V1 = 1.0


def _score_batch(mus, sd, ys):
    """Score a batch of gaussian forecasts; return (mean CRPS, PIT list, residual rows)."""
    crps, pits, residuals = [], [], []
    for mu, y in zip(mus, ys):
        fc = Forecast("f", "gaussian", info_as_of=0, mean=mu, sd=sd)
        sc = score_pair(fc, Observation("o", observed_at=1, value=y))
        crps.append(sc["crps"])
        pits.append(sc["pit"])
        residuals.append({"error": y - mu, "sd": sd})
    return sum(crps) / len(crps), pits, residuals


def run_cycle():
    # ── (1) score v1 — measure the model error against fact
    crps_v1, pit_v1, residuals = _score_batch(_MU_V1, _SD_V1, _Y)
    calib_v1 = calibration_summary(pit_v1)

    # ── (2) learn the correction from the residuals (full-step alpha=1 for a clean demo)
    upd = propose_update({"cell_state": {}, "model_id": "m-loop", "from_version": 1,
                          "residuals": residuals, "runtime": "baien-edge", "alpha": 1.0})
    assert upd["cell_state"]["phase"] == UpdatePhase.PROPOSED.value
    p = upd["cell_state"]["proposed"]
    bias_corr, var_infl = p["biasCorr"], p["varInfl"]

    # ── (3) apply the learned weights → v2 forecasts, re-score against the SAME facts
    v2 = [apply_correction(mu, _SD_V1, bias_corr, var_infl) for mu in _MU_V1]
    mus_v2 = [m for m, _ in v2]
    sd_v2 = v2[0][1]
    crps_v2, pit_v2, _ = _score_batch(mus_v2, sd_v2, _Y)
    calib_v2 = calibration_summary(pit_v2)

    # ── (4) the model improved on BOTH axes
    skill_self = skill_score(crps_v2, crps_v1)      # vs its own previous version

    # ── (5) gate the promotion (skill vs the v1 baseline, new calibration, signed)
    promote_signed = review_promotion({
        "cell_state": {}, "model_id": "m-loop", "to_version": p["toVersion"],
        "skill": skill_self, "deviation": calib_v2["deviation"], "deviation_max": calib_v1["deviation"],
        "signed_by": "did:web:etzhayyim.com:member:operator",
    })
    promote_unsigned = review_promotion({
        "cell_state": {}, "model_id": "m-loop", "to_version": p["toVersion"],
        "skill": skill_self, "deviation": calib_v2["deviation"], "deviation_max": calib_v1["deviation"],
        "signed_by": "",
    })
    return {
        "crps_v1": crps_v1, "crps_v2": crps_v2, "skill_self": skill_self,
        "pit_mean_v1": calib_v1["pit_mean"], "pit_mean_v2": calib_v2["pit_mean"],
        "bias_corr": bias_corr, "var_infl": var_infl,
        "promote_signed": promote_signed["cell_state"]["phase"],
        "promote_unsigned": promote_unsigned["cell_state"]["phase"],
    }


# ───────────────────────────── assertions ─────────────────────────────
def test_residuals_recover_the_systematic_bias():
    r = run_cycle()
    assert abs(r["bias_corr"] - 2.02) < 0.05   # learned the ~+2 under-forecast


def test_error_strictly_decreases_after_correction():
    r = run_cycle()
    assert r["crps_v2"] < r["crps_v1"]
    assert r["crps_v2"] < 0.6 * r["crps_v1"]   # a large, unambiguous improvement


def test_calibration_improves_toward_uniform():
    r = run_cycle()
    # v1 is overconfident+biased → PIT mean pinned high; v2 lands near 0.5
    assert abs(r["pit_mean_v2"] - 0.5) < abs(r["pit_mean_v1"] - 0.5)
    assert abs(r["pit_mean_v2"] - 0.5) < 0.2


def test_self_skill_is_positive():
    r = run_cycle()
    assert r["skill_self"] > 0


def test_promotion_clears_when_signed():
    r = run_cycle()
    assert r["promote_signed"] == GatePhase.CLEARED.value


def test_promotion_refused_without_member_signature():
    r = run_cycle()
    assert r["promote_unsigned"] == GatePhase.REFUSED.value   # no-server-key (G9)


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    r = run_cycle()
    print(f"learning_loop: {len(fns)}/{len(fns)} tests passed")
    print(f"  CRPS {r['crps_v1']:.3f} → {r['crps_v2']:.3f}  (self-skill +{r['skill_self']:.2f}); "
          f"PIT mean {r['pit_mean_v1']:.2f} → {r['pit_mean_v2']:.2f}; "
          f"learned bias +{r['bias_corr']:.2f}, var×{r['var_infl']:.2f}; "
          f"promote signed={r['promote_signed']} unsigned={r['promote_unsigned']}")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
