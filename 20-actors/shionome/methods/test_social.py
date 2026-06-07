"""test_social.py — 潮目 (shionome) dry-run social post + no-trade body scan. ADR-2606072200."""
from __future__ import annotations

import social
from _t import expect_raises, run

_SRC = ["https://fred.stlouisfed.org/", "https://www.ici.org/research"]
_NET = [{"bucket": "us-equities", "label": "US equities", "net": 13.1, "inflow": 23.2, "outflow": 10.1},
        {"bucket": "us-govt-bonds", "label": "US Treasuries", "net": -21.7, "inflow": 0.0, "outflow": 21.7}]
_ROT = [{"from": "us-govt-bonds", "from_label": "US Treasuries", "to": "us-equities",
         "to_label": "US equities", "magnitude": 12.4}]
_REGIME = {"regime": "risk-on", "risk_net": 27.3, "safe_net": -26.6, "no_trade_notice": True}


def test_netflow_post_pins_invariants():
    p = social.draft_netflow_post(_NET, _SRC)
    assert p[":post/status"] == ":dry-run"
    assert p[":post/is-mirror"] is True
    assert p[":post/no-trade-notice"] is True
    assert p[":post/server-held-key"] is False


def test_netflow_post_body_has_disclaimer():
    p = social.draft_netflow_post(_NET, _SRC)
    assert "トレードはしない" in p[":post/body"]


def test_rotation_post_ok():
    p = social.draft_rotation_post(_ROT, _SRC)
    assert "US Treasuries" in p[":post/body"] and p[":post/status"] == ":dry-run"


def test_regime_post_states_descriptor():
    p = social.draft_regime_post(_REGIME, _SRC)
    assert "risk-on" in p[":post/body"]
    assert "助言ではありません" in p[":post/body"]


def test_post_requires_two_sources_g3():
    expect_raises(lambda: social.draft_netflow_post(_NET, ["only-one"]), contains="G3")


def test_post_refuses_denied_source():
    expect_raises(lambda: social.draft_netflow_post(_NET, ["bloomberg terminal", "x"]), contains="Rider")


def test_no_trade_guard_blocks_buy():
    expect_raises(lambda: social._guard_no_trade("you should buy equities"), contains="G2")


def test_no_trade_guard_blocks_japanese():
    expect_raises(lambda: social._guard_no_trade("目標株価は5000円"), contains="G2")


def test_no_trade_guard_allows_disclaimer():
    # the disclaimer NAMES the prohibited acts; it must not trip the guard
    social._guard_no_trade(social.DISCLAIMER)


def test_build_live_refuses_g8():
    expect_raises(lambda: social.build_live(), contains="G8")


def test_empty_rotation_post_safe():
    p = social.draft_rotation_post([], _SRC)
    assert p[":post/status"] == ":dry-run"


if __name__ == "__main__":
    run("social", [(n, f) for n, f in sorted(globals().items())
                   if n.startswith("test_") and callable(f)])
