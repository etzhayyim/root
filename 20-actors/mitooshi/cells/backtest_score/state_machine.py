"""Phase state machine for the mitooshi backtest_score (見通し) cell.

The G5/G12 scoring reasoner. Given a batch of issued forecasts and the observations that
later realized them, it runs the leak-checked proper-scoring engine (methods/score.py) and
produces a scorecard datom — OR refuses the batch if any pairing would leak future
information (obs not strictly after the forecast's info-as-of) or asserts a point.

This is the coded core the backtest_score cell's .solve() will eventually drive; it does not
touch the live Datom log (that wiring is G10-gated). REFUSAL gate, not a clamp.
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# single source of truth for scoring — reuse methods/score.py
_METHODS = pathlib.Path(__file__).resolve().parents[2] / "methods"
if str(_METHODS) not in sys.path:
    sys.path.insert(0, str(_METHODS))
from score import (  # noqa: E402
    Forecast, Observation, calibration_summary, score_pair, skill_score,
)


class ScorePhase(Enum):
    INIT = "init"
    SCORED = "scored"
    REFUSED = "refused"


@dataclass
class ScoreState:
    phase: str = ScorePhase.INIT.value
    model_id: str = ""
    # pairs: [{forecast: {...Forecast fields...}, obs: {...Observation fields...}}]
    pairs: list = field(default_factory=list)
    baseline_primary: float = 0.0   # optional baseline score for skill (0 = skip)
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> ScoreState:
    return ScoreState(**d.get("cell_state", {}))


def _mk_forecast(d: dict) -> Forecast:
    return Forecast(
        fid=d.get("forecastId", d.get("fid", "?")),
        dist_kind=(d.get("distKind", d.get("dist_kind", "gaussian")) or "").lstrip(":"),
        info_as_of=int(d.get("infoAsOf", d.get("info_as_of", 0))),
        use=(d.get("use", "resilience") or "").lstrip(":"),
        point_asserted=bool(d.get("pointAsserted", d.get("point_asserted", False))),
        mean=float(d.get("mean", 0.0)), sd=float(d.get("sd", 1.0)),
        quantiles={float(k): float(v) for k, v in d.get("quantiles", {}).items()},
        probs={str(k): float(v) for k, v in d.get("probs", {}).items()},
        members=[float(x) for x in d.get("members", [])],
    )


def _mk_obs(d: dict) -> Observation:
    return Observation(
        oid=d.get("obsId", d.get("oid", "?")),
        observed_at=int(d.get("observedAt", d.get("observed_at", 0))),
        value=float(d.get("value", 0.0)), cls=d.get("class", d.get("cls", "")),
    )


def score_batch(state: dict[str, Any]) -> dict[str, Any]:
    """Leak-checked scoring of a forecast/observation batch → scorecard, or REFUSED."""
    cs = _state(state)
    cs.model_id = state.get("model_id", cs.model_id)
    cs.pairs = list(state.get("pairs", cs.pairs))
    cs.baseline_primary = float(state.get("baseline_primary", cs.baseline_primary))

    rows = []
    for p in cs.pairs:
        fc = _mk_forecast(p.get("forecast", {}))
        ob = _mk_obs(p.get("obs", {}))
        try:
            rows.append(score_pair(fc, ob))   # raises on G1 point / G2 use / G5 leak
        except ValueError as e:
            cs.refusal = str(e)
            cs.phase = ScorePhase.REFUSED.value
            return {"cell_state": cs.__dict__}

    if not rows:
        cs.refusal = "empty batch; nothing to score"
        cs.phase = ScorePhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    # aggregate the primary metric present (crps > pinball > brier)
    primary = next((m for m in ("crps", "pinball", "brier") if any(m in r for r in rows)), None)
    mean_primary = sum(r[primary] for r in rows if primary in r) / sum(1 for r in rows if primary in r)
    pit = [r["pit"] for r in rows if "pit" in r]
    calib = calibration_summary(pit)
    skill = skill_score(mean_primary, cs.baseline_primary) if cs.baseline_primary > 0 else None

    cs.payload = {
        "modelId": cs.model_id,
        "n": len(rows),
        "metric": primary,
        "meanScore": round(mean_primary, 6),
        "pitMean": round(calib["pit_mean"], 6),
        "calibDeviation": round(calib["deviation"], 6),
        "skill": (round(skill, 6) if skill is not None else None),
        "skilled": (bool(skill is not None and skill > 0)),
        "derived": True,
    }
    cs.refusal = ""
    cs.phase = ScorePhase.SCORED.value
    return {"cell_state": cs.__dict__}
