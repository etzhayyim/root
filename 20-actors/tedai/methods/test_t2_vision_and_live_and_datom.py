"""Tests for t2_vision.py (G8/G2 unrepresentability), actuate_live.py (G6 refusal chain), and
datom.py (G7/G9 audit projection) — ADR-2606101400."""

from __future__ import annotations

import pytest

from desktop import TIER_T2, DesktopOp, plan
from t2_vision import (
    EVASION_ACTIONS,
    SURVEILLANCE_ACTIONS,
    VISION_ACTIONS,
    EvasionRefused,
    SurveillanceRefused,
    T2NotEligible,
    _make_step,
    assert_no_forbidden,
    build_vision_plan,
)
from actuate_live import LIVE_ACTUATION_FLAG, ActuationRefused, authorize_actuation
from datom import (
    LIVE_INGEST_FLAG,
    LiveIngestRefused,
    RawEvidenceRefused,
    evidence_hash,
    ingest_batch,
    ingest_live,
    op_entity,
    op_id,
)

PLANNED_AT = "2026-06-10T14:00:00Z"


# ── t2_vision: structural unrepresentability (G8 surveillance / G2 evasion) ────────────

@pytest.mark.parametrize("verb", sorted(SURVEILLANCE_ACTIONS))
def test_surveillance_verbs_unrepresentable(verb):
    with pytest.raises(SurveillanceRefused):
        _make_step(verb)


@pytest.mark.parametrize("verb", sorted(EVASION_ACTIONS))
def test_evasion_verbs_unrepresentable(verb):
    with pytest.raises(EvasionRefused):
        _make_step(verb)


def test_vocabularies_are_disjoint():
    assert not VISION_ACTIONS & SURVEILLANCE_ACTIONS
    assert not VISION_ACTIONS & EVASION_ACTIONS


def test_unknown_action_raises():
    with pytest.raises(ValueError):
        _make_step("teleport")


def test_assert_no_forbidden_catches_injected_step():
    with pytest.raises(SurveillanceRefused):
        assert_no_forbidden([{"action": "keylog"}])
    with pytest.raises(EvasionRefused):
        assert_no_forbidden([{"action": "bypass_anticheat"}])


# ── t2_vision: plan building (G1/G3/G4/G5/G6/G9) ───────────────────────────────────────

def test_read_plan_shape():
    op = plan("tedai legacy-win-app records.list")
    p = build_vision_plan(op)
    actions = [s["action"] for s in p["steps"]]
    assert actions[0] == "attach_pairing"           # G1/G3: member's own pairing grant first
    assert p["steps"][0]["server_held_key"] is False
    assert "observe_screen" in actions and "read_text" in actions
    assert actions[-1] == "evidence_hash"           # G9: hash, never the frame
    assert p["dry_run"] is True                     # G6
    assert p["surveillance"] is False and p["detection_evasion"] is False
    assert p["frame_leaves_device"] is False        # G4


def test_observe_is_op_scoped_and_unretained():
    op = plan("tedai legacy-win-app records.list")
    p = build_vision_plan(op)
    obs = next(s for s in p["steps"] if s["action"] == "observe_screen")
    assert obs["scope"] == "op" and obs["retain_raw"] is False   # G8


def test_mutating_plan_stops_at_member_signature():
    op = plan("tedai legacy-win-app form.fill --name x")
    p = build_vision_plan(op)
    gated = [s for s in p["steps"] if s["action"] in ("click", "type_text")]
    assert gated and all(s["requires"] == "member-signature" for s in gated)   # G5
    # G3: only flag KEYS surface in the plan, never values
    typed = next(s for s in p["steps"] if s["action"] == "type_text")
    assert typed["from_args"] == ["name"]


def test_t1_op_has_no_vision_plan():
    with pytest.raises(T2NotEligible):
        build_vision_plan(plan("tedai finder files.list"))


def test_prohibited_app_has_no_vision_plan():
    op = plan("tedai anticheat-game inventory.list", prefer_tier=TIER_T2)
    with pytest.raises(T2NotEligible):
        build_vision_plan(op)


def test_live_flag_refused():
    op = plan("tedai legacy-win-app records.list")
    with pytest.raises(T2NotEligible):
        build_vision_plan(op, live=True)            # G6


# ── actuate_live: the refusal chain (G6/G3/G5) ─────────────────────────────────────────

def _full_auth(**overrides):
    kw = dict(
        operator_token="op-tok",
        council_attestation="council:lv6:att-1",
        member_sig="sig:member",
        env={LIVE_ACTUATION_FLAG: "1"},
    )
    kw.update(overrides)
    return kw


