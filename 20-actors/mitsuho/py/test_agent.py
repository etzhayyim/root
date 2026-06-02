#!/usr/bin/env python3
"""mitsuho 瑞穂 — agent gate tests (offline, no kotoba host, no network, no LLM).

ADR-2605261015, R0 scaffold. Exercises the 5 handlers + settlement + gates with
injected functions so the suite runs offline (Murakumo-only invariant untouched; G1).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_parcel_attestation_recorded() -> bool:
    out = agent.handle_parcel_attestation({
        "parcel_id": "p1",
        "soil_health_score": 7.5,
        "water_quality_score": 8.0,
        "biodiversity_impact": "no-harm",
    })
    return _check("parcel attestation recorded",
                  out.get("attestation_state") == "recorded" and out["parcel_id"] == "p1")


def test_seed_source_svalbard_approved() -> bool:
    out = agent._validate_seed_source("did:web:svalbard.seedvault.no")
    return _check("Svalbard seed source approved (G7)", out["valid"] is True)


def test_seed_source_patented_rejected() -> bool:
    out = agent._validate_seed_source("Monsanto proprietary line X")
    return _check("patented seed source rejected (G7)", out["valid"] is False)


def test_crop_plan_pesticide_neonicotinoid_rejected() -> bool:
    out = agent.handle_crop_plan({
        "crop_plan_id": "cp1",
        "seed_source": "Svalbard",
        "pesticide_manifest": ["neonicotinoid imidacloprid"],
        "organic_certification": False,
    })
    return _check("neonicotinoid pesticide rejected (G9)",
                  out["plan_state"] == "rejected")


def test_crop_plan_glyphosate_rejected() -> bool:
    out = agent.handle_crop_plan({
        "crop_plan_id": "cp2",
        "seed_source": "national gene bank",
        "pesticide_manifest": ["glyphosate"],
        "organic_certification": False,
    })
    return _check("glyphosate rejected (G9)", out["plan_state"] == "rejected")


def test_crop_plan_no_pesticides_approved() -> bool:
    out = agent.handle_crop_plan({
        "crop_plan_id": "cp3",
        "seed_source": "NAVDANYA",
        "pesticide_manifest": [],
        "organic_certification": True,
    })
    return _check("organic plan with no pesticides approved (G9)",
                  out["plan_state"] == "recorded")


def test_harvest_positive_soil_carbon_recorded() -> bool:
    out = agent.handle_harvest({
        "harvest_id": "h1",
        "yield_quantity_kg": 5000.0,
        "quality_grade": "Grade A",
        "soil_carbon_delta_tons_co2eq": 2.5,
    })
    return _check("harvest with positive soil carbon recorded (G8)",
                  out["harvest_state"] == "recorded" and out["soil_carbon_delta_tons_co2eq"] == 2.5)


def test_harvest_negative_soil_carbon_pending_council() -> bool:
    out = agent.handle_harvest({
        "harvest_id": "h2",
        "yield_quantity_kg": 4000.0,
        "quality_grade": "Grade B",
        "soil_carbon_delta_tons_co2eq": -1.2,
    })
    return _check("harvest with negative soil carbon pending Council review (G8)",
                  out["harvest_state"] == "pending_council_review")


def test_food_lot_attestation_recorded() -> bool:
    out = agent.handle_food_lot({
        "food_lot_id": "lot1",
        "kilojoules_per_kg": 1510.0,
        "protein_g_per_100g": 6.3,
        "carbohydrate_g_per_100g": 78.0,
        "fat_g_per_100g": 1.2,
        "shelf_life_days": 365,
        "packaging_type": "vacuum-sealed",
    })
    return _check("food lot attestation recorded",
                  out["lot_state"] == "recorded" and out["food_lot_id"] == "lot1")


def test_settlement_tithe_split() -> bool:
    s = agent.build_settlement_intent(250_000_000)
    return _check("10% tithe split + stops at intent (G3/G5)",
                  s["titheMinor"] == 25_000_000
                  and s["producerPayoutMinor"] == 225_000_000
                  and s["state"] == "intent"
                  and s["rail"] == "usdc-base-l2")


def test_settlement_executed_only_with_member_sig() -> bool:
    s = agent.build_settlement_intent(1_000_000, buyer_sig_ref="0xmembersig")
    return _check("settlement executes only with member signature (G4)",
                  s["state"] == "executed")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"mitsuho agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
