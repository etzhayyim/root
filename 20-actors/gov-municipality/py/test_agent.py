#!/usr/bin/env python3
"""gov-municipality 官 — agent gate tests (offline, no kotoba host, no network, no LLM).

ADR-2605250800. Exercises the permitting constitutional gates: member consent (G19),
jurisdiction authority (G18), permit submission (G1/G15/G16), inspection scheduling,
final sign-off (G3/G18), and the USDC + tithe settlement (G17).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_member_consent_valid() -> bool:
    result = agent.enforce_member_consent("did:web:etzhayyim.com:member:test")
    return _check("valid member DID accepted (G19)", result["ok"] is True)


def test_member_consent_invalid() -> bool:
    result = agent.enforce_member_consent("not-a-did")
    return _check("invalid DID rejected (G19)", result["ok"] is False)


def test_jurisdiction_authority_valid() -> bool:
    result = agent.enforce_jurisdiction_authority("JP-13", "did:web:tokyo.jp:director:d001")
    return _check("valid authority DID accepted (G18)", result["ok"] is True)


def test_jurisdiction_authority_invalid() -> bool:
    result = agent.enforce_jurisdiction_authority("JP-13", "not-a-did")
    return _check("invalid authority DID rejected (G18)", result["ok"] is False)


def test_parse_project_scope_tokyo() -> bool:
    result = agent.parse_project_scope("Tokyo-13-Shibuya-1-2-3", "residential", 150000000, 800.0)
    return _check("Tokyo site parsed to JP-13 (G1)", result.get("jurisdiction_id") == "JP-13")


def test_parse_project_scope_invalid() -> bool:
    result = agent.parse_project_scope("", "residential", 0, 0.0)
    return _check("invalid siteId rejected", "error" in result)


def test_form_permit_application_valid() -> bool:
    result = agent.form_permit_application("did:web:etzhayyim.com:member:test", "JP-13", "residential",
                                           "3-story apartment building")
    return _check("permit application formed", ":permit-application/id" in result)


def test_form_permit_application_invalid_did() -> bool:
    result = agent.form_permit_application("not-a-did", "JP-13", "residential", "scope")
    return _check("invalid member DID in application rejected (G19)", result.get("blocked") is True)


def test_handle_permit_submission_valid() -> bool:
    result = agent.handle_permit_submission({
        "member_did": "did:web:etzhayyim.com:member:test",
        "site_id": "Tokyo-13-Shibuya-1-2-3",
        "building_type": "residential",
        "total_cost": 150000000,
        "gfa_m2": 800.0,
        "scope": "3-story apartment building"
    })
    return _check("permit submission created (G1/G15/G16/G19)",
                  "permit_application_id" in result and result.get("state") == "submitted")


def test_handle_permit_submission_consent_fail() -> bool:
    result = agent.handle_permit_submission({
        "member_did": "invalid",
        "site_id": "Tokyo-13-Shibuya-1-2-3",
        "building_type": "residential",
        "total_cost": 150000000,
        "gfa_m2": 800.0,
        "scope": "scope"
    })
    return _check("permit submission blocked on invalid member DID (G19)", result.get("blocked") is True)


def test_schedule_inspection_phases() -> bool:
    result = agent.schedule_inspection_phases("JP-13", "pa.JP-13.test.1")
    phases = result.get(":inspection-schedule/phases", "").split(",")
    return _check("5 inspection phases scheduled (G1/G15/G16)",
                  len(phases) == 5 and "foundation" in phases)


def test_handle_inspection_scheduling_valid() -> bool:
    result = agent.handle_inspection_scheduling({
        "permit_application_id": "pa.JP-13.test.1",
        "jurisdiction_id": "JP-13"
    })
    return _check("inspection schedule created",
                  "inspection_schedule_id" in result and result.get("state") == "inspecting")


def test_validate_inspection_results_all_pass() -> bool:
    results = [
        {"phase": "foundation", "result": "pass"},
        {"phase": "structural", "result": "pass"},
        {"phase": "mep", "result": "conditional"}
    ]
    valid = agent.validate_inspection_results(results)
    return _check("all phases ≥ conditional accepted", valid["ok"] is True)


def test_validate_inspection_results_has_fail() -> bool:
    results = [
        {"phase": "foundation", "result": "pass"},
        {"phase": "structural", "result": "fail"}
    ]
    valid = agent.validate_inspection_results(results)
    return _check("phase failure rejected", valid["ok"] is False)


def test_emit_occupancy_clearance_valid() -> bool:
    result = agent.emit_occupancy_clearance("pa.JP-13.test.1", "JP-13",
                                            "did:web:tokyo.jp:director:d001",
                                            "sig_base64_001")
    return _check("occupancy clearance issued (G3/G18)",
                  ":permits-finalized-record/id" in result)


def test_emit_occupancy_clearance_no_signature() -> bool:
    result = agent.emit_occupancy_clearance("pa.JP-13.test.1", "JP-13",
                                            "did:web:tokyo.jp:director:d001", "")
    return _check("occupancy clearance blocked without signature (G18)", result.get("blocked") is True)


def test_handle_final_sign_off_approved() -> bool:
    result = agent.handle_final_sign_off({
        "permit_application_id": "pa.JP-13.test.1",
        "jurisdiction_id": "JP-13",
        "inspection_results": [{"phase": "foundation", "result": "pass"}],
        "authority_did": "did:web:tokyo.jp:director:d001",
        "authority_signature": "sig001"
    })
    return _check("final sign-off approved (G3/G16/G18)",
                  result.get("state") == "finalized" and "permits_finalized_record_id" in result)


def test_settlement_tithe_split() -> bool:
    s = agent.build_settlement_intent(500000)
    return _check("10% tithe + stops at intent (G17/G18)",
                  s["titheMinor"] == 50000 and s["state"] == "intent"
                  and s["rail"] == "usdc-base-l2")


def test_settlement_executed_with_sig() -> bool:
    s = agent.build_settlement_intent(1000000, authority_sig_ref="0xsig")
    return _check("settlement executes only with authority signature (G18)", s["state"] == "executed")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"gov-municipality agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
