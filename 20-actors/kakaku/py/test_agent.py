#!/usr/bin/env python3
"""kakaku 価格 — agent logic tests (ADR-2605091200 + CLAUDE.md data model).

Pure-logic tests over the six handlers; no kotoba host bindings required (the
datalog/llm imports degrade to None in local dev). Verifies the constitutional
invariants that distinguish kakaku from a trading / affiliate engine:

  - landed price (price + shipping) is the comparison basis, not sticker (G3)
  - too-good-to-be-true offers are flagged suspicious, never ranked #1
  - arbitrage reports a buyer/resilience SPREAD, never a trade (G2)
  - supply/demand is a bounded present-state index, not a forecast (G2)
  - intel + social default to aggregate-first, no affiliate, no nudge (G3/G4)
  - live social broadcast is operator-gated; default is a :draft (G11)
"""
import agent


_MERCHANTS = {
    "a_com": {"reputationScore": 0.9, "status": "active"},
    "b_com": {"reputationScore": 0.6, "status": "active"},
    "scam_com": {"reputationScore": 0.2, "status": "suspended"},
}


def _offers():
    return [
        {"merchantId": "a_com", "price": 10_000, "shippingFee": 500, "availability": "in-stock",
         "deliveryEtaDays": 2, "productUrl": "https://a.example/p", "region": "jp"},
        {"merchantId": "b_com", "price": 9_000, "shippingFee": 2_000, "availability": "in-stock",
         "deliveryEtaDays": 7, "productUrl": "https://b.example/p", "region": "us"},
    ]


# ── landed price + ranking ────────────────────────────────────────────────
def test_landed_price_includes_shipping():
    o = {"price": 9_000, "shippingFee": 2_000}
    assert agent.landed_price(o) == 11_000


def test_cheapest_ranks_on_landed_not_sticker():
    # b has the lower sticker (9000) but higher landed (11000); a wins on landed (10500)
    out = agent.handle_rank({"offers": _offers(), "merchants": _MERCHANTS})
    assert out["cheapest"]["merchantId"] == "a_com"


def test_suspicious_offer_flagged_and_excluded():
    offers = _offers() + [
        {"merchantId": "scam_com", "price": 100, "shippingFee": 0, "availability": "in-stock",
         "deliveryEtaDays": 1, "productUrl": "https://scam.example/p", "region": "jp"},
    ]
    out = agent.handle_rank({"offers": offers, "merchants": _MERCHANTS})
    sus_ids = {o["merchantId"] for o in out["suspicious"]}
    assert "scam_com" in sus_ids
    assert out["cheapest"]["merchantId"] != "scam_com"  # never ranked #1


# ── arbitrage / spread ────────────────────────────────────────────────────
def test_arbitrage_spread_and_regions():
    out = agent.handle_arbitrage({"offers": _offers()})
    # landed: a=10500, b=11000 → spread 500, cheapest a_com
    assert out["spread"] == 500
    assert out["cheapestMerchant"] == "a_com"
    assert set(out["byRegion"].keys()) == {"jp", "us"}
    assert out["intent"] == "buyer-transparency+supply-resilience"  # G2: never a trade


def test_arbitrage_notable_threshold():
    offers = [
        {"merchantId": "a_com", "price": 10_000, "shippingFee": 0, "availability": "in-stock"},
        {"merchantId": "b_com", "price": 13_000, "shippingFee": 0, "availability": "in-stock"},
    ]
    out = agent.handle_arbitrage({"offers": offers})
    assert out["spreadFraction"] == 0.3
    assert out["notable"] is True


def test_arbitrage_single_offer_is_zero():
    out = agent.handle_arbitrage({"offers": _offers()[:1]})
    assert out["spread"] == 0 and out["notable"] is False


# ── supply / demand ───────────────────────────────────────────────────────
def test_supply_demand_scarcity_when_low_stock_and_rising():
    offers = [
        {"merchantId": "a_com", "availability": "out-of-stock"},
        {"merchantId": "b_com", "availability": "backorder"},
    ]
    history = [
        {"observedAt": "2026-06-01", "totalPrice": 10_000},
        {"observedAt": "2026-06-07", "totalPrice": 13_000},
    ]
    out = agent.handle_supply_demand({"offers": offers, "priceHistory": history})
    assert out["reading"] == "scarcity"
    assert out["supplyDemandIndex"] > 0.33


def test_supply_demand_glut_when_ample_and_falling():
    offers = [
        {"merchantId": "a_com", "availability": "in-stock"},
        {"merchantId": "b_com", "availability": "in-stock"},
    ]
    history = [
        {"observedAt": "2026-06-01", "totalPrice": 13_000},
        {"observedAt": "2026-06-07", "totalPrice": 10_000},
    ]
    out = agent.handle_supply_demand({"offers": offers, "priceHistory": history})
    assert out["reading"] == "glut"
    assert out["supplyDemandIndex"] < -0.33


def test_supply_demand_index_bounded():
    offers = [{"merchantId": "a_com", "availability": "out-of-stock"}]
    history = [
        {"observedAt": "2026-06-01", "totalPrice": 1},
        {"observedAt": "2026-06-07", "totalPrice": 1_000_000},
    ]
    out = agent.handle_supply_demand({"offers": offers, "priceHistory": history})
    assert -1.0 <= out["supplyDemandIndex"] <= 1.0


# ── demand proxy ──────────────────────────────────────────────────────────
def test_demand_is_present_proxy_not_forecast():
    history = [
        {"merchantId": "a_com", "totalPrice": 10_000},
        {"merchantId": "b_com", "totalPrice": 11_000},
        {"merchantId": "a_com", "totalPrice": 10_500},
    ]
    out = agent.handle_demand({"priceHistory": history, "cohortObservationTotal": 12})
    assert out["observationCount"] == 3
    assert out["merchantCount"] == 2
    assert out["demandShare"] == 0.25
    assert out["kind"] == "present-interest-proxy"  # G2: not a forecast


# ── intel (aggregate-first) ───────────────────────────────────────────────
def test_intel_is_aggregate_first():
    out = agent.handle_intel({
        "productId": "jan_4901777300443",
        "offers": _offers(),
        "priceHistory": [{"observedAt": "2026-06-01", "totalPrice": 10_500}],
    })
    assert out["intel"]["shape"] == "aggregate"
    assert "spread" in out["intel"]


# ── social (charter-clean, operator-gated) ────────────────────────────────
def test_social_default_is_draft_and_clean():
    out = agent.handle_social({
        "productId": "jan_4901777300443",
        "offers": _offers(),
        "priceHistory": [{"observedAt": "2026-06-01", "totalPrice": 10_500}],
    })
    assert out["state"] == "draft"           # G11: no live broadcast without operator
    assert out["post"]["affiliate"] is False  # G3
    assert out["post"]["nudge"] is False      # G4
    assert out["post"]["shape"] == "aggregate"


def test_social_posts_with_operator():
    out = agent.handle_social({
        "productId": "jan_4901777300443",
        "offers": _offers(),
        "priceHistory": [{"observedAt": "2026-06-01", "totalPrice": 10_500}],
        "operatorRef": "op:council-attest-123",
    })
    assert out["state"] == "posted"


def test_social_weekly_ceiling_enforced():
    out = agent.handle_social({
        "productId": "x", "offers": _offers(), "priceHistory": [],
        "postsThisWeek": agent.SOCIAL_WEEKLY_CEILING,
        "operatorRef": "op:council-attest-123",
    })
    assert out.get("refused") is True
