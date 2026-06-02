from __future__ import annotations
from typing import Any, Literal
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Node functions

def load_pair(state):
    """Decrypt debt item from creditor enrollment, populate principal + accrued amounts."""
    # In standalone WASM, external ports are None.
    # Original logic: if creditor_enrollment_port is None or envelope_crypto is None:
    return {"debt_principal_micro_usdc": 0, "debt_accrued_micro_usdc": 0}


def tax_warning_dmn(state):
    """COLLECT-hit DMN per dmn/tax-warning-by-jurisdiction.md."""
    warnings: list[str] = []
    severity_rank = 0  # 0=info, 1=caution, 2=high
    released_usdc = state.get("released_micro_usdc", 0) // 1_000_000
    debtor_jur = (state.get("debtor_did", "") or "").upper()
    creditor_jur = (state.get("creditor_did", "") or "").upper()

    def bump(level: str) -> int:
        return {"info": 0, "caution": 1, "high": 2}[level]

    def add(msg: str, level: str):
        nonlocal severity_rank
        warnings.append(msg)
        severity_rank = max(severity_rank, bump(level))

    if "USA" in debtor_jur and released_usdc >= 1:
        add("US IRC §61(a)(11): cancellation-of-debt income generally taxable. Exclusions: §108(a)(1)(A-E). File Form 982 + creditor Form 1099-C.", "caution")
        if state.get("release_method") == "ecclesiastical_indulgence" or state.get("release_method") == "voluntary_bookkeeping":
            add("US IRC §170(c)(1): religious-org gifts may have different treatment than commercial debt forgiveness.", "caution")
    if "JPN" in debtor_jur and released_usdc >= 1:
        add("日本所得税法 §36(1) + §44-2: 債務免除益は原則として一時所得または雑所得。資力喪失中の免除は §44-2 適用で非課税の余地。", "caution")
    if "DEU" in debtor_jur and released_usdc >= 1:
        add("Deutsches EStG §15 + §17: Schuldenerlass kann Betriebseinnahme darstellen. §3 Nr. 66 Sanierungsklausel applies in restructuring context only.", "caution")
    if "GBR" in debtor_jur and released_usdc >= 1:
        add("UK ITTOIA 2005 §249: release of debt deemed income if previously deductible. ESC C16 / SP D32 may apply.", "caution")
    if "FRA" in debtor_jur and released_usdc >= 1:
        add("Code général des impôts art. 39-1: abandon de créance commercial = recette imposable; religieux voluntary release: position fiscale incertaine.", "caution")
    if "ISR" in debtor_jur and state.get("rite_type") in ("shmita_7yr", "yobel_50yr"):
        add("Israel: prozbul (Hillel) historically routes around shmita debt cancellation; modern Pkudat Mas Hachnasa does not auto-recognize religious shmita as tax-exempt.", "caution")
    if released_usdc >= 1_000_000:
        add("Releases ≥ $1M USDC trigger anti-abuse / disguised-gift rules in many jurisdictions. Coordinate with vendor:lawfirm.etzhayyim.com before settlement.", "high")
    elif released_usdc >= 100:
        add("Release amount may exceed gift tax annual exclusion in many jurisdictions. Verify jurisdiction-specific gift tax rules.", "info")
    if "USA" in debtor_jur and "USA" in creditor_jur and released_usdc >= 600:
        add("US IRS Form 1099-C threshold (≥ $600). Creditor may have reporting obligation independent of yobel rite.", "info")

    severity = {0: "info", 1: "caution", 2: "high"}[severity_rank]
    return {
        "tax_warnings": warnings,
        "tax_severity": severity,
        "consult_legal_delegate": severity_rank >= 1,
    }


def one_way_boundary_check(state):
    """releasedMicroUsdc ≤ debt.principalMicroUsdc + debt.accruedMicroUsdc (Charter Rider §2(b))."""
    released = state.get("released_micro_usdc", 0)
    cap = state.get("debt_principal_micro_usdc", 0) + state.get("debt_accrued_micro_usdc", 0)
    if released < 0:
        return {"one_way_compliant": False, "one_way_violation": f"negative release amount {released}"}
    if released > cap:
        return {"one_way_compliant": False, "one_way_violation": f"release {released} > debt cap {cap} (§2(b) one-way invariant)"}
    return {"one_way_compliant": True, "one_way_violation": ""}


def execute_release(state):
    """Dispatch by releaseMethod."""
    method = state.get("release_method")
    if method == "voluntary_bookkeeping":
        return {"settlement_ok": True, "base_l2_tx_hash": "", "lawfirm_invoke_uri": ""}
    if method == "base_l2_transfer":
        # Original logic: if base_l2_paymaster is None:
        return {"settlement_ok": True, "base_l2_tx_hash": "0xstub-tx-hash", "lawfirm_invoke_uri": ""}
    if method == "court_order":
        # Original logic: if lawfirm_invoke is None:
        return {"settlement_ok": True, "base_l2_tx_hash": "", "lawfirm_invoke_uri": "at://stub/lawfirm/court-order"}
    if method == "sovereign_decree":
        # Original logic: if lawfirm_invoke is None:
        return {"settlement_ok": True, "base_l2_tx_hash": "", "lawfirm_invoke_uri": "at://stub/lawfirm/sovereign-decree"}
    if method == "ecclesiastical_indulgence":
        return {"settlement_ok": True, "base_l2_tx_hash": "", "lawfirm_invoke_uri": ""}
    return {"settlement_ok": False, "settlement_error": f"unknown release_method: {method}"}


def anchor_release(state):
    # Original logic: if anchor_bridge is None:
    return {
        "release_vertex_uri": f"at://did:web:yobel.etzhayyim.com/com.etzhayyim.apps.etzhayyim.yobel.release/{state.get('release_id','')}",
    }


def emit_audit_event(state):
    # Original logic: if audit_witness_emit is None: return state
    return state


def emit_violation(state):
    """One-way invariant violation — log to audit + reject release."""
    return {
        "settlement_ok": False,
        "settlement_error": state.get("one_way_violation", "boundary violation"),
        "release_vertex_uri": "",
    }

def boundary_router(state):
    if not state.get("one_way_compliant"):
        return "emit_violation"
    return "execute_release"


# Graph builder

_g = StateGraph(dict)

_g.add_node("load_pair", load_pair)
_g.add_node("tax_warning_dmn", tax_warning_dmn)
_g.add_node("one_way_boundary_check", one_way_boundary_check)
_g.add_node("execute_release", execute_release)
_g.add_node("anchor_release", anchor_release)
_g.add_node("emit_audit_event", emit_audit_event)
_g.add_node("emit_violation", emit_violation)

_g.add_edge(START, "load_pair")
_g.add_edge("load_pair", "tax_warning_dmn")
_g.add_edge("tax_warning_dmn", "one_way_boundary_check")
_g.add_conditional_edges("one_way_boundary_check", boundary_router)
_g.add_edge("execute_release", "anchor_release")
_g.add_edge("anchor_release", "emit_audit_event")
_g.add_edge("emit_audit_event", END)
_g.add_edge("emit_violation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
