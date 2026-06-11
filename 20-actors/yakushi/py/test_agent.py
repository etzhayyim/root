#!/usr/bin/env python3
"""yakushi 薬師 — agent gate tests (offline, no kotoba host, no network, no LLM).

ADR-2605250500. Exercises the pharmaceutical manufacturing constitutional gates:
OTC Wave 1 (G1), published literature routes (G2), silen-pharma-review (G3),
QP co-sign (G4), adverse event aggregation (G5/G10), witness invariant (G9),
and the USDC + tithe settlement (G17/G18).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_api_otc_wave1() -> bool:
    return _check("Wave 1 OTC API accepted (G1)",
                  agent.api_otc_ok("sodium-cromoglicate")["ok"] is True)


def test_api_not_wave1() -> bool:
    return _check("non-Wave 1 API rejected (G1)",
                  agent.api_otc_ok("omeprazole")["ok"] is False)


def test_review_approved() -> bool:
    return _check("silen-pharma-review approved (G3)",
                  agent.review_attested("approve", "Wave 1")["ok"] is True)


def test_review_rejected() -> bool:
    return _check("silen-pharma-review rejected blocks (G3)",
                  agent.review_attested("reject", "Wave 1")["ok"] is False)


def test_qp_signature_ok() -> bool:
    return _check("QP signature reference recorded (G4/G18)",
                  agent.qp_signature_ok("did:web:...qp", "passkey-ref")["ok"] is True)


def test_qp_signature_missing() -> bool:
    return _check("missing QP signature blocked (G4)",
                  agent.qp_signature_ok("", "")["ok"] is False)


def test_ae_valid_aggregation() -> bool:
    return _check("valid AE (lot + severity + outcome, no patient) (G5/G10)",
                  agent.adverse_event_ok("lot:001", "mild", "recovered")["ok"] is True)


def test_ae_invalid_severity() -> bool:
    return _check("invalid severity rejected (G5)",
                  agent.adverse_event_ok("lot:001", "extreme", "unknown")["ok"] is False)


def test_ae_invalid_outcome() -> bool:
    return _check("invalid outcome rejected (G5)",
                  agent.adverse_event_ok("lot:001", "mild", "cured")["ok"] is False)


def test_ae_missing_lot() -> bool:
    return _check("missing lot_id (would be patient ID) rejected (G10)",
                  agent.adverse_event_ok("", "mild", "recovered")["ok"] is False)


def test_witness_quorum_ok() -> bool:
    return _check("witness N=2 accepted (G9)",
                  agent.witness_quorum_ok(["did1", "did2"])["ok"] is True)


def test_witness_quorum_low() -> bool:
    return _check("witness N=1 rejected (G9)",
                  agent.witness_quorum_ok(["did1"])["ok"] is False)


def test_synthesis_wave1_ok() -> bool:
    result = agent.record_synthesis("sodium-cromoglicate", "literature-ref", ["did1", "did2"])
    return _check("synthesis Wave 1 API + witness N=2 accepted (G1/G2/G9)",
                  "blocked" not in result)


def test_synthesis_non_wave1() -> bool:
    result = agent.record_synthesis("omeprazole", "literature-ref", ["did1", "did2"])
    return _check("synthesis non-Wave 1 API blocked (G1)",
                  result.get("blocked") is True)


def test_synthesis_low_witness() -> bool:
    result = agent.record_synthesis("sodium-cromoglicate", "literature-ref", ["did1"])
    return _check("synthesis witness N=1 blocked (G9)",
                  result.get("blocked") is True)


def test_fill_aseptic_ok() -> bool:
    result = agent.record_fill("eye-drop", "aseptic-0.22µm-filter", "op-did", "qp-did")
    return _check("fill aseptic sterilization accepted (G8)",
                  "blocked" not in result)


def test_fill_autoclave_ok() -> bool:
    result = agent.record_fill("tablet", "terminal-autoclave", "op-did", "qp-did")
    return _check("fill terminal autoclave accepted (G8)",
                  "blocked" not in result)


def test_fill_invalid_sterilization() -> bool:
    result = agent.record_fill("eye-drop", "uv-sterilization", "op-did", "qp-did")
    return _check("fill invalid sterilization method blocked (G8)",
                  result.get("blocked") is True)


def test_qc_release_ok() -> bool:
    result = agent.record_qc("lot:001", "ICH Q3 compliant", "qp-did", "release")
    return _check("QC release with QP signature (G4/G13)",
                  "blocked" not in result)


def test_qc_release_no_qp() -> bool:
    result = agent.record_qc("lot:001", "ICH Q3 compliant", "", "release")
    return _check("QC release without QP blocked (G4)",
                  result.get("blocked") is True)


def test_ae_record_valid() -> bool:
    result = agent.record_ae("lot:001", "moderate", "not-recovered", "ipfs-cid")
    return _check("AE record lot + severity + outcome (G5/G10)",
                  "blocked" not in result)


def test_ae_record_invalid() -> bool:
    result = agent.record_ae("lot:001", "bad", "unknown")
    return _check("AE record invalid severity blocked (G5)",
                  result.get("blocked") is True)


def test_settlement_intent() -> bool:
    s = agent.build_settlement_intent(10_000_000)
    return _check("settlement intent: 10% tithe + stops at intent (G17/G18/G19)",
                  s["titheMinor"] == 1_000_000 and s["state"] == "intent"
                  and s["rail"] == "usdc-base-l2")


def test_settlement_executed_with_sig() -> bool:
    s = agent.build_settlement_intent(10_000_000, qp_sig_ref="0xsig")
    return _check("settlement executed only with QP signature (G18)",
                  s["state"] == "executed")


def test_raw_material_valid_grade() -> bool:
    result = agent.record_raw_material("sodium cromoglicate", "公定", "low-risk")
    return _check("raw material valid grade recorded",
                  "blocked" not in result)


def test_raw_material_invalid_grade() -> bool:
    result = agent.record_raw_material("sodium cromoglicate", "custom", "low-risk")
    return _check("raw material invalid grade blocked",
                  result.get("blocked") is True)


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"yakushi agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
