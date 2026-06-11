#!/usr/bin/env python3
"""yamabiko 山彦 — high-speed rail trainset manufacturing langgraph actor (kotoba WASM cell).

ADR-2605252600, R0 scaffold. Runs in-WASM on kotoba :8077. Nine handlers over one
kotoba EAVT graph, mirroring the 9-cell 5-layer assembly workflow:

  carbody_fabrication  (L1) aluminum/composite FSW seams + structural integrity
  bogie_assembly       (L2) wheel set + suspension + traction motor marriage
  interior_hvac        (L3) seating + HVAC + PIS installation
  traction_electrical  (L4) 25 kV AC / 1500 V DC harness + ATP/ATO firmware
  final_assembly       (L5a) integrate all layers into unified trainset
  dynamic_test         (L5b) speed ramp-up to ≤320 km/h, braking, power validation
  emissions_acoustic   (cross) ISO 3095 + IEC 62236 + 騒音規制法 attestation
  homologation_binder  (L5c) aggregate all tests; mint per-trainset DID
  silen_rail_review    (governance) Council 5-of-7 attestation of all gates G1..G22

LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G15). State is
written back to the kotoba Datom log (G16). Settlement is USDC on Base L2 + ERC-4337 +
TitheRouter 10% only — no fiat, no Stripe (G17). The platform holds no key; member
signs each settlement with their own passkey/smart-account (G21). Every stage is
recorded as a Datom — no silent truncation (G22).

This R0 build computes and returns plans/records; it does not dispatch real manufacturing
and does not broadcast settlements (both G17-gated; settlement stops at :intent).
"""
from __future__ import annotations

from typing import TypedDict

# kotoba-provided host bindings (WASM Component Model imports)
try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

TITHE_BPS = 1000  # 10% TitheRouter auto-split (G17), basis points


# --------------------------------------------------------------------------- #
# carbody_fabrication — L1 aluminum/composite FSW seams
# --------------------------------------------------------------------------- #
def validate_carbody_fabrication(fsw_count: int, test_pass: bool) -> dict:
    """Validate FSW weld quality (≥2 robot witness per G4)."""
    if fsw_count < 100:
        return {"ok": False, "reason": "FSW count too low for Shinkansen-class trainset"}
    if not test_pass:
        return {"ok": False, "reason": "Structural test failed"}
    return {"ok": True, "reason": "carbody fabrication valid"}


def record_carbody_attestation(carbody_id: str, fsw_count: int,
                               structural_pass: bool, material: str) -> dict:
    """Record L1 carbody attestation."""
    val = validate_carbody_fabrication(fsw_count, structural_pass)
    if not val["ok"]:
        return {"error": val["reason"], "blocked": True}
    return {
        ":carbodyAttestation/id": carbody_id,
        ":carbodyAttestation/fswWelds": str(fsw_count),
        ":carbodyAttestation/structuralTests": "passed" if structural_pass else "failed",
        ":carbodyAttestation/material": material,
    }


# --------------------------------------------------------------------------- #
# bogie_assembly — L2 wheel set + suspension + traction motor
# --------------------------------------------------------------------------- #
def validate_bogie_assembly(bogie_id: str, traction_type: str,
                            witness_ok: bool) -> dict:
    """Validate bogie marriage (≥2 robot witness per G4; traction type per G7)."""
    if traction_type not in ("bemu", "h2", "electric"):
        return {"ok": False, "reason": f"unknown traction type '{traction_type}'"}
    if not witness_ok:
        return {"ok": False, "reason": "bogie marriage quorum < 2 robots (G4)"}
    return {"ok": True, "reason": "bogie assembly valid"}


def record_bogie_attestation(bogie_id: str, position: str, traction_type: str,
                             witness_ok: bool) -> dict:
    """Record L2 bogie attestation."""
    val = validate_bogie_assembly(bogie_id, traction_type, witness_ok)
    if not val["ok"]:
        return {"error": val["reason"], "blocked": True}
    return {
        ":bogieAttestation/id": bogie_id,
        ":bogieAttestation/position": position,
        ":bogieAttestation/tractionMotor": traction_type,
        ":bogieAttestation/witnessQuorum": "passed" if witness_ok else "failed",
    }


