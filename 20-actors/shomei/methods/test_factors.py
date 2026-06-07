"""test_factors.py — taxonomy + assurance ladder. ADR-2606072100."""
from __future__ import annotations

from _t import expect_raises, run
from factors import (
    ALLOWED_PROOFS,
    FACTOR_CLASS,
    FACTOR_KINDS,
    GOV_FACTORS,
    PUBLIC_HANDLE_FACTORS,
    assurance_level,
    factor_class,
    proof_of_personhood,
)


def test_every_kind_has_class_and_proofs():
    for k in FACTOR_KINDS:
        assert k in FACTOR_CLASS
        assert ALLOWED_PROOFS.get(k), f"{k} has no allowed proofs"


def test_class_partition():
    assert FACTOR_CLASS["wallet-evm"] == "key" == FACTOR_CLASS["wallet-btc"]
    assert FACTOR_CLASS["gov-mynumber"] == "government"
    assert FACTOR_CLASS["etz-at-oath"] == "covenant"
    assert FACTOR_CLASS["webauthn"] == "device"
    assert FACTOR_CLASS["sns-x"] == "social"


def test_gov_factors_set():
    assert GOV_FACTORS == {"gov-mynumber", "gov-passport", "gov-license"}


def test_public_handle_only_wallet_sns():
    for k in PUBLIC_HANDLE_FACTORS:
        assert k.startswith("wallet-") or k.startswith("sns-")
    assert "gov-mynumber" not in PUBLIC_HANDLE_FACTORS
    assert "etz-at-oath" not in PUBLIC_HANDLE_FACTORS


def test_factor_class_unknown_raises():
    expect_raises(lambda: factor_class("nope"), contains="unknown factorKind")


def test_ial_levels():
    assert assurance_level(set(), 0) == 0
    assert assurance_level({"key"}, 1) == 1                         # single factor
    assert assurance_level({"key", "social"}, 2) == 2              # two classes
    assert assurance_level({"key", "covenant"}, 2) == 3           # covenant-bound
    assert assurance_level({"device", "government"}, 2) == 4      # gov-verified


def test_two_key_wallets_is_one_class_not_ial2():
    # EVM + BTC both 'key' → count 2 but class-diversity 1 → still IAL1 (sybil-resistance: classes)
    assert assurance_level({"key"}, 2) == 1


def test_covenant_alone_one_factor_is_ial1():
    assert assurance_level({"covenant"}, 1) == 1


def test_proof_of_personhood():
    assert proof_of_personhood(2, 2) is True
    assert proof_of_personhood(1, 1) is False
    assert proof_of_personhood(2, 1) is False  # one class, even if level bumped, never PoP


CASES = [
    ("every_kind_has_class_and_proofs", test_every_kind_has_class_and_proofs),
    ("class_partition", test_class_partition),
    ("gov_factors_set", test_gov_factors_set),
    ("public_handle_only_wallet_sns", test_public_handle_only_wallet_sns),
    ("factor_class_unknown_raises", test_factor_class_unknown_raises),
    ("ial_levels", test_ial_levels),
    ("two_key_wallets_one_class", test_two_key_wallets_is_one_class_not_ial2),
    ("covenant_alone_ial1", test_covenant_alone_one_factor_is_ial1),
    ("proof_of_personhood", test_proof_of_personhood),
]

if __name__ == "__main__":
    run("factors", CASES)
