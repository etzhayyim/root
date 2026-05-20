"""Tests for DebtorEnrollmentCell — DMN eligibility (R12 SBT, R13 §2(b), R1-R11 rite-type rules)."""

from __future__ import annotations

import pytest

from yobel.cells.debtor_enrollment.cell import build_graph, run_eligibility_dmn
from yobel.ports import DebtRow, Rite


# ─── DMN R14: natural-person-only gate (highest-priority short-circuit) ──


def test_dmn_r14_legal_person_sbt_rejects_all_rite_types():
    """Even if SBT level is high and instruments are clean, legal_person entityType → R14 reject."""
    for rite_type in ("shmita_7yr", "yobel_50yr", "tokusei_rei", "religious_jubilee", "political_amnesty"):
        out = run_eligibility_dmn(
            {
                "debtor_sbt_level": 5,
                "debtor_entity_type": "natural_person",        # declared OK
                "debtor_sbt_entity_type": "legal_person",      # but SBT says legal_person
                "debtor_community_member": True,
                "rite_type": rite_type,
                "rite_effective_date": "2026-09-26T00:00:00Z",
                "rite_jurisdiction_scope": ["ALL"],
                "debtor_jurisdiction_iso3": "JPN",
                "matched_debts": [{"instrument": "loan", "origination_date": "2024-01-01T00:00:00Z"}],
            }
        )
        assert out["eligible"] is False, f"R14 (legal_person SBT) failed for {rite_type}"
        assert out["dmn_rule_fired"] == "R14"


def test_dmn_r14_declared_legal_person_rejects():
    """Declared debtorEntityType=legal_person → R14 reject (caller cannot lie)."""
    out = run_eligibility_dmn(
        {
            "debtor_sbt_level": 5,
            "debtor_entity_type": "legal_person",
            "debtor_sbt_entity_type": "natural_person",
            "debtor_community_member": True,
            "rite_type": "shmita_7yr",
            "rite_effective_date": "2026-09-26T00:00:00Z",
            "rite_jurisdiction_scope": ["ALL"],
            "matched_debts": [],
        }
    )
    assert out["eligible"] is False
    assert out["dmn_rule_fired"] == "R14"


def test_dmn_r14_unset_entity_type_rejects():
    """Missing entity_type (neither declared nor SBT) → R14 reject."""
    out = run_eligibility_dmn(
        {
            "debtor_sbt_level": 5,
            "debtor_community_member": True,
            "rite_type": "shmita_7yr",
            "rite_effective_date": "2026-09-26T00:00:00Z",
            "rite_jurisdiction_scope": ["ALL"],
            "matched_debts": [],
        }
    )
    assert out["eligible"] is False
    assert out["dmn_rule_fired"] == "R14"


def test_dmn_r14_takes_priority_over_r12():
    """Even with NO SBT, legal_person entityType → R14 fires first (not R12)."""
    out = run_eligibility_dmn(
        {
            "debtor_sbt_level": 0,
            "debtor_entity_type": "legal_person",
            "debtor_sbt_entity_type": "legal_person",
            "rite_type": "shmita_7yr",
            "matched_debts": [],
        }
    )
    assert out["dmn_rule_fired"] == "R14"


# ─── DMN R12: SBT gate (short-circuit) ───────────────────────────────


def test_dmn_r12_no_sbt_rejects_all_rite_types():
    for rite_type in ("shmita_7yr", "yobel_50yr", "tokusei_rei", "religious_jubilee", "political_amnesty"):
        out = run_eligibility_dmn(
            {
                "debtor_sbt_level": 0,
                "debtor_entity_type": "natural_person",
                "debtor_sbt_entity_type": "natural_person",
                "debtor_community_member": True,
                "rite_type": rite_type,
                "rite_effective_date": "2026-09-26T00:00:00Z",
                "rite_jurisdiction_scope": ["ALL"],
                "debtor_jurisdiction_iso3": "JPN",
                "matched_debts": [],
            }
        )
        assert out["eligible"] is False, f"R12 failed for {rite_type}"
        assert out["dmn_rule_fired"] == "R12"


# ─── DMN R13: Charter Rider §2(b) prohibited-instrument gate ──────────


