#!/usr/bin/env python3
"""hagukumi 育み — agent gate tests (offline, no kotoba host, no network, no LLM).

ADR-2605261030. Exercises the care constitutional gates: consent verification (G1/G3),
caregiver vetting (G4), emergency escalation (G5), work cap (G10), encrypted payload (G15),
pseudonym rotation (G16), guardian consent for children (G17), and USDC + tithe settlement
(G13/G14).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_consent_window_valid() -> bool:
    return _check("consent within session window accepted (G1/G3)",
                  agent.verify_consent_window("2026-05-20T10:00:00Z",
                                              "2026-05-20T08:00:00Z",
                                              "2026-05-20T12:00:00Z")["ok"] is True)


def test_consent_window_outside() -> bool:
    return _check("consent outside session window rejected (G1/G3)",
                  agent.verify_consent_window("2026-05-20T15:00:00Z",
                                              "2026-05-20T08:00:00Z",
                                              "2026-05-20T12:00:00Z")["ok"] is False)


def test_caregiver_attested_ok() -> bool:
    registry = {"did:web:hagukumi.etzhayyim.com:caregiver:alice": {"councilApprovalDate": "2026-05-15"}}
    return _check("Council-attested caregiver accepted (G4)",
                  agent.verify_caregiver_attested("did:web:hagukumi.etzhayyim.com:caregiver:alice", registry)["ok"] is True)


def test_caregiver_not_in_registry() -> bool:
    registry = {}
    return _check("caregiver not in registry rejected (G4)",
                  agent.verify_caregiver_attested("did:web:hagukumi.etzhayyim.com:caregiver:unknown", registry)["ok"] is False)


def test_caregiver_no_council_approval() -> bool:
    registry = {"did:web:hagukumi.etzhayyim.com:caregiver:bob": {}}
    return _check("caregiver without Council approval rejected (G4)",
                  agent.verify_caregiver_attested("did:web:hagukumi.etzhayyim.com:caregiver:bob", registry)["ok"] is False)


def test_emergency_escalation_triggered() -> bool:
    return _check("emergency keyword triggers mitate escalation (G5)",
                  agent.check_mitate_emergency_keywords("child fever 39C breathing difficulty",
                                                         ["fever", "breathing"])["escalate"] is True)


def test_emergency_escalation_not_triggered() -> bool:
    return _check("normal session no escalation (G5)",
                  agent.check_mitate_emergency_keywords("routine play and rest", ["fever"])["escalate"] is False)


def test_work_cap_under_limit() -> bool:
    work_log = {"did:caregiver:alice": {"cumulative_hours_24h": 8.0, "hours_since_last_session": 24.0}}
    return _check("caregiver within work cap accepted (G10)",
                  agent.check_caregiver_work_cap("did:caregiver:alice", work_log, 4.0)["ok"] is True)


def test_work_cap_over_cumulative() -> bool:
    work_log = {"did:caregiver:alice": {"cumulative_hours_24h": 10.0, "hours_since_last_session": 24.0}}
    return _check("caregiver over 12h cumulative rejected (G10)",
                  agent.check_caregiver_work_cap("did:caregiver:alice", work_log, 4.0)["ok"] is False)


def test_work_cap_insufficient_recovery() -> bool:
    work_log = {"did:caregiver:alice": {"cumulative_hours_24h": 4.0, "hours_since_last_session": 6.0}}
    return _check("caregiver insufficient recovery rejected (G10)",
                  agent.check_caregiver_work_cap("did:caregiver:alice", work_log, 2.0)["ok"] is False)


def test_encrypted_payload_valid() -> bool:
    return _check("valid encrypted payload CID accepted (G15)",
                  agent.verify_encrypted_payload("ipfs://QmXChaCha20Encrypted")["ok"] is True)


def test_encrypted_payload_missing() -> bool:
    return _check("missing encrypted payload rejected (G15)",
                  agent.verify_encrypted_payload("")["ok"] is False)


def test_pseudonym_rotation_needed() -> bool:
    result = agent.rotate_pseudonym_did("did:web:hagukumi.etzhayyim.com:recipient:pseudonym:2026-04", 31)
    return _check("pseudonym rotation at >30 days (G16)",
                  result["rotate"] is True)


def test_pseudonym_rotation_not_needed() -> bool:
    result = agent.rotate_pseudonym_did("did:web:hagukumi.etzhayyim.com:recipient:pseudonym:2026-05", 15)
    return _check("pseudonym rotation not needed at 15 days (G16)",
                  result["rotate"] is False)


def test_guardian_consent_child_ok() -> bool:
    return _check("child <14 with guardian consent accepted (G17)",
                  agent.verify_guardian_consent_for_child(8, "did:web:parent:bob")["ok"] is True)


def test_guardian_consent_child_missing() -> bool:
    return _check("child <14 without guardian consent rejected (G17)",
                  agent.verify_guardian_consent_for_child(8, "")["ok"] is False)


def test_guardian_consent_adult_not_required() -> bool:
    return _check("adult >=14 guardian consent not required (G17)",
                  agent.verify_guardian_consent_for_child(18, "")["ok"] is True)


def test_care_session_all_gates_pass() -> bool:
    registry = {"did:caregiver:alice": {"councilApprovalDate": "2026-05-15"}}
    work_log = {"did:caregiver:alice": {"cumulative_hours_24h": 4.0, "hours_since_last_session": 24.0}}
    result = agent.record_care_session(
        "test-001",
        "did:web:hagukumi.etzhayyim.com:recipient:pseudonym:2026-05",
        "did:caregiver:alice",
        "2026-05-20T08:00:00Z",
        "2026-05-20T12:00:00Z",
        "ipfs://QmXChaCha20PolyEncrypted",
        "ipfs://QmConsentRecord0001",
        "child-daily-care",
        caregiver_registry=registry,
        consent_timestamp_iso="2026-05-20T10:00:00Z",
        emergency_keywords=["fever", "injury"],
        session_description="routine play",
        work_log=work_log,
        recipient_age=8,
        guardian_did="did:web:parent:bob"
    )
    return _check("care session with all gates pass", result.get(":careSessionAttestation/id") is not None)


def test_care_session_blocked_no_encryption() -> bool:
    registry = {"did:caregiver:alice": {"councilApprovalDate": "2026-05-15"}}
    result = agent.record_care_session(
        "test-002",
        "did:web:hagukumi.etzhayyim.com:recipient:pseudonym:2026-05",
        "did:caregiver:alice",
        "2026-05-20T08:00:00Z",
        "2026-05-20T12:00:00Z",
        "",
        "ipfs://QmConsentRecord0001",
        "child-daily-care",
        caregiver_registry=registry,
        recipient_age=8,
        guardian_did="did:web:parent:bob"
    )
    return _check("care session blocked without encryption (G15)", result.get("blocked") is True)


def test_care_session_blocked_unauthenticated_caregiver() -> bool:
    registry = {}
    result = agent.record_care_session(
        "test-003",
        "did:web:hagukumi.etzhayyim.com:recipient:pseudonym:2026-05",
        "did:caregiver:unknown",
        "2026-05-20T08:00:00Z",
        "2026-05-20T12:00:00Z",
        "ipfs://QmXChaCha20PolyEncrypted",
        "ipfs://QmConsentRecord0001",
        "child-daily-care",
        caregiver_registry=registry
    )
    return _check("care session blocked without caregiver attestation (G4)", result.get("blocked") is True)


def test_care_session_blocked_child_no_guardian() -> bool:
    registry = {"did:caregiver:alice": {"councilApprovalDate": "2026-05-15"}}
    result = agent.record_care_session(
        "test-004",
        "did:web:hagukumi.etzhayyim.com:recipient:pseudonym:2026-05",
        "did:caregiver:alice",
        "2026-05-20T08:00:00Z",
        "2026-05-20T12:00:00Z",
        "ipfs://QmXChaCha20PolyEncrypted",
        "ipfs://QmConsentRecord0001",
        "child-daily-care",
        caregiver_registry=registry,
        recipient_age=10,
        guardian_did=""
    )
    return _check("care session blocked child <14 without guardian (G17)", result.get("blocked") is True)


def test_settlement_tithe_split() -> bool:
    s = agent.build_settlement_intent(10_000_000)
    return _check("10% tithe + stops at intent (G13/G14)",
                  s["titheMinor"] == 1_000_000 and s["state"] == "intent"
                  and s["rail"] == "usdc-base-l2")


def test_settlement_executed_with_sig() -> bool:
    s = agent.build_settlement_intent(5_000_000, caregiver_sig_ref="0xsig")
    return _check("settlement executes only with caregiver signature (G14)", s["state"] == "executed")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"hagukumi agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
