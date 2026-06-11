#!/usr/bin/env python3
"""End-to-end membrane test for analyze.py — propose → triage → route → revision."""
from __future__ import annotations

import contributor as contrib
from analyze import _report, run
from revision import current


def test_run_routes_every_seed_edit():
    res = run()
    by_id = {r["edit"]: r for r in res["rows"]}
    assert set(by_id) == {"e1", "e2", "e3", "e4", "e5"}


def test_optimistic_and_voted_edits_are_accepted():
    res = run()
    by_id = {r["edit"]: r for r in res["rows"]}
    assert by_id["e1"]["route"] == ":auto-accept" and by_id["e1"]["accepted"]
    assert by_id["e2"]["route"] == ":vote" and by_id["e2"]["accepted"]      # 8-1
    assert by_id["e3"]["route"] == ":vote" and by_id["e3"]["accepted"]      # 5-0


def test_invariant_and_rider_edits_are_not_accepted():
    res = run()
    by_id = {r["edit"]: r for r in res["rows"]}
    assert by_id["e4"]["route"] == ":council-lv7" and not by_id["e4"]["accepted"]
    assert by_id["e5"]["route"] == ":refused" and not by_id["e5"]["accepted"]


def test_accepted_edits_landed_in_revision_history():
    res = run()
    # e1 (tsmc hq-address) and e2 (example-listed status) accepted → present as current
    assert current(res["history"], "org.corp.tsmc", "hq-address") is not None
    assert current(res["history"], "org.corp.example-listed", "status") is not None
    # e4 (license, council-pending) and e5 (refused) did NOT land
    assert current(res["history"], "org.corp.example-listed", "license") is None


def test_contributor_trajectory_recorded():
    res = run()
    # the rider-violating author (esau) is recorded as refused, not accepted
    esau = "did:web:etzhayyim.com:member:esau"
    c = contrib.counts(res["trajectory"], esau)
    assert c["accepted"] == 0 and c["refused"] >= 1
    # the council-pending author (dan) has no decided event yet (pending ≠ refused)
    dan = "did:web:etzhayyim.com:member:dan"
    assert contrib.counts(res["trajectory"], dan) == {"accepted": 0, "refused": 0}


def test_report_renders():
    md = _report(run())
    assert "community-edit membrane dry-run" in md
    assert "Revision history" in md


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} passed in test_analyze.py")
    sys.exit(1 if failed else 0)
