"""Tests for the tazuna teleop_session state machine (ADR-2606042100). G3/G4/G10/N1.

These exercise the transition functions directly (the cell's .solve() raises at R0).
"""

from __future__ import annotations

import pytest

from teleop_session.cell import TeleopSessionCell
from teleop_session.state_machine import (
    SessionPhase,
    transition_build_grant,
    transition_relay_command,
    transition_verify_force_auth,
)


def _wrap(cell_state: dict) -> dict:
    return {"cell_state": cell_state}


# ── R0 invariant: solve() raises ─────────────────────────────────────────────
def test_solve_raises_at_r0():
    with pytest.raises(RuntimeError):
        TeleopSessionCell().solve({})


# ── N1 / G3: force-auth admission ────────────────────────────────────────────
def test_verify_force_auth_refuses_unrepresentable_class():
    st = _wrap({"force_class": "weaponizable", "force_auth_ref": "x"})
    with pytest.raises(ValueError):
        transition_verify_force_auth(st)


def test_verify_force_auth_requires_force_auth_ref():
    st = _wrap({"force_class": "soft-actuation", "force_auth_ref": ""})
    with pytest.raises(ValueError):
        transition_verify_force_auth(st)


def test_verify_force_auth_passes_when_authorized():
    st = _wrap({"force_class": "soft-actuation", "force_auth_ref": "forceauth:ok"})
    out = transition_verify_force_auth(st)
    assert out["cell_state"]["phase"] == SessionPhase.FORCE_AUTHORIZED.value
    assert out["next_node"] == "grant_built"


# ── G4: no-server-key grant ──────────────────────────────────────────────────
def test_build_grant_refuses_plaintext_secret():
    st = _wrap({"secret_ref": "hunter2"})
    with pytest.raises(ValueError):
        transition_build_grant(st)


def test_build_grant_is_server_keyless():
    st = _wrap({"secret_ref": "encref:com.etzhayyim.encrypted/tazuna-x",
                "force_auth_ref": "forceauth:ok"})
    out = transition_build_grant(st)
    grant = out["cell_state"]["payload"]["grant"]
    assert grant["serverHeldKey"] is False
    assert grant["onChainAnchor"] is True
    assert grant["outwardGated"] is True


# ── G4 / G10: command relay ──────────────────────────────────────────────────
def test_relay_refuses_server_signature():
    st = _wrap({"command_kind": "move", "member_sig": "m", "server_sig": "s"})
    with pytest.raises(ValueError):
        transition_relay_command(st)


def test_relay_actuation_requires_member_sig():
    st = _wrap({"command_kind": "move", "member_sig": ""})
    with pytest.raises(ValueError):
        transition_relay_command(st)


def test_relay_nominal_actuation_passes_dry_run():
    st = _wrap({"command_kind": "move", "member_sig": "m", "observed_latency_ms": 10,
                "latency_budget_ms": 150, "deadman_ms": 300})
    out = transition_relay_command(st)
    cmd = out["cell_state"]["payload"]["command"]
    assert cmd["safeState"] == "nominal"
    assert cmd["dryRun"] is True
    assert cmd["serverSigned"] is False
    assert out["cell_state"]["phase"] == SessionPhase.COMMAND_RELAYED.value


def test_relay_deadman_lapse_drops_to_safe_stop():
    st = _wrap({"command_kind": "move", "member_sig": "m", "elapsed_since_presence_ms": 999,
                "deadman_ms": 300})
    out = transition_relay_command(st)
    cmd = out["cell_state"]["payload"]["command"]
    assert cmd["kind"] == "halt"
    assert cmd["safeState"] == "autonomy-fallback"
    assert out["cell_state"]["phase"] == SessionPhase.SAFE_STOPPED.value


def test_relay_estop_always_honoured():
    st = _wrap({"command_kind": "estop"})
    out = transition_relay_command(st)
    assert out["cell_state"]["payload"]["command"]["safeState"] == "estopped"
