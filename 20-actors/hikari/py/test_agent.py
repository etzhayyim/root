#!/usr/bin/env python3
"""hikari 光 — agent cell tests (no kotoba host, no network, no LLM).

ADR-2605261100 Phase 3. Exercises the 5 handlers + settlement + gates with injected
functions so the suite runs offline (Murakumo-only invariant untouched; G5).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_solar_pv_install_estimates_kwh() -> bool:
    out = agent.handle_solar_pv_install({
        "parcel_did": "did:web:etzhayyim.com:lands:parcel/jp-001",
        "location": "Tokyo",
        "area_sqm": 250,
    })
    return _check("solar PV estimates kWh from area",
                  out.get("solar_potential_kwh") == 25)


def test_solar_pv_requires_parcel_did() -> bool:
    out = agent.handle_solar_pv_install({"location": "Tokyo", "area_sqm": 250})
    return _check("solar PV requires parcel_did",
                  out.get("error") is not None)


def test_battery_validates_chemistry() -> bool:
    out = agent.handle_storage_battery({
        "battery_id": "b1",
        "chemistry": "invalid",
        "capacity_kwh": 50.0,
    })
    return _check("battery rejects unknown chemistry",
                  out.get("error") is not None)


def test_battery_accepts_lifepo4() -> bool:
    out = agent.handle_storage_battery({
        "battery_id": "b1",
        "chemistry": "lifepo4",
        "capacity_kwh": 50.0,
        "soc_pct": 75,
    })
    return _check("battery accepts lifepo4 chemistry",
                  out.get("chemistry_ok") is True)


def test_geothermal_depth_limit() -> bool:
    out = agent.handle_geothermal_micro({
        "parcel_did": "did:web:etzhayyim.com:lands:parcel/jp-001",
        "depth_m": 600,
    })
    return _check("geothermal rejects depth > 500 m",
                  out.get("error") is not None)


def test_geothermal_potential_at_200m() -> bool:
    out = agent.handle_geothermal_micro({
        "parcel_did": "did:web:etzhayyim.com:lands:parcel/jp-001",
        "depth_m": 200,
    })
    return _check("geothermal potential 3 kW at 200 m",
                  out.get("geo_potential_kw") == 3)


def test_grid_edge_net_load() -> bool:
    out = agent.handle_grid_edge({
        "generation_kwh": 100,
        "consumption_kwh": 65,
        "battery_soc_pct": 72,
    })
    return _check("grid net load = (100 - 65) / 6 ≈ 5 kW",
                  out.get("net_load_kw") == 5)


def test_grid_edge_frequency_low_soc() -> bool:
    out = agent.handle_grid_edge({
        "generation_kwh": 50,
        "consumption_kwh": 45,
        "battery_soc_pct": 25,
    })
    return _check("grid frequency 49 Hz when battery SoC < 30 %",
                  out.get("frequency_hz") == 49)


def test_grid_edge_grid_ok_threshold() -> bool:
    out = agent.handle_grid_edge({
        "generation_kwh": 50,
        "consumption_kwh": 45,
        "battery_soc_pct": 15,
    })
    return _check("grid not ok when battery SoC < 20 %",
                  out.get("grid_ok") is False)


def test_consumption_audit_requires_period() -> bool:
    out = agent.handle_consumption_audit({"facility_did": "f1", "kwh": 35})
    return _check("consumption audit requires period_start/end",
                  out.get("error") is not None)


def test_consumption_audit_encrypts_detail() -> bool:
    out = agent.handle_consumption_audit({
        "period_start": "2026-06-02T00:00:00Z",
        "period_end": "2026-06-02T06:00:00Z",
        "facility_did": "did:web:mitsuho.example.com",
        "kwh": 35,
    })
    return _check("consumption audit detail encrypted (G9)",
                  out.get("detail_encrypted_cid") is not None
                  and "ipfs://" in out.get("detail_encrypted_cid", ""))


def test_settlement_tithe_split() -> bool:
    s = agent.build_settlement_intent(1_000_000_000)
    return _check("10% tithe split + stops at intent (G7/G8)",
                  s["titheMinor"] == 100_000_000
                  and s["operatorPayoutMinor"] == 900_000_000
                  and s["state"] == "intent"
                  and s["rail"] == "usdc-base-l2")


def test_settlement_executed_only_with_sig() -> bool:
    s = agent.build_settlement_intent(500_000_000, buyer_sig_ref="0xopsig")
    return _check("settlement executes only with operator signature (G8)",
                  s["state"] == "executed")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"hikari agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
