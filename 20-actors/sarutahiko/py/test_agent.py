#!/usr/bin/env python3
"""sarutahiko 猿田彦 — agent cell tests (no kotoba host, no network, no LLM).

ADR-2605252500 R0 scaffold. Exercises the handlers + settlement + gates with injected
functions so the suite runs offline (Murakumo-only invariant untouched; G16).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_handle_vehicle_order_success() -> bool:
    out = agent.handle_vehicle_order({
        "buyer_did": "did:web:member.example.etzhayyim.com",
        "specs": "Class-8 truck",
        "initial_state": "placed",
        "sbt_active": True
    })
    return _check("vehicle order created successfully with SBT active",
                  "vehicle_order" in out and out["vehicle_order"][":vehicle-order/state"] == "placed")


def test_handle_vehicle_order_sbt_inactive() -> bool:
    out = agent.handle_vehicle_order({
        "buyer_did": "did:web:member.example.etzhayyim.com",
        "specs": "Class-8 truck",
        "initial_state": "placed",
        "sbt_active": False
    })
    return _check("vehicle order refused if SBT inactive",
                  "error" in out and out["state"] == "cancelled")


def test_handle_production_progress_no_cid() -> bool:
    order_id = "vo.test.0001"
    stage = "frame-fabrication"
    out = agent.handle_production_progress({
        "order_id": order_id,
        "stage": stage,
        "details": "Steel cutting complete."
    })
    return _check("production progress recorded without CID",
                  "production_progress" in out and out["attestation"] is None)


def test_handle_production_progress_with_cid() -> bool:
    order_id = "vo.test.0002"
    stage = "paint-finishing"
    cid = "bafybeicidexample"
    out = agent.handle_production_progress({
        "order_id": order_id,
        "stage": stage,
        "cid": cid,
        "details": "White paint applied."
    })
    return _check("production progress recorded with CID and attestation",
                  "production_progress" in out and "attestation" in out and
                  out["attestation"][":attestation/cid"] == cid)


def test_handle_quality_pass() -> bool:
    order_id = "vo.test.0003"
    out = agent.handle_quality({
        "order_id": order_id,
        "result": "pass",
        "inspector_did": "did:web:inspector.example.com",
        "current_order_state": "qc"
    })
    return _check("quality pass marks order as ready",
                  "quality_record" in out and out["quality_record"][":quality/result"] == "pass" and
                  out["new_order_state"] == "ready")


def test_handle_quality_fail() -> bool:
    order_id = "vo.test.0004"
    out = agent.handle_quality({
        "order_id": order_id,
        "result": "fail",
        "defects": ["major dent"],
        "inspector_did": "did:web:inspector.example.com",
        "current_order_state": "qc"
    })
    return _check("quality fail marks order as cancelled",
                  "quality_record" in out and out["quality_record"][":quality/result"] == "fail" and
                  out["new_order_state"] == "cancelled")


def test_handle_quality_rework() -> bool:
    order_id = "vo.test.0005"
    out = agent.handle_quality({
        "order_id": order_id,
        "result": "rework",
        "defects": ["minor scratch"],
        "inspector_did": "did:web:inspector.example.com",
        "current_order_state": "qc"
    })
    return _check("quality rework marks order as in-production",
                  "quality_record" in out and out["quality_record"][":quality/result"] == "rework" and
                  out["new_order_state"] == "in-production")


def test_handle_vin_attestation_success() -> bool:
    order_id = "vo.test.0006"
    vin = "TESTVIN0000000001"
    out = agent.handle_vin_attestation({
        "order_id": order_id,
        "vin": vin,
        "emissions_audit_id": "emissions.test.0006",
        "silen_vehicle_review_id": "silen.test.0006",
        "attestation_ids": ["attest.test.0006.frame"]
    })
    return _check("VIN attestation creates vehicle record",
                  "vehicle_record" in out and out["vehicle_record"][":vehicle/vin"] == vin and
                  out["vehicle_record"][":vehicle/did"] == f"did:web:etzhayyim.com:sarutahiko:vehicle:{vin}")


def test_build_settlement_intent_tithe_split() -> bool:
    gross_minor = 1000000000 # 10,000 USDC
    out = agent.build_settlement_intent(gross_minor)
    return _check("10% tithe split is correct and state is intent",
                  out["titheMinor"] == 100000000 and
                  out["factoryPayoutMinor"] == 900000000 and
                  out["state"] == "intent")


def test_build_settlement_intent_executed_with_sig() -> bool:
    gross_minor = 500000000 # 5,000 USDC
    buyer_sig = "0xdeadbeef"
    out = agent.build_settlement_intent(gross_minor, buyer_sig_ref=buyer_sig)
    return _check("settlement state is executed with buyer signature",
                  out["state"] == "executed" and out["buyerSigRef"] == buyer_sig)


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"sarutahiko agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
