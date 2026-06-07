#!/usr/bin/env python3
"""Cohort end-to-end: kakaku → mitooshi → meyasu (the whole price-intel pipeline).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_cohort_e2e.py
    python3 test_cohort_e2e.py

Proves the five-actor cohort actually composes across actor boundaries with every gate held:

  kakaku   offers → handle_arbitrage (spread) + handle_supply_demand (index now)
  mitooshi bridge_kakaku (sd → series) → forecast_next (distribution, :resilience)
  meyasu   handle_fuse ({kakaku, mitooshi} → unified card) → handle_publish (aggregate post)

This is the capstone that verifies the cohort's coverage is real code, not per-actor claims.
Each actor's agent.py is loaded under a UNIQUE module name (both kakaku and meyasu name their
module `agent`), so the import does not collide.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

_ACTORS = pathlib.Path(__file__).resolve().parents[2]   # …/20-actors
sys.path.insert(0, str(_ACTORS / "mitooshi" / "methods"))   # bridge_kakaku, forecast (unique names)


def _load(mod_name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)  # type: ignore
    return mod


kakaku = _load("kakaku_agent", _ACTORS / "kakaku" / "py" / "agent.py")
meyasu = _load("meyasu_agent", _ACTORS / "meyasu" / "py" / "agent.py")
import bridge_kakaku  # noqa: E402  (mitooshi/methods)
import forecast       # noqa: E402  (mitooshi/methods)

_PID = "jan_4901777300443"
_SID = "s-jan-4901777300443-supply-demand"


def _kakaku_card():
    """kakaku leg: cross-merchant offers → spread + present supply/demand index."""
    offers = [
        {"merchantId": "a_com", "price": 3000, "shippingFee": 200, "availability": "out-of-stock", "region": "jp"},
        {"merchantId": "b_com", "price": 2700, "shippingFee": 1200, "availability": "backorder", "region": "us"},
        {"merchantId": "c_com", "price": 3500, "shippingFee": 0, "availability": "out-of-stock", "region": "jp"},
    ]
    # a rising price history → demand pressure (drives supply/demand index up)
    history = [{"observedAt": f"2026-06-0{t}", "totalPrice": 3000 + 60 * t} for t in range(1, 8)]
    arb = kakaku.handle_arbitrage({"offers": offers})
    sd = kakaku.handle_supply_demand({"offers": offers, "priceHistory": history})
    return {
        "spread": arb["spread"], "spreadFraction": arb["spreadFraction"], "notable": arb["notable"],
        "cheapestMerchant": arb["cheapestMerchant"],
        "supplyDemandIndex": sd["supplyDemandIndex"], "reading": sd["reading"],
    }


def _mitooshi_forecast(now_index: float):
    """mitooshi leg: bridge a rising supply-demand series → forecast a distribution."""
    series: dict = {}
    obs: list = []
    for t in range(1, 8):
        idx = round(now_index + 0.12 * (t - 7), 4)   # ends at now_index at t=7, rising
        b = bridge_kakaku.bridge_kakaku([{":sd/product": _PID, ":sd/index": idx}], observed_at=t)
        series.update(b["series"]); obs.extend(b["obs"])
    fc = forecast.forecast_next(_SID, forecast.series_histories(list(series.values()) + obs)[_SID],
                                target_at=8)
    return {"mean": fc.mean, "sd": fc.sd, "target": 8, "use": fc.use, "pointAsserted": fc.point_asserted}


def test_full_cohort_composes_into_one_card():
    k = _kakaku_card()
    f = _mitooshi_forecast(k["supplyDemandIndex"])
    fused = meyasu.handle_fuse({"items": [{"productId": _PID, "kakaku": k, "mitooshi": f}]})
    assert len(fused["cards"]) == 1
    c = fused["cards"][0]
    # the card carries data from ALL THREE actors
    assert c["priceSpread"] == k["spread"]                       # kakaku
    assert c["supplyDemandNow"] == k["supplyDemandIndex"]        # kakaku
    assert c["forecastBand"] is not None                         # mitooshi
    assert c["intent"] == "buyer-transparency+supply-resilience" # meyasu G1


def test_cohort_publish_is_aggregate_draft():
    k = _kakaku_card()
    f = _mitooshi_forecast(k["supplyDemandIndex"])
    cards = meyasu.handle_fuse({"items": [{"productId": _PID, "kakaku": k, "mitooshi": f}]})["cards"]
    out = meyasu.handle_publish({"cards": cards})
    assert out["posts"][0]["state"] == "draft"      # operator-gated (no-server-key)
    assert out["posts"][0]["shape"] == "aggregate"  # G3
    assert out["aggregateSharePct"] == 100


def test_cohort_forecast_is_distribution_not_point_g2():
    f = _mitooshi_forecast(0.1)
    assert f["pointAsserted"] is False               # mitooshi G1
    assert f["use"] == ":resilience"                 # mitooshi G2
    # and meyasu would refuse it if it were a point assertion
    bad = meyasu.handle_fuse({"items": [{"productId": _PID, "kakaku": _kakaku_card(),
                                         "mitooshi": {**f, "pointAsserted": True}}]})
    assert bad["cards"] == [] and "G2" in bad["refused"][0]["reason"]


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"cohort_e2e.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
