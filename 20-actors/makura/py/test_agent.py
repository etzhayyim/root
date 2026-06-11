#!/usr/bin/env python3
"""makura 枕 — agent gate tests (offline, no kotoba host, no network, no LLM).

ADR-2605261115. Exercises the foam-pillow constitutional gates: KPI caps (G11),
isocyanate exposure (G6), FR-chemistry exclusion (G8), no-embedded-sensors (G14),
and the USDC + tithe settlement (G17/G18).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_kpi_mass_cap() -> bool:
    return _check("foam mass over 2.0 kg rejected (G11)",
                  agent.kpi_caps_ok(2.5, (50, 40, 20), 3.0)["ok"] is False)


def test_kpi_dims_cap() -> bool:
    return _check("dims over 80x50x25 rejected (G11)",
                  agent.kpi_caps_ok(1.5, (90, 40, 20), 3.0)["ok"] is False)


def test_kpi_within() -> bool:
    return _check("within KPI caps accepted (G11)",
                  agent.kpi_caps_ok(1.5, (60, 40, 20), 3.0)["ok"] is True)


def test_exposure_mdi_ceiling() -> bool:
    return _check("MDI over 5 ppb rejected (G6)", agent.exposure_ok(6.0, 1.0)["ok"] is False)


def test_exposure_tdi_ceiling() -> bool:
    return _check("TDI over 2 ppb rejected (G6)", agent.exposure_ok(3.0, 3.0)["ok"] is False)


def test_fr_chemistry_excluded() -> bool:
    return _check("PBDE/TDCPP rejected (G8)",
                  agent.fr_chemistry_ok(["polyol", "TDCPP"])["ok"] is False)


def test_fr_free_ok() -> bool:
    return _check("FR-free chemistry accepted (G8)",
                  agent.fr_chemistry_ok(["polyol", "mdi", "surfactant"])["ok"] is True)


def test_bom_rejects_embedded() -> bool:
    return _check("RFID/NFC in BoM rejected (G14)",
                  agent.bom_no_embedded(["foam", "fabric", "RFID tag"])["ok"] is False)


def test_bom_clean() -> bool:
    return _check("clean BoM accepted (G14)",
                  agent.bom_no_embedded(["foam", "fabric", "zipper"])["ok"] is True)


def test_foam_batch_blocked_on_fr() -> bool:
    out = agent.record_foam_batch("b", ["pbde"], 1.0, 1.0)
    return _check("foam batch blocked on prohibited FR (G8)", out.get("blocked") is True)


def test_foam_batch_blocked_on_exposure() -> bool:
    out = agent.record_foam_batch("b", ["polyol"], 9.0, 1.0)
    return _check("foam batch blocked on MDI over-exposure (G6)", out.get("blocked") is True)


def test_lot_blocked_over_kpi() -> bool:
    out = agent.finalize_pillow_lot("l", 3.0, (50, 40, 20), 3.0, [])
    return _check("pillow lot blocked over KPI (G11)", out.get("blocked") is True)


def test_settlement_tithe_split() -> bool:
    s = agent.build_settlement_intent(20_000_000)
    return _check("10% tithe + stops at intent (G17/G18)",
                  s["titheMinor"] == 2_000_000 and s["state"] == "intent"
                  and s["rail"] == "usdc-base-l2")


def test_settlement_executed_with_sig() -> bool:
    s = agent.build_settlement_intent(1_000_000, buyer_sig_ref="0xsig")
    return _check("settlement executes only with member signature (G18)", s["state"] == "executed")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"makura agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
