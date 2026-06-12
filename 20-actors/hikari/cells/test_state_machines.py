"""Tests for hikari gated cell state machines.

    cd 20-actors/hikari/cells
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "methods"))

from grid_edge.state_machine import (  # noqa: E402
    GridPhase,
    transition_commission,
    transition_commit_dispatch,
)
from solar_pv_install.state_machine import (  # noqa: E402
    InstallPhase,
    transition_commit_job,
    transition_plan_motion,
)
from _substrate import SafetyError  # noqa: E402

WITNESS = ["did:web:etzhayyim.com:kuniumi:robot:otete-01",
           "did:web:etzhayyim.com:kuniumi:robot:mimi-01"]


# ─── grid_edge ───────────────────────────────────────────────────────

def test_grid_edge_happy_path_commits_dry_run_dispatch():
    s1 = transition_commission({"load_step_kw": 140.0})
    assert s1["cell_state"]["phase"] == GridPhase.COMMISSIONED.value
    assert s1["cell_state"]["freq_restored"] is True
    s1["member_sig"] = "m:ed25519:demo"
    s1["witness_sigs"] = WITNESS
    s2 = transition_commit_dispatch(s1)
    dispatch = s2["cell_state"]["payload"]["dispatch"]
    assert s2["cell_state"]["phase"] == GridPhase.DISPATCH_COMMITTED.value
    assert dispatch["serverHeldKey"] is False
    assert dispatch["dryRun"] is True
    assert dispatch["witnessOk"] is True


def test_grid_edge_non_civilian_use_raises():
    with pytest.raises(SafetyError):
        transition_commission({"use": "weapon", "load_step_kw": 120.0})


def test_grid_edge_server_signature_refused():
    s1 = transition_commission({"load_step_kw": 120.0})
    s1["member_sig"] = "m:sig"
    s1["server_sig"] = "s:sig"
    s1["witness_sigs"] = WITNESS
    with pytest.raises(SafetyError):
        transition_commit_dispatch(s1)


# ─── solar_pv_install ────────────────────────────────────────────────

def test_install_happy_path_commits_dry_run_job():
    s1 = transition_plan_motion(
        {"target_x": 1.5, "target_y": 0.4, "member_sig": "m:sig", "witness_sigs": WITNESS}
    )
    assert s1["cell_state"]["phase"] == InstallPhase.MOTION_PLANNED.value
    s2 = transition_commit_job(s1)
    assert s2["cell_state"]["phase"] == InstallPhase.JOB_COMMITTED.value
    assert s2["cell_state"]["payload"]["job"]["dryRun"] is True


def test_install_unreachable_target_blocks_commit():
    s1 = transition_plan_motion(
        {"target_x": 99.0, "target_y": 0.0, "member_sig": "m:sig", "witness_sigs": WITNESS}
    )
    with pytest.raises(ValueError):
        transition_commit_job(s1)


def test_install_witness_below_quorum_blocks_commit():
    s1 = transition_plan_motion(
        {"target_x": 1.5, "target_y": 0.4, "member_sig": "m:sig", "witness_sigs": ["did:r:a"]}
    )
    with pytest.raises(ValueError):
        transition_commit_job(s1)
