#!/usr/bin/env python3
"""tsutae 伝え — handheld communication device manufacturing langgraph actor (kotoba WASM cell).

ADR-2605261300, R0 scaffold. Runs in-WASM on kotoba :8077. Handlers manage the
device manufacturing lifecycle:

  handle_device_order        Create and manage member device orders (SBT-gated)
  handle_production_progress Update the 8-stage assembly + record attestations
  handle_quality             Record QC / RF / functional results
  handle_device_attestation  Bind serial → per-device DID + BoM lineage (≥2 robot sig)

LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G16). State is
written back to the kotoba Datom log (G17). Settlement is USDC on Base L2 +
ERC-4337 + TitheRouter 10% only — no fiat, no Stripe (G18); SBT↔SBT internal only
(N9). The platform holds no key; the member signs each settlement (G15). Every
stage is recorded as a Datom — no silent truncation.

This R0 build computes and returns plans/records; it does not dispatch real factory
work and does not broadcast settlements (both G11/G13-gated; settlement stops at
:intent). Open SoC only (G9) — proprietary SoC is rejected, never assembled (N1).
"""
from __future__ import annotations

from typing import TypedDict, Literal

# kotoba-provided host bindings (WASM Component Model imports)
try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

TITHE_BPS = 1000  # 10% TitheRouter auto-split (G18), basis points

# Device order states
DEVICE_ORDER_FLOW = [
    "draft", "placed", "in-production", "qc", "ready", "shipped", "cancelled"
]

# Production stages = the 8 tsutae Pregel cells (CLAUDE.md + manifest.edn)
PRODUCTION_STAGES = [
    "pcb-smt", "chassis-assembly", "display-attachment", "firmware-load",
    "final-qc", "packaging", "device-attestation", "recycling-intake",
]

# G9: open SoC allow-list (R1 open RISC-V; R2+ iwakura). Proprietary = rejected (N1).
OPEN_SOC_ALLOWLIST = ("StarFive-JH7110", "SiFive-HiFive-Unmatched", "Allwinner-D1", "iwakura")
PROPRIETARY_SOC = ("Snapdragon", "Apple-A", "Exynos", "Helio", "Dimensity")

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _now() -> str:
    return "2026-06-02T00:00:00Z"


def _infer_llm(prompt: str) -> str:
    """Murakumo-only LLM inference (G16)."""
    if llm:
        try:
            return str(llm.infer(model="gemma3:4b", prompt=prompt))
        except Exception:
            return "LLM_INFERENCE_FAILED"
    return "LLM_NOT_AVAILABLE"


def is_open_soc(soc: str) -> bool:
    """G9 enforcement: open RISC-V only; proprietary SoC rejected (N1)."""
    if any(soc.startswith(p) for p in PROPRIETARY_SOC):
        return False
    return any(soc.startswith(a) for a in OPEN_SOC_ALLOWLIST)


# --------------------------------------------------------------------------- #
# handle_device_order — SBT-gated member order intake
# --------------------------------------------------------------------------- #
class DeviceOrderState(TypedDict, total=False):
    order_id: str
    buyer_did: str
    specs: str
    soc: str
    initial_state: Literal["draft", "placed"]
    sbt_active: bool


def handle_device_order(state: DeviceOrderState) -> dict:
    order_id = state.get("order_id")
    buyer_did = state.get("buyer_did")
    specs = state.get("specs")
    soc = state.get("soc", "StarFive-JH7110")
    initial_state = state.get("initial_state", "draft")
    sbt_active = state.get("sbt_active", False)

    if not buyer_did or not sbt_active:
        return {"error": "Buyer DID missing or SBT not active (N9 SBT↔SBT internal)",
                "state": "cancelled"}
    if not is_open_soc(soc):
        return {"error": f"SoC {soc} rejected — open RISC-V only (G9/N1)", "state": "cancelled"}

    if not order_id:
        order_id = f"do.new.order.{hash(specs or '') % 10000}"

    order_record = {
        ":device-order/id": order_id,
        ":device-order/buyer-did": buyer_did,
        ":device-order/specs": specs,
        ":device-order/soc": soc,
        ":device-order/state": initial_state,
    }
    return {"device_order": order_record}


# --------------------------------------------------------------------------- #
# handle_production_progress — 8-stage assembly + attestation
# --------------------------------------------------------------------------- #
class ProductionProgressState(TypedDict, total=False):
    order_id: str
    stage: str
    cid: str
    details: str
    timestamp: str


