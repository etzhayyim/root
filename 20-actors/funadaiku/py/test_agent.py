#!/usr/bin/env python3
"""funadaiku 船大工 — agent cell tests (no kotoba host, no network, no LLM).

ADR-2606013400 Phase 4. Exercises the 9 handlers + gate + settlement with injected
functions so the suite runs offline (Murakumo-only invariant untouched; G5). Tests
focus on zero-emission propulsion enforcement (G8), green-H₂ chain-of-custody (G9),
and USDC tithe-split (G7).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_steel_block_fabrication_plan() -> bool:
    out = agent.handle_steel_block_fabrication({"blockId": "block-001", "dimensions": "12000x8000x25"})
    return _check("L1: steel block cutting-plan generated",
                  out.get("status") == "cutting-plan" and "cutting_plan" in out)


def test_grand_block_assembly_needs_minimum_blocks() -> bool:
    out = agent.handle_grand_block_assembly({"gblockId": "gb-001", "subBlocks": []})
    return _check("L2: rejects grand-block with <2 sub-blocks",
                  out.get("error") is not None)


def test_grand_block_assembly_success() -> bool:
    out = agent.handle_grand_block_assembly(
        {"gblockId": "gb-001", "subBlocks": ["block-a", "block-b", "block-c"]})
    return _check("L2: jig design + Oshidashi witness",
                  out.get("status") == "jig-designed" and "witness_quorum" in out)


def test_weld_ndt_zero_welds_pass() -> bool:
    out = agent.handle_weld_ndt_inspection({"gblockId": "gb-001", "welds": []})
    return _check("L3: NDT pass when zero welds (vacuous)",
                  out.get("result") == "pass" and out.get("defects") == [])


def test_weld_ndt_with_welds() -> bool:
    out = agent.handle_weld_ndt_inspection(
        {"gblockId": "gb-001", "welds": [{"id": "w1"}, {"id": "w2"}]})
    return _check("L3: NDT evaluation result present",
                  out.get("ndt_eval") is not None)


def test_gate_g8_rejects_fossil() -> bool:
    """G8 (defining): zero fossil propulsion."""
    out = agent.gate_zero_emission_propulsion({"type": "diesel-main-engine"})
    return _check("G8: diesel propulsion rejected (DEFINING GATE)",
                  out.get("ok") is False and "fossil" in out.get("reason", "").lower())


def test_gate_g8_rejects_missing_hydrogen() -> bool:
    out = agent.gate_zero_emission_propulsion({"type": "solar-wind"})
    return _check("G8: missing hydrogen rejected",
                  out.get("ok") is False and "hydrogen" in out.get("reason", "").lower())


def test_gate_g8_rejects_missing_solar() -> bool:
    out = agent.gate_zero_emission_propulsion({"type": "wind-hydrogen"})
    return _check("G8: missing solar rejected",
                  out.get("ok") is False and "solar" in out.get("reason", "").lower())


def test_gate_g9_rejects_non_green_hydrogen() -> bool:
    """G9: well-to-wake green-H₂ chain-of-custody mandatory."""
    out = agent.gate_zero_emission_propulsion({
        "type": "wind-solar-hydrogen",
        "hydrogen_source_certification": "fossil-steam-reforming",
    })
    return _check("G9: non-green hydrogen rejected (well-to-wake)",
                  out.get("ok") is False and "green" in out.get("reason", "").lower())


def test_gate_g8_g9_pass_green_zero_emission() -> bool:
    """G8+G9 pass: wind + solar + green-H₂."""
    out = agent.gate_zero_emission_propulsion({
        "type": "wind-solar-hydrogen",
        "hydrogen_source_certification": "green-h2-electrolyzer-renewable",
    })
    return _check("G8+G9: zero-emission + green-H₂ passes (defining gate)",
                  out.get("ok") is True)


def test_powertrain_integration_blocked_by_non_zero_emission() -> bool:
    """L4: powertrain integration blocked if G8 fails."""
    out = agent.handle_powertrain_integration({
        "powertrain": {"type": "coal-auxiliary-boiler"}
    })
    return _check("L4: powertrain integration blocked by G8 violation",
                  out.get("blocked") is True and out.get("reason") is not None)


def test_powertrain_integration_success() -> bool:
    """L4: full zero-emission integration."""
    out = agent.handle_powertrain_integration({
        "vesselId": "nagi-0001",
        "powertrain": {
            "type": "wind-solar-hydrogen",
            "wind_rig_type": "Flettner rotor",
            "solar_wattage": 160000,
            "fc_power_mw": 2.4,
            "battery_capacity_mwh": 2.0,
            "hydrogen_source_certification": "green-h2-electrolyzer-norway",
        },
        "gross_minor": 500_000_000,
    })
    return _check("L4: zero-emission propulsion verified + settlement intent",
                  out.get("powertrain_verified") is True and "settlement_intent" in out)


def test_outfitting_mep_verify() -> bool:
    out = agent.handle_outfitting({"vesselId": "nagi-0001"})
    return _check("L5a: MEP verification + no fossil aux",
                  out.get("status") == "outfitting-complete" and "mep_verification" in out)


def test_launch_commissioning_gnc_smoke() -> bool:
    out = agent.handle_launch_commissioning({"vesselId": "nagi-0001"})
    return _check("L5b: launch + GNC smoke-test verify",
                  out.get("gnc_ready") is True and out.get("status") == "launched")


def test_sea_trial_efficiency_measure() -> bool:
    out = agent.handle_sea_trial({
        "vesselId": "nagi-0001"
    })
    return _check("L5c: sea trial wind/solar/H₂ efficiency measure",
                  out.get("sea_trial_pass") is True and "sea_trial_plan" in out)


def test_decarbonization_audit_imo_ghg() -> bool:
    out = agent.handle_decarbonization_audit({
        "vesselId": "nagi-0001"
    })
    return _check("L5x: well-to-wake IMO GHG audit (EEXI/CII)",
                  out.get("eexi_rating") is not None and out.get("cii_rating") is not None)


def test_class_certification_terminal() -> bool:
    out = agent.handle_class_certification_binder({
        "vesselId": "nagi-0001"
    })
    return _check("terminal: ABS/DNV/ClassNK cert binding + IMO registration",
                  out.get("imo_registered") is True and out.get("status") == "class-certified")


def test_settlement_tithe_split() -> bool:
    s = agent.build_settlement_intent(500_000_000)
    return _check("G7: 10% tithe split + stops at intent",
                  s["titheMinor"] == 50_000_000
                  and s["shipyardPayoutMinor"] == 450_000_000
                  and s["state"] == "intent"
                  and s["rail"] == "usdc-base-l2")


def test_settlement_executed_only_with_operator_sig() -> bool:
    s = agent.build_settlement_intent(1_000_000, operator_sig_ref="0xoperatorsig")
    return _check("G12: settlement executes only with operator signature",
                  s["state"] == "executed")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"funadaiku agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
