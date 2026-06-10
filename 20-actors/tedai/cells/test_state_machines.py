"""State-machine tests for tedai cells (R0). .solve() is NOT called for flow (it raises) —
ADR-2606101400."""

import pytest

from app_resolve.cell import AppResolveCell
from app_resolve.state_machine import (
    OUTCOME_ROUTE_KARAKURI,
    OUTCOME_UNKNOWN_APP,
    ResolvePhase,
    transition_lookup,
    transition_stance,
    transition_tier_select,
)
from pairing_broker.cell import PairingBrokerCell
from pairing_broker.state_machine import (
    BrokerPhase,
    transition_authorize_mutate,
    transition_build_grant,
    transition_read_allowed,
    transition_verify_owner,
)
from intent_plan.cell import IntentPlanCell
from intent_plan.state_machine import (
    OUTCOME_PROHIBITED,
    PlanPhase,
    transition_emit_plan,
    transition_parse_brief,
    transition_prohibition_scan,
)
from actuate_invoke.cell import ActuateInvokeCell
from actuate_invoke.state_machine import (
    OUTCOME_NOT_INVOKABLE,
    OUTCOME_STANCE_REFUSED,
    InvokePhase,
    transition_build_adapter_plan,
    transition_mutate_gate,
    transition_plan_op,
    transition_stance_gate,
)
from evidence_audit.cell import EvidenceAuditCell
from evidence_audit.state_machine import (
    AuditPhase,
    transition_assemble_batch,
    transition_hash_evidence,
    transition_project_datoms,
)

PLANNED_AT = "2026-06-10T14:00:00Z"


# ── app_resolve ────────────────────────────────────────────────────────────────────────

def _resolve(app):
    s = transition_lookup({"cell_state": {}, "app": app})
    if s["next_node"] == "end":
        return s
    s = transition_tier_select(s)
    return transition_stance(s)


def test_resolve_t1_app():
    s = _resolve("finder")
    cs = s["cell_state"]
    assert cs["phase"] == ResolvePhase.RESOLVED.value
    assert cs["payload"]["tier"] == "t1-scripting-api"
    assert cs["payload"]["t1Surface"] == "applescript+ax"


def test_resolve_t2_app_carries_on_device_engine():
    s = _resolve("legacy-win-app")
    cs = s["cell_state"]
    assert cs["payload"]["tier"] == "t2-vision-pointer"
    assert cs["payload"]["t2Engine"] == "on-device-vision"     # G4


def test_resolve_prohibited_app_falls_to_t3_without_engine():
    s = _resolve("anticheat-game")
    cs = s["cell_state"]
    assert cs["payload"]["tier"] == "t3-file-level"
    assert "t2Engine" not in cs["payload"]                     # G2


def test_resolve_unknown_app_degrades():
    s = _resolve("mystery-app")
    cs = s["cell_state"]
    assert cs["phase"] == ResolvePhase.REFUSED.value
    assert cs["payload"]["outcome"] == OUTCOME_UNKNOWN_APP     # G8


def test_resolve_browser_routes_to_karakuri():
    s = _resolve("chrome")
    cs = s["cell_state"]
    assert cs["phase"] == ResolvePhase.ROUTED.value
    assert cs["payload"]["outcome"] == OUTCOME_ROUTE_KARAKURI  # N7


# ── pairing_broker ─────────────────────────────────────────────────────────────────────

def _broker_read(**overrides):
    base = {"cell_state": {"op_safety": "read"}}
    base.update(overrides)
    s = transition_verify_owner(base)
    s = transition_build_grant(s)
    return transition_read_allowed(s)


def _broker_mutate(member_sig="member-ed25519-sig", server_sig="", safety="update"):
    s = transition_verify_owner({"cell_state": {"op_safety": safety}})
    s = transition_build_grant(s)
    return transition_authorize_mutate({**s, "member_sig": member_sig, "server_sig": server_sig})


