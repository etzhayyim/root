"""Tests for the Displacement Dividend allocator (ADR-2606032130).

Asserts the constitutional invariants the formula must preserve:
  - cash≡0 for every worker (N1)
  - shares over the vowed cohort sum to 1
  - longer tenure -> larger share (monotone), but the gradient is COMPRESSED (not linear)
  - hazard scales the weight
  - the in-kind floor is stage-capped and decays monotonically over the horizon
  - outreach (pre-covenant) workers get share 0 (N7 covenant gate), full floor only when vowed
"""

import math

from allocate import (
    HORIZON_YEARS,
    TENURE_CAP_YEARS,
    Allocation,
    DisplacedWorker,
    allocate,
    floor_decay,
    tenure_weight,
)


def _w(did, years, hazard=1500, prior=4_000_000_000, covenant="vowed"):
    return DisplacedWorker(did, tenure_months=int(years * 12), hazard_permille=hazard,
                           prior_imputed_usd_micros_yr=prior, covenant=covenant)


def test_cash_is_always_zero():
    cohort = [_w("a", 30), _w("b", 5), _w("c", 1)]
    for a in allocate(cohort, stage_ceiling_usd_micros_yr=5_000_000_000):
        assert a.cash_stipend_usd_micros == 0


def test_shares_sum_to_one_over_vowed():
    cohort = [_w("a", 30), _w("b", 10), _w("c", 2)]
    allocs = allocate(cohort, stage_ceiling_usd_micros_yr=5_000_000_000)
    assert math.isclose(sum(a.share for a in allocs), 1.0, rel_tol=1e-9)


def test_longer_tenure_larger_share_but_compressed():
    cohort = [_w("vet", 40), _w("new", 1)]
    allocs = {a.subject_did: a for a in allocate(cohort, 5_000_000_000)}
    assert allocs["vet"].share > allocs["new"].share          # monotone in tenure
    ratio = allocs["vet"].share / allocs["new"].share
    # linear tenure would give 40x; the ln(1+.) curve must compress well below ~6x
    assert ratio < 6.0
    assert ratio > 1.0


def test_hazard_scales_weight():
    low = _w("low", 10, hazard=1000)
    high = _w("high", 10, hazard=2000)
    # same tenure, double hazard -> double weight
    assert math.isclose(tenure_weight(high), 2.0 * tenure_weight(low), rel_tol=1e-9)


def test_tenure_capped_at_40y():
    a = tenure_weight(_w("x", 80, hazard=1000))   # 80y caps to 40y
    b = tenure_weight(_w("y", TENURE_CAP_YEARS, hazard=1000))
    assert math.isclose(a, b, rel_tol=1e-9)


def test_priority_rank_orders_by_weight():
    cohort = [_w("mid", 10), _w("vet", 35), _w("new", 1)]
    allocs = {a.subject_did: a for a in allocate(cohort, 5_000_000_000)}
    assert allocs["vet"].priority_rank == 1
    assert allocs["new"].priority_rank == 3


def test_floor_is_stage_capped():
    # prior imputed (8B) exceeds the stage ceiling (5B) -> floor capped at ceiling at t=0
    cohort = [_w("rich", 10, prior=8_000_000_000)]
    a = allocate(cohort, stage_ceiling_usd_micros_yr=5_000_000_000, elapsed_months=0)[0]
    assert a.floor_usd_micros_yr == 5_000_000_000


def test_floor_decays_monotonically_to_zero():
    cohort = [_w("w", 10, prior=4_000_000_000)]
    prev = None
    for m in range(0, int(HORIZON_YEARS * 12) + 13, 6):
        f = allocate(cohort, 5_000_000_000, elapsed_months=m)[0].floor_usd_micros_yr
        if prev is not None:
            assert f <= prev
        prev = f
    # past the horizon the floor is fully decayed (worker has ascended the Ladder)
    assert allocate(cohort, 5_000_000_000, elapsed_months=int(HORIZON_YEARS * 12) + 12)[0].floor_usd_micros_yr == 0


def test_decay_endpoints():
    assert math.isclose(floor_decay(0), 1.0)
    assert floor_decay(int(HORIZON_YEARS * 12)) == 0.0


def test_outreach_worker_gets_no_share_until_vowed():
    cohort = [_w("vowed", 10, covenant="vowed"), _w("outreach", 30, covenant="outreach")]
    allocs = {a.subject_did: a for a in allocate(cohort, 5_000_000_000)}
    assert allocs["outreach"].share == 0.0           # N7 covenant gate
    assert allocs["outreach"].floor_usd_micros_yr == 0
    assert math.isclose(allocs["vowed"].share, 1.0)  # sole vowed member holds the pool


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