@pytest.mark.parametrize("bad_instrument", ["liquidation", "margin_call", "seizure"])
def test_dmn_r13_prohibited_instrument_rejects(bad_instrument):
    out = run_eligibility_dmn(
        {
            "debtor_sbt_level": 5,
                "debtor_entity_type": "natural_person",
                "debtor_sbt_entity_type": "natural_person",  # SBT OK
            "debtor_community_member": True,
            "rite_type": "shmita_7yr",
            "rite_effective_date": "2026-09-26T00:00:00Z",
            "rite_jurisdiction_scope": ["ALL"],
            "debtor_jurisdiction_iso3": "JPN",
            "matched_debts": [
                {"instrument": "loan", "origination_date": "2020-01-01T00:00:00Z"},
                {"instrument": bad_instrument, "origination_date": "2020-01-01T00:00:00Z"},
            ],
        }
    )
    assert out["eligible"] is False
    assert out["dmn_rule_fired"] == "R13"
    assert any("§2(b)" in r for r in out["dmn_reasons"])


# ─── DMN R1-R3: shmita ────────────────────────────────────────────────


def test_dmn_r1_shmita_happy_path():
    out = run_eligibility_dmn(
        {
            "debtor_sbt_level": 1,
                "debtor_entity_type": "natural_person",
                "debtor_sbt_entity_type": "natural_person",
            "debtor_community_member": True,
            "rite_type": "shmita_7yr",
            "rite_effective_date": "2026-09-26T00:00:00Z",
            "rite_jurisdiction_scope": ["ALL"],
            "debtor_jurisdiction_iso3": "ISR",
            "matched_debts": [{"instrument": "loan", "origination_date": "2024-01-01T00:00:00Z"}],
        }
    )
    assert out["eligible"] is True
    assert out["dmn_rule_fired"] == "R1"


def test_dmn_r2_shmita_post_cycle_debt_rejects():
    out = run_eligibility_dmn(
        {
            "debtor_sbt_level": 1,
                "debtor_entity_type": "natural_person",
                "debtor_sbt_entity_type": "natural_person",
            "debtor_community_member": True,
            "rite_type": "shmita_7yr",
            "rite_effective_date": "2026-09-26T00:00:00Z",
            "rite_jurisdiction_scope": ["ALL"],
            "debtor_jurisdiction_iso3": "ISR",
            "matched_debts": [{"instrument": "loan", "origination_date": "2027-01-01T00:00:00Z"}],
        }
    )
    assert out["eligible"] is False
    assert out["dmn_rule_fired"] == "R2"


def test_dmn_r3_shmita_non_community_rejects():
    out = run_eligibility_dmn(
        {
            "debtor_sbt_level": 1,
                "debtor_entity_type": "natural_person",
                "debtor_sbt_entity_type": "natural_person",
            "debtor_community_member": False,  # Deut 15:3 foreigner exclusion
            "rite_type": "shmita_7yr",
            "rite_effective_date": "2026-09-26T00:00:00Z",
            "rite_jurisdiction_scope": ["ALL"],
            "debtor_jurisdiction_iso3": "USA",
            "matched_debts": [],
        }
    )
    assert out["eligible"] is False
    assert out["dmn_rule_fired"] == "R3"


# ─── DMN R4-R5: yobel ─────────────────────────────────────────────────


def test_dmn_r4_yobel_happy_path():
    out = run_eligibility_dmn(
        {
            "debtor_sbt_level": 1,
                "debtor_entity_type": "natural_person",
                "debtor_sbt_entity_type": "natural_person",
            "debtor_community_member": True,
            "rite_type": "yobel_50yr",
            "rite_effective_date": "2074-01-01T00:00:00Z",
            "rite_jurisdiction_scope": ["ALL"],
            "debtor_jurisdiction_iso3": "ISR",
            "matched_debts": [{"instrument": "loan", "origination_date": "2050-01-01T00:00:00Z"}],
        }
    )
    assert out["eligible"] is True
    assert out["dmn_rule_fired"] == "R4"


# ─── DMN R6-R7: tokusei ──────────────────────────────────────────────