def test_read_op_allowed_without_signature():
    cs = _broker_read()["cell_state"]
    assert cs["phase"] == BrokerPhase.READ_ALLOWED.value
    assert cs["server_held_key"] is False                      # G3
    assert cs["payload"]["mutateGate"] == "read-allowed"       # G5
    assert cs["payload"]["grant"]["paired"] is True            # G1


def test_third_party_device_refused():
    with pytest.raises(ValueError, match="G1"):
        transition_verify_owner({"cell_state": {}, "device_owner": "someone-else"})


def test_unpaired_device_refused():
    with pytest.raises(ValueError, match="paired"):
        transition_verify_owner({"cell_state": {}, "paired": False})


def test_non_member_principal_refused():
    with pytest.raises(ValueError, match="G1"):
        transition_verify_owner({"cell_state": {}, "principal": "platform"})


def test_plaintext_pairing_key_refused():
    s = transition_verify_owner({"cell_state": {"op_safety": "read"}})
    with pytest.raises(ValueError, match="G3"):
        transition_build_grant({**s, "pairing_ref": "plaintext:abc123"})


def test_mutate_authorized_on_member_sig_only():
    cs = _broker_mutate()["cell_state"]
    assert cs["phase"] == BrokerPhase.AUTHORIZED.value
    assert cs["payload"]["authorization"]["serverSigned"] is False
    assert cs["payload"]["authorization"]["actuationGated"] is True    # G6 still ahead


def test_server_signature_refused():
    with pytest.raises(ValueError, match="G3"):
        _broker_mutate(server_sig="server-sig")


def test_mutate_without_member_sig_refused():
    with pytest.raises(ValueError, match="member signature"):
        _broker_mutate(member_sig="")


def test_outward_op_held_at_outward_gate_even_with_member_sig():
    cs = _broker_mutate(safety="outward")["cell_state"]
    assert cs["phase"] == BrokerPhase.AWAITING_OUTWARD_GATE.value      # G5: sig necessary, not sufficient
    assert cs["payload"]["outwardGate"]["authorized"] is False
    assert cs["payload"]["outwardGate"]["requires"] == "council-outward-gate"


# ── intent_plan ────────────────────────────────────────────────────────────────────────

def _plan_brief(brief, lines):
    s = transition_parse_brief({"cell_state": {}, "brief": brief, "command_lines": lines})
    s = transition_prohibition_scan(s)
    if s["cell_state"]["phase"] == PlanPhase.REFUSED.value:
        return s
    return transition_emit_plan(s)


def test_clean_brief_plans_gated_dry_run_ops():
    s = _plan_brief("file my receipts", ["tedai finder files.move --to receipts",
                                         "tedai finder files.list"])
    cs = s["cell_state"]
    assert cs["phase"] == PlanPhase.PLANNED.value
    assert cs["payload"]["dryRun"] is True                     # G6
    assert cs["payload"]["mutatingCount"] == 1
    assert len(cs["payload"]["ops"]) == 2


@pytest.mark.parametrize("bad_brief", [
    "keylog my roommate",
    "monitor my employee all day",
    "bypass anti-cheat in this game",
    "record their screen without them knowing",
])
def test_prohibited_intent_refused_before_planning(bad_brief):
    s = _plan_brief(bad_brief, ["tedai finder files.list"])
    cs = s["cell_state"]
    assert cs["phase"] == PlanPhase.REFUSED.value
    assert cs["payload"]["outcome"] == OUTCOME_PROHIBITED      # G8/G2
    assert "ops" not in cs["payload"]


def test_empty_command_lines_raise():
    with pytest.raises(ValueError):
        transition_parse_brief({"cell_state": {}, "brief": "x", "command_lines": []})


# ── actuate_invoke ─────────────────────────────────────────────────────────────────────

def _invoke(line):
    s = transition_plan_op({"cell_state": {}, "line": line})
    if s["next_node"] == "end":
        return s
    s = transition_stance_gate(s)
    if s["next_node"] == "end":
        return s
    s = transition_mutate_gate(s)
    return transition_build_adapter_plan(s)


