#!/usr/bin/env python3
"""meyasu 目安 — unified arbitrage orchestrator tests.

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_agent.py
    python3 test_agent.py

Verifies the fusion + publication invariants that keep the integration charter-clean:

  - fuses kakaku spread/SD + mitooshi forecast into one card (no math re-implemented)
  - G2: a point-asserted / speculative forecast is REFUSED, never fused
  - trajectory = forecast mean vs present index (tightening/easing/stable)
  - attention = notable spread AND tightening → routed to the resilience planner (G4)
  - publish is aggregate-first (G3), no nudge/affiliate (G1), operator-gated (no-server-key)
"""
import agent


def _item(notable=True, mean=0.5, now=0.1, point=False, use=":resilience"):
    return {
        "productId": "jan_x",
        "kakaku": {"spread": 700, "spreadFraction": 0.22, "notable": notable,
                   "cheapestMerchant": "a_com", "supplyDemandIndex": now, "reading": "balanced"},
        "mitooshi": {"mean": mean, "sd": 0.3, "target": 7, "use": use, "pointAsserted": point},
    }


# ── fuse ──────────────────────────────────────────────────────────────────
def test_fuse_combines_spread_and_forecast():
    out = agent.handle_fuse({"items": [_item()]})
    assert len(out["cards"]) == 1
    c = out["cards"][0]
    assert c["priceSpread"] == 700
    assert c["forecastBand"] == [0.2, 0.8]          # mean 0.5 ± sd 0.3
    assert c["intent"] == "buyer-transparency+supply-resilience"


def test_trajectory_tightening_easing_stable():
    assert agent._trajectory(0.1, 0.5) == "tightening"
    assert agent._trajectory(0.5, 0.1) == "easing"
    assert agent._trajectory(0.3, 0.32) == "stable"


def test_attention_routes_to_resilience_planner():
    c = agent.handle_fuse({"items": [_item(notable=True, mean=0.6, now=0.1)]})["cards"][0]
    assert c["attention"] is True
    assert c["routeTo"] == agent.RESILIENCE_PLANNER  # danjo


def test_non_attention_routes_to_buyer_planner():
    # notable spread but NOT tightening → buyer side
    c = agent.handle_fuse({"items": [_item(notable=True, mean=0.1, now=0.1)]})["cards"][0]
    assert c["attention"] is False
    assert c["routeTo"] == agent.BUYER_PLANNER       # okaimono


def test_fuse_refuses_point_asserted_forecast_g2():
    out = agent.handle_fuse({"items": [_item(point=True)]})
    assert out["cards"] == []
    assert "G2" in out["refused"][0]["reason"]


def test_fuse_refuses_speculative_use_g2():
    out = agent.handle_fuse({"items": [_item(use=":trade")]})
    assert out["cards"] == []
    assert "G2" in out["refused"][0]["reason"]


def test_fuse_without_forecast_is_ok():
    item = {"productId": "p", "kakaku": {"spread": 100, "spreadFraction": 0.1,
            "notable": False, "supplyDemandIndex": 0.0, "reading": "balanced"}}
    c = agent.handle_fuse({"items": [item]})["cards"][0]
    assert c["forecastBand"] is None
    assert c["trajectory"] == "unknown"


# ── publish ───────────────────────────────────────────────────────────────
def test_publish_default_draft_aggregate_no_nudge():
    cards = agent.handle_fuse({"items": [_item()]})["cards"]
    out = agent.handle_publish({"cards": cards})
    p = out["posts"][0]
    assert p["state"] == "draft"                     # operator-gated
    assert p["shape"] == "aggregate"                 # G3
    assert p["nudge"] is False and p["affiliate"] is False  # G1
    assert out["aggregateSharePct"] == 100


def test_publish_attention_card_creates_handoff():
    cards = agent.handle_fuse({"items": [_item(notable=True, mean=0.6, now=0.1)]})["cards"]
    out = agent.handle_publish({"cards": cards})
    assert len(out["handoffs"]) == 1
    assert out["handoffs"][0]["routeTo"] == agent.RESILIENCE_PLANNER


def test_publish_posts_with_operator():
    cards = agent.handle_fuse({"items": [_item()]})["cards"]
    out = agent.handle_publish({"cards": cards, "operatorRef": "op:1"})
    assert out["posts"][0]["state"] == "posted"
    assert out["broadcast"] is True


# ── persist (kotoba Datoms, no-server-key) ────────────────────────────────
def test_persist_emits_card_datoms():
    cards = agent.handle_fuse({"items": [_item()]})["cards"]
    out = agent.handle_persist({"cards": cards, "observedAt": "2026-06-07T00:00:00Z"})
    assert out["datomCount"] > 0
    kinds = {d[1] for d in out["datoms"]}
    assert ":meyasu.card/product" in kinds
    assert ":meyasu.card/intent" in kinds


def test_persist_writes_forecast_as_band_not_point_g1():
    cards = agent.handle_fuse({"items": [_item(mean=0.5, now=0.1)]})["cards"]
    out = agent.handle_persist({"cards": cards, "observedAt": "t"})
    attrs = {d[1] for d in out["datoms"]}
    assert ":meyasu.card/forecast-band-lo" in attrs
    assert ":meyasu.card/forecast-band-hi" in attrs
    # there is NO point-value attribute — a band, never a point (G1/G2)
    assert not any("forecast-point" in a or a == ":meyasu.card/forecast-mean" for a in attrs)


def test_persist_no_server_key_tx_only_without_operator():
    cards = agent.handle_fuse({"items": [_item()]})["cards"]
    out = agent.handle_persist({"cards": cards})
    assert out["writeState"] == "tx-only"          # no-server-key: returned, not written


def test_persist_commits_with_operator():
    cards = agent.handle_fuse({"items": [_item()]})["cards"]
    out = agent.handle_persist({"cards": cards, "operatorRef": "op:1"})
    assert out["writeState"] == "committed"


def test_card_to_datoms_uses_observed_at_in_id():
    card = agent.handle_fuse({"items": [_item()]})["cards"][0]
    datoms = agent.card_to_datoms(card, "2026-06-07T12:00:00Z")
    eid = datoms[0][0]
    assert "2026-06-07T12:00:00Z" in eid and eid.startswith("meyasu.card.")
