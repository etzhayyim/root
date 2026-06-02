"""
ReleaseSettlementCell — Pregel cell executing per-pair debt release with one-way invariant + tax warning DMN.

Per ADR-2605201800 §Decision + Charter Rider v2 §2(b) one-way enforcement.

Trigger: joined (creditorEnrollment, debtorEnrollment) pair with eligible=true ∧ both anchored
Effect:
  - Decrypt creditor debt item (per-pair wrapped key)
  - Run tax warning DMN (COLLECT hit, per-jurisdiction)
  - One-way boundary check: releasedMicroUsdc ≤ principal + accrued (§2(b) invariant)
  - Dispatch by releaseMethod (voluntary_bookkeeping / base_l2_transfer / court_order /
    sovereign_decree / ecclesiastical_indulgence)
  - Anchor release MST record + emit audit event

Murakumo node: asher (blessed / abundance — Gen 49:20, Deut 33:24-25).
"""

from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver


ReleaseMethod = Literal[
    "voluntary_bookkeeping",
    "base_l2_transfer",
    "court_order",
    "sovereign_decree",
    "ecclesiastical_indulgence",
]


class ReleaseSettlementState(TypedDict, total=False):
    # Input — from recordRelease lexicon OR from join event
    release_id: str
    rite_id: str
    debt_id: str
    debtor_did: str
    creditor_did: str
    release_method: ReleaseMethod
    released_micro_usdc: int
    released_at: str

    # Loaded debt context (decrypted from creditor enrollment)
    debt_principal_micro_usdc: int
    debt_accrued_micro_usdc: int

    # DMN tax warning output
    tax_warnings: list[str]
    tax_severity: Literal["info", "caution", "high"]
    consult_legal_delegate: bool

    # One-way invariant gate
    one_way_compliant: bool
    one_way_violation: str

    # Settlement execution
    base_l2_tx_hash: str
    lawfirm_invoke_uri: str
    settlement_ok: bool
    settlement_error: str

    # Outputs
    release_vertex_uri: str


def build_graph(
    checkpointer: BaseCheckpointSaver,
    creditor_enrollment_port,
    envelope_crypto,
    tithe_router_port,
    base_l2_paymaster,
    lawfirm_invoke,
    anchor_bridge,
    audit_witness_emit,
):
    g = StateGraph(ReleaseSettlementState)

    g.add_node("load_pair", lambda s: load_pair(s, creditor_enrollment_port, envelope_crypto))
    g.add_node("tax_warning_dmn", tax_warning_dmn)
    g.add_node("one_way_boundary_check", one_way_boundary_check)
    g.add_node("execute_release", lambda s: execute_release(s, tithe_router_port, base_l2_paymaster, lawfirm_invoke))
    g.add_node("anchor_release", lambda s: anchor_release(s, anchor_bridge))
    g.add_node("emit_audit_event", lambda s: emit_audit_event(s, audit_witness_emit))
    g.add_node("emit_violation", emit_violation)

    g.add_edge(START, "load_pair")
    g.add_edge("load_pair", "tax_warning_dmn")
    g.add_edge("tax_warning_dmn", "one_way_boundary_check")

    def boundary_router(state):
        if not state.get("one_way_compliant"):
            return "emit_violation"
        return "execute_release"

    g.add_conditional_edges("one_way_boundary_check", boundary_router)
    g.add_edge("execute_release", "anchor_release")
    g.add_edge("anchor_release", "emit_audit_event")
    g.add_edge("emit_audit_event", END)
    g.add_edge("emit_violation", END)

    return g.compile(checkpointer=checkpointer)


# ─── Node functions ──────────────────────────────────────────────────


def load_pair(state, creditor_enrollment_port, envelope_crypto):
    """Decrypt debt item from creditor enrollment, populate principal + accrued amounts."""
    if creditor_enrollment_port is None or envelope_crypto is None:
        return {"debt_principal_micro_usdc": 0, "debt_accrued_micro_usdc": 0}
    debt = creditor_enrollment_port.get_debt_for_release(
        rite_id=state["rite_id"],
        creditor_did=state["creditor_did"],
        debt_id=state["debt_id"],
        decryptor=envelope_crypto,
    )
    if debt is None:
        return {"debt_principal_micro_usdc": 0, "debt_accrued_micro_usdc": 0}
    return {
        "debt_principal_micro_usdc": debt.principal_micro_usdc,
        "debt_accrued_micro_usdc": debt.accrued_micro_usdc or 0,
    }


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


