"""Tests for CreditorEnrollmentCell — signedConsent verify, historical-record gate, §2(b) instrument gate."""

from __future__ import annotations

import pytest

from yobel.cells.creditor_enrollment.cell import (
    build_graph,
    historical_record_gate,
    instrument_safety_gate,
    validate_input,
)
from yobel.ports import Rite


# ─── validate_input ──────────────────────────────────────────────────


def test_validate_input_happy():
    out = validate_input(
        {
            "creditor_did": "did:web:creditor.example",
            "signed_consent": "0xdeadbeef",
            "debts": [
                {
                    "debt_id": "d1",
                    "debtor_did": "did:web:debtor.example",
                    "principal_micro_usdc": 100_000_000,
                    "origination_date": "2020-01-01T00:00:00Z",
                    "instrument": "loan",
                }
            ],
        }
    )
    assert out["input_valid"] is True


def test_validate_input_empty_debts_fails():
    out = validate_input(
        {
            "creditor_did": "did:web:creditor.example",
            "signed_consent": "0xdeadbeef",
            "debts": [],
        }
    )
    assert out["input_valid"] is False
    assert any("debts[]" in e for e in out["input_errors"])


def test_validate_input_caps_at_1000():
    debts = [
        {"debt_id": f"d{i}", "principal_micro_usdc": 1, "origination_date": "2020-01-01T00:00:00Z"}
        for i in range(1001)
    ]
    out = validate_input(
        {"creditor_did": "did", "signed_consent": "0x", "debts": debts}
    )
    assert out["input_valid"] is False


def test_validate_input_negative_principal_fails():
    out = validate_input(
        {
            "creditor_did": "did:web:creditor.example",
            "signed_consent": "0xdeadbeef",
            "debts": [{"debt_id": "d1", "principal_micro_usdc": -1, "origination_date": "2020-01-01T00:00:00Z"}],
        }
    )
    assert out["input_valid"] is False
    assert any("principalMicroUsdc" in e for e in out["input_errors"])


# ─── historical_record_gate ──────────────────────────────────────────


def test_historical_record_gate_accepts_pre_cycle_debt():
    out = historical_record_gate(
        {
            "rite_effective_date": "2026-09-26T00:00:00Z",
            "debts": [
                {"origination_date": "2020-01-01T00:00:00Z"},
                {"origination_date": "2025-12-31T23:59:59Z"},
            ],
        }
    )
    assert out["historical_record_compliant"] is True


def test_historical_record_gate_rejects_post_cycle_debt():
    out = historical_record_gate(
        {
            "rite_effective_date": "2026-09-26T00:00:00Z",
            "debts": [
                {"origination_date": "2020-01-01T00:00:00Z"},
                {"origination_date": "2026-12-01T00:00:00Z"},  # AFTER cycle start
            ],
        }
    )
    assert out["historical_record_compliant"] is False
    assert any("new debt origination not allowed" in v for v in out["historical_record_violations"])


# ─── instrument_safety_gate ──────────────────────────────────────────


def test_instrument_safety_gate_accepts_normal_instruments():
    out = instrument_safety_gate(
        {"debts": [{"instrument": "loan"}, {"instrument": "promissory_note"}, {"instrument": "mortgage"}]}
    )
    assert out["instrument_safety_compliant"] is True


def test_instrument_safety_gate_rejects_margin_call():
    """Charter Rider §2(b) — defense in depth even though lexicon enum excludes."""
    out = instrument_safety_gate(
        {"debts": [{"instrument": "loan"}, {"instrument": "margin_call"}]}
    )
    assert out["instrument_safety_compliant"] is False
    assert any("§2(b)" in v for v in out["instrument_violations"])


# ─── End-to-end via build_graph ──────────────────────────────────────


