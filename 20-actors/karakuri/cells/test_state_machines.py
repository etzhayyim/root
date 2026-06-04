"""State-machine tests for karakuri cells (R0). .solve() is NOT called (it raises)."""

import pytest

from session_broker.cell import SessionBrokerCell
from session_broker.state_machine import (
    BrokerPhase,
    transition_authorize_mutate,
    transition_build_grant,
    transition_read_allowed,
    transition_verify_owner,
)


def _broker_read(
    principal="member",
    account_owner="member",
    secret_ref="encref:com.etzhayyim.encrypted/squarespace-session",
):
    s = transition_verify_owner(
        {"cell_state": {"op_safety": "read"}, "principal": principal, "account_owner": account_owner}
    )
    s = transition_build_grant({**s, "secret_ref": secret_ref})
    s = transition_read_allowed(s)
    return s


def _broker_mutate(member_sig="member-ed25519-sig", server_sig="", safety="update"):
    s = transition_verify_owner({"cell_state": {"op_safety": safety}})
    s = transition_build_grant(s)
    s = transition_authorize_mutate({**s, "member_sig": member_sig, "server_sig": server_sig})
    return s


def test_read_op_reaches_read_allowed_without_signature():
    s = _broker_read()
    cs = s["cell_state"]
    assert cs["phase"] == BrokerPhase.READ_ALLOWED.value
    assert cs["server_held_key"] is False          # G3
    assert cs["payload"]["mutateGate"] == "read-allowed"   # G5
    assert cs["payload"]["grant"]["accountOwner"] == "member"  # G1


def test_mutate_op_reaches_authorized_on_member_sig():
    s = _broker_mutate()
    cs = s["cell_state"]
    assert cs["phase"] == BrokerPhase.AUTHORIZED.value
    assert cs["payload"]["mutateGate"] == "authorized"
    assert cs["payload"]["authorization"]["serverSigned"] is False  # G3
    assert cs["payload"]["authorization"]["outwardGated"] is True   # G6


def test_g1_refuses_third_party_account():
    with pytest.raises(ValueError, match="G1 violation"):
        _broker_read(account_owner="someone-else")


def test_g1_refuses_non_member_principal():
    with pytest.raises(ValueError, match="G1 violation"):
        _broker_read(principal="karakuri")


def test_g3_refuses_plaintext_secret():
    with pytest.raises(ValueError, match="G3 violation"):
        _broker_read(secret_ref="hunter2-plaintext-password")


def test_g3_refuses_server_signature_on_mutate():
    with pytest.raises(ValueError, match="G3 violation"):
        _broker_mutate(member_sig="member-sig", server_sig="server-sig")


def test_g5_mutate_requires_member_signature():
    with pytest.raises(ValueError, match="G5 violation"):
        _broker_mutate(member_sig="")


def test_solve_raises_at_r0():
    with pytest.raises(RuntimeError, match="R0 scaffold"):
        SessionBrokerCell().solve({})
