"""Tests for ReleaseSettlementCell — tax warning DMN, one-way boundary, 5-way method dispatch."""

from __future__ import annotations

import pytest

from yobel.cells.release_settlement.cell import (
    build_graph,
    execute_release,
    one_way_boundary_check,
    tax_warning_dmn,
)
from yobel.ports import DebtRow


# ─── tax_warning_dmn (COLLECT hit) ───────────────────────────────────


def test_tax_dmn_usa_caution_severity():
    out = tax_warning_dmn(
        {
            "debtor_did": "did:web:debtor.usa.example",
            "creditor_did": "did:web:creditor.example",
            "released_micro_usdc": 100_000_000,  # $100
            "release_method": "base_l2_transfer",
        }
    )
    assert out["tax_severity"] == "caution"
    assert any("IRC §61(a)(11)" in w for w in out["tax_warnings"])
    assert out["consult_legal_delegate"] is True


def test_tax_dmn_japan_caution():
    out = tax_warning_dmn(
        {
            "debtor_did": "did:web:debtor.jpn.example",
            "creditor_did": "did:web:creditor.example",
            "released_micro_usdc": 1_000_000_000,  # $1000
            "release_method": "voluntary_bookkeeping",
        }
    )
    assert any("日本所得税法" in w for w in out["tax_warnings"])
    assert out["tax_severity"] == "caution"


def test_tax_dmn_high_severity_at_1m_usdc():
    out = tax_warning_dmn(
        {
            "debtor_did": "did:web:debtor.usa.example",
            "creditor_did": "did:web:creditor.usa.example",
            "released_micro_usdc": 1_000_000 * 1_000_000,  # $1M USDC
            "release_method": "base_l2_transfer",
        }
    )
    assert out["tax_severity"] == "high"
    assert any("disguised-gift" in w for w in out["tax_warnings"])


def test_tax_dmn_form_1099c_threshold():
    out = tax_warning_dmn(
        {
            "debtor_did": "did:web:debtor.usa.example",
            "creditor_did": "did:web:creditor.usa.example",
            "released_micro_usdc": 700 * 1_000_000,  # $700 (≥ $600 threshold)
            "release_method": "voluntary_bookkeeping",
        }
    )
    assert any("1099-C" in w for w in out["tax_warnings"])


def test_tax_dmn_no_warnings_below_thresholds():
    out = tax_warning_dmn(
        {
            "debtor_did": "did:web:debtor.unknown.example",
            "creditor_did": "did:web:creditor.unknown.example",
            "released_micro_usdc": 0,
            "release_method": "voluntary_bookkeeping",
        }
    )
    assert out["tax_severity"] == "info"
    assert out["consult_legal_delegate"] is False


# ─── one_way_boundary_check (Charter Rider §2(b)) ────────────────────


def test_one_way_check_accepts_equal_to_cap():
    out = one_way_boundary_check(
        {
            "released_micro_usdc": 100_000_000,
            "debt_principal_micro_usdc": 90_000_000,
            "debt_accrued_micro_usdc": 10_000_000,
        }
    )
    assert out["one_way_compliant"] is True


def test_one_way_check_rejects_over_release():
    out = one_way_boundary_check(
        {
            "released_micro_usdc": 200_000_000,
            "debt_principal_micro_usdc": 90_000_000,
            "debt_accrued_micro_usdc": 10_000_000,
        }
    )
    assert out["one_way_compliant"] is False
    assert "one-way invariant" in out["one_way_violation"]


def test_one_way_check_rejects_negative():
    out = one_way_boundary_check(
        {
            "released_micro_usdc": -1,
            "debt_principal_micro_usdc": 100_000_000,
            "debt_accrued_micro_usdc": 0,
        }
    )
    assert out["one_way_compliant"] is False
    assert "negative" in out["one_way_violation"]


# ─── execute_release: 5-way dispatch ─────────────────────────────────


def test_execute_release_voluntary_bookkeeping_no_tx(base_l2_paymaster, lawfirm_invoke):
    out = execute_release(
        {"release_method": "voluntary_bookkeeping", "creditor_did": "c", "debtor_did": "d", "released_micro_usdc": 100, "rite_id": "r"},
        tithe_router_port=None,
        base_l2_paymaster=base_l2_paymaster,
        lawfirm_invoke=lawfirm_invoke,
    )
    assert out["settlement_ok"] is True
    assert out["base_l2_tx_hash"] == ""
    assert out["lawfirm_invoke_uri"] == ""


def test_execute_release_base_l2_calls_paymaster(base_l2_paymaster, lawfirm_invoke):
    out = execute_release(
        {"release_method": "base_l2_transfer", "creditor_did": "c", "debtor_did": "d", "released_micro_usdc": 100, "rite_id": "r"},
        tithe_router_port=None,
        base_l2_paymaster=base_l2_paymaster,
        lawfirm_invoke=lawfirm_invoke,
    )
    assert out["settlement_ok"] is True
    assert out["base_l2_tx_hash"] == base_l2_paymaster.next_hash


def test_execute_release_base_l2_revert_recorded(base_l2_paymaster, lawfirm_invoke):
    base_l2_paymaster.revert = True
    out = execute_release(
        {"release_method": "base_l2_transfer", "creditor_did": "c", "debtor_did": "d", "released_micro_usdc": 100, "rite_id": "r"},
        tithe_router_port=None,
        base_l2_paymaster=base_l2_paymaster,
        lawfirm_invoke=lawfirm_invoke,
    )
    assert out["settlement_ok"] is False
    assert "revert" in out["settlement_error"]


