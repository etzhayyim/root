#!/usr/bin/env python3
"""matsurigoto 政 — `tax-assess` module (R0 reference implementation).

ADR-2606052300. The FIRST executable vertical slice of the COFOG e-gov standard: a
PURE-FUNCTION tax-assessment engine for the services `tax.income.file` /
`tax.corporate.file` / `tax.vat.file`.

WHAT IT IS: a deterministic, spec-derived reference assessment. Income/corporate tax is a
progressive marginal-bracket computation; VAT is output−input. The *bracket table* is the
localized jurisdiction parameter (G2 spec-derived; per-country rates documented + sourced),
so one universal algorithm serves every polity.

WHAT IT IS NOT (honest R0): NOT a certified tax engine, NOT wired to any live government
record. It computes a liability from a return-shaped input and returns a structured
assessment + an unsigned filing-receipt skeleton. There is NO key here and NO live filing —

  G1 no-operator-master-key : SERVER_HELD_AUTHORITY is False and the module SIGNS NOTHING; a
                              filing receipt is returned UNSIGNED for the governing authority
                              (Council / adopting state) to sign with ITS OWN key.
  G2 spec-derived-only      : the algorithm follows public tax law (progressive marginal
                              brackets; OECD SAF-T-shaped aggregates); rate tables cite source.
  G3 authority-bearing      : the caller passes :operated-by; this module never asserts it.

Conformance is checked against the published JP 速算表 (quick-calc table) — the reference
liabilities are reproduced exactly (see test_tax_assess.py).

stdlib only, no I/O, no network. Importable as a kotoba-wasm module contract.
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass

# G1: this module holds NO signing authority. It computes; the governing organ signs.
SERVER_HELD_AUTHORITY = False

# ── Reference marginal-bracket rate tables (the localized G2 parameter) ──
# Each table: ascending list of (lower_bound_inclusive, marginal_rate). The last bracket
# extends to +∞. These are :representative reference figures anchored to public tax law;
# a live deployment supplies the authoritative current table (data/rates/<iso3>.edn, later).
RATE_TABLES: dict[str, dict] = {
    # Japan national income tax (所得税) — 7 brackets. Source: 所得税法 別表 / 国税庁 速算表.
    "JPN.income": {
        "currency": "JPY",
        "source": "所得税法 / 国税庁 速算表 (:representative)",
        "brackets": [
            [0, 0.05],
            [1_950_000, 0.10],
            [3_300_000, 0.20],
            [6_950_000, 0.23],
            [9_000_000, 0.33],
            [18_000_000, 0.40],
            [40_000_000, 0.45],
        ],
    },
    # A flat-rate reference (e.g. a 20% schedular regime) — proves localization generality.
    "FLAT20.income": {
        "currency": "XXX",
        "source": "illustrative flat 20% (:representative)",
        "brackets": [[0, 0.20]],
    },
}


def load_rate_tables(directory: pathlib.Path | None = None) -> int:
    """R1.D: merge per-jurisdiction rate tables from data/rates/*.edn into RATE_TABLES.

    Each file is a map "<KEY>" → {:currency :source :brackets [[lower rate] ...]}. Keeps the
    universal algorithm; the bracket table is the localized (G2 spec-derived) parameter. Returns
    the number of tables loaded. Robust: a missing dir / parse error leaves the embedded tables.
    """
    directory = directory or (pathlib.Path(__file__).resolve().parent.parent.parent / "data" / "rates")
    if not directory.exists():
        return 0
    methods_dir = str(pathlib.Path(__file__).resolve().parent.parent)
    if methods_dir not in sys.path:
        sys.path.insert(0, methods_dir)
    from _edn import load_edn  # the shared minimal EDN reader
    n = 0
    for f in sorted(directory.glob("*.edn")):
        try:
            doc = load_edn(f)
        except Exception:
            continue
        for key, tbl in (doc or {}).items():
            RATE_TABLES[key] = {
                "currency": tbl.get(":currency", "XXX"),
                "source": tbl.get(":source", ""),
                "brackets": [[b[0], b[1]] for b in tbl[":brackets"]],
            }
            n += 1
    return n


@dataclass(frozen=True)
class BracketLine:
    lower: int
    upper: float  # +inf for the top bracket
    rate: float
    taxable_in_bracket: float
    tax_in_bracket: float


def assess_income_tax(taxable_income: float, brackets: list) -> dict:
    """Progressive marginal-bracket assessment. Pure function.

    `brackets` = ascending [(lower_inclusive, marginal_rate), ...]; the top bracket → +∞.
    Returns the per-bracket breakdown, total liability, and effective rate.
    """
    if taxable_income < 0:
        raise ValueError("taxable_income must be >= 0")
    if not brackets:
        raise ValueError("brackets must be non-empty")

    lines: list[BracketLine] = []
    total = 0.0
    for i, (lower, rate) in enumerate(brackets):
        upper = brackets[i + 1][0] if i + 1 < len(brackets) else float("inf")
        if taxable_income > lower:
            amount = min(taxable_income, upper) - lower
            tax = amount * rate
            total += tax
            lines.append(BracketLine(lower, upper, rate, amount, tax))

    return {
        "taxable_income": taxable_income,
        "liability": round(total, 2),
        "effective_rate": round(total / taxable_income, 6) if taxable_income else 0.0,
        "brackets": [
            {"lower": ln.lower, "upper": ln.upper, "rate": ln.rate,
             "taxable_in_bracket": ln.taxable_in_bracket, "tax_in_bracket": round(ln.tax_in_bracket, 2)}
            for ln in lines
        ],
    }


def assess_from_return(gross_income: float, deductions: float, table_key: str) -> dict:
    """Assess income tax from a return-shaped input (gross − deductions → taxable).

    `gross_income` / `deductions` map to the aggregated income/deduction totals of an OECD
    SAF-T / national return. `table_key` selects a RATE_TABLES entry (the localized G2 param).
    """
    if table_key not in RATE_TABLES:
        raise ValueError(f"unknown rate table {table_key!r}")
    table = RATE_TABLES[table_key]
    taxable = max(0.0, gross_income - deductions)
    out = assess_income_tax(taxable, table["brackets"])
    out["currency"] = table["currency"]
    out["rate_table"] = table_key
    out["rate_table_source"] = table["source"]
    out["receipt"] = _unsigned_receipt(out["liability"], table["currency"])
    return out


def assess_vat(output_vat: float, input_vat: float, currency: str = "XXX") -> dict:
    """Net VAT = output VAT − input VAT (EN 16931 / SAF-T aggregates). Pure function.

    Negative net → a refund position. No key, no filing; receipt is unsigned (G1).
    """
    net = round(output_vat - input_vat, 2)
    return {
        "output_vat": output_vat,
        "input_vat": input_vat,
        "net_vat_due": net if net > 0 else 0.0,
        "refund_due": -net if net < 0 else 0.0,
        "currency": currency,
        "receipt": _unsigned_receipt(net if net > 0 else 0.0, currency),
    }


def _unsigned_receipt(amount: float, currency: str) -> dict:
    """A filing-receipt SKELETON. G1: unsigned — the governing organ signs with ITS key.

    `signature` is explicitly None and `server_held_authority` is False so a reviewer can see
    the module never signs. The Council (sovereign) or adopting state attaches the signature.
    """
    return {
        "assessed_amount": amount,
        "currency": currency,
        "proof": None,                # G1 — this module signs nothing (unified with civil/corp/cred)
        "server_held_authority": SERVER_HELD_AUTHORITY,  # False
        "status": "assessed-unsigned",
    }


# R1.D: load per-jurisdiction rate tables at import (embedded JPN/FLAT20 remain as fallback).
load_rate_tables()


def solve(*_args, **_kwargs):
    """Cell entry — R0 is reference-only; a LIVE filing against a real government record is
    Council+operator gated. The pure assessment functions above run in conformance tests."""
    raise RuntimeError(
        "tax-assess R0: reference assessment only. Live filing against a government record is "
        "Council+operator gated (principal A: Council Lv7+; principal B: adopting state)."
    )


if __name__ == "__main__":
    # quick demo on the JP reference table
    demo = assess_from_return(gross_income=6_000_000, deductions=1_000_000, table_key="JPN.income")
    print(f"JP taxable 5,000,000 → liability {demo['liability']:,.0f} JPY "
          f"(eff {demo['effective_rate']:.2%})")
