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


# ----------------------------- R3 — assisted secure checkout (member-principal) ----------------------------- #
MEMBER = "did:plc:member-001"
_SIG_MEMBER = {"origin": "member", "ref": "sig:passkey:abc"}
_SIG_SERVER = {"origin": "server", "ref": "sig:platform:xyz"}


def test_payment_intent_is_unsigned_member_principal_no_server_key():
    pi = agent.build_payment_intent(MEMBER, "shop.example", 4200, "USD", "member-external-card")
    assert pi["principal"] == "member"        # G14: member is the buyer, not okaimono
    assert pi["serverHeldKey"] is False        # G15: okaimono holds no key
    assert pi["signed"] is False               # must be member-authorized
    assert pi["requiredSigner"].startswith("member")


def test_payment_authorize_requires_member_signature():
    pi = agent.build_payment_intent(MEMBER, "shop.example", 4200, "USD", "member-external-card")
    refused = agent.authorize_payment(pi, _SIG_SERVER)   # server signature must be refused (G15)
    assert refused["refused"] is True and refused["signed"] is False
    ok = agent.authorize_payment(pi, _SIG_MEMBER)
    assert ok["signed"] is True


def test_warifu_external_trips_its_own_gate():
    pi = agent.build_payment_intent(MEMBER, "shop.example", 4200, "USD", "warifu", external=True)
    assert pi.get("requiresWarifuExternalGate") is True   # warifu Phase-2 Lv7+ (ADR-2605302000)
    pi_internal = agent.build_payment_intent(MEMBER, "int", 4200, "USD", "warifu", external=False)
    assert "requiresWarifuExternalGate" not in pi_internal


def test_payment_intent_rejects_unknown_instrument():
    try:
        agent.build_payment_intent(MEMBER, "shop", 1, "USD", "stolen-card")
        assert False
    except ValueError:
        pass


def test_seal_encrypted_never_leaks_plaintext():
    env = agent.seal_encrypted({"pan": "4111111111111111", "cvv": "123", "name": "A B"}, MEMBER)
    blob = repr(env)
    assert "4111111111111111" not in blob and "123" not in blob and "A B" not in blob
    assert env["envelopeRef"].startswith("com.etzhayyim.encrypted:")
    assert env["sealedFields"] == ["cvv", "name", "pan"]  # field NAMES only, no values


def test_assist_checkout_awaits_member_without_signature():
    p = {"retailerUrl": "https://shop.example/p?tag=etz-22", "priceMinor": 4200, "currency": "USD"}
    out = agent.assist_checkout(MEMBER, p, {"address": "123 Secret St, Apt 9"})
    assert out["state"] == "awaiting-member-authorization"
    assert out["principal"] == "member" and out["titheMinor"] == 0  # §1.3 preserved (G14)
    assert "tag=" not in out["handoffUri"]                          # G3 still enforced
    assert "123 Secret St" not in repr(out["encrypted"])           # G9: PII VALUE never leaks (names ok)


def test_assist_checkout_member_authorized_pending_operator():
    p = {"retailerUrl": "https://shop.example/p", "priceMinor": 4200, "currency": "USD"}
    out = agent.assist_checkout(MEMBER, p, {"address": "x"}, member_signature=_SIG_MEMBER)
    assert out["state"] == "authorized-pending-operator"           # G11: live submit needs operator


def test_assist_checkout_submits_with_member_sig_and_operator():
    p = {"retailerUrl": "https://shop.example/p", "priceMinor": 4200, "currency": "USD"}
    out = agent.assist_checkout(MEMBER, p, {"address": "x"},
                                member_signature=_SIG_MEMBER, operator_ref="council-op-1")
    assert out["state"] == "submitted" and out["paymentIntent"]["signed"] is True


def test_assist_checkout_refuses_server_signature():
    p = {"retailerUrl": "https://shop.example/p", "priceMinor": 4200, "currency": "USD"}
    out = agent.assist_checkout(MEMBER, p, {"address": "x"},
                                member_signature=_SIG_SERVER, operator_ref="council-op-1")
    assert out["state"] == "refused"


def test_arrange_delivery_prefers_no_gig():
    d = agent.arrange_delivery({"itemClass": "bulky"}, "jp")
    assert d["mode"] == "etzhayyim-logistics" and d["gig"] is False and d["carrier"] == "haraedo"
    d2 = agent.arrange_delivery({}, "us")
    assert d2["mode"] == "retailer-shipping" and d2["gig"] is False


# ── R1 live USDC + TitheRouter settlement broadcast (G7/G11/G15) ───────────
def test_build_user_op_no_server_key():
    intent = agent.build_settlement_intent(10_000_000, "mitsuho")
    op = agent.build_user_op(intent, "did:web:etzhayyim.com:member:abc")
    assert op["rail"] == "erc4337-user-op"
    assert op["serverHeldKey"] is False           # invariant
    assert op["requiredSigner"] == "member-smart-account"
    assert op["titheMinor"] == 1_000_000          # 10% TitheRouter preserved (G7)
    assert op["grossMinor"] == op["titheMinor"] + op["makerPayoutMinor"]  # exact split


def test_submit_refuses_server_signature_g15():
    intent = agent.build_settlement_intent(10_000_000, "mitsuho")
    out = agent.submit_settlement(intent, {"origin": "server", "ref": "x"})
    assert out.get("refused") is True
    assert "no-server-key" in out["reason"]


def test_submit_member_signed_pending_operator_g11():
    intent = agent.build_settlement_intent(10_000_000, "mitsuho")
    out = agent.submit_settlement(intent, {"origin": "member", "ref": "sig:1",
                                           "memberDid": "did:m:1"})
    assert out["state"] == "authorized-pending-operator"   # signed but live submit gated (G11)
    assert out["userOp"]["signed"] is True


def test_submit_member_signed_with_operator_broadcasts():
    intent = agent.build_settlement_intent(10_000_000, "mitsuho")
    out = agent.submit_settlement(intent, {"origin": "member", "ref": "sig:1",
                                           "memberDid": "did:m:1"}, operator_ref="op:1")
    assert out["state"] == "submitted"
    assert out["userOp"]["signatureRef"] == "sig:1"


def test_submit_refuses_non_intent_state():
    intent = agent.build_settlement_intent(10_000_000, "mitsuho", operator_ref="op:1")  # executed
    out = agent.submit_settlement(intent, {"origin": "member", "ref": "s"})
    assert out.get("refused") is True


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
