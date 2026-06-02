"""Tests for RiteDeclarationCell — input validation, Charter Rider §2 gate, Council DMN + ratification."""

from __future__ import annotations

import pytest

from yobel.cells.rite_declaration.cell import (
    build_graph,
    charter_rider_gate,
    council_ratification_dmn,
    validate_input,
)


# ─── validate_input ──────────────────────────────────────────────────


def test_validate_input_happy():
    out = validate_input(
        {
            "rite_type": "shmita_7yr",
            "doctrinal_basis": "Lev 25:1-7",
            "scope": "etzhayyim community",
            "effective_date": "2026-09-26T00:00:00Z",
        }
    )
    assert out == {"input_valid": True, "input_errors": []}


@pytest.mark.parametrize(
    "patch,expected_error_substring",
    [
        ({"rite_type": "bogus"}, "invalid riteType"),
        ({"doctrinal_basis": ""}, "doctrinalBasis required"),
        ({"scope": ""}, "scope required"),
        ({"effective_date": ""}, "effectiveDate required"),
    ],
)
def test_validate_input_rejects_missing_or_bogus(patch, expected_error_substring):
    base = {
        "rite_type": "shmita_7yr",
        "doctrinal_basis": "Lev 25:1-7",
        "scope": "etzhayyim community",
        "effective_date": "2026-09-26T00:00:00Z",
    }
    base.update(patch)
    out = validate_input(base)
    assert out["input_valid"] is False
    assert any(expected_error_substring in e for e in out["input_errors"])


# ─── charter_rider_gate ──────────────────────────────────────────────


def test_charter_rider_gate_accepts_normal_scope():
    out = charter_rider_gate({"scope": "etzhayyim community small loans"}, charter_compliance_port=None)
    assert out["charter_rider_compliant"] is True
    assert out["charter_rider_violations"] == []


def test_charter_rider_gate_rejects_military_without_disclosure():
    out = charter_rider_gate(
        {"scope": "military debt forgiveness for veterans"},
        charter_compliance_port=None,
    )
    assert out["charter_rider_compliant"] is False
    assert any("§2(a) military" in v for v in out["charter_rider_violations"])


def test_charter_rider_gate_accepts_military_with_disclosure():
    out = charter_rider_gate(
        {"scope": "military debt forgiveness with transparent-force-rd disclosure"},
        charter_compliance_port=None,
    )
    assert out["charter_rider_compliant"] is True


def test_charter_rider_gate_rejects_speculative_keywords():
    out = charter_rider_gate({"scope": "margin trading loss release"}, charter_compliance_port=None)
    assert out["charter_rider_compliant"] is False
    assert any("§2(b)" in v for v in out["charter_rider_violations"])


# ─── council_ratification_dmn ────────────────────────────────────────


def test_council_dmn_baseline():
    out = council_ratification_dmn({"rite_type": "shmita_7yr"})
    assert out["required_lv6_plus_count"] == 3
    assert out["required_lv9_chair_count"] == 1
    assert out["required_quorum_pct"] == 50


def test_council_dmn_yobel_50yr_adds_land_gate():
    out = council_ratification_dmn({"rite_type": "yobel_50yr"})
    assert out["required_lv6_plus_count"] == 5
    assert out["required_quorum_pct"] == 60
    assert "land-sovereignty-coordination" in out["additional_gates"]


def test_council_dmn_political_amnesty_aggregates_all_gates():
    out = council_ratification_dmn({"rite_type": "political_amnesty"})
    assert out["required_lv6_plus_count"] == 6  # B1 3 + R5 +3
    assert out["required_lv9_chair_count"] == 2  # B1 1 + R5 +1
    assert out["required_quorum_pct"] == 70  # B1 50 + R5 +20
    assert "transparent-force-rd-disclosure" in out["additional_gates"]
    assert "council-five-bootstrap-consultation" in out["additional_gates"]


def test_council_dmn_tokusei_adds_jurisdiction_gate():
    out = council_ratification_dmn({"rite_type": "tokusei_rei"})
    assert out["required_lv6_plus_count"] == 4
    assert out["required_lv9_chair_count"] == 2
    assert "jurisdiction-claim-coordination" in out["additional_gates"]


def test_council_dmn_quorum_cap_100pct(monkeypatch):
    """Multiple rules cannot push quorum > 100%."""
    out = council_ratification_dmn({"rite_type": "political_amnesty"})
    assert 0 <= out["required_quorum_pct"] <= 100


# ─── End-to-end via build_graph ──────────────────────────────────────


def test_e2e_happy_path_shmita(checkpointer, council_sbt, charter_compliance, council_ratification, anchor_bridge, land_registry):
    council_sbt.levels["did:web:etzhayyim.com:steward-001"] = 6  # SBT Lv6
    council_ratification.next_decision = type(council_ratification.next_decision)(
        ratified=True, signatures=["did:web:council/lv9-chair", "did:web:council/lv6-a", "did:web:council/lv6-b", "did:web:council/lv6-c"]
    )
    graph = build_graph(
        checkpointer=checkpointer,
        charter_compliance_port=charter_compliance,
        council_sbt_port=council_sbt,
        council_ratification_port=council_ratification,
        land_registry_port=land_registry,
        anchor_bridge=anchor_bridge,
    )
    initial = {
        "rite_id": "shmita-5786",
        "rite_type": "shmita_7yr",
        "scope": "etzhayyim community small monetary debts",
        "effective_date": "2026-09-26T00:00:00Z",
        "doctrinal_basis": "Lev 25:1-7 / Deut 15:1-2",
        "issuer_did": "did:web:etzhayyim.com:steward-001",
    }
    result = graph.invoke(initial, {"configurable": {"thread_id": "test-shmita"}})
    assert result["rite_status"] == "active"
    assert result["council_ratified"] is True
    assert len(anchor_bridge.writes) == 1
    assert anchor_bridge.writes[0]["collection"] == "com.etzhayyim.apps.etzhayyim.yobel.rite"


def test_e2e_council_rejection_cancels_rite(
    checkpointer, council_sbt, charter_compliance, council_ratification, anchor_bridge, land_registry
):
    council_sbt.levels["did:web:etzhayyim.com:steward-001"] = 6
    council_ratification.next_decision = type(council_ratification.next_decision)(
        ratified=False, signatures=[]
    )
    graph = build_graph(
        checkpointer=checkpointer,
        charter_compliance_port=charter_compliance,
        council_sbt_port=council_sbt,
        council_ratification_port=council_ratification,
        land_registry_port=land_registry,
        anchor_bridge=anchor_bridge,
    )
    result = graph.invoke(
        {
            "rite_id": "shmita-5786",
            "rite_type": "shmita_7yr",
            "scope": "etzhayyim community",
            "effective_date": "2026-09-26T00:00:00Z",
            "doctrinal_basis": "Lev 25",
            "issuer_did": "did:web:etzhayyim.com:steward-001",
        },
        {"configurable": {"thread_id": "test-reject"}},
    )
    assert result["rite_status"] == "cancelled"
    # No anchor write should have happened
    assert len(anchor_bridge.writes) == 0