def test_invoke_t2_read_emits_vision_plan():
    cs = _invoke("tedai legacy-win-app records.list")["cell_state"]
    assert cs["phase"] == InvokePhase.EMITTED.value
    assert cs["payload"]["dryRun"] is True                     # G6
    ap = cs["payload"]["adapterPlan"]
    assert ap["engine"] == "on-device-vision" and ap["frame_leaves_device"] is False


def test_invoke_t1_emits_stub_plan():
    cs = _invoke("tedai finder files.list")["cell_state"]
    assert cs["phase"] == InvokePhase.EMITTED.value
    assert cs["payload"]["adapterPlan"]["tier"] == "t1-scripting-api"
    assert cs["payload"]["adapterPlan"]["dry_run"] is True


def test_invoke_mutating_op_carries_gate():
    cs = _invoke("tedai legacy-win-app form.fill --name x")["cell_state"]
    assert cs["payload"]["mutateGate"] == "awaiting-member-sig"        # G5


def test_invoke_unknown_app_not_invokable():
    cs = _invoke("tedai mystery-app thing.list")["cell_state"]
    assert cs["phase"] == InvokePhase.REFUSED.value
    assert cs["payload"]["outcome"] == OUTCOME_NOT_INVOKABLE   # G8


def test_invoke_browser_not_invokable():
    cs = _invoke("tedai chrome tabs.list")["cell_state"]
    assert cs["payload"]["outcome"] == OUTCOME_NOT_INVOKABLE   # N7


def test_invoke_forced_t2_on_prohibited_app_refused():
    import desktop
    op = desktop.plan("tedai anticheat-game inventory.list", prefer_tier=desktop.TIER_T2)
    s = transition_plan_op({"cell_state": {}, "line": "tedai anticheat-game inventory.list"})
    s["cell_state"]["op"] = op.__dict__
    s = transition_stance_gate(s)
    assert s["cell_state"]["phase"] == InvokePhase.REFUSED.value
    assert s["cell_state"]["payload"]["outcome"] == OUTCOME_STANCE_REFUSED   # G2


# ── evidence_audit ─────────────────────────────────────────────────────────────────────

def _audit(ops, frame=None):
    s = transition_hash_evidence(
        {"cell_state": {}, "ops": ops, "planned_at": PLANNED_AT, "frame_bytes": frame}
    )
    s = transition_project_datoms(s)
    return transition_assemble_batch(s)


def _op_dict(line):
    import desktop
    return desktop.plan(line).__dict__


def test_audit_projects_batch_with_hashed_evidence():
    cs = _audit([_op_dict("tedai legacy-win-app records.list")], frame=b"frame-bytes")["cell_state"]
    assert cs["phase"] == AuditPhase.ASSEMBLED.value
    assert cs["payload"]["batch"]["graph"] == "tedai-audit-v1"          # G7
    ent = cs["payload"]["batch"]["entities"][0]
    assert len(ent[":op/evidence-sha256"]) == 64                        # G9: hash only
    assert b"frame-bytes" not in str(cs).encode()
    assert cs["payload"]["liveIngest"] is False                         # G6


def test_audit_without_frame_has_no_evidence_attr():
    cs = _audit([_op_dict("tedai finder files.list")])["cell_state"]
    assert ":op/evidence-sha256" not in cs["payload"]["batch"]["entities"][0]


def test_audit_requires_caller_stamped_time():
    with pytest.raises(ValueError, match="planned_at"):
        transition_hash_evidence({"cell_state": {}, "ops": [_op_dict("tedai finder files.list")]})


# ── R0 scaffolds: .solve() raises by design ───────────────────────────────────────────

@pytest.mark.parametrize("cell_cls", [
    AppResolveCell, PairingBrokerCell, IntentPlanCell, ActuateInvokeCell, EvidenceAuditCell,
])
def test_solve_raises_at_r0(cell_cls):
    with pytest.raises(RuntimeError, match="R0 scaffold"):
        cell_cls().solve({})
