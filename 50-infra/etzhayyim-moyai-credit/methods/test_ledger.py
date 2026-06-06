"""Tests: append-only ledger, decay, conservation, overdraw refusal, non-transferability."""

from __future__ import annotations

from _harness import approx, run_suite
from ledger import HALF_LIFE_EPOCHS, MoyaiLedger, redeemable_usd_micros


def test_mint_and_balance():
    L = MoyaiLedger()
    L.mint("did:a", 100, epoch=0, ref="att-1")
    assert approx(L.balance("did:a", 0), 100.0)


def test_burn_reduces_balance():
    L = MoyaiLedger()
    L.mint("did:a", 100, 0, "att-1")
    L.burn("did:a", 40, 0, "draw-1")
    assert approx(L.balance("did:a", 0), 60.0)


def test_overdraw_refused():
    L = MoyaiLedger()
    L.mint("did:a", 30, 0, "att-1")
    try:
        L.burn("did:a", 50, 0, "draw-1")
        raise AssertionError("overdraw should have been refused")
    except ValueError as e:
        assert "overdraw" in str(e)


def test_decay_half_life():
    L = MoyaiLedger()
    L.mint("did:a", 100, 0, "att-1")
    # after one half-life, ~half remains
    assert approx(L.balance("did:a", HALF_LIFE_EPOCHS), 50.0, tol=1e-6)
    assert approx(L.balance("did:a", 2 * HALF_LIFE_EPOCHS), 25.0, tol=1e-6)


def test_decay_makes_it_a_flow_not_a_store():
    # A whale who hoards loses it; credit cannot accumulate into a class lever (anti-class).
    L = MoyaiLedger()
    L.mint("did:whale", 1000, 0, "att-1")
    far = 10 * HALF_LIFE_EPOCHS
    assert L.balance("did:whale", far) < 1.0


def test_append_only_monotone_epoch():
    L = MoyaiLedger()
    L.mint("did:a", 10, 5, "att-1")
    try:
        L.mint("did:a", 10, 3, "att-2")  # epoch goes backwards
        raise AssertionError("non-monotone epoch should be refused")
    except ValueError as e:
        assert "append-only" in str(e)


def test_conservation():
    L = MoyaiLedger()
    L.mint("did:a", 100, 0, "att-1")
    L.burn("did:a", 100, 0, "draw-1")
    L.assert_conservation()  # burned == minted, ok
    assert L.total_minted() == 100 and L.total_burned() == 100


def test_no_transfer_operation_exists():
    # Structural non-transferability: the ledger has mint + burn and NOTHING that moves
    # credit between identities. A sybil farm cannot recombine splits because the verb
    # does not exist.
    L = MoyaiLedger()
    for verb in ("transfer", "gift", "merge", "pool", "send", "assign"):
        assert not hasattr(L, verb), f"non-transferable invariant: {verb} must not exist"


def test_non_monetary():
    L = MoyaiLedger()
    e = L.mint("did:a", 100, 0, "att-1")
    assert redeemable_usd_micros(e) == 0
    # no monetary attribute anywhere on the entry
    for bad in ("usd", "amount", "price", "usd_micros", "value_usd"):
        assert not hasattr(e, bad)


def test_per_identity_isolation():
    L = MoyaiLedger()
    L.mint("did:a", 100, 0, "att-1")
    L.mint("did:b", 50, 0, "att-2")
    assert approx(L.balance("did:a", 0), 100.0)
    assert approx(L.balance("did:b", 0), 50.0)


run_suite("test_ledger", [
    ("mint_and_balance", test_mint_and_balance),
    ("burn_reduces_balance", test_burn_reduces_balance),
    ("overdraw_refused", test_overdraw_refused),
    ("decay_half_life", test_decay_half_life),
    ("decay_flow_not_store", test_decay_makes_it_a_flow_not_a_store),
    ("append_only_monotone_epoch", test_append_only_monotone_epoch),
    ("conservation", test_conservation),
    ("no_transfer_operation_exists", test_no_transfer_operation_exists),
    ("non_monetary", test_non_monetary),
    ("per_identity_isolation", test_per_identity_isolation),
])
