"""Tests for kamado 竈 cell state machines (ADR-2606051500).

Run in isolation:
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_state_machines.py
"""
from __future__ import annotations

import pytest

from decommission_plan import state_machine as dp
from feedstock_guard import state_machine as fg


# ── feedstock_guard: G1 closed-loop-only + G2/D3 ─────────────────────────────
def _run_guard(feedstock, energy="hikari-renewable", fate="combusted-fuel"):
    s = {"cell_state": {}, "feedstock": feedstock, "energy": energy, "fate": fate}
    s = fg.transition_to_screened(s)
    s = fg.transition_to_balanced(s)
    return fg.transition_to_admitted(s)


def test_g1_biogenic_run_is_admitted_and_passes_d3():
    s = _run_guard(":biogenic")
    cs = s["cell_state"]
    assert cs["phase"] == fg.GuardPhase.ADMITTED.value
    assert cs["passes_d3"] is True
    assert cs["net_delta"] <= fg.D3_TOLERANCE


def test_g1_fossil_feedstock_raises_before_any_record():
    s = {"cell_state": {}, "feedstock": ":fossil-virgin-crude"}
    with pytest.raises(ValueError, match="G1 violation"):
        fg.transition_to_screened(s)


def test_g2_locked_carbon_is_net_negative():
    s = _run_guard(":biogenic", fate="durable-material")
    assert s["cell_state"]["net_delta"] < 0


def test_g2_grid_powered_combusted_fails_d3_and_is_refused():
    # grid-mixed energy + combusted biogenic → net ~0.22 > tolerance → not admitted
    s = {"cell_state": {}, "feedstock": ":biogenic", "energy": ":grid-mixed",
         "fate": ":combusted-fuel"}
    s = fg.transition_to_screened(s)
    s = fg.transition_to_balanced(s)
    assert s["cell_state"]["passes_d3"] is False
    with pytest.raises(ValueError, match="G2 violation"):
        fg.transition_to_admitted(s)


# ── decommission_plan: G3 wind-down-only + G5 + G8 ───────────────────────────
def _run_plan(intervention, convert_to="none", principal="operator", server_key=False):
    s = {"cell_state": {}, "refinery": "rf.jp.muroran", "intervention": intervention,
         "convert_to": convert_to, "principal": principal, "server_held_key": server_key}
    s = dp.transition_to_scoped(s)
    s = dp.transition_to_planned(s)
    return dp.transition_to_gated(s)


def test_g3_convert_plan_reaches_gated_intent_only():
    s = _run_plan(":convert", convert_to=":synthesis-plant")
    cs = s["cell_state"]
    assert cs["phase"] == dp.PlanPhase.GATED.value
    assert cs["payload"]["status"] == "intent-only"
    assert cs["payload"]["outwardGated"] is True


def test_g3_fossil_life_extension_is_unrepresentable():
    for bad in (":expand", ":restart-fossil"):
        with pytest.raises(ValueError, match="G3 violation"):
            _run_plan(bad)


def test_g5_server_held_key_is_refused():
    with pytest.raises(ValueError, match="G5 violation"):
        _run_plan(":decommission", server_key=True)


def test_g3_all_permitted_interventions_pass():
    for ok in (":decommission", ":remediate", ":convert", ":monitor"):
        s = _run_plan(ok)
        assert s["cell_state"]["phase"] == dp.PlanPhase.GATED.value
