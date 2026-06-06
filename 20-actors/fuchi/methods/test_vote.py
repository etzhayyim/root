#!/usr/bin/env python3
"""Tests for 扶持 (fuchi) vote.py — R1(b) 1 SBT = 1 vote + 48h timelock.

Standalone-runnable: python3 test_vote.py
"""
from __future__ import annotations

import sys

from vote import Ballot, ballots_from_seed, cast, finalize, tally


def _ballots(spec, opened=1000):
    out = []
    t = opened + 1
    for did, choice in spec:
        out = cast(out, Ballot(did, choice, t))
        t += 2
    return out


def test_accepts_after_timelock_with_quorum():
    b = _ballots([("did:m:a", "yes"), ("did:m:b", "yes"), ("did:m:c", "yes"), ("did:m:d", "no")])
    r = tally(b, opened_at=1000, now=1060, timelock_h=48)
    assert r["finalizable"] and r["outcome"] == "accepted" and r["yes"] == 3 and r["no"] == 1


def test_pending_before_timelock():
    b = _ballots([("did:m:a", "yes"), ("did:m:b", "yes"), ("did:m:c", "yes")])
    r = tally(b, opened_at=1000, now=1010, timelock_h=48)
    assert r["finalizable"] is False and r["outcome"] == "pending"


def test_finalize_raises_before_timelock():
    b = _ballots([("did:m:a", "yes"), ("did:m:b", "yes")])
    try:
        finalize(b, opened_at=1000, now=1010, timelock_h=48)
    except ValueError as e:
        assert "timelock" in str(e)
        return
    raise AssertionError("finalize must raise before the timelock elapses")


def test_rejected_without_quorum():
    b = _ballots([("did:m:a", "yes")])
    r = tally(b, opened_at=1000, now=1060, timelock_h=48, quorum=3)
    assert r["quorum_met"] is False and r["outcome"] == "rejected"


def test_rejected_when_no_beats_yes():
    b = _ballots([("did:m:a", "yes"), ("did:m:b", "no"), ("did:m:c", "no")])
    r = tally(b, opened_at=1000, now=1060, timelock_h=48)
    assert r["outcome"] == "rejected"


def test_one_sbt_one_vote_rejects_duplicate():
    b = cast([], Ballot("did:m:a", "yes", 1001))
    try:
        cast(b, Ballot("did:m:a", "no", 1002))
    except ValueError as e:
        assert "1 SBT = 1 vote" in str(e)
        return
    raise AssertionError("a duplicate voter must be rejected (1 SBT = 1 vote)")


def test_ballot_weight_must_be_one():
    try:
        Ballot("did:m:a", "yes", 1001, weight=5)
    except ValueError as e:
        assert "1 SBT = 1 vote" in str(e)
        return
    raise AssertionError("weight != 1 must be rejected")


def test_server_voter_unrepresentable():
    try:
        Ballot("server", "yes", 1001)
    except ValueError as e:
        assert "G9" in str(e) or "G4" in str(e)
        return
    raise AssertionError("a server voter must be rejected (no-server-key)")


def test_ballot_server_key_refused():
    try:
        Ballot("did:m:a", "yes", 1001, server_held_key=True)
    except ValueError as e:
        assert "no-server-key" in str(e)
        return
    raise AssertionError("server-held-key ballot must be refused (G9)")


def test_out_of_window_ballot_not_counted():
    # a ballot cast after the window closes is ignored in the tally
    b = [Ballot("did:m:a", "yes", 1004), Ballot("did:m:b", "yes", 1004),
         Ballot("did:m:c", "yes", 1004), Ballot("did:m:d", "yes", 9999)]
    r = tally(b, opened_at=1000, now=1060, timelock_h=48)
    assert r["yes"] == 3   # the 9999 ballot is outside [1000, 1048]


def test_ballots_from_seed_dedupes():
    recs = [{":ballot/voter": "did:m:a", ":ballot/choice": ":yes", ":ballot/cast-at": 1004},
            {":ballot/voter": "did:m:b", ":ballot/choice": ":no", ":ballot/cast-at": 1006}]
    b = ballots_from_seed(recs)
    assert len(b) == 2 and b[0].choice == "yes"


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"test_vote.py: {len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