def test_dmn_r6_tokusei_in_jurisdiction_accepts():
    out = run_eligibility_dmn(
        {
            "debtor_sbt_level": 1,
                "debtor_entity_type": "natural_person",
                "debtor_sbt_entity_type": "natural_person",
            "debtor_community_member": False,  # tokusei doesn't require community
            "rite_type": "tokusei_rei",
            "rite_effective_date": "2026-09-26T00:00:00Z",
            "rite_jurisdiction_scope": ["JPN"],
            "debtor_jurisdiction_iso3": "JPN",
            "matched_debts": [{"instrument": "loan", "origination_date": "2020-01-01T00:00:00Z"}],
        }
    )
    assert out["eligible"] is True
    assert out["dmn_rule_fired"] == "R6"


def test_dmn_r7_tokusei_out_of_jurisdiction_rejects():
    out = run_eligibility_dmn(
        {
            "debtor_sbt_level": 1,
                "debtor_entity_type": "natural_person",
                "debtor_sbt_entity_type": "natural_person",
            "debtor_community_member": False,
            "rite_type": "tokusei_rei",
            "rite_effective_date": "2026-09-26T00:00:00Z",
            "rite_jurisdiction_scope": ["JPN"],
            "debtor_jurisdiction_iso3": "USA",  # not in scope
            "matched_debts": [],
        }
    )
    assert out["eligible"] is False
    assert out["dmn_rule_fired"] == "R7"


# ─── DMN R8-R9: religious_jubilee ────────────────────────────────────


def test_dmn_r8_religious_jubilee_tithe_accepts():
    out = run_eligibility_dmn(
        {
            "debtor_sbt_level": 1,
                "debtor_entity_type": "natural_person",
                "debtor_sbt_entity_type": "natural_person",
            "debtor_community_member": True,
            "rite_type": "religious_jubilee",
            "rite_effective_date": "2026-09-26T00:00:00Z",
            "rite_jurisdiction_scope": ["ALL"],
            "debtor_jurisdiction_iso3": "ITA",
            "matched_debts": [{"instrument": "tithe_obligation", "origination_date": "2024-01-01T00:00:00Z"}],
        }
    )
    assert out["eligible"] is True
    assert out["dmn_rule_fired"] == "R8"


def test_dmn_r9_religious_jubilee_monetary_debt_rejects():
    out = run_eligibility_dmn(
        {
            "debtor_sbt_level": 1,
                "debtor_entity_type": "natural_person",
                "debtor_sbt_entity_type": "natural_person",
            "debtor_community_member": True,
            "rite_type": "religious_jubilee",
            "rite_effective_date": "2026-09-26T00:00:00Z",
            "rite_jurisdiction_scope": ["ALL"],
            "debtor_jurisdiction_iso3": "ITA",
            "matched_debts": [{"instrument": "loan", "origination_date": "2024-01-01T00:00:00Z"}],
        }
    )
    assert out["eligible"] is False
    assert out["dmn_rule_fired"] == "R9"


# ─── DMN R10-R11: political_amnesty ──────────────────────────────────


def test_dmn_r10_political_amnesty_accepts_individual_tax_amnesty():
    """political_amnesty scope (post-natural-person-only amendment): mass amnesty for
    individual debtors under sovereign decree (e.g. national tax delinquency pardon).
    Sovereign / corporate debt restructuring is OUT of scope for yobel."""
    out = run_eligibility_dmn(
        {
            "debtor_sbt_level": 1,
                "debtor_entity_type": "natural_person",
                "debtor_sbt_entity_type": "natural_person",
            "debtor_community_member": False,
            "rite_type": "political_amnesty",
            "rite_effective_date": "2026-09-26T00:00:00Z",
            "rite_jurisdiction_scope": ["AFG"],
            "debtor_jurisdiction_iso3": "AFG",
            "matched_debts": [
                {"instrument": "tax_obligation", "origination_date": "2010-01-01T00:00:00Z"},
                {"instrument": "loan", "origination_date": "2015-01-01T00:00:00Z"},
            ],
        }
    )
    assert out["eligible"] is True
    assert out["dmn_rule_fired"] == "R10"


