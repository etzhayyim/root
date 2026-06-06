"""State-machine tests for the karakuri command_plan cell (R0). .solve() is NOT called."""

import pytest

from command_plan.cell import CommandPlanCell
from command_plan.state_machine import (
    PlanPhase,
    transition_charter_scan,
    transition_classify,
    transition_parse,
    transition_plan,
)


def _plan(brief):
    s = transition_parse({"brief": brief})
    if s["next_node"] == "end":
        return s
    s = transition_classify(s)
    s = transition_charter_scan(s)
    s = transition_plan(s)
    return s


def test_nl_read_brief_plans_t1_google_op():
    p = _plan("show my gmail messages")["cell_state"]["payload"]
    assert p["charterClean"] is True
    assert len(p["ops"]) == 1
    op = p["ops"][0]
    assert (op["service"], op["noun"], op["verb"]) == ("google", "messages", "list")
    assert op["adapter_tier"] == "t1-official-api"
    assert p["inference"] == "murakumo"          # G4
    assert p["dryRun"] is True                    # G6


def test_nl_mutate_brief_marks_awaiting_sig():
    p = _plan("delete a post on facebook")["cell_state"]["payload"]
    assert p["mutateGate"] == "awaiting-member-sig"   # G5


def test_charter_dirty_brief_plans_nothing():
    p = _plan("list my gmail and set up a casino gambling page")["cell_state"]["payload"]
    assert p["charterClean"] is False
    assert p["ops"] == []                         # N6


def test_unparseable_brief_degrades():
    s = _plan("hello there")
    cs = s["cell_state"]
    assert cs["phase"] == PlanPhase.REFUSED.value
    assert cs["payload"]["outcome"] == "no-confident-parse"


def test_solve_raises_at_r0():
    with pytest.raises(RuntimeError, match="R0 scaffold"):
        CommandPlanCell().solve({})
