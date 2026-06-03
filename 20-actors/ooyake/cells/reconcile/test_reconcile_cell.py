"""Tests for ooyake ReconcileCell (ADR-2606021600 §5).

Run: python3 -m pytest 20-actors/ooyake/cells/reconcile/test_reconcile_cell.py
 or: python3 20-actors/ooyake/cells/reconcile/test_reconcile_cell.py  (self-run)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cell import ReconcileCell, reconcile  # noqa: E402


def test_bundled_promotes_expected_units():
    rep = reconcile()
    # full JP central + proof-of-model chain + country/ministry breadth rows
    assert rep["total_units"] == 38, rep["total_units"]
    # exactly the 36 units present in authority-reference.edn, all agreeing.
    # (2026-06-03: authority-reference expanded 8 → 26 after the QID-integrity fix
    #  — every JP-subnational/agency QID had been fabricated; see MATURITY.md — then
    #  → 30 adding web-verified France + Canada, → 36 adding Italy + Australia +
    #  India country+finance-ministry rows, completing the G7 nations.)
    assert rep["coverage"]["authoritative_after"] == 36
    assert rep["promoted_to_authoritative"] == [
        "gov.aus",
        "gov.aus.treasury",
        "gov.can",
        "gov.can.fin",
        "gov.deu",
        "gov.eu",
        "gov.fra",
        "gov.fra.minefi",
        "gov.gbr",
        "gov.gbr.hmrc",
        "gov.ind",
        "gov.ind.mof",
        "gov.ita",
        "gov.ita.mef",
        "gov.jpn",
        "gov.jpn.cao",
        "gov.jpn.city.13104",
        "gov.jpn.digital",
        "gov.jpn.maff",
        "gov.jpn.meti",
        "gov.jpn.mext",
        "gov.jpn.mhlw",
        "gov.jpn.mic",
        "gov.jpn.mlit",
        "gov.jpn.mod",
        "gov.jpn.moe",
        "gov.jpn.mof",
        "gov.jpn.mof.nta",
        "gov.jpn.mofa",
        "gov.jpn.moj",
        "gov.jpn.pref.13",
        "gov.jpn.reconstruction",
        "gov.kor",
        "gov.usa",
        "gov.usa.treasury",
        "gov.usa.treasury.irs",
    ]


def test_no_conflicts_and_honest_remainder():
    rep = reconcile()
    # all QIDs now agree across seed↔authority (no fabricated mismatches)
    assert rep["conflicts_kept_unverified"] == []
    # only the 2 units without a Wikidata QID (NTA Tokyo regional + 麹町税務署)
    # stay representative — no authority record can confirm them (G5)
    assert len(rep["no_authority_record_kept_representative"]) == 2
    assert rep["coverage"]["representative_after"] == 2


def test_cell_bundled_mode_ok():
    out = ReconcileCell().solve({"mode": "bundled"})
    assert out["status"] == "ok"
    assert out["report"]["coverage"]["authoritative_after"] == 36


def test_cell_live_mode_gated():
    try:
        ReconcileCell().solve({"mode": "live"})
    except RuntimeError as e:
        assert "G4" in str(e) and "not activated" in str(e)
    else:
        raise AssertionError("live mode must raise (G4 gated)")


def test_cell_unknown_mode_rejected():
    try:
        ReconcileCell().solve({"mode": "bogus"})
    except ValueError as e:
        assert "unknown reconcile mode" in str(e)
    else:
        raise AssertionError("unknown mode must raise ValueError")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"{len(fns)} passed")
