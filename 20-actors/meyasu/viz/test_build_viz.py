#!/usr/bin/env python3
"""meyasu 目安 — dashboard viz builder tests (build_viz_data.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_build_viz.py
    python3 test_build_viz.py

Verifies the dashboard payload mirrors agent.handle_fuse (single source of truth) and is
charter-clean: carries the G1 buyer-transparency intent, routes attention cards to a planner
(G4), and the rendered HTML inlines the payload (self-contained, file://, no external fetch).
"""
from __future__ import annotations
import json
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "py"))
import build_viz_data as b  # noqa: E402

_SEED = _HERE.parent / "kotoba" / "seed.json"


def _payload():
    items = json.loads(_SEED.read_text(encoding="utf-8"))["items"]
    return b.build_payload(items)


def test_one_card_per_seed_item():
    p = _payload()
    assert len(p["cards"]) == 3
    assert p["intent"] == "buyer-transparency+supply-resilience"   # G1


def test_attention_card_routes_to_resilience_planner():
    cards = {c["productId"]: c for c in _payload()["cards"]}
    # rising SD (now 0.12 → mean 0.42) + notable spread → tightening + attention
    a = cards["jan_4901777300443"]
    assert a["trajectory"] == "tightening"
    assert a["attention"] is True
    assert a["routeTo"] == "danjo"


def test_non_attention_routes_to_buyer_planner():
    cards = {c["productId"]: c for c in _payload()["cards"]}
    b2 = cards["gtin_04901234567894"]      # easing → not attention
    assert b2["attention"] is False
    assert b2["routeTo"] == "okaimono"


def test_forecast_band_present():
    a = {c["productId"]: c for c in _payload()["cards"]}["jan_4901777300443"]
    assert a["forecastBand"] == [0.24, 0.6]   # mean 0.42 ± sd 0.18


def test_html_inlines_payload_self_contained():
    html = b.render_html(_payload(), _HERE / "_template.htm")
    assert "/*__PAYLOAD__*/null" not in html
    assert "jan_4901777300443" in html
    js = html.split("<script>")[1]
    assert "http://" not in js and "https://" not in js   # no external fetch in JS


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"build_viz.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
