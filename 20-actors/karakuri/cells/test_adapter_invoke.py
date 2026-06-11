"""State-machine tests for the karakuri adapter_invoke cell (R0). .solve() is NOT called (it raises)."""

import pytest

from adapter_invoke.cell import AdapterInvokeCell
from adapter_invoke.state_machine import (
    EXECUTE_GATE,
    OUTCOME_REFUSED_TOS,
    OUTCOME_UNKNOWN_SERVICE,
    AdapterPhase,
    transition_dry_run,
    transition_execute_gated,
    transition_mutate_gate,
    transition_tos_gate,
)


def _run(line, prefer_tier=None):
    """Drive the full graph; stops early if a transition routes to 'end'."""
    s = transition_tos_gate({"line": line, "prefer_tier": prefer_tier})
    if s["next_node"] == "end":
        return s
    s = transition_mutate_gate(s)
    s = transition_dry_run(s)
    s = transition_execute_gated(s)
    return s


# ── happy paths ──────────────────────────────────────────────────────────────────────

def test_t1_read_reaches_execute_gated_dry_run():
    s = _run("karakuri squarespace pages.list")
    cs = s["cell_state"]
    assert cs["phase"] == AdapterPhase.EXECUTE_GATED.value
    assert cs["payload"]["mutateGate"] == "read-allowed"        # G5
    assert cs["payload"]["plan"]["tier"] == "t1-official-api"
    assert "engine" not in cs["payload"]["plan"]                # no browser-use on T1
    assert cs["payload"]["executed"] is False                  # G6
    assert cs["payload"]["executeGate"] == EXECUTE_GATE


def test_google_read_routes_to_official_api_not_browser():
    s = _run("karakuri google messages.list")
    plan = s["cell_state"]["payload"]["plan"]
    assert plan["tier"] == "t1-official-api"
    assert "engine" not in plan                                 # Google is NOT browser-automated


def test_t2_op_embeds_browser_use_plan():
    s = _run("karakuri legacy-portal records.list")             # no API + ToS permits → T2
    plan = s["cell_state"]["payload"]["plan"]
    assert plan["tier"] == "t2-headless-browser"
    assert plan["engine"] == "browser-use"                      # the T2 engine
    assert plan["runtime"] == "langgraph->wasm"
    assert plan["detectionEvasion"] is False                    # G2/N2 — unrepresentable
    assert plan["steps"][0]["action"] == "open_session"
    assert plan["steps"][0]["server_held_key"] is False         # G3


def test_t2_mutate_awaits_member_sig_but_still_plans():
    s = _run("karakuri legacy-portal records.update --name x")
    cs = s["cell_state"]
    assert cs["payload"]["mutateGate"] == "awaiting-member-sig"  # G5
    submit = [st for st in cs["payload"]["plan"]["steps"] if st["action"] == "submit"][0]
    assert submit["requires"] == "member-signature"
    assert cs["payload"]["executed"] is False                   # G6 — still not executed


# ── refusals ─────────────────────────────────────────────────────────────────────────

def test_g2_browser_automation_on_google_refused_no_plan():
    s = _run("karakuri google search.query --q hi", prefer_tier="t2-headless-browser")
    cs = s["cell_state"]
    assert cs["phase"] == AdapterPhase.REFUSED.value
    assert cs["payload"]["adapterOutcome"] == OUTCOME_REFUSED_TOS  # G2
    assert "plan" not in cs["payload"]                            # nothing planned, nothing executed


def test_g2_browser_automation_on_facebook_refused():
    s = _run("karakuri facebook posts.list", prefer_tier="t2-headless-browser")
    assert s["cell_state"]["payload"]["adapterOutcome"] == OUTCOME_REFUSED_TOS


def test_g2_automation_prohibited_service_refused():
    s = _run("karakuri noauto-saas records.list", prefer_tier="t2-headless-browser")
    assert s["cell_state"]["payload"]["adapterOutcome"] == OUTCOME_REFUSED_TOS


def test_g8_unknown_service_degrades_honestly():
    s = _run("karakuri totally-made-up things.list")
    cs = s["cell_state"]
    assert cs["phase"] == AdapterPhase.REFUSED.value
    assert cs["payload"]["adapterOutcome"] == OUTCOME_UNKNOWN_SERVICE
    assert "plan" not in cs["payload"]


# ── R0 invariant ─────────────────────────────────────────────────────────────────────

def test_solve_raises_at_r0():
    with pytest.raises(RuntimeError, match="R0 scaffold"):
        AdapterInvokeCell().solve({})
