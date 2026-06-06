#!/usr/bin/env python3
"""Tests for 扶持 (fuchi) book.py — R1(c) toritate booking + kanae flow viz.

Standalone-runnable: python3 test_book.py
"""
from __future__ import annotations

import sys

from book import (
    FUCHI,
    PUBLIC_FUND,
    RAIL_TO_CATEGORY,
    LedgerEntry,
    book_toritate,
    flow_graph,
)
from provision import provision
from route import route_envelope


def _env(line, imputed):
    return {":envelope/line": ":" + line, ":envelope/imputed-usd-micros-yr": imputed,
            ":envelope/cash-usd-micros": 0}


def _rails(*pairs):
    return route_envelope([_env(l, v) for l, v in pairs])


# ── toritate booking ────────────────────────────────────────────────────────
def test_categories_map_to_toritate_enum():
    rails = _rails(("housing", 1), ("food", 1), ("energy", 1),
                   ("compute", 1), ("tooling", 1), ("care", 1))
    cats = {e.category for e in book_toritate(rails, "a", "did:m:x")}
    assert cats == {"subsistence-flow", "vocation-flow", "care-flow"}


def test_liquidity_is_not_booked_as_income():
    rails = _rails(("food", 5), ("liquidity", 5))
    entries = book_toritate(rails, "a", "did:m:x")
    assert len(entries) == 1 and entries[0].category == "subsistence-flow"


def test_every_ledger_entry_is_cashless():
    rails = _rails(("food", 4), ("care", 1))
    for e in book_toritate(rails, "a", "did:m:x"):
        assert e.cash_usd_micros == 0


def test_payroll_category_is_unrepresentable():
    for bad in ("payroll", "salary", "wage", "bonus"):
        try:
            LedgerEntry("a", bad, 1, "did:m:x")
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} category must be refused")


def test_nonzero_cash_ledger_refused():
    try:
        LedgerEntry("a", "subsistence-flow", 1, "did:m:x", cash_usd_micros=5)
    except ValueError as e:
        assert "cash" in str(e).lower()
        return
    raise AssertionError("nonzero cash ledger entry must be refused")


# ── kanae flow graph ────────────────────────────────────────────────────────
def test_flow_graph_has_publicfund_source():
    rails = _rails(("food", 4), ("energy", 1))
    edges = flow_graph(rails, "a", "did:m:x")
    src = [e for e in edges if e.flow_class == "publicfund-to-fuchi"]
    assert len(src) == 1 and src[0].frm == PUBLIC_FUND and src[0].to == FUCHI
    assert src[0].imputed_usd_micros_yr == 5   # sum of in-kind


def test_flow_legs_chain_to_maintainer():
    rails = _rails(("food", 4))
    edges = flow_graph(rails, "a", "did:m:x")
    classes = [e.flow_class for e in edges]
    assert "fuchi-to-provider" in classes and "provider-to-maintainer" in classes


def test_liquidity_leg_is_not_in_kind_and_not_funded():
    rails = _rails(("liquidity", 14))
    edges = flow_graph(rails, "a", "did:m:x")
    # no public-fund source (liquidity is a member loan, not funded here)
    assert not any(e.flow_class == "publicfund-to-fuchi" for e in edges)
    legs = [e for e in edges if e.flow_class != "publicfund-to-fuchi"]
    assert legs and all(e.in_kind is False for e in legs)


def test_provision_rails_compose_with_booking():
    # the route → provision → book chain is consistent
    rails = _rails(("food", 4), ("compute", 2))
    intents = provision(rails, "a")
    entries = book_toritate(rails, "a", "did:m:x")
    assert len(intents) == 2 and len(entries) == 2


def test_rail_to_category_excludes_liquidity():
    assert "liquidity-warifu" not in RAIL_TO_CATEGORY


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"test_book.py: {len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
