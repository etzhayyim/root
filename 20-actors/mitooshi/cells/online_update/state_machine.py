"""Phase state machine for the mitooshi online_update (見通し) cell — the weight-correction
step. This is the "事実からモデル誤差・weight を修正・学習する" architecture, made concrete.

When facts arrive, the residuals they produce (error = y - mu, and the forecast sd that
was claimed) drive a recalibration of the model's parameters:

  bias_corr  = EWMA blend of the prior bias and the mean residual error
               → corrects SYSTEMATIC over/under-forecasting (the model's drift).
  var_infl   = empirical_residual_std / mean_claimed_sd
               → if the model was OVERCONFIDENT (residuals wider than its sd) var_infl > 1
                 and inflates the spread; if UNDERCONFIDENT, var_infl < 1 and sharpens it.
                 This is exactly the recalibration that makes the PIT histogram uniform.

The update PROPOSES a new model version; it does NOT promote it (calibration_gate does,
under G9 no-server-key). The real training substrate is baien federated edge (runtime
:baien-edge, ADR-2605242600/2630, edge envelope ADR-2605241900) — Murakumo-only, no
commercial GPU. At R0 this is the design-only reference recalibrator; the live federated
backward pass is G10-gated.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class UpdatePhase(Enum):
    INIT = "init"
    PROPOSED = "proposed"
    REJECTED = "rejected"


@dataclass
class UpdateState:
    phase: str = UpdatePhase.INIT.value
    model_id: str = ""
    from_version: int = 1
    alpha: float = 0.3                       # EWMA learning rate
    prior_bias: float = 0.0
    prior_var_infl: float = 1.0
    residuals: list = field(default_factory=list)  # [{error, sd}]
    trigger: str = "residual-drift"
    runtime: str = "baien-edge"
    proposed: dict = field(default_factory=dict)
    rejection: str = ""


def _state(d: dict[str, Any]) -> UpdateState:
    return UpdateState(**d.get("cell_state", {}))


def _norm(v: str | None) -> str:
    return (v or "").lstrip(":")


def propose_update(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.model_id = state.get("model_id", cs.model_id)
    cs.from_version = int(state.get("from_version", cs.from_version))
    cs.alpha = float(state.get("alpha", cs.alpha))
    cs.prior_bias = float(state.get("prior_bias", cs.prior_bias))
    cs.prior_var_infl = float(state.get("prior_var_infl", cs.prior_var_infl))
    cs.residuals = list(state.get("residuals", cs.residuals))
    cs.trigger = _norm(state.get("trigger", cs.trigger))
    cs.runtime = _norm(state.get("runtime", cs.runtime))

    # G8 — training runtime must be the edge envelope (no commercial GPU).
    if cs.runtime != "baien-edge":
        cs.rejection = f"G8: update runtime {cs.runtime!r} must be :baien-edge (Murakumo-only, no commercial GPU)"
        cs.phase = UpdatePhase.REJECTED.value
        return {"cell_state": cs.__dict__}

    errs = [float(r["error"]) for r in cs.residuals if "error" in r]
    sds = [float(r["sd"]) for r in cs.residuals if r.get("sd", 0) > 0]
    if not errs:
        cs.rejection = "no residuals to learn from; nothing to correct"
        cs.phase = UpdatePhase.REJECTED.value
        return {"cell_state": cs.__dict__}

    n = len(errs)
    mean_err = sum(errs) / n
    # EWMA bias correction: blend prior with the freshly measured systematic error.
    new_bias = (1.0 - cs.alpha) * cs.prior_bias + cs.alpha * mean_err

    # variance inflation = empirical residual std / mean claimed sd.
    if n >= 2:
        resid_var = sum((e - mean_err) ** 2 for e in errs) / (n - 1)
        resid_std = math.sqrt(resid_var) if resid_var > 0 else 0.0
    else:
        resid_std = abs(errs[0])
    mean_sd = (sum(sds) / len(sds)) if sds else 1.0
    raw_infl = resid_std / mean_sd if mean_sd > 0 else 1.0
    # EWMA the inflation too, and clamp to a sane band so one noisy batch can't blow up sd.
    new_var_infl = (1.0 - cs.alpha) * cs.prior_var_infl + cs.alpha * raw_infl
    new_var_infl = max(0.25, min(4.0, new_var_infl))

    cs.proposed = {
        "modelId": cs.model_id,
        "fromVersion": cs.from_version,
        "toVersion": cs.from_version + 1,
        "trigger": cs.trigger,
        "runtime": cs.runtime,
        "biasCorr": round(new_bias, 6),
        "varInfl": round(new_var_infl, 6),
        "meanError": round(mean_err, 6),
        "n": n,
        "promoted": False,  # promotion is calibration_gate's job, under G9
    }
    cs.rejection = ""
    cs.phase = UpdatePhase.PROPOSED.value
    return {"cell_state": cs.__dict__}


def apply_correction(mean: float, sd: float, bias_corr: float, var_infl: float) -> tuple[float, float]:
    """The corrected forecast under a proposed update: shift the mean by the learned bias,
    scale the spread by the learned inflation. (Used to re-forecast / re-backtest.)

    bias_corr = EWMA(mean residual error), error = y - mu, so a model that under-forecasts
    has bias_corr > 0 and the correction ADDS it back. Idempotent direction: applying the
    learned bias reduces the next batch's systematic error toward 0.
    """
    return mean + bias_corr, max(sd * var_infl, 1e-9)
