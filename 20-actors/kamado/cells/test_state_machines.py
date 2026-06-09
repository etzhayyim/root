"""Tests for kamado 竈 cell state machines (ADR-2606051500).

Run in isolation:
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_state_machines.py
"""
from __future__ import annotations

import pytest

from decommission_plan import state_machine as dp
from decommission_robot import state_machine as dr
from feedstock_guard import state_machine as fg

# decommission_robot.state_machine inserts ../methods on sys.path; import the shared
# SafetyError from there for the entry-gate assertions.
from _substrate import SafetyError  # noqa: E402

WITNESS = [
    "did:web:etzhayyim.com:kuniumi:robot:kamado-arm-01",
    "did:web:etzhayyim.com:kuniumi:robot:kamado-mimi-01",
]


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


# ── decommission_robot: purge → entry-gated cut → member-signed commit ────────
def _run_robot(target_x=1.5, target_y=0.4, member_sig="m:sig", witness=None,
               server_sig="", initial_ppm=120.0):
    s = {"cell_state": {}, "target_x": target_x, "target_y": target_y,
         "member_sig": member_sig, "witness_sigs": witness if witness is not None else WITNESS,
         "server_sig": server_sig, "initial_ppm": initial_ppm}
    s = dr.transition_purge(s)
    s = dr.transition_plan_cut(s)
    return dr.transition_commit_entry(s)


def test_robot_happy_path_purges_then_commits_dry_run_entry():
    s1 = dr.transition_purge({"cell_state": {}})
    assert s1["cell_state"]["phase"] == dr.RobotPhase.PURGED.value
    assert s1["cell_state"]["entry_permitted"] is True
    s1["member_sig"] = "m:ed25519:demo"
    s1["witness_sigs"] = WITNESS
    s2 = dr.transition_plan_cut(s1)
    assert s2["cell_state"]["phase"] == dr.RobotPhase.CUT_PLANNED.value
    s3 = dr.transition_commit_entry(s2)
    rec = s3["cell_state"]["payload"]["record"]
    assert s3["cell_state"]["phase"] == dr.RobotPhase.ENTRY_COMMITTED.value
    assert rec[":decommission/server-held-key"] is False
    assert rec[":decommission/dry-run"] is True
    assert rec[":decommission/entry-permitted"] is True
    assert rec[":decommission/committed"] is True


def test_robot_entry_gate_refuses_unpurged_zone():
    # A zone that cannot be purged below the limit (purge too weak) must refuse entry
    # at the cut-plan transition — structural SafetyError, not a warning.
    s = {"cell_state": {}, "initial_ppm": 120.0, "target_ppm": 10.0, "gas_limit": 10.0}
    # Force an un-purged final concentration by overriding state after purge.
    s = dr.transition_purge(s)
    s["cell_state"]["final_ppm"] = 50.0  # above the 10 ppm limit
    s["member_sig"] = "m:sig"
    s["witness_sigs"] = WITNESS
    with pytest.raises(SafetyError, match="ENTRY REFUSED"):
        dr.transition_plan_cut(s)


def test_robot_non_civilian_use_raises_on_purge():
    with pytest.raises(SafetyError):
        dr.transition_purge({"cell_state": {}, "use": "weapon"})


@pytest.mark.parametrize("use", ["restart-fossil", "expand", "throughput-revamp"])
def test_robot_fossil_life_extension_use_unrepresentable(use):
    # G3: a fossil life-extension verb is not in the civilian allowlist; closed-world
    # refusal rejects it at the purge stage, before any motion is planned.
    with pytest.raises(SafetyError):
        dr.transition_purge({"cell_state": {}, "use": use})


def test_robot_server_signature_refused():
    s = dr.transition_purge({"cell_state": {}})
    s["member_sig"] = "m:sig"
    s["server_sig"] = "s:sig"
    s["witness_sigs"] = WITNESS
    with pytest.raises(SafetyError):
        dr.transition_plan_cut(s)


def test_robot_unreachable_target_blocks_commit():
    s = dr.transition_purge({"cell_state": {}})
    s["target_x"] = 99.0
    s["target_y"] = 0.0
    s["member_sig"] = "m:sig"
    s["witness_sigs"] = WITNESS
    s = dr.transition_plan_cut(s)
    with pytest.raises(ValueError):
        dr.transition_commit_entry(s)


def test_robot_witness_below_quorum_blocks_commit():
    s = dr.transition_purge({"cell_state": {}})
    s["member_sig"] = "m:sig"
    s["witness_sigs"] = ["did:r:only-one"]
    s = dr.transition_plan_cut(s)
    with pytest.raises(ValueError):
        dr.transition_commit_entry(s)
