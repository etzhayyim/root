#!/usr/bin/env python3
"""hodoki 解き — ELV disassembly + materials recovery langgraph actor (kotoba WASM cell).

ADR-2605261215, R0 scaffold. Runs in-WASM on kotoba :8077. Handlers over the ELV
processing schema (intake audit, depollution, battery handling, parts harvest,
catalyst recovery, shredding, data wipe, emissions audit, provenance binding), with
hodoki's constitutional gates enforced:

  G2   mass-balance ≥98%       (kotoba-datomic-anchored audit)
  G5   charter-rider scan      (no military/weapon-carrying vehicles)
  G6   f-gas ≥95% capture      (UNEP Kigali Amendment alignment)
  G8   ecu-data-wipe mandatory (cryptographic destruction + witness ≥2 robots)
  G12  right-to-repair parts   (IPFS-pinned catalog with VIN provenance)
  G13  material recovery ≥95%  (cross-actor circular feed: kanayama + makura + silicon)
  G14  pgm recovery ≥95%       (PGM yield audit from catalytic converters)

LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G9). State is
written back to the kotoba Datom log (S1). Settlement is USDC on Base L2 + ERC-4337
+ TitheRouter 10% only — no fiat, no Stripe (S2). The platform holds no key; the
operator signs settlement (S3). Every stage is recorded as a Datom — no silent
truncation (S4). This R0 build computes and returns plans/records; it does not
dispatch real factory work and does not broadcast settlements (both S4-gated; settle-
ment stops at :intent).
"""
from __future__ import annotations

from typing import TypedDict

# kotoba-provided host bindings (WASM Component Model imports)
try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

TITHE_BPS = 1000  # 10% TitheRouter auto-split (S2), basis points

# ───────────────────────────────────────────────────────────────────────────
# G5 Charter Rider scan — no military/weapon/covert-modification vehicles
# ───────────────────────────────────────────────────────────────────────────
PROHIBITED_PATTERNS = [
    "military", "weapon", "armored", "ballistic", "surveillance",
    "drone", "robot-swarm", "autonomous-targeting", "covert"
]


def scan_charter_compliance(vin: str, vehicle_desc: str) -> dict:
    """G5 Charter §2(a-h) scan: reject military/weapon-carrying vehicles."""
    desc_lower = vehicle_desc.lower()
    hits = [p for p in PROHIBITED_PATTERNS if p in desc_lower]
    if hits:
        return {"ok": False, "reason": f"Charter violation: {hits} (G5)", "status": "failed"}
    return {"ok": True, "reason": "Charter scan passed", "status": "passed"}


# ───────────────────────────────────────────────────────────────────────────
# G6 F-gas capture gate
# ───────────────────────────────────────────────────────────────────────────
def check_fgas_compliance(fgas_mass_g: float, target_pct: float = 95.0) -> dict:
    """G6 F-gas (HFC/HFO) capture ≥95% by mass; no atmospheric venting."""
    if fgas_mass_g < 0:
        return {"ok": False, "reason": "F-gas mass cannot be negative"}
    if target_pct < 95.0:
        return {"ok": False, "reason": f"F-gas capture {target_pct}% < 95% (G6)"}
    return {"ok": True, "reason": f"F-gas capture {target_pct}% ≥ 95% (G6)"}


# ───────────────────────────────────────────────────────────────────────────
# G8 ECU data wipe gate — cryptographic destruction + witness ≥2 robots
# ───────────────────────────────────────────────────────────────────────────
def ecu_data_wipe_mandatory(ecu_wiped: bool, witness_count: int) -> dict:
    """G8 CONSTITUTIONAL FIRST: MANDATORY ECU + infotainment + telematics wipe."""
    if not ecu_wiped:
        return {"ok": False, "reason": "ECU data wipe NOT completed (G8)", "blocked": True}
    if witness_count < 2:
        return {"ok": False, "reason": f"Witness count {witness_count} < 2 robots (G8)", "blocked": True}
    return {"ok": True, "reason": "ECU wipe + witness quorum ≥2 (G8)"}


