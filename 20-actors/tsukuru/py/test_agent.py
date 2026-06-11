#!/usr/bin/env python3
"""tsukuru 作 — agent cell tests (no kotoba host, no network, no LLM).

ADR-2605202800 Phase 4. Exercises the 4 handlers + settlement + gates with injected
functions so the suite runs offline (Murakumo-only invariant untouched; G5).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_discover_ranks_by_capability() -> bool:
    out = agent.handle_discover({
        "spec": "5-axis CNC aluminum bracket, anodized black",
        "factories": [
            {"factoryDid": "inj", "capabilities": ["injection-molding"]},
            {"factoryDid": "cnc", "capabilities": ["cnc-5axis", "anodizing"]},
        ],
    })
    return _check("discover puts best capability match first",
                  out["candidates"][0]["factoryDid"] == "cnc")


def test_sbt_gate_refuses_non_member() -> bool:
    order = agent.create_production_order("did:web:stranger", "f1", "bto", "x", sbt_registry={})
    return _check("non-SBT buyer refused (§3/G2)", order["state"] == "refused")


def test_unknown_mode_refused() -> bool:
    reg = {"did:web:m": {"active": True}}
    order = agent.create_production_order("did:web:m", "f1", "zzz", "x", sbt_registry=reg)
    return _check("unknown fulfillment mode refused", order["state"] == "refused")


def test_compliance_no_auto_pass_when_unresolved() -> bool:
    out = agent.handle_compliance({"factoryDid": "f1", "buyerCountry": "JP", "factoryCountry": "TW"})
    return _check("unresolved screening never auto-passes (G16)",
                  out["complianceState"] == "pending")


def test_compliance_denied_party_rejects() -> bool:
    out = agent.handle_compliance(
        {"factoryDid": "bad"},
        screen_fn=lambda did: {"clear": False, "note": "OFAC SDN"},
    )
    return _check("denied-party hit rejects (G16)", out["complianceState"] == "rejected")


def test_advance_blocked_until_compliance_passed() -> bool:
    order = {"state": "placed", "complianceState": "pending"}
    out = agent.advance_order(order)
    return _check("dispatch blocked until compliance passes (G16)",
                  out.get("blocked") is not None and out["state"] == "placed")


def test_advance_proceeds_after_compliance() -> bool:
    order = {"state": "placed", "complianceState": "passed"}
    out = agent.advance_order(order)
    return _check("advances to dispatched after compliance pass",
                  out["state"] == "dispatched")


def test_qc_fail_diverts_to_quarantine() -> bool:
    out = agent.handle_qc({"order": {"state": "qc"}, "defects": ["crack"], "reworkable": False})
    return _check("QC fail → quarantine (G17)", out["order"]["state"] == "quarantine")


def test_qc_pass_marks_ready() -> bool:
    out = agent.handle_qc({"order": {"state": "qc"}, "defects": []})
    return _check("QC pass → ready", out["order"]["state"] == "ready"
                  and out["quality"]["result"] == "pass")


def test_settlement_tithe_split() -> bool:
    s = agent.build_settlement_intent(500_000_000)
    return _check("10% tithe split + stops at intent (G7/G11)",
                  s["titheMinor"] == 50_000_000
                  and s["factoryPayoutMinor"] == 450_000_000
                  and s["state"] == "intent"
                  and s["rail"] == "usdc-base-l2")


def test_settlement_executed_only_with_member_sig() -> bool:
    s = agent.build_settlement_intent(1_000_000, buyer_sig_ref="0xmembersig")
    return _check("settlement executes only with member signature (G15)",
                  s["state"] == "executed")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"tsukuru agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
