#!/usr/bin/env python3
"""kakaku 価格 — viz builder tests (build_viz_data.py + kakaku_edn.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_build_viz.py
    python3 test_build_viz.py

Verifies the viz payload is correct AND charter-clean: it mirrors agent.py's math
(single source of truth), carries the G2 buyer-transparency intent, and the rendered
HTML inlines the payload (self-contained, file:// — no external fetch).
"""
from __future__ import annotations
import json
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "methods"))
sys.path.insert(0, str(_HERE.parent / "py"))

import build_viz_data as b  # noqa: E402
from kakaku_edn import classify, load_edn  # noqa: E402

_SEED = _HERE.parent / "kotoba" / "seed.edn"


def _payload():
    products, merchants, offers, ph = classify(load_edn(_SEED))
    return b.build_payload(products, merchants, offers, ph)


def test_one_card_per_product_with_offers():
    p = _payload()
    assert len(p["cards"]) == 1
    card = p["cards"][0]
    assert card["productId"] == "jan_4901777300443"
    assert len(card["offers"]) == 3


def test_spread_matches_agent_math():
    card = _payload()["cards"][0]
    # seed landed: a_com 3200, b_com 3900, c_com 3500 → spread 700, cheapest a_com
    assert card["minLanded"] == 3200 and card["maxLanded"] == 3900
    assert card["spread"] == 700
    assert card["cheapestMerchant"] == "a_com"


def test_offers_sorted_cheapest_first():
    offers = _payload()["cards"][0]["offers"]
    landeds = [o["landed"] for o in offers]
    assert landeds == sorted(landeds)
    assert offers[0]["merchantId"] == "a_com"


def test_by_region_min_landed():
    card = _payload()["cards"][0]
    # jp: a_com(3200) & c_com(3500) → min 3200; us: b_com(3900)
    assert card["byRegion"]["jp"]["minLanded"] == 3200
    assert card["byRegion"]["us"]["minLanded"] == 3900


def test_supply_demand_present():
    card = _payload()["cards"][0]
    assert card["reading"] in ("scarcity", "balanced", "glut")
    assert -1.0 <= card["supplyDemandIndex"] <= 1.0


def test_g2_intent_is_carried_not_a_trade():
    p = _payload()
    assert p["intent"] == "buyer-transparency+supply-resilience"
    assert p["cards"][0]["intent"] == "buyer-transparency+supply-resilience"


def test_html_inlines_payload_self_contained():
    tpl = _HERE / "_template.htm"
    html = b.render_html(_payload(), tpl)
    assert "/*__PAYLOAD__*/null" not in html        # placeholder was replaced
    assert "jan_4901777300443" in html              # data is inlined
    assert "http://" not in html and "https://" not in html.split("<script>")[1]  # no external fetch in JS


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"build_viz.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