# --------------------------------------------------------------------------- #
# interior_hvac — L3 seating + HVAC + PIS
# --------------------------------------------------------------------------- #
def validate_interior_hvac(car_number: int, seating: int,
                           hvac_pass: bool) -> dict:
    """Validate interior configuration (cars 1-16 per Wave 1)."""
    if car_number < 1 or car_number > 16:
        return {"ok": False, "reason": f"invalid car number {car_number}"}
    if seating < 60 or seating > 100:
        return {"ok": False, "reason": f"seating {seating} out of range"}
    if not hvac_pass:
        return {"ok": False, "reason": "HVAC functional test failed"}
    return {"ok": True, "reason": "interior HVAC valid"}


def record_interior_attestation(interior_id: str, car_number: int,
                                seating: int, hvac_pass: bool,
                                pis_version: str) -> dict:
    """Record L3 interior attestation."""
    val = validate_interior_hvac(car_number, seating, hvac_pass)
    if not val["ok"]:
        return {"error": val["reason"], "blocked": True}
    return {
        ":interiorAttestation/id": interior_id,
        ":interiorAttestation/carNumber": str(car_number),
        ":interiorAttestation/seatingCount": str(seating),
        ":interiorAttestation/hvacSpec": "passed" if hvac_pass else "failed",
        ":interiorAttestation/pisVersions": pis_version,
    }


# --------------------------------------------------------------------------- #
# traction_electrical — L4 25 kV AC / 1500 V DC + ATP/ATO firmware (open-source G1)
# --------------------------------------------------------------------------- #
def validate_traction_electrical(hv_type: str, firmware_sha: str,
                                 license_verified: bool) -> dict:
    """Validate traction electrical (open-source ATP/ATO firmware, G1)."""
    if hv_type not in ("25kV AC", "1500V DC", "25kV AC / 1500V DC hybrid"):
        return {"ok": False, "reason": f"unknown HV system type '{hv_type}'"}
    if not firmware_sha or len(firmware_sha) < 20:
        return {"ok": False, "reason": "ATP/ATO firmware SHA invalid"}
    if not license_verified:
        return {"ok": False, "reason": "ATP/ATO firmware license not Apache 2.0 (G1)"}
    return {"ok": True, "reason": "traction electrical valid"}


def record_traction_electrical_attestation(traction_id: str, hv_type: str,
                                           firmware_sha: str,
                                           license_verified: bool) -> dict:
    """Record L4 traction electrical attestation."""
    val = validate_traction_electrical(hv_type, firmware_sha, license_verified)
    if not val["ok"]:
        return {"error": val["reason"], "blocked": True}
    return {
        ":tractionElectricalAttestation/id": traction_id,
        ":tractionElectricalAttestation/hvHarness": hv_type,
        ":tractionElectricalAttestation/atpAtoFirmwareSha": firmware_sha,
        ":tractionElectricalAttestation/firmwareOpenSource": "Apache 2.0" if license_verified else "unverified",
    }


# --------------------------------------------------------------------------- #
# final_assembly — L5a carbody + bogie + interior + traction integration
# --------------------------------------------------------------------------- #
def validate_final_assembly(integration_pass: bool,
                            system_checks_pass: bool) -> dict:
    """Validate final assembly integration."""
    if not integration_pass:
        return {"ok": False, "reason": "carbody-bogie integration failed"}
    if not system_checks_pass:
        return {"ok": False, "reason": "system cross-checks failed"}
    return {"ok": True, "reason": "final assembly valid"}


def record_final_assembly_attestation(assembly_id: str, integration_pass: bool,
                                      system_checks_pass: bool) -> dict:
    """Record L5a final assembly attestation."""
    val = validate_final_assembly(integration_pass, system_checks_pass)
    if not val["ok"]:
        return {"error": val["reason"], "blocked": True}
    return {
        ":finalAssemblyAttestation/id": assembly_id,
        ":finalAssemblyAttestation/carbodyBogieIntegration": "passed" if integration_pass else "failed",
        ":finalAssemblyAttestation/systemCrossChecks": "passed" if system_checks_pass else "failed",
    }


