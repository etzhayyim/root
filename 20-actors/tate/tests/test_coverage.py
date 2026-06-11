#!/usr/bin/env python3
"""tate 盾 — jurisdiction-coverage honesty tests (G10, ADR-2606112400). Pure stdlib.

Verifies the worldwide expansion stays HONEST:
  - the jurisdiction registry is bounded + representative (5 systems), every entry
    carries the UPL anchor + fake-help + referral directories + verify-current-law
  - every covered jurisdiction has ≥1 clause pattern AND ≥1 procedure (no hollow flag)
  - the coverage ratio against ~193 UN states is LOW and reported as such (推測より空白)
  - named gaps are non-empty (the next-wave worklist exists)
"""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from coverage_report import coverage, report  # noqa: E402
from respond_plan import load_jurisdictions  # noqa: E402


def test_jurisdiction_registry_complete():
    juris = load_jurisdictions()
    assert set(juris.keys()) == {":jp", ":us", ":eu", ":uk", ":de"}
    for j in juris.values():
        assert j[":juris/upl-anchor"], j[":juris/id"]
        assert j[":juris/fake-help"] and j[":juris/referrals"], j[":juris/id"]
        assert j[":juris/service-note"], j[":juris/id"]
        assert j[":juris/verify-current-law"] is True
        assert j[":juris/sourcing"] == ":representative"
        assert float(j[":juris/refer-over-amount"]) > 0


def test_no_hollow_jurisdiction():
    cov = coverage()
    for j in cov["jurisdictions"]:
        assert cov["patterns_by_jurisdiction"].get(j, 0) >= 1, f"{j} has no clause patterns"
        assert cov["procedures_by_jurisdiction"].get(j, 0) >= 1, f"{j} has no procedures"


def test_coverage_ratio_honest():
    cov = coverage()
    assert cov["covered_count"] == 5
    assert cov["un_member_states"] == 193
    assert cov["coverage_ratio"] < 0.05, "coverage must be reported as the small number it is"
    assert len(cov["named_gaps"]) >= 4


def test_report_names_the_gap():
    text = report(coverage())
    assert "named gaps" in text.lower() or "Named gaps" in text
    assert ":unknown-jurisdiction" in text  # the degrade path is documented in the readout
    assert "193" in text


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok {fn.__name__}")
    print(f"{len(fns)} passed")