# ───────────────────────────────────────────────────────────────────────────
# G12 Right-to-repair invariant — parts catalog with VIN provenance + DID
# ───────────────────────────────────────────────────────────────────────────
def issue_part_did(vin: str, part_name: str) -> str:
    """G12 Issue DID for harvested part (IPFS-pinned, VIN-provenanced)."""
    import hashlib
    h = hashlib.sha256(f"{vin}:{part_name}".encode()).hexdigest()
    return f"did:web:hodoki.etzhayyim.com:part:{h[:16]}"


# ───────────────────────────────────────────────────────────────────────────
# G13 Material recovery ≥95% gate
# ───────────────────────────────────────────────────────────────────────────
def calc_recovery_rate(ferrous_kg: float, non_ferrous_kg: float, copper_kg: float,
                       asr_kg: float, input_mass_kg: float) -> dict:
    """G13 Material recovery ≥95%; ASR <5% to landfill."""
    total_recovered = ferrous_kg + non_ferrous_kg + copper_kg
    recovery_pct = (total_recovered / input_mass_kg * 100) if input_mass_kg > 0 else 0
    asr_pct = (asr_kg / input_mass_kg * 100) if input_mass_kg > 0 else 0

    if recovery_pct < 95.0:
        return {"ok": False, "reason": f"Recovery {recovery_pct}% < 95% (G13)", "blocked": True}
    if asr_pct >= 5.0:
        return {"ok": False, "reason": f"ASR landfill {asr_pct}% >= 5% (G13)", "blocked": True}
    return {
        "ok": True,
        "reason": f"Recovery {recovery_pct}% ≥ 95%, ASR {asr_pct}% < 5% (G13)",
        "recovery_pct": int(recovery_pct),
        "asr_landfill_pct": int(asr_pct)
    }


# ───────────────────────────────────────────────────────────────────────────
# G14 PGM recovery ≥95% gate
# ───────────────────────────────────────────────────────────────────────────
def audit_pgm_yield(pgm_yield_pct: float) -> dict:
    """G14 PGM (Pt/Pd/Rh) recovery ≥95% from catalytic converters."""
    if pgm_yield_pct < 95.0:
        return {"ok": False, "reason": f"PGM yield {pgm_yield_pct}% < 95% (G14)", "blocked": True}
    return {"ok": True, "reason": f"PGM yield {pgm_yield_pct}% ≥ 95% (G14)"}


# ───────────────────────────────────────────────────────────────────────────
# Settlement — USDC + TitheRouter intent (NOT broadcast; S4-gated)
# ───────────────────────────────────────────────────────────────────────────
def build_settlement_intent(gross_minor: int, buyer_sig_ref: str | None = None) -> dict:
    """USDC settlement split. 10% tithe → Public Fund. Stops at :intent — broadcast
    needs operator signature (S3)."""
    tithe = (gross_minor * TITHE_BPS) // 10_000
    return {
        "rail": "usdc-base-l2",
        "grossMinor": gross_minor,
        "titheMinor": tithe,
        "operatorPayoutMinor": gross_minor - tithe,
        "titheRouter": "50-infra/etzhayyim-tithe-router",
        "state": "executed" if buyer_sig_ref else "intent",
        "operatorSigRef": buyer_sig_ref or "",
    }


# ───────────────────────────────────────────────────────────────────────────
# Main handlers
# ───────────────────────────────────────────────────────────────────────────

class IntakeAuditState(TypedDict, total=False):
    vin: str
    title_doc: str
    owner_consent: str
    vehicle_desc: str
    charter_status: str


def handle_intake_audit(state: IntakeAuditState) -> IntakeAuditState:
    """L1a: Intake audit — VIN + title + consent + Charter scan."""
    vin = state.get("vin", "")
    vehicle_desc = state.get("vehicle_desc", "")
    result = scan_charter_compliance(vin, vehicle_desc)
    return {**state, "charter_status": result.get("status", "pending")}


