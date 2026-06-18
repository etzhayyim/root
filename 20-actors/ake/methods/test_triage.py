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
    QUALITY_AUTO_ACCEPT, RISKS, ROUTES, assess_quality, rider_hit, route_for, score_edit,
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


# ── route_for TOTALITY + PRIORITY — the G2 structural guarantee ──────────────────
# A pure router is only trustworthy if it is TOTAL (defined on its whole domain) and
# its priority ordering is exhaustive, not just spot-checked. These sweep the entire
# (risk × quality-grid × {clean,rider}) space so no future signal can quietly open an
# auto-accept hole or leave a (risk,quality) pair routing to an undefined value.
_QGRID = (0.0, 0.15, 0.5, QUALITY_AUTO_ACCEPT - 1e-9, QUALITY_AUTO_ACCEPT, 0.85, 1.0)


def test_route_for_is_total_and_closed_over_domain():
    # every (risk, quality, rider) combination resolves to exactly one declared ROUTE
    for risk in RISKS:
        for q in _QGRID:
            for rider in ("", "advertis", "兵器"):
                r = route_for(risk, q, rider)
                assert r in ROUTES, f"route_for({risk!r},{q},{rider!r})={r!r} not in {ROUTES}"


def test_route_rider_dominates_every_risk_and_quality():
    # a Charter-Rider §2 hit is :refused no matter the risk class or quality (G7/§2)
    for risk in RISKS:
        for q in _QGRID:
            assert route_for(risk, q, "advertis") == "refused"


def test_route_auto_accept_requires_low_risk_clean_and_high_quality():
    # the ONLY door to the optimistic fast-path: low risk + clean + quality ≥ threshold.
    # Nothing else may ever auto-accept (the inverse of the G2/G7 escalation guarantee).
    for risk in RISKS:
        for q in _QGRID:
            for rider in ("", "advertis"):
                got = route_for(risk, q, rider)
                expected_auto = (risk == "low" and not rider and q >= QUALITY_AUTO_ACCEPT)
                assert (got == "auto-accept") == expected_auto, (
                    f"auto-accept leak: route_for({risk!r},{q},{rider!r})={got!r}"
                )


def test_route_is_monotone_at_low_risk_no_demotion_as_quality_rises():
    # at low risk + clean, raising quality must never move AWAY from auto-accept
    # (vote → auto-accept is allowed; auto-accept → vote on higher quality is a bug)
    rank = {"vote": 0, "auto-accept": 1}
    prev = -1
    for q in sorted(_QGRID):
        r = route_for("low", q, "")
        assert r in rank, f"unexpected low-risk route {r!r}"
        assert rank[r] >= prev, f"non-monotone at q={q}: {r!r}"
        prev = rank[r]


def test_route_invariant_risk_never_optimistic_accepts():
    # constitutional-adjacent edits always escalate (council-lv7), never fast-path (G7)
    for q in _QGRID:
        assert route_for("invariant", q, "") == "council-lv7"


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


# ── assess_quality SCORE BREAKDOWN — pin every additive branch of the ORES analogue ──
# The score is sourcing(0/.15/.5) + rationale(0/.2) + plausibility(0/.3), clamped to 1.0.
# These lock the exact contribution of each signal so a future re-weighting cannot silently
# shift the auto-accept boundary (route_for keys off QUALITY_AUTO_ACCEPT).
_Q_BASE = {":edit/op": ":assert", ":edit/proposed-value": "x",
           ":edit/rationale": "a clear reason here", ":edit/provenance": "https://example.com/x"}


def test_quality_full_marks_verifiable_rationale_assert_value():
    assert assess_quality(_Q_BASE, "") == 1.0  # 0.5 + 0.2 + 0.3, clamped


def test_quality_nonverifiable_provenance_scores_partial_sourcing():
    # provenance PRESENT but not obviously verifiable → 0.15 (not 0.5) — the 84->86 branch
    assert assess_quality({**_Q_BASE, ":edit/provenance": "trust me"}, "") == 0.65


def test_quality_empty_provenance_scores_zero_sourcing():
    # neither verifiable nor present → +0 sourcing (assess_quality is total even though
    # score_edit refuses unsourced upstream) — the elif-False exit
    assert assess_quality({**_Q_BASE, ":edit/provenance": ""}, "") == 0.5


def test_quality_short_rationale_earns_no_clarity_credit():
    # rationale < 10 stripped chars → no +0.2 — the 87->90 branch
    assert assess_quality({**_Q_BASE, ":edit/rationale": "short"}, "") == 0.8


def test_quality_retract_and_challenge_need_no_value():
    # a retract/challenge earns the +0.3 plausibility credit with an empty value — the elif arm
    assert assess_quality({**_Q_BASE, ":edit/op": ":retract", ":edit/proposed-value": ""}, "") == 1.0
    assert assess_quality({**_Q_BASE, ":edit/op": ":challenge", ":edit/proposed-value": ""}, "") == 1.0


def test_quality_oversized_value_earns_no_plausibility_credit():
    # an assert whose value exceeds 4000 chars gets no +0.3 — the 93->95 length guard
    assert assess_quality({**_Q_BASE, ":edit/proposed-value": "z" * 4001}, "") == 0.7


def test_quality_rider_hit_zeroes_the_whole_score():
    # a Charter-Rider token short-circuits to 0.0 regardless of any other signal
    assert assess_quality(_Q_BASE, "advertis") == 0.0


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
