"""Tests for karakuri T3 export (G9), the live-adapter membrane (G6/G3), and the Datom audit (G7)."""

import pytest

from command import plan
from export import (
    EXPORT_FORMATS,
    OwnerViolation,
    build_export_plan,
    verify_roundtrip,
)
from adapter_live import LiveAdapterRefused, authorize_live
from datom import (
    LiveIngestRefused,
    export_to_entity,
    ingest_live,
    op_id,
    op_to_entity,
    plan_to_entities,
    to_ingest_batch,
)
from nl_plan import plan_from_brief

PLANNED_AT = "2026-06-06T00:00:00Z"


# ── T3 export (G9) ───────────────────────────────────────────────────────────────────

def test_export_plan_is_member_owned_and_encrypted():
    a = build_export_plan("google", "kotoba-edn")
    assert a.owner == "member"          # G9
    assert a.encrypted is True          # G9
    assert a.secret_ref.startswith("encref:")
    assert a.dry_run is True            # G6


def test_export_refuses_non_member_owner():
    with pytest.raises(OwnerViolation):
        build_export_plan("google", "json", owner="someone-else")


def test_export_refuses_unknown_format():
    with pytest.raises(ValueError):
        build_export_plan("google", "pdf")


def test_export_refuses_plaintext_secret_ref():
    with pytest.raises(ValueError):
        build_export_plan("google", "json", secret_ref="plaintext-token")


def test_roundtrip_ok_for_valid_export():
    a = verify_roundtrip(build_export_plan("notion", "json"))
    assert a.roundtrip_ok is True


def test_all_formats_roundtrip():
    for fmt in EXPORT_FORMATS:
        assert verify_roundtrip(build_export_plan("github", fmt)).roundtrip_ok is True


# ── live-adapter membrane (G6 / G3) ──────────────────────────────────────────────────

def _t2_op():
    return plan("karakuri legacy-portal records.list")   # T2 browser-use, ToS ok

_FULL = dict(operator_attestation="did:web:op.example", member_sig="member-sig",
             council_level=6, env={"KARAKURI_ALLOW_LIVE_ADAPTER": "1"})


def test_live_refused_by_default():
    with pytest.raises(LiveAdapterRefused):
        authorize_live(_t2_op(), env={})


def test_live_refused_without_operator_attestation():
    args = {**_FULL, "operator_attestation": None}
    with pytest.raises(LiveAdapterRefused):
        authorize_live(_t2_op(), **args)


def test_live_refused_below_council_level():
    args = {**_FULL, "council_level": 5}
    with pytest.raises(LiveAdapterRefused):
        authorize_live(_t2_op(), **args)


def test_live_refused_without_member_signature():
    args = {**_FULL, "member_sig": ""}
    with pytest.raises(LiveAdapterRefused):
        authorize_live(_t2_op(), **args)            # G3 no-server-key


def test_live_authorized_with_all_gates_but_does_not_execute():
    auth = authorize_live(_t2_op(), **_FULL)
    assert auth["authorized"] is True
    assert auth["serverSigned"] is False            # G3
    assert auth["executed"] is False                # membrane authorizes, never executes
    assert auth["engine"] == "browser-use"


# ── kotoba Datom audit (G7) ──────────────────────────────────────────────────────────

def test_op_entity_mirrors_schema_keys():
    op = plan("karakuri google messages.list")
    ent = op_to_entity(op, PLANNED_AT)
    assert ent[":op/adapter-tier"] == ":t1-official-api"
    assert ent[":op/safety"] == ":read"
    assert ent[":op/dry-run"] is True               # G6
    assert ent[":op/planned-at"] == PLANNED_AT       # G7 as-of


def test_op_id_is_deterministic():
    op = plan("karakuri google messages.list")
    assert op_id(op, PLANNED_AT) == op_id(op, PLANNED_AT)


def test_t2_op_entity_records_browser_use_engine():
    op = plan("karakuri legacy-portal records.list")
    ent = op_to_entity(op, PLANNED_AT)
    assert ent[":op/t2-engine"] == ":browser-use"


def test_args_serializes_keys_only_no_values():
    op = plan("karakuri legacy-portal records.update --token SECRET --name x")
    ent = op_to_entity(op, PLANNED_AT)
    assert ent[":op/args"] == "name,token"          # G3 — keys only
    assert "SECRET" not in ent[":op/args"]


def test_plan_to_entities_links_plan_to_ops():
    cp = plan_from_brief("show my gmail messages")
    ents = plan_to_entities(cp, PLANNED_AT)
    plan_ent = ents[0]
    op_ents = ents[1:]
    assert plan_ent[":plan/charter-clean"] is True   # N6
    assert plan_ent[":plan/op"] == [e[":op/id"] for e in op_ents]


def test_export_entity_is_member_and_encrypted():
    ent = export_to_entity(build_export_plan("google", "json"))
    assert ent[":export/owner"] == ":member"        # G9
    assert ent[":export/encrypted"] is True


def test_ingest_batch_shape():
    op = plan("karakuri google messages.list")
    batch = to_ingest_batch([op_to_entity(op, PLANNED_AT)])
    assert batch["op"] == "kg.ingest_batch"
    assert batch["graph"] == "karakuri-audit-v1"
    assert len(batch["entities"]) == 1


def test_live_ingest_refused_by_default():
    batch = to_ingest_batch([])
    with pytest.raises(LiveIngestRefused):
        ingest_live(batch, env={})
