"""Tests: the BHI firewall — free subsistence floor, idle-free surplus, contention reciprocity."""

from __future__ import annotations

from _harness import run_suite
from fair_share import (CONTENTION_THRESHOLD, SUBSISTENCE_FLOOR_UNITS, Decision,
                        affects_basic_high_income, evaluate_draw)


def test_within_floor_always_free_even_with_zero_credit():
    v = evaluate_draw(requested_units=SUBSISTENCE_FLOOR_UNITS, floor_used_this_period=0,
                      mesh_load=0.99, credit_balance=0.0)
    assert v.decision is Decision.FREE_SUBSISTENCE and v.credit_to_burn == 0
    assert v.essential_guaranteed


def test_floor_identical_regardless_of_credit():
    # The BHI-isolation invariant: a credit-rich whale and a zero-credit member get the
    # SAME essential floor. Credit does not touch Basic High Income.
    poor = evaluate_draw(requested_units=80, floor_used_this_period=0, mesh_load=0.99,
                         credit_balance=0.0)
    rich = evaluate_draw(requested_units=80, floor_used_this_period=0, mesh_load=0.99,
                         credit_balance=10_000.0)
    assert poor.decision is rich.decision is Decision.FREE_SUBSISTENCE


def test_surplus_free_when_mesh_idle():
    v = evaluate_draw(requested_units=300, floor_used_this_period=0,
                      mesh_load=CONTENTION_THRESHOLD - 0.01, credit_balance=0.0)
    assert v.decision is Decision.FREE_IDLE and v.credit_to_burn == 0


def test_surplus_under_contention_charges_credit():
    v = evaluate_draw(requested_units=SUBSISTENCE_FLOOR_UNITS + 50, floor_used_this_period=0,
                      mesh_load=0.95, credit_balance=200.0)
    assert v.decision is Decision.CHARGE_SURPLUS
    assert v.credit_to_burn == 50  # only the overage above the floor is charged


def test_surplus_under_contention_without_credit_deferred_not_denied():
    v = evaluate_draw(requested_units=SUBSISTENCE_FLOOR_UNITS + 50, floor_used_this_period=0,
                      mesh_load=0.95, credit_balance=0.0)
    assert v.decision is Decision.DEFERRED_NO_CREDIT
    # essential floor was still guaranteed — only non-essential surplus waits
    assert v.essential_guaranteed and v.credit_to_burn == 0


def test_floor_portion_always_served_before_surplus_charge():
    # request spans floor + surplus; floor part free, only overage charged
    v = evaluate_draw(requested_units=SUBSISTENCE_FLOOR_UNITS + 30, floor_used_this_period=0,
                      mesh_load=0.95, credit_balance=100.0)
    assert v.credit_to_burn == 30


def test_partial_floor_remaining():
    # member already used 90 of 100 floor; requests 40 under contention with no credit:
    # 10 fits the remaining floor (free), 30 surplus is deferred.
    v = evaluate_draw(requested_units=40, floor_used_this_period=90, mesh_load=0.95,
                      credit_balance=0.0)
    assert v.decision is Decision.DEFERRED_NO_CREDIT and v.essential_guaranteed


def test_affects_bhi_is_constant_false():
    assert affects_basic_high_income() is False


def test_zero_request_refused():
    try:
        evaluate_draw(requested_units=0, floor_used_this_period=0, mesh_load=0.5,
                      credit_balance=0.0)
        raise AssertionError("zero request should be refused")
    except ValueError:
        pass


run_suite("test_fair_share", [
    ("within_floor_always_free", test_within_floor_always_free_even_with_zero_credit),
    ("floor_identical_regardless_of_credit", test_floor_identical_regardless_of_credit),
    ("surplus_free_when_idle", test_surplus_free_when_mesh_idle),
    ("surplus_contention_charges", test_surplus_under_contention_charges_credit),
    ("surplus_no_credit_deferred", test_surplus_under_contention_without_credit_deferred_not_denied),
    ("floor_before_surplus_charge", test_floor_portion_always_served_before_surplus_charge),
    ("partial_floor_remaining", test_partial_floor_remaining),
    ("affects_bhi_false", test_affects_bhi_is_constant_false),
    ("zero_request_refused", test_zero_request_refused),
])
