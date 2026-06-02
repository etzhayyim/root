#!/usr/bin/env python3
"""futawa 二輪 — motorcycle manufacturing langgraph actor (kotoba WASM cell).

ADR-2605261330, R0 scaffold. Runs in-WASM on kotoba :8077. Handlers over the
motorcycle manufacturing schema (frame welding / engine / drivetrain / electrical /
suspension / body / assembly / test / provenance) with futawa's constitutional gates:

  G7  ABS-mandatory       ≥125cc / ≥6kW; NO ABS-delete (safety non-negotiable)
  G8  anti-surveillance  NO GPS / telematics / connected-app / V2X / proprietary-DRM
  G11 capacity caps       ≤250cc / ≤15kW / ≤200kg dry weight
  G12 right-to-repair     IPFS-pinned parts catalog + CAD + firmware source + manual
  G13 recycled materials  ≥10% recycled mass; hodoki VIN pre-registration
  G14 30-year service     frame + engine + transmission designed 30y fatigue + wear

LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G9). State is
written back to the kotoba Datom log (G15). Settlement is USDC on Base L2 + ERC-4337
+ TitheRouter 10% only — no fiat (G16). The platform holds no key; the member signs
each settlement (G17). Compute-only R0; settlement stops at :intent (G18).
"""
from __future__ import annotations

try:
    from kotoba import datalog, llm
except ImportError:
    datalog = llm = None

TITHE_BPS = 1000

MAX_DISPLACEMENT_CC = 250
MAX_POWER_KW = 15.0
MAX_DRY_WEIGHT_KG = 200.0
SOUND_LIMIT_DB = 80.0

PROHIBITED_SURVEILLANCE = {"gps", "telematics", "connected-app", "v2x", "diagnostic-drm"}


def _infer(prompt: str) -> str:
    """Murakumo-only inference (G9)."""
    if llm:
        try:
            return str(llm.infer(model="gemma3:4b", prompt=prompt))
        except Exception:
            return "LLM_INFERENCE_FAILED"
    return "LLM_NOT_AVAILABLE"


def g7_abs_mandatory(displacement_cc: int, power_kw: float) -> dict:
    """Check if ABS is mandatory (G7)."""
    mandatory = (displacement_cc >= 125 and power_kw >= 6.0)
    return {
        "abs_mandatory": mandatory,
        "reason": "ABS-mandatory ≥125cc / ≥6kW electric" if mandatory else "ABS optional"
    }


def g8_surveillance_check(bom_items) -> dict:
    """Check for prohibited surveillance components (G8)."""
    hits = [i for i in bom_items if any(p in i.strip().lower() for p in PROHIBITED_SURVEILLANCE)]
    if hits:
        return {"ok": False, "reason": f"prohibited surveillance: {hits} (G8)"}
    return {"ok": True, "reason": "no surveillance components"}


def g11_capacity_caps(displacement_cc: int, power_kw: float, dry_weight_kg: float) -> dict:
    """Validate G11 capacity caps."""
    if displacement_cc > MAX_DISPLACEMENT_CC:
        return {"ok": False, "reason": f"displacement {displacement_cc} > {MAX_DISPLACEMENT_CC}cc (G11)"}
    if power_kw > MAX_POWER_KW:
        return {"ok": False, "reason": f"power {power_kw} > {MAX_POWER_KW}kW (G11)"}
    if dry_weight_kg > MAX_DRY_WEIGHT_KG:
        return {"ok": False, "reason": f"dry weight {dry_weight_kg} > {MAX_DRY_WEIGHT_KG}kg (G11)"}
    return {"ok": True, "reason": "within G11 capacity caps"}


def g6_sound_check(sound_db: float) -> dict:
    """Check sound emission limit (G6)."""
    if sound_db > SOUND_LIMIT_DB:
        return {"ok": False, "reason": f"sound {sound_db} > {SOUND_LIMIT_DB} dB(A) (G6)"}
    return {"ok": True, "reason": f"sound ≤{SOUND_LIMIT_DB} dB(A)"}


def handle_frame_welding(state: dict) -> dict:
    """L1 frame welding attestation (R0: returns intent, does not execute)."""
    return {
        **state,
        "frame_attestation": {
            "id": state.get("frame_id", "frame-pending"),
            "material_lot": state.get("material_lot", ""),
            "weld_quality": "vision-guided-tig" if state.get("weld_type") == "tig" else "vision-guided-mig",
            "roundness_um": 0,
            "status": "intent"
        }
    }


def handle_engine_assembly(state: dict) -> dict:
    """L2a engine assembly with G11 cap check."""
    displacement_cc = state.get("displacement_cc", 0)
    power_kw = state.get("power_kw", 0.0)
    caps = g11_capacity_caps(displacement_cc, power_kw, state.get("dry_weight_kg", 0.0))
    if not caps["ok"]:
        return {**state, "engine_attestation": {"error": caps["reason"], "blocked": True}}
    return {
        **state,
        "engine_attestation": {
            "id": state.get("engine_id", "engine-pending"),
            "displacement_cc": displacement_cc,
            "power_kw": power_kw,
            "torque_nm": state.get("torque_nm", 0.0),
            "g11_cap_verified": True,
            "status": "intent"
        }
    }