def test_dmn_r11_political_amnesty_out_of_scope_rejects():
    out = run_eligibility_dmn(
        {
            "debtor_sbt_level": 1,
                "debtor_entity_type": "natural_person",
                "debtor_sbt_entity_type": "natural_person",
            "debtor_community_member": False,
            "rite_type": "political_amnesty",
            "rite_effective_date": "2026-09-26T00:00:00Z",
            "rite_jurisdiction_scope": ["AFG"],
            "debtor_jurisdiction_iso3": "USA",
            "matched_debts": [],
        }
    )
    assert out["eligible"] is False
    assert out["dmn_rule_fired"] == "R11"


# ─── End-to-end via build_graph ──────────────────────────────────────


def test_e2e_eligible_debtor_anchors_with_base_l2(
    checkpointer, rite_registry, creditor_enrollment_port, council_sbt, charter_compliance, envelope_crypto, anchor_bridge
):
    rite_registry.rites["shmita-5786"] = Rite(
        rite_id="shmita-5786", rite_type="shmita_7yr", status="active",
        effective_date="2026-09-26T00:00:00Z", expiry_date=None,
        scope="etzhayyim", scope_jurisdictions=["ALL"],
        issuer_did="did:web:etzhayyim.com", doctrinal_basis="Lev 25",
    )
    council_sbt.levels["did:web:etzhayyim.com:debtor1"] = 1
    council_sbt.entity_types["did:web:etzhayyim.com:debtor1"] = "natural_person"
    creditor_enrollment_port.debts_by_debtor[
        ("shmita-5786", "did:web:etzhayyim.com:debtor1")
    ] = [
        DebtRow(
            debt_id="d1", debtor_did="did:web:etzhayyim.com:debtor1",
            principal_micro_usdc=100_000_000, accrued_micro_usdc=0,
            origination_date="2024-01-01T00:00:00Z", instrument="loan",
        )
    ]
    graph = build_graph(
        checkpointer=checkpointer,
        rite_registry_port=rite_registry,
        creditor_enrollment_port=creditor_enrollment_port,
        council_sbt_port=council_sbt,
        charter_compliance_port=charter_compliance,
        envelope_crypto=envelope_crypto,
        anchor_bridge=anchor_bridge,
    )
    result = graph.invoke(
        {
            "rite_id": "shmita-5786",
            "debtor_did": "did:web:etzhayyim.com:debtor1",
            "debtor_entity_type": "natural_person",
            "eligibility_proof": "community-member-card-x123",
        },
        {"configurable": {"thread_id": "test-debtor-happy"}},
    )
    assert result["pairing_status"] == "paired"
    assert len(anchor_bridge.writes) == 1
    assert anchor_bridge.writes[0]["anchored"] is True


def test_e2e_ineligible_debtor_anchors_without_base_l2(
    checkpointer, rite_registry, creditor_enrollment_port, council_sbt, charter_compliance, envelope_crypto, anchor_bridge
):
    """R12 (no SBT) → eligible=false → AT MST write but skip Base L2 anchor (gas savings)."""
    rite_registry.rites["shmita-5786"] = Rite(
        rite_id="shmita-5786", rite_type="shmita_7yr", status="active",
        effective_date="2026-09-26T00:00:00Z", expiry_date=None,
        scope="etzhayyim", scope_jurisdictions=["ALL"],
        issuer_did="did:web:etzhayyim.com", doctrinal_basis="Lev 25",
    )
    # NO SBT
    graph = build_graph(
        checkpointer=checkpointer,
        rite_registry_port=rite_registry,
        creditor_enrollment_port=creditor_enrollment_port,
        council_sbt_port=council_sbt,
        charter_compliance_port=charter_compliance,
        envelope_crypto=envelope_crypto,
        anchor_bridge=anchor_bridge,
    )
    result = graph.invoke(
        {
            "rite_id": "shmita-5786",
            "debtor_did": "did:web:no-sbt.example",
            "eligibility_proof": "",
        },
        {"configurable": {"thread_id": "test-debtor-r12"}},
    )
    assert len(anchor_bridge.writes) == 1
    assert anchor_bridge.writes[0]["anchored"] is False  # Base L2 anchor SKIPPED for ineligible
