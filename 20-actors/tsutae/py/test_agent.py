#!/usr/bin/env python3
"""tsutae 伝え — agent cell tests (no kotoba host, no network, no LLM).

ADR-2605261300 R0 scaffold. Exercises the handlers + settlement + constitutional
gates offline (Murakumo-only invariant untouched; G16).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_device_order_success() -> bool:
    out = agent.handle_device_order({
        "buyer_did": "did:web:member.example.etzhayyim.com",
        "specs": "handheld", "soc": "StarFive-JH7110",
        "initial_state": "placed", "sbt_active": True})
    return _check("device order created with active SBT + open SoC",
                  "device_order" in out and out["device_order"][":device-order/state"] == "placed")


def test_device_order_sbt_inactive() -> bool:
    out = agent.handle_device_order({"buyer_did": "did:web:m", "sbt_active": False})
    return _check("device order refused if SBT inactive (N9)",
                  "error" in out and out["state"] == "cancelled")


def test_device_order_rejects_proprietary_soc() -> bool:
    out = agent.handle_device_order({
        "buyer_did": "did:web:m", "soc": "Snapdragon-8-Gen3", "sbt_active": True})
    return _check("device order refused for proprietary SoC (G9/N1)",
                  "error" in out and out["state"] == "cancelled")


def test_is_open_soc() -> bool:
    ok = all(agent.is_open_soc(s) for s in ("StarFive-JH7110", "iwakura", "SiFive-HiFive-Unmatched"))
    bad = not any(agent.is_open_soc(s) for s in ("Snapdragon-8", "Apple-A17", "Exynos-2400"))
    return _check("is_open_soc accepts RISC-V, rejects proprietary", ok and bad)


def test_production_progress_no_cid() -> bool:
    out = agent.handle_production_progress({"order_id": "do.t.1", "stage": "pcb-smt"})
    return _check("production progress without CID → no attestation",
                  "production_progress" in out and out["attestation"] is None)


def test_production_progress_with_cid() -> bool:
    out = agent.handle_production_progress({
        "order_id": "do.t.2", "stage": "display-attachment", "cid": "bafkreicid", "details": "laminated"})
    return _check("production progress with CID → attestation",
                  out.get("attestation", {}).get(":attestation/cid") == "bafkreicid")


def test_production_progress_unknown_stage() -> bool:
    out = agent.handle_production_progress({"order_id": "do.t.3", "stage": "frame-weld"})
    return _check("unknown (truck) stage rejected", "error" in out)


def test_quality_pass_fail_rework() -> bool:
    base = {"order_id": "do.t.4", "inspector_did": "did:web:insp", "current_order_state": "qc"}
    p = agent.handle_quality({**base, "result": "pass"})
    f = agent.handle_quality({**base, "result": "fail", "defects": ["dead pixel"]})
    r = agent.handle_quality({**base, "result": "rework"})
    return _check("quality pass→ready / fail→cancelled / rework→in-production",
                  p["new_order_state"] == "ready" and f["new_order_state"] == "cancelled"
                  and r["new_order_state"] == "in-production")


def test_device_attestation_quorum() -> bool:
    ok = agent.handle_device_attestation({
        "order_id": "do.t.5", "serial": "SN0001",
        "robot_signers": ["did:web:etzhayyim.com:mimi-1", "did:web:etzhayyim.com:otete-1"],
        "bom_lineage_cids": ["bafpcb", "bafchassis"]})
    bad = agent.handle_device_attestation({
        "order_id": "do.t.5", "serial": "SN0002", "robot_signers": ["did:web:etzhayyim.com:mimi-1"]})
    return _check("device attestation needs ≥2 robot signers (G4) + mints DID (G14)",
                  ok.get("accept") is True
                  and ok["device_record"][":device/did"] == "did:web:etzhayyim.com:tsutae:device:SN0001"
                  and bad.get("accept") is False)


def test_settlement_tithe_split() -> bool:
    out = agent.build_settlement_intent(60_000_000)
    return _check("10% tithe split + state intent",
                  out["titheMinor"] == 6_000_000 and out["factoryPayoutMinor"] == 54_000_000
                  and out["state"] == "intent")


def test_settlement_executed_with_sig() -> bool:
    out = agent.build_settlement_intent(50_000_000, buyer_sig_ref="0xdeadbeef")
    return _check("settlement executed with buyer signature (G15)",
                  out["state"] == "executed" and out["buyerSigRef"] == "0xdeadbeef")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"tsutae agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
