"""Tests for the karakuri T2 browser-use adapter plan builder (ADR-2606039200). Offline only (G6)."""

import pytest

from command import T2_ENGINE, TIER_T2, plan
from t2_browser import (
    BROWSER_ACTIONS,
    EVASION_ACTIONS,
    EvasionRefused,
    T2NotEligible,
    _make_step,
    assert_no_evasion,
    build_browser_plan,
)


def _permitted_t2_op(line="karakuri legacy-portal records.list"):
    op = plan(line)
    assert op.adapter_tier == TIER_T2 and op.t2_engine == T2_ENGINE
    return op


# ── eligibility (G2 / G6) ────────────────────────────────────────────────────────────

def test_plan_built_for_permitted_t2_read():
    out = build_browser_plan(_permitted_t2_op())
    assert out["engine"] == T2_ENGINE
    assert out["runtime"] == "langgraph->wasm"
    assert out["dry_run"] is True
    assert out["detection_evasion"] is False
    assert out["steps"][0]["action"] == "open_session"
    assert out["steps"][0]["server_held_key"] is False        # G3
    assert out["steps"][0]["account_owner"] == "member"       # G1


def test_read_plan_extracts_does_not_submit():
    out = build_browser_plan(_permitted_t2_op("karakuri legacy-portal records.list"))
    actions = [s["action"] for s in out["steps"]]
    assert "extract" in actions and "submit" not in actions


def test_mutate_plan_stops_at_member_signature():
    out = build_browser_plan(_permitted_t2_op("karakuri legacy-portal records.update --name x"))
    submit = [s for s in out["steps"] if s["action"] == "submit"][0]
    assert submit["requires"] == "member-signature"          # G5
    assert out["mutate_gate"] == "awaiting-member-sig"


def test_live_execution_refused():
    with pytest.raises(T2NotEligible):
        build_browser_plan(_permitted_t2_op(), live=True)    # G6


def test_t1_op_has_no_browser_plan():
    op = plan("karakuri squarespace pages.list")             # T1
    with pytest.raises(T2NotEligible):
        build_browser_plan(op)


def test_google_op_has_no_browser_plan():
    op = plan("karakuri google messages.list")               # T1 — API path, not browser
    with pytest.raises(T2NotEligible):
        build_browser_plan(op)


def test_tos_refused_op_has_no_browser_plan():
    op = plan("karakuri noauto-saas records.list", prefer_tier=TIER_T2)  # refused
    with pytest.raises(T2NotEligible):
        build_browser_plan(op)


# ── G2 / N2 detection-evasion is structurally unrepresentable ────────────────────────

def test_evasion_and_action_sets_are_disjoint():
    assert BROWSER_ACTIONS.isdisjoint(EVASION_ACTIONS)


@pytest.mark.parametrize("evasion", sorted(EVASION_ACTIONS))
def test_make_step_refuses_every_evasion_action(evasion):
    with pytest.raises(EvasionRefused):
        _make_step(evasion, target="anything")


def test_make_step_rejects_unknown_action():
    with pytest.raises(ValueError):
        _make_step("teleport", target="x")


def test_assert_no_evasion_catches_smuggled_step():
    steps = [{"action": "goto", "target": "x"}, {"action": "rotate_proxy"}]
    with pytest.raises(EvasionRefused):
        assert_no_evasion(steps)


def test_built_plan_passes_evasion_audit():
    out = build_browser_plan(_permitted_t2_op())
    assert_no_evasion(out["steps"])                          # does not raise
