#!/usr/bin/env python3
"""mitooshi 見通し — forecast viz builder tests (build_forecast_viz.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_build_forecast_viz.py
    python3 test_build_forecast_viz.py

Verifies the fan-chart payload mirrors methods/forecast.py (single source of truth) AND is
charter-clean: it carries a DISTRIBUTION (bands), never a point (G1), routed to :resilience
(G2); the rendered HTML inlines the payload (self-contained, file://, no external fetch).
"""
from __future__ import annotations
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "methods"))

import build_forecast_viz as b  # noqa: E402


def test_payload_has_history_and_forecast():
    p = b.build_payload(target_at=7)
    assert len(p["history"]) == 7
    assert p["forecast"] is not None


def test_forecast_is_distribution_not_point_g1():
    fc = b.build_payload()["forecast"]
    assert fc["pointAsserted"] is False           # G1
    assert fc["distKind"] == "gaussian"
    # bands are a real interval around the mean (a distribution, not a line)
    assert fc["band95"][0] < fc["mean"] < fc["band95"][1]
    assert fc["band68"][0] >= fc["band95"][0] and fc["band68"][1] <= fc["band95"][1]


def test_forecast_use_is_resilience_g2():
    fc = b.build_payload()["forecast"]
    assert fc["use"] == ":resilience"             # G2 — never a trade/price target


def test_forecast_is_leak_free_info_before_target():
    fc = b.build_payload(target_at=7)["forecast"]
    assert fc["infoAsOf"] < 7                      # G5 — built from history strictly before target


def test_climatology_mean_matches_history():
    # history t=1..6 = -0.45,-0.30,-0.15,0.0,0.15,0.30 → mean -0.075 (climatology, leak-free)
    fc = b.build_payload(target_at=7)["forecast"]
    assert fc["mean"] == -0.075


def test_html_inlines_payload_self_contained():
    p = b.build_payload()
    html = b.render_html(p, _HERE / "_template.htm")
    assert "/*__PAYLOAD__*/null" not in html      # placeholder replaced
    assert "s-jan-4901777300443-supply-demand" in html
    # the only http(s) literal allowed in the JS is the inert SVG namespace, not a fetch
    js = html.split("<script>")[1]
    leftover = js.replace("http://www.w3.org/2000/svg", "")
    assert "http://" not in leftover and "https://" not in leftover


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"build_forecast_viz.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
