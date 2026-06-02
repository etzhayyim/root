#!/usr/bin/env python3
"""yamabiko 山彦 — agent gate tests (offline, no kotoba host, no network, no LLM).

ADR-2605252600. Exercises the high-speed rail constitutional gates: max speed (G12),
traction propulsion phase-in (G7), noise + EMC compliance (G8), EoL recyclability (G14),
open-source firmware (G1), robot witness quorum (G4), and the USDC + tithe settlement
(G17/G21/G22).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_carbody_fsw_count_ok() -> bool:
    return _check("carbody with 120 FSWs accepted",
                  agent.validate_carbody_fabrication(120, True)["ok"] is True)


def test_carbody_fsw_count_low() -> bool:
    return _check("carbody with <100 FSWs rejected",
                  agent.validate_carbody_fabrication(50, True)["ok"] is False)


def test_carbody_structural_fail() -> bool:
    return _check("carbody with failed structural test rejected",
                  agent.validate_carbody_fabrication(120, False)["ok"] is False)


def test_bogie_traction_type_valid() -> bool:
    return _check("bogie with electric traction accepted",
                  agent.validate_bogie_assembly("bg1", "electric", True)["ok"] is True)


def test_bogie_traction_type_invalid() -> bool:
    return _check("bogie with unknown traction type rejected",
                  agent.validate_bogie_assembly("bg1", "diesel", True)["ok"] is False)


def test_bogie_witness_quorum_fail() -> bool:
    return _check("bogie marriage without ≥2 robots rejected (G4)",
                  agent.validate_bogie_assembly("bg1", "electric", False)["ok"] is False)


def test_interior_car_number_valid() -> bool:
    return _check("interior car 1-16 accepted",
                  agent.validate_interior_hvac(8, 80, True)["ok"] is True)


def test_interior_car_number_invalid() -> bool:
    return _check("interior car 0 or >16 rejected",
                  agent.validate_interior_hvac(17, 80, True)["ok"] is False)


def test_interior_seating_valid() -> bool:
    return _check("interior seating 60-100 accepted",
                  agent.validate_interior_hvac(1, 75, True)["ok"] is True)


def test_interior_seating_low() -> bool:
    return _check("interior seating <60 rejected",
                  agent.validate_interior_hvac(1, 50, True)["ok"] is False)


def test_interior_hvac_fail() -> bool:
    return _check("interior with failed HVAC test rejected",
                  agent.validate_interior_hvac(1, 80, False)["ok"] is False)


def test_traction_hv_type_valid() -> bool:
    return _check("traction 25kV AC / 1500V DC hybrid accepted",
                  agent.validate_traction_electrical("25kV AC / 1500V DC hybrid", "abc1234567def89fghijk", True)["ok"] is True)


def test_traction_firmware_sha_invalid() -> bool:
    return _check("traction with short firmware SHA rejected",
                  agent.validate_traction_electrical("25kV AC", "short", True)["ok"] is False)


def test_traction_firmware_license_unverified() -> bool:
    return _check("traction with unverified firmware license rejected (G1)",
                  agent.validate_traction_electrical("25kV AC", "abc1234567def89fghijk", False)["ok"] is False)


def test_dynamic_test_speed_320_ok() -> bool:
    return _check("dynamic test max 320 km/h (G12) passes",
                  agent.validate_dynamic_test(320, 850, 8500)["ok"] is True)


def test_dynamic_test_speed_over_320() -> bool:
    return _check("dynamic test >320 km/h rejected (G12)",
                  agent.validate_dynamic_test(350, 850, 8500)["ok"] is False)


def test_dynamic_test_speed_too_low() -> bool:
    return _check("dynamic test <200 km/h rejected (Shinkansen minimum)",
                  agent.validate_dynamic_test(150, 850, 8500)["ok"] is False)


def test_dynamic_test_braking_excessive() -> bool:
    return _check("dynamic test braking distance >1000 m rejected",
                  agent.validate_dynamic_test(320, 1200, 8500)["ok"] is False)


def test_dynamic_test_power_draw_low() -> bool:
    return _check("dynamic test power draw <5000 kW rejected",
                  agent.validate_dynamic_test(320, 850, 4000)["ok"] is False)


def test_dynamic_test_power_draw_high() -> bool:
    return _check("dynamic test power draw >15000 kW rejected",
                  agent.validate_dynamic_test(320, 850, 20000)["ok"] is False)


def test_emissions_iso3095_over_85dba() -> bool:
    return _check("ISO 3095 >85 dB(A) rejected (G8)",
                  agent.validate_emissions_acoustic(90, True, True)["ok"] is False)


def test_emissions_iec62236_fail() -> bool:
    return _check("IEC 62236 EMC test fail rejected (G8)",
                  agent.validate_emissions_acoustic(75, False, True)["ok"] is False)


def test_emissions_kyoukusei_fail() -> bool:
    return _check("騒音規制法 compliance fail rejected (G8)",
                  agent.validate_emissions_acoustic(75, True, False)["ok"] is False)


def test_emissions_all_pass() -> bool:
    return _check("all emissions tests pass",
                  agent.validate_emissions_acoustic(75, True, True)["ok"] is True)


def test_homologation_eol_recyclability_low() -> bool:
    return _check("EoL recyclability <90% rejected (G14)",
                  agent.validate_homologation(True, 85)["ok"] is False)


def test_homologation_eol_recyclability_ok() -> bool:
    return _check("EoL recyclability ≥90% accepted (G14)",
                  agent.validate_homologation(True, 92)["ok"] is True)


def test_homologation_gates_not_pass() -> bool:
    return _check("homologation without all gates passing rejected",
                  agent.validate_homologation(False, 92)["ok"] is False)


def test_council_review_sigs_insufficient() -> bool:
    return _check("Council review with <5 sigs rejected",
                  agent.validate_silen_review(3, True, True)["ok"] is False)


def test_council_review_all_passed() -> bool:
    return _check("Council review with ≥5 sigs + gates + firmware audit passes",
                  agent.validate_silen_review(5, True, True)["ok"] is True)


def test_settlement_tithe_split() -> bool:
    s = agent.build_settlement_intent(5_000_000_000)
    return _check("10% tithe + stops at intent (G17/G21)",
                  s["titheMinor"] == 500_000_000 and s["state"] == "intent"
                  and s["rail"] == "usdc-base-l2")


def test_settlement_executed_with_sig() -> bool:
    s = agent.build_settlement_intent(5_000_000_000, buyer_sig_ref="0xsig")
    return _check("settlement executes only with member signature (G21)",
                  s["state"] == "executed")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"yamabiko agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
