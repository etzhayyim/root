#!/usr/bin/env python3
"""futawa 二輪 — agent gate tests (offline, no kotoba host, no network, no LLM).

ADR-2605261330. Exercises the motorcycle manufacturing constitutional gates: capacity
caps (G11), ABS-mandatory (G7), sound limit (G6), anti-surveillance (G8), and the
USDC + tithe settlement (G16/G17/G18).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_g11_displacement_cap() -> bool:
    return _check("displacement over 250cc rejected (G11)",
                  agent.g11_capacity_caps(300, 12.0, 150.0)["ok"] is False)


def test_g11_power_cap() -> bool:
    return _check("power over 15kW rejected (G11)",
                  agent.g11_capacity_caps(200, 16.0, 150.0)["ok"] is False)


def test_g11_weight_cap() -> bool:
    return _check("dry weight over 200kg rejected (G11)",
                  agent.g11_capacity_caps(200, 12.0, 250.0)["ok"] is False)


def test_g11_within_caps() -> bool:
    return _check("within G11 caps accepted",
                  agent.g11_capacity_caps(200, 12.0, 150.0)["ok"] is True)


def test_g7_abs_mandatory_low_cc() -> bool:
    result = agent.g7_abs_mandatory(100, 8.0)
    return _check("ABS optional below 125cc (G7)",
                  result["abs_mandatory"] is False)


def test_g7_abs_mandatory_high_cc() -> bool:
    result = agent.g7_abs_mandatory(150, 8.0)
    return _check("ABS mandatory ≥125cc / ≥6kW (G7)",
                  result["abs_mandatory"] is True)


def test_g6_sound_under_limit() -> bool:
    return _check("sound under 80dB accepted (G6)",
                  agent.g6_sound_check(75.0)["ok"] is True)


def test_g6_sound_over_limit() -> bool:
    return _check("sound over 80dB rejected (G6)",
                  agent.g6_sound_check(85.0)["ok"] is False)


def test_g8_surveillance_clean() -> bool:
    return _check("clean BOM accepted (G8)",
                  agent.g8_surveillance_check(["harness", "ecu", "battery"])["ok"] is True)


def test_g8_surveillance_gps() -> bool:
    return _check("GPS in BOM rejected (G8)",
                  agent.g8_surveillance_check(["harness", "GPS module", "ecu"])["ok"] is False)


def test_g8_surveillance_v2x() -> bool:
    return _check("V2X in BOM rejected (G8)",
                  agent.g8_surveillance_check(["harness", "v2x modem"])["ok"] is False)


def test_engine_assembly_blocked_on_caps() -> bool:
    out = agent.handle_engine_assembly({"engine_id": "e1", "displacement_cc": 300, "power_kw": 12.0, "dry_weight_kg": 150.0})
    return _check("engine assembly blocked on G11 cap (G11)",
                  out.get("engine_attestation", {}).get("blocked") is True)


def test_engine_assembly_passes_caps() -> bool:
    out = agent.handle_engine_assembly({"engine_id": "e1", "displacement_cc": 200, "power_kw": 12.0, "dry_weight_kg": 150.0})
    return _check("engine assembly within G11 caps passes",
                  out.get("engine_attestation", {}).get("g11_cap_verified") is True)


def test_electrical_harness_blocks_surveillance() -> bool:
    out = agent.handle_electrical_harness({"bom_items": ["harness", "telematics modem"]})
    return _check("electrical harness blocks surveillance (G8)",
                  out.get("electrical_attestation", {}).get("blocked") is True)


def test_suspension_brake_abs_check() -> bool:
    out = agent.handle_suspension_brake({"displacement_cc": 150, "power_kw": 10.0, "suspension_brake_id": "sb1"})
    return _check("suspension brake marks ABS-mandatory ≥125cc/≥6kW (G7)",
                  out.get("suspension_brake_attestation", {}).get("abs_mandatory_certified") is True)


def test_test_dyno_sound_limit() -> bool:
    out = agent.handle_test_dyno_road({"sound_db": 85.0, "test_id": "t1"})
    return _check("dyno test blocks sound > 80dB (G6)",
                  out.get("test_record", {}).get("blocked") is True)


def test_test_dyno_passes() -> bool:
    out = agent.handle_test_dyno_road({"sound_db": 75.0, "dyno_power_kw": 12.0, "dyno_torque_nm": 50.0, "abs_pass": True, "test_id": "t1"})
    return _check("dyno test passes under 80dB (G6)",
                  out.get("test_record", {}).get("result") == "pass")


def test_settlement_tithe_split() -> bool:
    s = agent.build_settlement_intent(20_000_000)
    return _check("10% tithe + stops at intent (G16/G17)",
                  s["titheMinor"] == 2_000_000 and s["state"] == "intent" and s["rail"] == "usdc-base-l2")


def test_settlement_executed_with_sig() -> bool:
    s = agent.build_settlement_intent(10_000_000, buyer_sig_ref="0xsig")
    return _check("settlement executes only with member signature (G17)",
                  s["state"] == "executed")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"futawa agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
