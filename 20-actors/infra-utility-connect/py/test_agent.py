#!/usr/bin/env python3
"""infra-utility-connect — agent gate tests (offline, no kotoba host, no network, no LLM).

ADR-2605250900. Exercises the utility-activation constitutional gates: provider
signature validation (G3), SLA compliance (G5), PII encryption (G11), and the
USDC + tithe settlement (G8/G9).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_provider_sig_validated() -> bool:
    result = agent.validate_provider_sig("Tokyo Water Bureau", "did:web:tokyo-water.go.jp")
    return _check("provider signature validated (G3)", result["ok"] is True)


def test_provider_sig_missing() -> bool:
    result = agent.validate_provider_sig("Tokyo Water Bureau", "")
    return _check("missing provider signature rejected (G3)", result["ok"] is False)


def test_provider_sig_invalid_format() -> bool:
    result = agent.validate_provider_sig("Tokyo Water Bureau", "invalid-format-123")
    return _check("invalid sig format rejected (G3)", result["ok"] is False)


def test_sla_compliance_ok() -> bool:
    result = agent.check_sla_compliance("2026-06-02T00:00:00Z", "2026-06-05T00:00:00Z")
    return _check("SLA window valid (G5)", result["ok"] is True)


def test_sla_missing_date() -> bool:
    result = agent.check_sla_compliance("", "2026-06-05T00:00:00Z")
    return _check("missing SLA date rejected (G5)", result["ok"] is False)


def test_sla_invalid_format() -> bool:
    result = agent.check_sla_compliance("2026-06-02", "2026-06-05")
    return _check("non-ISO-8601 format rejected (G5)", result["ok"] is False)


def test_pii_masked() -> bool:
    result = agent.mask_pii("Tanaka Yuki", "ACC-1234567890")
    return _check("PII masked for encryption (G11)",
                  "customer_masked" in result and "account_masked" in result)


def test_pii_missing_name() -> bool:
    result = agent.mask_pii("", "ACC-1234567890")
    return _check("missing customer name rejected (G11)", result.get("blocked") is True)


def test_service_request_mep_incomplete() -> bool:
    incomplete_mep = {"water": True, "gas": False, "electric": True}
    result = agent.handle_service_request(incomplete_mep, "35.6595,139.7004")
    return _check("incomplete MEP signoff rejected", result.get("blocked") is True)


def test_service_request_all_providers() -> bool:
    complete_mep = {"water": True, "gas": True, "electric": True, "telecom": True}
    result = agent.handle_service_request(complete_mep, "35.6595,139.7004")
    return _check("complete MEP generates 4 service requests",
                  len(result.get("service_requests", [])) == 4)


def test_provider_approval_signatures() -> bool:
    result = agent.handle_provider_approval(["req.water.001", "req.gas.001"])
    approvals = result.get("approvals", [])
    return _check("provider approvals validated (G3)",
                  all(a["status"] == "approved" for a in approvals))


def test_meter_install_calibrated() -> bool:
    result = agent.handle_meter_install(["appr.water.001"])
    meters = result.get("meters", [])
    return _check("meters returned calibrated (G2)",
                  len(meters) > 0 and meters[0]["status"] == "calibrated")


def test_activation_all_live() -> bool:
    result = agent.handle_activation_test([{"serial": "WM-JP-2026-001"}])
    return _check("all 4 services confirmed live",
                  result["water_live"] and result["gas_live"] and
                  result["electric_live"] and result["telecom_live"] and
                  result["result"] == "pass")


def test_settlement_tithe_split() -> bool:
    s = agent.build_settlement_intent(100_000_000)
    return _check("10% tithe + stops at intent (G8/G9)",
                  s["titheMinor"] == 10_000_000 and s["state"] == "intent"
                  and s["rail"] == "usdc-base-l2")


def test_settlement_executed_with_sig() -> bool:
    s = agent.build_settlement_intent(100_000_000, buyer_sig_ref="did:key:z6Mk123")
    return _check("settlement executes only with member signature (G9)", s["state"] == "executed")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"infra-utility-connect agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
