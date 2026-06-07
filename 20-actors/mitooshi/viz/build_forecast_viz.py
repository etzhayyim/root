#!/usr/bin/env python3
"""mitooshi 見通し — forecast distribution visualization payload + viewer.

ADR-2606051800 × ADR-2605091200. Renders the kakaku → bridge → forecast pipeline as a
DISTRIBUTION fan chart: the historical as-of observation trail of a kakaku supply-demand
series plus the forecast distribution (mean ± 1σ / ± 2σ bands) at the target horizon.

The math is computed once in methods/{bridge_kakaku, forecast}.py (single source of truth);
this tool only shapes the payload and inlines it into the viewer. Emits:

  1. viz/forecast-viz.json  — the viz payload (data CONTRACT; browser-native, ADR-2606013600)
  2. viz/forecast-viz.htm   — a SELF-CONTAINED viewer (payload inlined; opens via file://)

CONSTITUTIONAL: the chart shows a DISTRIBUTION (band), never a single line target (G1
point_asserted=false), routed to :resilience (G2) — it is the charter-clean inverse of a
price-target chart. No trade, no advice, no prophecy.

stdlib only. Usage:
    python3 viz/build_forecast_viz.py
"""
from __future__ import annotations
import json
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "methods"))
from bridge_kakaku import bridge_kakaku  # noqa: E402
from forecast import forecast_next, series_histories  # noqa: E402

_PID = "jan_4901777300443"
_SID = "s-jan-4901777300443-supply-demand"


def build_payload(target_at: int = 7) -> dict:
    """Bridge a rising kakaku supply-demand series over t=1..target_at, forecast the next
    value as a Gaussian distribution, and shape both into a fan-chart payload."""
    series: dict = {}
    obs: list = []
    for t in range(1, target_at + 1):
        idx = round(-0.6 + 0.15 * t, 4)
        b = bridge_kakaku([{":sd/product": _PID, ":sd/index": idx}], observed_at=t)
        series.update(b["series"])
        obs.extend(b["obs"])
    rows = list(series.values()) + obs
    hist = series_histories(rows)[_SID]
    history = [{"t": t, "v": round(v, 4)} for t, v in hist]

    fc = forecast_next(_SID, hist, target_at)   # built from history strictly before target
    forecast = None
    if fc is not None:
        mean, sd = fc.mean, fc.sd
        forecast = {
            "target": target_at,
            "infoAsOf": fc.info_as_of,
            "mean": mean,
            "sd": sd,
            "band68": [round(mean - sd, 4), round(mean + sd, 4)],
            "band95": [round(mean - 2 * sd, 4), round(mean + 2 * sd, 4)],
            "distKind": fc.dist_kind,
            "use": fc.use,                       # :resilience (G2)
            "pointAsserted": fc.point_asserted,  # False (G1)
        }
    return {
        "generator": "mitooshi/viz/build_forecast_viz.py",
        "series": _SID,
        "unit": "supply-demand-index",
        "history": history,
        "forecast": forecast,
        "intent": "distribution-forecast → resilience (never a point, never a trade)",
    }


def render_html(payload: dict, template: pathlib.Path) -> str:
    return template.read_text(encoding="utf-8").replace(
        "/*__PAYLOAD__*/null", json.dumps(payload, ensure_ascii=False))


def main(argv: list[str]) -> int:
    payload = build_payload()
    (_HERE / "forecast-viz.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    tpl = _HERE / "_template.htm"
    if tpl.exists():
        (_HERE / "forecast-viz.htm").write_text(render_html(payload, tpl))
    f = payload["forecast"]
    print(f"mitooshi forecast viz: {len(payload['history'])} obs → forecast "
          f"N({f['mean']}, {f['sd']}) at t={f['target']} [{f['use']}, "
          f"point={f['pointAsserted']}] → forecast-viz.json"
          + (" + forecast-viz.htm" if tpl.exists() else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
