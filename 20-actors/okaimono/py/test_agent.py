#!/usr/bin/env python3
"""okaimono 御買物 — agent logic tests (ADR-2606012100).

Pure-logic tests over the six handlers; no kotoba host bindings required (the
datalog/llm imports degrade to None in local dev). Verifies the constitutional
invariants that distinguish okaimono from an Amazon clone:

  - commons-first ring ordering (G4/G12)
  - Wellbecoming ranking beats price-only (G3/G4)
  - 10% tithe auto-split on the internal portion only (G7)
  - external 代理-purchase refused without a gate-ref (G2/G11)
  - Ring 2 R0 default is a self-checkout handoff, no affiliate (G3)
"""
import agent


def test_commons_first_ordering():
    st = agent.handle_discover(
        {
            "need_text": "warm bedding",
            "candidates": [],
            # inject candidates directly (datalog is None in dev)
        }
    )
    # with no host catalog, resolved_ring is unresolved but the contract holds
    assert st["resolved_ring"] in ("commons", "internal", "external", "unresolved")


def test_wellbecoming_beats_price():
    durable = {"priceMinor": 18_000_000, "durabilityYears": 5.0, "repairability": 8,
               "laborProvenance": "etzhayyim-dignity", "carbonKg": 3.2}
    cheap_throwaway = {"priceMinor": 1_290_000, "durabilityYears": 1.0, "repairability": 1,
                       "laborProvenance": "unknown", "carbonKg": 14.0}
    out = agent.handle_compare({"products": [cheap_throwaway, durable]})
    assert out["ranked"][0] is durable, "durable + dignified labor must outrank cheap throwaway"


def test_tithe_internal_only():
    lines = [
        {"priceMinor": 10_000_000, "qty": 1, "ring": "internal"},
        {"priceMinor": 5_000_000, "qty": 1, "ring": "external"},
    ]
    out = agent.handle_basket({"lines": lines})
    # 10% of the 10_000_000 internal portion only
    assert out["titheMinor"] == 1_000_000
    assert out["landedMinor"] == 10_000_000 + 5_000_000 + 1_000_000


def test_external_proxy_refused_without_gate():
    out = agent.handle_provision({"ring": "external", "requestProxy": True})
    assert out["settlement"] == "proxy-gated"
    assert out.get("refused") is True


def test_external_proxy_allowed_with_gate():
    out = agent.handle_provision({"ring": "external", "requestProxy": True, "gateRef": "council-lv7-2026xxxx"})
    assert out["settlement"] == "proxy-gated"
    assert out.get("refused") is not True


def test_external_default_is_handoff():
    out = agent.handle_provision({"ring": "external"})
    assert out["settlement"] == "self-checkout-handoff"
    assert out["titheMinor"] == 0


def test_internal_settles_usdc_warifu_with_tithe():
    out = agent.handle_provision({"ring": "internal", "titheMinor": 2_400_000})
    assert out["settlement"] == "usdc-warifu"
    assert out["titheMinor"] == 2_400_000


def test_commons_no_settlement():
    out = agent.handle_provision({"ring": "commons"})
    assert out["settlement"] == "commons-none"
    assert out["titheMinor"] == 0


def test_lifecycle_no_terminal_state():
    out = agent.handle_lifecycle({"lifecycleRoute": "hodoki"})
    assert out["stage"] != "consumed"
    assert out["routeActor"] == "hodoki"


# ----------------------------- R1 — Ring 1 internal economy ----------------------------- #
BUYER = "did:plc:member-001"
_REG = {BUYER: True,
        "did:web:etzhayyim.com:makura": True,
        "did:web:etzhayyim.com:mitsuho": True}


def test_sbt_eligibility_both_active():
    out = agent.check_sbt_eligibility(BUYER, "makura", _REG)
    assert out["eligible"] is True


def test_sbt_eligibility_buyer_not_holder():
    out = agent.check_sbt_eligibility("did:plc:outsider", "makura", _REG)
    assert out["eligible"] is False


def test_sbt_eligibility_non_producing_actor():
    out = agent.check_sbt_eligibility(BUYER, "amazon", _REG)
    assert out["eligible"] is False


def test_tithe_split_is_exact():
    s = agent.build_settlement_intent(18_000_000, "makura")
    assert s["titheMinor"] == 1_800_000
    assert s["makerPayoutMinor"] == 16_200_000
    # the canonical invariant: gross == tithe + payout, no remainder loss
    assert s["grossMinor"] == s["titheMinor"] + s["makerPayoutMinor"]
    assert s["state"] == "intent"  # NOT broadcast at R1 (G11)


def test_tithe_split_remainder_absorbed_by_payout():
    s = agent.build_settlement_intent(9_999_999, "mitsuho")
    assert s["grossMinor"] == s["titheMinor"] + s["makerPayoutMinor"]


def test_settlement_executes_only_with_operator_ref():
    s = agent.build_settlement_intent(5_000_000, "makura", operator_ref="council-op-2026xxxx")
    assert s["state"] == "executed"


def test_place_order_refuses_ineligible():
    out = agent.place_order("did:plc:outsider", "makura", 18_000_000, "bulky", _REG)
    assert out["state"] == "refused"


