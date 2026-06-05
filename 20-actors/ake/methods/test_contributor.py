#!/usr/bin/env python3
"""Tests for contributor.py — anti-vandalism rate + recoverable Wellbecoming trajectory (G9)."""
from __future__ import annotations

import contributor as contrib


def test_record_is_append_only_and_non_mutating():
    t0 = contrib.empty()
    t1 = contrib.record(t0, "did:m:a", "accepted", 100)
    assert t0 == {} and contrib.counts(t1, "did:m:a") == {"accepted": 1, "refused": 0}
    t2 = contrib.record(t1, "did:m:a", "refused", 200)
    assert contrib.counts(t1, "did:m:a")["refused"] == 0     # t1 untouched
    assert contrib.counts(t2, "did:m:a") == {"accepted": 1, "refused": 1}


def test_record_rejects_bad_outcome():
    try:
        contrib.record(contrib.empty(), "did:m:a", "maybe", 1)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_acceptance_rate():
    t = contrib.empty()
    assert contrib.acceptance_rate(t, "did:m:a") is None        # no events
    for o in ("accepted", "accepted", "refused"):
        t = contrib.record(t, "did:m:a", o, 1)
    assert contrib.acceptance_rate(t, "did:m:a") == round(2 / 3, 4)


def test_rate_limit_blocks_a_flood():
    t = contrib.empty()
    for i in range(contrib.RATE_MAX_IN_WINDOW):
        t = contrib.record(t, "did:m:flood", "accepted", 1000 + i)
    # the ceiling is reached within the window → next is blocked
    assert not contrib.rate_ok(t, "did:m:flood", now=1000 + contrib.RATE_MAX_IN_WINDOW)
    # but far in the future the window has slid past → allowed again
    assert contrib.rate_ok(t, "did:m:flood", now=1000 + contrib.RATE_WINDOW + 10_000)


def test_throttle_only_on_an_unbroken_refusal_run():
    t = contrib.empty()
    for i in range(contrib.THROTTLE_REFUSED_RUN):
        t = contrib.record(t, "did:m:vandal", "refused", 100 + i)
    assert contrib.is_throttled(t, "did:m:vandal")


def test_throttle_is_recoverable():
    # a run of refusals throttles…
    t = contrib.empty()
    for i in range(contrib.THROTTLE_REFUSED_RUN):
        t = contrib.record(t, "did:m:x", "refused", 100 + i)
    assert contrib.is_throttled(t, "did:m:x")
    # …but a single subsequent accepted edit breaks the run → un-throttled (no score-of-soul)
    t = contrib.record(t, "did:m:x", "accepted", 999)
    assert not contrib.is_throttled(t, "did:m:x")


def test_new_contributor_is_never_throttled():
    t = contrib.record(contrib.empty(), "did:m:new", "refused", 1)
    assert not contrib.is_throttled(t, "did:m:new")    # too few events to judge


def test_trajectory_view_shape():
    t = contrib.record(contrib.empty(), "did:m:a", "accepted", 1)
    v = contrib.trajectory(t, "did:m:a")
    assert v["did"] == "did:m:a" and v["accepted"] == 1 and v["throttled"] is False
    assert "acceptanceRate" in v and "events" in v


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
    print(f"{len(fns) - failed}/{len(fns)} passed in test_contributor.py")
    sys.exit(1 if failed else 0)