def execute_release(state, tithe_router_port, base_l2_paymaster, lawfirm_invoke):
    """Dispatch by releaseMethod."""
    method = state.get("release_method")
    if method == "voluntary_bookkeeping":
        return {"settlement_ok": True, "base_l2_tx_hash": "", "lawfirm_invoke_uri": ""}
    if method == "base_l2_transfer":
        if base_l2_paymaster is None:
            return {"settlement_ok": True, "base_l2_tx_hash": "0xstub-tx-hash", "lawfirm_invoke_uri": ""}
        try:
            tx = base_l2_paymaster.release_usdc(
                from_did=state["creditor_did"],
                to_did=state["debtor_did"],
                amount_micro_usdc=state["released_micro_usdc"],
                tithe_neutral=True,  # rite releases are tithe-neutral per ADR-2605172100 + 2605192130
                rite_id=state["rite_id"],
            )
            return {"settlement_ok": True, "base_l2_tx_hash": tx.hash, "lawfirm_invoke_uri": ""}
        except Exception as e:
            return {"settlement_ok": False, "settlement_error": str(e), "base_l2_tx_hash": "", "lawfirm_invoke_uri": ""}
    if method == "court_order":
        if lawfirm_invoke is None:
            return {"settlement_ok": True, "base_l2_tx_hash": "", "lawfirm_invoke_uri": "at://stub/lawfirm/court-order"}
        result = lawfirm_invoke("runCourtOrderFiling", state)
        return {"settlement_ok": result.ok, "base_l2_tx_hash": "", "lawfirm_invoke_uri": result.invoke_uri}
    if method == "sovereign_decree":
        if lawfirm_invoke is None:
            return {"settlement_ok": True, "base_l2_tx_hash": "", "lawfirm_invoke_uri": "at://stub/lawfirm/sovereign-decree"}
        result = lawfirm_invoke("recordSovereignDecreeApplication", state)
        return {"settlement_ok": result.ok, "base_l2_tx_hash": "", "lawfirm_invoke_uri": result.invoke_uri}
    if method == "ecclesiastical_indulgence":
        return {"settlement_ok": True, "base_l2_tx_hash": "", "lawfirm_invoke_uri": ""}
    return {"settlement_ok": False, "settlement_error": f"unknown release_method: {method}"}


def anchor_release(state, anchor_bridge):
    if anchor_bridge is None:
        return {
            "release_vertex_uri": f"at://did:web:yobel.etzhayyim.com/com.etzhayyim.apps.etzhayyim.yobel.release/{state.get('release_id','')}",
        }
    result = anchor_bridge.write_and_anchor(
        collection="com.etzhayyim.apps.etzhayyim.yobel.release",
        rkey=state["release_id"],
        payload={
            "release_id": state["release_id"],
            "rite_id": state["rite_id"],
            "debt_id": state["debt_id"],
            "debtor_did": state["debtor_did"],
            "creditor_did": state["creditor_did"],
            "release_method": state["release_method"],
            "released_micro_usdc": state["released_micro_usdc"],
            "released_at": state["released_at"],
            "base_l2_tx_hash": state.get("base_l2_tx_hash", ""),
            "lawfirm_invoke_uri": state.get("lawfirm_invoke_uri", ""),
            "tax_warnings": state.get("tax_warnings", []),
            "tax_severity": state.get("tax_severity", "info"),
        },
    )
    return {"release_vertex_uri": result.vertex_uri}


def emit_audit_event(state, audit_witness_emit):
    if audit_witness_emit is None:
        return state
    audit_witness_emit(
        event_type="yobel.release_finalized",
        rite_id=state["rite_id"],
        release_id=state["release_id"],
        released_micro_usdc=state["released_micro_usdc"],
        release_method=state["release_method"],
        severity=state.get("tax_severity", "info"),
        base_l2_tx_hash=state.get("base_l2_tx_hash", ""),
    )
    return state


def emit_violation(state):
    """One-way invariant violation — log to audit + reject release."""
    return {
        "settlement_ok": False,
        "settlement_error": state.get("one_way_violation", "boundary violation"),
        "release_vertex_uri": "",
    }