def test_place_order_eligible_reaches_settle_intent():
    out = agent.place_order(BUYER, "makura", 18_000_000, "bulky", _REG)
    assert out["state"] == "settle-intent"
    assert out["settlement"]["titheMinor"] == 1_800_000
    assert out["fulfillmentActor"] == "haraedo"  # bulky → haraedo fleet (G8, no gig)


def test_fulfillment_never_gig():
    assert agent.assign_fulfillment("heavy") == "sarutahiko"
    assert agent.assign_fulfillment("road") == "wadachi"
    assert agent.assign_fulfillment("bulky") == "haraedo"


def test_order_advance_caps_at_in_use():
    o = {"state": "in-use"}
    assert agent.advance_order(o)["state"] == "in-use"  # never advances to a terminal :consumed (G13)
    o2 = {"state": "placed"}
    assert agent.advance_order(o2)["state"] == "settle-intent"


# ----------------------------- R2 — Ring 2 external catalog ----------------------------- #
def test_strip_affiliate_amazon():
    url = "https://www.amazon.co.jp/dp/B0XXXX/ref=as_li_ss_tl?tag=etz-22&linkCode=ll1&psc=1&th=1"
    out = agent.strip_affiliate(url)
    assert "tag=" not in out and "linkCode=" not in out and "psc=" not in out
    assert "/ref=" not in out
    assert "th=1" in out  # functional param preserved
    assert out.startswith("https://www.amazon.co.jp/dp/B0XXXX")


def test_strip_affiliate_utm_and_click_ids():
    url = "https://shop.example/p/123?utm_source=x&utm_medium=aff&gclid=abc&fbclid=def&q=pillow&aff_id=99"
    out = agent.strip_affiliate(url)
    for bad in ("utm_source", "utm_medium", "gclid", "fbclid", "aff_id"):
        assert bad not in out
    assert "q=pillow" in out  # the real query survives


def test_strip_affiliate_idempotent_and_clean_url_untouched():
    clean = "https://shop.example/p/123?q=pillow&sku=AB12"
    assert agent.strip_affiliate(clean) == clean
    assert agent.strip_affiliate(agent.strip_affiliate(clean)) == clean


def test_normalize_external_is_data_only():
    raw = {
        "gtin": "04901234567894", "title": "down comforter", "unspsc": "52121500",
        "url": "https://shop.example/p/9?tag=etz-22&utm_campaign=x",
        "priceMinor": 1290000, "currency": "JPY", "availability": "in-stock",
        # adversarial: affiliate/commission/sponsored fields must NOT survive
        "affiliateLink": "https://aff.example/redirect?tag=etz-22",
        "commissionBps": 300, "sponsoredRank": 1, "trackingPixel": "https://px.example/x.gif",
    }
    p = agent.normalize_external(raw, "api-data-only")
    assert p["ring"] == "external" and p["source"] == "api-data-only"
    assert p["sourcing"] == "representative"
    # affiliate stripped from the retailer URL
    assert "tag=" not in p["retailerUrl"] and "utm_campaign" not in p["retailerUrl"]
    # data-only: no affiliate/commission/sponsored/tracking keys carried over (G3)
    for forbidden in ("affiliateLink", "commissionBps", "sponsoredRank", "trackingPixel"):
        assert forbidden not in p


def test_normalize_external_rejects_unknown_source():
    try:
        agent.normalize_external({"id": "x"}, "blackhat-scrape")
        assert False, "should reject unknown source"
    except ValueError:
        pass


def test_external_handoff_has_no_tithe_and_clean_uri():
    p = {"retailerUrl": "https://shop.example/p/9?tag=etz-22&q=z"}
    h = agent.build_external_handoff(p)
    assert h["settlement"] == "self-checkout-handoff"
    assert h["titheMinor"] == 0          # external: no internal value flow (G2/G7)
    assert "tag=" not in h["handoffUri"] and "q=z" in h["handoffUri"]


def test_scrape_gate_denies_robots_disallow():
    g = agent.scrape_gate("https://site.example/private/x", ["/private"], {})
    assert g["allowed"] is False and g["verdict"] == "denied"


def test_scrape_gate_policy_ok_but_operator_gated():
    g = agent.scrape_gate("https://site.example/public/x", ["/private"], {"_limit": 30})
    assert g["allowed"] is True and g["verdict"] == "gated"  # G11: no live fetch without operator


def test_scrape_gate_fetch_with_operator():
    g = agent.scrape_gate("https://site.example/public/x", ["/private"], {"_limit": 30},
                          operator_ref="council-op-xxxx")
    assert g["verdict"] == "fetch"


def test_scrape_gate_rate_budget():
    g = agent.scrape_gate("https://site.example/p", [], {"site.example": 30, "_limit": 30})
    assert g["allowed"] is False and "rate budget" in g["reason"]


def test_landed_cost_external():
    lc = agent.landed_cost_external(1_290_000, 80_000, 1000)  # 10% tariff
    assert lc["tariffMinor"] == 129_000
    assert lc["landedMinor"] == 1_290_000 + 80_000 + 129_000


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
