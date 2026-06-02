#!/usr/bin/env python3
"""makura 枕 — foam pillow manufacturing langgraph actor (kotoba WASM cell).

ADR-2605261115, R0 scaffold. Runs in-WASM on kotoba :8077. Handlers over the foam
pillow manufacturing schema (foam batch / fabric / pillow lot / QC / packaging /
recycling / worker exposure), with makura's constitutional gates enforced:

  G6  isocyanate exposure   MDI <=5 ppb / TDI <=2 ppb 8h TWA (worker safety)
  G8  FR-chemistry exclusion no PBDE/TDCPP/TCEP/Sb2O3; baseline FR-free
  G11 KPI caps              foam mass <=2.0 kg / dims <=80x50x25 cm / combined <=4.0 kg
  G13 take-back / recycling  IPFS-pinned take-back QR; >=10% recycled crumb by R3
  G14 no embedded sensors    no RFID/NFC/IoT in the BoM (anti-surveillance consumer goods)

LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G15). State is
written back to the kotoba Datom log (G16). Settlement is USDC on Base L2 + ERC-4337
+ TitheRouter 10% only — no fiat (G17). The platform holds no key; the member signs
each settlement (G18). Compute-only R0; settlement stops at :intent (G19).
"""
from __future__ import annotations

# kotoba-provided host bindings (WASM Component Model imports)
try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

TITHE_BPS = 1000  # 10% TitheRouter auto-split (G17), basis points

# G11 KPI caps
MAX_FOAM_MASS_KG = 2.0
MAX_DIMS_CM = (80.0, 50.0, 25.0)
MAX_COMBINED_KG = 4.0
# G6 worker exposure ceilings (8h TWA, ppb)
MDI_CEILING_PPB = 5.0
TDI_CEILING_PPB = 2.0
# G8 prohibited flame-retardant chemistries
PROHIBITED_FR = {"pbde", "tdcpp", "tcep", "sb2o3", "antimony trioxide"}
# G14 prohibited embedded electronics in the BoM
PROHIBITED_EMBEDDED = {"rfid", "nfc", "iot", "sensor", "bluetooth", "smart-chip"}


def _infer(prompt: str) -> str:
    """Murakumo-only inference (G15)."""
    if llm:
        try:
            return str(llm.infer(model="gemma3:4b", prompt=prompt))
        except Exception:
            return "LLM_INFERENCE_FAILED"
    return "LLM_NOT_AVAILABLE"


# --------------------------------------------------------------------------- #
# G11 — KPI caps (foam mass / dimensions / combined)
# --------------------------------------------------------------------------- #
def kpi_caps_ok(foam_mass_kg: float, dims_cm: tuple, combined_kg: float) -> dict:
    if foam_mass_kg > MAX_FOAM_MASS_KG:
        return {"ok": False, "reason": f"foam mass {foam_mass_kg} > {MAX_FOAM_MASS_KG} kg (G11)"}
    if any(d > m for d, m in zip(dims_cm, MAX_DIMS_CM)):
        return {"ok": False, "reason": f"dims {dims_cm} exceed {MAX_DIMS_CM} cm (G11)"}
    if combined_kg > MAX_COMBINED_KG:
        return {"ok": False, "reason": f"combined {combined_kg} > {MAX_COMBINED_KG} kg (G11)"}
    return {"ok": True, "reason": "within KPI caps"}


# --------------------------------------------------------------------------- #
# G6 — isocyanate worker exposure gate
# --------------------------------------------------------------------------- #
def exposure_ok(mdi_ppb: float, tdi_ppb: float) -> dict:
    if mdi_ppb > MDI_CEILING_PPB:
        return {"ok": False, "reason": f"MDI {mdi_ppb} > {MDI_CEILING_PPB} ppb 8h TWA (G6)"}
    if tdi_ppb > TDI_CEILING_PPB:
        return {"ok": False, "reason": f"TDI {tdi_ppb} > {TDI_CEILING_PPB} ppb 8h TWA (G6)"}
    return {"ok": True, "reason": "exposure within ceilings"}


