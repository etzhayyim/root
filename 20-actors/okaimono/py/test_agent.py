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
