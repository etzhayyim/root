#!/usr/bin/env python3
"""Tests for 扶持 (fuchi) allocate.py — tenure-weighted in-kind sustenance, cash≡0.

Standalone-runnable: python3 test_allocate.py
"""
from __future__ import annotations

import sys

from allocate import (
    ALLOWED_INSTRUMENTS,
    Allocation,
    Maintainer,
    allocate,
    assert_instrument,
    floor_decay,
    tenure_weight,
)


def _cohort():
    return [
        Maintainer("did:m:abel", tenure_months=96, hazard_permille=1800,
                   maintains=("sanae",), prior_imputed_usd_micros_yr=9_000_000_000),
        Maintainer("did:m:seth", tenure_months=36, hazard_permille=1400,
                   prior_imputed_usd_micros_yr=28_000_000_000),
        Maintainer("did:m:noah", tenure_months=2, hazard_permille=1000,
                   prior_imputed_usd_micros_yr=6_000_000_000, covenant="outreach"),
    ]


def test_shares_sum_to_one_over_vowed():
    allocs = allocate(_cohort(), stage_ceiling_usd_micros_yr=30_000_000_000)
    vowed = [a for a in allocs if a.share > 0]
    assert abs(sum(a.share for a in vowed) - 1.0) < 1e-9


def test_cash_is_zero_for_every_allocation():
    for a in allocate(_cohort(), 30_000_000_000):
        assert a.cash_usd_micros == 0


def test_no_server_held_key():
    for a in allocate(_cohort(), 30_000_000_000):
        assert a.server_held_key is False


def test_tenure_weight_is_log_compressed():
    # 40y veteran is ~2x a 5y worker at equal hazard, not 8x (log curve).
    vet = Maintainer("v", tenure_months=480, hazard_permille=1000)
    jr = Maintainer("j", tenure_months=60, hazard_permille=1000)
    ratio = tenure_weight(vet) / tenure_weight(jr)
    assert 1.8 < ratio < 2.3, ratio


def test_hazard_amplifies_weight():
    safe = Maintainer("s", tenure_months=60, hazard_permille=1000)
    risky = Maintainer("r", tenure_months=60, hazard_permille=2000)
    assert abs(tenure_weight(risky) - 2 * tenure_weight(safe)) < 1e-9


def test_priority_rank_orders_by_weight():
    allocs = {a.maintainer_did: a for a in allocate(_cohort(), 30_000_000_000)}
    # abel (8y, hazard 1.8) outranks seth (3y, hazard 1.4)
    assert allocs["did:m:abel"].priority_rank < allocs["did:m:seth"].priority_rank


def test_outreach_gets_zero_share_but_a_floor():
    allocs = {a.maintainer_did: a for a in allocate(_cohort(), 30_000_000_000)}
    noah = allocs["did:m:noah"]
    assert noah.share == 0.0 and noah.floor_usd_micros_yr > 0


def test_floor_decays_over_five_years():
    assert floor_decay(0) == 1.0
    assert abs(floor_decay(30) - 0.5) < 1e-9     # 2.5y
    assert floor_decay(60) == 0.0                # 5y
    assert floor_decay(120) == 0.0               # clamped


def test_floor_is_stage_capped():
    # seth's prior imputed (28k) exceeds a 20k ceiling → capped at 20k.
    allocs = {a.maintainer_did: a for a in allocate(_cohort(), 20_000_000_000)}
    assert allocs["did:m:seth"].floor_usd_micros_yr == 20_000_000_000


# ── G1: no investment vehicle ───────────────────────────────────────────────
def test_assert_instrument_accepts_sustenance_set():
    for i in ALLOWED_INSTRUMENTS:
        assert assert_instrument(i) == i


def test_equity_instrument_is_unrepresentable():
    for bad in ("equity", ":equity", "debt", "revenue-share", "carry", "dividend", "exit"):
        try:
            assert_instrument(bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} must be rejected (G1)")


def test_allocate_refuses_investment_instrument():
    try:
        allocate(_cohort(), 30_000_000_000, instrument="equity")
    except ValueError as e:
        assert "G1" in str(e)
        return
    raise AssertionError("allocate must refuse an investment instrument")


def test_allocation_construction_refuses_cash():
    try:
        Allocation("d", "sustenance", 1.0, 1.0, 1, 1000, cash_usd_micros=5)
    except ValueError as e:
        assert "cash" in str(e).lower()
        return
    raise AssertionError("Allocation must refuse nonzero cash")


def test_allocation_construction_refuses_server_key():
    try:
        Allocation("d", "sustenance", 1.0, 1.0, 1, 1000, server_held_key=True)
    except ValueError as e:
        assert "no-server-key" in str(e)
        return
    raise AssertionError("Allocation must refuse server-held-key")


# ── G5: payoff attribution ──────────────────────────────────────────────────
def test_maintainer_cannot_own_payoff():
    cohort = _cohort() + [Maintainer("did:m:x", 12, 1000, owns_payoff=True)]
    try:
        allocate(cohort, 30_000_000_000)
    except ValueError as e:
        assert "G5" in str(e)
        return
    raise AssertionError("a maintainer owning the payoff must be refused (G5)")


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"test_allocate.py: {len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