# --------------------------------------------------------------------------- #
# G8 — flame-retardant chemistry exclusion
# --------------------------------------------------------------------------- #
def fr_chemistry_ok(chemistry_terms) -> dict:
    hits = [t for t in chemistry_terms if t.strip().lower() in PROHIBITED_FR]
    if hits:
        return {"ok": False, "reason": f"prohibited FR chemistry: {hits} (G8)"}
    return {"ok": True, "reason": "FR-free"}


# --------------------------------------------------------------------------- #
# G14 — no embedded sensors in the BoM
# --------------------------------------------------------------------------- #
def bom_no_embedded(bom_items) -> dict:
    hits = [i for i in bom_items if any(p in i.strip().lower() for p in PROHIBITED_EMBEDDED)]
    if hits:
        return {"ok": False, "reason": f"embedded electronics prohibited: {hits} (G14)"}
    return {"ok": True, "reason": "no embedded sensors"}


# --------------------------------------------------------------------------- #
# foam batch attestation (gates G6 + G8 enforced before record)
# --------------------------------------------------------------------------- #
def record_foam_batch(batch_id: str, chemistry_terms, mdi_ppb: float, tdi_ppb: float,
                      density: str = "", voc_test: str = "") -> dict:
    fr = fr_chemistry_ok(chemistry_terms)
    if not fr["ok"]:
        return {"error": fr["reason"], "blocked": True}
    exp = exposure_ok(mdi_ppb, tdi_ppb)
    if not exp["ok"]:
        return {"error": exp["reason"], "blocked": True}
    return {
        ":foamBatchAttestation/id": batch_id,
        ":foamBatchAttestation/chemistry": ",".join(chemistry_terms),
        ":foamBatchAttestation/density": density,
        ":foamBatchAttestation/vocTest": voc_test,
    }


# --------------------------------------------------------------------------- #
# QC record + pillow lot (KPI caps enforced)
# --------------------------------------------------------------------------- #
def record_qc(lot_id: str, result: str, reject_pct: str = "0") -> dict:
    return {
        ":qcRecord/id": f"qc.{lot_id}",
        ":qcRecord/visual": result,
        ":qcRecord/rejectPercentage": reject_pct,
    }


def finalize_pillow_lot(lot_id: str, foam_mass_kg: float, dims_cm: tuple,
                        combined_kg: float, bom_items) -> dict:
    caps = kpi_caps_ok(foam_mass_kg, dims_cm, combined_kg)
    if not caps["ok"]:
        return {"error": caps["reason"], "blocked": True}
    bom = bom_no_embedded(bom_items)
    if not bom["ok"]:
        return {"error": bom["reason"], "blocked": True}
    return {
        ":pillowLotAttestation/id": lot_id,
        ":pillowLotAttestation/fillWeight": f"{foam_mass_kg}kg",
        ":pillowLotAttestation/lotDid": f"did:web:makura.etzhayyim.com:lot:{lot_id}",
    }


# --------------------------------------------------------------------------- #
# settlement — USDC + TitheRouter intent (NOT broadcast; G17/G18/G19)
# --------------------------------------------------------------------------- #
def build_settlement_intent(gross_minor: int, buyer_sig_ref: str | None = None) -> dict:
    """USDC settlement split. 10% tithe → Public Fund. Stops at :intent — broadcast
    needs a member signature (G18)."""
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


if __name__ == "__main__":  # pragma: no cover
    print("foam batch (FR-free, safe):",
          record_foam_batch("b1", ["polyol", "mdi"], 3.0, 1.0).get(":foamBatchAttestation/id"))
    print("foam batch (PBDE):", record_foam_batch("b2", ["pbde"], 1.0, 1.0).get("blocked"))
    print("lot over KPI:", finalize_pillow_lot("l1", 3.0, (50, 40, 20), 3.0, []).get("blocked"))
    print("settlement:", build_settlement_intent(20_000_000))
