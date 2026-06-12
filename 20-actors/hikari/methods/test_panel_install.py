"""Tests for hikari panel-install robot motion loop.

    cd 20-actors/hikari/methods
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest
"""

from __future__ import annotations

import pytest

from _substrate import SafetyError
from panel_install import OTETE_ARM, plan_panel_install, to_datoms

WITNESS = ["did:web:etzhayyim.com:kuniumi:robot:otete-01",
           "did:web:etzhayyim.com:kuniumi:robot:mimi-01"]


def test_reachable_target_plans_clean_motion():
    plan = plan_panel_install((1.5, 0.4), member_sig="m:ed25519:demo", witness_sigs=WITNESS)
    assert plan.reachable
    assert plan.joints_goal is not None
    assert plan.envelope_ok
    assert plan.witness_ok
    assert plan.server_held_key is False
    assert plan.dry_run is True


def test_unreachable_target_reports_not_reachable():
    far = (OTETE_ARM.max_reach + 1.0, 0.0)
    plan = plan_panel_install(far, member_sig="m:sig", witness_sigs=WITNESS)
    assert plan.reachable is False
    assert plan.joints_goal is None
    assert plan.trajectory_steps == 0


@pytest.mark.parametrize("use", ["weapon", "interdiction", "smelting"])
def test_non_civilian_use_refused(use):
    with pytest.raises(SafetyError):
        plan_panel_install((1.0, 0.2), member_sig="m:sig", witness_sigs=WITNESS, use=use)


def test_server_signature_refused():
    with pytest.raises(SafetyError):
        plan_panel_install((1.0, 0.2), member_sig="m:sig", witness_sigs=WITNESS, server_sig="s:sig")


def test_missing_member_signature_refused():
    with pytest.raises(SafetyError):
        plan_panel_install((1.0, 0.2), member_sig="", witness_sigs=WITNESS)


def test_witness_quorum_below_two_recorded_not_raised():
    plan = plan_panel_install((1.2, 0.3), member_sig="m:sig", witness_sigs=["did:r:a"])
    assert plan.witness_ok is False  # escalation Datom, not a hard raise


def test_human_proximity_forces_slower_envelope():
    # A fast 60-step move that is fine far from humans violates the slow ceiling
    # when a person may be present.
    target = (1.8, 0.6)
    fast = plan_panel_install(target, member_sig="m:sig", witness_sigs=WITNESS,
                              human_present=False, steps=15)
    slow_ceiling = plan_panel_install(target, member_sig="m:sig", witness_sigs=WITNESS,
                                      human_present=True, steps=15)
    assert fast.envelope_ok is True
    assert slow_ceiling.envelope_ok is False
    assert slow_ceiling.envelope_violations


def test_datoms_dry_run_and_keyless():
    plan = plan_panel_install((1.5, 0.4), member_sig="m:sig", witness_sigs=WITNESS)
    d = to_datoms(plan, "install-001")
    assert d[":install/server-held-key"] is False
    assert d[":install/dry-run"] is True
    assert d[":install/reachable"] is True
