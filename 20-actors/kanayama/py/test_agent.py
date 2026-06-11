#!/usr/bin/env python3
"""kanayama 金 — agent gate tests (offline, no kotoba host, no network, no LLM).

ADR-2605252400. Exercises the circular-metallurgy constitutional gates: mass-balance
audit (G2), KPI caps (G12), witness quorum (G4), and the USDC + tithe settlement
(G7/G11/G15).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_intake_qa_pass() -> bool:
    out = agent.intake_qa(500.0, 0.8, 2.1, 45)
    return _check("intake QA pass (normal UBC bale)",
                  out[":intake/qaPassed"] is True)


def test_intake_qa_fail_cl_residue() -> bool:
    out = agent.intake_qa(500.0, 3.0, 2.0, 45)
    return _check("intake QA fail (Cl residue >2%, G3)",
                  out[":intake/blocked"] is True)


def test_intake_qa_fail_moisture() -> bool:
    out = agent.intake_qa(500.0, 0.8, 6.0, 45)
    return _check("intake QA fail (moisture >5%, G3)",
                  out[":intake/blocked"] is True)


def test_intake_qa_fail_fe_contamination() -> bool:
    out = agent.intake_qa(500.0, 0.8, 2.0, 600)
    return _check("intake QA fail (Fe >500ppm, G3)",
                  out[":intake/blocked"] is True)


def test_mass_balance_ok() -> bool:
    out = agent.check_mass_balance(500.0, 475.0, 20.0, 5.0)
    return _check("mass-balance ≥98% closure (G2)",
                  out["ok"] is True and out["closure_pct"] >= 98.0)


def test_mass_balance_fail_low_closure() -> bool:
    out = agent.check_mass_balance(500.0, 300.0, 50.0, 50.0)
    return _check("mass-balance <98% closure rejected (G2)",
                  out["ok"] is False and out["closure_pct"] < 98.0)


def test_mass_balance_invalid_input() -> bool:
    out = agent.check_mass_balance(0.0, 1.0, 1.0, 1.0)
    return _check("mass-balance rejects non-positive input",
                  out["ok"] is False)


def test_kpi_recovery_below_min() -> bool:
    out = agent.check_kpi_caps(90.0, 5.0)
    return _check("recovery <95% rejected (G12)",
                  out["ok"] is False)


def test_kpi_energy_above_cap() -> bool:
    out = agent.check_kpi_caps(96.0, 7.0)
    return _check("energy >6 kWh/kg rejected (G12)",
                  out["ok"] is False)


def test_kpi_both_ok() -> bool:
    out = agent.check_kpi_caps(96.0, 5.5)
    return _check("recovery ≥95% + energy ≤6 kWh/kg (G12)",
                  out["ok"] is True)


def test_witness_quorum_ok() -> bool:
    out = agent.check_witness_sigs(["did:web:robot.yokin", "did:web:robot.kamado"])
    return _check("witness quorum ≥2 (G4)",
                  out["ok"] is True and out["witness_count"] == 2)


def test_witness_quorum_fail_one() -> bool:
    out = agent.check_witness_sigs(["did:web:robot.yokin"])
    return _check("witness quorum <2 rejected (G4)",
                  out["ok"] is False)


def test_witness_quorum_fail_empty() -> bool:
    out = agent.check_witness_sigs([])
    return _check("witness quorum empty rejected (G4)",
                  out["ok"] is False)


def test_settlement_tithe_split() -> bool:
    s = agent.build_settlement_intent(1_000_000_000)
    return _check("10% tithe + stops at intent (G7/G11)",
                  s["titheMinor"] == 100_000_000
                  and s["operatorPayoutMinor"] == 900_000_000
                  and s["state"] == "intent"
                  and s["rail"] == "usdc-base-l2")


def test_settlement_executed_only_with_sig() -> bool:
    s = agent.build_settlement_intent(500_000_000, operator_sig_ref="0xoperatorsig")
    return _check("settlement executes only with operator signature (G15)",
                  s["state"] == "executed")


def test_batch_settlement_ok() -> bool:
    out = agent.finalize_batch_settlement("b1", 500.0, 475.0, 20.0, 5.0, 96.0, 5.5)
    return _check("batch settlement OK (mb ≥98%, kpi ≥95%, energy ≤6)",
                  out.get("blocked") is not True and ":batchSettlement/id" in out)


def test_batch_settlement_blocked_mass_balance() -> bool:
    out = agent.finalize_batch_settlement("b2", 500.0, 300.0, 50.0, 50.0, 96.0, 5.5)
    return _check("batch settlement blocked on mass-balance <98% (G2)",
                  out.get("blocked") is True)


def test_batch_settlement_blocked_kpi() -> bool:
    out = agent.finalize_batch_settlement("b3", 500.0, 475.0, 20.0, 5.0, 90.0, 5.5)
    return _check("batch settlement blocked on recovery <95% (G12)",
                  out.get("blocked") is True)


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"kanayama agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
