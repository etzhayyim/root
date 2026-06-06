#!/usr/bin/env python3
"""Conformance tests for the tax-assess module (matsurigoto 政, ADR-2606052300).

The income-tax assertions reproduce the published JP 速算表 (quick-calc table) EXACTLY —
that is the conformance anchor proving the engine computes real progressive tax, not a toy.
JP quick formula: liability = taxable × marginal_rate − deduction_constant.

Standalone-runnable AND pytest-compatible.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import tax_assess as T  # noqa: E402


def test_no_server_authority():
    """G1 — the module holds no signing authority and signs nothing."""
    assert T.SERVER_HELD_AUTHORITY is False
    r = T.assess_from_return(5_000_000, 0, "JPN.income")
    assert r["receipt"]["proof"] is None
    assert r["receipt"]["server_held_authority"] is False


def test_jp_quick_table_5m():
    """taxable 5,000,000 → 5,000,000×0.20 − 427,500 = 572,500 (JP 速算表)."""
    r = T.assess_income_tax(5_000_000, T.RATE_TABLES["JPN.income"]["brackets"])
    assert r["liability"] == 572_500.0


def test_jp_quick_table_3m():
    """taxable 3,000,000 → 3,000,000×0.10 − 97,500 = 202,500."""
    r = T.assess_income_tax(3_000_000, T.RATE_TABLES["JPN.income"]["brackets"])
    assert r["liability"] == 202_500.0


def test_jp_quick_table_20m():
    """taxable 20,000,000 → 20,000,000×0.40 − 2,796,000 = 5,204,000."""
    r = T.assess_income_tax(20_000_000, T.RATE_TABLES["JPN.income"]["brackets"])
    assert r["liability"] == 5_204_000.0


def test_jp_top_bracket_50m():
    """taxable 50,000,000 → 50,000,000×0.45 − 4,796,000 = 17,704,000 (top 45% bracket)."""
    r = T.assess_income_tax(50_000_000, T.RATE_TABLES["JPN.income"]["brackets"])
    assert r["liability"] == 17_704_000.0


def test_zero_income_zero_tax():
    r = T.assess_income_tax(0, T.RATE_TABLES["JPN.income"]["brackets"])
    assert r["liability"] == 0.0
    assert r["effective_rate"] == 0.0


def test_negative_income_raises():
    try:
        T.assess_income_tax(-1, T.RATE_TABLES["JPN.income"]["brackets"])
    except ValueError:
        return
    raise AssertionError("negative income must raise")


def test_flat_rate_localization():
    """Localization generality: a flat-20% table gives 20% of taxable."""
    r = T.assess_income_tax(1_000_000, T.RATE_TABLES["FLAT20.income"]["brackets"])
    assert r["liability"] == 200_000.0
    assert r["effective_rate"] == 0.20


def test_deductions_reduce_taxable():
    r = T.assess_from_return(gross_income=6_000_000, deductions=1_000_000, table_key="JPN.income")
    assert r["taxable_income"] == 5_000_000
    assert r["liability"] == 572_500.0
    assert r["currency"] == "JPY"


def test_deductions_floor_at_zero():
    r = T.assess_from_return(gross_income=500_000, deductions=900_000, table_key="JPN.income")
    assert r["taxable_income"] == 0.0
    assert r["liability"] == 0.0


def test_unknown_table_raises():
    try:
        T.assess_from_return(1, 0, "NOPE.income")
    except ValueError:
        return
    raise AssertionError("unknown table must raise")


def test_vat_net_due_and_refund():
    due = T.assess_vat(output_vat=300_000, input_vat=120_000, currency="JPY")
    assert due["net_vat_due"] == 180_000.0
    assert due["refund_due"] == 0.0
    refund = T.assess_vat(output_vat=100_000, input_vat=160_000, currency="JPY")
    assert refund["net_vat_due"] == 0.0
    assert refund["refund_due"] == 60_000.0


def test_effective_rate_is_below_top_marginal():
    """Progressive: effective rate < top marginal rate (sanity on the bracket walk)."""
    r = T.assess_income_tax(20_000_000, T.RATE_TABLES["JPN.income"]["brackets"])
    assert r["effective_rate"] < 0.40


def test_solve_is_gated_at_r0():
    try:
        T.solve()
    except RuntimeError:
        return
    raise AssertionError("solve() must raise at R0 (live filing is gated)")


def test_r1d_rate_tables_loaded_for_each_country():
    """R1.D: per-jurisdiction tables load from data/rates/*.edn."""
    for key in ("JPN.income", "USA.income", "DEU.income", "GBR.income", "KOR.income", "IND.income"):
        assert key in T.RATE_TABLES, key
        assert T.RATE_TABLES[key]["brackets"], key


def test_usa_lowest_bracket_10pct():
    r = T.assess_from_return(10_000, 0, "USA.income")
    assert r["liability"] == 1_000.0           # 10% of 10,000
    assert r["currency"] == "USD"


def test_gbr_personal_allowance_zero_tax():
    r = T.assess_from_return(10_000, 0, "GBR.income")
    assert r["liability"] == 0.0               # below the £12,570 allowance
    assert r["currency"] == "GBP"


def test_ind_new_regime_below_threshold_zero():
    r = T.assess_from_return(250_000, 0, "IND.income")
    assert r["liability"] == 0.0               # below ₹300,000


def test_kor_currency_and_progression():
    r = T.assess_from_return(20_000_000, 0, "KOR.income")
    assert r["currency"] == "KRW"
    assert r["effective_rate"] < 0.15          # progressive, below 2nd marginal


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
