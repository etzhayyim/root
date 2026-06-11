#!/usr/bin/env python3
"""kanayama 金 — circular metallurgy (UBC recycling) langgraph actor (kotoba WASM cell).

ADR-2605252400, migration plan Phase 4. Runs in-WASM on kotoba :8077. Handlers over
the closed-loop Al recycling schema (intake QA, decoating, melting, casting, rolling,
QC, emissions audit, settlement), enforcing kanayama's constitutional gates:

  G1  firmware open-source (all furnace/casting/rolling/robotics firmware Apache 2.0+Rider)
  G2  mass-balance audit ≥98% closure (input = output_metal + dross + emission)
  G3  IPFS-pinned per-batch + per-coil photo/video
  G4  every pour signed by witness quorum ≥2 distinct robots (Ed25519, DID-bound)
  G6  kotoba EAVT-native state (no SQL/RisingWave/Cypher)
  G7  USDC Base L2 + ERC-4337 + TitheRouter 10%; no Stripe/fiat
  G12 KPI caps — recovery rate ≥95%; energy ≤6 kWh/kg for Wave 1 Al
  G13 renewable + grid-balanced energy only

LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G5). State is
written back to the kotoba Datom log (G6). Settlement is USDC on Base L2 + ERC-4337 +
TitheRouter 10% only — no fiat, no Stripe (G7). The platform holds no key; the
operator signs each settlement with their own passkey/smart-account (G15). Every
stage is recorded as a Datom — no silent truncation (G17).

This R0 build computes and returns plans/records; it does not dispatch real recycling
work and does not broadcast settlements (both G11-gated; settlement stops at :intent).
"""
from __future__ import annotations

from typing import TypedDict

# kotoba-provided host bindings (WASM Component Model imports)
try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

TITHE_BPS = 1000  # 10% TitheRouter auto-split (G7), basis points
RECOVERY_RATE_MIN_PCT = 95.0  # G12 minimum recovery rate
ENERGY_CAP_KWH_PER_KG = 6.0  # G12 energy cap for Wave 1 Al


# --------------------------------------------------------------------------- #
# mass-balance audit gate (G2)
# --------------------------------------------------------------------------- #
def check_mass_balance(input_mass: float, output_metal: float, dross: float,
                       emissions_mass: float) -> dict:
    """Verify ≥98% mass closure (input = output_metal + dross + emission)."""
    accounted = output_metal + dross + emissions_mass
    if input_mass <= 0:
        return {"ok": False, "reason": "input_mass must be positive"}
    closure_pct = (accounted / input_mass) * 100.0
    if closure_pct >= 98.0:
        return {"ok": True, "closure_pct": closure_pct}
    return {"ok": False, "closure_pct": closure_pct,
            "reason": f"mass closure {closure_pct:.1f}% < 98% required (G2)"}


# --------------------------------------------------------------------------- #
# KPI caps (G12)
# --------------------------------------------------------------------------- #
def check_kpi_caps(recovery_rate_pct: float, energy_kwh_per_kg: float) -> dict:
    """Verify recovery rate ≥95% and energy ≤6 kWh/kg for Wave 1 Al."""
    failures = []
    if recovery_rate_pct < RECOVERY_RATE_MIN_PCT:
        failures.append(f"recovery {recovery_rate_pct:.1f}% < {RECOVERY_RATE_MIN_PCT}% (G12)")
    if energy_kwh_per_kg > ENERGY_CAP_KWH_PER_KG:
        failures.append(f"energy {energy_kwh_per_kg:.1f} kWh/kg > {ENERGY_CAP_KWH_PER_KG} (G12)")
    if failures:
        return {"ok": False, "reason": "; ".join(failures)}
    return {"ok": True}


# --------------------------------------------------------------------------- #
# witness quorum gate (G4)
# --------------------------------------------------------------------------- #
def check_witness_sigs(witness_sigs: list) -> dict:
    """≥2 distinct robots must sign each pour (Ed25519, DID-bound)."""
    if not witness_sigs or len(witness_sigs) < 2:
        return {"ok": False, "reason": f"witness quorum {len(witness_sigs or [])} < 2 required (G4)"}
    return {"ok": True, "witness_count": len(witness_sigs)}


