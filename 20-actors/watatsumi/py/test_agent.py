#!/usr/bin/env python3
"""watatsumi 綿津見 — agent cell tests (no kotoba host, no network, no LLM).

ADR-2605252200 Phase 4. Exercises the 9 handlers + settlement + gates with injected
functions so the suite runs offline (Murakumo-only invariant untouched; G15). Tests
enforce civilian-only constraints (depth ≤6500m, no military, max 3 crew, max 72h submerged).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_hull_ring_fabrication_pass() -> bool:
    out = agent.handle_hull_ring_fabrication({
        "material_lot": "HSLA-80-LOT-001",
        "ndt_pass": True,
        "roundness_pct": 0.3,
    })
    return _check("L1: hull ring fabrication passes with NDT + roundness <0.5%",
                  out["attestation"] == "L1-pass-HSLA-80-LOT-001")


def test_hull_ring_roundness_fail() -> bool:
    out = agent.handle_hull_ring_fabrication({
        "material_lot": "HSLA-80-LOT-001",
        "ndt_pass": True,
        "roundness_pct": 0.6,
    })
    return _check("L1: hull ring rejects roundness >0.5%",
                  out["attestation"] == "FAIL_roundness_exceeded")


def test_hull_ring_ndt_fail() -> bool:
    out = agent.handle_hull_ring_fabrication({
        "material_lot": "HSLA-80-LOT-001",
        "ndt_pass": False,
        "roundness_pct": 0.3,
    })
    return _check("L1: hull ring rejects failed NDT",
                  out["attestation"] == "FAIL_ndt_not_passed")


def test_section_assembly_pass() -> bool:
    out = agent.handle_section_assembly({
        "ring_ids": ["ring.001", "ring.002"],
        "penetrators": ["power-conduit", "data-fiber"],
    })
    return _check("L2: section assembly passes with power/data/fluid penetrators",
                  out["attestation"] == "L2-pass-2-rings")


def test_section_assembly_no_weapon_mounts() -> bool:
    out = agent.handle_section_assembly({
        "ring_ids": ["ring.001"],
        "penetrators": ["weapon-mount", "torpedo-tube"],
    })
    return _check("L2: section assembly rejects weapon mounts (civilian-only G12)",
                  out["attestation"] == "FAIL_weapon_mount_detected")


def test_weld_inspection_pass() -> bool:
    out = agent.handle_weld_inspection({
        "ndt_results": [True, True, True],
    })
    return _check("L3: weld inspection passes 100% NDT",
                  out["result"] == "L3-pass-100pct-ndt")


def test_system_integration_clean_fuel() -> bool:
    out = agent.handle_system_integration({
        "propulsion_type": "LFP",
        "sonar_db": 170,
    })
    return _check("L4: system integration passes LFP fuel-cell (G13)",
                  out["result"] == "L4-pass-lfp-propulsion")


def test_system_integration_no_nuclear() -> bool:
    out = agent.handle_system_integration({
        "propulsion_type": "nuclear",
        "sonar_db": 170,
    })
    return _check("L4: system integration rejects nuclear propulsion (N2/Charter §2(g))",
                  out["result"] == "FAIL_forbidden_propulsion")


def test_system_integration_sonar_cetacean_gate() -> bool:
    out = agent.handle_system_integration({
        "propulsion_type": "H2",
        "sonar_db": 190,
    })
    return _check("L4: system integration rejects sonar >180dB (G8 cetacean protection)",
                  out["result"] == "FAIL_sonar_exceeds_180db")


def test_section_joining_pass() -> bool:
    out = agent.handle_section_joining({
        "weld_passes": 6,
        "rt_100pct": True,
        "pwht_temperature_c": 600,
    })
    return _check("L5a: section joining passes multi-pass TIG + 100% RT + PWHT",
                  out["result"] == "L5a-pass-6passes-pwht600c")


def test_pressure_test_depth_cap_6500m() -> bool:
    out = agent.handle_pressure_test({
        "design_depth_m": 6500,
        "duration_hours": 6,
    })
    return _check("L5b: pressure test passes at 6500m civilian depth cap",
                  out["test_depth_m"] == 8125.0
                  and out["result"] == "L5b-pass-8125.0m-6h")


def test_pressure_test_exceeds_depth_cap() -> bool:
    out = agent.handle_pressure_test({
        "design_depth_m": 7000,
        "duration_hours": 6,
    })
    return _check("L5b: pressure test rejects depth >6500m (civilian-only G12)",
                  "FAIL_depth_exceeds" in out["result"])


def test_sea_trial_all_stages_pass() -> bool:
    out = agent.handle_sea_trial({
        "dock_pass": True,
        "harbor_pass": True,
        "deep_water_pass": True,
        "crew_count": 3,
        "submerged_duration_h": 72,
    })
    return _check("L5c: sea trial passes all stages + crew ≤3 + submerged ≤72h",
                  out["result"] == "L5c-pass-all-stages")


def test_sea_trial_crew_cap() -> bool:
    out = agent.handle_sea_trial({
        "dock_pass": True,
        "harbor_pass": True,
        "deep_water_pass": True,
        "crew_count": 5,
        "submerged_duration_h": 72,
    })
    return _check("L5c: sea trial rejects crew >3 (civilian-only G12)",
                  "FAIL_crew" in out["result"])


def test_sea_trial_submerged_duration_cap() -> bool:
    out = agent.handle_sea_trial({
        "dock_pass": True,
        "harbor_pass": True,
        "deep_water_pass": True,
        "crew_count": 3,
        "submerged_duration_h": 100,
    })
    return _check("L5c: sea trial rejects submerged >72h (civilian-only G12)",
                  "FAIL_submerged" in out["result"])


def test_marine_emissions_audit_pass() -> bool:
    out = agent.handle_marine_emissions_audit({
        "marpol_compliant": True,
        "bwmc_compliant": True,
        "biofouling_clean": True,
    })
    return _check("Cross: marine emissions audit passes MARPOL + BWMC + biofouling (G14)",
                  out["result"] == "audit-pass-all-annexes")


def test_settlement_tithe_split() -> bool:
    s = agent.build_settlement_intent(10_000_000_000)
    return _check("Settlement: 10% tithe split + stops at intent (G17/G19)",
                  s["titheMinor"] == 1_000_000_000
                  and s["payoutMinor"] == 9_000_000_000
                  and s["state"] == "intent"
                  and s["rail"] == "usdc-base-l2")


def test_settlement_executed_only_with_member_sig() -> bool:
    s = agent.build_settlement_intent(10_000_000_000, buyer_sig_ref="0xmembersig")
    return _check("Settlement: executes only with member signature (G18)",
                  s["state"] == "executed")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"watatsumi agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