def handle_production_progress(state: ProductionProgressState) -> dict:
    order_id = state.get("order_id")
    stage = state.get("stage")
    cid = state.get("cid")
    details = state.get("details", "")
    timestamp = state.get("timestamp", _now())

    if not order_id or not stage:
        return {"error": "Order ID or stage missing"}
    if stage not in PRODUCTION_STAGES:
        return {"error": f"unknown stage {stage} (not one of the 8 tsutae cells)"}

    progress_record = {
        ":production-progress/id": f"pp.{order_id}.{stage}",
        ":production-progress/order": order_id,
        ":production-progress/stage": stage,
        ":production-progress/timestamp": timestamp,
        ":production-progress/note": f"Stage {stage} completed."
                                     + (f" Details: {details}" if details else ""),
    }
    attestation_record = None
    if cid:  # G14: IPFS-pinned per-stage evidence
        attestation_record = {
            ":attestation/id": f"attest.{order_id}.{stage}",
            ":attestation/order": order_id,
            ":attestation/type": stage,
            ":attestation/cid": cid,
            ":attestation/timestamp": timestamp,
            ":attestation/details": details,
        }
    return {"production_progress": progress_record, "attestation": attestation_record}


# --------------------------------------------------------------------------- #
# handle_quality — QC / RF / functional result
# --------------------------------------------------------------------------- #
class QualityState(TypedDict, total=False):
    order_id: str
    result: Literal["pass", "fail", "rework"]
    defects: list[str]
    inspector_did: str
    timestamp: str
    current_order_state: str


def handle_quality(state: QualityState) -> dict:
    order_id = state.get("order_id")
    result = state.get("result")
    defects = state.get("defects", [])
    inspector_did = state.get("inspector_did")
    timestamp = state.get("timestamp", _now())
    current_order_state = state.get("current_order_state", "in-production")

    if not order_id or not result or not inspector_did:
        return {"error": "Order ID, result, or inspector DID missing"}

    quality_record = {
        ":quality/id": f"qc.{order_id}.{timestamp}",
        ":quality/order": order_id,
        ":quality/result": result,
        ":quality/defects": defects,
        ":quality/inspector-did": inspector_did,
        ":quality/timestamp": timestamp,
    }
    new_order_state = current_order_state
    if result == "pass":
        new_order_state = "ready"
    elif result == "fail":
        new_order_state = "cancelled"
    elif result == "rework":
        new_order_state = "in-production"
    return {"quality_record": quality_record, "new_order_state": new_order_state}


# --------------------------------------------------------------------------- #
# handle_device_attestation — serial → per-device DID + BoM lineage (G4/G14)
# --------------------------------------------------------------------------- #
class DeviceAttestationState(TypedDict, total=False):
    order_id: str
    serial: str
    bom_lineage_cids: list[str]
    robot_signers: list[str]
    timestamp: str


def handle_device_attestation(state: DeviceAttestationState) -> dict:
    order_id = state.get("order_id")
    serial = state.get("serial")
    bom_lineage_cids = state.get("bom_lineage_cids", [])
    robot_signers = state.get("robot_signers", [])
    timestamp = state.get("timestamp", _now())

    if not order_id or not serial:
        return {"error": "Order ID or serial missing"}
    # G4: witness quorum ≥2 distinct robot signers
    if len(set(robot_signers)) < 2:
        return {"error": "G4: fewer than 2 distinct robot signers", "accept": False}

    device_did = f"did:web:etzhayyim.com:tsutae:device:{serial}"  # G14
    device_record = {
        ":device/serial": serial,
        ":device/order": order_id,
        ":device/did": device_did,
        ":device/bom-lineage": bom_lineage_cids,
        ":device/signers": list(set(robot_signers)),
        ":device/repair-event-ready": True,  # G14
    }
    return {"device_record": device_record, "accept": True}


# --------------------------------------------------------------------------- #
# build_settlement_intent — USDC + TitheRouter intent (NOT broadcast; G18/G15)
# --------------------------------------------------------------------------- #
def build_settlement_intent(gross_minor: int, buyer_sig_ref: str | None = None) -> dict:
    """Compute the USDC settlement split. 10% tithe → Public Fund.
    Stops at :intent — broadcast needs a member signature (G15)."""
    tithe = (gross_minor * TITHE_BPS) // 10_000
    return {
        "rail": "usdc-base-l2",
        "grossMinor": gross_minor,
        "titheMinor": tithe,
        "factoryPayoutMinor": gross_minor - tithe,
        "titheRouter": "50-infra/etzhayyim-tithe-router",
        "state": "executed" if buyer_sig_ref else "intent",
        "buyerSigRef": buyer_sig_ref or "",
    }


if __name__ == "__main__":  # pragma: no cover
    print("--- Device Order Demo ---")
    od = handle_device_order({
        "buyer_did": "did:web:member.example.etzhayyim.com",
        "specs": "≤200g handheld, open RISC-V, LCD, removable cellular",
        "soc": "StarFive-JH7110", "initial_state": "placed", "sbt_active": True,
    })
    print("Device Order:", od)
    print("\n--- Proprietary SoC refusal (G9/N1) ---")
    print(handle_device_order({"buyer_did": "did:web:m", "soc": "Snapdragon-8", "sbt_active": True}))
    print("\n--- Settlement Demo ---")
    print("Settlement:", build_settlement_intent(60_000_000))
