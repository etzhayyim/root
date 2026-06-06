#!/usr/bin/env python3
"""Tests for 扶持 (fuchi) live_gate.py + the per-engine live legs — R1(live).

The core deliverable: every outward leg REFUSES by default, and only fires when the operator
flag + attestation + Council level + member signature are ALL present. cash≡0 / no-server-key
hold in live mode too. Standalone-runnable: python3 test_live_gate.py
"""
from __future__ import annotations

import sys

import book
import couple as couple_mod
import provision as prov
import vote as vote_mod
from live_gate import (
    LEG_POLICY,
    LiveGate,
    LiveGateRefused,
    gate_status,
    require,
)

# a fully-satisfied env + gate for each leg (env flag present)
def _env(leg, on=True):
    flag = LEG_POLICY[leg][0]
    return {flag: "1"} if on else {}


def _full_gate(leg, level=None):
    lvl = LEG_POLICY[leg][1] if level is None else level
    return LiveGate(leg=leg, operator_did="did:web:etzhayyim.com:operator:op1",
                    council_level=lvl, member_signature="sig:member:abel:ed25519:deadbeef")


# ── construction ────────────────────────────────────────────────────────────
def test_unknown_leg_rejected():
    try:
        LiveGate(leg="bogus")
        assert False, "unknown leg should raise"
    except ValueError:
        pass


def test_all_four_legs_known():
    assert set(LEG_POLICY) == {"provision", "vote", "book", "couple"}


def test_couple_requires_lv7_others_lv6():
    assert LEG_POLICY["couple"][1] == 7
    assert LEG_POLICY["provision"][1] == 6
    assert LEG_POLICY["vote"][1] == 6
    assert LEG_POLICY["book"][1] == 6


# ── default refusal (the deliverable) ────────────────────────────────────────
def test_default_gate_refused_every_leg():
    for leg in LEG_POLICY:
        st = gate_status(LiveGate(leg=leg), env={})
        assert st["admissible"] is False
        try:
            require(LiveGate(leg=leg), env={})
            assert False, f"{leg} default must refuse"
        except LiveGateRefused:
            pass


def test_missing_operator_flag_refused():
    for leg in LEG_POLICY:
        g = _full_gate(leg)
        try:
            require(g, env={})  # no env flag
            assert False
        except LiveGateRefused as e:
            assert "operator process flag" in str(e)


def test_missing_attestation_refused():
    leg = "provision"
    g = LiveGate(leg=leg, operator_did="", council_level=6, member_signature="sig:x")
    try:
        require(g, env=_env(leg))
        assert False
    except LiveGateRefused as e:
        assert "operator attestation" in str(e)


def test_insufficient_council_refused():
    leg = "couple"  # needs Lv7
    g = LiveGate(leg=leg, operator_did="op", council_level=6, member_signature="sig:x")
    try:
        require(g, env=_env(leg))
        assert False
    except LiveGateRefused as e:
        assert "Lv7" in str(e)


def test_lv6_ok_for_provision_not_couple():
    # Lv6 satisfies provision but not couple
    require(_full_gate("provision", level=6), env=_env("provision"))  # ok
    try:
        require(_full_gate("couple", level=6), env=_env("couple"))
        assert False
    except LiveGateRefused:
        pass


def test_server_signer_refused():
    for sig in ("", "server", "did:server:x", ":server", "anon", "  "):
        leg = "vote"
        g = LiveGate(leg=leg, operator_did="op", council_level=6, member_signature=sig)
        try:
            require(g, env=_env(leg))
            assert False, f"signer {sig!r} must be refused"
        except LiveGateRefused as e:
            assert "member signature" in str(e) or "operator" in str(e)


def test_full_gate_admissible_every_leg():
    for leg in LEG_POLICY:
        st = require(_full_gate(leg), env=_env(leg))
        assert st["admissible"] is True


# ── provision.dispatch_live ──────────────────────────────────────────────────
def _intents():
    rails = [{"kind": "food-mitsuho", "imputed_usd_micros_yr": 12_000_000_000},
             {"kind": "liquidity-warifu", "imputed_usd_micros_yr": 3_000_000_000,
              "member_principal": True}]
    return prov.provision(rails, "alloc:abel")


def test_dispatch_live_refused_by_default():
    try:
        prov.dispatch_live(_intents(), LiveGate(leg="provision"), env={})
        assert False
    except LiveGateRefused:
        pass


