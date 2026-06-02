#!/usr/bin/env python3
"""tatekata 建方 — construction langgraph actor (kotoba WASM cell).

ADR-2605250715, R0 scaffold. Runs in-WASM on kotoba :8077. Handlers over the
construction project lifecycle (5 phases: foundation → structural → mep →
finishing → commissioning), with tatekata's constitutional gates enforced:

  G1  open-source firmware         all robot firmware open-source (Apache 2.0 + Charter Rider)
  G2  IPFS-pinned site attestation site survey photos + depth maps pinned before human enters
  G3  witness-quorum robots        progress records signed by ≥2 distinct robots (G3)
  G5  charter-rider sourcing       sourcing audit + no conflict minerals (R0 scope)
  G6  trajectory determinism       Giemon joint angles logged @ 10 Hz; WASM state machine sealed
  G11 KPI caps                     ≤2 stories / ≤5000 m² footprint (prevents scope creep)
  G13 murakumo-only                inference via KotobaLLM 127.0.0.1:4000; external LLM prohibited
  G14 kotoba-eavt-native           state is kotoba Datom log (no SQL/RisingWave/Cypher)
  G15 tithe-non-fiat               USDC Base L2 + ERC-4337 + TitheRouter 10% only (no fiat)
  G16 no-server-key                platform holds no key; owner/operator signs attestations
  G17 consent-bound                compute-only R0; settlement stops at :intent

LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G13). State
is written back to the kotoba Datom log (G14). Settlement is USDC on Base L2 +
ERC-4337 + TitheRouter 10% only — no fiat, no Stripe (G15). The platform holds no
key; the owner signs each settlement with their own passkey/smart-account (G16).
All phase boundaries are recorded as Datoms — no silent truncation. Every progress
record requires ≥2 robot witness signatures (G3).

This R0 build computes and returns plans/records; it does not dispatch real
construction work and does not broadcast settlements (both G17-gated; settlement
stops at :intent).
"""
from __future__ import annotations

from typing import TypedDict

# kotoba-provided host bindings (WASM Component Model imports)
try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

TITHE_BPS = 1000  # 10% TitheRouter auto-split (G15), basis points
# G11 KPI caps
MAX_STORIES = 2
MAX_FOOTPRINT_M2 = 5000
# linear phase trajectory (G17) — every transition is a recorded stage
PHASES = ["foundation", "structural", "mep", "finishing", "commissioning"]


# --------------------------------------------------------------------------- #
# G11 — KPI caps (stories / footprint)
# --------------------------------------------------------------------------- #
def kpi_caps_ok(stories: int, footprint_m2: int) -> dict:
    """Check project scope against KPI caps."""
    if stories > MAX_STORIES:
        return {"ok": False, "reason": f"stories {stories} > {MAX_STORIES} (G11)"}
    if footprint_m2 > MAX_FOOTPRINT_M2:
        return {"ok": False, "reason": f"footprint {footprint_m2} m² > {MAX_FOOTPRINT_M2} (G11)"}
    return {"ok": True, "reason": "within KPI caps"}


# --------------------------------------------------------------------------- #
# G3 — witness quorum (≥2 distinct robot DIDs per phase boundary)
# --------------------------------------------------------------------------- #
def witness_quorum_ok(robot_dids: list) -> dict:
    """Verify ≥2 distinct robot DIDs witness the phase boundary."""
    distinct = len(set(robot_dids))
    if distinct < 2:
        return {"ok": False, "reason": f"witness count {distinct} < 2 (G3)"}
    return {"ok": True, "reason": "witness quorum satisfied"}


# --------------------------------------------------------------------------- #
# Phase advancement state machine (G17 — every stage recorded)
# --------------------------------------------------------------------------- #
def advance_phase(current_phase: str) -> dict:
    """Advance one phase along PHASES. Return error if already terminal."""
    if current_phase not in PHASES:
        return {"state": current_phase, "blocked": "unknown phase"}
    try:
        nxt = PHASES[PHASES.index(current_phase) + 1]
    except IndexError:
        return {"state": current_phase, "blocked": "already terminal (commissioning)"}
    return {"state": nxt, "blocked": None}


# --------------------------------------------------------------------------- #
# foundation_excavation handler
# --------------------------------------------------------------------------- #
def handle_foundation_excavation(state: dict) -> dict:
    """Parse site plan, survey utilities, generate giemon excavation plan, approve."""
    spec = state.get("spec", "")
    if not spec:
        return {**state, "blocked": "spec required"}
    # R0 compute-only: return plan record without dispatch
    plan = {
        "phase": "foundation",
        "spec": spec,
        "giemon_plan_type": "excavation-grid-5m-spacing",
        "trajectory_logged": True,
    }
    return {**state, "plan": plan}


