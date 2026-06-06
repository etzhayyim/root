#!/usr/bin/env python3
"""Conformance tests for the corp-registry module (matsurigoto 政, ADR-2606052300).

The LEI tests exercise the real ISO 7064 MOD 97-10 checksum: an assembled LEI validates (mod
97 == 1, proven algebraically), and flipping any character breaks it. Standalone + pytest.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import corp_registry as R  # noqa: E402


def test_no_server_authority_certificate_unsigned():
    """G1 — certificate unsigned, module signs nothing."""
    assert R.SERVER_HELD_AUTHORITY is False
    r = R.register_incorporation("Co", ["o"], 0, "art", "addr", "JPN", 1)
    assert r["certificate"]["proof"] is None
    assert r["certificate"]["server_held_authority"] is False


def test_to_digits_iso7064_mapping():
    """A=10 … Z=35; digits pass through."""
    assert R._to_digits("0A9Z") == "0" + "10" + "9" + "35"


def test_lei_roundtrip_validates():
    """An assembled LEI (check digits computed) must satisfy mod 97 == 1."""
    lei = R.assign_lei("EZHY", "000000000001")
    assert len(lei) == 20
    assert R.validate_lei(lei) is True


def test_lei_check_digits_make_mod97_one_for_many_entities():
    """Property holds for many distinct entity ids (exercises the MOD-97-10 arithmetic)."""
    for n in range(1, 50):
        lei = R.assign_lei("EZHY", f"{n:012d}")
        assert R.validate_lei(lei), lei


def test_lei_corruption_detected():
    """Flipping a character breaks the checksum (the test that proves digit-dependence)."""
    lei = R.assign_lei("EZHY", "000000000042")
    assert R.validate_lei(lei)
    # mutate one char in the entity-id region
    bad = list(lei)
    bad[8] = "Z" if bad[8] != "Z" else "Y"
    assert R.validate_lei("".join(bad)) is False


def test_lei_rejects_bad_length_and_chars():
    assert R.validate_lei("TOOSHORT") is False
    assert R.validate_lei("EZHY00000000000001*9") is False  # '*' illegal
    assert R.validate_lei(12345) is False


def test_check_digits_two_chars_zero_padded():
    cd = R.compute_lei_check_digits("EZHY00" + "000000000007")
    assert len(cd) == 2 and cd.isdigit()


def test_incorporation_assigns_registry_number_and_lei():
    r = R.register_incorporation("Tree of Life K.K.", ["officer:rin"], 10_000_000,
                                 "articles", "東京都", "JPN", 7)
    assert r["registry_number"] == "JPN-00000007"
    assert R.validate_lei(r["lei"])
    assert r["record"]["immutable"] is True


def test_incorporation_validation_rules():
    bad_args = [
        ("", ["o"], 0, "a", "ad"),       # no name
        ("Co", [], 0, "a", "ad"),        # no officer
        ("Co", ["o"], -1, "a", "ad"),    # negative capital
        ("Co", ["o"], 0, "", "ad"),      # no articles
        ("Co", ["o"], 0, "a", ""),       # no address
    ]
    for args in bad_args:
        try:
            R.register_incorporation(*args, "JPN", 1)
        except ValueError:
            continue
        raise AssertionError(f"should reject {args}")


def test_change_is_append_only_g5():
    hist = []
    inc = R.register_incorporation("Co", ["o"], 0, "a", "ad", "JPN", 1)
    hist = R.append(hist, inc)
    chg = R.register_change(inc["registry_number"], {"address": "new"}, "2026-06-05")
    hist2 = R.append(hist, chg)
    assert len(hist) == 1 and len(hist2) == 2          # original untouched, new list
    assert hist2[0]["kind"] == "incorporation"          # incorporation record preserved
    assert hist2[1]["kind"] == "change"                 # amendment appended


def test_solve_is_gated_at_r0():
    try:
        R.solve()
    except RuntimeError:
        return
    raise AssertionError("solve() must raise at R0")


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