def test_execute_release_court_order_invokes_lawfirm(base_l2_paymaster, lawfirm_invoke):
    out = execute_release(
        {"release_method": "court_order", "creditor_did": "c", "debtor_did": "d", "released_micro_usdc": 100, "rite_id": "r"},
        tithe_router_port=None,
        base_l2_paymaster=base_l2_paymaster,
        lawfirm_invoke=lawfirm_invoke,
    )
    assert out["settlement_ok"] is True
    assert out["lawfirm_invoke_uri"].startswith("at://fake/lawfirm")


def test_execute_release_sovereign_decree_invokes_lawfirm(base_l2_paymaster, lawfirm_invoke):
    out = execute_release(
        {"release_method": "sovereign_decree", "creditor_did": "c", "debtor_did": "d", "released_micro_usdc": 100, "rite_id": "r"},
        tithe_router_port=None,
        base_l2_paymaster=base_l2_paymaster,
        lawfirm_invoke=lawfirm_invoke,
    )
    assert out["settlement_ok"] is True


def test_execute_release_ecclesiastical_indulgence_no_tx(base_l2_paymaster, lawfirm_invoke):
    out = execute_release(
        {"release_method": "ecclesiastical_indulgence", "creditor_did": "c", "debtor_did": "d", "released_micro_usdc": 0, "rite_id": "r"},
        tithe_router_port=None,
        base_l2_paymaster=base_l2_paymaster,
        lawfirm_invoke=lawfirm_invoke,
    )
    assert out["settlement_ok"] is True


# ─── End-to-end via build_graph ──────────────────────────────────────


def test_e2e_happy_path_base_l2(
    checkpointer, creditor_enrollment_port, envelope_crypto, base_l2_paymaster,
    lawfirm_invoke, anchor_bridge, audit_witness_emit,
):
    creditor_enrollment_port.debts_by_debt_id[
        ("shmita-5786", "did:web:creditor.example", "d1")
    ] = DebtRow(
        debt_id="d1", debtor_did="did:web:debtor.example",
        principal_micro_usdc=100_000_000, accrued_micro_usdc=5_000_000,
        origination_date="2022-01-01T00:00:00Z", instrument="loan",
    )
    graph = build_graph(
        checkpointer=checkpointer,
        creditor_enrollment_port=creditor_enrollment_port,
        envelope_crypto=envelope_crypto,
        tithe_router_port=None,
        base_l2_paymaster=base_l2_paymaster,
        lawfirm_invoke=lawfirm_invoke,
        anchor_bridge=anchor_bridge,
        audit_witness_emit=audit_witness_emit,
    )
    result = graph.invoke(
        {
            "release_id": "rel-shmita-5786-d1",
            "rite_id": "shmita-5786",
            "debt_id": "d1",
            "debtor_did": "did:web:debtor.example",
            "creditor_did": "did:web:creditor.example",
            "release_method": "base_l2_transfer",
            "released_micro_usdc": 100_000_000,
            "released_at": "2026-10-01T00:00:00Z",
        },
        {"configurable": {"thread_id": "test-release-happy"}},
    )
    assert result["release_vertex_uri"].startswith("at://")
    assert len(anchor_bridge.writes) == 1
    assert len(audit_witness_emit.events) == 1
    assert audit_witness_emit.events[0]["event_type"] == "yobel.release_finalized"


def test_e2e_one_way_violation_blocks_anchor(
    checkpointer, creditor_enrollment_port, envelope_crypto, base_l2_paymaster,
    lawfirm_invoke, anchor_bridge, audit_witness_emit,
):
    """released > principal+accrued → Charter Rider §2(b) blocks before settlement."""
    creditor_enrollment_port.debts_by_debt_id[
        ("shmita-5786", "did:web:creditor.example", "d1")
    ] = DebtRow(
        debt_id="d1", debtor_did="did:web:debtor.example",
        principal_micro_usdc=10_000_000, accrued_micro_usdc=0,  # only $10
        origination_date="2022-01-01T00:00:00Z", instrument="loan",
    )
    graph = build_graph(
        checkpointer=checkpointer,
        creditor_enrollment_port=creditor_enrollment_port,
        envelope_crypto=envelope_crypto,
        tithe_router_port=None,
        base_l2_paymaster=base_l2_paymaster,
        lawfirm_invoke=lawfirm_invoke,
        anchor_bridge=anchor_bridge,
        audit_witness_emit=audit_witness_emit,
    )
    result = graph.invoke(
        {
            "release_id": "rel-bad",
            "rite_id": "shmita-5786",
            "debt_id": "d1",
            "debtor_did": "did:web:debtor.example",
            "creditor_did": "did:web:creditor.example",
            "release_method": "base_l2_transfer",
            "released_micro_usdc": 100_000_000,  # Trying to release $100 from $10 debt
            "released_at": "2026-10-01T00:00:00Z",
        },
        {"configurable": {"thread_id": "test-release-violation"}},
    )
    assert result["settlement_ok"] is False
    assert "one-way invariant" in result["settlement_error"]
    assert len(anchor_bridge.writes) == 0
    assert len(audit_witness_emit.events) == 0