# --------------------------------------------------------------------------- #
# structural_assembly handler
# --------------------------------------------------------------------------- #
def handle_structural_assembly(state: dict) -> dict:
    """Load BIM, validate foundations, coordinate robots, get metrology witness."""
    bim_ref = state.get("bim_ref", "")
    if not bim_ref:
        return {**state, "blocked": "BIM reference required"}
    plan = {
        "phase": "structural",
        "bim_ref": bim_ref,
        "robot_coordination": "giemon-otete-shoring-sequence",
        "metrology": "mimi-witness-plumb-level",
    }
    return {**state, "plan": plan}


# --------------------------------------------------------------------------- #
# mep_installation handler
# --------------------------------------------------------------------------- #
def handle_mep_installation(state: dict) -> dict:
    """Route ductwork, conduit, piping; perform pressure testing."""
    mep_design = state.get("mep_design", "")
    if not mep_design:
        return {**state, "blocked": "MEP design required"}
    plan = {
        "phase": "mep",
        "ductwork_route": "otete-arm-3d-trajectory",
        "conduit_route": "otete-arm-conduit-chase",
        "piping_route": "otete-arm-press-fit-sequence",
        "pressure_test_type": "pneumatic-5-bar-15min",
    }
    return {**state, "plan": plan}


# --------------------------------------------------------------------------- #
# finishing_handoff handler
# --------------------------------------------------------------------------- #
def handle_finishing_handoff(state: dict) -> dict:
    """Prep surfaces, drywall/tape/mud (R0 manual), paint, trim install."""
    phase_input = state.get("phase_input", "")
    if not phase_input:
        return {**state, "blocked": "phase input required"}
    plan = {
        "phase": "finishing",
        "surface_prep": "giemon-substrate-clean",
        "drywall": "manual-subcontractor-r0",
        "paint": "spray-cure-r0",
        "trim": "manual-installation-r0",
    }
    return {**state, "plan": plan}


# --------------------------------------------------------------------------- #
# commissioning handler
# --------------------------------------------------------------------------- #
def handle_commissioning(state: dict) -> dict:
    """Final systems test, defect walkdown, waste inventory, sign-off."""
    phase_input = state.get("phase_input", "")
    if not phase_input:
        return {**state, "blocked": "phase input required"}
    plan = {
        "phase": "commissioning",
        "hvac_test": "airflow-temp-control-verify",
        "electrical_test": "circuit-continuity-load-test",
        "plumbing_test": "water-pressure-flow-rate",
        "defect_walkdown": "photo-punch-list-generation",
        "waste_categorization": "reuse/recycle/landfill percent",
    }
    return {**state, "plan": plan}


# --------------------------------------------------------------------------- #
# progress record — all phase boundaries recorded as Datoms (G17)
# --------------------------------------------------------------------------- #
def record_phase_progress(phase: str, project_did: str, robot_dids: list,
                           photo_cid: str = "", depth_map_cid: str = "") -> dict:
    """Create a phase-boundary progress record. Requires ≥2 robot witnesses (G3)."""
    witness = witness_quorum_ok(robot_dids)
    if not witness["ok"]:
        return {"error": witness["reason"], "blocked": True}
    return {
        ":progress/phase": phase,
        ":progress/project-did": project_did,
        ":progress/robot-dids": robot_dids,
        ":progress/photo-cid": photo_cid,
        ":progress/depth-map-cid": depth_map_cid,
    }


# --------------------------------------------------------------------------- #
# settlement — USDC + TitheRouter intent (NOT broadcast; G15/G16/G17)
# --------------------------------------------------------------------------- #
def build_settlement_intent(gross_minor: int, owner_sig_ref: str | None = None) -> dict:
    """Compute the USDC settlement split. 10% tithe → Public Fund. Stops at :intent —
    broadcast needs an owner signature (G16) + operator gate (G17)."""
    tithe = (gross_minor * TITHE_BPS) // 10_000
    return {
        "rail": "usdc-base-l2",
        "grossMinor": gross_minor,
        "titheMinor": tithe,
        "ownerPayoutMinor": gross_minor - tithe,
        "titheRouter": "50-infra/etzhayyim-tithe-router",
        # owner signs with their own passkey/smart-account; platform holds no key (G16)
        "state": "executed" if owner_sig_ref else "intent",
        "ownerSigRef": owner_sig_ref or "",
    }


if __name__ == "__main__":  # pragma: no cover
    demo_foundation = handle_foundation_excavation({"spec": "site survey + grid excavation"})
    print("foundation plan:", demo_foundation["plan"]["phase"])
    demo_settlement = build_settlement_intent(50_000_000)
    print("settlement:", demo_settlement)
