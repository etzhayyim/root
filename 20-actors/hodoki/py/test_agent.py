#!/usr/bin/env python3
"""hodoki 解き — agent gate tests (offline, no kotoba host, no network, no LLM).

ADR-2605261215. Exercises the 9 cell handlers + settlement + gates with injected
functions so the suite runs offline (Murakumo-only invariant untouched; G9).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_charter_scan_passes_civilian() -> bool:
    result = agent.scan_charter_compliance("ABC123", "2024 Toyota Corolla")
    return _check("civilian vehicle passes Charter scan (G5)",
                  result["ok"] is True and result["status"] == "passed")


def test_charter_scan_blocks_military() -> bool:
    result = agent.scan_charter_compliance("XYZ789", "Military armored platform")
    return _check("military vehicle fails Charter scan (G5)",
                  result["ok"] is False and result["status"] == "failed")


def test_charter_scan_blocks_weapon() -> bool:
    result = agent.scan_charter_compliance("XYZ789", "Weapon delivery system")
    return _check("weapon-carrying vehicle fails Charter scan (G5)",
                  result["ok"] is False)


def test_fgas_capture_below_threshold() -> bool:
    result = agent.check_fgas_compliance(100.0, 94.0)
    return _check("F-gas capture 94% < 95% rejected (G6)",
                  result["ok"] is False)


def test_fgas_capture_at_threshold() -> bool:
    result = agent.check_fgas_compliance(100.0, 95.0)
    return _check("F-gas capture 95% accepted (G6)",
                  result["ok"] is True)


def test_ecu_wipe_requires_both() -> bool:
    result = agent.ecu_data_wipe_mandatory(False, 2)
    return _check("ECU not wiped rejected (G8)",
                  result["ok"] is False and result.get("blocked") is True)


def test_ecu_wipe_requires_witness_quorum() -> bool:
    result = agent.ecu_data_wipe_mandatory(True, 1)
    return _check("Witness count 1 < 2 rejected (G8)",
                  result["ok"] is False and result.get("blocked") is True)


def test_ecu_wipe_with_quorum() -> bool:
    result = agent.ecu_data_wipe_mandatory(True, 2)
    return _check("ECU wiped + witness quorum ≥2 accepted (G8)",
                  result["ok"] is True)


def test_part_did_generation() -> bool:
    did = agent.issue_part_did("VIN123", "Engine Block")
    return _check("part DID generated (G12)",
                  did.startswith("did:web:hodoki.etzhayyim.com:part:"))


def test_pgm_yield_below_threshold() -> bool:
    result = agent.audit_pgm_yield(94.0)
    return _check("PGM yield 94% < 95% rejected (G14)",
                  result["ok"] is False and result.get("blocked") is True)


def test_pgm_yield_at_threshold() -> bool:
    result = agent.audit_pgm_yield(95.0)
    return _check("PGM yield 95% accepted (G14)",
                  result["ok"] is True)


def test_recovery_rate_below_threshold() -> bool:
    result = agent.calc_recovery_rate(700, 100, 40, 200, 1040)
    return _check("Recovery 84% < 95% rejected (G13)",
                  result["ok"] is False and result.get("blocked") is True)


def test_recovery_rate_at_threshold() -> bool:
    result = agent.calc_recovery_rate(800, 150, 50, 20, 1000)
    return _check("Recovery 100% accepted (G13)",
                  result["ok"] is True and result.get("recovery_pct") == 100)


def test_asr_landfill_cap() -> bool:
    result = agent.calc_recovery_rate(850, 150, 0, 50, 1000)
    return _check("ASR 5% at cap (G13)",
                  result["ok"] is False and result.get("blocked") is True)


def test_asr_landfill_below_cap() -> bool:
    result = agent.calc_recovery_rate(850, 150, 0, 40, 1000)
    return _check("ASR 4% below cap (G13)",
                  result["ok"] is True and result.get("asr_landfill_pct") == 4)


def test_settlement_tithe_split() -> bool:
    s = agent.build_settlement_intent(10_000_000)
    return _check("10% tithe + stops at intent (S2/S4)",
                  s["titheMinor"] == 1_000_000 and s["state"] == "intent"
                  and s["rail"] == "usdc-base-l2")


def test_settlement_executed_with_sig() -> bool:
    s = agent.build_settlement_intent(10_000_000, buyer_sig_ref="0xsig")
    return _check("settlement executes only with operator signature (S3)",
                  s["state"] == "executed")


def test_intake_audit_handler() -> bool:
    out = agent.handle_intake_audit({
        "vin": "VIN123",
        "vehicle_desc": "2024 Honda Civic"
    })
    return _check("intake audit handler sets charter status",
                  out.get("charter_status") == "passed")


def test_depollution_handler_passes() -> bool:
    out = agent.handle_depollution({
        "vin": "VIN123",
        "ecu_wiped": True,
        "witness_count": 2,
        "fgas_mass_g": 100.0,
        "fgas_target_pct": 96.0
    })
    return _check("depollution handler passes when gates met",
                  out.get("status") == "passed")


def test_battery_routing_soh_high() -> bool:
    out = agent.handle_battery_handling({
        "vin": "VIN123",
        "soh_pct": 75
    })
    return _check("SoH >=70 routes to hikari-second-life",
                  out.get("routing_decision") == "hikari-second-life")


def test_battery_routing_soh_medium() -> bool:
    out = agent.handle_battery_handling({
        "vin": "VIN123",
        "soh_pct": 50
    })
    return _check("SoH 40-70 routes to cell-recycle",
                  out.get("routing_decision") == "cell-recycle")


def test_battery_routing_soh_low() -> bool:
    out = agent.handle_battery_handling({
        "vin": "VIN123",
        "soh_pct": 30
    })
    return _check("SoH <40 routes to kanayama-reclaim",
                  out.get("routing_decision") == "kanayama-reclaim")


def test_parts_harvest_handler() -> bool:
    out = agent.handle_parts_harvest({
        "vin": "VIN123",
        "part_name": "Engine Block"
    })
    return _check("parts harvest handler generates DID",
                  out.get("part_did", "").startswith("did:web:hodoki.etzhayyim.com"))


def test_catalyst_recovery_handler() -> bool:
    out = agent.handle_catalyst_recovery({
        "pgm_yield_pct": 96.0
    })
    return _check("catalyst recovery handler passes at 96% PGM yield",
                  out.get("status") == "passed")


def test_body_shred_handler() -> bool:
    out = agent.handle_body_shred({
        "ferrous_kg": 800.0,
        "non_ferrous_kg": 150.0,
        "copper_kg": 50.0,
        "asr_kg": 20.0,
        "input_mass_kg": 1000.0
    })
    return _check("body shred handler calculates recovery %",
                  out.get("recovery_pct") == 100)


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"hodoki agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