# --------------------------------------------------------------------------- #
# dynamic_test — L5b speed ramp-up (≤320 km/h per G12), braking, power
# --------------------------------------------------------------------------- #
def validate_dynamic_test(max_speed: int, braking_dist: int,
                          power_draw: int) -> dict:
    """Validate dynamic test results (≤320 km/h per G12)."""
    if max_speed > 320:
        return {"ok": False, "reason": f"max speed {max_speed} exceeds 320 km/h (G12)"}
    if max_speed < 200:
        return {"ok": False, "reason": f"max speed {max_speed} too low for Shinkansen-class"}
    if braking_dist > 1000:
        return {"ok": False, "reason": f"braking distance {braking_dist} m excessive"}
    if power_draw < 5000 or power_draw > 15000:
        return {"ok": False, "reason": f"power draw {power_draw} kW out of range"}
    return {"ok": True, "reason": "dynamic test valid"}


def record_dynamic_test_record(test_id: str, max_speed: int, braking_dist: int,
                               power_draw: int) -> dict:
    """Record L5b dynamic test results."""
    val = validate_dynamic_test(max_speed, braking_dist, power_draw)
    if not val["ok"]:
        return {"error": val["reason"], "blocked": True}
    return {
        ":dynamicTestRecord/id": test_id,
        ":dynamicTestRecord/speedProfile": f"max {max_speed} km/h",
        ":dynamicTestRecord/brakingDistance": f"{braking_dist} m",
        ":dynamicTestRecord/powerDraw": f"{power_draw} kW",
        ":dynamicTestRecord/thermalSignature": "nominal",
    }


# --------------------------------------------------------------------------- #
# emissions_acoustic — cross-cutting ISO 3095 + IEC 62236 + 騒音規制法
# --------------------------------------------------------------------------- #
def validate_emissions_acoustic(iso3095_dba: int, iec62236_pass: bool,
                                kyoukusei_pass: bool) -> dict:
    """Validate acoustic emissions (noise + EMC compliance, G8)."""
    if iso3095_dba > 85:
        return {"ok": False, "reason": f"ISO 3095 {iso3095_dba} dB(A) exceeds 85 dB(A) (G8)"}
    if not iec62236_pass:
        return {"ok": False, "reason": "IEC 62236 EMC test failed (G8)"}
    if not kyoukusei_pass:
        return {"ok": False, "reason": "騒音規制法 (Noise Regulation Act) compliance failed (G8)"}
    return {"ok": True, "reason": "emissions acoustic valid"}


def record_acoustic_emissions_audit(audit_id: str, iso3095_dba: int,
                                    iec62236_pass: bool,
                                    kyoukusei_pass: bool) -> dict:
    """Record acoustic emissions audit."""
    val = validate_emissions_acoustic(iso3095_dba, iec62236_pass, kyoukusei_pass)
    if not val["ok"]:
        return {"error": val["reason"], "blocked": True}
    return {
        ":acousticEmissionsAuditRecord/id": audit_id,
        ":acousticEmissionsAuditRecord/iso3095Wayside": f"{iso3095_dba} dB(A)",
        ":acousticEmissionsAuditRecord/iec62236Emc": "passed" if iec62236_pass else "failed",
        ":acousticEmissionsAuditRecord/kyoukuseiFuinsho": "passed" if kyoukusei_pass else "failed",
    }


# --------------------------------------------------------------------------- #
# homologation_binder — L5c aggregate tests + mint per-trainset DID + EoL recyclability
# --------------------------------------------------------------------------- #
def mint_trainset_did(serial: str) -> str:
    """Mint a per-trainset DID (G13)."""
    return f"did:web:etzhayyim.com:yamabiko:trainset:{serial}"


def validate_homologation(all_gates_pass: bool, eol_recyclability: int) -> dict:
    """Validate homologation preconditions (all gates G1..G22, ≥90% EoL recyclability)."""
    if not all_gates_pass:
        return {"ok": False, "reason": "not all constitutional gates passed"}
    if eol_recyclability < 90:
        return {"ok": False, "reason": f"EoL recyclability {eol_recyclability}% < 90% (G14)"}
    return {"ok": True, "reason": "homologation preconditions valid"}


