"""Tests for AuditWitnessCell — chain continuity, signing, tampering detection."""

from __future__ import annotations

import pytest

from yobel.cells.audit_witness.cell import (
    build_graph,
    collect_state_diff,
    verify_chain_continuity,
)
from yobel.ports import (
    AuditBatchStatus,
    ReplicaConsensus,
    SignedTriple,
)


# ─── collect_state_diff ──────────────────────────────────────────────


def test_collect_state_diff_passes_through_when_digest_present():
    out = collect_state_diff(
        {
            "state_root_before": "0xaaaa",
            "state_root_after": "0xbbbb",
            "tx_digest": "0xdeadbeef",
        }
    )
    # When tx_digest present, function is a no-op pass-through
    assert "tx_digest" in out
    assert out.get("tx_digest", "0xdeadbeef") == "0xdeadbeef" or out["tx_digest"] == "0xdeadbeef"


def test_collect_state_diff_fallback_digest_when_missing():
    out = collect_state_diff(
        {
            "state_root_before": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "state_root_after": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        }
    )
    assert "::" in out["tx_digest"]
    assert "0xaaaa" in out["tx_digest"]
    assert "0xbbbb" in out["tx_digest"]


# ─── verify_chain_continuity ─────────────────────────────────────────


def test_chain_continuity_genesis_no_prior_triple(audit_log):
    audit_log.tail = None  # No prior witness for this rite
    out = verify_chain_continuity({"rite_id": "shmita-5786"}, audit_log_port=audit_log)
    assert out["chain_valid"] is True
    assert out["tampering_severity"] == "none"


def test_chain_continuity_valid_link(audit_log):
    audit_log.tail = SignedTriple(cid="ipfs://prev-1")
    audit_log.chain_ok = True
    out = verify_chain_continuity(
        {"rite_id": "shmita-5786", "state_root_before": "0xaa"}, audit_log_port=audit_log
    )
    assert out["chain_valid"] is True
    assert out["tampering_severity"] == "none"


def test_chain_break_single_node_is_suspicion(audit_log):
    """Chain break + replicas disagree → 'suspicion' (not 'confirmed')."""
    audit_log.tail = SignedTriple(cid="ipfs://prev-1")
    audit_log.chain_ok = False
    audit_log.consensus = False  # replicas DON'T agree
    out = verify_chain_continuity(
        {"rite_id": "shmita-5786", "state_root_before": "0xaa"}, audit_log_port=audit_log
    )
    assert out["chain_valid"] is False
    assert out["tampering_severity"] == "suspicion"


def test_chain_break_replica_consensus_is_confirmed(audit_log):
    """Chain break + replicas agree → 'confirmed' tampering."""
    audit_log.tail = SignedTriple(cid="ipfs://prev-1")
    audit_log.chain_ok = False
    audit_log.consensus = True  # replicas AGREE on chain break
    out = verify_chain_continuity(
        {"rite_id": "shmita-5786", "state_root_before": "0xaa"}, audit_log_port=audit_log
    )
    assert out["chain_valid"] is False
    assert out["tampering_severity"] == "confirmed"


# ─── End-to-end via build_graph: happy path ──────────────────────────


def test_e2e_super_step_signed_and_logged(
    checkpointer, audit_log, witness_keystore, anchor_bridge, public_fund, council_notifier
):
    audit_log.tail = None  # Genesis for this rite
    graph = build_graph(
        checkpointer=checkpointer,
        audit_log_port=audit_log,
        witness_keystore=witness_keystore,
        anchor_bridge=anchor_bridge,
        public_fund_port=public_fund,
        council_notifier=council_notifier,
    )
    result = graph.invoke(
        {
            "source_kind": "super_step",
            "rite_id": "shmita-5786",
            "state_root_before": "0xaa",
            "state_root_after": "0xbb",
            "tx_digest": "0xcc",
            "event_payload": {"step": "declareRite"},
        },
        {"configurable": {"thread_id": "test-audit-happy"}},
    )
    assert result["audit_event_uri"].startswith("at://")
    assert len(audit_log.appended) == 1
    # No anchor yet (batch threshold not reached)
    assert result.get("batch_anchored", False) is False
    # No tampering incident
    assert "incident_uri" not in result or not result.get("incident_uri")


def test_e2e_tampering_triggers_council_notification(
    checkpointer, audit_log, witness_keystore, anchor_bridge, public_fund, council_notifier
):
    """Chain break + replica consensus → mark superseded + Public Fund + Council."""
    audit_log.tail = SignedTriple(cid="ipfs://corrupt-prev")
    audit_log.chain_ok = False
    audit_log.consensus = True  # CONFIRMED tampering
    graph = build_graph(
        checkpointer=checkpointer,
        audit_log_port=audit_log,
        witness_keystore=witness_keystore,
        anchor_bridge=anchor_bridge,
        public_fund_port=public_fund,
        council_notifier=council_notifier,
    )
    result = graph.invoke(
        {
            "source_kind": "super_step",
            "rite_id": "shmita-5786",
            "state_root_before": "0xnew",
            "state_root_after": "0xnewer",
            "tx_digest": "0xtx",
            "event_payload": {},
        },
        {"configurable": {"thread_id": "test-audit-tamper"}},
    )
    # Tampering path: no audit append, no anchor — instead Public Fund + Council
    assert len(audit_log.appended) == 0
    assert len(public_fund.grants) == 1
    assert public_fund.grants[0]["reason"] == "yobel.tampering_detected"
    assert len(council_notifier.notifications) == 1
    assert "council_lv9_chair" in council_notifier.notifications[0]["targets"]
    assert "five_bootstrap_council" in council_notifier.notifications[0]["targets"]
    assert result["incident_uri"].startswith("at://")


def test_e2e_anchor_batch_fires_at_threshold(
    checkpointer, audit_log, witness_keystore, anchor_bridge, public_fund, council_notifier
):
    """Once batch has ≥100 events, anchor_batch fires + Base L2 tx returned."""
    audit_log.batch = AuditBatchStatus(
        event_count=100,
        seconds_since_last_anchor=300,
        pending_cids=[f"ipfs://e{i}" for i in range(100)],
    )
    graph = build_graph(
        checkpointer=checkpointer,
        audit_log_port=audit_log,
        witness_keystore=witness_keystore,
        anchor_bridge=anchor_bridge,
        public_fund_port=public_fund,
        council_notifier=council_notifier,
    )
    result = graph.invoke(
        {
            "source_kind": "super_step",
            "rite_id": "shmita-5786",
            "state_root_before": "0xaa",
            "state_root_after": "0xbb",
            "tx_digest": "0xcc",
        },
        {"configurable": {"thread_id": "test-audit-anchor"}},
    )
    assert result["batch_anchored"] is True
    assert result["base_l2_anchor_tx_hash"].startswith("0xfake-batch-")
    # mark_anchored should have been called
    assert len(audit_log.anchored_marks) == 1
    assert audit_log.anchored_marks[0][1].startswith("0xfake-batch-")
