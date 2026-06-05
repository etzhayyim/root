#!/usr/bin/env python3
"""Behavioral tests for triage.py — risk/quality scoring + pure-function routing (G2).

Standalone-runnable AND pytest-compatible (repo pytest plugin env is broken):
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_triage.py
    python3 test_triage.py
"""
from __future__ import annotations

import pathlib

from _edn import load_edn
from triage import (
    QUALITY_AUTO_ACCEPT, assess_quality, rider_hit, route_for, score_edit,
)

_SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-edit-graph.kotoba.edn"


def _seed():
    return {e[":edit/id"]: e for e in load_edn(_SEED)[":edit/batch"]}


# ── route_for is a PURE FUNCTION of (risk, quality, rider) — G2 ─────────────────
def test_route_invariant_goes_to_council():
    assert route_for("invariant", 1.0, "") == "council-lv7"


def test_route_low_high_quality_auto_accepts():
    assert route_for("low", QUALITY_AUTO_ACCEPT, "") == "auto-accept"
    assert route_for("low", 0.95, "") == "auto-accept"


def test_route_low_but_thin_goes_to_vote():
    assert route_for("low", QUALITY_AUTO_ACCEPT - 0.01, "") == "vote"


def test_route_high_risk_always_votes():
    assert route_for("high", 1.0, "") == "vote"
    assert route_for("medium", 1.0, "") == "vote"


def test_route_rider_hit_is_refused_regardless():
    # even a "low risk, perfect quality" shape is refused if a Rider token is present
    assert route_for("low", 1.0, "advertis") == "refused"


# ── full scoring over the seed batch ────────────────────────────────────────────
def test_seed_e1_kgfact_sourced_auto_accepts():
    t = score_edit(_seed()["e1"])
    assert t[":triage/risk"] == ":low"
    assert t[":triage/route"] == ":auto-accept"
    assert t[":triage/quality"] >= QUALITY_AUTO_ACCEPT


def test_seed_e2_status_change_is_high_and_votes():
    t = score_edit(_seed()["e2"])
    assert t[":triage/risk"] == ":high"        # :status is a sensitive attr
    assert t[":triage/route"] == ":vote"


def test_seed_e3_profile_edit_is_medium_and_votes():
    t = score_edit(_seed()["e3"])
    assert t[":triage/risk"] == ":medium"
    assert t[":triage/route"] == ":vote"


def test_seed_e4_license_attr_is_invariant_and_council():
    t = score_edit(_seed()["e4"])
    assert t[":triage/risk"] == ":invariant"   # :license ∈ INVARIANT_ATTRS
    assert t[":triage/route"] == ":council-lv7"


def test_seed_e5_advertising_is_rider_refused():
    t = score_edit(_seed()["e5"])
    assert t[":triage/route"] == ":refused"
    assert t[":triage/quality"] == 0.0
    assert t[":triage/rider-token"]            # a token was found


# ── validation gates (G1/G3/G4) raise, they don't silently pass ─────────────────
def test_score_edit_refuses_non_member_author():
    e = dict(_seed()["e1"]); e[":edit/author-kind"] = ":server"
    try:
        score_edit(e); assert False, "expected ValueError"
    except ValueError as ex:
        assert "G1" in str(ex)


def test_score_edit_refuses_server_held_key():
    e = dict(_seed()["e1"]); e[":edit/server-held-key"] = True
    try:
        score_edit(e); assert False, "expected ValueError"
    except ValueError as ex:
        assert "no-server-key" in str(ex)


def test_score_edit_refuses_unsourced():
    e = dict(_seed()["e1"]); e[":edit/provenance"] = ""
    try:
        score_edit(e); assert False, "expected ValueError"
    except ValueError as ex:
        assert "G4" in str(ex)


def test_score_edit_refuses_bad_target_kind():
    e = dict(_seed()["e1"]); e[":edit/target-kind"] = ":entity-speech"
    try:
        score_edit(e); assert False, "expected ValueError"
    except ValueError as ex:
        assert "G3" in str(ex)


def test_score_edit_refuses_a_smuggled_decision():
    e = dict(_seed()["e1"]); e["decision"] = "accept"
    try:
        score_edit(e); assert False, "expected ValueError"
    except ValueError as ex:
        assert "G2" in str(ex)


# ── rider + quality helpers ─────────────────────────────────────────────────────
def test_rider_hit_finds_jp_and_en_tokens():
    assert rider_hit("includes 広告") == "広告" or rider_hit("includes 広告")
    assert rider_hit("clean technical note") == ""


def test_quality_rewards_verifiable_provenance():
    base = {":edit/op": ":assert", ":edit/proposed-value": "x", ":edit/rationale": "a clear reason here",
            ":edit/provenance": "https://example.com/x"}
    bad = dict(base); bad[":edit/provenance"] = "trust me"
    assert assess_quality(base, "") > assess_quality(bad, "")


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} passed in test_triage.py")
    sys.exit(1 if failed else 0)
