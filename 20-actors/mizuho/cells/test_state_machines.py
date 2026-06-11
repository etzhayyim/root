"""Tests for mizuho gated cell state machines.

    cd 20-actors/mizuho/cells
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "methods"))  # append: cells/water_supply package must win

from water_supply.state_machine import (  # noqa: E402
    SupplyPhase,
    transition_commission,
    transition_commit_supply,
)
from _substrate import SafetyError  # noqa: E402

WITNESS = [
    "did:web:etzhayyim.com:kuniumi:robot:tsutsu-01",
    "did:web:etzhayyim.com:kuniumi:robot:shizuku-01",
]


# ─── water_supply ────────────────────────────────────────────────────

def test_supply_happy_path_commits_dry_run_record():
    s1 = transition_commission({"demand_step_lps": 20.0, "service_population": 200})
    assert s1["cell_state"]["phase"] == SupplyPhase.COMMISSIONED.value
    assert s1["cell_state"]["level_restored"] is True
    assert s1["cell_state"]["ceiling_respected"] is True
    s1["member_sig"] = "m:ed25519:demo"
    s1["witness_sigs"] = WITNESS
    s2 = transition_commit_supply(s1)
    rec = s2["cell_state"]["payload"]["supply_record"]
    assert s2["cell_state"]["phase"] == SupplyPhase.SUPPLY_COMMITTED.value
    assert rec["serverHeldKey"] is False
    assert rec["dryRun"] is True
    assert rec["witnessOk"] is True


def test_supply_non_civilian_use_raises():
    with pytest.raises(SafetyError):
        transition_commission({"use": "weapon", "demand_step_lps": 20.0})


def test_supply_over_cap_raises_g3():
    with pytest.raises(SafetyError):
        transition_commission({"demand_step_lps": 20.0, "service_population": 9999})


def test_supply_fluoride_without_consent_raises_g6():
    with pytest.raises(SafetyError):
        transition_commission({"demand_step_lps": 20.0, "dosing_agent": "fluoridate"})


def test_supply_fluoride_with_consent_commissions():
    s1 = transition_commission(
        {"demand_step_lps": 20.0, "dosing_agent": "fluoridate", "per_member_consent": True}
    )
    assert s1["cell_state"]["phase"] == SupplyPhase.COMMISSIONED.value
    assert s1["cell_state"]["residual_held"] is True


def test_supply_server_signature_refused():
    s1 = transition_commission({"demand_step_lps": 20.0})
    s1["member_sig"] = "m:sig"
    s1["server_sig"] = "s:sig"
    s1["witness_sigs"] = WITNESS
    with pytest.raises(SafetyError):
        transition_commit_supply(s1)


def test_supply_witness_below_quorum_blocks_commit():
    s1 = transition_commission({"demand_step_lps": 20.0})
    s1["member_sig"] = "m:sig"
    s1["witness_sigs"] = ["did:r:a"]
    with pytest.raises(ValueError):
        transition_commit_supply(s1)


def test_cell_solve_stays_gated():
    from water_supply.cell import WaterSupplyCell

    with pytest.raises(RuntimeError):
        WaterSupplyCell().solve({})
