#!/usr/bin/env python3
"""Tests for 扶持 (fuchi) route.py — in-kind rail decomposition + governance gate.

Standalone-runnable: python3 test_route.py
"""
from __future__ import annotations

import sys

from route import (
    LINE_TO_RAIL,
    OPTIMISTIC_CEILING_USD_MICROS_YR,
    gov_route,
    in_kind_coverage,
    rider_hit,
    route_envelope,
    touches_invariant,
)


def _env(line, imputed, cash=0):
    return {":envelope/line": ":" + line, ":envelope/imputed-usd-micros-yr": imputed,
            ":envelope/cash-usd-micros": cash}


# ── route_envelope ──────────────────────────────────────────────────────────
def test_each_line_maps_to_its_producing_actor():
    rails = route_envelope([_env(l, 1_000_000) for l in
                            ("housing", "food", "energy", "compute", "tooling", "care", "liquidity")])
    kinds = {r.kind for r in rails}
    assert kinds == set(k for k, _ in LINE_TO_RAIL.values())
    providers = {r.provider_actor for r in rails}
    assert {"commons-land", "mitsuho", "hikari", "murakumo", "okaimono", "iyashi", "warifu"} == providers


def test_liquidity_is_member_principal_only():
    rails = route_envelope([_env("food", 1), _env("liquidity", 1)])
    by_kind = {r.kind: r for r in rails}
    assert by_kind["food-mitsuho"].member_principal is False
    assert by_kind["liquidity-warifu"].member_principal is True


def test_cash_line_is_unrepresentable():
    for bad in ("cash", "stipend", "cash-disbursement"):
        try:
            route_envelope([_env(bad, 1)])
        except ValueError as e:
            assert "cash≡0" in str(e)
            continue
        raise AssertionError(f"{bad!r} line must be refused (cash≡0)")


def test_nonzero_cash_field_is_refused():
    try:
        route_envelope([_env("food", 1, cash=5)])
    except ValueError as e:
        assert "cash≡0" in str(e)
        return
    raise AssertionError("nonzero :envelope/cash-usd-micros must be refused")


def test_unknown_line_has_no_rail():
    try:
        route_envelope([_env("yacht", 1)])
    except ValueError as e:
        assert "G3" in str(e)
        return
    raise AssertionError("an unknown line must have no rail (G3)")


# ── in_kind_coverage ────────────────────────────────────────────────────────
def test_fully_in_kind_is_100pct():
    rails = route_envelope([_env("food", 4), _env("energy", 1)])
    assert in_kind_coverage(rails) == 1.0


def test_liquidity_lowers_coverage():
    rails = route_envelope([_env("food", 5), _env("liquidity", 5)])
    assert in_kind_coverage(rails) == 0.5


# ── gov_route (G7 pure function) ────────────────────────────────────────────
def test_low_imputed_in_kind_auto_accepts():
    assert gov_route(1_000_000_000, invariant_touch=False, rider="") == "auto"


def test_above_ceiling_goes_to_vote():
    assert gov_route(OPTIMISTIC_CEILING_USD_MICROS_YR + 1, False, "") == "sbt-vote"


def test_invariant_touch_goes_to_council():
    assert gov_route(1, invariant_touch=True, rider="") == "council-lv7"


def test_rider_hit_is_refused_over_everything():
    # a rider hit beats both ceiling and invariant-touch → always refused
    assert gov_route(10 ** 18, invariant_touch=True, rider="affiliate") == "refused"


def test_rider_hit_detection():
    assert rider_hit("requests an affiliate ad-revenue share")
    assert rider_hit("広告 revenue")
    assert not rider_hit("maintains the sanae weeder")


def test_invariant_touch_detection():
    assert touches_invariant("new commons-land grant for housing")
    assert not touches_invariant("food and energy sustenance")


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"test_route.py: {len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
