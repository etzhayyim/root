#!/usr/bin/env python3
"""Multi-round CONTINUAL-LEARNING / drift-tracking test for mitooshi 見通し.

Where test_learning_loop.py proves ONE recalibration step closes, this proves the loop is
STABLE when run continually: the EWMA bias correction converges to the true systematic bias
over many rounds, rejects per-round noise, and — critically — RE-converges when the world
drifts (a regime change), so the model keeps tracking instead of getting stuck. That is the
"継続学習 + drift 監視" half of the architecture.

Each round feeds a small batch of residuals (the model's raw systematic error + zero-mean
noise) to online_update.propose_update, threading the previous round's correction in as the
prior. c_t = (1-alpha)·c_{t-1} + alpha·mean_err  →  geometric convergence to the true bias.

Run:  python3 test_continual_learning.py
"""
from __future__ import annotations

import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT / "methods"))
sys.path.insert(0, str(_ROOT / "cells"))

from score import gaussian_crps  # noqa: E402
from online_update.state_machine import UpdatePhase, propose_update  # noqa: E402

# zero-mean noise pattern (deterministic — no RNG, reproducible)
_NOISE = [-0.2, 0.1, -0.1, 0.2, 0.0]
_RAW_MU = 10.0   # the uncorrected model's forecast; the truth is _RAW_MU + true_bias
_SD = 1.0
_ALPHA = 0.4


def _round(true_bias: float, prior_bias: float, prior_var_infl: float):
    errs = [{"error": true_bias + d, "sd": _SD} for d in _NOISE]
    out = propose_update({"cell_state": {}, "model_id": "m-cont", "from_version": 1,
                          "residuals": errs, "runtime": "baien-edge", "alpha": _ALPHA,
                          "prior_bias": prior_bias, "prior_var_infl": prior_var_infl})
    assert out["cell_state"]["phase"] == UpdatePhase.PROPOSED.value
    p = out["cell_state"]["proposed"]
    return p["biasCorr"], p["varInfl"]


def run_schedule(schedule):
    """schedule = list of (true_bias, n_rounds). Returns the full correction trajectory."""
    c, vi = 0.0, 1.0
    traj = []
    for true_bias, n in schedule:
        for _ in range(n):
            c, vi = _round(true_bias, c, vi)
            traj.append({"true_bias": true_bias, "c": c, "var_infl": vi,
                         "deployed_err": abs(true_bias - c),
                         "crps": gaussian_crps(_RAW_MU + c, _SD, _RAW_MU + true_bias)})
    return traj


# ───────────────────────────── assertions ─────────────────────────────
def test_converges_to_true_bias():
    traj = run_schedule([(2.0, 12)])
    assert abs(traj[-1]["c"] - 2.0) < 0.1          # converged to the true +2 bias


def test_error_decreases_monotonically_during_convergence():
    traj = run_schedule([(2.0, 12)])
    errs = [r["deployed_err"] for r in traj]
    assert all(errs[i + 1] <= errs[i] + 1e-9 for i in range(len(errs) - 1))
    # CRPS more than halves (it cannot reach 0 — a Gaussian has an irreducible ~0.23·sd
    # sharpness floor even at a perfect mean; the residual error is what we drive out)
    assert traj[-1]["crps"] < 0.5 * traj[0]["crps"]


def test_tracks_a_regime_drift():
    # converge at +2, then the world shifts to +4 — the corrector must re-converge.
    traj = run_schedule([(2.0, 12), (4.0, 12)])
    mid = traj[11]      # end of phase 1
    end = traj[-1]      # end of phase 2
    assert abs(mid["c"] - 2.0) < 0.1
    assert abs(end["c"] - 4.0) < 0.2               # re-converged, did NOT get stuck at 2


def test_variance_inflation_stays_bounded():
    traj = run_schedule([(2.0, 8), (4.0, 8)])
    assert all(0.25 <= r["var_infl"] <= 4.0 for r in traj)   # clamp holds every round


def test_noise_is_rejected_not_amplified():
    # the final correction is far closer to the true mean than any single noisy sample
    traj = run_schedule([(2.0, 15)])
    worst_single = max(abs(2.0 + d - 2.0) for d in _NOISE)   # = 0.2
    assert abs(traj[-1]["c"] - 2.0) < worst_single


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    traj = run_schedule([(2.0, 12), (4.0, 12)])
    print(f"continual_learning: {len(fns)}/{len(fns)} tests passed")
    print(f"  phase1 c→{traj[11]['c']:.3f} (true 2.0), phase2 c→{traj[-1]['c']:.3f} (true 4.0); "
          f"CRPS {traj[0]['crps']:.3f}→{traj[11]['crps']:.3f}→{traj[-1]['crps']:.3f} (drift re-tracked)")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
