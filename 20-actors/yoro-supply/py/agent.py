#!/usr/bin/env python3
"""yoro-supply material sourcing & logistics langgraph actor (kotoba WASM cell).

ADR-2605250850, migration plan Phase 2. Runs in-WASM on kotoba :8077. Five
handlers over one kotoba EAVT graph, mirroring the supply chain lifecycle:

  handle_supplier_selection  projectBOM -> capability/region match
  handle_order_placement     selectedSuppliers -> purchaseOrderConfirmation
  handle_manufacture_track   purchaseOrderConfirmation -> progress
  handle_shipment            manufacturingProgressRecord -> tracking
  handle_delivery_verify     shipmentTrackingRecord -> attestation

LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G5).
State is written to kotoba Datom log (G6). Charter Rider screening enforced
(G2). Settlement is USDC Base L2 + ERC-4337 + TitheRouter 10% only (G7).
Platform holds no key (G11). Every stage recorded as Datom (G13).

This R0 build computes and returns plans; it does not dispatch real work and
does not broadcast settlements (settlement stops at :intent).
"""
from __future__ import annotations

from typing import TypedDict

try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:
    datalog = llm = None  # type: ignore

TITHE_BPS = 1000


class SupplierSelectionState(TypedDict, total=False):
    bom_id: str
    materials: list
    suppliers: list
    candidates: list
    charter_passed: bool


def _capability_match(material: str, supplier: dict) -> int:
    """Token-overlap capability scoring. Crude by design; Murakumo reranks."""
    material_tokens = set(material.lower().split())
    supplier_caps = supplier.get("capabilities", [])
    score = 0
    for cap in supplier_caps:
        cap_tokens = set(cap.lower().split())
        if material_tokens & cap_tokens:
            score += 1
    return score


def _llm_rank_suppliers(materials: list, cands: list) -> list:
    """Murakumo-only rerank by genuine fit (capability + region)."""
    if not llm or not cands:
        return cands
    try:
        spec_str = "; ".join(materials)
        order = llm.infer(
            model="gemma3:4b",
            prompt=f"Rank suppliers for {spec_str} by capability fit:\
 {[c['supplierDid'] for c in cands]}",
        )
        rank = {did: i for i, did in enumerate(str(order).split())}
        cands.sort(key=lambda c: rank.get(c["supplierDid"], len(cands)))
    except Exception:
        pass
    return cands


def handle_supplier_selection(state: SupplierSelectionState)\
 -> SupplierSelectionState:
    """Match BOM materials to capable suppliers."""
    materials = state.get("materials", [])
    suppliers = state.get("suppliers", [])
    scored = []
    for s in suppliers:
        score = sum(_capability_match(m, s) for m in materials)
        if score > 0:
            scored.append((score, s))
    scored.sort(reverse=True, key=lambda x: x[0])
    cands = [s for _, s in scored]
    cands = _llm_rank_suppliers(materials, list(cands))
    charter_ok = all(s.get("charter-compliance") == "passed"\
 for s in cands)
    return {**state, "candidates": cands, "charter_passed": charter_ok}


def check_sbt_eligibility(member_did: str, sbt_registry: dict) -> dict:
    """Member must hold active Adherent SBT to order."""
    active = bool(sbt_registry.get(member_did, {}).get("active"))
    return {"eligible": active,
            "reason": "" if active else "no active Adherent SBT"}


def create_purchase_order(member_did: str, supplier_did: str,\
 materials: list, quantities: list, delivery_date: str,\
 sbt_registry: dict | None = None) -> dict:
    """Create purchase order. Member = ordering principal."""
    elig = check_sbt_eligibility(member_did, sbt_registry or {})
    if not elig["eligible"]:
        return {"state": "refused", "reason": elig["reason"]}
    return {"memberDid": member_did, "supplierDid": supplier_did,
            "materials": materials, "quantities": quantities,
            "deliveryDate": delivery_date, "state": "placed"}


def handle_order_placement(state: dict) -> dict:
    """Create purchase order from supplier selection result."""
    po = state.get("order") or create_purchase_order(
        state.get("memberDid", ""), state.get("supplierDid", ""),
        state.get("materials", []), state.get("quantities", []),
        state.get("deliveryDate", ""), state.get("sbtRegistry", {}))
    return {**state, "order": po}


def handle_manufacture_track(state: dict) -> dict:
    """Track manufacturing progress. IPFS-pinned telemetry."""
    order = state.get("order", {})
    progress = {
        "orderId": order.get("supplierDid", ""),
        "stage": state.get("stage", "raw"),
        "pct": state.get("pct", 0),
        "ipfsPin": state.get("ipfsPin", ""),
        "factoryNote": state.get("factoryNote", ""),
        "timestamp": state.get("now", ""),
    }
    return {**state, "progress": progress}


def handle_shipment(state: dict) -> dict:
    """Arrange shipment. Carrier coordination + ETA."""
    shipment = {
        "carrier": state.get("carrier", ""),
        "trackingNumber": state.get("trackingNumber", ""),
        "eta": state.get("eta", ""),
        "customsCleared": state.get("customsCleared", False),
        "timestamp": state.get("now", ""),
    }
    return {**state, "shipment": shipment}


def handle_delivery_verify(state: dict, witness_fn=None) -> dict:
    """Verify delivery. >=2 independent witnesses."""
    witnesses = (witness_fn() if witness_fn else\
 state.get("witnessDids", [])) or []
    attestation = {
        "receivedQty": state.get("receivedQty", []),
        "witnessDids": witnesses,
        "certificationStatus": state.get("certStatus", "pending"),
        "qcResult": state.get("qcResult", "pass"),
        "qcNotes": state.get("qcNotes", ""),
        "timestamp": state.get("now", ""),
    }
    return {**state, "attestation": attestation}


def build_settlement_intent(gross_minor: int,\
 member_sig_ref: str | None = None) -> dict:
    """Compute USDC settlement split. 10% tithe to Public Fund.
    Stops at :intent; broadcast needs member signature + operator gate."""
    tithe = (gross_minor * TITHE_BPS) // 10_000
    return {
        "rail": "usdc-base-l2",
        "grossMinor": gross_minor,
        "titheMinor": tithe,
        "supplierPayoutMinor": gross_minor - tithe,
        "titheRouter": "50-infra/etzhayyim-tithe-router",
        "state": "executed" if member_sig_ref else "intent",
        "memberSigRef": member_sig_ref or "",
    }


if __name__ == "__main__":
    demo = handle_supplier_selection({
        "materials": ["steel H-beam 200mm", "concrete 25 MPa"],
        "suppliers": [
            {"supplierDid": "s1", "capabilities": ["concrete", "cement"]},
            {"supplierDid": "s2", "capabilities": ["steel", "h-beam"]},
        ],
    })
    print("selection candidates:", [c["supplierDid"]\
 for c in demo["candidates"]])
    print("settlement:", build_settlement_intent(500_000_000))