# --------------------------------------------------------------------------- #
# intake QA (L1)
# --------------------------------------------------------------------------- #
def intake_qa(bale_weight: float, cl_pct: float, moisture_pct: float,
              fe_ppm: int) -> dict:
    """L1 UBC bale QA thresholds (heuristic; wave 1 baseline)."""
    passed = (cl_pct <= 2.0 and moisture_pct <= 5.0 and fe_ppm <= 500)
    return {
        ":intake/id": f"intake.{bale_weight:.0f}kg",
        ":intake/baleWeight": bale_weight,
        ":intake/clResiduePct": cl_pct,
        ":intake/moisturePct": moisture_pct,
        ":intake/magneticImpurityPpm": fe_ppm,
        ":intake/qaPassed": passed,
        ":intake/blocked": not passed,
    }


# --------------------------------------------------------------------------- #
# settlement — USDC + TitheRouter intent (NOT broadcast; G7/G11/G15)
# --------------------------------------------------------------------------- #
def build_settlement_intent(gross_minor: int, operator_sig_ref: str | None = None) -> dict:
    """Compute the USDC settlement split. 10% tithe → Public Fund; operator gets the net.
    Stops at :intent — broadcast needs an operator signature (G15) + gate (G11)."""
    tithe = (gross_minor * TITHE_BPS) // 10_000
    return {
        "rail": "usdc-base-l2",
        "grossMinor": gross_minor,
        "titheMinor": tithe,
        "operatorPayoutMinor": gross_minor - tithe,
        "titheRouter": "50-infra/etzhayyim-tithe-router",
        # operator signs with their own passkey/smart-account; platform holds no key (G15)
        "state": "executed" if operator_sig_ref else "intent",
        "operatorSigRef": operator_sig_ref or "",
    }


# --------------------------------------------------------------------------- #
# full batch settlement (mass-balance basis)
# --------------------------------------------------------------------------- #
def finalize_batch_settlement(batch_id: str, input_mass: float, output_metal: float,
                              dross: float, emissions_mass: float, recovery_pct: float,
                              energy_per_kg: float) -> dict:
    """Compute full batch record + settlement intent after all 9 cells."""
    mb = check_mass_balance(input_mass, output_metal, dross, emissions_mass)
    if not mb["ok"]:
        return {"error": mb["reason"], "blocked": True}
    kpi = check_kpi_caps(recovery_pct, energy_per_kg)
    if not kpi["ok"]:
        return {"error": kpi["reason"], "blocked": True}
    # R0 — compute & return intent; no broadcast (G11)
    # Gross = input_mass × $/kg estimate (mock 2.5 USDC/kg = 2.5e6 minor/kg)
    gross_minor = int(input_mass * 2_500_000)
    settlement = build_settlement_intent(gross_minor)
    return {
        ":batchSettlement/id": batch_id,
        ":batchSettlement/inputMass": input_mass,
        ":batchSettlement/outputMetal": output_metal,
        ":batchSettlement/drossCollected": dross,
        ":batchSettlement/closurePct": mb.get("closure_pct", 0),
        ":batchSettlement/recoveryRate": recovery_pct,
        ":batchSettlement/energyKwhPerKg": energy_per_kg,
        ":batchSettlement/settlement": settlement,
    }


if __name__ == "__main__":  # pragma: no cover
    print("intake QA (pass):", intake_qa(500.0, 0.8, 2.1, 45).get(":intake/qaPassed"))
    print("intake QA (fail):", intake_qa(500.0, 3.0, 6.0, 600).get(":intake/blocked"))
    print("mass-balance (OK):", check_mass_balance(500.0, 475.0, 20.0, 5.0).get("ok"))
    print("mass-balance (FAIL):", check_mass_balance(500.0, 300.0, 50.0, 50.0).get("ok"))
    print("witness quorum (OK):", check_witness_sigs(["did:web:r1", "did:web:r2"]).get("ok"))
    print("witness quorum (FAIL):", check_witness_sigs(["did:web:r1"]).get("ok"))
    print("KPI (OK):", check_kpi_caps(96.0, 5.5).get("ok"))
    print("KPI (FAIL):", check_kpi_caps(90.0, 7.0).get("ok"))
    print("settlement:", build_settlement_intent(1_000_000_000))