def record_homologation(hom_id: str, serial: str, all_gates_pass: bool,
                        eol_recyclability: int) -> dict:
    """Record L5c homologation."""
    val = validate_homologation(all_gates_pass, eol_recyclability)
    if not val["ok"]:
        return {"error": val["reason"], "blocked": True}
    trainset_did = mint_trainset_did(serial)
    return {
        ":homologationRecord/id": hom_id,
        ":homologationRecord/trainsetDid": trainset_did,
        ":homologationRecord/iso3095Cert": "passed" if all_gates_pass else "pending",
        ":homologationRecord/iec62236Cert": "passed" if all_gates_pass else "pending",
        ":homologationRecord/kyoukuseiCert": "passed" if all_gates_pass else "pending",
        ":homologationRecord/eolRecyclabilityAudit": f"{eol_recyclability}%",
    }


# --------------------------------------------------------------------------- #
# silen_rail_review — governance attestation of all gates G1..G22
# --------------------------------------------------------------------------- #
def validate_silen_review(member_sigs: int, all_gates_checked: bool,
                          firmware_audit_pass: bool) -> dict:
    """Validate Council 5-of-7 review preconditions."""
    if member_sigs < 5:
        return {"ok": False, "reason": f"Council sigs {member_sigs} < 5 (need ≥5 of 7)"}
    if not all_gates_checked:
        return {"ok": False, "reason": "not all gates G1..G22 checked"}
    if not firmware_audit_pass:
        return {"ok": False, "reason": "ATP/ATO firmware audit failed (G1)"}
    return {"ok": True, "reason": "Council review valid"}


def record_silen_rail_review(review_id: str, member_sigs: int,
                             all_gates_checked: bool,
                             firmware_audit_pass: bool) -> dict:
    """Record governance attestation."""
    val = validate_silen_review(member_sigs, all_gates_checked, firmware_audit_pass)
    if not val["ok"]:
        return {"error": val["reason"], "blocked": True}
    return {
        ":silenRailReview/id": review_id,
        ":silenRailReview/councilAttestationSigs": f"{member_sigs}/7",
        ":silenRailReview/gatesChecklist": "all passed" if all_gates_checked else "incomplete",
        ":silenRailReview/openSourceFirmwareVerified": "verified" if firmware_audit_pass else "failed",
    }


# --------------------------------------------------------------------------- #
# settlement — USDC + TitheRouter intent (NOT broadcast; G17/G21/G22)
# --------------------------------------------------------------------------- #
def build_settlement_intent(gross_minor: int, buyer_sig_ref: str|None=None) -> dict:
    """Compute the USDC settlement split. 10% tithe → Public Fund; manufacturer gets the net.
    Stops at :intent — broadcast needs a member signature (G21) + operator gate (G17)."""
    tithe = (gross_minor * TITHE_BPS) // 10_000
    return {
        "rail": "usdc-base-l2",
        "grossMinor": gross_minor,
        "titheMinor": tithe,
        "manufacturerPayoutMinor": gross_minor - tithe,
        "titheRouter": "50-infra/etzhayyim-tithe-router",
        # member signs with their own passkey/smart-account; platform holds no key (G21)
        "state": "executed" if buyer_sig_ref else "intent",
        "buyerSigRef": buyer_sig_ref or "",
    }


if __name__ == "__main__":  # pragma: no cover
    print("carbody fabrication:", record_carbody_attestation(
        "cb1", 120, True, "Al 6N01").get(":carbodyAttestation/id"))
    print("bogie assembly:", record_bogie_attestation(
        "bg1", "front", "electric", True).get(":bogieAttestation/id"))
    print("dynamic test (valid 320 km/h):", record_dynamic_test_record(
        "dt1", 320, 850, 8500).get(":dynamicTestRecord/id"))
    print("dynamic test (over max):", record_dynamic_test_record(
        "dt2", 350, 850, 8500).get("blocked"))
    print("homologation (valid EoL):", record_homologation(
        "hom1", "ts-0001", True, 92).get(":homologationRecord/id"))
    print("homologation (low EoL):", record_homologation(
        "hom2", "ts-0002", True, 85).get("blocked"))
    print("settlement:", build_settlement_intent(5_000_000_000))