def test_e2e_happy_path(
    checkpointer, rite_registry, council_sbt, charter_compliance, erc725, envelope_crypto, anchor_bridge
):
    rite_registry.rites["shmita-5786"] = Rite(
        rite_id="shmita-5786",
        rite_type="shmita_7yr",
        status="active",
        effective_date="2026-09-26T00:00:00Z",
        expiry_date=None,
        scope="etzhayyim",
        scope_jurisdictions=["ALL"],
        issuer_did="did:web:etzhayyim.com:steward-001",
        doctrinal_basis="Lev 25",
    )
    council_sbt.levels["did:web:creditor.example"] = 2
    erc725.valid_signers.add(("did:web:creditor.example", "0xgoodsig"))
    graph = build_graph(
        checkpointer=checkpointer,
        rite_registry_port=rite_registry,
        council_sbt_port=council_sbt,
        charter_compliance_port=charter_compliance,
        erc725_port=erc725,
        envelope_crypto=envelope_crypto,
        anchor_bridge=anchor_bridge,
    )
    result = graph.invoke(
        {
            "rite_id": "shmita-5786",
            "creditor_did": "did:web:creditor.example",
            "signed_consent": "0xgoodsig",
            "debts": [
                {
                    "debt_id": "d1",
                    "debtor_did": "did:web:debtor1.example",
                    "principal_micro_usdc": 500_000_000,  # $500 USDC
                    "accrued_micro_usdc": 5_000_000,
                    "origination_date": "2022-01-01T00:00:00Z",
                    "instrument": "loan",
                }
            ],
        },
        {"configurable": {"thread_id": "test-credit-happy"}},
    )
    assert result["debt_count"] == 1
    assert result["enrollment_vertex_uri"].startswith("at://")
    assert len(anchor_bridge.writes) == 1


def test_e2e_rejects_bad_signature(
    checkpointer, rite_registry, council_sbt, charter_compliance, erc725, envelope_crypto, anchor_bridge
):
    rite_registry.rites["shmita-5786"] = Rite(
        rite_id="shmita-5786", rite_type="shmita_7yr", status="active",
        effective_date="2026-09-26T00:00:00Z", expiry_date=None,
        scope="etzhayyim", scope_jurisdictions=["ALL"],
        issuer_did="did:web:etzhayyim.com:steward-001", doctrinal_basis="Lev 25",
    )
    council_sbt.levels["did:web:creditor.example"] = 2
    # Note: erc725.valid_signers is EMPTY — signature is bogus
    graph = build_graph(
        checkpointer=checkpointer,
        rite_registry_port=rite_registry,
        council_sbt_port=council_sbt,
        charter_compliance_port=charter_compliance,
        erc725_port=erc725,
        envelope_crypto=envelope_crypto,
        anchor_bridge=anchor_bridge,
    )
    result = graph.invoke(
        {
            "rite_id": "shmita-5786",
            "creditor_did": "did:web:creditor.example",
            "signed_consent": "0xbadsig",
            "debts": [
                {
                    "debt_id": "d1",
                    "debtor_did": "did:web:debtor.example",
                    "principal_micro_usdc": 100_000_000,
                    "origination_date": "2022-01-01T00:00:00Z",
                    "instrument": "loan",
                }
            ],
        },
        {"configurable": {"thread_id": "test-credit-badsig"}},
    )
    assert result["enrollment_vertex_uri"] == ""
    assert len(anchor_bridge.writes) == 0


def test_e2e_rejects_post_cycle_debt(
    checkpointer, rite_registry, council_sbt, charter_compliance, erc725, envelope_crypto, anchor_bridge
):
    rite_registry.rites["shmita-5786"] = Rite(
        rite_id="shmita-5786", rite_type="shmita_7yr", status="active",
        effective_date="2026-09-26T00:00:00Z", expiry_date=None,
        scope="etzhayyim", scope_jurisdictions=["ALL"],
        issuer_did="did:web:etzhayyim.com:steward-001", doctrinal_basis="Lev 25",
    )
    council_sbt.levels["did:web:creditor.example"] = 2
    erc725.valid_signers.add(("did:web:creditor.example", "0xgoodsig"))
    graph = build_graph(
        checkpointer=checkpointer,
        rite_registry_port=rite_registry,
        council_sbt_port=council_sbt,
        charter_compliance_port=charter_compliance,
        erc725_port=erc725,
        envelope_crypto=envelope_crypto,
        anchor_bridge=anchor_bridge,
    )
    result = graph.invoke(
        {
            "rite_id": "shmita-5786",
            "creditor_did": "did:web:creditor.example",
            "signed_consent": "0xgoodsig",
            "debts": [
                {
                    "debt_id": "d1",
                    "debtor_did": "did:web:debtor.example",
                    "principal_micro_usdc": 100_000_000,
                    "origination_date": "2027-01-01T00:00:00Z",  # POST cycle — rejected
                    "instrument": "loan",
                }
            ],
        },
        {"configurable": {"thread_id": "test-credit-postcycle"}},
    )
    assert result["enrollment_vertex_uri"] == ""
    assert len(anchor_bridge.writes) == 0
