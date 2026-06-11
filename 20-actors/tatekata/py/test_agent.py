#!/usr/bin/env python3
"""tatekata 建方 — agent gate tests (offline, no kotoba host, no network, no LLM).

ADR-2605250715. Exercises the construction constitutional gates: KPI caps (G11),
witness quorum (G3), phase advancement (G17), and the USDC + tithe settlement
(G15/G16).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_kpi_stories_cap() -> bool:
    return _check("stories over 2 rejected (G11)",
                  agent.kpi_caps_ok(3, 5000)["ok"] is False)


def test_kpi_footprint_cap() -> bool:
    return _check("footprint over 5000 m² rejected (G11)",
                  agent.kpi_caps_ok(2, 6000)["ok"] is False)


def test_kpi_within_caps() -> bool:
    return _check("within KPI caps accepted (G11)",
                  agent.kpi_caps_ok(2, 5000)["ok"] is True)


def test_witness_quorum_insufficient() -> bool:
    return _check("witness count <2 rejected (G3)",
                  agent.witness_quorum_ok(["did:web:giemon"])["ok"] is False)


def test_witness_quorum_sufficient() -> bool:
    dids = ["did:web:giemon.kuni-umi.etzhayyim.com",
            "did:web:mimi.kuni-umi.etzhayyim.com"]
    return _check("witness count ≥2 accepted (G3)",
                  agent.witness_quorum_ok(dids)["ok"] is True)


def test_advance_phase_foundation() -> bool:
    result = agent.advance_phase("foundation")
    return _check("foundation → structural advance (G17)",
                  result["state"] == "structural" and result["blocked"] is None)


def test_advance_phase_structural() -> bool:
    result = agent.advance_phase("structural")
    return _check("structural → mep advance (G17)",
                  result["state"] == "mep" and result["blocked"] is None)


def test_advance_phase_terminal() -> bool:
    result = agent.advance_phase("commissioning")
    return _check("commissioning terminal (G17)",
                  result["state"] == "commissioning" and result["blocked"] is not None)


def test_foundation_excavation() -> bool:
    result = agent.handle_foundation_excavation({"spec": "site grid excavation"})
    return _check("foundation excavation plan recorded (G17)",
                  result["plan"]["phase"] == "foundation")


def test_structural_assembly() -> bool:
    result = agent.handle_structural_assembly({"bim_ref": "freeCAD-model-ref"})
    return _check("structural assembly plan recorded (G17)",
                  result["plan"]["phase"] == "structural")


def test_mep_installation() -> bool:
    result = agent.handle_mep_installation({"mep_design": "hvac-electrical-plumbing"})
    return _check("MEP installation plan recorded (G17)",
                  result["plan"]["phase"] == "mep")


def test_finishing_handoff() -> bool:
    result = agent.handle_finishing_handoff({"phase_input": "from-mep-complete"})
    return _check("finishing handoff plan recorded (G17)",
                  result["plan"]["phase"] == "finishing")


def test_commissioning() -> bool:
    result = agent.handle_commissioning({"phase_input": "from-finishing-complete"})
    return _check("commissioning plan recorded (G17)",
                  result["plan"]["phase"] == "commissioning")


def test_progress_witness_quorum_fail() -> bool:
    result = agent.record_phase_progress("foundation", "did:project", ["did:giemon"])
    return _check("progress blocked on insufficient witnesses (G3/G17)",
                  result.get("blocked") is True)


def test_progress_witness_quorum_pass() -> bool:
    dids = ["did:web:giemon.kuni-umi.etzhayyim.com",
            "did:web:mimi.kuni-umi.etzhayyim.com"]
    result = agent.record_phase_progress("structural", "did:project", dids,
                                          photo_cid="QmPhotos", depth_map_cid="QmDepths")
    return _check("progress recorded with witness quorum (G3/G17)",
                  result.get(":progress/phase") == "structural")


def test_settlement_tithe_split() -> bool:
    s = agent.build_settlement_intent(50_000_000)
    return _check("10% tithe + stops at intent (G15/G16)",
                  s["titheMinor"] == 5_000_000 and s["state"] == "intent"
                  and s["rail"] == "usdc-base-l2")


def test_settlement_executed_with_sig() -> bool:
    s = agent.build_settlement_intent(10_000_000, owner_sig_ref="0xsig")
    return _check("settlement executes only with owner signature (G16)",
                  s["state"] == "executed")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"tatekata agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