def test_default_deny_lists_all_missing_authorities():
    op = plan("tedai finder files.list")
    with pytest.raises(ActuationRefused) as e:
        authorize_actuation(op, env={})
    msg = str(e.value)
    for needle in (LIVE_ACTUATION_FLAG, "operator_token", "council_attestation", "member_sig"):
        assert needle in msg


@pytest.mark.parametrize("drop", ["operator_token", "council_attestation", "member_sig"])
def test_any_single_missing_authority_refuses(drop):
    op = plan("tedai finder files.list")
    with pytest.raises(ActuationRefused):
        authorize_actuation(op, **_full_auth(**{drop: None}))


def test_env_flag_alone_is_insufficient():
    op = plan("tedai finder files.list")
    with pytest.raises(ActuationRefused):
        authorize_actuation(op, env={LIVE_ACTUATION_FLAG: "1"})


def test_outward_op_unsatisfiable_at_r0():
    op = plan("tedai mail message.send --to friend")
    with pytest.raises(ActuationRefused, match="outward"):
        authorize_actuation(op, **_full_auth())     # G5: no parameter satisfies the outward gate


def test_gate_drift_refused():
    op = plan("tedai finder files.rename --from a --to b")
    drifted = DesktopOp(**{**op.__dict__, "mutate_gate": "read-allowed"})
    with pytest.raises(ActuationRefused, match="G5"):
        authorize_actuation(drifted, **_full_auth())


def test_all_authorities_present_still_not_implemented_at_r0():
    op = plan("tedai finder files.list")
    with pytest.raises(NotImplementedError):
        authorize_actuation(op, **_full_auth())     # G6: driver layer is R1+


# ── datom: audit projection (G7/G9/G3/G6) ──────────────────────────────────────────────

def test_op_id_deterministic():
    op = plan("tedai finder files.list")
    assert op_id(op, PLANNED_AT) == op_id(op, PLANNED_AT)
    assert op_id(op, PLANNED_AT) != op_id(op, "2026-06-10T15:00:00Z")
    assert op_id(op, PLANNED_AT).startswith("op:finder:files.list:")


def test_entity_serializes_only_flag_keys():
    op = plan("tedai mail message.send --to secret@example.com --subject hello")
    ent = op_entity(op, PLANNED_AT)
    assert ent[":op/args"] == "subject,to"          # G3: keys only, sorted
    assert "secret@example.com" not in str(ent)


def test_entity_keywords_and_dry_run():
    op = plan("tedai legacy-win-app records.list")
    ent = op_entity(op, PLANNED_AT)
    assert ent[":op/safety"] == ":read"
    assert ent[":op/adapter-tier"] == ":t2-vision-pointer"
    assert ent[":op/stance-gate"] == ":ok"
    assert ent[":op/dry-run"] is True               # G6
    assert ent[":op/t2-engine"] == ":on-device-vision"


def test_outward_and_route_projection():
    out = op_entity(plan("tedai mail message.send --to x"), PLANNED_AT)
    assert out[":op/safety"] == ":outward"
    assert out[":op/mutate-gate"] == ":awaiting-member-sig-and-outward-gate"
    routed = op_entity(plan("tedai chrome tabs.list"), PLANNED_AT)
    assert routed[":op/route"] == ":karakuri"       # N7


def test_gate_value_drift_raises_not_fail_open():
    op = plan("tedai finder files.list")
    drifted = DesktopOp(**{**op.__dict__, "stance_gate": "totally-new-value"})
    with pytest.raises(ValueError, match="stance-gate"):
        op_entity(drifted, PLANNED_AT)              # G7: never misreport


def test_raw_frame_refused_hash_accepted():
    op = plan("tedai legacy-win-app records.list")
    with pytest.raises(RawEvidenceRefused):
        op_entity(op, PLANNED_AT, raw_frame=b"\x89PNG...")   # G9
    h = evidence_hash(b"\x89PNG...")
    ent = op_entity(op, PLANNED_AT, evidence_sha256=h)
    assert ent[":op/evidence-sha256"] == h and len(h) == 64


def test_live_ingest_operator_gated():
    ents = [op_entity(plan("tedai finder files.list"), PLANNED_AT)]
    assert ingest_batch(ents)["graph"] == "tedai-audit-v1"
    with pytest.raises(LiveIngestRefused):
        ingest_live(ents, env={})                   # G6: default-deny
    assert ingest_live(ents, env={LIVE_INGEST_FLAG: "1"})["entities"] == ents