def test_dispatch_live_ok_when_gated():
    out = prov.dispatch_live(_intents(), _full_gate("provision"), env=_env("provision"))
    assert len(out) == 2
    # cash≡0 + no-server-key hold on the wrapped intent in live mode
    assert all(d.intent.cash_usd_micros == 0 for d in out)
    assert all(d.intent.server_held_key is False for d in out)
    # member-principal liquidity stays member-principal
    assert any(d.intent.member_principal for d in out)


def test_dispatch_live_intent_stays_unpublished():
    out = prov.dispatch_live(_intents(), _full_gate("provision"), env=_env("provision"))
    assert all(d.intent.published is False for d in out)  # G10 structural on the intent
    assert all(d.authorized_to_publish for d in out)      # authorization on the receipt


# ── vote.finalize_binding ────────────────────────────────────────────────────
def _ballots():
    return vote_mod.ballots_from_seed([
        {":ballot/voter": "did:m:a", ":ballot/choice": "yes", ":ballot/cast-at": 10},
        {":ballot/voter": "did:m:b", ":ballot/choice": "yes", ":ballot/cast-at": 11},
        {":ballot/voter": "did:m:c", ":ballot/choice": "yes", ":ballot/cast-at": 12},
    ])


def test_finalize_binding_refused_by_default():
    try:
        vote_mod.finalize_binding(_ballots(), 0, 100, LiveGate(leg="vote"), env={})
        assert False
    except LiveGateRefused:
        pass


def test_finalize_binding_ok_after_timelock():
    r = vote_mod.finalize_binding(_ballots(), 0, 100, _full_gate("vote"), env=_env("vote"))
    assert r["binding"] is True
    assert r["outcome"] == "accepted"


def test_finalize_binding_timelock_still_strict():
    # gated, but before the 48h window closes → ValueError (the gate can't bypass the timelock)
    try:
        vote_mod.finalize_binding(_ballots(), 0, 10, _full_gate("vote"), env=_env("vote"))
        assert False
    except ValueError as e:
        assert "timelock" in str(e)


# ── book.write_live ──────────────────────────────────────────────────────────
def _ledger():
    rails = [{"kind": "food-mitsuho", "imputed_usd_micros_yr": 12_000_000_000}]
    return book.book_toritate(rails, "alloc:abel", "did:m:abel")


def test_write_live_refused_by_default():
    try:
        book.write_live(_ledger(), LiveGate(leg="book"), env={})
        assert False
    except LiveGateRefused:
        pass


def test_write_live_ok_when_gated_cash_zero():
    r = book.write_live(_ledger(), _full_gate("book"), env=_env("book"))
    assert r.committed is True
    assert all(e.cash_usd_micros == 0 for e in r.entries)


# ── couple.commit_live ───────────────────────────────────────────────────────
def _funded():
    ev = couple_mod.DisplacementEvent("sanae", "c-sanae", 12, 60_000_000_000, funded=True)
    return ev, couple_mod.earmark_from_surplus(ev)


def _unfunded():
    ev = couple_mod.DisplacementEvent("hataori", "c-hataori", 30, 0, funded=False)
    return ev, couple_mod.earmark_from_surplus(ev)


def test_commit_live_refused_without_gate():
    ev, em = _funded()
    try:
        couple_mod.commit_live(ev, em, 8_500_000_000, LiveGate(leg="couple"), env={})
        assert False
    except LiveGateRefused:
        pass


def test_commit_live_ok_when_gated_and_funded():
    ev, em = _funded()
    c = couple_mod.commit_live(ev, em, 8_500_000_000, _full_gate("couple"), env=_env("couple"))
    assert c.admissible is True
    assert c.cohort_id == "c-sanae"


def test_commit_live_g2_refuses_unfunded_even_when_gated():
    # gate passes (Lv7) but the G2 coupling gate refuses an unfunded cohort → ValueError
    ev, em = _unfunded()
    try:
        couple_mod.commit_live(ev, em, 1_000_000, _full_gate("couple"), env=_env("couple"))
        assert False
    except ValueError as e:
        assert "G2" in str(e)


def test_commit_live_g2_refuses_over_earmark():
    ev, em = _funded()  # earmark = 54_000_000_000
    try:
        couple_mod.commit_live(ev, em, 99_000_000_000, _full_gate("couple"), env=_env("couple"))
        assert False
    except ValueError as e:
        assert "exceeds funded earmark" in str(e)


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"test_live_gate.py: {len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
