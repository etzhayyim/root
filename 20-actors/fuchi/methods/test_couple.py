#!/usr/bin/env python3
"""Tests for 扶持 (fuchi) couple.py — R1(d) Displacement-Dividend cohort coupling.

Standalone-runnable: python3 test_couple.py
"""
from __future__ import annotations

import sys

from couple import (
    TITHE_BPS,
    CohortEarmark,
    DisplacementEvent,
    coupling_gate,
    earmark_from_surplus,
    events_from_seed,
)


def _event(**over):
    base = dict(displacing_actor="sanae", cohort_id="cohort-sanae",
                displaced_count=12, surplus_usd_micros_yr=60_000_000_000, funded=True)
    base.update(over)
    return DisplacementEvent(**base)


# ── TitheRouter split ───────────────────────────────────────────────────────
def test_tithe_split_is_ten_percent_exact():
    e = earmark_from_surplus(_event(surplus_usd_micros_yr=60_000_000_000))
    assert e.tithe_usd_micros == 6_000_000_000
    assert e.earmark_usd_micros_yr == 54_000_000_000


def test_gross_equals_tithe_plus_earmark_always():
    for s in (1, 7, 999, 10_001, 60_000_000_000, 123_456_789):
        e = earmark_from_surplus(_event(surplus_usd_micros_yr=s))
        assert e.tithe_usd_micros + e.earmark_usd_micros_yr == s


def test_tithe_bps_is_1000():
    assert TITHE_BPS == 1000


def test_earmark_construction_rejects_inexact_split():
    try:
        CohortEarmark("c", "sanae", 100, 5, 90, True)  # 5+90 != 100
    except ValueError as e:
        assert "split" in str(e).lower()
        return
    raise AssertionError("inexact gross/tithe/earmark split must be refused")


# ── G2 coupling gate ────────────────────────────────────────────────────────
def test_funded_cohort_within_earmark_is_admissible():
    e = _event(funded=True)
    em = earmark_from_surplus(e)
    g = coupling_gate(e, em, committed_floor_usd_micros_yr=20_000_000_000)
    assert g["admissible"] is True and g["headroom"] > 0


def test_unfunded_cohort_is_refused():
    e = _event(funded=False)
    em = earmark_from_surplus(e)
    g = coupling_gate(e, em, committed_floor_usd_micros_yr=1)
    assert g["admissible"] is False and "G2" in g["reason"] and "no funded" in g["reason"]


def test_over_earmark_commitment_is_refused():
    e = _event(surplus_usd_micros_yr=10_000_000_000, funded=True)  # earmark 9_000_000_000
    em = earmark_from_surplus(e)
    g = coupling_gate(e, em, committed_floor_usd_micros_yr=20_000_000_000)
    assert g["admissible"] is False and "exceeds funded earmark" in g["reason"]


def test_committed_exactly_at_earmark_is_admissible():
    e = _event(surplus_usd_micros_yr=10_000_000_000, funded=True)  # earmark 9_000_000_000
    em = earmark_from_surplus(e)
    g = coupling_gate(e, em, committed_floor_usd_micros_yr=9_000_000_000)
    assert g["admissible"] is True and g["headroom"] == 0


def test_negative_surplus_refused():
    try:
        DisplacementEvent("sanae", "c", 1, -5)
    except ValueError:
        return
    raise AssertionError("negative surplus must be refused")


# ── seed parsing ────────────────────────────────────────────────────────────
def test_events_from_seed_reads_funded_flag():
    recs = [{":event/displacing-actor": "sanae", ":event/cohort-id": "c1",
             ":event/displaced-count": 12, ":event/surplus-usd-micros-yr": 60_000_000_000,
             ":event/funded": True},
            {":event/displacing-actor": "hataori", ":event/cohort-id": "c2",
             ":event/displaced-count": 30, ":event/surplus-usd-micros-yr": 0,
             ":event/funded": False}]
    evs = events_from_seed(recs)
    assert evs[0].funded is True and evs[1].funded is False


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"test_couple.py: {len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