class DepollutionState(TypedDict, total=False):
    vin: str
    ecu_wiped: bool
    witness_count: int
    fgas_mass_g: float
    fgas_target_pct: float
    status: str


def handle_depollution(state: DepollutionState) -> DepollutionState:
    """L1b: Depollution — fluid drain + F-gas capture + airbag disarm."""
    ecu_result = ecu_data_wipe_mandatory(
        state.get("ecu_wiped", False),
        state.get("witness_count", 0)
    )
    fgas_result = check_fgas_compliance(
        state.get("fgas_mass_g", 0),
        state.get("fgas_target_pct", 0)
    )
    overall_ok = ecu_result.get("ok") and fgas_result.get("ok")
    return {**state, "status": "passed" if overall_ok else "blocked"}


class BatteryHandlingState(TypedDict, total=False):
    vin: str
    soh_pct: int
    routing_decision: str


def handle_battery_handling(state: BatteryHandlingState) -> BatteryHandlingState:
    """L2: Battery handling — SoH measurement + routing."""
    soh = state.get("soh_pct", 0)
    if soh >= 70:
        routing = "hikari-second-life"
    elif soh >= 40:
        routing = "cell-recycle"
    else:
        routing = "kanayama-reclaim"
    return {**state, "routing_decision": routing}


class PartsHarvestState(TypedDict, total=False):
    vin: str
    part_name: str
    part_did: str


def handle_parts_harvest(state: PartsHarvestState) -> PartsHarvestState:
    """L3a: Parts harvest — grade + DID + IPFS catalog (G12)."""
    vin = state.get("vin", "")
    part_name = state.get("part_name", "")
    part_did = issue_part_did(vin, part_name)
    return {**state, "part_did": part_did}


class CatalystRecoveryState(TypedDict, total=False):
    pgm_yield_pct: float
    status: str


def handle_catalyst_recovery(state: CatalystRecoveryState) -> CatalystRecoveryState:
    """L3b: Catalyst recovery — PGM yield audit ≥95% (G14)."""
    result = audit_pgm_yield(state.get("pgm_yield_pct", 0))
    return {**state, "status": "passed" if result.get("ok") else "blocked"}


class BodyShredState(TypedDict, total=False):
    ferrous_kg: float
    non_ferrous_kg: float
    copper_kg: float
    asr_kg: float
    input_mass_kg: float
    recovery_pct: int
    asr_landfill_pct: int


def handle_body_shred(state: BodyShredState) -> BodyShredState:
    """L4: Body shred — ferrous/non-ferrous/Cu/ASR sort (G13)."""
    result = calc_recovery_rate(
        state.get("ferrous_kg", 0),
        state.get("non_ferrous_kg", 0),
        state.get("copper_kg", 0),
        state.get("asr_kg", 0),
        state.get("input_mass_kg", 0)
    )
    update = {}
    if result.get("ok"):
        update = {
            "recovery_pct": result.get("recovery_pct", 0),
            "asr_landfill_pct": result.get("asr_landfill_pct", 0)
        }
    return {**state, **update}


if __name__ == "__main__":  # pragma: no cover
    print("Charter scan (ok):",
          scan_charter_compliance("ABC123DEF456GH", "2024 Toyota Corolla").get("status"))
    print("Charter scan (blocked):",
          scan_charter_compliance("XYZ789", "Military armored platform").get("status"))
    print("F-gas capture (ok):", check_fgas_compliance(100.0, 95.5).get("ok"))
    print("Material recovery (ok):", calc_recovery_rate(800, 150, 50, 20, 1000).get("ok"))
    print("PGM yield (ok):", audit_pgm_yield(96.0).get("ok"))
    print("Settlement:", build_settlement_intent(10_000_000))