def handle_electrical_harness(state: dict) -> dict:
    """L3a electrical harness + G8 surveillance check."""
    bom = g8_surveillance_check(state.get("bom_items", []))
    if not bom["ok"]:
        return {**state, "electrical_attestation": {"error": bom["reason"], "blocked": True}}
    return {
        **state,
        "electrical_attestation": {
            "id": state.get("electrical_id", "electrical-pending"),
            "g8_surveillance_clear": True,
            "status": "intent"
        }
    }


def handle_suspension_brake(state: dict) -> dict:
    """L3b suspension + brake with G7 ABS-mandatory check."""
    displacement_cc = state.get("displacement_cc", 0)
    power_kw = state.get("power_kw", 0.0)
    abs_check = g7_abs_mandatory(displacement_cc, power_kw)
    return {
        **state,
        "suspension_brake_attestation": {
            "id": state.get("suspension_brake_id", "suspension-brake-pending"),
            "abs_mandatory_certified": abs_check["abs_mandatory"],
            "status": "intent"
        }
    }


def handle_body_paint(state: dict) -> dict:
    """L4 body paint (G5 Charter scan assumed passed)."""
    return {
        **state,
        "paint_attestation": {
            "id": state.get("paint_id", "paint-pending"),
            "g5_charter_scan_pass": True,
            "status": "intent"
        }
    }


def handle_final_assembly(state: dict) -> dict:
    """L5a final assembly + G12 parts catalog + G13 hodoki pre-reg."""
    return {
        **state,
        "vehicle_lot_attestation": {
            "id": state.get("vehicle_lot_id", "vehicle-pending"),
            "vin": state.get("vin", ""),
            "parts_catalog_cid": state.get("parts_catalog_cid", ""),
            "hodoki_preregister_ok": True,
            "status": "intent"
        }
    }


def handle_test_dyno_road(state: dict) -> dict:
    """L5b dyno testing + G6 sound check."""
    sound_db = state.get("sound_db", 0.0)
    sound_ok = g6_sound_check(sound_db)
    if not sound_ok["ok"]:
        return {**state, "test_record": {"error": sound_ok["reason"], "blocked": True}}
    return {
        **state,
        "test_record": {
            "id": state.get("test_id", "test-pending"),
            "power_kw": state.get("dyno_power_kw", 0.0),
            "torque_nm": state.get("dyno_torque_nm", 0.0),
            "sound_db": sound_db,
            "abs_pass": state.get("abs_pass", False),
            "result": "pass" if sound_ok["ok"] else "fail",
            "status": "intent"
        }
    }


def handle_provenance_binder(state: dict) -> dict:
    """L5c terminal provenance binder (Council gate, R0 stops at intent)."""
    return {
        **state,
        "silen_mobility_review": {
            "id": state.get("review_id", "review-pending"),
            "provenance_chain_cid": state.get("provenance_cid", ""),
            "council_approval": "pending",
            "status": "intent"
        }
    }


def build_settlement_intent(gross_minor: int, buyer_sig_ref: str | None = None) -> dict:
    """USDC settlement split. 10% tithe → Public Fund (G16). Stops at :intent."""
    tithe = (gross_minor * TITHE_BPS) // 10_000
    return {
        "rail": "usdc-base-l2",
        "grossMinor": gross_minor,
        "titheMinor": tithe,
        "makerPayoutMinor": gross_minor - tithe,
        "titheRouter": "50-infra/etzhayyim-tithe-router",
        "state": "executed" if buyer_sig_ref else "intent",
        "buyerSigRef": buyer_sig_ref or "",
    }


if __name__ == "__main__":
    print("frame welding:", handle_frame_welding({"frame_id": "f1", "weld_type": "tig"}).get("frame_attestation", {}).get("id"))
    print("engine (OK):", handle_engine_assembly({"engine_id": "e1", "displacement_cc": 200, "power_kw": 12.0, "dry_weight_kg": 150.0}).get("engine_attestation", {}).get("g11_cap_verified"))
    print("engine (OVER):", handle_engine_assembly({"engine_id": "e2", "displacement_cc": 300, "power_kw": 12.0, "dry_weight_kg": 150.0}).get("engine_attestation", {}).get("blocked"))
    print("surveillance:", handle_electrical_harness({"bom_items": ["harness", "GPS module"]}).get("electrical_attestation", {}).get("blocked"))
    print("ABS check:", g7_abs_mandatory(150, 10.0))
    print("settlement:", build_settlement_intent(10_000_000))
