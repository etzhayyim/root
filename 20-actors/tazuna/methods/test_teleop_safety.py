"""Tests for the tazuna teleop-safety reasoner (ADR-2606042100). Stdlib + pytest only."""

from __future__ import annotations

import pytest

from teleop_safety import (
    Command,
    ForceClassError,
    Grant,
    NoServerKeyError,
    TransparentForceError,
    admit_session,
    evaluate,
)

AUTHORIZED = Grant(force_class="soft-actuation", force_auth_ref="forceauth:sanae-soft-001",
                   deadman_ms=300, latency_budget_ms=150)


# ── N1: force-class admission ────────────────────────────────────────────────
def test_weaponizable_force_class_is_unrepresentable():
    with pytest.raises(ForceClassError):
        admit_session(Grant(force_class="weaponizable", force_auth_ref="x"))


def test_arbitrary_force_class_refused():
    with pytest.raises(ForceClassError):
        admit_session(Grant(force_class="lethal", force_auth_ref="x"))


@pytest.mark.parametrize("fc", ["observational", "soft-actuation", "powered-actuation"])
def test_admitted_force_classes_pass(fc):
    admit_session(Grant(force_class=fc, force_auth_ref="forceauth:ok"))  # no raise


# ── G3: Transparent Force ────────────────────────────────────────────────────
def test_grant_without_force_auth_ref_refused():
    with pytest.raises(TransparentForceError):
        admit_session(Grant(force_class="soft-actuation", force_auth_ref=""))


def test_actuation_refused_without_force_auth_even_if_signed():
    with pytest.raises(TransparentForceError):
        evaluate(Command("move", member_sig="m:sig"),
                 Grant(force_class="soft-actuation", force_auth_ref=""))


# ── G4: no-server-key ────────────────────────────────────────────────────────
def test_server_signature_always_refused():
    with pytest.raises(NoServerKeyError):
        evaluate(Command("move", member_sig="m:sig", server_sig="s:sig"), AUTHORIZED)


def test_actuation_requires_member_signature():
    with pytest.raises(NoServerKeyError):
        evaluate(Command("move", member_sig=""), AUTHORIZED)


def test_nominal_actuation_is_member_signed_and_passes():
    v = evaluate(Command("move", member_sig="m:sig", observed_latency_ms=40), AUTHORIZED)
    assert v.safe_state == "nominal"
    assert v.actuates is True
    assert v.effective_kind == "move"


# ── G10: soft-RT supervision ─────────────────────────────────────────────────
def test_deadman_lapse_forces_autonomy_fallback_halt():
    v = evaluate(Command("move", member_sig="m:sig", elapsed_since_presence_ms=900), AUTHORIZED)
    assert v.safe_state == "autonomy-fallback"
    assert v.actuates is False
    assert v.effective_kind == "halt"
    assert "deadman" in v.reason


def test_latency_breach_forces_autonomy_fallback_halt():
    v = evaluate(Command("move", member_sig="m:sig", observed_latency_ms=400), AUTHORIZED)
    assert v.safe_state == "autonomy-fallback"
    assert v.actuates is False
    assert v.effective_kind == "halt"
    assert "latency" in v.reason


def test_deadman_takes_priority_over_latency():
    v = evaluate(Command("move", member_sig="m:sig", elapsed_since_presence_ms=900,
                         observed_latency_ms=400), AUTHORIZED)
    assert "deadman" in v.reason


def test_estop_always_honoured_without_signature():
    v = evaluate(Command("estop"), AUTHORIZED)
    assert v.safe_state == "estopped"
    assert v.actuates is False


def test_halt_and_handback_need_no_signature():
    assert evaluate(Command("halt"), AUTHORIZED).effective_kind == "halt"
    assert evaluate(Command("handback"), AUTHORIZED).effective_kind == "handback"


def test_estop_honoured_even_with_breached_supervision():
    # an e-stop must work regardless of deadman/latency state
    v = evaluate(Command("estop", elapsed_since_presence_ms=99999), AUTHORIZED)
    assert v.safe_state == "estopped"


# ── G7: never live at R0 ─────────────────────────────────────────────────────
def test_actuation_is_advisory_only_at_r0():
    # evaluate() returns a verdict; it never performs a live actuation. `actuates` is a permission
    # flag the cell still routes through dry-run + operator/Council gate (G7).
    v = evaluate(Command("manipulate", member_sig="m:sig", observed_latency_ms=10), AUTHORIZED)
    assert v.actuates is True  # permitted...
    # ...but the lexicon pins dryRun const true and outwardGated const true; no live call here.


def test_unknown_command_kind_rejected():
    with pytest.raises(ValueError):
        evaluate(Command("teleport", member_sig="m:sig"), AUTHORIZED)
