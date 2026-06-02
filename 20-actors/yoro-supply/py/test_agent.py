#!/usr/bin/env python3
"""yoro-supply 綾取供給 — agent cell tests (no kotoba host, no network, no LLM).

ADR-2605250850 Phase 2. Exercises the 5 handlers + settlement + gates with
injected functions so the suite runs offline (Murakumo-only invariant
untouched; G5).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_supplier_selection_ranks_by_capability() -> bool:
    out = agent.handle_supplier_selection({
        "materials": ["steel H-beam 200mm", "concrete 25 MPa"],
        "suppliers": [
            {"supplierDid": "concrete-s1", "capabilities": ["concrete",\
 "cement"], "charter-compliance": "passed"},
            {"supplierDid": "steel-s1", "capabilities": ["steel",\
 "h-beam"], "charter-compliance": "passed"},
        ],
    })
    return _check("supplier selection ranks by capability match",
                  len(out["candidates"]) == 2\
 and out["candidates"][0]["supplierDid"] in ["concrete-s1", "steel-s1"])


def test_sbt_gate_refuses_non_member() -> bool:
    order = agent.create_purchase_order("did:web:stranger", "s1",\
 ["steel"], [10], "2026-07-01", sbt_registry={})
    return _check("non-SBT member refused", order["state"] == "refused")


def test_sbt_gate_accepts_active_member() -> bool:
    reg = {"did:web:m": {"active": True}}
    order = agent.create_purchase_order("did:web:m", "s1", ["steel"],\
 [10], "2026-07-01", sbt_registry=reg)
    return _check("active SBT member accepted",\
 order["state"] == "placed")


def test_charter_screening_all_passed() -> bool:
    out = agent.handle_supplier_selection({
        "materials": ["materials"],
        "suppliers": [
            {"supplierDid": "s1", "capabilities": ["materials"],\
 "charter-compliance": "passed"},
        ],
    })
    return _check("charter screening marked passed",\
 out["charter_passed"] is True)


def test_charter_screening_one_failed() -> bool:
    out = agent.handle_supplier_selection({
        "materials": ["materials"],
        "suppliers": [
            {"supplierDid": "s1", "capabilities": ["materials"],\
 "charter-compliance": "passed"},
            {"supplierDid": "s2", "capabilities": ["materials"],\
 "charter-compliance": "failed"},
        ],
    })
    return _check("charter screening marked failed if any supplier fails",
                  out["charter_passed"] is False)


def test_manufacture_track_records_progress() -> bool:
    out = agent.handle_manufacture_track({
        "stage": "assembly",
        "pct": 45,
        "ipfsPin": "bafkqzzz",
        "now": "2026-06-01T12:00:00Z",
    })
    return _check("manufacture track records progress datom",
                  out["progress"]["stage"] == "assembly"\
 and out["progress"]["pct"] == 45)


def test_shipment_arranges_carrier() -> bool:
    out = agent.handle_shipment({
        "carrier": "FedEx",
        "trackingNumber": "1234567890",
        "eta": "2026-06-15T00:00:00Z",
        "customsCleared": True,
        "now": "2026-06-01T14:30:00Z",
    })
    return _check("shipment arranges carrier + tracking",
                  out["shipment"]["carrier"] == "FedEx"\
 and out["shipment"]["trackingNumber"] == "1234567890")


def test_delivery_verify_witness_quorum() -> bool:
    out = agent.handle_delivery_verify({
        "witnessDids": ["did:web:w1", "did:web:w2"],
        "qcResult": "pass",
        "now": "2026-06-15T10:00:00Z",
    })
    return _check("delivery verify records witness quorum",
                  len(out["attestation"]["witnessDids"]) == 2)


def test_settlement_tithe_split() -> bool:
    s = agent.build_settlement_intent(500_000_000)
    return _check("10% tithe split + stops at intent (G7)",
                  s["titheMinor"] == 50_000_000\
 and s["supplierPayoutMinor"] == 450_000_000\
 and s["state"] == "intent"\
 and s["rail"] == "usdc-base-l2")


def test_settlement_executed_only_with_member_sig() -> bool:
    s = agent.build_settlement_intent(1_000_000,\
 member_sig_ref="0xmembersig")
    return _check("settlement executes only with member signature (G11)",
                  s["state"] == "executed")


def test_settlement_stops_at_intent_without_sig() -> bool:
    s = agent.build_settlement_intent(1_000_000)
    return _check("settlement stops at intent without sig (G7/G11)",
                  s["state"] == "intent" and s["memberSigRef"] == "")


def main() -> int:
    tests = [v for k, v in sorted(globals().items())\
 if k.startswith("test_")]
    print(f"yoro-supply agent -- {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
